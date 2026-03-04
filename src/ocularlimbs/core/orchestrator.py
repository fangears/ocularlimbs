"""
任务编排器 - 协调各模块完成复杂任务
"""

import time
from typing import Optional, Dict, Any, List

from ..vision import VisionModule
from ..action import ActionModule
from ..planning import PlanningModule

from ..core.types import (
    TaskGoal, Observation, ActionResult, ExecutionPlan,
    SystemState, AgentError
)
from ..config.settings import SystemConfig


class Orchestrator:
    """任务编排器 - Agent 的大脑核心"""

    def __init__(self, config: SystemConfig):
        self.config = config

        # 初始化模块
        self.vision = VisionModule(config.vision)
        self.action = ActionModule(config.action)
        self.planning = PlanningModule(config.planning)

        # 状态
        self.is_running = False
        self.should_stop = False

    # =========================================================================
    # 核心执行循环
    # =========================================================================

    def execute(self, goal_description: str, **kwargs) -> ActionResult:
        """
        执行任务

        Args:
            goal_description: 任务描述（自然语言）
            **kwargs: 额外参数

        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"🎯 目标: {goal_description}")
        print(f"{'='*60}\n")

        # 重置停止标志
        self.should_stop = False
        self.is_running = True

        try:
            # 1. 规划阶段
            print("📋 规划中...")
            plan = self.planning.plan(goal_description, **kwargs)

            print(f"   ✅ 计划生成: {len(plan.steps)} 个步骤")
            print(f"   💡 推理: {plan.reasoning}\n")

            # 2. 开始任务
            goal = TaskGoal(description=goal_description, **kwargs)
            self.planning.start_task(goal)

            # 3. 执行阶段
            results = []

            for i, step in enumerate(plan.steps, 1):
                if self.should_stop:
                    print("\n⚠️  任务被中止")
                    break

                print(f"\n📍 步骤 {i}/{len(plan.steps)}: {step.description}")
                print(f"   类型: {step.action_type} | 置信度: {step.confidence:.2f}")

                # 执行步骤
                result = self._execute_step(step, plan)
                results.append(result)

                if not result.success:
                    print(f"   ❌ 失败: {result.error}")

                    # 判断是否重试
                    if self.planning.should_retry(result.error or ""):
                        print(f"   🔄 重试中...")
                        self.planning.record_error(result.error or "")

                        # 重试一次
                        result = self._execute_step(step, plan)
                        results.append(result)

                        if not result.success:
                            print(f"   ❌ 重试失败")
                            break
                    else:
                        break

                self.planning.advance_step()

            # 4. 完成任务
            success = all(r.success for r in results[-3:]) if results else False  # 最后3步成功即为成功
            self.planning.finish_task(success)

            print(f"\n{'='*60}")
            if success:
                print(f"✅ 任务完成!")
            else:
                print(f"⚠️  任务未完全成功")
            print(f"{'='*60}\n")

            return ActionResult(
                success=success,
                action=goal_description,
                summary=f"完成 {len(results)} 个步骤，{'成功' if success else '失败'}"
            )

        except Exception as e:
            error_msg = f"执行异常: {e}"
            print(f"\n❌ {error_msg}")
            return ActionResult(
                success=False,
                action=goal_description,
                error=error_msg
            )

        finally:
            self.is_running = False

    def _execute_step(self, step, plan: ExecutionPlan) -> ActionResult:
        """
        执行单个步骤

        Args:
            step: 执行步骤
            plan: 执行计划

        Returns:
            执行结果
        """
        step_type = step.action_type.lower()

        try:
            # 观察类操作
            if step_type in ['observe', 'look', 'see', 'watch']:
                return self._do_observe(step)

            # 鼠标操作
            elif step_type in ['click', 'tap']:
                return self._do_click(step)
            elif step_type in ['double_click', 'doubleclick']:
                return self._do_double_click(step)
            elif step_type in ['right_click', 'rightclick']:
                return self._do_right_click(step)
            elif step_type in ['drag', 'move']:
                return self._do_drag(step)
            elif step_type in ['scroll', 'scroll_up', 'scroll_down']:
                return self._do_scroll(step)

            # 键盘操作
            elif step_type in ['type', 'input', 'enter_text']:
                return self._do_type(step)
            elif step_type in ['press', 'key', 'keypress']:
                return self._do_press(step)
            elif step_type in ['hotkey', 'shortcut', 'combo']:
                return self._do_hotkey(step)

            # 等待操作
            elif step_type in ['wait', 'sleep', 'delay']:
                return self._do_wait(step)

            # 验证操作
            elif step_type in ['verify', 'check', 'validate']:
                return self._do_verify(step)

            # 思考/分析
            elif step_type in ['think', 'analyze', 'plan']:
                return self._do_think(step)

            # 未知操作
            else:
                return ActionResult(
                    success=False,
                    action=step,
                    error=f"未知操作类型: {step_type}"
                )

        except Exception as e:
            return ActionResult(
                success=False,
                action=step,
                error=str(e)
            )

    # =========================================================================
    # 具体操作实现
    # =========================================================================

    def _do_observe(self, step) -> ActionResult:
        """观察操作"""
        observation_data = self.vision.observe()

        # 更新规划模块的观察
        self.planning.remember_observation(
            observation_data.get('capture'),
            importance=0.6
        )

        summary = observation_data.get('summary', '')
        print(f"   👁️  观察: {summary}")

        return ActionResult(
            success=True,
            action=step,
            summary=summary
        )

    def _do_click(self, step) -> ActionResult:
        """点击操作"""
        params = step.parameters

        # 检查参数
        if 'x' in params and 'y' in params:
            # 直接坐标点击
            x, y = params['x'], params['y']
            print(f"   🖱️  点击: ({x}, {y})")
            success = self.action.click(x, y)

        elif 'text' in params:
            # 文字查找点击
            text = params['text']
            print(f"   🔍 查找并点击: {text}")

            text_region = self.vision.find_text(text)
            if text_region:
                success = self.action.click_text_region(text_region)
            else:
                success = False

        elif 'element' in params:
            # 元素点击
            element = params['element']
            print(f"   🎯 点击元素: {element}")
            success = self.action.click_element(element)

        else:
            success = False

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "点击失败"
        )

    def _do_double_click(self, step) -> ActionResult:
        """双击操作"""
        params = step.parameters

        if 'x' in params and 'y' in params:
            print(f"   🖱️🖱️  双击: ({params['x']}, {params['y']})")
            success = self.action.double_click(params['x'], params['y'])
        else:
            success = False

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "双击失败"
        )

    def _do_right_click(self, step) -> ActionResult:
        """右键点击"""
        params = step.parameters

        if 'x' in params and 'y' in params:
            print(f"   🖱️  右键: ({params['x']}, {params['y']})")
            success = self.action.right_click(params['x'], params['y'])
        else:
            success = False

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "右键失败"
        )

    def _do_drag(self, step) -> ActionResult:
        """拖拽操作"""
        params = step.parameters

        if 'from' in params and 'to' in params:
            from_pos = params['from']
            to_pos = params['to']
            print(f"   ↔️  拖拽: {from_pos} → {to_pos}")
            success = self.action.drag(
                from_pos[0], from_pos[1],
                to_pos[0], to_pos[1]
            )
        else:
            success = False

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "拖拽失败"
        )

    def _do_scroll(self, step) -> ActionResult:
        """滚动操作"""
        params = step.parameters
        amount = params.get('amount', 1)

        if step.action_type == 'scroll_up':
            amount = abs(amount)
        elif step.action_type == 'scroll_down':
            amount = -abs(amount)

        print(f"   📜 滚动: {amount}")
        success = self.action.scroll(amount)

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "滚动失败"
        )

    def _do_type(self, step) -> ActionResult:
        """输入文本"""
        params = step.parameters
        text = params.get('text', '')

        print(f"   ⌨️  输入: {text[:30]}{'...' if len(text) > 30 else ''}")
        success = self.action.type_text(text)

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "输入失败"
        )

    def _do_press(self, step) -> ActionResult:
        """按键"""
        params = step.parameters
        key = params.get('key', 'enter')

        print(f"   ⌨️  按键: {key}")
        success = self.action.press_key(key)

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "按键失败"
        )

    def _do_hotkey(self, step) -> ActionResult:
        """组合键"""
        params = step.parameters
        keys = params.get('keys', ['ctrl', 'c'])

        print(f"   ⌨️  组合键: {'+'.join(keys)}")
        success = self.action.hotkey(*keys)

        return ActionResult(
            success=success,
            action=step,
            error=None if success else "组合键失败"
        )

    def _do_wait(self, step) -> ActionResult:
        """等待"""
        params = step.parameters
        duration = params.get('duration', 1.0)

        print(f"   ⏳ 等待 {duration}秒")
        time.sleep(duration)

        return ActionResult(
            success=True,
            action=step,
            summary=f"等待了 {duration}秒"
        )

    def _do_verify(self, step) -> ActionResult:
        """验证"""
        print(f"   🔍 验证中...")

        # 观察当前状态
        observation_data = self.vision.observe()

        # 检查预期结果
        expected = step.expected_outcome or ""

        # 简单验证：检查摘要中是否包含关键词
        summary = observation_data.get('summary', '')
        success = True

        if expected and expected not in summary:
            print(f"   ⚠️  预期: {expected}")
            print(f"   📍 实际: {summary}")
            success = False
        else:
            print(f"   ✅ 验证通过")

        return ActionResult(
            success=success,
            action=step,
            summary=summary
        )

    def _do_think(self, step) -> ActionResult:
        """思考/分析"""
        print(f"   🤔 思考: {step.description}")

        # 这里可以调用 LLM 进行更复杂的分析
        # 目前简单返回成功
        return ActionResult(
            success=True,
            action=step,
            summary="思考完成"
        )

    # =========================================================================
    # 控制方法
    # =========================================================================

    def stop(self):
        """停止当前任务"""
        print("\n🛑 正在停止...")
        self.should_stop = True

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'is_running': self.is_running,
            'planning_status': self.planning.get_status(),
            'memory_stats': self.planning.get_memory_stats()
        }
