"""
窗口管理模块
支持窗口激活、移动、调整大小等操作
"""

import time
from typing import List, Optional, Tuple

try:
    import pygetwindow as gw
    GETWINDOW_AVAILABLE = True
except ImportError:
    GETWINDOW_AVAILABLE = False

from ..core.types import Rectangle, Point
from ..config.settings import ActionConfig


class WindowController:
    """窗口控制器"""

    def __init__(self, config: ActionConfig):
        self.config = config

        if not GETWINDOW_AVAILABLE:
            print("Warning: pygetwindow not available, window operations limited")

    def get_all_windows(self) -> List:
        """获取所有窗口列表"""
        if not GETWINDOW_AVAILABLE:
            return []

        try:
            return gw.getAllWindows()
        except Exception as e:
            print(f"Error getting windows: {e}")
            return []

    def get_active_window(self):
        """获取当前活动窗口"""
        if not GETWINDOW_AVAILABLE:
            return None

        try:
            return gw.getActiveWindow()
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None

    def find_window(self, title: str, exact: bool = False) -> Optional:
        """
        查找窗口

        Args:
            title: 窗口标题
            exact: 是否精确匹配

        Returns:
            窗口对象，如果没找到返回 None
        """
        if not GETWINDOW_AVAILABLE:
            return None

        try:
            if exact:
                windows = gw.getWindowsWithTitle(title)
                return windows[0] if windows else None
            else:
                # 模糊匹配
                all_windows = gw.getAllWindows()
                for window in all_windows:
                    if title.lower() in window.title.lower():
                        return window
                return None
        except Exception as e:
            print(f"Error finding window: {e}")
            return None

    def find_windows_by_pattern(self, pattern: str) -> List:
        """根据模式查找窗口"""
        import re
        if not GETWINDOW_AVAILABLE:
            return []

        try:
            all_windows = gw.getAllWindows()
            regex = re.compile(pattern, re.IGNORECASE)
            return [w for w in all_windows if regex.search(w.title)]
        except Exception as e:
            print(f"Error finding windows by pattern: {e}")
            return []

    def activate(self, window) -> bool:
        """
        激活窗口（前置）

        Args:
            window: 窗口对象

        Returns:
            是否成功
        """
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'activate'):
                window.activate()
                return True
            return False
        except Exception as e:
            print(f"Error activating window: {e}")
            return False

    def activate_by_title(self, title: str, exact: bool = False) -> bool:
        """
        通过标题激活窗口

        Args:
            title: 窗口标题
            exact: 是否精确匹配

        Returns:
            是否成功
        """
        window = self.find_window(title, exact)
        if window:
            return self.activate(window)
        return False

    def close(self, window) -> bool:
        """关闭窗口"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'close'):
                window.close()
                return True
            return False
        except Exception as e:
            print(f"Error closing window: {e}")
            return False

    def minimize(self, window) -> bool:
        """最小化窗口"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'minimize'):
                window.minimize()
                return True
            return False
        except Exception as e:
            print(f"Error minimizing window: {e}")
            return False

    def maximize(self, window) -> bool:
        """最大化窗口"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'maximize'):
                window.maximize()
                return True
            return False
        except Exception as e:
            print(f"Error maximizing window: {e}")
            return False

    def restore(self, window) -> bool:
        """恢复窗口（从最小化）"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'restore'):
                window.restore()
                return True
            return False
        except Exception as e:
            print(f"Error restoring window: {e}")
            return False

    def move(self, window, x: int, y: int) -> bool:
        """移动窗口"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'move'):
                window.moveTo(x, y)
                return True
            return False
        except Exception as e:
            print(f"Error moving window: {e}")
            return False

    def resize(self, window, width: int, height: int) -> bool:
        """调整窗口大小"""
        if not GETWINDOW_AVAILABLE or window is None:
            return False

        try:
            if hasattr(window, 'resize'):
                window.resizeTo(width, height)
                return True
            return False
        except Exception as e:
            print(f"Error resizing window: {e}")
            return False

    def get_bounds(self, window) -> Optional[Rectangle]:
        """
        获取窗口边界

        Returns:
            Rectangle 对象，如果获取失败返回 None
        """
        if not GETWINDOW_AVAILABLE or window is None:
            return None

        try:
            if hasattr(window, 'left') and hasattr(window, 'top') and \
               hasattr(window, 'width') and hasattr(window, 'height'):
                return Rectangle(
                    x=window.left,
                    y=window.top,
                    width=window.width,
                    height=window.height
                )
            return None
        except Exception as e:
            print(f"Error getting window bounds: {e}")
            return None

    def get_center(self, window) -> Optional[Point]:
        """获取窗口中心点"""
        bounds = self.get_bounds(window)
        if bounds:
            return bounds.center
        return None

    def bring_to_front(self, title: str) -> bool:
        """
        将窗口带到最前面

        Args:
            title: 窗口标题

        Returns:
            是否成功
        """
        window = self.find_window(title)
        if window:
            return self.activate(window)
        return False

    def list_windows(self) -> List[str]:
        """列出所有窗口标题"""
        windows = self.get_all_windows()
        return [w.title for w in windows if w.title]

    def wait_for_window(
        self,
        title: str,
        timeout: float = 10.0,
        check_interval: float = 0.5
    ) -> Optional:
        """
        等待窗口出现

        Args:
            title: 窗口标题
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            窗口对象，如果超时返回 None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            window = self.find_window(title)
            if window:
                return window
            time.sleep(check_interval)

        return None

    def wait_for_window_close(
        self,
        title: str,
        timeout: float = 10.0,
        check_interval: float = 0.5
    ) -> bool:
        """
        等待窗口关闭

        Args:
            title: 窗口标题
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            是否关闭
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            window = self.find_window(title)
            if not window:
                return True
            time.sleep(check_interval)

        return False
