# 贡献指南

感谢你对 OcularLimbs 的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

1. 在 Issues 中搜索，确认问题未被报告
2. 创建新 Issue，包含：
   - 清晰的标题
   - 详细的复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（操作系统、Python 版本等）
   - 相关日志或截图

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- **Python**: 遵循 PEP 8
- **提交信息**: 使用 Conventional Commits 格式
  - `feat:` 新功能
  - `fix:` Bug 修复
  - `docs:` 文档更新
  - `refactor:` 代码重构
  - `test:` 测试相关
  - `chore:` 构建/工具链相关

### 测试

- 为新功能添加测试
- 确保所有测试通过：`pytest`
- 尽量保持测试覆盖率在 80% 以上

### 文档

- 更新相关文档
- 为新功能添加使用示例
- 更新 README（如果需要）

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/anthropics/ocularlimbs.git
cd ocularlimbs

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/
```

## 项目结构

- `src/ocularlimbs/` - 主要代码
- `tests/` - 测试文件
- `skills/` - Claude Code 技能
- `commands/` - Claude Code 命令
- `docs/` - 文档

## 许可证

贡献的代码将使用 MIT 许可证发布。
