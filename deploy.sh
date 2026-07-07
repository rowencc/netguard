#!/bin/bash
# NetGuard 服务器部署脚本
# 用法: ./deploy.sh [setup|deploy|restart|status|logs]

set -e

DEPLOY_PATH="/opt/netguard"
BACKEND_PORT=8089
FRONTEND_PORT=3000

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

setup_server() {
    info "Setting up server..."
    
    # Install Python 3.10+
    if ! command -v python3 &>/dev/null; then
        info "Installing Python3..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    fi
    
    # Install Node.js 18
    if ! command -v node &>/dev/null; then
        info "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install MySQL
    if ! command -v mysql &>/dev/null; then
        info "Installing MySQL..."
        sudo apt-get install -y mysql-server
        sudo mysql_secure_installation
    fi
    
    # Install Redis
    if ! command -v redis-cli &>/dev/null; then
        info "Installing Redis..."
        sudo apt-get install -y redis-server
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
    fi
    
    # Install git
    if ! command -v git &>/dev/null; then
        sudo apt-get install -y git
    fi
    
    # Clone repo
    sudo mkdir -p $DEPLOY_PATH
    sudo chown $USER:$USER $DEPLOY_PATH
    
    if [ ! -d "$DEPLOY_PATH/.git" ]; then
        git clone https://github.com/rowencc/netguard.git $DEPLOY_PATH
    fi
    
    cd $DEPLOY_PATH
    
    # Setup backend
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ..
    
    # Setup frontend
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Create logs directory
    mkdir -p logs
    
    # Create systemd services
    create_services
    
    log "Server setup complete!"
}

create_services() {
    info "Creating systemd services..."
    
    sudo tee /etc/systemd/system/netguard-backend.service > /dev/null <<EOF
[Unit]
Description=NetGuard Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_PATH/backend
ExecStart=$DEPLOY_PATH/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/netguard-frontend.service > /dev/null <<EOF
[Unit]
Description=NetGuard Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_PATH/frontend/dist
ExecStart=/usr/bin/python3 -m http.server $FRONTEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable netguard-backend netguard-frontend
    log "Systemd services created"
}

deploy() {
    info "Deploying..."
    
    cd $DEPLOY_PATH
    
    # Pull latest
    git pull origin main
    
    # Update backend
    cd backend
    source venv/bin/activate
    pip install -r requirements.txt -q
    deactivate
    cd ..
    
    # Rebuild frontend
    cd frontend
    npm install --silent
    npm run build
    cd ..
    
    # Restart services
    restart
    
    log "Deployment complete!"
}

restart() {
    info "Restarting services..."
    sudo systemctl restart netguard-backend netguard-frontend
    sleep 2
    status
}

status() {
    echo ""
    echo "=================================="
    echo "  NetGuard Service Status"
    echo "=================================="
    
    if systemctl is-active --quiet mysql; then
        echo -e "  MySQL:    ${GREEN}Running${NC}"
    else
        echo -e "  MySQL:    ${RED}Stopped${NC}"
    fi
    
    if systemctl is-active --quiet redis-server; then
        echo -e "  Redis:    ${GREEN}Running${NC}"
    else
        echo -e "  Redis:    ${RED}Stopped${NC}"
    fi
    
    if systemctl is-active --quiet netguard-backend; then
        echo -e "  Backend:  ${GREEN}Running${NC} (port $BACKEND_PORT)"
    else
        echo -e "  Backend:  ${RED}Stopped${NC}"
    fi
    
    if systemctl is-active --quiet netguard-frontend; then
        echo -e "  Frontend: ${GREEN}Running${NC} (port $FRONTEND_PORT)"
    else
        echo -e "  Frontend: ${RED}Stopped${NC}"
    fi
    
    echo "=================================="
    echo ""
}

logs() {
    echo "=== Backend Logs ==="
    sudo journalctl -u netguard-backend -n 50 --no-pager
    echo ""
    echo "=== Frontend Logs ==="
    sudo journalctl -u netguard-frontend -n 50 --no-pager
}

case "${1:-help}" in
    setup)
        setup_server
        ;;
    deploy)
        deploy
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "用法: $0 {setup|deploy|restart|status|logs}"
        echo ""
        echo "  setup   - 首次安装依赖并配置服务"
        echo "  deploy  - 拉取最新代码并部署"
        echo "  restart - 重启所有服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看服务日志"
        exit 1
        ;;
esac
