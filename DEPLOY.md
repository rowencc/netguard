# NetGuard 部署指南

## 一、云服务器准备（阿里云 ECS）

### 1. 购买 ECS 实例
- 推荐配置：2核4G 内存，40G 系统盘
- 操作系统：Ubuntu 22.04 LTS
- 安全组开放端口：22(SSH), 8089(后端), 3000(前端), 3306(MySQL), 6379(Redis)

### 2. SSH 连接服务器
```bash
ssh root@your-server-ip
```

### 3. 首次部署 - 运行安装脚本
```bash
# 上传部署脚本
scp deploy.sh root@your-server-ip:/opt/

# 登录服务器执行
ssh root@your-server-ip
chmod +x /opt/deploy.sh
/opt/deploy.sh setup
```

### 4. 手动部署（不用 GitHub Actions）
```bash
cd /opt/netguard
./deploy.sh deploy
```

---

## 二、GitHub Actions 自动部署

### 1. 配置 GitHub Secrets

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `SERVER_HOST` | 服务器 IP 地址 | `47.98.xxx.xxx` |
| `SERVER_USERNAME` | SSH 用户名 | `root` |
| `SERVER_SSH_KEY` | SSH 私钥内容 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_PORT` | SSH 端口（可选，默认 22） | `22` |

### 2. 生成 SSH 密钥对

在本地执行：
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_deploy
```

将公钥添加到服务器：
```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
```

将私钥内容（`~/.ssh/github_deploy` 文件全部内容）复制到 GitHub Secret `SERVER_SSH_KEY`。

### 3. 推送代码触发部署
```bash
git add .
git commit -m "feat: initial deploy setup"
git push origin main
```

---

## 三、常用命令

```bash
# 查看服务状态
./deploy.sh status

# 重启服务
./deploy.sh restart

# 查看日志
./deploy.sh logs

# 手动部署
./deploy.sh deploy
```

---

## 四、故障排查

### 后端启动失败
```bash
sudo journalctl -u netguard-backend -n 50
```

### MySQL 连接失败
```bash
mysql -u root -e "SHOW DATABASES"
```

### 端口被占用
```bash
sudo lsof -i :8089
sudo lsof -i :3000
```
