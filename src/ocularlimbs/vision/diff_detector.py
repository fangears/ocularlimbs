"""
图像差异检测模块
检测屏幕变化，用于验证操作结果
"""

import io
import time
from typing import List, Optional, Tuple
from PIL import Image, ImageChops
import numpy as np
import cv2

from ..core.types import ScreenCapture, DiffRegion, Rectangle
from ..config.settings import VisionConfig


class DiffDetector:
    """图像差异检测器"""

    def __init__(self, config: VisionConfig):
        self.config = config
        self._prev_capture: Optional[ScreenCapture] = None

    def compare(
        self,
        before: ScreenCapture,
        after: ScreenCapture,
        threshold: float = 0.0,
        min_region_size: int = 10
    ) -> List[DiffRegion]:
        """
        比较两幅图像的差异

        Args:
            before: 操作前的捕获
            after: 操作后的捕获
            threshold: 差异阈值（0-1），越小越敏感
            min_region_size: 最小差异区域大小（像素）

        Returns:
            差异区域列表
        """
        # 转换为 PIL Image
        img_before = Image.open(io.BytesIO(before.image))
        img_after = Image.open(io.BytesIO(after.image))

        # 确保尺寸相同
        if img_before.size != img_after.size:
            img_after = img_after.resize(img_before.size)

        # 计算差异
        diff = ImageChops.difference(img_before, img_after)

        # 转换为 numpy array
        diff_array = np.array(diff)

        # 计算差异强度（RGB 平均值）
        if len(diff_array.shape) == 3:
            diff_intensity = np.mean(diff_array, axis=2)
        else:
            diff_intensity = diff_array

        # 应用阈值
        threshold_value = int(threshold * 255)
        diff_mask = (diff_intensity > threshold_value).astype(np.uint8) * 255

        # 找到差异区域的轮廓
        contours, _ = cv2.findContours(
            diff_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        diff_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # 过滤太小的区域
            if w < min_region_size or h < min_region_size:
                continue

            # 计算该区域的平均差异强度
            region_diff = diff_intensity[y:y+h, x:x+w]
            confidence = np.mean(region_diff) / 255.0

            # 判断变化类型
            change_type = self._determine_change_type(
                img_before, img_after, Rectangle(x, y, w, h)
            )

            diff_regions.append(DiffRegion(
                bbox=Rectangle(x, y, w, h),
                change_type=change_type,
                confidence=confidence
            ))

        return diff_regions

    def _determine_change_type(
        self,
        before: Image.Image,
        after: Image.Image,
        region: Rectangle
    ) -> str:
        """
        判断变化类型

        Args:
            before: 操作前图像
            after: 操作后图像
            region: 差异区域

        Returns:
            变化类型: 'appeared', 'disappeared', 'changed'
        """
        # 提取区域
        before_array = np.array(before.crop((region.x, region.y, region.right, region.bottom)))
        after_array = np.array(after.crop((region.x, region.y, region.right, region.bottom)))

        # 计算亮度
        before_brightness = np.mean(before_array)
        after_brightness = np.mean(after_array)

        # 简单判断：如果之前很暗（接近背景色），之后很亮，则是出现
        # 如果之前很亮，之后很暗，则是消失
        # 否则是变化

        if before_brightness < 50 and after_brightness > 100:
            return 'appeared'
        elif before_brightness > 100 and after_brightness < 50:
            return 'disappeared'
        else:
            return 'changed'

    def has_changed(
        self,
        before: ScreenCapture,
        after: ScreenCapture,
        threshold: float = 0.05
    ) -> bool:
        """
        快速检查是否有显著变化

        Args:
            before: 操作前的捕获
            after: 操作后的捕获
            threshold: 变化阈值（0-1）

        Returns:
            是否有显著变化
        """
        diff_regions = self.compare(before, after, threshold=threshold)
        return len(diff_regions) > 0

    def wait_for_change(
        self,
        capture_func,
        timeout: float = 5.0,
        check_interval: float = 0.1
    ) -> Optional[ScreenCapture]:
        """
        等待屏幕发生变化

        Args:
            capture_func: 捕获函数
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            变化后的捕获，如果超时返回 None
        """
        start_time = time.time()
        baseline = capture_func()

        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            current = capture_func()

            if self.has_changed(baseline, current, threshold=0.05):
                return current

        return None

    def get_diff_summary(
        self,
        before: ScreenCapture,
        after: ScreenCapture
    ) -> str:
        """
        获取差异摘要

        Args:
            before: 操作前
            after: 操作后

        Returns:
            差异描述
        """
        diff_regions = self.compare(before, after, threshold=0.1)

        if not diff_regions:
            return "无明显变化"

        # 统计变化类型
        appeared = sum(1 for r in diff_regions if r.change_type == 'appeared')
        disappeared = sum(1 for r in diff_regions if r.change_type == 'disappeared')
        changed = sum(1 for r in diff_regions if r.change_type == 'changed')

        parts = []
        if appeared > 0:
            parts.append(f"{appeared}个新元素出现")
        if disappeared > 0:
            parts.append(f"{disappeared}个元素消失")
        if changed > 0:
            parts.append(f"{changed}个元素变化")

        return "、".join(parts) if parts else "无明显变化"

    def save_diff_image(
        self,
        before: ScreenCapture,
        after: ScreenCapture,
        output_path: str
    ):
        """
        保存差异可视化图像

        Args:
            before: 操作前
            after: 操作后
            output_path: 输出路径
        """
        img_before = Image.open(io.BytesIO(before.image))
        img_after = Image.open(io.BytesIO(after.image))

        # 确保尺寸相同
        if img_before.size != img_after.size:
            img_after = img_after.resize(img_before.size)

        # 计算差异
        diff = ImageChops.difference(img_before, img_after)

        # 增强差异（使差异更明显）
        diff_enhanced = Image.eval(diff, lambda x: x * 3)

        # 保存
        diff_enhanced.save(output_path)


class MotionDetector:
    """运动检测器（用于视频流）"""

    def __init__(self, config: VisionConfig):
        self.config = config
        self._background: Optional[np.ndarray] = None

    def update_background(self, capture: ScreenCapture):
        """更新背景帧"""
        image = Image.open(io.BytesIO(capture.image))
        self._background = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    def detect_motion(self, capture: ScreenCapture, threshold: int = 25) -> List[Rectangle]:
        """
        检测运动区域

        Args:
            capture: 当前帧
            threshold: 运动阈值

        Returns:
            运动区域列表
        """
        if self._background is None:
            self.update_background(capture)
            return []

        # 转换当前帧
        image = Image.open(io.BytesIO(capture.image))
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        # 计算差异
        diff = cv2.absdiff(self._background, gray)
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # 找到轮廓
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        motion_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 10 and h > 10:  # 过滤小区域
                motion_regions.append(Rectangle(x, y, w, h))

        return motion_regions
