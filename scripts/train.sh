#!/bin/bash
#SBATCH --job-name=version1
#SBATCH -p qdagnormal
#SBATCH -N 1
#SBATCH -n 8
#SBATCH --gres=gpu:1
#SBATCH -o desktop_pet.log   # 标准输出日志

source /work/home/shiyan_dong/miniconda3/etc/profile.d/conda.sh
conda activate DesktopPet


python  ./src/llm/train.py --config config/train.yaml