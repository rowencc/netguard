#!/bin/bash
# NetGuard 停止脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

kill_port() {
    local pid=$(lsof -i :$1 -P -t 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null || true
        sleep 1
        log "Stopped process on port $1"
    fi
}

echo "Stopping NetGuard services..."

kill_port 8089
kill_port 3000

[ -f "$LOG_DIR/backend.pid" ] && kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null && rm "$LOG_DIR/backend.pid"
[ -f "$LOG_DIR/frontend.pid" ] && kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null && rm "$LOG_DIR/frontend.pid"

echo ""
log "All services stopped"
