"""
UI 元素解析模块
识别按钮、输入框、链接等 UI 元素
"""

import io
import re
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw
import numpy as np
import cv2

from ..core.types import ScreenCapture, UIElement, Rectangle, TextRegion
from ..config.settings import VisionConfig


class UIElementDetector:
    """UI 元素检测器"""

    def __init__(self, config: VisionConfig):
        self.config = config

    def detect_elements(self, capture: ScreenCapture, text_regions: List[TextRegion]) -> List[UIElement]:
        """
        检测 UI 元素

        Args:
            capture: 屏幕捕获
            text_regions: 已识别的文字区域

        Returns:
            检测到的 UI 元素列表
        """
        elements = []

        # 从文字区域推断 UI 元素
        for region in text_regions:
            element = self._infer_element_from_text(region)
            if element:
                elements.append(element)

        # 使用图像处理检测其他元素
        elements.extend(self._detect_by_image_processing(capture))

        return elements

    def _infer_element_from_text(self, text_region: TextRegion) -> Optional[UIElement]:
        """从文字推断 UI 元素类型"""
        text = text_region.text.strip().lower()

        # 按钮类型的文字模式
        button_patterns = [
            r'^确定$|^ok$|^取消$|^cancel$',
            r'^是$|^否$|^yes$|^no$',
            r'^保存$|^save$',
            r'^删除$|^delete$',
            r'^提交$|^submit$',
            r'^下一步$|^next$',
            r'^关闭$|^close$',
            r'^登录$|^login$|^注册$|^register$',
            r'^搜索$|^search$',
            r'^下载$|^download$|^上传$|^upload$',
        ]

        # 输入框类型的文字模式
        input_patterns = [
            r'.*输入.*',
            r'.*用户名.*',
            r'.*密码.*',
            r'.*邮箱.*',
            r'.*搜索.*',
        ]

        # 检查是否匹配按钮模式
        for pattern in button_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return UIElement(
                    type='button',
                    label=text_region.text,
                    bbox=text_region.bbox,
                    confidence=text_region.confidence
                )

        # 检查是否匹配输入框模式
        for pattern in input_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return UIElement(
                    type='input',
                    label=text_region.text,
                    bbox=text_region.bbox,
                    confidence=text_region.confidence * 0.8  # 降低置信度
                )

        # 默认为文本
        return UIElement(
            type='text',
            label=text_region.text,
            bbox=text_region.bbox,
            confidence=text_region.confidence
        )

    def _detect_by_image_processing(self, capture: ScreenCapture) -> List[UIElement]:
        """使用图像处理检测 UI 元素"""
        elements = []

        # 转换为 OpenCV 格式
        image = Image.open(io.BytesIO(capture.image))
        img_array = np.array(image)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # 检测矩形（可能是按钮、输入框等）
        contours, _ = cv2.findContours(
            img_gray,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            # 近似为多边形
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # 检查是否是四边形
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)

                # 过滤太小的区域
                if w < 20 or h < 10:
                    continue

                # 根据长宽比推断类型
                aspect_ratio = w / h if h > 0 else 0

                if aspect_ratio > 3:
                    # 很宽的可能是输入框或按钮
                    elem_type = 'input'
                elif 0.8 < aspect_ratio < 1.2:
                    # 接近正方形，可能是复选框
                    elem_type = 'checkbox'
                else:
                    # 其他矩形可能是按钮
                    elem_type = 'button'

                elements.append(UIElement(
                    type=elem_type,
                    bbox=Rectangle(x=x, y=y, width=w, height=h),
                    confidence=0.5  # 较低置信度
                ))

        return elements

    def find_element_by_label(
        self,
        elements: List[UIElement],
        label: str,
        fuzzy: bool = True
    ) -> Optional[UIElement]:
        """
        根据标签查找 UI 元素

        Args:
            elements: UI 元素列表
            label: 要查找的标签
            fuzzy: 是否模糊匹配

        Returns:
            找到的元素，如果没找到返回 None
        """
        for element in elements:
            if element.label:
                if fuzzy:
                    if label.lower() in element.label.lower():
                        return element
                else:
                    if label.lower() == element.label.lower():
                        return element
        return None

    def find_elements_by_type(
        self,
        elements: List[UIElement],
        elem_type: str
    ) -> List[UIElement]:
        """根据类型查找 UI 元素"""
        return [e for e in elements if e.type == elem_type]

    def get_clickable_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """获取所有可点击的元素"""
        clickable_types = {'button', 'link', 'checkbox', 'radio'}
        return [e for e in elements if e.type in clickable_types and e.bbox]


class VisualDebugger:
    """可视化调试工具"""

    @staticmethod
    def draw_elements(
        capture: ScreenCapture,
        elements: List[UIElement],
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        在图像上绘制检测到的 UI 元素

        Args:
            capture: 屏幕捕获
            elements: UI 元素列表
            output_path: 输出路径（可选）

        Returns:
            绘制后的图像
        """
        image = Image.open(io.BytesIO(capture.image))
        draw = ImageDraw.Draw(image)

        # 不同类型使用不同颜色
        colors = {
            'button': 'red',
            'input': 'blue',
            'link': 'green',
            'text': 'gray',
            'checkbox': 'orange',
            'radio': 'purple',
            'unknown': 'yellow'
        }

        for element in elements:
            if element.bbox:
                bbox = element.bbox
                color = colors.get(element.type, 'gray')

                # 绘制边框
                draw.rectangle(
                    [bbox.left, bbox.top, bbox.right, bbox.bottom],
                    outline=color,
                    width=2
                )

                # 绘制标签
                if element.label:
                    draw.text(
                        (bbox.left, bbox.top - 15),
                        f"{element.type}: {element.label}",
                        fill=color
                    )

        if output_path:
            image.save(output_path)

        return image
