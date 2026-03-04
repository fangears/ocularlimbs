"""
屏幕捕获模块 - 带压缩选项
支持 PNG、JPEG、WebP 格式
"""

import mss
import mss.tools
from PIL import Image
import io
import time
from typing import Optional, Literal
from ..core.types import ScreenCapture
from ..config.settings import VisionConfig


class ScreenCaptureCompressed:
    """支持多种压缩格式的屏幕捕获器"""

    def __init__(self, config: VisionConfig):
        self.config = config
        self._capture = mss.mss()
        self.monitors = self._capture.monitors
        self.primary_monitor = self.monitors[1] if len(self.monitors) > 1 else self.monitors[0]

    def capture_full_screen(
        self,
        screen_index: int = 0,
        format: Literal['png', 'jpeg', 'webp'] = 'png',
        quality: int = 95
    ) -> ScreenCapture:
        """
        捕获完整屏幕

        Args:
            screen_index: 显示器索引
            format: 图片格式 ('png', 'jpeg', 'webp')
            quality: 压缩质量 (1-100, 仅对 jpeg/webp 有效)

        Returns:
            ScreenCapture 对象
        """
        monitor = self._get_monitor(screen_index)
        screenshot = self._capture.grab(monitor)

        # 转换为 PIL Image
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

        # 根据格式压缩
        buffer = io.BytesIO()

        if format == 'png':
            # PNG 无损压缩
            img.save(buffer, format='PNG', optimize=True)

        elif format == 'jpeg':
            # JPEG 有损压缩
            img.save(buffer, format='JPEG', quality=quality, optimize=True)

        elif format == 'webp':
            # WebP 现代格式
            img.save(buffer, format='WebP', quality=quality, method=6)

        img_bytes = buffer.getvalue()

        return ScreenCapture(
            image=img_bytes,
            timestamp=time.time(),
            screen_index=screen_index,
            width=screenshot.width,
            height=screenshot.height
        )

    def capture_and_save(
        self,
        output_path: str,
        format: Literal['png', 'jpeg', 'webp'] = 'png',
        quality: int = 95,
        screen_index: int = 0
    ):
        """
        捕获并直接保存到文件

        Args:
            output_path: 输出文件路径
            format: 图片格式
            quality: 压缩质量
            screen_index: 显示器索引
        """
        capture = self.capture_full_screen(screen_index, format, quality)

        with open(output_path, 'wb') as f:
            f.write(capture.image)

        return capture

    def get_compressed_size(
        self,
        format: Literal['png', 'jpeg', 'webp'],
        quality: int = 95,
        screen_index: int = 0
    ) -> dict:
        """
        比较不同压缩格式的大小

        Returns:
            格式和大小信息字典
        """
        results = {}

        for fmt in ['png', 'jpeg', 'webp']:
            capture = self.capture_full_screen(screen_index, fmt, quality)
            results[fmt] = {
                'size': len(capture.image),
                'size_kb': len(capture.image) / 1024,
                'size_mb': len(capture.image) / (1024 * 1024)
            }

        return results

    def auto_select_format(
        self,
        max_size_kb: int = 500,
        screen_index: int = 0
    ) -> tuple:
        """
        自动选择最适合的格式

        Args:
            max_size_kb: 最大允许大小（KB）
            screen_index: 显示器索引

        Returns:
            (format, quality) 元组
        """
        # 先尝试 PNG
        png_capture = self.capture_full_screen(screen_index, 'png', 95)
        png_size_kb = len(png_capture.image) / 1024

        if png_size_kb <= max_size_kb:
            return ('png', 95)  # PNG 符合要求，使用无损

        # PNG 太大，尝试 JPEG
        for quality in [95, 85, 75, 65]:
            jpeg_capture = self.capture_full_screen(screen_index, 'jpeg', quality)
            jpeg_size_kb = len(jpeg_capture.image) / 1024

            if jpeg_size_kb <= max_size_kb:
                return ('jpeg', quality)

        # 最后回退到低质量 JPEG
        return ('jpeg', 50)

    def _get_monitor(self, screen_index: int) -> dict:
        """获取显示器信息"""
        idx = screen_index + 1
        if idx >= len(self.monitors):
            raise IndexError(f"显示器索引 {screen_index} 超出范围")
        return self.monitors[idx]


# ============================================================================
# 使用示例
# ============================================================================

def compare_compression():
    """比较不同压缩格式"""
    from ..config.settings import VisionConfig

    config = VisionConfig()
    capturer = ScreenCaptureCompressed(config)

    print("压缩格式对比测试\n")
    print("="*60)

    # 比较不同格式
    results = capturer.get_compressed_size('jpeg', 85)

    for fmt, info in results.items():
        print(f"{fmt:8s}: {info['size_kb']:7.1f} KB  ({info['size_mb']:5.2f} MB)")

    # 计算压缩比
    png_size = results['png']['size']
    jpeg_size = results['jpeg']['size']
    webp_size = results['webp']['size']

    print("\n压缩比（相对于 PNG）:")
    print(f"  JPEG: {jpeg_size/png_size*100:.1f}%")
    print(f"  WebP: {webp_size/png_size*100:.1f}%")

    # 自动选择
    format, quality = capturer.auto_select_format(max_size_kb=500)
    print(f"\n自动选择（最大500KB）: {format}, 质量={quality}")

    print("="*60)


if __name__ == '__main__':
    compare_compression()
