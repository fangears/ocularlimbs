"""
安全保护模块
防止危险操作和误操作
"""

from typing import List, Tuple, Optional
import re

from ..core.types import Point, Rectangle, MouseAction, KeyAction
from ..config.settings import ActionConfig


class SafetyChecker:
    """安全检查器"""

    def __init__(self, config: ActionConfig):
        self.config = config
        self._dangerous_keywords = config.forbidden_actions

        # 预定义的危险区域（屏幕角落，用于紧急停止）
        self._emergency_zones = [
            (0, 0, 50, 50),  # 左上角
        ]

    def is_mouse_action_safe(
        self,
        action: MouseAction,
        screen_width: int,
        screen_height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        检查鼠标操作是否安全

        Args:
            action: 鼠标操作
            screen_width: 屏幕宽度
            screen_height: 屏幕高度

        Returns:
            (是否安全, 警告信息)
        """
        # 检查坐标是否在屏幕范围内
        if action.position:
            x, y = action.position.x, action.position.y
            if not (0 <= x < screen_width and 0 <= y < screen_height):
                return False, f"坐标超出屏幕范围: ({x}, {y})"

        # 检查是否在禁止区域内
        for region in self.config.forbidden_regions:
            x, y, w, h = region
            forbidden_rect = Rectangle(x, y, w, h)
            if action.position and forbidden_rect.contains(action.position):
                return False, f"操作在禁止区域内: {region}"

        return True, None

    def is_keyboard_action_safe(self, action: KeyAction) -> Tuple[bool, Optional[str]]:
        """
        检查键盘操作是否安全

        Args:
            action: 键盘操作

        Returns:
            (是否安全, 警告信息)
        """
        # 检查危险关键词
        if action.action == 'type' and action.text:
            text_lower = action.text.lower()
            for keyword in self._dangerous_keywords:
                if keyword in text_lower:
                    return False, f"检测到危险关键词: {keyword}"

        # 检查危险快捷键
        if action.key:
            dangerous_shortcuts = [
                ('win', 'r'),  # 运行对话框
                ('win', 'l'),  # 锁定电脑
                ('alt', 'f4'),  # 关闭窗口
                ('ctrl', 'alt', 'delete'),  # 任务管理器
            ]

            if action.modifiers:
                keys = action.modifiers + [action.key]
                for shortcut in dangerous_shortcuts:
                    if all(k in keys for k in shortcut):
                        if not self.config.safety_enabled:
                            return True, None
                        return False, f"危险快捷键: {'+'.join(shortcut)}"

        return True, None

    def is_position_in_emergency_zone(self, x: int, y: int) -> bool:
        """
        检查位置是否在紧急停止区域

        Args:
            x, y: 坐标

        Returns:
            是否在紧急区域
        """
        for zone_x, zone_y, zone_w, zone_h in self._emergency_zones:
            if zone_x <= x < zone_x + zone_w and zone_y <= y < zone_y + zone_h:
                return True
        return False

    def add_forbidden_region(self, region: Tuple[int, int, int, int]):
        """添加禁止区域"""
        self.config.forbidden_regions.append(region)

    def remove_forbidden_region(self, region: Tuple[int, int, int, int]):
        """移除禁止区域"""
        if region in self.config.forbidden_regions:
            self.config.forbidden_regions.remove(region)

    def add_dangerous_keyword(self, keyword: str):
        """添加危险关键词"""
        if keyword not in self._dangerous_keywords:
            self._dangerous_keywords.append(keyword)

    def check_text_safety(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        检查文本是否包含危险内容

        Args:
            text: 要检查的文本

        Returns:
            (是否安全, 警告信息)
        """
        text_lower = text.lower()

        # 检查危险关键词
        for keyword in self._dangerous_keywords:
            if keyword in text_lower:
                return False, f"检测到危险关键词: {keyword}"

        # 检查是否尝试执行命令
        command_patterns = [
            r'^rm\s+-rf\s+',  # Linux 删除命令
            r'^del\s+',  # Windows 删除命令
            r'^format\s+',  # 格式化命令
            r'^shutdown\s+',  # 关机命令
            r'^reboot\s+',  # 重启命令
        ]

        for pattern in command_patterns:
            if re.match(pattern, text_lower):
                return False, f"检测到危险命令: {text}"

        return True, None

    def should_confirm_action(self, action_description: str) -> bool:
        """
        判断操作是否需要用户确认

        Args:
            action_description: 操作描述

        Returns:
            是否需要确认
        """
        if not self.config.confirm_dangerous_actions:
            return False

        dangerous_patterns = [
            r'删除',
            r'删除文件',
            r'格式化',
            r'关机',
            r'重启',
            r'清空',
            r'卸载',
            r'停止',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, action_description, re.IGNORECASE):
                return True

        return False


class OperationLogger:
    """操作日志记录器"""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self._operations: List[dict] = []

    def log_mouse_action(self, action: MouseAction, result: bool):
        """记录鼠标操作"""
        entry = {
            'type': 'mouse',
            'action': action.action,
            'button': action.button.value if action.button else None,
            'position': (action.position.x, action.position.y) if action.position else None,
            'success': result,
            'timestamp': self._get_timestamp()
        }
        self._operations.append(entry)
        self._write_to_log(entry)

    def log_keyboard_action(self, action: KeyAction, result: bool):
        """记录键盘操作"""
        entry = {
            'type': 'keyboard',
            'action': action.action,
            'key': action.key,
            'text': action.text if action.action == 'type' else None,
            'success': result,
            'timestamp': self._get_timestamp()
        }
        self._operations.append(entry)
        self._write_to_log(entry)

    def log_error(self, error: str):
        """记录错误"""
        entry = {
            'type': 'error',
            'message': error,
            'timestamp': self._get_timestamp()
        }
        self._operations.append(entry)
        self._write_to_log(entry)

    def get_recent_operations(self, count: int = 10) -> List[dict]:
        """获取最近的操作"""
        return self._operations[-count:]

    def clear_log(self):
        """清空日志"""
        self._operations.clear()

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _write_to_log(self, entry: dict):
        """写入日志文件"""
        if self.log_path:
            import json
            try:
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Error writing to log: {e}")
