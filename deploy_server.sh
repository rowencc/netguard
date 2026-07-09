#!/bin/bash
# NetGuard 一键部署脚本 - 阿里云 ECS
# 用法: 上传到服务器后执行 bash deploy_server.sh

set -e

DEPLOY_PATH="/opt/netguard"
BACKEND_PORT=8089
FRONTEND_PORT=3000
REPO_URL="https://github.com/rowencc/netguard.git"

# 数据库配置
DB_USER="net_soccn_com"
DB_PASS="TtP2SQE8MPEkW2A7"
DB_NAME="net_soccn_com"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

# ============================================
# 1. 安装系统依赖
# ============================================
install_deps() {
    info "安装系统依赖..."

    # 更新系统
    dnf update -y -q 2>/dev/null || yum update -y -q 2>/dev/null

    # 安装编译工具
    dnf install -y gcc make openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel wget tar git -q 2>/dev/null \
    || yum install -y gcc make openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel wget tar git -q 2>/dev/null

    log "系统依赖安装完成"
}

# ============================================
# 2. 安装 Python 3.10+
# ============================================
install_python() {
    info "检查 Python 版本..."

    # 检查是否有 Python 3.9+
    if command -v python3.10 &>/dev/null; then
        PYTHON_CMD="python3.10"
    elif command -v python3.9 &>/dev/null; then
        PYTHON_CMD="python3.9"
    else
        CURRENT_PY=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
        if [[ $(echo "$CURRENT_PY >= 3.9" | bc 2>/dev/null || echo 0) -eq 1 ]]; then
            PYTHON_CMD="python3"
        else
            info "Python 版本过低 ($CURRENT_PY)，正在安装 Python 3.10..."
            install_python_from_source
            PYTHON_CMD="/usr/local/bin/python3.10"
        fi
    fi

    log "使用 Python: $($PYTHON_CMD --version)"
}

install_python_from_source() {
    cd /tmp
    wget -q https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
    tar xzf Python-3.10.13.tgz
    cd Python-3.10.13
    ./configure --enable-optimizations --prefix=/usr/local -q
    make -j$(nproc) -q 2>/dev/null
    make altinstall -q 2>/dev/null
    cd /tmp && rm -rf Python-3.10.13 Python-3.10.13.tgz
    log "Python 3.10 安装完成"
}

# ============================================
# 3. 安装 Node.js 18
# ============================================
install_nodejs() {
    info "检查 Node.js..."

    if command -v node &>/dev/null; then
        NODE_VER=$(node --version | grep -oP '\d+')
        if [ "$NODE_VER" -ge 18 ]; then
            log "Node.js 已安装: $(node --version)"
            return
        fi
    fi

    info "安装 Node.js 18..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - 2>/dev/null
    dnf install -y nodejs -q 2>/dev/null || yum install -y nodejs -q 2>/dev/null
    log "Node.js 安装完成: $(node --version)"
}

# ============================================
# 4. 配置 MySQL
# ============================================
setup_mysql() {
    info "配置 MySQL..."

    # 确保 MySQL 运行
    systemctl start mysqld 2>/dev/null || systemctl start mysql 2>/dev/null || true
    systemctl enable mysqld 2>/dev/null || systemctl enable mysql 2>/dev/null || true

    # 检查数据库是否已存在
    if mysql -u${DB_USER} -p${DB_PASS} -e "USE ${DB_NAME}" 2>/dev/null; then
        log "数据库 ${DB_NAME} 已存在"
    else
        # 使用 root 创建数据库和用户
        if mysql -u root -e "SELECT 1" 2>/dev/null; then
            mysql -u root -e "
                CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
                GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
                FLUSH PRIVILEGES;
            " 2>/dev/null
            log "数据库 ${DB_NAME} 创建完成"
        else
            warn "无法连接 MySQL root，请手动创建数据库"
        fi
    fi
}

# ============================================
# 5. 配置 Redis
# ============================================
setup_redis() {
    info "检查 Redis..."
    systemctl start redis 2>/dev/null || systemctl start redis-server 2>/dev/null || true
    systemctl enable redis 2>/dev/null || systemctl enable redis-server 2>/dev/null || true

    if redis-cli ping 2>/dev/null | grep -q PONG; then
        log "Redis 运行中"
    else
        warn "Redis 启动失败，请手动检查"
    fi
}

# ============================================
# 6. 克隆/更新代码
# ============================================
setup_code() {
    info "部署代码..."

    if [ -d "$DEPLOY_PATH/.git" ]; then
        cd "$DEPLOY_PATH"
        git pull origin main
        log "代码更新完成"
    else
        sudo mkdir -p "$DEPLOY_PATH"
        sudo chown $(whoami):$(whoami) "$DEPLOY_PATH"
        git clone "$REPO_URL" "$DEPLOY_PATH"
        cd "$DEPLOY_PATH"
        log "代码克隆完成"
    fi
}

# ============================================
# 7. 配置后端
# ============================================
setup_backend() {
    info "配置后端..."

    cd "$DEPLOY_PATH/backend"

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
    fi

    source venv/bin/activate

    # 安装依赖
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    # 更新数据库配置
    cat > config.yaml <<EOF
app:
  name: NetGuard
  version: 1.0.0
  debug: false

database:
  host: localhost
  port: 3306
  user: ${DB_USER}
  password: ${DB_PASS}
  database: ${DB_NAME}

scanner:
  networks:
    - 192.168.1.0/24
  interval: 300
  timeout: 30

alerter:
  email:
    enabled: false
  wechat:
    enabled: false
  dingtalk:
    enabled: false
EOF

    deactivate
    log "后端配置完成"
}

# ============================================
# 8. 构建前端
# ============================================
setup_frontend() {
    info "构建前端..."

    cd "$DEPLOY_PATH/frontend"

    if [ ! -d "node_modules" ]; then
        npm install --silent
    fi

    npm run build

    # 同步到 Nginx 服务目录
    NGINX_ROOT="/home/wwwroot/net.soccn.com"
    if [ -d "$NGINX_ROOT" ]; then
        rm -rf "$NGINX_ROOT/assets" "$NGINX_ROOT/index.html" "$NGINX_ROOT/favicon.svg"
        cp -r "$DEPLOY_PATH/frontend/dist/"* "$NGINX_ROOT/"
        log "前端构建完成，已同步到 $NGINX_ROOT"
    else
        log "前端构建完成（未找到 Nginx 目录 $NGINX_ROOT）"
    fi
}

# ============================================
# 9. 创建 systemd 服务
# ============================================
create_services() {
    info "创建系统服务..."

    sudo tee /etc/systemd/system/netguard-backend.service > /dev/null <<EOF
[Unit]
Description=NetGuard Backend API
After=network.target mysqld.service redis.service

[Service]
Type=simple
User=root
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
User=root
WorkingDirectory=$DEPLOY_PATH/frontend/dist
ExecStart=/usr/bin/python3 -m http.server $FRONTEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable netguard-backend netguard-frontend
    log "系统服务创建完成"
}

# ============================================
# 10. 启动服务
# ============================================
start_services() {
    info "启动服务..."

    sudo systemctl restart netguard-backend
    sleep 2
    sudo systemctl restart netguard-frontend
    sleep 2

    log "服务启动完成"
}

# ============================================
# 11. 验证部署
# ============================================
verify() {
    echo ""
    echo "=================================="
    echo "  NetGuard 部署状态"
    echo "=================================="

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

    if mysql -u${DB_USER} -p${DB_PASS} -e "USE ${DB_NAME}" 2>/dev/null; then
        echo -e "  MySQL:    ${GREEN}Connected${NC}"
    else
        echo -e "  MySQL:    ${RED}Connection Failed${NC}"
    fi

    if redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "  Redis:    ${GREEN}Running${NC}"
    else
        echo -e "  Redis:    ${RED}Stopped${NC}"
    fi

    echo "=================================="
    echo ""
    echo "  访问地址: http://47.94.58.173:${FRONTEND_PORT}"
    echo "  API 地址: http://47.94.58.173:${BACKEND_PORT}"
    echo ""
    echo "  管理命令:"
    echo "    systemctl restart netguard-backend"
    echo "    systemctl restart netguard-frontend"
    echo "    journalctl -u netguard-backend -f"
    echo ""
}

# ============================================
# 主流程
# ============================================
echo "=================================="
echo "  NetGuard 服务器部署脚本"
echo "  目标: 47.94.58.173"
echo "=================================="
echo ""

install_deps
install_python
install_nodejs
setup_mysql
setup_redis
setup_code
setup_backend
setup_frontend
create_services
start_services
verify
