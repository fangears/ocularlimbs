"""
OcularLimbs 配置文件
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import os

@dataclass
class VisionConfig:
    """视觉模块配置"""

    # 屏幕捕获配置
    capture_width: int = 1920
    capture_height: int = 1080
    capture_fps: int = 10
    screen_index: int = 0  # 主显示器

    # OCR 配置
    ocr_engine: str = "tesseract"  # tesseract | paddleocr
    ocr_languages: List[str] = field(default_factory=lambda: ['eng', 'chi_sim'])
    ocr_confidence_threshold: float = 0.6

    # 目标检测配置
    enable_object_detection: bool = False  # YOLO 检测（可选）
    detection_confidence: float = 0.5

    # 图像处理配置
    image_quality: int = 95  # PNG 压缩质量
    max_image_size: Tuple[int, int] = (1920, 1080)

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 1  # 缓存存活时间（秒）


@dataclass
class ActionConfig:
    """操作模块配置"""

    # 鼠标配置
    mouse_dpi: int = 1000
    default_click_duration: float = 0.1
    smooth_movement: bool = True
    movement_speed: float = 0.5  # 0-1，越小越慢

    # 键盘配置
    typing_delay: float = 0.05
    key_press_duration: float = 0.05

    # 安全配置
    safety_enabled: bool = True
    confirm_dangerous_actions: bool = True
    forbidden_actions: List[str] = field(default_factory=lambda: [
        'delete', 'format', 'shutdown', 'reboot'
    ])

    # 禁用区域（屏幕坐标，防止误操作）
    forbidden_regions: List[Tuple[int, int, int, int]] = field(default_factory=list)

    # 操作后延迟
    action_delay: float = 0.5  # 每次操作后等待时间

    # 日志配置
    log_file: Optional[str] = None


@dataclass
class PlanningConfig:
    """规划模块配置"""

    # LLM 配置
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    max_tokens: int = 4096

    # 推理配置
    max_planning_iterations: int = 5
    enable_reflection: bool = True
    confidence_threshold: float = 0.6

    # 记忆配置
    memory_enabled: bool = True
    memory_size: int = 100  # 保留最近 N 条记忆
    work_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), 'ocularlimbs_workspace'))

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class SystemConfig:
    """系统总配置"""

    # 模块配置
    vision: VisionConfig = field(default_factory=VisionConfig)
    action: ActionConfig = field(default_factory=ActionConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)

    # 系统配置
    debug_mode: bool = False
    log_level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    log_file: Optional[str] = None

    # 性能配置
    max_concurrent_operations: int = 1
    operation_timeout: float = 30.0

    # UI 配置
    show_visual_feedback: bool = True  # 显示操作轨迹
    overlay_opacity: float = 0.3

    # 工作目录
    work_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), 'ocularlimbs_workspace'))

    def __post_init__(self):
        """创建工作目录"""
        os.makedirs(self.work_dir, exist_ok=True)
        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file) or '.', exist_ok=True)


# 默认配置实例
default_config = SystemConfig()
