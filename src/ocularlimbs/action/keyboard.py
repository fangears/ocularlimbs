"""
键盘控制模块
支持按键输入、文本输入、快捷键等操作
"""

import time
from typing import List, Optional, Union

import pyautogui

from ..core.types import KeyAction
from ..config.settings import ActionConfig


class KeyboardController:
    """键盘控制器"""

    def __init__(self, config: ActionConfig):
        self.config = config
        pyautogui.PAUSE = config.action_delay

    def press(self, key: str, duration: Optional[float] = None) -> None:
        """
        按下并释放按键

        Args:
            key: 按键名称（如 'a', 'enter', 'f1' 等）
            duration: 按住持续时间（秒）
        """
        if duration is None:
            duration = self.config.key_press_duration

        pyautogui.press(key)

    def press_key(self, key: str, press_duration: float = 0.1) -> None:
        """
        按住按键一段时间后释放

        Args:
            key: 按键名称
            press_duration: 按住持续时间
        """
        pyautogui.keyDown(key)
        time.sleep(press_duration)
        pyautogui.keyUp(key)

    def type_text(self, text: str, interval: Optional[float] = None) -> None:
        """
        输入文本

        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔（秒）
        """
        if interval is None:
            interval = self.config.typing_delay

        pyautogui.typewrite(text, interval=interval)

    def hotkey(self, *keys: str) -> None:
        """
        按下组合键（快捷键）

        Args:
            *keys: 按键列表（如 'ctrl', 'shift', 's'）

        Example:
            hotkey('ctrl', 'c')  # 复制
            hotkey('ctrl', 'v')  # 粘贴
            hotkey('alt', 'f4')  # 关闭窗口
        """
        pyautogui.hotkey(*keys)

    # ========================================================================
    # 常用快捷键
    # ========================================================================

    def copy(self) -> None:
        """复制 (Ctrl+C)"""
        self.hotkey('ctrl', 'c')

    def paste(self) -> None:
        """粘贴 (Ctrl+V)"""
        self.hotkey('ctrl', 'v')

    def cut(self) -> None:
        """剪切 (Ctrl+X)"""
        self.hotkey('ctrl', 'x')

    def select_all(self) -> None:
        """全选 (Ctrl+A)"""
        self.hotkey('ctrl', 'a')

    def save(self) -> None:
        """保存 (Ctrl+S)"""
        self.hotkey('ctrl', 's')

    def undo(self) -> None:
        """撤销 (Ctrl+Z)"""
        self.hotkey('ctrl', 'z')

    def redo(self) -> None:
        """重做 (Ctrl+Y 或 Ctrl+Shift+Z)"""
        self.hotkey('ctrl', 'y')

    def find(self) -> None:
        """查找 (Ctrl+F)"""
        self.hotkey('ctrl', 'f')

    def enter(self) -> None:
        """回车键"""
        self.press('enter')

    def tab(self) -> None:
        """Tab 键"""
        self.press('tab')

    def escape(self) -> None:
        """Escape 键"""
        self.press('esc')

    def delete(self) -> None:
        """Delete 键"""
        self.press('delete')

    def backspace(self, count: int = 1) -> None:
        """
        退格键

        Args:
            count: 按下次数
        """
        for _ in range(count):
            self.press('backspace')

    # ========================================================================
    # 功能键
    # ========================================================================

    def f1(self): self.press('f1')
    def f2(self): self.press('f2')
    def f3(self): self.press('f3')
    def f4(self): self.press('f4')
    def f5(self): self.press('f5')
    def f6(self): self.press('f6')
    def f7(self): self.press('f7')
    def f8(self): self.press('f8')
    def f9(self): self.press('f9')
    def f10(self): self.press('f10')
    def f11(self): self.press('f11')
    def f12(self): self.press('f12')

    # ========================================================================
    # 方向键
    # ========================================================================

    def up(self, count: int = 1):
        """向上箭头"""
        for _ in range(count):
            self.press('up')

    def down(self, count: int = 1):
        """向下箭头"""
        for _ in range(count):
            self.press('down')

    def left(self, count: int = 1):
        """向左箭头"""
        for _ in range(count):
            self.press('left')

    def right(self, count: int = 1):
        """向右箭头"""
        for _ in range(count):
            self.press('right')

    def page_up(self):
        """Page Up"""
        self.press('pageup')

    def page_down(self):
        """Page Down"""
        self.press('pagedown')

    def home(self):
        """Home"""
        self.press('home')

    def end(self):
        """End"""
        self.press('end')

    # ========================================================================
    # 高级操作
    # ========================================================================

    def clear_input(self) -> None:
        """清除输入框内容（Ctrl+A 然后 Delete）"""
        self.select_all()
        time.sleep(0.05)
        self.delete()

    def replace_text(self, old_text: str, new_text: str) -> None:
        """
        替换选中的文本

        Args:
            old_text: 旧文本（用于验证）
            new_text: 新文本
        """
        # 确保已选中
        self.copy()
        time.sleep(0.1)

        # 输入新文本
        self.type_text(new_text)

    def input_with_clear(self, text: str) -> None:
        """清除后输入文本"""
        self.clear_input()
        time.sleep(0.05)
        self.type_text(text)

    def execute_action(self, action: KeyAction) -> None:
        """
        执行键盘操作

        Args:
            action: KeyAction 对象
        """
        if action.action == 'press':
            if action.modifiers:
                # 有修饰键，使用 hotkey
                keys = action.modifiers + ([action.key] if action.key else [])
                self.hotkey(*keys)
            else:
                self.press(action.key)

        elif action.action == 'type':
            if action.text:
                self.type_text(action.text)

        elif action.action == 'release':
            # 独立释放操作（较少使用）
            pyautogui.keyUp(action.key or '')

    # ========================================================================
    # 特殊操作
    # ========================================================================

    def screenshot(self) -> None:
        """截图 (Win+Shift+S)"""
        self.hotkey('win', 'shift', 's')

    def lock_computer(self) -> None:
        """锁定电脑 (Win+L)"""
        self.hotkey('win', 'l')

    def open_task_manager(self) -> None:
        """打开任务管理器 (Ctrl+Shift+Esc)"""
        self.hotkey('ctrl', 'shift', 'esc')

    def show_run_dialog(self) -> None:
        """显示运行对话框 (Win+R)"""
        self.hotkey('win', 'r')

    def open_explorer(self) -> None:
        """打开资源管理器 (Win+E)"""
        self.hotkey('win', 'e')

    def switch_window(self) -> None:
        """切换窗口 (Alt+Tab)"""
        self.hotkey('alt', 'tab')

    def close_window(self) -> None:
        """关闭窗口 (Alt+F4)"""
        self.hotkey('alt', 'f4')

    def minimize_window(self) -> None:
        """最小化窗口 (Win+Down)"""
        self.hotkey('win', 'down')

    def maximize_window(self) -> None:
        """最大化窗口 (Win+Up)"""
        self.hotkey('win', 'up')
