---
description: 捕获屏幕截图并可选保存到文件
---

# /capture - 屏幕截图

捕获当前屏幕截图，可选择保存到文件或仅捕获。

## 使用方法

```
/capture [filename] [compression]
```

### 参数

- **filename** (可选): 保存的文件名，如 `screenshot.png`
- **compression** (可选): 压缩级别
  - `ultra_fast` - 极速
  - `fast` - 快速
  - `balanced` - 平衡（默认）
  - `quality` - 高质量
  - `archival` - 存档质量

## 示例

```
# 仅捕获（不保存）
/capture

# 保存到文件
/capture screenshot.png

# 高质量保存
/capture screenshot.png quality
```

## 返回信息

- 截图尺寸
- 保存路径（如果指定了文件名）
- 压缩级别
- 文件大小

## 注意事项

- 文件会保存到当前工作目录
- 支持的格式: PNG, JPEG
- 首次使用会自动启动后台服务
