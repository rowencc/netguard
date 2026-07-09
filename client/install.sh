#!/bin/bash
# ============================================
# NetGuard Client 一键安装脚本
# 支持: macOS / Linux (Ubuntu/Debian/CentOS)
# 用法: curl -fsSL https://raw.githubusercontent.com/rowencc/netguard/main/client/install.sh | bash
# ============================================

set -e

INSTALL_DIR="$HOME/.netguard"
REPO_URL="https://github.com/rowencc/netguard.git"
SERVER_URL="https://net.soccn.com"
CLIENT_ID="client-$(hostname)-$(date +%s)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo "=========================================="
echo "  NetGuard Client 一键安装"
echo "=========================================="
echo ""

# ============================================
# 1. 检测系统
# ============================================
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
        info "检测到 macOS"
    elif [[ -f /etc/debian_version ]]; then
        OS="linux"
        PKG_MANAGER="apt"
        info "检测到 Debian/Ubuntu"
    elif [[ -f /etc/redhat-release ]]; then
        OS="linux"
        PKG_MANAGER="yum"
        info "检测到 CentOS/RHEL"
    else
        OS="linux"
        PKG_MANAGER="unknown"
        info "检测到 Linux"
    fi
}

# ============================================
# 2. 检查/安装 Python
# ============================================
check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_VER=$(python3 --version 2>&1 | sed -E 's/[^0-9]*([0-9]+\.[0-9]+).*/\1/')
        log "Python3 已安装: $(python3 --version)"
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_VER=$(python --version 2>&1 | sed -E 's/[^0-9]*([0-9]+\.[0-9]+).*/\1/')
        log "Python 已安装: $(python --version)"
        PYTHON_CMD="python"
    else
        info "正在安装 Python3..."
        if [[ "$OS" == "macos" ]]; then
            if ! command -v brew &>/dev/null; then
                err "请先安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            fi
            brew install python3
        elif [[ "$PKG_MANAGER" == "apt" ]]; then
            sudo apt update -qq && sudo apt install -y python3 python3-pip python3-venv -qq
        elif [[ "$PKG_MANAGER" == "yum" ]]; then
            sudo yum install -y python3 python3-pip -q
        fi
        PYTHON_CMD="python3"
        log "Python3 安装完成"
    fi
}

# ============================================
# 3. 安装系统依赖
# ============================================
install_system_deps() {
    info "检查系统依赖..."
    
    # 安装 nmap (可选，用于深度扫描)
    if ! command -v nmap &>/dev/null; then
        info "安装 nmap (可选，用于深度扫描)..."
        if [[ "$OS" == "macos" ]]; then
            brew install nmap 2>/dev/null || true
        elif [[ "$PKG_MANAGER" == "apt" ]]; then
            sudo apt install -y nmap -qq 2>/dev/null || true
        elif [[ "$PKG_MANAGER" == "yum" ]]; then
            sudo yum install -y nmap -q 2>/dev/null || true
        fi
    fi
    
    # 检查 git
    if ! command -v git &>/dev/null; then
        info "安装 git..."
        if [[ "$OS" == "macos" ]]; then
            xcode-select --install 2>/dev/null || true
        elif [[ "$PKG_MANAGER" == "apt" ]]; then
            sudo apt install -y git -qq
        elif [[ "$PKG_MANAGER" == "yum" ]]; then
            sudo yum install -y git -q
        fi
    fi
}

# ============================================
# 4. 下载客户端代码
# ============================================
download_client() {
    if [[ -d "$INSTALL_DIR" ]]; then
        info "更新客户端..."
        cd "$INSTALL_DIR"
        git pull origin main -q
    else
        info "下载客户端..."
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" -q
    fi
    log "客户端代码就绪"
}

# ============================================
# 5. 安装 Python 依赖
# ============================================
install_deps() {
    info "安装 Python 依赖..."
    cd "$INSTALL_DIR/client"
    
    if [[ ! -d "venv" ]]; then
        $PYTHON_CMD -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    log "依赖安装完成"
}

# ============================================
# 6. 配置客户端
# ============================================
configure() {
    info "配置客户端..."
    
    mkdir -p "$INSTALL_DIR/client/config"
    
    # 生成唯一 client_id
    CLIENT_ID="client-$(hostname)-$(date +%s)"
    
    cat > "$INSTALL_DIR/client/config/client.json" << EOF
{
  "server_url": "$SERVER_URL",
  "api_key": "netguard-sync-key-2024",
  "client_id": "$CLIENT_ID",
  "scan_interval": 300,
  "scan_subnets": [],
  "use_websocket": true
}
EOF
    
    log "配置完成: $CLIENT_ID"
}

# ============================================
# 7. 创建启动脚本
# ============================================
create_scripts() {
    # 启动脚本
    cat > "$INSTALL_DIR/start.sh" << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")/client"
source venv/bin/activate
echo "NetGuard Client 启动中..."
python3 -m app.main "$@"
SCRIPT
    chmod +x "$INSTALL_DIR/start.sh"
    
    # 停止脚本
    cat > "$INSTALL_DIR/stop.sh" << 'SCRIPT'
#!/bin/bash
PID_FILE="$HOME/.netguard/client.pid"
if [[ -f "$PID_FILE" ]]; then
    kill $(cat "$PID_FILE") 2>/dev/null
    rm "$PID_FILE"
    echo "NetGuard Client 已停止"
else
    # 尝试通过进程名查找
    pkill -f "app.main" 2>/dev/null && echo "NetGuard Client 已停止" || echo "客户端未运行"
fi
SCRIPT
    chmod +x "$INSTALL_DIR/stop.sh"
    
    # 状态脚本
    cat > "$INSTALL_DIR/status.sh" << 'SCRIPT'
#!/bin/bash
PID_FILE="$HOME/.netguard/client.pid"
if [[ -f "$PID_FILE" ]] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "NetGuard Client: 运行中 (PID: $(cat $PID_FILE))"
else
    echo "NetGuard Client: 未运行"
fi
SCRIPT
    chmod +x "$INSTALL_DIR/status.sh"
    
    # 创建符号链接到 /usr/local/bin (可选)
    if [[ -w /usr/local/bin ]]; then
        ln -sf "$INSTALL_DIR/start.sh" /usr/local/bin/netguard-start
        ln -sf "$INSTALL_DIR/stop.sh" /usr/local/bin/netguard-stop
        ln -sf "$INSTALL_DIR/status.sh" /usr/local/bin/netguard-status
        log "已创建快捷命令: netguard-start / netguard-stop / netguard-status"
    fi
}

# ============================================
# 8. 启动客户端
# ============================================
start_client() {
    info "启动客户端..."
    
    cd "$INSTALL_DIR/client"
    source venv/bin/activate
    
    nohup python3 -m app.main > "$INSTALL_DIR/client.log" 2>&1 &
    echo $! > "$INSTALL_DIR/client.pid"
    
    sleep 2
    
    if [[ -f "$INSTALL_DIR/client.pid" ]] && kill -0 $(cat "$INSTALL_DIR/client.pid") 2>/dev/null; then
        log "客户端启动成功 (PID: $(cat $INSTALL_DIR/client.pid))"
    else
        warn "客户端启动失败，请查看日志: $INSTALL_DIR/client.log"
    fi
}

# ============================================
# 主流程
# ============================================
detect_os
check_python
install_system_deps
download_client
install_deps
configure
create_scripts
start_client

echo ""
echo "=========================================="
echo "  安装完成!"
echo "=========================================="
echo ""
echo "  安装目录: $INSTALL_DIR"
echo "  配置文件: $INSTALL_DIR/client/config/client.json"
echo "  日志文件: $INSTALL_DIR/client.log"
echo ""
echo "  管理命令:"
echo "    启动: $INSTALL_DIR/start.sh"
echo "    停止: $INSTALL_DIR/stop.sh"
echo "    状态: $INSTALL_DIR/status.sh"
echo ""
echo "  或使用快捷命令 (需要 sudo):"
echo "    netguard-start"
echo "    netguard-stop"
echo "    netguard-status"
echo ""
echo "  打开 https://net.soccn.com/ 查看设备"
echo ""
