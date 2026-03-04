# OcularLimbs - AI 的眼睛和手脚

> 为 AI Claude 提供真正的视觉和操作能力，一键安装，开箱即用！

## 🎯 这是什么？

OcularLimbs 是一个**完整的 AI Agent 系统**，让 Claude 可以：
- **👁️ 看见**：实时捕获屏幕、识别文字、理解 UI
- **🧠 思考**：规划任务、做出决策、学习经验
- **🦾 行动**：控制鼠标、键盘、窗口操作

**一句话：让 AI 真正地使用电脑！**

## ⚡ 一键安装（推荐）

### Windows 用户

```
双击运行: 一键安装.bat
```

就这么简单！

安装完成后：
- ✅ 桌面快捷方式
- ✅ 开机自动启动
- ✅ 图形化控制面板
- ✅ Web 管理界面

### 命令行安装

```bash
# 运行安装脚本
python install.py

# 或使用 GUI 控制面板
python gui_launcher.py
```

## 🚀 快速开始

### 第一次使用

1. **启动服务**
   - 双击桌面 "OcularLimbs" 图标
   - 或运行 `gui_launcher.py`

2. **打开控制界面**
   - 浏览器自动打开 http://localhost:8848
   - 或手动访问

3. **开始使用**
   - 在 Web 界面点击功能按钮
   - 或使用 Python SDK

### Python 使用示例

```python
from ocularlimbs_client import see, capture, click, type_text

# 查看屏幕
info = see()

# 捕获截图
capture(save_path='screenshot.png')

# 点击操作
click(100, 200)

# 输入文本
type_text("Hello World")
```

## 📊 核心功能

### 1. 视觉能力 👁️

| 功能 | 说明 | API |
|------|------|-----|
| 屏幕捕获 | 实时获取屏幕 | `see()` |
| OCR 识别 | 识别屏幕文字 | `find_text("text")` |
| UI 理解 | 识别按钮、输入框 | `see()['elements']` |
| 差异检测 | 检测屏幕变化 | `compare(before, after)` |

### 2. 操作能力 🦾

| 功能 | 说明 | API |
|------|------|-----|
| 鼠标控制 | 点击、拖拽、滚动 | `click(x, y)` |
| 键盘输入 | 输入文本、快捷键 | `type_text("Hello")` |
| 窗口操作 | 激活、移动、关闭 | `activate_window("Notepad")` |
| 安全保护 | 防止误操作 | `safety_enabled=True` |

### 3. 智能压缩 📦

| 预设 | 大小 | 说明 |
|------|------|------|
| ultra_fast | 45 KB | 实时监控 |
| fast | 74 KB | 日常使用 |
| balanced | 137 KB | 推荐 ⭐ |
| quality | 231 KB | 高质量 |
| archival | 433 KB | 无损存档 |

### 4. 自动清理 🧹

| 规则 | 说明 |
|------|------|
| 重复检测 | MD5 哈希值 |
| 质量检测 | 尺寸、黑屏、模糊 |
| 过期清理 | 自动删除旧文件 |
| 损坏检测 | 自动修复或删除 |

## 🎮 使用场景

### 场景 1: 自动化测试

```python
# 打开应用
execute("打开计算器")

# 执行操作
click(500, 400)
type_text("123+456=")

# 验证结果
capture(save_path='result.png')
```

### 场景 2: RPA 自动化

```python
# 批量处理
for file in files:
    execute(f"打开 {file}")
    execute("点击保存")
    execute("关闭")
```

### 场景 3: 游戏辅助

```python
# 类似 BetterGI
while True:
    see()  # 观察屏幕
    click(find("怪物"))
    time.sleep(1)
```

### 场景 4: 屏幕监控

```python
# 定时截图
while True:
    capture(save_time=f'auto_{time.time()}.png')
    time.sleep(60)
```

## 📁 项目结构

```
ocularlimbs/
├── 🎯 一键安装.bat           # Windows 一键安装
├── 🎮 gui_launcher.py        # 图形化控制面板
├── 🚀 start_service.py       # 快速启动脚本
│
├── core/                     # 核心模块
│   ├── types.py              # 类型定义
│   └── orchestrator.py       # 任务编排
│
├── vision/                   # 视觉模块
│   ├── capture.py            # 屏幕捕获
│   ├── ocr.py                # 文字识别
│   ├── ui_parser.py          # UI 理解
│   ├── diff_detector.py      # 差异检测
│   ├── smart_compression.py  # 智能压缩
│   └── image_cleaner.py      # 图片清理
│
├── action/                   # 操作模块
│   ├── mouse.py              # 鼠标控制
│   ├── keyboard.py           # 键盘控制
│   ├── window.py             # 窗口管理
│   └── safety.py             # 安全保护
│
├── planning/                 # 规划模块
│   ├── memory.py             # 记忆系统
│   └── planner.py            # 任务规划
│
├── ocularlimbs_service.py    # 后台服务
├── ocularlimbs_client.py     # Python SDK
├── agent.py                  # Agent 入口
│
└── ocularlimbs_workspace/    # 工作目录
    ├── screenshots/          # 截图保存
    ├── logs/                 # 日志文件
    └── compression_samples/  # 压缩示例
```

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 屏幕捕获 | mss | 跨平台 |
| 图像处理 | Pillow, OpenCV | 压缩、识别 |
| OCR | Tesseract, PaddleOCR | 文字识别 |
| 输入控制 | pyautogui | 鼠标键盘 |
| Web 服务 | HTTP Server | REST API |
| 压缩 | JPEG, WebP, PNG | 多种格式 |

## 📚 文档

- [**一键安装指南**](一键安装指南.md) - 快速上手
- [**服务使用指南**](SERVICE_GUIDE.md) - API 文档
- [**压缩优化指南**](COMPRESSION_GUIDE.md) - 图片压缩
- [**清理功能指南**](IMAGE_CLEANER_GUIDE.md) - 自动清理
- [**项目总结**](PROJECT_SUMMARY.md) - 完整说明

## 🎁 快捷命令

### Windows 快捷方式

```
双击 "启动_OcularLimbs.bat"  # 启动服务
双击 "停止_OcularLimbs.bat"   # 停止服务
```

### Python SDK

```python
# 查看屏幕
from ocularlimbs_client import see
info = see()

# 捕获屏幕
from ocularlimbs_client import capture
capture('test.png')

# 执行任务
from ocularlimbs_client import execute
execute("打开记事本")
```

### HTTP API

```bash
# 查看屏幕
curl http://localhost:8848/api/see

# 点击
curl -X POST http://localhost:8848/api/click \
  -H "Content-Type: application/json" \
  -d '{"x": 100, "y": 200}'
```

## 🔧 配置选项

### 基础配置

```python
from ocularlimbs import SystemConfig

config = SystemConfig(
    vision={'ocr_engine': 'paddleocr'},  # OCR 引擎
    action={'safety_enabled': True},    # 安全模式
    planning={'model': 'claude-sonnet-4-6'}  # AI 模型
)
```

### 压缩配置

```python
# 使用 fast 预设（日常使用）
client.capture(compression='fast')

# 使用 ultra_fast 预设（实时）
client.capture(compression='ultra_fast')
```

### 清理配置

```python
# 自动清理过期文件
cleaner.clean_directory(
    "screenshots",
    max_age_days=7  # 保留7天
)
```

## 🆘 故障排除

### 问题: 服务无法启动

```bash
# 检查端口
netstat -an | findstr 8848

# 更换端口
python ocularlimbs_service.py --port 8849
```

### 问题: 模块加载失败

```bash
# 重新安装依赖
pip install -r requirements.txt

# 重新安装项目
pip install -e .
```

### 问题: OCR 不工作

```bash
# 安装 Tesseract
# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# 或使用 PaddleOCR
pip install paddleocr
```

## 🎯 最佳实践

### 1. 日常使用

```python
# 使用 balanced 预设（最佳平衡）
client = OcularLimbsClient()
```

### 2. 性能优先

```python
# 使用 fast 预设（快速响应）
client.capture(compression='fast')
```

### 3. 质量优先

```python
# 使用 quality 预设（高准确率）
client.capture(compression='quality')
```

### 4. 自动清理

```python
# 定期清理过期文件
auto = AutoCleaner(directories=["screenshots"])
auto.start()  # 后台自动清理
```

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 屏幕捕获 | <50ms | 实时捕获 |
| OCR 识别 | 100-500ms | 取决于文字量 |
| 图片压缩 | 200-400ms | 取决于预设 |
| 鼠标操作 | <10ms | 几乎瞬时 |
| 键盘操作 | <50ms | 包含延迟 |
| API 响应 | <100ms | HTTP 请求 |

## 🎉 总结

### 核心优势

- ✅ **一键安装**：双击即可使用
- ✅ **图形界面**：可视化控制面板
- ✅ **Web 管理**：浏览器直接操作
- ✅ **Python SDK**：代码轻松调用
- ✅ **自动启动**：开机后台运行
- ✅ **智能压缩**：节省 90% 空间
- ✅ **自动清理**：定期维护

### 适用场景

- 🎮 **游戏辅助**：类似 BetterGI
- 🧪 **自动化测试**：UI 测试、E2E 测试
- 🤖 **RPA 办公**：重复任务自动化
- 👁️ **屏幕监控**：定期截图、状态监控
- 🔬 **数据分析**：屏幕数据采集

### 立即开始

```bash
# Windows 用户
双击 "一键安装.bat"

# 其他用户
python install.py

# 或使用 GUI
python gui_launcher.py
```

---

**OcularLimbs - 让 AI 拥有真正的眼睛和手脚！** 🎯👁️🦾

**Made with ❤️ by Claude**
