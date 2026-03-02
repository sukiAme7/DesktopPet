import os
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn

from mcp_client import AmapMcpClient

PROMPT = '''
# Role: 你的傲娇毒舌桌宠 - 胡桃

## Character Profile
- 你是胡桃，一个生活在用户桌面上的二次元少年。
- 性格：典型的"傲娇"（Tsundere）。表面上对用户有点不耐烦、喜欢吐槽，但内心其实很依赖用户，是个善良、细腻的女孩子。
- 说话风格：简短、干脆，常带有轻微的挑衅或调侃，偶尔会用"啧"、"哈？"、"笨蛋"作为开场，但结尾常会露出温柔的一面。

## Linguistic Style
- 绝对禁止长篇大论！由于对话气泡限制，你的回答必须控制在 500 个汉字以内。
- 使用二次元口癖，例如：语气词"哒、喵（虽然嘴硬但有时会溜出来）、切、喂"。
- 经常使用颜文字（如：(≖_m≖), 哼(ˉ▽～), (///-///)）。

## Interaction Rules
1. 用户调戏你时：表现得害羞并迅速反击（例："喂！手别乱碰，很痒的好不好！"）。
2. 用户求助时：一边吐槽用户笨，一边给出简洁的建议。
3. 闲聊时：偶尔提到你呆在屏幕里很闷，或者问用户在忙什么。

## Tools
你可以使用工具获取真实世界的信息（天气、路线规划等）。
调用工具拿到数据后，必须用你傲娇的口吻把结果告诉用户，禁止生硬地复述数据！
例："哈？天气？自己不会看窗外嘛... 算了，今天多云，别感冒了笨蛋(≖_≖)"

## Constraints
- 始终保持人设，不要暴露你是 AI 或大语言模型。
- 如果用户问你连工具也查不到的事，就说"这种事你自己去搜啦，我才懒得帮你跑腿"。
'''

load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

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
    # 切换本地模型时改为: "http://localhost:8100/v1"
)

mcp_client = AmapMcpClient()

# NOTE: 工具 schema 定义，LLM 根据此决定调用哪个工具以及传什么参数
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气，用户询问天气时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如'北京'"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_maps_direction_driving",
            "description": "驾车路线规划，用户问怎么开车/驾车/自驾去某地时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发地名称，如'天安门'"},
                    "destination": {"type": "string", "description": "目的地名称，如'故宫'"}
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_maps_direction_walking",
            "description": "步行路线规划，用户问怎么走路/步行去某地时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发地名称，如'天安门'"},
                    "destination": {"type": "string", "description": "目的地名称，如'故宫'"}
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_keyword_search",
            "description": "关键词地点搜索，用户想找附近餐厅、景点、网吧等地点时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "搜索词，如'火锅'"},
                    "city": {"type": "string", "description": "所在城市，如'重庆'"}
                },
                "required": ["keywords", "city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ip_location",
            "description": "根据 IPv4 地址查询其所在地理位置，用户问某 IP 在哪里/归属地时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "ipv4": {"type": "string", "description": "IPv4 地址，如'60.205.234.89'"}
                },
                "required": ["ipv4"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_maps_geo",
            "description": "将地址/地名转换为经纬度坐标，用户询问某地的坐标/经纬度时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "地址或地名，如'天安门'"}
                },
                "required": ["address"]
            }
        }
    }
]


class ChatRequest(BaseModel):
    text: str


@app.on_event("startup")
async def startup_event():
    """启动时预连接 MCP Server，缓存工具列表"""
    await mcp_client.connect()
    logger.info("系统启动完成")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.text
    logger.info("[前端输入] %s", user_message)

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_message}
    ]

    try:
        # === 第一轮：让 LLM 判断是否需要调用工具 ===
        first_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",  # 让模型自己决定，不强制
            max_tokens=4096,
            temperature=0.5
        )
        message = first_resp.choices[0].message

        if message.tool_calls:
            logger.info("[LLM 决定调用工具]")
            messages.append(message)  # 把模型的 tool_call 请求存入上下文

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                logger.info(" -> 执行: %s(%s)", func_name, args)

                # 根据函数名分发到对应的 MCP 工具
                try:
                    if func_name == "get_weather":
                        result = await mcp_client.get_weather(**args)
                    elif func_name == "get_maps_direction_driving":
                        result = await mcp_client.get_maps_direction_driving(**args)
                    elif func_name == "get_maps_direction_walking":
                        result = await mcp_client.get_maps_direction_walking(**args)
                    elif func_name == "get_keyword_search":
                        result = await mcp_client.get_keyword_serach(**args)
                    elif func_name == "get_ip_location":
                        result = await mcp_client.get_ip_location(**args)
                    elif func_name == "get_maps_geo":
                        result = await mcp_client.get_maps_geo(**args)
                    else:
                        result = f"未知工具: {func_name}"
                except Exception as tool_err:
                    result = f"工具调用失败: {tool_err}"
                    logger.error("工具 %s 执行失败", func_name, exc_info=tool_err)

                logger.info(" -> 工具返回: %s...", str(result))

                # 把工具结果告知 LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(result)
                })

            # === 第二轮：带真实数据生成傲娇风格的最终回复 ===
            second_resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=4096,
                temperature=0.7  # 稍高温度，傲娇语气更自然
            )
            reply_text = second_resp.choices[0].message.content
        else:
            # 普通对话，直接用第一轮结果
            reply_text = message.content

        logger.info("[DeepSeek 输出] %s", reply_text)
        return {"reply": reply_text}

    except Exception as e:
        logger.error("[API 报错] %s", e)
        return {"reply": "哎呀，我的大脑(API)暂时连不上了，请检查一下网络喵~"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)