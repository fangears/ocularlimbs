#!/usr/bin/env bash
# install.sh — OcularLimbs 一键安装脚本
#
# 用法:
#   ./install.sh
#
# 此脚本会：
#   1. 安装 Python 依赖
#   2. 配置 MCP 服务器到 Claude Code
#   3. 安装技能和命令

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════╗"
echo "║        OcularLimbs - AI 的眼和手脚             ║"
echo "║    Eyes and Hands for Claude Code              ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python 3${NC}"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} 检测到 Python ${PYTHON_VERSION}"

# 检查 pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}错误: 未找到 pip${NC}"
    exit 1
fi

PIP_CMD=$(command -v pip3 &> /dev/null && echo "pip3" || echo "pip")
echo -e "${GREEN}✓${NC} 检测到 pip"

# 检查 Claude Code 配置目录
CLAUDE_DIR="$HOME/.claude"
if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo -e "${YELLOW}创建 Claude Code 配置目录${NC}"
    mkdir -p "$CLAUDE_DIR"
fi

# 安装 Python 包
echo ""
echo -e "${YELLOW}正在安装 Python 依赖...${NC}"
cd "$SCRIPT_DIR"

if [[ -f "requirements.txt" ]]; then
    $PIP_CMD install -e . -q
    echo -e "${GREEN}✓${NC} Python 依赖安装完成"
else
    echo -e "${RED}错误: 未找到 requirements.txt${NC}"
    exit 1
fi

# 检查 settings.json
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "{}" > "$SETTINGS_FILE"
fi

# 添加 MCP 服务器配置
echo ""
echo -e "${YELLOW}配置 MCP 服务器...${NC}"

# 使用 Python 来安全地修改 JSON
python3 << 'PYTHON_SCRIPT'
import json
import os
import sys

claude_dir = os.path.expanduser("~/.claude")
settings_file = os.path.join(claude_dir, "settings.json")

# 读取现有配置
try:
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# 确保 mcpServers 存在
if "mcpServers" not in settings:
    settings["mcpServers"] = {}

# 添加 ocularlimbs MCP 服务器
settings["mcpServers"]["ocularlimbs"] = {
    "command": "python",
    "args": ["-m", "ocularlimbs.mcp_server"],
    "env": {}
}

# 写回文件
with open(settings_file, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("✓ MCP 服务器配置已添加")
PYTHON_SCRIPT

# 安装技能
echo ""
echo -e "${YELLOW}安装技能和命令...${NC}"

# 创建 skills 目录
SKILLS_DIR="$CLAUDE_DIR/skills/ocularlimbs"
mkdir -p "$SKILLS_DIR"

# 复制技能文件
if [[ -f "skills/ocularlimbs/SKILL.md" ]]; then
    cp "skills/ocularlimbs/SKILL.md" "$SKILLS_DIR/"
    echo -e "${GREEN}✓${NC} 技能文件已安装"
fi

# 创建 commands 目录
COMMANDS_DIR="$CLAUDE_DIR/commands"
mkdir -p "$COMMANDS_DIR"

# 复制命令文件
if [[ -f "commands/see.md" ]]; then
    cp "commands/see.md" "$COMMANDS_DIR/"
fi
if [[ -f "commands/capture.md" ]]; then
    cp "commands/capture.md" "$COMMANDS_DIR/"
fi
if [[ -f "commands/click.md" ]]; then
    cp "commands/click.md" "$COMMANDS_DIR/"
fi

echo -e "${GREEN}✓${NC} 命令文件已安装"

# 完成
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗"
echo "║              安装完成！                                ║"
echo "╚════════════════════════════════════════════════╝${NC}"
echo ""
echo "现在你可以："
echo "  1. 重启 Claude Code"
echo "  2. 使用 MCP 工具: see(), capture(), click(), type_text() 等"
echo "  3. 或使用命令: /see, /capture, /click"
echo ""
echo -e "${YELLOW}注意: 首次使用时，服务会自动启动${NC}"
echo ""
