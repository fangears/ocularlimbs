"""
OcularLimbs MCP 服务器
为 Claude Code 提供 Model Context Protocol 集成
"""

import asyncio
import json
import sys
import logging
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ocularlimbs.mcp")

# 导入客户端
try:
    from .client import see, capture, find_text, click, click_text, type_text, press_key, execute
    logger.info("OcularLimbs 客户端导入成功")
except ImportError as e:
    logger.error(f"无法导入 OcularLimbs 客户端: {e}")
    sys.stderr.write(f"错误: {e}\n")
    sys.stderr.write("请确保已正确安装 OcularLimbs: pip install -e .\n")
    sys.exit(1)

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

    logger.info(f"调用工具: {name}, 参数: {arguments}")

    try:
        if name == "see":
            result = see()
            logger.info(f"see() 结果: 屏幕尺寸 {result.get('width', 0)}x{result.get('height', 0)}")
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "capture":
            filename = arguments.get("filename")
            compression = arguments.get("compression", "balanced")
            result = capture(filename, compression)
            logger.info(f"capture() 完成: filename={filename}, compression={compression}")
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "find_text":
            text = arguments.get("text")
            result = find_text(text)
            logger.info(f"find_text('{text}') 结果: found={result.get('found', False)}")
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "click":
            x = arguments.get("x")
            y = arguments.get("y")
            logger.info(f"click({x}, {y})")
            result = click(x, y)
            logger.info(f"click() 结果: success={result}")
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "click_text":
            text = arguments.get("text")
            logger.info(f"click_text('{text}')")
            result = click_text(text)
            logger.info(f"click_text() 结果: success={result}")
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "type_text":
            text = arguments.get("text")
            logger.info(f"type_text('{text[:50]}...')")
            result = type_text(text)
            logger.info(f"type_text() 结果: success={result}")
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "press_key":
            key = arguments.get("key")
            logger.info(f"press_key('{key}')")
            result = press_key(key)
            logger.info(f"press_key() 结果: success={result}")
            return [TextContent(
                type="text",
                text=json.dumps({"success": result}, ensure_ascii=False)
            )]

        elif name == "execute":
            goal = arguments.get("goal")
            logger.info(f"execute('{goal[:50]}...')")
            result = execute(goal)
            logger.info(f"execute() 结果: {str(result)[:100]}")
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        else:
            logger.warning(f"未知工具: {name}")
            return [TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]

    except Exception as e:
        logger.error(f"工具调用出错: {name}, 错误: {e}", exc_info=True)
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
