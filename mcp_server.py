#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OcularLimbs MCP Server
使用官方 MCP SDK 实现，确保兼容性
"""

import sys
import json
import os
from pathlib import Path
from typing import Any, Optional
import asyncio
import io
import contextlib

# 添加项目路径到 Python 路径
OCULAR_HOME = Path(os.environ.get('OCULAR_LIMBS_HOME',
                                  Path(__file__).parent.absolute()))

lib_path = OCULAR_HOME / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))
if str(OCULAR_HOME) not in sys.path:
    sys.path.insert(0, str(OCULAR_HOME))

# 导入 MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 导入 OcularLimbs 模块（延迟导入以避免干扰 MCP 协议）
_vision_module = None
_action_module = None
_config = None

def _get_modules():
    """延迟加载模块"""
    global _vision_module, _action_module, _config

    if _config is None:
        from ocularlimbs.config.settings import SystemConfig
        _config = SystemConfig()

    if _action_module is None:
        from ocularlimbs.action import ActionModule
        _action_module = ActionModule(_config.action)

    return _config, _action_module, _vision_module


def _get_vision_module():
    """获取视觉模块（延迟加载）"""
    global _vision_module, _config

    if _vision_module is None and _config is not None:
        try:
            # 静默加载，避免输出干扰 MCP 协议
            with contextlib.redirect_stderr(io.StringIO()):
                from ocularlimbs.vision import VisionModule
                _vision_module = VisionModule(_config.vision)
        except Exception as e:
            # OCR 不可用，视觉模块不可用
            _vision_module = None

    return _vision_module


# 创建 MCP 服务器实例
app = Server("ocularlimbs")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具"""

    return [
        Tool(
            name="ocular_see",
            description="观察屏幕，捕获屏幕内容并识别文字和UI元素",
            inputSchema={
                "type": "object",
                "properties": {
                    "use_ocr": {
                        "type": "boolean",
                        "description": "是否使用OCR识别文字",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="ocular_capture",
            description="截取屏幕并保存为图片文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "save_path": {
                        "type": "string",
                        "description": "保存路径（可选）"
                    }
                }
            }
        ),
        Tool(
            name="ocular_click",
            description="点击屏幕上的指定位置",
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
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "description": "鼠标按钮",
                        "default": "left"
                    }
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="ocular_type",
            description="在当前焦点输入文本",
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
            name="ocular_hotkey",
            description="按下组合键",
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
            name="ocular_find_text",
            description="在屏幕上查找指定文字",
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
            name="ocular_get_mouse_position",
            description="获取当前鼠标位置",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ocular_get_screen_size",
            description="获取屏幕尺寸",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""

    try:
        config, action, vision = _get_modules()

        if name == "ocular_see":
            return await _tool_see(arguments, config)
        elif name == "ocular_capture":
            return await _tool_capture(arguments, config)
        elif name == "ocular_click":
            return _tool_click(arguments, action)
        elif name == "ocular_type":
            return _tool_type(arguments, action)
        elif name == "ocular_hotkey":
            return _tool_hotkey(arguments, action)
        elif name == "ocular_find_text":
            return await _tool_find_text(arguments, config)
        elif name == "ocular_get_mouse_position":
            return _tool_get_mouse_position(action)
        elif name == "ocular_get_screen_size":
            return _tool_get_screen_size(action)
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]


async def _tool_see(args: dict, config) -> list[TextContent]:
    """观察屏幕"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "视觉模块不可用（OCR未安装或初始化失败）"}, ensure_ascii=False)
        )]

    try:
        observation = vision.observe()
        capture = observation["capture"]

        result = {
            "screen": {
                "width": capture.width,
                "height": capture.height,
                "timestamp": capture.timestamp
            },
            "texts": [],
            "elements": [],
            "summary": observation["summary"]
        }

        # 文字区域
        for text_region in observation["texts"]:
            result["texts"].append({
                "text": text_region.text,
                "bbox": {
                    "x": text_region.bbox.x,
                    "y": text_region.bbox.y,
                    "width": text_region.bbox.width,
                    "height": text_region.bbox.height
                },
                "confidence": text_region.confidence
            })

        # UI 元素
        for element in observation["elements"]:
            if element.bbox:
                result["elements"].append({
                    "type": element.type,
                    "label": element.label,
                    "bbox": {
                        "x": element.bbox.x,
                        "y": element.bbox.y,
                        "width": element.bbox.width,
                        "height": element.bbox.height
                    }
                })

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"观察失败: {str(e)}"}, ensure_ascii=False)
        )]


async def _tool_capture(args: dict, config) -> list[TextContent]:
    """截取屏幕"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "视觉模块不可用"}, ensure_ascii=False)
        )]

    save_path = args.get("save_path")

    try:
        import time
        from pathlib import Path

        observation = vision.observe()
        capture = observation["capture"]

        # 默认保存路径
        if not save_path:
            workspace = Path(config.work_dir) / "screenshots"
            workspace.mkdir(parents=True, exist_ok=True)
            save_path = str(workspace / f"capture_{int(time.time())}.png")

        # 保存图片
        from PIL import Image
        img = Image.open(io.BytesIO(capture.image))
        img.save(save_path)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "path": save_path,
                "size": len(capture.image)
            }, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"截图失败: {str(e)}"}, ensure_ascii=False)
        )]


def _tool_click(args: dict, action) -> list[TextContent]:
    """点击屏幕"""
    x = args.get("x")
    y = args.get("y")
    button = args.get("button", "left")

    try:
        success = action.click(x, y, button)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "position": {"x": x, "y": y},
                "button": button
            }, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"点击失败: {str(e)}"}, ensure_ascii=False)
        )]


def _tool_type(args: dict, action) -> list[TextContent]:
    """输入文本"""
    text = args.get("text", "")

    try:
        success = action.type_text(text)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "text_length": len(text)
            }, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"输入失败: {str(e)}"}, ensure_ascii=False)
        )]


def _tool_hotkey(args: dict, action) -> list[TextContent]:
    """按下组合键"""
    keys = args.get("keys", [])

    try:
        success = action.hotkey(*keys)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": success,
                "keys": keys
            }, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"组合键失败: {str(e)}"}, ensure_ascii=False)
        )]


async def _tool_find_text(args: dict, config) -> list[TextContent]:
    """查找文字"""
    vision = _get_vision_module()
    if vision is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "视觉模块不可用"}, ensure_ascii=False)
        )]

    text = args.get("text", "")

    try:
        observation = vision.observe()

        for text_region in observation["texts"]:
            if text.lower() in text_region.text.lower():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "found": True,
                        "text": text_region.text,
                        "bbox": {
                            "x": text_region.bbox.x,
                            "y": text_region.bbox.y,
                            "width": text_region.bbox.width,
                            "height": text_region.bbox.height
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
            text=json.dumps({"error": f"查找失败: {str(e)}"}, ensure_ascii=False)
        )]


def _tool_get_mouse_position(action) -> list[TextContent]:
    """获取鼠标位置"""
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
            text=json.dumps({"error": f"获取失败: {str(e)}"}, ensure_ascii=False)
        )]


def _tool_get_screen_size(action) -> list[TextContent]:
    """获取屏幕尺寸"""
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
            text=json.dumps({"error": f"获取失败: {str(e)}"}, ensure_ascii=False)
        )]


async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
