"""
智能图片压缩模块
在保留 OCR 识别能力的前提下，优化图片大小和速度
"""

import mss
import mss.tools
from PIL import Image, ImageEnhance
import io
import time
from typing import Optional, Literal, Tuple, List
from enum import Enum
import numpy as np


class CompressionPreset(Enum):
    """压缩预设"""
    ULTRA_FAST = "ultra_fast"      # 极速：最小体积，最快速度
    FAST = "fast"                  # 快速：平衡速度和质量
    BALANCED = "balanced"          # 平衡：默认选择
    QUALITY = "quality"            # 质量：优先 OCR 准确性
    ARCHIVAL = "archival"          # 存档：无损保存


class SmartCompressor:
    """智能压缩器 - 针对 OCR 优化"""

    # 压缩预设配置
    PRESETS = {
        CompressionPreset.ULTRA_FAST: {
            'format': 'jpeg',
            'quality': 65,
            'max_resolution': (1280, 720),
            'enhance_contrast': True,
            'convert_grayscale': True,  # 灰度更小
            'description': '极速模式 - 适合实时监控'
        },
        CompressionPreset.FAST: {
            'format': 'jpeg',
            'quality': 75,
            'max_resolution': (1600, 900),
            'enhance_contrast': True,
            'convert_grayscale': True,
            'description': '快速模式 - 适合快速识别'
        },
        CompressionPreset.BALANCED: {
            'format': 'jpeg',
            'quality': 85,
            'max_resolution': (1920, 1080),
            'enhance_contrast': False,
            'convert_grayscale': False,
            'description': '平衡模式 - 默认推荐'
        },
        CompressionPreset.QUALITY: {
            'format': 'jpeg',
            'quality': 92,
            'max_resolution': (2560, 1440),
            'enhance_contrast': False,
            'convert_grayscale': False,
            'description': '质量模式 - 优先准确率'
        },
        CompressionPreset.ARCHIVAL: {
            'format': 'png',
            'quality': 100,
            'max_resolution': None,  # 原始分辨率
            'enhance_contrast': False,
            'convert_grayscale': False,
            'description': '存档模式 - 无损保存'
        }
    }

    def __init__(self):
        self._capture = mss.mss()
        self.stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_time': 0,
            'compression_ratio': 0
        }

    def capture_for_ocr(
        self,
        preset: CompressionPreset = CompressionPreset.BALANCED,
        screen_index: int = 0,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Tuple[bytes, dict]:
        """
        为 OCR 捕获并优化图片

        Args:
            preset: 压缩预设
            screen_index: 屏幕索引
            region: 指定区域 (x, y, w, h)，None 表示全屏

        Returns:
            (压缩后的图片数据, 元数据字典)
        """
        start_time = time.time()
        config = self.PRESETS[preset]

        # 1. 捕获屏幕
        if region:
            capture = self._capture_region(region, screen_index)
        else:
            capture = self._capture_full_screen(screen_index)

        img = Image.frombytes('RGB', capture.size, capture.rgb)
        original_size = len(mss.tools.to_png(capture.rgb, capture.size))
        self.stats['original_size'] = original_size

        # 2. 预处理 - 优化 OCR 效果
        img = self._preprocess_for_ocr(img, config)

        # 3. 压缩
        compressed = self._compress(img, config)
        self.stats['compressed_size'] = len(compressed)

        # 4. 计算统计信息
        self.stats['compression_time'] = time.time() - start_time
        self.stats['compression_ratio'] = len(compressed) / original_size

        # 5. 返回结果和元数据
        metadata = {
            'preset': preset.value,
            'format': config['format'],
            'quality': config['quality'],
            'original_size': original_size,
            'compressed_size': len(compressed),
            'compression_ratio': self.stats['compression_ratio'],
            'size_reduction': (1 - self.stats['compression_ratio']) * 100,
            'processing_time': self.stats['compression_time'],
            'resolution': img.size,
            'description': config['description']
        }

        return compressed, metadata

    def _capture_full_screen(self, screen_index: int):
        """捕获全屏"""
        monitor = self._get_monitor(screen_index)
        return self._capture.grab(monitor)

    def _capture_region(self, region: Tuple[int, int, int, int], screen_index: int):
        """捕获指定区域"""
        x, y, w, h = region
        monitor = self._get_monitor(screen_index)

        capture_dict = {
            "left": monitor["left"] + x,
            "top": monitor["top"] + y,
            "width": w,
            "height": h
        }
        return self._capture.grab(capture_dict)

    def _preprocess_for_ocr(self, img: Image, config: dict) -> Image:
        """预处理图片以优化 OCR 效果"""

        # 1. 调整分辨率
        if config['max_resolution']:
            img = self._resize_to_max(img, config['max_resolution'])

        # 2. 增强对比度（提升 OCR 准确率）
        if config['enhance_contrast']:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # 增加 20% 对比度

            # 增加锐化
            sharpener = ImageEnhance.Sharpness(img)
            img = sharpener.enhance(1.1)

        # 3. 转换为灰度（减少 2/3 大小，对 OCR 影响很小）
        if config['convert_grayscale']:
            img = img.convert('L')

        return img

    def _compress(self, img: Image, config: dict) -> bytes:
        """压缩图片"""
        buffer = io.BytesIO()

        fmt = config['format']
        quality = config['quality']

        if fmt == 'png':
            img.save(buffer, format='PNG', optimize=True)
        elif fmt == 'jpeg':
            # 如果是灰度图，保存为灰度 JPEG
            if img.mode == 'L':
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                img.save(buffer, format='JPEG', quality=quality, optimize=True, progressive=True)
        elif fmt == 'webp':
            img.save(buffer, format='WebP', quality=quality, method=6)

        return buffer.getvalue()

    def _resize_to_max(self, img: Image, max_size: Tuple[int, int]) -> Image:
        """调整图片到最大尺寸，保持宽高比"""
        max_w, max_h = max_size
        w, h = img.size

        # 如果已经小于最大尺寸，不调整
        if w <= max_w and h <= max_h:
            return img

        # 计算缩放比例
        scale_w = max_w / w
        scale_h = max_h / h
        scale = min(scale_w, scale_h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        # 使用高质量缩放
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def _get_monitor(self, screen_index: int) -> dict:
        """获取显示器信息"""
        monitors = self._capture.monitors
        idx = screen_index + 1
        if idx >= len(monitors):
            raise IndexError(f"显示器索引 {screen_index} 超出范围")
        return monitors[idx]

    def compare_presets(
        self,
        screen_index: int = 0
    ) -> List[dict]:
        """
        对比所有压缩预设的效果

        Returns:
            每个预设的元数据列表
        """
        results = []

        print("正在测试所有压缩预设...\n")

        for preset in CompressionPreset:
            try:
                compressed, metadata = self.capture_for_ocr(preset, screen_index)
                results.append(metadata)

                # 打印结果
                print(f"[{preset.value.upper()}]")
                print(f"  格式: {metadata['format']}")
                print(f"  质量: {metadata['quality']}")
                print(f"  分辨率: {metadata['resolution'][0]}x{metadata['resolution'][1]}")
                print(f"  大小: {metadata['compressed_size']/1024:.1f} KB")
                print(f"  压缩率: {metadata['compression_ratio']*100:.1f}%")
                print(f"  减少: {metadata['size_reduction']:.1f}%")
                print(f"  耗时: {metadata['processing_time']*1000:.1f} ms")
                print(f"  说明: {metadata['description']}")
                print()

            except Exception as e:
                print(f"[{preset.value.upper()}] 失败: {e}\n")

        return results

    def auto_select_preset(
        self,
        max_size_kb: float = 200,
        min_quality: float = 0.7
    ) -> CompressionPreset:
        """
        自动选择最适合的压缩预设

        Args:
            max_size_kb: 最大允许大小（KB）
            min_quality: 最小质量要求（0-1）

        Returns:
            推荐的压缩预设
        """
        # 按速度优先级测试
        presets_to_try = [
            CompressionPreset.ULTRA_FAST,
            CompressionPreset.FAST,
            CompressionPreset.BALANCED,
            CompressionPreset.QUALITY
        ]

        for preset in presets_to_try:
            _, metadata = self.capture_for_ocr(preset)
            size_kb = metadata['compressed_size'] / 1024

            if size_kb <= max_size_kb:
                return preset

        # 如果都太大，返回最小的
        return CompressionPreset.ULTRA_FAST

    def get_stats(self) -> dict:
        """获取压缩统计信息"""
        return self.stats.copy()


class AdaptiveOCRCompressor:
    """自适应 OCR 压缩器 - 根据内容动态调整"""

    def __init__(self):
        self.compressor = SmartCompressor()
        self.content_history = []

    def capture_with_analysis(
        self,
        screen_index: int = 0
    ) -> Tuple[bytes, dict, str]:
        """
        分析内容并选择最佳压缩策略

        Returns:
            (压缩图片, 元数据, 推荐原因)
        """
        # 先用快速模式捕获
        compressed_fast, meta_fast = self.compressor.capture_for_ocr(
            CompressionPreset.FAST, screen_index
        )

        # 分析内容复杂度
        complexity = self._analyze_complexity(compressed_fast)

        # 根据复杂度选择预设
        if complexity == 'simple':
            preset = CompressionPreset.ULTRA_FAST
            reason = "内容简单，使用极速模式"
        elif complexity == 'medium':
            preset = CompressionPreset.FAST
            reason = "内容中等，使用快速模式"
        elif complexity == 'complex':
            preset = CompressionPreset.BALANCED
            reason = "内容复杂，使用平衡模式"
        else:
            preset = CompressionPreset.QUALITY
            reason = "内容很复杂，使用质量模式"

        # 使用选定预设重新捕获
        compressed, metadata = self.compressor.capture_for_ocr(preset, screen_index)
        metadata['reason'] = reason
        metadata['complexity'] = complexity

        return compressed, metadata, reason

    def _analyze_complexity(self, image_data: bytes) -> str:
        """分析图片复杂度"""
        try:
            img = Image.open(io.BytesIO(image_data))

            # 转换为 numpy 数组
            arr = np.array(img)

            # 计算边缘密度（简单指标）
            if len(arr.shape) == 3:
                gray = np.mean(arr, axis=2)
            else:
                gray = arr

            # 计算标准差作为复杂度指标
            std = np.std(gray)

            if std < 30:
                return 'simple'
            elif std < 60:
                return 'medium'
            elif std < 90:
                return 'complex'
            else:
                return 'very_complex'

        except Exception as e:
            return 'medium'  # 默认中等复杂度


# ============================================================================
# 便捷函数
# ============================================================================

def quick_capture(preset: str = 'balanced') -> Tuple[bytes, dict]:
    """
    快速捕获

    Args:
        preset: 预设名称 ('ultra_fast', 'fast', 'balanced', 'quality', 'archival')

    Returns:
        (图片数据, 元数据)
    """
    compressor = SmartCompressor()
    preset_enum = CompressionPreset(preset)
    return compressor.capture_for_ocr(preset_enum)


def auto_capture(max_size_kb: float = 200) -> Tuple[bytes, dict]:
    """自动选择最佳压缩并捕获"""
    compressor = SmartCompressor()
    preset = compressor.auto_select_preset(max_size_kb=max_size_kb)
    return compressor.capture_for_ocr(preset)
