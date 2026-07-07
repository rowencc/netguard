# NetGuard 客户端安装指南

## 功能说明

客户端 Agent 部署在你的电脑上，负责：
- 扫描本地局域网设备
- 自动识别设备厂商和类型
- 上报数据到云服务器
- 接收服务器指令执行扫描

## 系统要求

- **操作系统**: macOS 10.15+ / Ubuntu 18.04+ / CentOS 7+
- **Python**: 3.9+
- **网络**: 能访问云服务器 (https://net.soccn.com)

## 快速安装

### 1. 下载客户端

```bash
git clone https://github.com/rowencc/netguard.git
cd netguard/client
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置服务器地址

编辑 `config/client.json`:

```json
{
  "server_url": "https://net.soccn.com",
  "api_key": "netguard-sync-key-2024",
  "client_id": "client-mycomputer-001",
  "scan_interval": 300,
  "scan_subnets": [],
  "use_websocket": true
}
```

**配置说明:**
- `server_url`: 云服务器地址（必须是 https://net.soccn.com）
- `client_id`: 客户端唯一标识（建议用 `client-电脑名-编号` 格式）
- `scan_interval`: 自动扫描间隔（秒），默认 300 秒
- `scan_subnets`: 扫描的子网（留空则自动检测）
- `use_websocket`: 是否使用 WebSocket 实时通信

### 5. 测试连接

```bash
python3 -m app.main --server https://net.soccn.com --scan-once
```

如果看到 `Found XX devices` 表示安装成功。

### 6. 启动服务

**前台运行（调试用）:**
```bash
python3 -m app.main --server https://net.soccn.com
```

**后台运行（生产用）:**
```bash
nohup python3 -m app.main --server https://net.soccn.com > netguard.log 2>&1 &
echo $! > netguard.pid
```

**停止服务:**
```bash
kill $(cat netguard.pid)
```

## macOS 开机自启

创建 `~/Library/LaunchAgents/com.netguard.client.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.netguard.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/client/venv/bin/python3</string>
        <string>-m</string>
        <string>app.main</string>
        <string>--server</string>
        <string>https://net.soccn.com</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/client</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/netguard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/netguard.log</string>
</dict>
</plist>
```

加载服务:
```bash
launchctl load ~/Library/LaunchAgents/com.netguard.client.plist
```

## Linux 开机自启

创建 `/etc/systemd/system/netguard.service`:

```ini
[Unit]
Description=NetGuard Client Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/client
ExecStart=/path/to/client/venv/bin/python3 -m app.main --server https://net.soccn.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable netguard
sudo systemctl start netguard
```

## 常用命令

```bash
# 单次扫描
python3 -m app.main --scan-once

# 指定服务器
python3 -m app.main --server https://net.soccn.com

# 禁用 WebSocket（仅使用 HTTP 上报）
python3 -m app.main --no-ws

# 使用自定义配置
python3 -m app.main -c /path/to/config.json
```

## 故障排查

### 无法连接服务器
```bash
# 测试网络连通性
curl -s https://net.soccn.com/api/health

# 检查防火墙
# 确保能访问 443 端口
```

### 扫描不到设备
```bash
# 检查 ARP 表
arp -a

# 手动测试 scapy
python3 -c "from scapy.all import srp, ARP, Ether; print(srp(ARP(pdst='192.168.1.0/24')/Ether(dst='ff:ff:ff:ff:ff:ff'), timeout=2)[0])"
```

### 查看日志
```bash
# 前台运行时直接查看输出
# 后台运行时查看日志文件
tail -f netguard.log
```
