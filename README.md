# NetGuard - 网络安全监控系统

## 项目概述

NetGuard 是一个局域网设备扫描与安全监控系统，用于发现、识别和追踪网络中的设备，特别针对摄像头等高风险设备进行监控。

## 系统架构

```
netguard/
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── models/    # 数据模型
│   │   └── services/  # 业务逻辑
│   ├── data/          # OUI 厂商数据库
│   └── config.yaml    # 配置文件
├── frontend/          # Vue 3 前端
│   └── src/views/     # 页面组件
├── start.sh           # 启动脚本
├── stop.sh            # 停止脚本
└── docs/              # 文档
```

## 功能模块

### 1. 设备扫描 (`scanner.py`)

- **ARP 表扫描**：通过系统 ARP 表获取局域网设备
- **MAC 地址标准化**：自动补零格式化（如 `1:0:5E` → `01:00:5E`）
- **深度扫描**：使用 Nmap 进行端口扫描和操作系统识别

### 2. 设备识别 (`identifier.py`)

- **厂商识别**：基于 MAC 地址前缀（OUI）匹配厂商
- **设备类型判断**：根据厂商、主机名、端口识别设备类型
  - `camera` - 摄像头（高风险）
  - `router` - 路由器
  - `phone` - 手机
  - `computer` - 电脑
  - `iot` - IoT 设备
- **风险评估**：根据设备类型和开放端口评估风险等级

### 3. 厂商数据库 (`vendor_lookup.py`)

- **数据来源**：IEEE OUI 注册表
- **记录数量**：39,512+ 条厂商记录
- **自动更新**：支持从 IEEE 实时同步最新数据

### 4. 告警系统 (`alerter.py`)

- 支持邮件、微信、钉钉通知
- 高风险设备发现时自动告警

## API 接口

### 设备管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/devices/` | 获取设备列表 |
| GET | `/api/devices/{id}` | 获取设备详情 |
| POST | `/api/devices/scan` | 触发网络扫描 |
| PUT | `/api/devices/{id}` | 更新设备信息 |
| POST | `/api/devices/{id}/deep-scan` | 深度扫描设备 |

### 系统管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/stats` | 获取系统统计 |
| GET | `/api/system/health` | 健康检查 |
| GET | `/api/system/oui/status` | OUI 数据库状态 |
| POST | `/api/system/oui/update` | 更新 OUI 数据库 |

### 告警管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/alerts/` | 获取告警列表 |
| PUT | `/api/alerts/{id}/ack` | 确认告警 |

## 启动与停止

### 启动所有服务

```bash
cd netguard
chmod +x start.sh
./start.sh
```

### 启动选项

```bash
./start.sh all        # 启动所有服务（默认）
./start.sh db         # 仅启动数据库
./start.sh backend    # 仅启动后端
./start.sh frontend   # 仅启动前端
./start.sh status     # 查看服务状态
./start.sh restart    # 重启所有服务
./start.sh stop       # 停止所有服务
```

### 停止服务

```bash
./stop.sh
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | Vue 开发服务器 |
| Backend | 8089 | FastAPI 后端 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |

## 配置文件

### `backend/config.yaml`

```yaml
app:
  name: NetGuard
  version: 1.0.0
  debug: true

database:
  host: localhost
  port: 3306
  user: root
  password: root
  database: netguard

scanner:
  networks:
    - 192.168.100.0/24
    - 192.168.101.0/24
  interval: 300    # 自动扫描间隔（秒）
  timeout: 30
```

## 移动端适配

系统支持响应式布局：

- **桌面端**：左侧侧边栏导航
- **移动端**（<768px）：底部导航栏 + 卡片列表

## OUI 数据库更新

### 命令行更新

```bash
cd backend
python update_oui.py
```

### API 更新

```bash
curl -X POST http://localhost:8089/api/system/oui/update
```

### 查看状态

```bash
curl http://localhost:8089/api/system/oui/status
```

## 数据库迁移

### MAC 地址标准化

```bash
cd backend
python migrate_mac.py
```

## 日志文件

| 文件 | 说明 |
|------|------|
| `logs/backend.log` | 后端日志 |
| `logs/frontend.log` | 前端日志 |
| `data/oui_update.log` | OUI 更新日志 |

## 依赖

### 后端

- Python 3.9+
- FastAPI
- SQLAlchemy
- python-nmap
- scapy
- redis

### 前端

- Node.js 16+
- Vue 3
- Vite
- Element Plus
- ECharts

## Docker 部署

```bash
docker-compose up -d
```

## 故障排查

### 后端启动失败

```bash
cat logs/backend.log
```

### 前端启动失败

```bash
cat logs/frontend.log
```

### 端口占用

```bash
lsof -i :8089
lsof -i :3000
```

### 数据库连接失败

```bash
mysql -u root -proot -e "SHOW DATABASES"
```
