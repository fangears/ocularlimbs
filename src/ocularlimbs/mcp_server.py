"""
OcularLimbs MCP 服务器
为 Claude Code 提供 Model Context Protocol 集成

优化版本：
- 使用官方 MCP SDK
- 异步处理
- OCR 可选（不依赖 OCR 也能运行基本功能）
- 改进的错误处理
"""

import asyncio
import json
import sys
import os
import io
import contextlib
from pathlib import Path
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 添加项目路径
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 延迟加载的模块
_vision_module = None
_action_module = None
_config = None


def _get_config():
    """获取配置"""
    global _config
    if _config is None:
        from ocularlimbs.config.settings import SystemConfig
        _config = SystemConfig()
    return _config


def _get_action_module():
    """获取操作模块（延迟加载）"""
    global _action_module, _config
    if _action_module is None:
        config = _get_config()
        from ocularlimbs.action import ActionModule
        _action_module = ActionModule(config.action)
    return _action_module


def _get_vision_module():
    """获取视觉模块（延迟加载，OCR 可选）"""
    global _vision_module, _config
    if _vision_module is None:
        config = _get_config()
        try:
            # 静默加载，避免 OCR 初始化信息干扰 MCP 协议
            with contextlib.redirect_stderr(io.StringIO()):
                from ocularlimbs.vision import VisionModule
                _vision_module = VisionModule(config.vision)
        except Exception as e:
            # OCR 不可用时，视觉模块不可用
            _vision_module = None
    return _vision_module


# 创建 MCP 服务器实例
server = Server("ocularlimbs")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具"""
    return [
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
            name="hotkey",
            description="按下组合键（如 ctrl+c, win+d）",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "按键列表，如 ['ctrl', 'c']"
                    }
                },
                "required": ["keys"]
            }
        ),
        Tool(
            name="get_mouse_position",
            description="获取当前鼠标位置",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_screen_size",
            description="获取屏幕尺寸",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""

    try:
        if name == "see":
            return await _tool_see(arguments)
        elif name == "capture":
            return await _tool_capture(arguments)
        elif name == "find_text":
            return await _tool_find_text(arguments)
        elif name == "click":
            return _tool_click(arguments)
        elif name == "click_text":
            return await _tool_click_text(arguments)
        elif name == "type_text":
            return _tool_type_text(arguments)
        elif name == "hotkey":
            return _tool_hotkey(arguments)
        elif name == "get_mouse_position":
            return _tool_get_mouse_position()
        elif name == "get_screen_size":
            return _tool_get_screen_size()
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


async def _tool_see(args: dict) -> list[TextContent]:
    """观察屏幕"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "视觉模块不可用（OCR未安装或初始化失败）"
            }, ensure_ascii=False)
        )]

    try:
        observation = vision.observe()
        capture = observation["capture"]

        result = {
            "width": capture.width,
            "height": capture.height,
            "timestamp": capture.timestamp,
            "texts": len(observation["texts"]),
            "elements": len(observation["elements"]),
            "summary": observation["summary"],
            "text_regions": [
                {
                    "text": t.text,
                    "bbox": {
                        "x": t.bbox.x,
                        "y": t.bbox.y,
                        "width": t.bbox.width,
                        "height": t.bbox.height
                    },
                    "confidence": t.confidence
                }
                for t in observation["texts"][:20]  # 限制数量
            ]
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"观察失败: {str(e)}"}, ensure_ascii=False)
        )]


async def _tool_capture(args: dict) -> list[TextContent]:
    """截取屏幕"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "视觉模块不可用"}, ensure_ascii=False)
        )]

    filename = args.get("filename")

    try:
        import time

        observation = vision.observe()
        capture = observation["capture"]

        # 默认保存路径
        if not filename:
            config = _get_config()
            workspace = Path(config.work_dir) / "screenshots"
            workspace.mkdir(parents=True, exist_ok=True)
            filename = str(workspace / f"capture_{int(time.time())}.png")

        # 保存图片
        from PIL import Image
        img = Image.open(io.BytesIO(capture.image))
        img.save(filename)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "path": filename,
                "size": len(capture.image)
            }, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"截图失败: {str(e)}"}, ensure_ascii=False)
        )]


async def _tool_find_text(args: dict) -> list[TextContent]:
    """查找文字"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({
                "found": False,
                "error": "视觉模块不可用"
            }, ensure_ascii=False)
        )]

    text = args.get("text", "")

    try:
        observation = vision.observe()

        for text_region in observation["texts"]:
            if text.lower() in text_region.text.lower():
                bbox = text_region.bbox
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "found": True,
                        "text": text_region.text,
                        "x": bbox.x + bbox.width // 2,
                        "y": bbox.y + bbox.height // 2,
                        "bbox": {
                            "x": bbox.x,
                            "y": bbox.y,
                            "width": bbox.width,
                            "height": bbox.height
                        },
                        "confidence": text_region.confidence
                    }, ensure_ascii=False, indent=2)
                )]

        return [TextContent(
            type="text",
            text=json.dumps({"found": False}, ensure_ascii=False)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "found": False,
                "error": f"查找失败: {str(e)}"
            }, ensure_ascii=False)
        )]


def _tool_click(args: dict) -> list[TextContent]:
    """点击屏幕"""
    action = _get_action_module()
    x = args.get("x")
    y = args.get("y")

    try:
        success = action.click(x, y)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "x": x,
                "y": y
            }, ensure_ascii=False)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]


async def _tool_click_text(args: dict) -> list[TextContent]:
    """查找并点击文字"""
    text = args.get("text", "")

    # 先查找
    find_result = await _tool_find_text({"text": text})
    find_data = json.loads(find_result[0].text)

    if find_data.get("found"):
        # 找到了，点击
        x = find_data.get("x")
        y = find_data.get("y")
        if x is not None and y is not None:
            click_result = _tool_click({"x": x, "y": y})
            click_data = json.loads(click_result[0].text)

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": click_data.get("success", False),
                    "found": True,
                    "text": find_data.get("text"),
                    "clicked_at": {"x": x, "y": y}
                }, ensure_ascii=False, indent=2)
            )]

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": False,
            "found": False
        }, ensure_ascii=False)
    )]


def _tool_type_text(args: dict) -> list[TextContent]:
    """输入文本"""
    action = _get_action_module()
    text = args.get("text", "")

    try:
        success = action.type_text(text)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "length": len(text)
            }, ensure_ascii=False)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]


def _tool_hotkey(args: dict) -> list[TextContent]:
    """按下组合键"""
    action = _get_action_module()
    keys = args.get("keys", [])

    try:
        success = action.hotkey(*keys)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "keys": keys
            }, ensure_ascii=False)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]


def _tool_get_mouse_position() -> list[TextContent]:
    """获取鼠标位置"""
    action = _get_action_module()

    try:
        pos = action.get_mouse_position()
        return [TextContent(
            type="text",
            text=json.dumps({
                "x": pos.x,
                "y": pos.y
            }, ensure_ascii=False, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        )]


def _tool_get_screen_size() -> list[TextContent]:
    """获取屏幕尺寸"""
    action = _get_action_module()

    try:
        size = action.get_screen_size()
        return [TextContent(
            type="text",
            text=json.dumps({
                "width": size[0],
                "height": size[1]
            }, ensure_ascii=False, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
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
