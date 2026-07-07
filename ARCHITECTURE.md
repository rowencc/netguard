# NetGuard - 网络安全监控系统

## 架构说明

本项目采用 **服务端-客户端** 分离架构：

```
┌─────────────────────────────────────────────────────────────┐
│                      Cloud Server                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend + MySQL Database                    │   │
│  │  - REST API 接口                                     │   │
│  │  - 设备数据存储                                       │   │
│  │  - 告警管理                                          │   │
│  │  - 客户端数据接收                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ▲                                 │
│                           │ HTTP/WebSocket                   │
└───────────────────────────┼─────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Desktop PC   │  │ ARM Device 1 │  │ ARM Device 2 │
│ Client Agent │  │ Client Agent │  │ Client Agent │
│ - 本地扫描   │  │ - 本地扫描   │  │ - 本地扫描   │
│ - 设备上报   │  │ - 设备上报   │  │ - 设备上报   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 目录结构

```
netguard/
├── server/                 # 云端服务端
│   ├── app/
│   │   ├── api/           # API 接口
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 入口
│   ├── requirements.txt
│   └── deploy.sh
│
├── client/                 # 客户端（桌面/ARM）
│   ├── app/
│   │   ├── scanner.py     # 本地网络扫描
│   │   ├── reporter.py    # 数据上报
│   │   ├── config.py      # 配置管理
│   │   └── main.py        # 入口
│   ├── config/
│   │   └── client.json    # 客户端配置
│   ├── requirements.txt
│   └── deploy.sh
│
└── frontend/               # Web 前端（可选部署）
```

## 部署指南

### 1. 部署服务端（云服务器）

```bash
# SSH 登录云服务器
ssh user@your-server-ip

# 克隆项目
git clone <repo-url> netguard
cd netguard/server

# 安装依赖并初始化
./deploy.sh install

# 启动服务
./deploy.sh start

# 查看状态
./deploy.sh status
```

服务端默认端口：**8089**

### 2. 部署客户端（桌面电脑）

```bash
cd netguard/client

# 安装依赖
./deploy.sh install

# 配置客户端
./deploy.sh configure
# 输入服务器地址、客户端ID等

# 测试连接
./deploy.sh test

# 启动客户端
./deploy.sh start
```

### 3. 部署客户端（ARM 硬件 / Ubuntu）

```bash
# SSH 登录 ARM 设备
ssh user@arm-device-ip

# 克隆项目
git clone <repo-url> netguard
cd netguard/client

# 安装依赖
./deploy.sh install

# 配置客户端
./deploy.sh configure

# 启动客户端
./deploy.sh start
```

### 4. 手动扫描（一次性）

```bash
cd netguard/client
./deploy.sh scan
```

## 配置说明

### 服务端配置

编辑 `server/app/config.py` 或使用环境变量：

```bash
export NETGUARD_DB_HOST=localhost
export NETGUARD_DB_USER=root
export NETGUARD_DB_PASS=root
export NETGUARD_DB_NAME=netguard
```

### 客户端配置

编辑 `client/config/client.json`：

```json
{
  "server_url": "http://YOUR_SERVER_IP:8089",
  "api_key": "netguard-sync-key-2024",
  "client_id": "client-desktop-001",
  "scan_interval": 300,
  "scan_subnets": ["192.168.100.0/24"]
}
```

## API 接口

### 服务端 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/devices/` | GET | 获取设备列表 |
| `/api/devices/scan` | POST | 触发扫描 |
| `/api/alerts/` | GET | 获取告警列表 |
| `/api/sync/heartbeat` | POST | 客户端心跳 |
| `/api/sync/report-devices` | POST | 上报设备数据 |
| `/api/sync/clients` | GET | 获取客户端列表 |

### 客户端命令

```bash
./deploy.sh install      # 安装依赖
./deploy.sh configure    # 配置客户端
./deploy.sh test         # 测试连接
./deploy.sh start        # 启动客户端
./deploy.sh stop         # 停止客户端
./deploy.sh scan         # 一次性扫描
./deploy.sh status       # 查看状态
```

## 平台兼容

| 平台 | 支持状态 |
|------|----------|
| macOS | ✅ 完全支持 |
| Ubuntu Linux | ✅ 完全支持 |
| ARM Linux (armbian) | ✅ 完全支持 |

## 安全说明

- 客户端使用 API Key 认证
- 建议在生产环境使用 HTTPS
- 可修改 `server/app/api/sync.py` 中的 `API_KEY`
