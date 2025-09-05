# 🚀 AI_Stock 生产环境Docker部署指南

## 📋 部署概述

本指南将帮助您在生产环境中使用Docker部署AI_Stock系统。系统将自动运行爬虫、LLM分析和Web服务。

**部署特点**:
- 🐳 完全Docker化，一键部署
- 🔄 自动重启，高可用性
- 📊 实时监控和健康检查
- 💾 数据持久化，重启不丢失
- 🛡️ 生产级安全配置

## 🛠️ 环境要求

### 服务器配置
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+)
- **内存**: 最低2GB，推荐4GB+
- **磁盘**: 最低5GB可用空间
- **网络**: 能访问互联网 (爬取新闻和调用LLM API)

### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 1.29+ 或 Docker Compose V2

## 📦 部署步骤

### 第一步: 准备服务器环境

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# sudo yum update -y                    # CentOS/RHEL

# 2. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 4. 安装Docker Compose (如果未安装)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. 将当前用户添加到docker组 (可选)
sudo usermod -aG docker $USER
# 注销并重新登录以生效
```

### 第二步: 上传项目文件

```bash
# 方法1: 使用scp上传 (推荐)
# 在本地执行:
scp -r AI_Stock/ user@your-server-ip:~/ai_stock/

# 方法2: 使用git克隆
# 在服务器执行:
git clone <your-repository-url> ~/ai_stock
cd ~/ai_stock

# 方法3: 手动上传核心文件
# 确保上传以下文件和目录:
# - docker-compose.yml
# - Dockerfile  
# - requirements.txt
# - main.py
# - config/
# - src/
# - .env.template
```

### 第三步: 配置环境变量

```bash
# 1. 进入项目目录
cd ~/ai_stock

# 2. 复制环境变量模板
cp .env.template .env

# 3. 编辑环境变量文件
vi .env
# 或使用其他编辑器: nano .env
```

**重要配置项**:
```bash
# 🔑 必须配置 - LLM API密钥
LLM_API_KEY=your-actual-volcengine-ark-api-key

# 🔐 建议修改 - Web密钥
WEB_SECRET_KEY=your-unique-secret-key-here

# 🌐 可选修改 - Web端口 (如果5000端口被占用)
WEB_PORT=5000

# ⚡ 性能调优 (根据服务器性能调整)
SCRAPY_MAX_ARTICLES=50
SCRAPY_DELAY=1
LLM_TEMPERATURE=0.1
```

### 第四步: 运行部署前检查

```bash
# 运行部署检查脚本
python3 scripts/production_deployment_checklist.py

# 如果检查通过，继续下一步
# 如果有问题，根据提示解决后重新检查
```

### 第五步: 构建和启动服务

```bash
# 1. 构建Docker镜像
docker-compose build --no-cache

# 2. 启动服务 (后台运行)
docker-compose up -d

# 3. 查看启动状态
docker-compose ps

# 4. 查看启动日志
docker-compose logs -f
```

### 第六步: 验证部署

```bash
# 1. 检查容器状态 (应该显示 Up)
docker-compose ps

# 2. 检查健康状态
docker-compose exec ai-stock curl -f http://localhost:5000/api/stats

# 3. 测试Web访问
curl http://localhost:5000/

# 4. 查看系统状态
docker-compose exec ai-stock python main.py status
```

## 🌐 访问系统

部署成功后，您可以通过以下方式访问系统:

- **Web界面**: http://服务器IP:5000
- **API接口**: http://服务器IP:5000/api/stats
- **健康检查**: http://服务器IP:5000/api/health

## 📊 系统监控

### 查看运行状态
```bash
# 查看容器状态
docker-compose ps

# 查看资源使用情况
docker stats ai-stock-system

# 查看实时日志
docker-compose logs -f --tail=50
```

### 健康检查
```bash
# 检查系统健康
docker-compose exec ai-stock python scripts/check_system_health.py

# 检查Web服务
docker-compose exec ai-stock python scripts/test_web_service.py
```

## 🔧 日常管理

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart ai-stock
```

### 更新系统
```bash
# 1. 停止服务
docker-compose down

# 2. 更新代码 (如果使用git)
git pull

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d
```

### 查看日志
```bash
# 查看所有日志
docker-compose logs

# 查看最近的日志
docker-compose logs --tail=100

# 实时查看日志
docker-compose logs -f

# 查看特定时间的日志
docker-compose logs --since="2025-09-05T10:00:00"
```

### 数据备份
```bash
# 备份数据库和日志
tar -czf ai_stock_backup_$(date +%Y%m%d_%H%M%S).tar.gz database/ logs/

# 恢复数据 (如果需要)
tar -xzf ai_stock_backup_YYYYMMDD_HHMMSS.tar.gz
```

## 🛡️ 安全配置

### 防火墙设置
```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### SSL/HTTPS配置 (可选)
如果需要HTTPS访问，建议使用Nginx反向代理:

```bash
# 安装Nginx
sudo apt install nginx  # Ubuntu/Debian
# sudo yum install nginx # CentOS/RHEL

# 配置反向代理
sudo vi /etc/nginx/sites-available/ai-stock
```

## ❗ 故障排查

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细错误信息
   docker-compose logs ai-stock
   
   # 检查配置文件
   docker-compose config
   ```

2. **端口被占用**
   ```bash
   # 查看端口占用
   sudo netstat -tlnp | grep :5000
   
   # 修改端口 (编辑.env文件)
   WEB_PORT=5001
   ```

3. **内存不足**
   ```bash
   # 查看内存使用
   free -h
   
   # 调整配置 (编辑.env文件)
   SCRAPY_MAX_ARTICLES=20
   SCRAPY_CONCURRENT_REQUESTS=4
   ```

4. **LLM API调用失败**
   ```bash
   # 检查API密钥配置
   docker-compose exec ai-stock env | grep LLM_API_KEY
   
   # 测试API连接
   docker-compose exec ai-stock python -c "
   from src.llm.llm_service import LLMService
   service = LLMService('ark')
   print('API连接正常' if service else 'API连接失败')
   "
   ```

### 紧急恢复
```bash
# 完全重置 (谨慎使用)
docker-compose down
docker system prune -a
docker-compose up -d --build
```

## 📞 技术支持

如遇到部署问题，请联系:
- **开发者**: Corey
- **邮箱**: lijingfan@pku.org.cn
- **提供信息**: 服务器系统版本、错误日志、配置文件

---

## 🚀 一键部署脚本

为了简化部署过程，我们提供了一键部署脚本:

```bash
# 下载并运行一键部署脚本
curl -fsSL https://raw.githubusercontent.com/your-repo/AI_Stock/main/deploy.sh | bash

# 或者如果已有项目文件
chmod +x deploy.sh
./deploy.sh
```

**🎉 部署完成后，您的AI股票分析系统将24小时自动运行，每小时抓取新闻并进行AI分析！**
