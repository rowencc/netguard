#!/bin/bash
# NetGuard Client 部署脚本
# 用于桌面电脑或 ARM 硬件部署

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }

install_deps() {
    echo "Installing dependencies..."
    
    if ! command -v python3 &>/dev/null; then
        err "Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    python3 -m venv venv 2>/dev/null || true
    source venv/bin/activate
    
    pip install -r requirements.txt -q
    log "Dependencies installed"
    
    if ! command -v nmap &>/dev/null; then
        warn "nmap not found. Deep scan will be limited."
        warn "Install with: sudo apt install nmap (Ubuntu) or brew install nmap (macOS)"
    fi
}

configure_client() {
    echo ""
    echo "=== NetGuard Client Configuration ==="
    echo ""
    
    read -p "Server URL [http://localhost:8089]: " SERVER_URL
    SERVER_URL=${SERVER_URL:-"http://localhost:8089"}
    
    read -p "Client ID [client-$(hostname)]: " CLIENT_ID
    CLIENT_ID=${CLIENT_ID:-"client-$(hostname)"}
    
    read -p "Scan interval in seconds [300]: " SCAN_INTERVAL
    SCAN_INTERVAL=${SCAN_INTERVAL:-300}
    
    cat > "$PROJECT_DIR/config/client.json" << EOF
{
  "server_url": "$SERVER_URL",
  "api_key": "netguard-sync-key-2024",
  "client_id": "$CLIENT_ID",
  "scan_interval": $SCAN_INTERVAL,
  "scan_subnets": ["192.168.100.0/24", "192.168.101.0/24"]
}
EOF
    
    log "Configuration saved to config/client.json"
}

test_connection() {
    echo "Testing connection to server..."
    source venv/bin/activate
    
    python3 -c "
from app.reporter import ServerReporter
from app.config import ClientConfig

config = ClientConfig()
reporter = ServerReporter(config.server_url, config.api_key, config.client_id)

if reporter.test_connection():
    print('✓ Connection successful!')
else:
    print('✗ Connection failed. Check server URL and port.')
    exit(1)
"
}

start_client() {
    echo "Starting NetGuard Client..."
    
    source venv/bin/activate
    
    nohup python3 -m app.main \
        > "$PROJECT_DIR/client.log" 2>&1 &
    
    echo $! > "$PROJECT_DIR/client.pid"
    
    sleep 2
    
    if [ -f "$PROJECT_DIR/client.pid" ] && kill -0 $(cat "$PROJECT_DIR/client.pid") 2>/dev/null; then
        log "Client running (PID: $(cat $PROJECT_DIR/client.pid))"
    else
        err "Client failed to start. Check client.log"
    fi
}

stop_client() {
    if [ -f "$PROJECT_DIR/client.pid" ]; then
        kill $(cat "$PROJECT_DIR/client.pid") 2>/dev/null
        rm "$PROJECT_DIR/client.pid"
        log "Client stopped"
    fi
}

scan_once() {
    echo "Running one-time scan..."
    source venv/bin/activate
    python3 -m app.main --scan-once
}

show_status() {
    echo ""
    echo "=============================="
    echo "  NetGuard Client Status"
    echo "=============================="
    
    if [ -f "$PROJECT_DIR/client.pid" ] && kill -0 $(cat "$PROJECT_DIR/client.pid") 2>/dev/null; then
        echo -e "  Client: ${GREEN}Running${NC} (PID: $(cat $PROJECT_DIR/client.pid))"
    else
        echo -e "  Client: ${RED}Stopped${NC}"
    fi
    
    if [ -f "$PROJECT_DIR/config/client.json" ]; then
        echo "  Config: $PROJECT_DIR/config/client.json"
    else
        echo -e "  Config: ${YELLOW}Not configured${NC}"
    fi
    
    echo "=============================="
}

case "${1:-start}" in
    install)
        install_deps
        ;;
    configure)
        configure_client
        ;;
    test)
        test_connection
        ;;
    start)
        start_client
        show_status
        ;;
    stop)
        stop_client
        ;;
    restart)
        stop_client
        sleep 1
        start_client
        show_status
        ;;
    scan)
        scan_once
        ;;
    status)
        show_status
        ;;
    *)
        echo "用法: $0 {install|configure|test|start|stop|restart|scan|status}"
        exit 1
        ;;
esac
