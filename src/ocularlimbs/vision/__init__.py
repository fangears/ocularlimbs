"""
视觉模块 - 统一接口
提供屏幕捕获、OCR、UI解析、差异检测功能
"""

from typing import List, Optional, Tuple
import io
from PIL import Image

from .capture import ScreenCaptureDevice
from .ocr import OCRRecognizer
from .ui_parser import UIElementDetector, VisualDebugger
from .diff_detector import DiffDetector, MotionDetector
from ..core.types import (
    ScreenCapture, TextRegion, UIElement, DiffRegion,
    Rectangle, Point
)
from ..config.settings import VisionConfig


class VisionModule:
    """视觉模块 - 统一接口"""

    def __init__(self, config: VisionConfig):
        self.config = config

        # 初始化子模块
        self.capture = ScreenCaptureDevice(config)

        # OCR 可选初始化（静默模式，不输出调试信息以避免干扰 MCP 协议）
        try:
            self.ocr = OCRRecognizer(config)
            if not self.ocr.is_available:
                # OCR 不可用，静默继续
                pass
        except Exception as e:
            # OCR 初始化失败，静默设置 None
            self.ocr = None

        self.ui_detector = UIElementDetector(config)
        self.diff_detector = DiffDetector(config)
        self.motion_detector = MotionDetector(config)
        self.debugger = VisualDebugger()

        # 缓存
        self._last_capture: Optional[ScreenCapture] = None
        self._last_text_regions: List[TextRegion] = []
        self._last_ui_elements: List[UIElement] = []

    # =========================================================================
    # 屏幕捕获
    # =========================================================================

    def capture_screen(self, screen_index: int = 0) -> ScreenCapture:
        """捕获完整屏幕"""
        capture = self.capture.capture_full_screen(screen_index)
        self._last_capture = capture
        return capture

    def capture_region(self, region: Rectangle, screen_index: int = 0) -> ScreenCapture:
        """捕获指定区域"""
        capture = self.capture.capture_region(region, screen_index)
        return capture

    def get_screen_size(self, screen_index: int = 0) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        return self.capture.get_screen_size(screen_index)

    # =========================================================================
    # OCR 文字识别
    # =========================================================================

    def recognize_text(
        self,
        capture: Optional[ScreenCapture] = None,
        **kwargs
    ) -> List[TextRegion]:
        """
        识别屏幕上的文字

        Args:
            capture: 屏幕捕获（如果为 None，使用最后一次捕获）
            **kwargs: 传递给 OCR 引擎的参数

        Returns:
            识别到的文字区域列表
        """
        if self.ocr is None or not self.ocr.is_available:
            return []

        if capture is None:
            capture = self._last_capture

        if capture is None:
            raise ValueError("没有可用的屏幕捕获，请先调用 capture_screen()")

        regions = self.ocr.recognize(capture, **kwargs)
        self._last_text_regions = regions
        return regions

    def find_text(
        self,
        text: str,
        capture: Optional[ScreenCapture] = None,
        exact_match: bool = False,
        case_sensitive: bool = False
    ) -> Optional[TextRegion]:
        """
        查找指定文字

        Args:
            text: 要查找的文字
            capture: 屏幕捕获（如果为 None，使用最后一次捕获）
            exact_match: 是否精确匹配
            case_sensitive: 是否区分大小写

        Returns:
            找到的文字区域，如果没找到返回 None
        """
        if self.ocr is None or not self.ocr.is_available:
            return None

        if capture is None:
            capture = self._last_capture

        return self.ocr.find_text(capture, text, exact_match, case_sensitive)

    def find_all_text(
        self,
        text: str,
        capture: Optional[ScreenCapture] = None,
        case_sensitive: bool = False
    ) -> List[TextRegion]:
        """查找所有匹配的文字"""
        if self.ocr is None or not self.ocr.is_available:
            return []

        if capture is None:
            capture = self._last_capture

        return self.ocr.find_all_text(capture, text, case_sensitive)

    # =========================================================================
    # UI 元素解析
    # =========================================================================

    def parse_ui(
        self,
        capture: Optional[ScreenCapture] = None,
        force_ocr: bool = False
    ) -> List[UIElement]:
        """
        解析 UI 元素

        Args:
            capture: 屏幕捕获（如果为 None，使用最后一次捕获）
            force_ocr: 是否强制重新 OCR

        Returns:
            UI 元素列表
        """
        if capture is None:
            capture = self._last_capture

        if capture is None:
            raise ValueError("没有可用的屏幕捕获")

        # 如果需要，先进行 OCR
        if force_ocr or not self._last_text_regions:
            text_regions = self.recognize_text(capture)
        else:
            text_regions = self._last_text_regions

        # 检测 UI 元素
        elements = self.ui_detector.detect_elements(capture, text_regions)
        self._last_ui_elements = elements
        return elements

    def find_element(
        self,
        label: str,
        elem_type: Optional[str] = None
    ) -> Optional[UIElement]:
        """
        查找 UI 元素

        Args:
            label: 元素标签
            elem_type: 元素类型（可选）

        Returns:
            找到的元素，如果没找到返回 None
        """
        elements = self._last_ui_elements
        if elem_type:
            elements = self.ui_detector.find_elements_by_type(elements, elem_type)

        return self.ui_detector.find_element_by_label(elements, label)

    def find_buttons(self) -> List[UIElement]:
        """查找所有按钮"""
        return self.ui_detector.find_elements_by_type(self._last_ui_elements, 'button')

    def find_inputs(self) -> List[UIElement]:
        """查找所有输入框"""
        return self.ui_detector.find_elements_by_type(self._last_ui_elements, 'input')

    # =========================================================================
    # 差异检测
    # =========================================================================

    def compare_screens(
        self,
        before: ScreenCapture,
        after: ScreenCapture,
        threshold: float = 0.0
    ) -> List[DiffRegion]:
        """比较两幅屏幕的差异"""
        return self.diff_detector.compare(before, after, threshold)

    def has_changed(
        self,
        before: ScreenCapture,
        after: ScreenCapture,
        threshold: float = 0.05
    ) -> bool:
        """检查是否有显著变化"""
        return self.diff_detector.has_changed(before, after, threshold)

    def wait_for_change(
        self,
        timeout: float = 5.0,
        check_interval: float = 0.1
    ) -> Optional[ScreenCapture]:
        """等待屏幕发生变化"""
        return self.diff_detector.wait_for_change(
            lambda: self.capture_screen(),
            timeout,
            check_interval
        )

    # =========================================================================
    # 观察功能（综合）
    # =========================================================================

    def observe(self, screen_index: int = 0) -> dict:
        """
        综合观察屏幕

        Returns:
            观察结果字典，包含：
            - capture: 屏幕捕获
            - texts: 识别的文字
            - elements: UI 元素
            - summary: 自然语言摘要
        """
        # 捕获屏幕
        capture = self.capture_screen(screen_index)

        # 识别文字（如果 OCR 可用）
        texts = self.recognize_text(capture) if self.ocr and self.ocr.is_available else []

        # 解析 UI
        elements = self.parse_ui(capture)

        # 生成摘要
        summary = self._generate_summary(texts, elements)

        return {
            'capture': capture,
            'texts': texts,
            'elements': elements,
            'summary': summary
        }

    def _generate_summary(
        self,
        texts: List[TextRegion],
        elements: List[UIElement]
    ) -> str:
        """生成自然语言摘要"""
        parts = []

        # 统计 UI 元素
        button_count = sum(1 for e in elements if e.type == 'button')
        input_count = sum(1 for e in elements if e.type == 'input')

        if button_count > 0:
            parts.append(f"检测到 {button_count} 个按钮")
        if input_count > 0:
            parts.append(f"检测到 {input_count} 个输入框")

        # 提取重要文字（置信度高的）
        important_texts = [
            t.text for t in texts
            if t.confidence > 0.8 and len(t.text) > 2
        ][:10]  # 最多10个

        if important_texts:
            parts.append(f"识别到文字: {', '.join(important_texts[:5])}")

        return "；".join(parts) if parts else "屏幕无明显内容"

    # =========================================================================
    # 可视化调试
    # =========================================================================

    def draw_debug_image(
        self,
        capture: Optional[ScreenCapture] = None,
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        绘制调试图像（显示检测到的元素）

        Args:
            capture: 屏幕捕获（如果为 None，使用最后一次捕获）
            output_path: 输出路径（可选）

        Returns:
            绘制后的图像
        """
        if capture is None:
            capture = self._last_capture

        return self.debugger.draw_elements(capture, self._last_ui_elements, output_path)

    def save_debug_image(self, path: str):
        """保存调试图像"""
        self.draw_debug_image(output_path=path)

    # =========================================================================
    # 工具方法
    # =========================================================================

    def capture_to_pil(self, screen_index: int = 0) -> Image.Image:
        """捕获屏幕并返回 PIL Image"""
        return self.capture.capture_to_pil(screen_index)

    def get_capture_as_image(self, capture: ScreenCapture) -> Image.Image:
        """将 ScreenCapture 转换为 PIL Image"""
        return Image.open(io.BytesIO(capture.image))

    def clear_cache(self):
        """清空缓存"""
        self._last_capture = None
        self._last_text_regions = []
        self._last_ui_elements = []
