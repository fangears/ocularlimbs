"""
记忆系统
存储和管理 Agent 的经验和知识
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class Memory:
    """记忆项"""
    timestamp: str
    type: str  # 'observation', 'action', 'result', 'error', 'learning'
    content: Dict[str, Any]
    importance: float = 0.5  # 0-1，重要性评分


class MemorySystem:
    """记忆系统"""

    def __init__(self, max_size: int = 100, persist_path: Optional[str] = None):
        self.max_size = max_size
        self.persist_path = persist_path
        self._memories: List[Memory] = []

        # 加载持久化记忆
        if persist_path and os.path.exists(persist_path):
            self._load()

    def add(self, memory_type: str, content: Dict[str, Any], importance: float = 0.5):
        """添加记忆"""
        memory = Memory(
            timestamp=datetime.now().isoformat(),
            type=memory_type,
            content=content,
            importance=importance
        )

        self._memories.append(memory)

        # 如果超过最大容量，删除不重要的记忆
        if len(self._memories) > self.max_size:
            self._cleanup()

        # 自动保存
        if self.persist_path:
            self._save()

    def get_recent(self, count: int = 10, memory_type: Optional[str] = None) -> List[Memory]:
        """获取最近的记忆"""
        memories = self._memories

        if memory_type:
            memories = [m for m in memories if m.type == memory_type]

        return memories[-count:]

    def get_important(self, count: int = 10, memory_type: Optional[str] = None) -> List[Memory]:
        """获取重要的记忆"""
        memories = self._memories

        if memory_type:
            memories = [m for m in memories if m.type == memory_type]

        # 按重要性排序
        memories = sorted(memories, key=lambda m: m.importance, reverse=True)
        return memories[:count]

    def search(self, query: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        # 简单的关键词搜索
        query_lower = query.lower()
        results = []

        for memory in self._memories:
            # 在内容中搜索
            content_str = json.dumps(memory.content, ensure_ascii=False).lower()
            if query_lower in content_str:
                results.append(memory)

        return results[:limit]

    def find_pattern(self, pattern: Dict[str, Any]) -> List[Memory]:
        """查找匹配特定模式的记忆"""
        results = []

        for memory in self._memories:
            match = True
            for key, value in pattern.items():
                if key not in memory.content or memory.content[key] != value:
                    match = False
                    break

            if match:
                results.append(memory)

        return results

    def learn_from_success(self, action: str, context: Dict[str, Any]):
        """从成功中学习"""
        self.add(
            memory_type='learning',
            content={
                'lesson': 'success',
                'action': action,
                'context': context
            },
            importance=0.7
        )

    def learn_from_failure(self, action: str, error: str, context: Dict[str, Any]):
        """从失败中学习"""
        self.add(
            memory_type='learning',
            content={
                'lesson': 'failure',
                'action': action,
                'error': error,
                'context': context
            },
            importance=0.9  # 失败更重要
        )

    def get_context_summary(self, last_n: int = 5) -> str:
        """获取上下文摘要"""
        recent = self.get_recent(last_n)
        if not recent:
            return "无历史记录"

        summary_parts = []
        for memory in recent:
            if memory.type == 'observation':
                summary_parts.append(f"观察: {memory.content.get('summary', '')}")
            elif memory.type == 'action':
                summary_parts.append(f"操作: {memory.content.get('description', '')}")
            elif memory.type == 'result':
                success = memory.content.get('success', False)
                summary_parts.append(f"结果: {'成功' if success else '失败'}")
            elif memory.type == 'learning':
                lesson = memory.content.get('lesson', '')
                summary_parts.append(f"学习: {lesson}")

        return " | ".join(summary_parts)

    def _cleanup(self):
        """清理不重要的记忆"""
        # 按重要性排序，保留重要的
        self._memories = sorted(
            self._memories,
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )[:self.max_size]

    def _save(self):
        """保存到文件"""
        if not self.persist_path:
            return

        try:
            os.makedirs(os.path.dirname(self.persist_path) or '.', exist_ok=True)

            data = [
                {
                    'timestamp': m.timestamp,
                    'type': m.type,
                    'content': m.content,
                    'importance': m.importance
                }
                for m in self._memories
            ]

            with open(self.persist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")

    def _load(self):
        """从文件加载"""
        if not self.persist_path or not os.path.exists(self.persist_path):
            return

        try:
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._memories = [
                Memory(
                    timestamp=item['timestamp'],
                    type=item['type'],
                    content=item['content'],
                    importance=item.get('importance', 0.5)
                )
                for item in data
            ]
        except Exception as e:
            print(f"加载记忆失败: {e}")

    def clear(self):
        """清空所有记忆"""
        self._memories.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        type_counts = {}
        for memory in self._memories:
            type_counts[memory.type] = type_counts.get(memory.type, 0) + 1

        return {
            'total': len(self._memories),
            'by_type': type_counts,
            'oldest': self._memories[0].timestamp if self._memories else None,
            'newest': self._memories[-1].timestamp if self._memories else None
        }
