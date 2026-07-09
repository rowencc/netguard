#!/bin/bash
# NetGuard Client 一键升级脚本

set -e

INSTALL_DIR="$HOME/.netguard"
REPO_URL="https://github.com/rowencc/netguard.git"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo ""
echo "=========================================="
echo "  NetGuard Client 升级"
echo "=========================================="
echo ""

# 停止客户端
if [[ -f "$INSTALL_DIR/client.pid" ]]; then
    PID=$(cat "$INSTALL_DIR/client.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "停止客户端..."
        kill "$PID" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$INSTALL_DIR/client.pid"
fi

# 更新代码
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "更新代码..."
    cd "$INSTALL_DIR"
    git pull origin main -q
    log "代码更新完成"
else
    echo "重新安装..."
    rm -rf "$INSTALL_DIR"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" -q
fi

# 重新安装依赖
echo "更新依赖..."
cd "$INSTALL_DIR/client"
source venv/bin/activate 2>/dev/null || python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "依赖更新完成"

# 启动客户端
echo "启动客户端..."
nohup python3 -m app.main > "$INSTALL_DIR/client.log" 2>&1 &
echo $! > "$INSTALL_DIR/client.pid"

sleep 2

if [[ -f "$INSTALL_DIR/client.pid" ]] && kill -0 $(cat "$INSTALL_DIR/client.pid") 2>/dev/null; then
    log "升级完成! 客户端已启动 (PID: $(cat $INSTALL_DIR/client.pid))"
else
    warn "启动失败，请查看日志: $INSTALL_DIR/client.log"
fi

echo ""
