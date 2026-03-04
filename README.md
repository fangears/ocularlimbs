# OcularLimbs - AI 的眼睛和手脚

> 为 Claude Code 提供真正的视觉和操作能力，一键安装，开箱即用！

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)

## ✨ 特性

OcularLimbs 通过 MCP (Model Context Protocol) 为 Claude Code 提供：

- **👁️ 视觉能力**：实时屏幕捕获、OCR 文字识别、UI 元素理解
- **🦾 操作能力**：鼠标点击、键盘输入、窗口管理
- **🧠 智能理解**：自动分析屏幕内容、识别 UI 结构
- **⚡ 极速响应**：优化的图像压缩、毫秒级操作响应
- **🔌 无缝集成**：作为 MCP 服务器直接集成到 Claude Code

## 🚀 一键安装

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/fangears/ocularlimbs/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/fangears/ocularlimbs/main/install.ps1 | iex
```

### 从源码安装

```bash
git clone https://github.com/fangears/ocularlimbs.git
cd ocularlimbs
./install.sh
```

## 📖 在 Claude Code 中使用

安装完成后，在 Claude Code 中直接使用：

### 查看屏幕

```
请帮我看看当前屏幕上有什么
```

### 捕获截图

```
捕获当前屏幕并保存为 test.png
```

### 查找并点击

```
查找屏幕上的"确定"按钮并点击
```

### 输入文本

```
在当前位置输入 "Hello World"
```

### 执行任务

```
打开计算器并计算 123 + 456
```

## 🛠️ Python SDK

也可以在 Python 代码中直接使用：

```python
from ocularlimbs import see, capture, click, type_text

# 查看屏幕
screen = see()
print(f"屏幕: {screen['width']}x{screen['height']}")

# 捕获截图
capture('test.png')

# 点击屏幕
click(100, 200)

# 输入文本
type_text("Hello World")
```

## 📁 项目结构

```
ocularlimbs/
├── install.sh              # 一键安装脚本
├── requirements.txt        # Python 依赖
├── mcp-configs/            # MCP 配置
├── src/
│   └── ocularlimbs/
│       ├── __init__.py     # 包入口
│       ├── client.py       # 客户端 API
│       ├── mcp_server.py   # MCP 服务器
│       ├── service.py      # 后台服务
│       ├── core/           # 核心模块
│       ├── vision/         # 视觉模块
│       ├── action/         # 操作模块
│       └── planning/       # 规划模块
└── scripts/                # 辅助脚本
```

## 🔧 系统要求

- Python 3.8+
- Tesseract OCR (可选)
- 依赖项见 `requirements.txt`

### 安装 Tesseract

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

安装完成后，MCP 配置会自动添加到 `~/.claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ocularlimbs": {
      "command": "python",
      "args": ["-m", "ocularlimbs.mcp_server"],
      "env": {
        "OCULARLIMBS_HOME": "~/.ocularlimbs"
      }
    }
  }
}
```

## 🚦 故障排除

### 服务无法启动

```bash
# 检查服务状态
ocularlimbs status

# 重启服务
ocularlimbs restart
```

### MCP 服务器未连接

1. 检查 Claude Code 的 MCP 配置
2. 确保服务正在运行：`ocularlimbs status`
3. 查看 MCP 日志：`~/.ocularlimbs/mcp.log`

### OCR 不工作

安装 Tesseract OCR：
```bash
# Ubuntu
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

## 📚 文档

- [快速开始](docs/quickstart.md)
- [API 文档](docs/api.md)
- [MCP 集成](docs/mcp.md)
- [故障排除](docs/troubleshooting.md)

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 👨‍💻 作者

fangears - [GitHub](https://github.com/fangears)

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code](https://claude.ai/code)
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) - 项目结构灵感

---

**OcularLimbs - 让 AI 真正地看到和操作你的电脑！** 👁️🦾
