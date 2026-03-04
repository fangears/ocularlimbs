"""
屏幕捕获模块
支持全屏、区域、多显示器捕获
"""

import mss
import mss.tools
from PIL import Image
import io
import time
from typing import Optional, Tuple, List
from ..core.types import ScreenCapture, Point, Rectangle
from ..config.settings import VisionConfig


class ScreenCapture:
    """屏幕捕获器"""

    def __init__(self, config: VisionConfig):
        self.config = config
        self._capture = mss.mss()

        # 获取显示器信息
        self.monitors = self._capture.monitors
        self.primary_monitor = self.monitors[1] if len(self.monitors) > 1 else self.monitors[0]

    def capture_full_screen(self, screen_index: int = 0) -> ScreenCapture:
        """
        捕获完整屏幕

        Args:
            screen_index: 显示器索引（0=主显示器）

        Returns:
            ScreenCapture 对象
        """
        monitor = self._get_monitor(screen_index)

        # 捕获屏幕
        screenshot = self._capture.grab(monitor)

        # 转换为 PNG
        img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

        return ScreenCapture(
            image=img_bytes,
            timestamp=time.time(),
            screen_index=screen_index,
            width=screenshot.width,
            height=screenshot.height
        )

    def capture_region(self, region: Rectangle, screen_index: int = 0) -> ScreenCapture:
        """
        捕获屏幕指定区域

        Args:
            region: 要捕获的区域
            screen_index: 显示器索引

        Returns:
            ScreenCapture 对象
        """
        monitor = self._get_monitor(screen_index)

        # 计算捕获区域
        capture_dict = {
            "left": monitor["left"] + region.x,
            "top": monitor["top"] + region.y,
            "width": region.width,
            "height": region.height
        }

        # 捕获
        screenshot = self._capture.grab(capture_dict)
        img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

        return ScreenCapture(
            image=img_bytes,
            timestamp=time.time(),
            screen_index=screen_index,
            width=screenshot.width,
            height=screenshot.height
        )

    def capture_all_screens(self) -> List[ScreenCapture]:
        """
        捕获所有显示器

        Returns:
            所有屏幕的捕获列表
        """
        captures = []
        for i in range(len(self.monitors) - 1):  # 排除第一个（虚拟监视器）
            captures.append(self.capture_full_screen(i))
        return captures

    def capture_to_pil(self, screen_index: int = 0) -> Image.Image:
        """
        捕获屏幕并返回 PIL Image

        Args:
            screen_index: 显示器索引

        Returns:
            PIL Image 对象
        """
        capture = self.capture_full_screen(screen_index)
        return Image.open(io.BytesIO(capture.image))

    def get_screen_size(self, screen_index: int = 0) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        monitor = self._get_monitor(screen_index)
        return monitor["width"], monitor["height"]

    def get_all_screen_sizes(self) -> List[Tuple[int, int]]:
        """获取所有显示器尺寸"""
        sizes = []
        for i in range(len(self.monitors) - 1):
            sizes.append(self.get_screen_size(i))
        return sizes

    def _get_monitor(self, screen_index: int) -> dict:
        """获取显示器信息"""
        # mss 的 monitors[0] 是所有显示器的组合，从 [1] 开始是单个显示器
        idx = screen_index + 1
        if idx >= len(self.monitors):
            raise IndexError(f"显示器索引 {screen_index} 超出范围")
        return self.monitors[idx]


class CaptureCache:
    """捕获缓存，避免重复捕获相同内容"""

    def __init__(self, ttl: float = 1.0):
        self.ttl = ttl  # 缓存存活时间（秒）
        self._cache: dict = {}

    def get(self, key: str) -> Optional[ScreenCapture]:
        """获取缓存的捕获"""
        if key in self._cache:
            capture, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return capture
            else:
                del self._cache[key]
        return None

    def set(self, key: str, capture: ScreenCapture):
        """设置缓存"""
        self._cache[key] = (capture, time.time())

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def cleanup(self):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            k for k, (_, ts) in self._cache.items()
            if now - ts >= self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]
