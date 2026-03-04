"""
操作模块 - 统一接口
提供鼠标、键盘、窗口控制和安全保护功能
"""

from typing import Optional, Tuple, List

from .mouse import MouseController
from .keyboard import KeyboardController
from .window import WindowController
from .safety import SafetyChecker, OperationLogger

from ..core.types import (
    Point, Rectangle, MouseButton, MouseAction, KeyAction, UIElement, TextRegion
)
from ..config.settings import ActionConfig


class ActionModule:
    """操作模块 - 统一接口"""

    def __init__(self, config: ActionConfig):
        self.config = config

        # 初始化子模块
        self.mouse = MouseController(config)
        self.keyboard = KeyboardController(config)
        self.window = WindowController(config)
        self.safety = SafetyChecker(config)

        # 日志记录器
        self.logger = OperationLogger(log_path=config.log_file if config.log_file else None)

        # 获取屏幕尺寸
        self.screen_width, self.screen_height = self.mouse.screen_width, self.mouse.screen_height

    # =========================================================================
    # 鼠标操作（快捷方式）
    # =========================================================================

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: MouseButton = MouseButton.LEFT
    ) -> bool:
        """点击"""
        try:
            action = MouseAction(action='click', button=button, position=Point(x, y) if x is not None else None)

            # 安全检查
            if x is not None and y is not None:
                is_safe, warning = self.safety.is_mouse_action_safe(action, self.screen_width, self.screen_height)
                if not is_safe:
                    self.logger.log_error(f"安全检查失败: {warning}")
                    raise ValueError(warning)

            self.mouse.click(x, y, button)
            self.logger.log_mouse_action(action, True)
            return True
        except Exception as e:
            self.logger.log_error(f"点击失败: {e}")
            return False

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """双击"""
        try:
            self.mouse.double_click(x, y)
            return True
        except Exception as e:
            self.logger.log_error(f"双击失败: {e}")
            return False

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """右键点击"""
        try:
            self.mouse.right_click(x, y)
            return True
        except Exception as e:
            self.logger.log_error(f"右键点击失败: {e}")
            return False

    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5) -> bool:
        """拖拽"""
        try:
            self.mouse.drag(from_x, from_y, to_x, to_y, duration)
            return True
        except Exception as e:
            self.logger.log_error(f"拖拽失败: {e}")
            return False

    def scroll(self, amount: int) -> bool:
        """滚动"""
        try:
            self.mouse.scroll(amount)
            return True
        except Exception as e:
            self.logger.log_error(f"滚动失败: {e}")
            return False

    def move_to(self, x: int, y: int, duration: float = 0.5) -> bool:
        """移动到"""
        try:
            self.mouse.move_to(x, y, duration)
            return True
        except Exception as e:
            self.logger.log_error(f"移动失败: {e}")
            return False

    # =========================================================================
    # 键盘操作（快捷方式）
    # =========================================================================

    def type_text(self, text: str) -> bool:
        """输入文本"""
        try:
            # 安全检查
            is_safe, warning = self.safety.check_text_safety(text)
            if not is_safe:
                self.logger.log_error(f"安全检查失败: {warning}")
                raise ValueError(warning)

            self.keyboard.type_text(text)
            action = KeyAction(action='type', text=text)
            self.logger.log_keyboard_action(action, True)
            return True
        except Exception as e:
            self.logger.log_error(f"输入文本失败: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """按下按键"""
        try:
            self.keyboard.press(key)
            return True
        except Exception as e:
            self.logger.log_error(f"按键失败: {e}")
            return False

    def hotkey(self, *keys: str) -> bool:
        """组合键"""
        try:
            self.keyboard.hotkey(*keys)
            return True
        except Exception as e:
            self.logger.log_error(f"组合键失败: {e}")
            return False

    # =========================================================================
    # 窗口操作（快捷方式）
    # =========================================================================

    def activate_window(self, title: str) -> bool:
        """激活窗口"""
        try:
            return self.window.activate_by_title(title)
        except Exception as e:
            self.logger.log_error(f"激活窗口失败: {e}")
            return False

    def find_window(self, title: str):
        """查找窗口"""
        return self.window.find_window(title)

    def list_windows(self) -> List[str]:
        """列出所有窗口"""
        return self.window.list_windows()

    # =========================================================================
    # 高级操作
    # =========================================================================

    def click_element(self, element: UIElement) -> bool:
        """点击 UI 元素"""
        if not element.bbox:
            return False

        center = element.bbox.center
        return self.click(center.x, center.y)

    def click_text_region(self, text_region: TextRegion) -> bool:
        """点击文字区域"""
        if not text_region.bbox:
            return False

        center = text_region.bbox.center
        return self.click(center.x, center.y)

    def click_button_by_label(self, label: str, elements: List[UIElement]) -> bool:
        """根据标签点击按钮"""
        for element in elements:
            if element.type == 'button' and element.label and label.lower() in element.label.lower():
                return self.click_element(element)
        return False

    def input_in_field(
        self,
        input_element: UIElement,
        text: str,
        clear_first: bool = True
    ) -> bool:
        """在输入框中输入文本"""
        if not input_element.bbox:
            return False

        # 点击输入框
        if not self.click_element(input_element):
            return False

        # 清空现有内容
        if clear_first:
            import time
            time.sleep(0.1)
            self.keyboard.select_all()
            time.sleep(0.05)
            self.keyboard.press('delete')
            time.sleep(0.05)

        # 输入文本
        return self.type_text(text)

    def wait_and_click(
        self,
        text: str,
        vision_module,
        timeout: float = 10.0,
        check_interval: float = 0.5
    ) -> bool:
        """
        等待文字出现并点击

        Args:
            text: 要等待的文字
            vision_module: 视觉模块
            timeout: 超时时间
            check_interval: 检查间隔
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            # 观察屏幕
            observation = vision_module.observe()

            # 查找文字
            text_region = vision_module.find_text(text)

            if text_region:
                # 点击文字区域
                return self.click_text_region(text_region)

            time.sleep(check_interval)

        return False

    # =========================================================================
    # 组合操作
    # =========================================================================

    def copy_to_clipboard(self) -> bool:
        """复制到剪贴板 (Ctrl+C)"""
        return self.hotkey('ctrl', 'c')

    def paste_from_clipboard(self) -> bool:
        """从剪贴板粘贴 (Ctrl+V)"""
        return self.hotkey('ctrl', 'v')

    def save_file(self) -> bool:
        """保存文件 (Ctrl+S)"""
        return self.hotkey('ctrl', 's')

    def open_file(self) -> bool:
        """打开文件 (Ctrl+O)"""
        return self.hotkey('ctrl', 'o')

    def new_file(self) -> bool:
        """新建文件 (Ctrl+N)"""
        return self.hotkey('ctrl', 'n')

    def close_current_window(self) -> bool:
        """关闭当前窗口 (Alt+F4)"""
        return self.hotkey('alt', 'f4')

    def switch_tab(self) -> bool:
        """切换标签 (Ctrl+Tab)"""
        return self.hotkey('ctrl', 'tab')

    # =========================================================================
    # 工具方法
    # =========================================================================

    def get_mouse_position(self) -> Point:
        """获取鼠标位置"""
        return self.mouse.get_position()

    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        return self.screen_width, self.screen_height

    def get_operation_log(self, count: int = 10) -> List[dict]:
        """获取操作日志"""
        return self.logger.get_recent_operations(count)

    def clear_log(self):
        """清空日志"""
        self.logger.clear_log()
