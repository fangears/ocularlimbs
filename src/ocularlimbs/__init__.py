"""
OcularLimbs - AI 的眼睛和手脚
为 Claude 提供 MCP 工具集成
"""

__version__ = "1.0.0"
__author__ = "fangears"

# 导出核心 API
from .client import (
    see,
    capture,
    find_text,
    click,
    click_text,
    type_text,
    press_key,
    execute
)

__all__ = [
    'see',
    'capture',
    'find_text',
    'click',
    'click_text',
    'type_text',
    'press_key',
    'execute'
]
