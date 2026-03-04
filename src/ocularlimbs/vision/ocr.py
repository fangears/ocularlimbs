"""
OCR 文字识别模块
支持 Tesseract 和 PaddleOCR
"""

import io
import time
from typing import List, Optional, Tuple
from PIL import Image
import numpy as np

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from ..core.types import ScreenCapture, TextRegion, Rectangle
from ..config.settings import VisionConfig


class OCREngine:
    """OCR 引擎基类"""

    def recognize(self, capture: ScreenCapture, **kwargs) -> List[TextRegion]:
        """识别文字"""
        raise NotImplementedError


class TesseractEngine(OCREngine):
    """Tesseract OCR 引擎"""

    def __init__(self, config: VisionConfig):
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract 未安装，请运行: pip install pytesseract")

        self.config = config
        self.languages = '+'.join(config.ocr_languages)

    def recognize(
        self,
        capture: ScreenCapture,
        min_confidence: float = None
    ) -> List[TextRegion]:
        """
        识别图像中的文字

        Args:
            capture: 屏幕捕获
            min_confidence: 最小置信度阈值

        Returns:
            识别到的文字区域列表
        """
        if min_confidence is None:
            min_confidence = self.config.ocr_confidence_threshold

        # 转换为 PIL Image
        image = Image.open(io.BytesIO(capture.image))

        # 使用 pytesseract 获取详细数据
        data = pytesseract.image_to_data(
            image,
            lang=self.languages,
            output_type=pytesseract.Output.DICT
        )

        # 解析结果
        regions = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue

            conf = int(data['conf'][i])
            if conf == -1:  # Tesseract 返回 -1 表示无法识别
                continue

            confidence = conf / 100.0
            if confidence < min_confidence:
                continue

            # 构建边界框
            bbox = Rectangle(
                x=data['left'][i],
                y=data['top'][i],
                width=data['width'][i],
                height=data['height'][i]
            )

            regions.append(TextRegion(
                text=text,
                bbox=bbox,
                confidence=confidence
            ))

        return regions


class PaddleOCREngine(OCREngine):
    """PaddleOCR 引擎（更好的中文支持）"""

    def __init__(self, config: VisionConfig):
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR 未安装，请运行: pip install paddleocr")

        self.config = config
        # 初始化 PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',  # 中文
            show_log=False
        )

    def recognize(
        self,
        capture: ScreenCapture,
        min_confidence: float = None
    ) -> List[TextRegion]:
        """
        识别图像中的文字

        Args:
            capture: 屏幕捕获
            min_confidence: 最小置信度阈值

        Returns:
            识别到的文字区域列表
        """
        if min_confidence is None:
            min_confidence = self.config.ocr_confidence_threshold

        # 转换为 numpy array
        image = Image.open(io.BytesIO(capture.image))
        img_array = np.array(image)

        # 使用 PaddleOCR 识别
        results = self.ocr.ocr(img_array, cls=True)

        regions = []
        if results and results[0]:
            for line in results[0]:
                box = line[0]  # 四个角点
                text_info = line[1]  # (text, confidence)

                text = text_info[0]
                confidence = text_info[1]

                if confidence < min_confidence:
                    continue

                # 计算边界框（从四个角点）
                x_coords = [int(p[0]) for p in box]
                y_coords = [int(p[1]) for p in box]

                bbox = Rectangle(
                    x=min(x_coords),
                    y=min(y_coords),
                    width=max(x_coords) - min(x_coords),
                    height=max(y_coords) - min(y_coords)
                )

                regions.append(TextRegion(
                    text=text,
                    bbox=bbox,
                    confidence=confidence
                ))

        return regions


class OCRRecognizer:
    """OCR 识别器（统一接口）"""

    def __init__(self, config: VisionConfig):
        self.config = config
        self.engine: Optional[OCREngine] = None
        self.available = False
        self._init_engine()

    @property
    def is_available(self) -> bool:
        """OCR 是否可用"""
        return self.available

    def _init_engine(self):
        """根据配置初始化 OCR 引擎"""
        engine_type = self.config.ocr_engine.lower()

        try:
            if engine_type == "paddleocr":
                if PADDLEOCR_AVAILABLE:
                    self.engine = PaddleOCREngine(self.config)
                    self.available = True
                else:
                    # PaddleOCR 不可用，回退到 Tesseract
                    if TESSERACT_AVAILABLE:
                        self.engine = TesseractEngine(self.config)
                        self.available = True
                    else:
                        # 都不可用，设置为不可用状态
                        self.available = False

            else:  # tesseract (默认)
                if TESSERACT_AVAILABLE:
                    self.engine = TesseractEngine(self.config)
                    self.available = True
                else:
                    # Tesseract 不可用，设置为不可用状态
                    self.available = False

        except Exception as e:
            # 初始化失败，OCR 不可用（静默模式）
            self.available = False

    def recognize(self, capture: ScreenCapture, **kwargs) -> List[TextRegion]:
        """识别文字"""
        if not self.available or self.engine is None:
            return []
        return self.engine.recognize(capture, **kwargs)

    def find_text(
        self,
        capture: ScreenCapture,
        target_text: str,
        exact_match: bool = False,
        case_sensitive: bool = False
    ) -> Optional[TextRegion]:
        """
        查找指定文字

        Args:
            capture: 屏幕捕获
            target_text: 要查找的文字
            exact_match: 是否精确匹配
            case_sensitive: 是否区分大小写

        Returns:
            找到的文字区域，如果没找到返回 None
        """
        if not self.available or self.engine is None:
            return None

        regions = self.recognize(capture)

        for region in regions:
            text = region.text
            search_text = target_text if case_sensitive else target_text.lower()
            compare_text = text if case_sensitive else text.lower()

            if exact_match:
                if search_text == compare_text:
                    return region
            else:
                if search_text in compare_text:
                    return region

        return None

    def find_all_text(
        self,
        capture: ScreenCapture,
        target_text: str,
        case_sensitive: bool = False
    ) -> List[TextRegion]:
        """查找所有匹配的文字"""
        if not self.available or self.engine is None:
            return []

        regions = self.recognize(capture)
        results = []

        for region in regions:
            text = region.text
            search_text = target_text if case_sensitive else target_text.lower()
            compare_text = text if case_sensitive else text.lower()

            if search_text in compare_text:
                results.append(region)

        return results
