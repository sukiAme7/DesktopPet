import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import argparse
import logging
import torch
import transformers


from src.utils.config_loader import load_config
from datasets import load_dataset
from peft import get_peft_model, LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def load_data(cfg, tokenizer):
    dataset = load_dataset("json", data_files=cfg.data.train_file)

    def format_chat_template(example):
        conversations = example['conversations']

        messages = []
        # 利用 zip 将被 HF 强行拆散的 from 和 value 重新两两配对
        for element in conversations:
            role_str = element['from']
            content_str = element['value']
            # 统一转换为模型认识的 role 规范
            if role_str == "system":
                role = "system"
            elif role_str == "user" or role_str == "human":
                role = "user"
            else:
                role = "assistant"

            messages.append({"role": role, "content": content_str})

        # 应用 Qwen 专属的对话模板，拼接成带 <|im_start|> 标识符的长字符串
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )

        model_inputs = tokenizer(
            text,
            max_length=1024, 
            truncation=True,
            padding=False  
        )

        # 3. 核心修复：为自回归训练构造 labels
        model_inputs["labels"] = model_inputs["input_ids"].copy()

        return model_inputs

    tokenized_dataset = dataset.map(
        format_chat_template,
    )

    return tokenized_dataset

def load_model_and_tokenizer(cfg):

    bnb_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    base_model=AutoModelForCausalLM.from_pretrained(
        cfg.model.model_path,
        quantization_config=bnb_config,
        device_map="auto",

    )
    base_model.config.use_cache=False
    base_model.config.pretraining_tp=1
    tokenizer=AutoTokenizer.from_pretrained(cfg.model.model_path)
    tokenizer.pad_token=tokenizer.eos_token

    return base_model, tokenizer
    
def apply_lora_to_model(cfg, model):
    lora_config=LoraConfig(
        r=cfg.lora.r,
        lora_alpha=cfg.lora.lora_alpha,
        target_modules=cfg.lora.target_modules,
        lora_dropout=cfg.lora.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )

    peft_model=get_peft_model(
        model,
        lora_config
    )

    return peft_model
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="训练配置文件路径")
    args = parser.parse_args()
    cfg = load_config(args.config)


    print(f"[INFO]Config Path: {args.config}")
    print(f"[INFO]Loading model and tokenizer...")

    model, tokenizer = load_model_and_tokenizer(cfg)

    model = apply_lora_to_model(cfg, model)
    model.print_trainable_parameters()

    print(f"[INFO]Processing dataset...")
    train_dataset = load_data(cfg, tokenizer)

    training_args = transformers.TrainingArguments(
        output_dir=cfg.training.output_dir,
        learning_rate=cfg.training.learning_rate,
        per_device_train_batch_size=cfg.training.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.training.gradient_accumulation_steps,
        save_steps=cfg.training.save_steps,
        logging_steps=cfg.training.logging_steps,
        num_train_epochs=cfg.training.num_train_epochs
    )

    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset['train'] if 'train' in train_dataset else train_dataset,
        data_collator=transformers.DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8),
    )

    print(f"[INFO]🔥Start Training...")
    trainer.train()

    print(f"[INFO]Training Completed...")
    print(f"[INFO]saving model to {cfg.training.output_dir}")
    trainer.model.save_pretrained(cfg.training.output_dir)
    tokenizer.save_pretrained(cfg.training.output_dir)

if __name__ == "__main__":
    main()