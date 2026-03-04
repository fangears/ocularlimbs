# Windows MCP 服务器配置指南

本文档记录了在 Windows 系统上配置 OcularLimbs MCP 服务器的完整流程和经验总结。

## 📋 配置步骤

### 1. 克隆项目

```bash
git clone https://github.com/fangears/ocularlimbs.git ~/.ocularlimbs
cd ~/.ocularlimbs
```

### 2. 修复 setup.py

**问题**：原始的 `setup.py` 没有指定 `src` 目录，导致包结构不正确。

**解决方案**：修改 `setup.py` 文件：

```python
setup(
    name="ocularlimbs",
    version="0.1.0",
    # ... 其他配置 ...
    package_dir={"": "src"},              # 添加此行
    packages=find_packages(where="src"),  # 修改此行
    # ...
)
```

### 3. 安装包

```bash
cd ~/.ocularlimbs
pip install -e .
```

### 4. 验证安装

```bash
python -c "import ocularlimbs; print(ocularlimbs.__version__)"
```

应该输出版本号：`1.0.0`

### 5. 配置 Claude Code MCP 服务器

编辑 `~/.claude.json` 文件，添加以下配置：

```json
{
  "mcpServers": {
    "ocularlimbs": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ocularlimbs.mcp_server"],
      "env": {}
    }
  }
}
```

或使用 Python 脚本自动添加：

```python
import json

config_path = r"C:\Users\Administrator\.claude.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['ocularlimbs'] = {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "ocularlimbs.mcp_server"],
    "env": {}
}

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
```

### 6. 重启 Claude Code

重启后，ocularlimbs 应该出现在已连接的 MCP 服务器列表中。

## 🔧 故障排除

### 问题 1: 模块导入失败

**症状**：
```
ModuleNotFoundError: No module named 'ocularlimbs'
```

**原因**：`setup.py` 没有正确配置包目录。

**解决方案**：
1. 确保已修改 `setup.py` 添加 `package_dir={"": "src"}`
2. 重新安装：`pip install -e .`

### 问题 2: 编码错误

**症状**：
```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**原因**：Windows 控制台默认使用 GBK 编码。

**解决方案**：使用 ASCII 字符或在 Python 中设置 UTF-8 编码：
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 问题 3: MCP 服务器无法连接

**症状**：Claude Code 显示 `ocularlimbs ✘ failed`

**检查项**：
1. 包是否正确安装：`pip show ocularlimbs`
2. 模块是否可导入：`python -c "import ocularlimbs.mcp_server"`
3. 配置文件是否正确：检查 `~/.claude.json` 中的配置

## 📊 成功标志

配置成功后，您应该看到：

1. ✅ `import ocularlimbs` 不报错
2. ✅ `pip show ocularlimbs` 显示包信息
3. ✅ Claude Code MCP 服务器列表中显示 `ocularlimbs ✔ connected`

## 🎯 可用的 MCP 工具

配置成功后，您可以在 Claude Code 中使用以下工具：

### 视觉工具
- `see()` - 查看屏幕信息
- `capture()` - 捕获屏幕截图

### 操作工具
- `click()` - 鼠标点击
- `type_text()` - 键盘输入
- `press_key()` - 按键操作

### 搜索工具
- `find_text()` - 查找屏幕文字
- `click_text()` - 点击指定文字

## 💡 最佳实践

1. **使用可编辑安装**：`pip install -e .` 便于开发调试
2. **验证配置**：每次修改后先验证模块导入
3. **查看日志**：MCP 服务器日志可以帮助诊断问题
4. **使用 Python 脚本**：自动化配置过程，避免手动编辑错误

## 🔄 更新项目

如果您从上游仓库更新：

```bash
cd ~/.ocularlimbs
git pull
pip install -e . --force-reinstall
```

## 📝 总结

Windows 系统上配置 OcularLimbs MCP 服务器的关键点：

1. **修复 setup.py**：添加 `package_dir` 配置
2. **使用可编辑安装**：便于开发和调试
3. **正确配置 MCP**：使用 JSON 格式配置 stdio 服务器
4. **重启 Claude Code**：使配置生效

---

**配置日期**：2026-03-05
**测试环境**：Windows 11, Python 3.12, Claude Code 2.1.63
