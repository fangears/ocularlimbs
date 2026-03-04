"""
OcularLimbs - 为 AI 提供眼睛和手脚
核心类型定义
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict, Tuple, Literal
from enum import Enum
import time

# =============================================================================
# 视觉相关类型
# =============================================================================

@dataclass
class Point:
    """2D 点坐标"""
    x: int
    y: int

    def __iter__(self):
        return iter((self.x, self.y))

    def distance_to(self, other: 'Point') -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5


@dataclass
class Rectangle:
    """矩形区域"""
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    def contains(self, point: Point) -> bool:
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def intersects(self, other: 'Rectangle') -> bool:
        return not (self.right < other.left or self.left > other.right or
                    self.bottom < other.top or self.top > other.bottom)


@dataclass
class TextRegion:
    """识别到的文本区域"""
    text: str
    bbox: Rectangle
    confidence: float
    language: Optional[str] = None


@dataclass
class UIElement:
    """识别到的 UI 元素"""
    type: Literal['button', 'input', 'link', 'text', 'image', 'checkbox', 'radio', 'dropdown', 'unknown']
    label: Optional[str] = None
    bbox: Optional[Rectangle] = None
    confidence: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenCapture:
    """屏幕捕获结果"""
    image: bytes  # PNG 格式图像数据
    timestamp: float = field(default_factory=time.time)
    screen_index: int = 0
    width: int = 0
    height: int = 0


@dataclass
class DiffRegion:
    """图像差异区域"""
    bbox: Rectangle
    change_type: Literal['appeared', 'disappeared', 'changed']
    confidence: float


# =============================================================================
# 操作相关类型
# =============================================================================

class MouseButton(Enum):
    """鼠标按钮"""
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class MouseAction:
    """鼠标操作"""
    action: Literal['move', 'click', 'double_click', 'drag', 'scroll']
    button: MouseButton = MouseButton.LEFT
    position: Optional[Point] = None
    from_position: Optional[Point] = None  # 用于拖拽
    to_position: Optional[Point] = None    # 用于拖拽
    scroll_amount: int = 0                 # 用于滚动
    duration: float = 0.0                  # 操作持续时间（秒）


@dataclass
class KeyAction:
    """键盘操作"""
    action: Literal['press', 'release', 'type']
    key: Optional[str] = None              # 按键名称
    text: Optional[str] = None             # 要输入的文本
    modifiers: List[str] = field(default_factory=list)  # ['ctrl', 'shift', 'alt', 'win']


# =============================================================================
# 任务相关类型
# =============================================================================

@dataclass
class TaskGoal:
    """任务目标"""
    description: str           # 自然语言描述
    constraints: List[str] = field(default_factory=list)  # 约束条件
    timeout: float = 30.0      # 超时时间（秒）
    priority: int = 0          # 优先级


@dataclass
class Observation:
    """观察结果"""
    timestamp: float = field(default_factory=time.time)
    screen_captured: Optional[ScreenCapture] = None
    text_found: List[TextRegion] = field(default_factory=list)
    ui_elements: List[UIElement] = field(default_factory=list)
    active_window: Optional[str] = None
    cursor_position: Optional[Point] = None
    summary: str = ""  # 自然语言摘要


@dataclass
class ActionResult:
    """操作结果"""
    success: bool
    action: Any
    error: Optional[str] = None
    new_observation: Optional[Observation] = None
    execution_time: float = 0.0
    summary: str = ""


# =============================================================================
# 规划相关类型
# =============================================================================

@dataclass
class PlanningStep:
    """规划步骤"""
    step_id: int
    description: str          # 步骤描述
    action_type: str          # 操作类型
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    confidence: float = 0.0


@dataclass
class ExecutionPlan:
    """执行计划"""
    goal: TaskGoal
    steps: List[PlanningStep]
    reasoning: str = ""
    confidence: float = 0.0
    alternative_approaches: List[str] = field(default_factory=list)


# =============================================================================
# 系统状态类型
# =============================================================================

@dataclass
class SystemState:
    """系统状态"""
    is_active: bool = False
    current_task: Optional[TaskGoal] = None
    current_step: int = 0
    last_observation: Optional[Observation] = None
    execution_history: List[ActionResult] = field(default_factory=list)
    error_count: int = 0
    start_time: Optional[float] = None


# =============================================================================
# 错误类型
# =============================================================================

class AgentError(Exception):
    """Agent 基础异常"""
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class VisionError(AgentError):
    """视觉模块错误"""
    def __init__(self, message: str):
        super().__init__(message, "vision")


class ActionError(AgentError):
    """操作模块错误"""
    def __init__(self, message: str):
        super().__init__(message, "action")


class PlanningError(AgentError):
    """规划模块错误"""
    def __init__(self, message: str):
        super().__init__(message, "planning")


class TimeoutError(AgentError):
    """超时错误"""
    def __init__(self, message: str):
        super().__init__(message, "timeout")
