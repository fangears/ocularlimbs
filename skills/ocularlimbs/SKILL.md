# OcularLimbs - AI 的眼和手脚

> Eyes and Hands for Claude Code - 计算机视觉和自动化框架

OcularLimbs 为 Claude Code 提供屏幕视觉和鼠标/键盘控制能力，让 AI 能够看到你的屏幕并与之交互。

## 能力概览

### 视觉能力
- **see()** - 查看屏幕，获取屏幕信息和识别到的文字
- **capture()** - 捕获屏幕截图并可选保存到文件

### 操作能力
- **find_text(text)** - 在屏幕上查找文字位置
- **click(x, y)** - 点击屏幕上的指定坐标
- **click_text(text)** - 查找并点击包含指定文字的元素
- **type_text(text)** - 输入文本到当前位置
- **press_key(key)** - 按下指定的键（如 enter、escape、f1）
- **execute(goal)** - 执行自然语言描述的任务

## 典型使用场景

### 场景 1: 查看屏幕状态

```python
# 获取当前屏幕信息
screen = see()
print(f"屏幕: {screen['width']}x{screen['height']}")
print(f"识别到 {screen['texts']} 个文字区域")
```

### 场景 2: 截图保存

```python
# 快速截图（不保存）
capture()

# 保存截图到文件
capture('screenshot.png')

# 使用高质量压缩
capture('screenshot.png', compression='quality')
```

### 场景 3: 查找并点击

```python
# 查找文字
result = find_text("确定")
if result['found']:
    # 点击找到的文字
    click(result['x'], result['y'])

# 或者直接一步完成
click_text("确定")
```

### 场景 4: 表单填写

```python
# 点击输入框
click_text("用户名")

# 输入文字
type_text("myusername")

# 切换到密码框
press_key('tab')

# 输入密码
type_text("mypassword")

# 提交
press_key('enter')
```

### 场景 5: 自然语言任务

```python
# 让 AI 理解并执行
execute("打开计算器")
execute("在浏览器中搜索 OcularLimbs")
execute("关闭当前窗口")
```

## 压缩级别

capture() 函数支持多种压缩预设：

| 级别 | 描述 | 适用场景 |
|------|------|----------|
| ultra_fast | 极速 | 实时预览、调试 |
| fast | 快速 | 频繁截图 |
| balanced | 平衡（默认） | 一般使用 |
| quality | 高质量 | 需要清晰文字 |
| archival | 存档质量 | 保存重要截图 |

## 技术实现

OcularLimbs 采用客户端-服务端架构：

- **服务端**: 运行在后台的 HTTP 服务（端口 8848）
- **客户端**: 简单的 Python API，自动管理服务生命周期
- **MCP 集成**: 支持 Model Context Protocol，可直接在 Claude Code 中使用

### 自动服务管理

客户端会自动检测服务状态：
- 如果服务未运行，自动启动
- 进程退出时自动清理
- 无需手动管理

## 返回值格式

### see() 返回值

```python
{
    'width': 1920,      # 屏幕宽度
    'height': 1080,     # 屏幕高度
    'texts': 15,        # 识别到的文字数量
    'summary': '屏幕 1920x1080',  # 简短描述
    'elements': [...]   # 识别到的元素列表
}
```

### find_text() 返回值

```python
{
    'found': True,      # 是否找到
    'text': '确定',     # 找到的文字
    'x': 100,          # 中心 X 坐标
    'y': 200,          # 中心 Y 坐标
    'bbox': {          # 边界框
        'x': 50,
        'y': 180,
        'width': 100,
        'height': 40
    }
}
```

## 错误处理

所有函数都包含错误处理：

```python
result = click_text("不存在的按钮")
if not result:
    print("未找到按钮")

result = see()
if 'error' in result:
    print(f"错误: {result['error']}")
```

## 安全注意事项

1. **权限**: 某些操作需要屏幕录制/辅助功能权限
2. **确认**: 重要操作前建议先用 see() 确认屏幕状态
3. **测试**: 在自动化脚本中充分测试每个步骤

## 系统要求

- Python 3.8+
- Windows / macOS / Linux
- 依赖包: mss, opencv-python, pytesseract, pyautogui, requests

## 安装

```bash
# 克隆仓库
git clone https://github.com/anthropics/ocularlimbs.git
cd ocularlimbs

# 运行安装脚本
./install.sh
```

安装脚本会自动：
1. 安装 Python 依赖
2. 配置 MCP 服务器到 Claude Code
3. 安装技能和命令

## 示例项目

查看 `examples/` 目录获取完整示例：
- 自动化测试
- GUI 操作
- 数据录入
- 屏幕监控

## 故障排除

### 服务无法启动

```bash
# 检查端口是否被占用
netstat -an | grep 8848

# 手动启动服务
python -m ocularlimbs.service
```

### OCR 识别不准确

```bash
# 安装 Tesseract 数据包
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
```

## 贡献

欢迎贡献！请查看 CONTRIBUTING.md 了解详情。

## 许可证

MIT License - 详见 LICENSE 文件
