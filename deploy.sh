#!/bin/bash
# AI股票分析系统统一部署脚本
# 适用于任意目录部署
# Author: Corey (lijingfan@pku.org.cn)
# Version: 1.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录 - 使用当前目录
PROJECT_DIR=$(pwd)
CURRENT_DIR=$(pwd)

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查当前目录
check_directory() {
    log_info "检查部署目录..."

    if [[ "$CURRENT_DIR" != "$PROJECT_DIR" ]]; then
        log_error "请在 $PROJECT_DIR 目录下运行此脚本"
        log_info "当前目录: $CURRENT_DIR"
        exit 1
    fi

    log_success "目录检查通过: $PROJECT_DIR"
}

# 检查Docker和Docker Compose
check_requirements() {
    log_info "检查系统要求..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        log_info "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Docker服务状态
    if ! systemctl is-active --quiet docker; then
        log_warning "Docker服务未启动，正在启动..."
        sudo systemctl start docker
    fi

    # 检查Docker权限
    if ! docker ps &> /dev/null; then
        log_warning "Docker权限问题，可能需要sudo或加入docker组"
        log_info "解决方案: sudo usermod -aG docker $USER && newgrp docker"
    fi

    log_success "系统要求检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    # 项目数据目录
    mkdir -p ${PROJECT_DIR}/{database/backup,logs,data}

    # 设置权限
    chown -R $USER:$USER ${PROJECT_DIR}
    chmod -R 755 ${PROJECT_DIR}

    log_success "目录创建完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."

    if [ ! -f ".env" ]; then
        log_error ".env文件不存在"
        log_info "请确保.env文件存在并配置了必要参数"
        exit 1
    fi

    # 检查关键配置
    if grep -q "your-volcengine-ark-api-key-here" .env; then
        log_error "请在.env文件中配置LLM_API_KEY"
        log_info "编辑命令: vi .env"
        read -p "是否现在编辑.env文件？(y/n): " edit_env
        if [ "$edit_env" = "y" ]; then
            ${EDITOR:-vi} .env
        else
            exit 1
        fi
    else
        log_success "LLM API密钥已配置"
    fi

    log_success "配置文件检查完成"
}

# 构建镜像
build_image() {
    log_info "构建Docker镜像..."
    
    docker-compose build --no-cache
    
    log_success "镜像构建完成"
}

# 部署服务 (简化版)
deploy_services() {
    log_info "部署AI股票分析系统..."

    # 使用统一的docker-compose.yml
    docker-compose up -d

    log_success "服务部署完成"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    # 等待主服务启动
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:5000/api/stats &> /dev/null; then
            log_success "服务启动成功"
            return 0
        fi
        
        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "服务启动超时"
    return 1
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    
    echo ""
    log_info "服务访问地址:"
    echo "  🌐 Web界面: http://localhost:5000"
    echo "  📊 API接口: http://localhost:5000/api"
    echo "  📈 健康检查: http://localhost:5000/api/stats"
    
    if docker-compose ps | grep -q prometheus; then
        echo "  📊 监控面板: http://localhost:9090"
    fi
}

# 显示日志
show_logs() {
    local service=${1:-ai-stock}
    log_info "显示 $service 服务日志:"
    docker-compose logs -f --tail=100 $service
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止服务
    docker-compose down -v
    
    # 清理镜像
    docker system prune -f
    
    # 清理数据卷 (谨慎操作)
    read -p "是否清理数据卷？这将删除所有数据 (y/n): " cleanup_volumes
    if [ "$cleanup_volumes" = "y" ]; then
        docker-compose down -v --remove-orphans
        sudo rm -rf /data/ai-stock
        log_warning "数据卷已清理"
    fi
    
    log_success "清理完成"
}

# 备份数据
backup_data() {
    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    
    log_info "备份数据到 $backup_dir..."
    
    mkdir -p $backup_dir
    
    # 备份数据库
    if [ -f "database/ai_stock.db" ]; then
        cp database/ai_stock.db $backup_dir/
    fi
    
    # 备份配置
    cp .env $backup_dir/
    cp config/settings.py $backup_dir/
    
    # 备份日志
    if [ -d "logs" ]; then
        cp -r logs $backup_dir/
    fi
    
    # 创建压缩包
    tar -czf $backup_dir.tar.gz $backup_dir
    rm -rf $backup_dir
    
    log_success "数据备份完成: $backup_dir.tar.gz"
}

# 更新服务
update_services() {
    log_info "更新服务..."

    # 备份数据
    backup_data

    # 拉取最新代码 (如果是git仓库)
    if [ -d ".git" ]; then
        git pull
    fi

    # 重新构建和部署
    build_image
    deploy_services $1

    log_success "服务更新完成"
}

# 快速部署
quick_deploy() {
    log_info "🚀 AI股票分析系统快速部署"
    echo "========================================"

    check_directory
    check_requirements
    create_directories
    check_config
    build_image
    deploy_services
    wait_for_services
    show_status

    log_success "🎉 快速部署完成！"
}

# 调试模式
debug_mode() {
    log_info "进入调试模式..."

    echo ""
    log_info "调试信息:"
    echo "  项目目录: ${PROJECT_DIR}"
    echo "  当前目录: ${CURRENT_DIR}"
    echo "  用户: $(whoami)"
    echo "  系统: $(uname -a)"

    echo ""
    log_info "Docker信息:"
    docker --version
    docker-compose --version

    echo ""
    log_info "容器状态:"
    docker-compose ps

    echo ""
    log_info "数据目录内容:"
    find ${PROJECT_DIR} -type f -name "*.db" -o -name "*.log" | head -10

    echo ""
    log_info "端口占用:"
    netstat -tlnp | grep 5000 || echo "端口5000未被占用"

    echo ""
    log_info "最近的容器日志:"
    docker-compose logs --tail=20 ai-stock
}

# 数据库调试
debug_database() {
    log_info "数据库调试信息..."

    local db_path="${PROJECT_DIR}/database/ai_stock.db"

    if [ -f "$db_path" ]; then
        log_success "数据库文件存在: $db_path"
        echo "  文件大小: $(du -h $db_path | cut -f1)"
        echo "  修改时间: $(stat -c %y $db_path)"

        # 检查数据库内容
        if command -v sqlite3 &> /dev/null; then
            log_info "数据库表信息:"
            sqlite3 $db_path ".tables"

            log_info "新闻数量:"
            sqlite3 $db_path "SELECT COUNT(*) FROM news;" 2>/dev/null || echo "无法查询新闻表"

            log_info "推荐数量:"
            sqlite3 $db_path "SELECT COUNT(*) FROM recommendations;" 2>/dev/null || echo "无法查询推荐表"
        else
            log_warning "sqlite3 未安装，无法查看数据库内容"
        fi
    else
        log_warning "数据库文件不存在: $db_path"
        log_info "运行数据库调试脚本: python3 scripts/server_database_debug.py"
    fi
}

# 主函数
main() {
    case "$1" in
        "init")
            check_requirements
            create_directories
            check_config
            ;;
        "build")
            build_image
            ;;
        "deploy")
            deploy_services
            wait_for_services
            show_status
            ;;
        "quick")
            quick_deploy
            ;;
        "start")
            deploy_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            deploy_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs $2
            ;;
        "backup")
            backup_data
            ;;
        "update")
            update_services
            ;;
        "cleanup")
            cleanup
            ;;
        "debug")
            debug_mode
            ;;
        "db-debug")
            debug_database
            ;;
        *)
            echo "AI股票分析系统统一部署脚本"
            echo "当前目录: ${PROJECT_DIR}"
            echo ""
            echo "使用方法: $0 <command> [options]"
            echo ""
            echo "🚀 部署命令:"
            echo "  init              初始化环境"
            echo "  build             构建Docker镜像"
            echo "  deploy            部署服务"
            echo "  quick             快速部署 (推荐)"
            echo ""
            echo "🔧 管理命令:"
            echo "  start             启动服务"
            echo "  stop              停止服务"
            echo "  restart           重启服务"
            echo "  status            显示服务状态"
            echo "  logs [service]    显示日志"
            echo ""
            echo "🛠️ 维护命令:"
            echo "  backup            备份数据"
            echo "  update            更新服务"
            echo "  cleanup           清理资源"
            echo ""
            echo "🔍 调试命令:"
            echo "  debug             调试模式"
            echo "  db-debug          数据库调试"
            echo ""
            echo "📋 使用示例:"
            echo "  $0 quick                   # 一键快速部署"
            echo "  $0 init && $0 deploy       # 分步部署"
            echo "  $0 status                  # 查看服务状态"
            echo "  $0 logs ai-stock           # 查看主服务日志"
            echo "  $0 debug                   # 查看调试信息"
            echo ""
            echo "📁 数据目录: ${PROJECT_DIR}/"
            echo "🌐 访问地址: http://服务器IP:5000"
            ;;
    esac
}

# 执行主函数
main "$@"
