#!/bin/bash
# NetGuard Client 卸载脚本

INSTALL_DIR="$HOME/.netguard"

echo "正在卸载 NetGuard Client..."

# 停止客户端
if [[ -f "$INSTALL_DIR/client.pid" ]]; then
    kill $(cat "$INSTALL_DIR/client.pid") 2>/dev/null
    rm "$INSTALL_DIR/client.pid"
fi

# 删除快捷命令
rm -f /usr/local/bin/netguard-start
rm -f /usr/local/bin/netguard-stop
rm -f /usr/local/bin/netguard-status

# 删除安装目录
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo "已删除: $INSTALL_DIR"
fi

echo "NetGuard Client 已卸载"
