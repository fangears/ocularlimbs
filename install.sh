#!/usr/bin/env bash
# install.sh — OcularLimbs 一键安装脚本
#
# Usage:
#   ./install.sh
#   curl -fsSL https://raw.githubusercontent.com/fangears/ocularlimbs/main/install.sh | bash
#
# 支持: Linux, macOS, Windows(WSL)

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS=linux;;
        Darwin*)    OS=macos;;
        MINGW*|MSYS*|CYGWIN*) OS=windows;;
        *)          OS=unknown;;
    esac
    log_info "检测到操作系统: $OS"
}

# 检测 Python 版本
check_python() {
    log_info "检查 Python 环境..."

    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python 3，请先安装 Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_info "Python 版本: $PYTHON_VERSION"
}

# 检测并创建虚拟环境
setup_venv() {
    log_info "设置虚拟环境..."

    VENV_DIR="$HOME/.ocularlimbs/venv"

    if [ ! -d "$VENV_DIR" ]; then
        log_info "创建虚拟环境: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi

    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    log_success "虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    log_info "安装 Python 依赖..."

    # 升级 pip
    pip install --upgrade pip -q

    # 安装依赖
    pip install -r requirements.txt -q

    log_success "依赖安装完成"
}

# 安装核心模块
install_core() {
    log_info "安装 OcularLimbs 核心模块..."

    CORE_DIR="$HOME/.ocularlimbs"
    mkdir -p "$CORE_DIR"

    # 复制核心文件
    cp -r src/* "$CORE_DIR/"

    log_success "核心模块安装完成"
}

# 配置 MCP 服务器
configure_mcp() {
    log_info "配置 MCP 服务器..."

    CLAUDE_DIR="$HOME/.claude"
    MCP_CONFIG="$CLAUDE_DIR/claude_desktop_config.json"

    # 创建 .claude 目录
    mkdir -p "$CLAUDE_DIR"

    # 备份现有配置
    if [ -f "$MCP_CONFIG" ]; then
        BACKUP="$MCP_CONFIG.backup.$(date +%Y%m%d%H%M%S)"
        log_info "备份现有配置: $BACKUP"
        cp "$MCP_CONFIG" "$BACKUP"
    fi

    # 创建或更新配置
    if [ ! -f "$MCP_CONFIG" ]; then
        echo '{"mcpServers":{}}' > "$MCP_CONFIG"
    fi

    # 添加 OcularLimbs MCP 服务器
    python3 scripts/update_mcp_config.py

    log_success "MCP 配置完成"
}

# 安装系统依赖（Tesseract 等）
install_system_deps() {
    log_info "安装系统依赖..."

    case "$OS" in
        linux)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils -qq
            elif command -v yum &> /dev/null; then
                sudo yum install -y tesseract tesseract-devel poppler-utils -q
            elif command -v brew &> /dev/null; then
                brew install tesseract poppler -q
            fi
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install tesseract poppler -q
            else
                log_warn "建议安装 Homebrew: https://brew.sh"
            fi
            ;;
        windows)
            log_warn "Windows 用户请手动安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
            ;;
    esac

    log_success "系统依赖安装完成"
}

# 创建快捷命令
create_commands() {
    log_info "创建快捷命令..."

    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"

    # 创建 ocularlimbs 命令
    cat > "$BIN_DIR/ocularlimbs" << 'EOF'
#!/usr/bin/env bash
source "$HOME/.ocularlimbs/venv/bin/activate"
python3 -m ocularlimbs "$@"
EOF

    chmod +x "$BIN_DIR/ocularlimbs"

    # 添加到 PATH（如果需要）
    if ! echo "$PATH" | grep -q "$BIN_DIR"; then
        echo "" >> ~/.bashrc
        echo "# OcularLimbs" >> ~/.bashrc
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.bashrc
        log_info "已添加到 PATH，请运行: source ~/.bashrc"
    fi

    log_success "快捷命令创建完成"
}

# 启动服务
start_service() {
    log_info "启动 OcularLimbs 服务..."

    # 后台启动服务
    nohup python3 -m ocularlimbs.service > /dev/null 2>&1 &

    # 等待服务就绪
    sleep 3

    log_success "服务已启动"
}

# 运行测试
run_test() {
    log_info "运行测试..."

    python3 -m ocularlimbs test

    log_success "测试完成"
}

# 显示完成信息
show_completion() {
    cat << 'EOF'

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     ✨ OcularLimbs 安装成功！                              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

📚 快速开始:

    # 在 Claude Code 中直接使用
    from ocularlimbs import see, capture, click

    # 查看屏幕
    screen = see()

    # 捕获截图
    capture('test.png')

    # 点击屏幕
    click(100, 200)

🔗 Web 管理界面:

    http://localhost:8848

📖 文档:

    https://github.com/fangears/ocularlimbs

🔄 重启服务:

    ocularlimbs restart

🛑 停止服务:

    ocularlimbs stop

EOF
}

# 主安装流程
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     👁️  OcularLimbs - AI 的眼睛和手脚                     ║"
    echo "║     🦾 一键安装脚本                                        ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    detect_os
    check_python
    setup_venv
    install_dependencies
    install_core
    install_system_deps
    configure_mcp
    create_commands
    start_service
    run_test
    show_completion
}

# 运行主程序
main "$@"
