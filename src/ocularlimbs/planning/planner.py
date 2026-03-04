"""
任务规划器
将目标分解为可执行的步骤
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from ..core.types import TaskGoal, ExecutionPlan, PlanningStep, Observation
from ..config.settings import PlanningConfig
from .memory import MemorySystem


@dataclass
class PlanningContext:
    """规划上下文"""
    goal: TaskGoal
    observation: Optional[Observation] = None
    previous_attempts: List[ExecutionPlan] = None
    memory_context: str = ""


class TaskPlanner:
    """任务规划器"""

    def __init__(self, config: PlanningConfig, memory: MemorySystem):
        self.config = config
        self.memory = memory

        # 初始化 Claude API
        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                print("Warning: ANTHROPIC_API_KEY not found, planning will be limited")
            self.client = Anthropic(api_key=api_key) if api_key else None
        else:
            self.client = None
            print("Warning: anthropic package not installed")

    def create_plan(
        self,
        goal: TaskGoal,
        observation: Optional[Observation] = None
    ) -> ExecutionPlan:
        """
        创建执行计划

        Args:
            goal: 任务目标
            observation: 当前观察

        Returns:
            执行计划
        """
        # 获取记忆上下文
        memory_context = self.memory.get_context_summary()

        # 构建规划上下文
        context = PlanningContext(
            goal=goal,
            observation=observation,
            memory_context=memory_context
        )

        # 使用 LLM 生成计划（如果可用）
        if self.client:
            return self._llm_plan(context)
        else:
            # 回退到规则基础规划
            return self._rule_based_plan(context)

    def _llm_plan(self, context: PlanningContext) -> ExecutionPlan:
        """使用 LLM 生成计划"""
        goal = context.goal
        obs = context.observation

        # 构建提示词
        prompt = self._build_planning_prompt(context)

        try:
            # 调用 Claude API
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # 解析响应
            plan_text = response.content[0].text
            return self._parse_plan(plan_text, goal)

        except Exception as e:
            print(f"LLM 规划失败: {e}")
            return self._rule_based_plan(context)

    def _build_planning_prompt(self, context: PlanningContext) -> str:
        """构建规划提示词"""
        goal = context.goal
        obs = context.observation
        memory = context.memory_context

        prompt = f"""你是一个 AI Agent 的任务规划器。请将以下目标分解为可执行的步骤。

# 目标
{goal.description}

# 约束条件
{chr(10).join(f'- {c}' for c in goal.constraints) if goal.constraints else '无'}

# 当前状态
{obs.summary if obs else '未知'}

# 历史经验
{memory if memory else '无'}

# 可用能力
- 视觉：屏幕捕获、OCR文字识别、UI元素理解
- 操作：鼠标点击、键盘输入、窗口控制
- 认知：任务规划、决策制定、错误恢复

请生成一个详细的执行计划，包括：
1. **目标分析**：理解用户想要做什么
2. **步骤分解**：将目标分解为具体步骤
3. **每个步骤包括**：
   - 步骤编号
   - 步骤描述
   - 操作类型（observe/click/type/wait/verify）
   - 参数（位置、文字等）
   - 预期结果

请用以下格式输出：

## 目标分析
[简短分析]

## 执行步骤
1. [步骤描述]
   - 操作类型: [类型]
   - 参数: [参数]
   - 预期结果: [结果]

2. [步骤描述]
   ...

## 替代方案
[如果有其他可行方法，列出 1-2 个]
"""

        return prompt

    def _parse_plan(self, plan_text: str, goal: TaskGoal) -> ExecutionPlan:
        """解析 LLM 返回的计划"""
        steps = []
        reasoning = ""

        # 简单解析（实际应该用更复杂的方法）
        lines = plan_text.split('\n')
        current_step = None
        step_counter = 0

        for line in lines:
            line = line.strip()

            # 提取目标分析
            if line.startswith('## 目标分析'):
                reasoning = "使用 AI 生成的计划"

            # 提取步骤
            elif line.match(r'^\d+\.\s+(.+)'):
                if current_step:
                    steps.append(current_step)

                step_counter += 1
                description = line.match(r'^\d+\.\s+(.+)')[1]
                current_step = PlanningStep(
                    step_id=step_counter,
                    description=description,
                    action_type='unknown',
                    confidence=0.7
                )

            # 提取操作类型
            elif line.startswith('- 操作类型:') and current_step:
                action_type = line.split(':', 1)[1].strip().lower()
                current_step.action_type = action_type

            # 提取参数
            elif line.startswith('- 参数:') and current_step:
                params_str = line.split(':', 1)[1].strip()
                # 简单解析为字典
                current_step.parameters = {'raw': params_str}

            # 提取预期结果
            elif line.startswith('- 预期结果:') and current_step:
                current_step.expected_outcome = line.split(':', 1)[1].strip()

        if current_step:
            steps.append(current_step)

        return ExecutionPlan(
            goal=goal,
            steps=steps,
            reasoning=reasoning,
            confidence=0.8
        )

    def _rule_based_plan(self, context: PlanningContext) -> ExecutionPlan:
        """基于规则的规划（回退方案）"""
        goal = context.goal
        description = goal.description.lower()

        steps = []
        reasoning = "基于规则生成的计划"

        # 简单的模式匹配规则
        if '打开' in description and '记事本' in description:
            steps = [
                PlanningStep(
                    step_id=1,
                    description="打开运行对话框",
                    action_type="hotkey",
                    parameters={'keys': ['win', 'r']},
                    expected_outcome="运行对话框出现"
                ),
                PlanningStep(
                    step_id=2,
                    description="输入 notepad",
                    action_type="type",
                    parameters={'text': 'notepad'},
                    expected_outcome="命令输入完成"
                ),
                PlanningStep(
                    step_id=3,
                    description="按回车",
                    action_type="press",
                    parameters={'key': 'enter'},
                    expected_outcome="记事本打开"
                ),
            ]

        elif '浏览器' in description and ('打开' in description or '启动' in description):
            steps = [
                PlanningStep(
                    step_id=1,
                    description="打开浏览器",
                    action_type="execute",
                    parameters={'command': 'chrome'},
                    expected_outcome="浏览器打开"
                ),
            ]

        else:
            # 通用计划
            steps = [
                PlanningStep(
                    step_id=1,
                    description="观察当前屏幕状态",
                    action_type="observe",
                    parameters={},
                    expected_outcome="获取屏幕信息"
                ),
                PlanningStep(
                    step_id=2,
                    description="分析目标并制定方案",
                    action_type="think",
                    parameters={'goal': description},
                    expected_outcome="明确操作步骤"
                ),
            ]

        return ExecutionPlan(
            goal=goal,
            steps=steps,
            reasoning=reasoning,
            confidence=0.6
        )

    def refine_plan(
        self,
        plan: ExecutionPlan,
        feedback: str,
        last_result: Any
    ) -> ExecutionPlan:
        """根据反馈优化计划"""
        # 简单实现：调整置信度
        new_plan = ExecutionPlan(
            goal=plan.goal,
            steps=plan.steps.copy(),
            reasoning=plan.reasoning + f" | 根据反馈优化: {feedback}",
            confidence=plan.confidence * 0.9
        )

        return new_plan
