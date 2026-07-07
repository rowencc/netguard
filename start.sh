#!/bin/bash
# NetGuard 启动脚本
# 支持 macOS 和 Ubuntu Linux
# 用法: ./start.sh [all|backend|frontend|db|stop|status|restart]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"
BACKEND_PORT=8089
FRONTEND_PORT=3099

mkdir -p "$LOG_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

PLATFORM=$(detect_platform)

check_port() {
    if [ "$PLATFORM" = "macos" ]; then
        lsof -i :$1 -P -t 2>/dev/null | head -1
    else
        ss -tlnp 2>/dev/null | grep ":$1 " | head -1 | awk '{print $NF}' | grep -oP '\d+' | head -1
    fi
}

kill_port() {
    local pid=$(check_port $1)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null || true
        sleep 1
        warn "Killed process on port $1"
    fi
}

start_mysql() {
    info "Checking MySQL..."
    if mysql -u root -proot -e "SELECT 1" &>/dev/null; then
        log "MySQL is running"
    else
        warn "MySQL not running, attempting to start..."
        if [ "$PLATFORM" = "macos" ]; then
            if command -v brew &>/dev/null; then
                brew services start mysql 2>/dev/null || true
            elif command -v mysqld &>/dev/null; then
                mysqld_safe --datadir=/usr/local/mysql/data &
                sleep 3
            else
                err "MySQL not found. Please start MySQL manually."
                return 1
            fi
        else
            if command -v systemctl &>/dev/null; then
                sudo systemctl start mysql 2>/dev/null || sudo systemctl start mysqld 2>/dev/null || true
            elif command -v service &>/dev/null; then
                sudo service mysql start 2>/dev/null || true
            elif command -v mysqld &>/dev/null; then
                sudo mysqld --user=root &
                sleep 3
            else
                err "MySQL not found. Please start MySQL manually."
                return 1
            fi
        fi
    fi
    
    mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS netguard" 2>/dev/null
    log "Database 'netguard' ready"
}

start_redis() {
    info "Checking Redis..."
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        log "Redis is running"
    else
        warn "Redis not running, attempting to start..."
        if [ "$PLATFORM" = "macos" ]; then
            if command -v brew &>/dev/null; then
                brew services start redis 2>/dev/null || true
            elif command -v redis-server &>/dev/null; then
                redis-server --daemonize yes
            else
                err "Redis not found. Please start Redis manually."
                return 1
            fi
        else
            if command -v systemctl &>/dev/null; then
                sudo systemctl start redis 2>/dev/null || true
            elif command -v service &>/dev/null; then
                sudo service redis-server start 2>/dev/null || true
            elif command -v redis-server &>/dev/null; then
                sudo redis-server --daemonize yes
            else
                err "Redis not found. Please start Redis manually."
                return 1
            fi
        fi
    fi
    log "Redis ready"
}

start_backend() {
    info "Starting backend..."
    
    kill_port $BACKEND_PORT
    
    cd "$BACKEND_DIR"
    
    if [ ! -d "venv" ]; then
        warn "Virtual environment not found, creating..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt -q
    else
        source venv/bin/activate
    fi
    
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        > "$LOG_DIR/backend.log" 2>&1 &
    
    echo $! > "$LOG_DIR/backend.pid"
    
    sleep 2
    if check_port $BACKEND_PORT >/dev/null; then
        log "Backend running on http://localhost:$BACKEND_PORT"
    else
        err "Backend failed to start. Check $LOG_DIR/backend.log"
        return 1
    fi
}

start_frontend() {
    info "Starting frontend..."
    
    kill_port $FRONTEND_PORT
    
    cd "$FRONTEND_DIR"
    
    if [ ! -d "node_modules" ]; then
        warn "node_modules not found, installing..."
        npm install
    fi
    
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    
    sleep 3
    if check_port $FRONTEND_PORT >/dev/null; then
        log "Frontend running on http://localhost:$FRONTEND_PORT"
    else
        err "Frontend failed to start. Check $LOG_DIR/frontend.log"
        return 1
    fi
}

stop_all() {
    info "Stopping all services..."
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    [ -f "$LOG_DIR/backend.pid" ] && kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null && rm "$LOG_DIR/backend.pid"
    [ -f "$LOG_DIR/frontend.pid" ] && kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null && rm "$LOG_DIR/frontend.pid"
    
    log "All services stopped"
}

show_status() {
    echo ""
    echo "=================================="
    echo "  NetGuard Service Status"
    echo "  Platform: $PLATFORM"
    echo "=================================="
    
    if mysql -u root -proot -e "SELECT 1" &>/dev/null; then
        echo -e "  MySQL:    ${GREEN}Running${NC}"
    else
        echo -e "  MySQL:    ${RED}Stopped${NC}"
    fi
    
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "  Redis:    ${GREEN}Running${NC}"
    else
        echo -e "  Redis:    ${RED}Stopped${NC}"
    fi
    
    if check_port $BACKEND_PORT >/dev/null; then
        echo -e "  Backend:  ${GREEN}Running${NC} (port $BACKEND_PORT)"
    else
        echo -e "  Backend:  ${RED}Stopped${NC}"
    fi
    
    if check_port $FRONTEND_PORT >/dev/null; then
        echo -e "  Frontend: ${GREEN}Running${NC} (port $FRONTEND_PORT)"
    else
        echo -e "  Frontend: ${RED}Stopped${NC}"
    fi
    
    echo "=================================="
    echo ""
}

case "${1:-all}" in
    all)
        start_mysql
        start_redis
        start_backend
        start_frontend
        show_status
        ;;
    db)
        start_mysql
        start_redis
        ;;
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    restart)
        stop_all
        sleep 1
        start_mysql
        start_redis
        start_backend
        start_frontend
        show_status
        ;;
    *)
        echo "用法: $0 {all|db|backend|frontend|stop|status|restart}"
        exit 1
        ;;
esac
