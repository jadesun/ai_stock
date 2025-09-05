# 📁 AI股票分析系统项目结构

**版本**: v1.0  
**更新时间**: 2025-01-04  
**开发者**: Corey (lijingfan@pku.org.cn)

## 🏗️ 项目目录结构

```
AI_Stock/                           # 项目根目录
├── 📦 Docker配置
│   ├── docker-compose.yml         # Docker编排配置
│   ├── Dockerfile                 # 容器镜像定义
│   └── .dockerignore              # Docker忽略文件
├── ⚙️ 配置文件
│   ├── .env                       # 环境变量配置
│   ├── requirements.txt           # Python依赖包
│   └── config/                    # 配置模块
│       ├── __init__.py
│       ├── settings.py            # 主配置文件
│       └── env_loader.py          # 环境变量加载器
├── 🚀 主程序
│   └── main.py                    # 程序入口
├── 📁 源代码
│   └── src/                       # 源代码目录
│       ├── __init__.py
│       ├── database/              # 数据库模块
│       │   ├── __init__.py
│       │   ├── models.py          # 数据模型
│       │   ├── database_manager.py # 数据库管理器
│       │   ├── clear_database.py  # 数据库清理
│       │   └── check_crawled_news.py # 新闻检查
│       ├── frontend/              # Web前端
│       │   ├── __init__.py
│       │   ├── app.py             # Flask应用
│       │   ├── templates/         # HTML模板
│       │   │   ├── base.html
│       │   │   ├── index.html
│       │   │   ├── news.html
│       │   │   ├── recommendations.html
│       │   │   └── simple_test.html
│       │   └── static/            # 静态资源
│       │       ├── css/
│       │       ├── js/
│       │       └── images/
│       ├── llm/                   # LLM分析模块
│       │   ├── __init__.py
│       │   ├── llm_service.py     # LLM服务
│       │   └── analysis_manager.py # 分析管理器
│       ├── scrapy_crawler/        # 爬虫模块
│       │   ├── __init__.py
│       │   ├── settings.py        # Scrapy设置
│       │   ├── items.py           # 数据项定义
│       │   ├── pipelines.py       # 数据管道
│       │   ├── middlewares.py     # 中间件
│       │   ├── runner.py          # 爬虫运行器
│       │   ├── selenium_helper.py # Selenium助手
│       │   ├── selenium_middleware.py # Selenium中间件
│       │   ├── spider_runner.py   # 爬虫执行器
│       │   └── spiders/           # 爬虫定义
│       │       ├── __init__.py
│       │       └── eastmoney_dynamic_spider.py
│       ├── scheduler/             # 任务调度
│       │   ├── __init__.py
│       │   ├── scheduler.py       # 调度器
│       │   └── jobs.py            # 任务定义
│       └── utils/                 # 工具函数
│           ├── __init__.py
│           └── logger.py          # 日志工具
├── 🛠️ 管理脚本
│   ├── deploy.sh                  # 部署脚本
│   └── scripts/                   # 辅助脚本
│       ├── server_database_debug.py      # 数据库调试
│       ├── check_server_environment.py   # 环境检查
│       ├── test_docker_deployment.py     # 部署测试
│       └── test_scheduler_tasks.py       # 任务测试
├── 📚 文档
│   ├── README.md                  # 项目说明
│   └── PROJECT_STRUCTURE.md       # 本文件
└── 💾 数据目录 (运行时创建)
    ├── database/                  # 数据库文件
    │   ├── ai_stock.db           # 主数据库
    │   └── backup/               # 数据库备份
    ├── logs/                     # 日志文件
    │   ├── app.log              # 应用日志
    │   ├── crawler.log          # 爬虫日志
    │   └── llm.log              # LLM日志
    └── data/                     # 临时数据
```

## 📦 核心文件说明

### Docker配置
- **docker-compose.yml**: 定义服务编排，包含Web服务、数据卷映射、环境变量
- **Dockerfile**: 定义容器镜像构建过程，安装依赖和配置环境
- **.dockerignore**: 排除不需要打包到镜像中的文件

### 配置文件
- **.env**: 环境变量配置，包含API密钥、数据库路径等关键配置
- **requirements.txt**: Python依赖包列表
- **config/settings.py**: 主配置文件，定义所有模块的配置参数

### 主程序
- **main.py**: 程序入口，支持多种运行模式（爬虫、分析、Web、调度、服务）

### 核心模块
- **database/**: 数据库操作，包含模型定义和数据管理
- **frontend/**: Web界面，Flask应用和HTML模板
- **llm/**: AI分析模块，调用DeepSeek-v3.1进行新闻分析
- **scrapy_crawler/**: 爬虫模块，抓取财经新闻
- **scheduler/**: 任务调度，定时执行爬虫和分析任务

## 🚀 部署文件

### 必须上传的文件
上传到服务器项目目录：

```
📦 核心文件 (必须)
├── docker-compose.yml
├── Dockerfile
├── .env
├── requirements.txt
├── main.py
├── config/
└── src/

🛠️ 管理文件 (可选)
├── deploy.sh
├── scripts/
└── README.md
```

### 运行时创建的目录
系统运行时会自动创建：
- `./database/` - 数据库文件
- `./logs/` - 日志文件
- `./data/` - 临时数据

## 🔧 关键配置

### 环境变量 (.env)
```bash
# LLM配置 (必须)
LLM_API_KEY=your-volcengine-ark-api-key-here
LLM_MODEL=ep-20250827105540-7wzzj

# Web服务
WEB_HOST=0.0.0.0
WEB_PORT=5000

# 爬虫配置
SCRAPY_MAX_ARTICLES=50
SCRAPY_DELAY=1

# 数据库路径（相对路径）
DATABASE_PATH=database/ai_stock.db
```

### Docker编排 (docker-compose.yml)
```yaml
services:
  ai-stock:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./data:/app/data
    env_file:
      - .env
```

## 📊 数据流转

```
财经网站 → 爬虫模块 → 数据库 → LLM分析 → 推荐结果 → Web界面
    ↓           ↓         ↓        ↓         ↓
  新闻内容    结构化数据   存储    AI分析    用户访问
```

## ⏰ 自动任务

- **爬虫任务**: 每小时第0分钟执行
- **分析任务**: 每小时第10分钟执行
- **Web服务**: 持续运行

## 🎯 系统特点

- **完全Docker化**: 一键部署，环境隔离
- **自动化运行**: 无需人工干预，24小时运行
- **模块化设计**: 清晰的代码结构，易于维护
- **数据持久化**: 重启后数据不丢失
- **实时监控**: 日志记录，状态查看

---

**🎉 项目结构清晰，部署简单，运行稳定！**
