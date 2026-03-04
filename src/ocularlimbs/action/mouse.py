"""
鼠标控制模块
支持平滑移动、点击、拖拽、滚动等操作
"""

import time
import math
from typing import Tuple, Optional, List
from dataclasses import dataclass

import pyautogui

from ..core.types import Point, Rectangle, MouseButton, MouseAction
from ..config.settings import ActionConfig


class MouseController:
    """鼠标控制器"""

    def __init__(self, config: ActionConfig):
        self.config = config

        # pyautogui 安全设置
        pyautogui.FAILSAFE = True  # 移动到左上角触发生鼠标异常
        pyautogui.PAUSE = config.action_delay

        # 获取屏幕尺寸
        self.screen_width, self.screen_height = pyautogui.size()

    def get_position(self) -> Point:
        """获取当前鼠标位置"""
        x, y = pyautogui.position()
        return Point(x, y)

    def move_to(self, x: int, y: int, duration: Optional[float] = None) -> None:
        """
        移动鼠标到指定位置

        Args:
            x, y: 目标坐标
            duration: 移动持续时间（秒），None 则使用配置值
        """
        if duration is None:
            duration = self._calculate_duration(x, y)

        if self.config.smooth_movement and duration > 0:
            # 平滑移动（使用缓动函数）
            self._smooth_move_to(x, y, duration)
        else:
            # 瞬间移动
            pyautogui.moveTo(x, y, duration=0)

    def move_relative(self, dx: int, dy: int, duration: float = 0.0) -> None:
        """
        相对移动鼠标

        Args:
            dx, dy: 相对位移
            duration: 移动持续时间
        """
        current = self.get_position()
        self.move_to(current.x + dx, current.y + dy, duration)

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        interval: float = 0.0
    ) -> None:
        """
        点击

        Args:
            x, y: 点击位置（None 则在当前位置）
            button: 鼠标按钮
            clicks: 点击次数
            interval: 多次点击之间的间隔
        """
        if x is not None and y is not None:
            self.move_to(x, y)

        # pyautogui 的 button 参数映射
        button_map = {
            MouseButton.LEFT: 'left',
            MouseButton.RIGHT: 'right',
            MouseButton.MIDDLE: 'middle'
        }

        pyautogui.click(
            clicks=clicks,
            interval=interval,
            button=button_map[button]
        )

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """双击"""
        self.click(x, y, clicks=2, interval=0.1)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """右键单击"""
        self.click(x, y, button=MouseButton.RIGHT)

    def drag(
        self,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT
    ) -> None:
        """
        拖拽

        Args:
            from_x, from_y: 起始坐标
            to_x, to_y: 目标坐标
            duration: 拖拽持续时间
            button: 鼠标按钮
        """
        # 移动到起始位置
        self.move_to(from_x, from_y)

        # 按下鼠标
        button_map = {
            MouseButton.LEFT: 'left',
            MouseButton.RIGHT: 'right',
            MouseButton.MIDDLE: 'middle'
        }
        pyautogui.mouseDown(button=button_map[button])

        # 拖动到目标位置
        if self.config.smooth_movement:
            self._smooth_move_to(to_x, to_y, duration)
        else:
            pyautogui.moveTo(to_x, to_y, duration=duration)

        # 释放鼠标
        pyautogui.mouseUp(button=button_map[button])

    def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """
        滚动滚轮

        Args:
            amount: 滚动量（正数向上，负数向下）
            x, y: 滚动位置（None 则在当前位置）
        """
        if x is not None and y is not None:
            self.move_to(x, y, duration=0.1)

        pyautogui.scroll(amount)

    def hover(self, x: int, y: int, duration: float = 0.5) -> None:
        """
        悬停（移动到位置并保持）

        Args:
            x, y: 悬停位置
            duration: 移动持续时间
        """
        self.move_to(x, y, duration)
        time.sleep(self.config.action_delay)

    # ========================================================================
    # 高级操作
    # ========================================================================

    def click_rectangle(
        self,
        rect: Rectangle,
        button: MouseButton = MouseButton.LEFT,
        position: str = 'center'
    ) -> None:
        """
        点击矩形区域

        Args:
            rect: 矩形区域
            button: 鼠标按钮
            position: 点击位置 ('center', 'random', 'top_left', 'top_right', etc.)
        """
        if position == 'center':
            point = rect.center
        elif position == 'random':
            import random
            point = Point(
                rect.x + random.randint(5, rect.width - 5),
                rect.y + random.randint(5, rect.height - 5)
            )
        elif position == 'top_left':
            point = Point(rect.x + 5, rect.y + 5)
        elif position == 'top_right':
            point = Point(rect.right - 5, rect.y + 5)
        elif position == 'bottom_left':
            point = Point(rect.x + 5, rect.bottom - 5)
        elif position == 'bottom_right':
            point = Point(rect.right - 5, rect.bottom - 5)
        else:
            point = rect.center

        self.click(point.x, point.y, button)

    def click_text(
        self,
        text_region,
        button: MouseButton = MouseButton.LEFT
    ) -> None:
        """点击文字区域"""
        rect = text_region.bbox
        self.click_rectangle(rect, button)

    def click_ui_element(
        self,
        element,
        button: MouseButton = MouseButton.LEFT
    ) -> None:
        """点击 UI 元素"""
        if element.bbox:
            self.click_rectangle(element.bbox, button)

    def drag_path(
        self,
        points: List[Point],
        duration: float = 1.0,
        button: MouseButton = MouseButton.LEFT
    ) -> None:
        """
        沿路径拖拽

        Args:
            points: 路径点列表
            duration: 总持续时间
            button: 鼠标按钮
        """
        if not points:
            return

        # 移动到起点
        self.move_to(points[0].x, points[0].y)

        # 按下鼠标
        button_map = {
            MouseButton.LEFT: 'left',
            MouseButton.RIGHT: 'right',
            MouseButton.MIDDLE: 'middle'
        }
        pyautogui.mouseDown(button=button_map[button])

        # 沿路径移动
        step_duration = duration / (len(points) - 1) if len(points) > 1 else 0

        for i in range(1, len(points)):
            point = points[i]
            if self.config.smooth_movement:
                self._smooth_move_to(point.x, point.y, step_duration)
            else:
                pyautogui.moveTo(point.x, point.y, duration=step_duration)

        # 释放鼠标
        pyautogui.mouseUp(button=button_map[button])

    # ========================================================================
    # 私有方法
    # ========================================================================

    def _calculate_duration(self, target_x: int, target_y: int) -> float:
        """根据移动距离计算持续时间"""
        current = self.get_position()
        distance = math.sqrt((target_x - current.x)**2 + (target_y - current.y)**2)

        # 基础速度：每毫秒移动像素数
        base_speed = 2000  # 可以根据 config.mouse_dpi 调整

        duration = distance / base_speed
        return min(duration, 1.0)  # 最多1秒

    def _smooth_move_to(self, target_x: int, target_y: int, duration: float) -> None:
        """使用缓动函数平滑移动"""
        current = self.get_position()
        steps = 20  # 移动步数

        for i in range(1, steps + 1):
            # 使用 ease-out 缓动函数
            t = i / steps
            eased = 1 - (1 - t) ** 2

            x = int(current.x + (target_x - current.x) * eased)
            y = int(current.y + (target_y - current.y) * eased)

            pyautogui.moveTo(x, y, duration=0)
            time.sleep(duration / steps)
