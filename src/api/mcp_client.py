"""
MCP Client

使用 Streamable HTTP 方式连接高德云端 MCP Server，，无需本地部署 MCP Server。
提供地理位置相关能力（天气、POI、路线规划等）。

依赖：pip install mcp httpx
"""

from six.moves.urllib import response
import hashlib
import os
import logging
import json
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

AMAP_MCP_BASE_URL = "https://mcp.amap.com/mcp"


class AmapMcpClient:
    """
    高德 MCP Client 封装

    通过 Streamable HTTP 连接高德云端 MCP Server，
    提供工具列表查询和工具调用的能力。
    """

    def __init__(self):
        """
        初始化 MCP Client
        """
        self._api_key = os.getenv("AMAP_API_KEY")
        if not self._api_key:
            raise ValueError("未提供高德 API Key，请在 .env 中设置 AMAP_API_KEY")
        self._server_url = f"{AMAP_MCP_BASE_URL}?key={self._api_key}"
        self._session = None
        self._tools: list[dict[str, Any]] = []

        # NOTE: 压制 httpx 的请求日志，避免打印完整 URL 导致 key 泄露
        logging.getLogger("httpx").setLevel(logging.WARNING)

        logger.info("MCP Client 初始化完成，key: %s", self._masked_key)

    @property
    def _masked_key(self) -> str:
        """hash加密key，用于日志输出，避免泄露完整密钥"""
        key_hash = hashlib.sha256(self._api_key.encode()).hexdigest()[:8]
        return f"{self._api_key[:4]}***{key_hash}"

    # @property
    # def server_url(self) -> str:
    #     """MCP Server 完整 URL（含 key）"""
    #     return self._server_url

    @property
    def tools(self) -> list[dict[str, Any]]:
        """工具列表（需先调用 connect）"""
        return self._tools

    async def connect(self) -> list[dict[str, Any]]:
        """
        连接 MCP Server 并获取可用工具列表
        使用 Streamable HTTP 传输方式，每次调用都会建立新连接
        @returns 可用工具列表
        """
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession

        async with streamablehttp_client(self._server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                self._tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in result.tools
                ]
                logger.info("已连接高德 MCP Server，发现 %d 个工具", len(self._tools))
                return self._tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        调用 MCP Server 上的指定工具

        @param tool_name 工具名称（如 maps_weather、maps_geo 等）
        @param arguments 工具参数（如 {"city": "北京"}）
        @returns 工具返回的文本结果
        """
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession

        async with streamablehttp_client(self._server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                # NOTE: MCP 工具返回的 content 是一个列表，每项可能是文本或其他类型
                # 这里只提取文本部分，拼接后返回
                text_parts = []
                for content in result.content:
                    if hasattr(content, "text"):
                        text_parts.append(content.text)

                response_text = "\n".join(text_parts)
                logger.info(
                    "调用工具 %s(%s) 成功，返回 %d 字符",
                    tool_name,
                    arguments,
                    len(response_text),
                )
                return response_text

    async def get_weather(self, city: str) -> str:
        """
        工具1: 天气查询

        @param city 城市名称，如"北京"、"上海"
        @returns 天气信息文本
        """
        return await self.call_tool("maps_weather", {"city": city})

    async def get_ip_location(self, ipv4: str) -> str:
        """
        工具2: IP 地址定位

        @param ipv4 IP 地址，如"[IP_ADDRESS]"
        @returns IP 地址定位信息文本
        """
        return await self.call_tool("maps_ip_location", {"ip": ipv4})

    async def get_keyword_serach(self, keywords, city, citylimit=False) -> str:
        """
        工具3: 关键词搜索

        @param keywords 搜索关键词，如"火锅"、"咖啡厅"
        @param city 城市名称 
        @param citylimit 是否只在城市范围内搜索,默认False
        @returns 相关信息
        """
        args: dict[str, Any] = {"keywords": keywords, "city": city, "citylimit": citylimit}
        return await self.call_tool("maps_text_search", args)

    async def get_maps_geo(
        self, address: str
    ) -> str:
        """
        工具4: 地址 -> 经纬度

        @param address 地址，如"天安门"
        @returns 经纬度文本
        """
        args: dict[str, Any] = {"address": address}
        response = await self.call_tool("maps_geo", args)
        result = json.loads(response)['results'][0]['location']
        return result

    async def get_maps_direction_driving(
        self, origin: str, destination: str
    ) -> str:
        """
        工具5: 驾车路径规划

        @param origin 起点，如"天安门"
        @param destination 终点，如"故宫"
        @returns 返回通勤方案的数据
        """
        origin_geo = await self.get_maps_geo(origin)
        destination_geo = await self.get_maps_geo(destination)
        args: dict[str, Any] = {"origin": origin_geo, "destination": destination_geo}

        return await self.call_tool("maps_direction_driving", args)
    
    async def get_maps_direction_walking(self, origin: str, destination: str) -> str:
        """
        工具6: 步行路径规划

        @param origin 起点，如"天安门"
        @param destination 终点，如"故宫"
        @returns 返回通勤方案的数据
        """
        origin_geo = await self.get_maps_geo(origin)
        destination_geo = await self.get_maps_geo(destination)
        args: dict[str, Any] = {"origin": origin_geo, "destination": destination_geo}

        return await self.call_tool("maps_direction_walking", args)

# ==================== 测试 ====================
async def _test():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    client = AmapMcpClient()

    logger.info("="*50)
    logger.info("正在获取可用工具列表...")
    tools = await client.connect()
    for tool in tools:
        print(f"   {tool['name']} {tool['description']}")
    # 测试工具1: 天气查询
    logger.info("="*50)
    logger.info("正在查询天气...")
    weather = await client.get_weather("重庆")
    logger.info(f"查询结果: {weather}")
    logger.info("="*50)

    # 测试工具2: ip地址定位
    logger.info("正在查询IP地址所在地...")
    ip_location = await client.get_ip_location("60.205.234.89")
    logger.info(f"查询结果: {ip_location}")

    # 测试工具3: 关键词搜索
    logger.info("正在进行关键词搜索...")
    results = await client.get_keyword_serach("火锅", "重庆", True)
    logger.info(f"查询结果: {results}")

    # 测试工具4: 地址 -> 经纬度
    logger.info("正在进行地址 -> 经纬度查询...")
    geo = await client.get_maps_geo("天安门")
    logger.info(f"查询结果: {geo}")

    # 测试工具5: 驾车路径规划
    logger.info("正在进行驾车路径规划...")
    driving = await client.get_maps_direction_driving("天津", "禹州")
    logger.info(f"查询结果: {driving}")

    # 测试工具6: 步行路径规划
    logger.info("正在进行步行路径规划...")
    walking = await client.get_maps_direction_walking("南开大学津南校区", "天津大学北洋园校区")
    logger.info(f"查询结果: {walking}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(_test())
