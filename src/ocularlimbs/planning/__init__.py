"""
规划模块 - 统一接口
负责任务规划、决策制定和记忆管理
"""

from typing import Optional, Dict, Any, List
import time

from .planner import TaskPlanner
from .memory import MemorySystem

from ..core.types import (
    TaskGoal, ExecutionPlan, Observation, ActionResult, SystemState
)
from ..config.settings import PlanningConfig


class PlanningModule:
    """规划模块 - 统一接口"""

    def __init__(self, config: PlanningConfig):
        self.config = config

        # 初始化子模块
        self.memory = MemorySystem(
            max_size=config.memory_size,
            persist_path=config.work_dir + '/memory.json'
        )
        self.planner = TaskPlanner(config, self.memory)

        # 当前状态
        self.state = SystemState()

    # =========================================================================
    # 规划功能
    # =========================================================================

    def plan(self, goal_description: str, **kwargs) -> ExecutionPlan:
        """
        创建执行计划

        Args:
            goal_description: 目标描述
            **kwargs: 其他参数

        Returns:
            执行计划
        """
        goal = TaskGoal(description=goal_description, **kwargs)

        # 记录目标
        self.memory.add(
            memory_type='goal',
            content={'description': goal_description},
            importance=0.8
        )

        # 创建计划
        plan = self.planner.create_plan(goal, self.state.last_observation)

        # 记录计划
        self.memory.add(
            memory_type='plan',
            content={
                'goal': goal_description,
                'steps': len(plan.steps),
                'reasoning': plan.reasoning
            },
            importance=0.7
        )

        return plan

    def decide_next_action(
        self,
        plan: ExecutionPlan,
        current_observation: Observation
    ) -> Optional[Dict[str, Any]]:
        """
        决定下一步操作

        Args:
            plan: 执行计划
            current_observation: 当前观察

        Returns:
            操作指令字典
        """
        if self.state.current_step >= len(plan.steps):
            return None

        step = plan.steps[self.state.current_step]

        # 更新状态
        self.state.last_observation = current_observation

        # 构建操作指令
        action = {
            'type': step.action_type,
            'description': step.description,
            'parameters': step.parameters,
            'expected_outcome': step.expected_outcome,
            'step_id': step.step_id
        }

        return action

    def should_retry(self, error: str) -> bool:
        """判断是否应该重试"""
        # 检查重试次数
        if self.state.error_count >= self.config.max_retries:
            return False

        # 检查错误类型
        fatal_errors = ['权限不足', '文件不存在', '找不到元素']
        for fatal in fatal_errors:
            if fatal in error:
                return False

        return True

    # =========================================================================
    # 记忆功能
    # =========================================================================

    def remember_observation(self, observation: Observation, importance: float = 0.5):
        """记住观察"""
        self.memory.add(
            memory_type='observation',
            content={'summary': observation.summary},
            importance=importance
        )

    def remember_action(self, description: str, params: Dict[str, Any]):
        """记住操作"""
        self.memory.add(
            memory_type='action',
            content={'description': description, 'params': params},
            importance=0.5
        )

    def remember_result(self, success: bool, summary: str):
        """记住结果"""
        importance = 0.8 if not success else 0.5
        self.memory.add(
            memory_type='result',
            content={'success': success, 'summary': summary},
            importance=importance
        )

    def learn_from_success(self, action: str, context: Dict[str, Any]):
        """从成功中学习"""
        self.memory.learn_from_success(action, context)

    def learn_from_failure(self, action: str, error: str, context: Dict[str, Any]):
        """从失败中学习"""
        self.memory.learn_from_failure(action, error, context)

    def get_similar_experience(self, current_goal: str) -> List[Dict[str, Any]]:
        """获取类似经验"""
        memories = self.memory.search(current_goal, limit=5)

        experiences = []
        for memory in memories:
            if memory.type == 'learning':
                experiences.append({
                    'lesson': memory.content.get('lesson'),
                    'action': memory.content.get('action'),
                    'context': memory.content.get('context')
                })

        return experiences

    # =========================================================================
    # 状态管理
    # =========================================================================

    def start_task(self, goal: TaskGoal):
        """开始任务"""
        self.state = SystemState(
            is_active=True,
            current_task=goal,
            current_step=0,
            start_time=time.time()
        )

    def finish_task(self, success: bool):
        """完成任务"""
        self.state.is_active = False

        # 记录任务结果
        elapsed = time.time() - self.state.start_time if self.state.start_time else 0

        self.memory.add(
            memory_type='task_complete',
            content={
                'goal': self.state.current_task.description if self.state.current_task else '',
                'success': success,
                'elapsed_time': elapsed,
                'steps_completed': self.state.current_step
            },
            importance=0.9
        )

    def advance_step(self):
        """前进一步"""
        self.state.current_step += 1

    def record_error(self, error: str):
        """记录错误"""
        self.state.error_count += 1

        self.memory.add(
            memory_type='error',
            content={'error': error, 'step': self.state.current_step},
            importance=0.8
        )

    # =========================================================================
    # 工具方法
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'is_active': self.state.is_active,
            'current_goal': self.state.current_task.description if self.state.current_task else None,
            'current_step': self.state.current_step,
            'total_steps': len(self.planner._parse_plan("", self.state.current_task or TaskGoal(description="")).steps) if self.state.current_task else 0,
            'error_count': self.state.error_count,
            'elapsed_time': time.time() - self.state.start_time if self.state.start_time else 0
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return self.memory.get_stats()

    def export_memory(self, path: str):
        """导出记忆"""
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.memory._memories, f, ensure_ascii=False, indent=2, default=lambda x: x.__dict__)

    def import_memory(self, path: str):
        """导入记忆"""
        self.memory._load()
