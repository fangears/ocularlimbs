# OcularLimbs - AI 的眼和手脚

> Eyes and Hands for Claude Code - 计算机视觉和自动化框架

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)

> **参考项目**: [everything-claude-code](https://github.com/affaan-m/everything-claude-code) - 项目结构灵感来源

## ✨ 特性

OcularLimbs 通过 MCP (Model Context Protocol) 为 Claude Code 提供：

- **👁️ 视觉能力**：实时屏幕捕获、OCR 文字识别、UI 元素理解
- **🦾 操作能力**：鼠标点击、键盘输入、窗口管理
- **🧠 智能理解**：自动分析屏幕内容、识别 UI 结构
- **⚡ 极速响应**：优化的图像压缩、毫秒级操作响应
- **🔌 无缝集成**：作为 Claude Code 插件和 MCP 服务器
- **🎯 一键安装**：自动配置，开箱即用

## 🚀 快速开始

### 方式 1: 作为 Claude Code 插件安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/fangears/ocularlimbs.git
cd ocularlimbs

# 运行安装脚本
./install.sh
```

安装脚本会自动：
1. ✅ 安装 Python 依赖
2. ✅ 配置 MCP 服务器到 Claude Code
3. ✅ 安装技能和命令

### 方式 2: 手动安装

```bash
# 安装 Python 包
pip install -e .

# 配置 MCP 服务器（添加到 ~/.claude/settings.json）
{
  "mcpServers": {
    "ocularlimbs": {
      "command": "python",
      "args": ["-m", "ocularlimbs.mcp_server"],
      "env": {}
    }
  }
}

# 复制技能文件
cp -r skills/ocularlimbs ~/.claude/skills/
```

## 📖 在 Claude Code 中使用

安装完成后，重启 Claude Code，然后就可以直接使用：

### 通过 MCP 工具使用

```
# 查看屏幕
请帮我看看当前屏幕上有什么

# 捕获截图
捕获当前屏幕并保存为 test.png

# 查找并点击
查找屏幕上的"确定"按钮并点击

# 输入文本
在当前位置输入 "Hello World"

# 执行任务
打开计算器并计算 123 + 456
```

### 通过命令使用

```
/see          # 查看屏幕
/capture      # 捕获截图
/click 确定   # 点击文字
```

### 通过技能使用

Claude 会自动使用 `skills/ocularlimbs/SKILL.md` 中的最佳实践。

## 🛠️ Python SDK

也可以在 Python 代码中直接使用：

```python
from ocularlimbs import see, capture, click, type_text

# 查看屏幕
screen = see()
print(f"屏幕: {screen['width']}x{screen['height']}")

# 捕获截图
capture('test.png')

# 查找并点击文字
from ocularlimbs import click_text
click_text("确定")

# 点击坐标
click(100, 200)

# 输入文本
type_text("Hello World")

# 按键
from ocularlimbs import press_key
press_key('enter')
```

## 📁 项目结构

```
ocularlimbs-unified/
├── .claude-plugin/         # Claude Code 插件配置
│   └── plugin.json         # 插件元数据
├── install.sh              # 一键安装脚本
├── requirements.txt        # Python 依赖
├── setup.py               # 包配置
├── mcp-configs/           # MCP 配置示例
│   └── ocularlimbs.json
├── skills/                # Claude Code 技能
│   └── ocularlimbs/
│       └── SKILL.md       # 眼手工具使用指南
├── commands/              # Claude Code 命令
│   ├── see.md
│   ├── capture.md
│   └── click.md
├── src/
│   └── ocularlimbs/
│       ├── __init__.py    # 包入口
│       ├── client.py      # 客户端 API
│       ├── mcp_server.py  # MCP 服务器
│       ├── service.py     # 后台 HTTP 服务
│       ├── core/          # 核心模块
│       ├── vision/        # 视觉模块
│       ├── action/        # 操作模块
│       └── planning/      # 规划模块
└── tests/                # 测试文件
```

## 🔧 系统要求

- Python 3.8+
- Claude Code CLI
- 依赖项见 `requirements.txt`

### 可选依赖

**Tesseract OCR**（用于更好的文字识别）：

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
下载安装包：https://github.com/UB-Mannheim/tesseract/wiki

## 🎯 MCP 工具列表

| 工具 | 描述 | 参数 |
|------|------|------|
| `see` | 查看屏幕 | - |
| `capture` | 捕获截图 | `filename` (可选), `compression` (可选) |
| `find_text` | 查找文字 | `text` (必需) |
| `click` | 点击坐标 | `x`, `y` (必需) |
| `click_text` | 点击文字 | `text` (必需) |
| `type_text` | 输入文本 | `text` (必需) |
| `press_key` | 按键 | `key` (必需) |
| `execute` | 执行任务 | `goal` (必需) |

## 🔌 MCP 配置

安装完成后，MCP 配置会自动添加到 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "ocularlimbs": {
      "command": "python",
      "args": ["-m", "ocularlimbs.mcp_server"],
      "env": {}
    }
  }
}
```

## 🚦 故障排除

### MCP 服务器未连接

1. 确认安装完成：
   ```bash
   python -c "import ocularlimbs; print('OK')"
   ```

2. 检查 MCP 配置：
   ```bash
   cat ~/.claude/settings.json | grep -A 5 ocularlimbs
   ```

3. 测试 MCP 服务器：
   ```bash
   python -m ocularlimbs.mcp_server
   ```

### 权限问题（macOS）

macOS 需要授予辅助功能权限：
1. 打开"系统偏好设置" > "安全性与隐私" > "隐私"
2. 选择"辅助功能"
3. 添加 Python 或 Terminal

### OCR 识别不准确

安装 Tesseract OCR 可提高识别准确率（见上方"可选依赖"）。

## 📚 文档

- [技能文档](skills/ocularlimbs/SKILL.md) - 完整的使用指南
- [MCP 协议](https://modelcontextprotocol.io/)
- [Claude Code 文档](https://code.claude.com/docs)

## 🤝 贡献

欢迎贡献！请随时提交 Issue 或 Pull Request。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code](https://code.claude.com)
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) - 项目结构灵感

---

**OcularLimbs - 让 AI 真正地看到和操作你的电脑！** 👁️🦾
