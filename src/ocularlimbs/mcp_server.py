"""
OcularLimbs MCP 服务器
为 Claude Code 提供 Model Context Protocol 集成
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 导入客户端
from .client import see, capture, find_text, click, click_text, type_text, press_key, execute

# 创建 MCP 服务器实例
server = Server("ocularlimbs")

# 定义工具列表
TOOLS = [
    Tool(
        name="see",
        description="查看当前屏幕，获取屏幕信息和识别到的文字",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="capture",
        description="捕获屏幕截图并可选保存到文件",
        inputSchema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "保存的文件名（可选）"
                },
                "compression": {
                    "type": "string",
                    "enum": ["ultra_fast", "fast", "balanced", "quality", "archival"],
                    "description": "压缩预设（默认: balanced）"
                }
            },
            "required": []
        }
    ),
    Tool(
        name="find_text",
        description="在屏幕上查找文字位置",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要查找的文字"
                }
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="click",
        description="点击屏幕上的指定坐标",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X坐标"
                },
                "y": {
                    "type": "integer",
                    "description": "Y坐标"
                }
            },
            "required": ["x", "y"]
        }
    ),
    Tool(
        name="click_text",
        description="查找并点击包含指定文字的元素",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要点击的文字"
                }
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="type_text",
        description="输入文本到当前位置",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要输入的文本"
                }
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="press_key",
        description="按下指定的键（如 enter, escape, f1）",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "按键名称"
                }
            },
            "required": ["key"]
        }
    ),
    Tool(
        name="execute",
        description="执行自然语言描述的任务",
        inputSchema={
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "任务描述"
                }
            },
            "required": ["goal"]
        }
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""

    try:
        if name == "see":
            result = see()
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "capture":
            filename = arguments.get("filename")
            compression = arguments.get("compression", "balanced")
            result = capture(filename, compression)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "find_text":
            text = arguments.get("text")
            result = find_text(text)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "click":
            x = arguments.get("x")
            y = arguments.get("y")
            result = click(x, y)
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "click_text":
            text = arguments.get("text")
            result = click_text(text)
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "type_text":
            text = arguments.get("text")
            result = type_text(text)
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "press_key":
            key = arguments.get("key")
            result = press_key(key)
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "execute":
            goal = arguments.get("goal")
            result = execute(goal)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        else:
            return [TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]


async def main():
    """启动 MCP 服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
