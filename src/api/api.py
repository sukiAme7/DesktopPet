import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn

# 加载 .env 文件中的环境变量
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

class ChatRequest(BaseModel):
    text: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.text
    print(f"[前端输入] {user_message}")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": "你是一个活泼可爱的桌面宠物，名叫Haruto。你的回答应该简短、有趣、带有一点二次元口癖，并且每次回答绝对不要超过50个字，因为桌面的聊天气泡装不下太多字。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1024,     
            temperature=0.5     
        )
        
        reply_text = response.choices[0].message.content
        print(f"[DeepSeek 输出] {reply_text}")
        
        return {"reply": reply_text}
        
    except Exception as e:
        print(f"[API 报错] {e}")
        return {"reply": "哎呀，我的大脑(API)暂时连不上了，请检查一下网络喵~"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)