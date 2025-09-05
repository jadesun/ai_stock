#!/usr/bin/env python3
"""
AI选股系统主程序入口
Author: Corey (ljingfan@pku.org.cn)
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.frontend.app import create_app
from src.database.database_manager import db_manager
from src.scheduler.scheduler import scheduler
from src.scheduler import jobs
from config.settings import WEB_CONFIG, LOGGING_CONFIG, SCHEDULER_CONFIG


def init_project():
    """初始化项目"""
    logger = setup_logger("main", LOGGING_CONFIG['level'])
    
    try:
        # 创建必要的目录
        directories = ['database', 'logs', 'database/backup']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
        
        # 初始化数据库
        logger.info("初始化数据库...")
        db_info = db_manager.get_database_info()
        logger.info(f"数据库初始化完成: {db_info}")
        
        # 创建数据库索引
        db_manager.create_indexes()
        logger.info("数据库索引创建完成")
        
        logger.info("项目初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"项目初始化失败: {e}")
        return False


def run_crawler(max_articles=50, use_scrapy=True, use_dynamic=True):
    """运行爬虫 - 现在只支持动态爬虫"""
    logger = setup_logger("crawler", LOGGING_CONFIG['level'])

    try:
        if use_scrapy:
            logger.info(f"开始运行Scrapy动态爬虫，最大文章数: {max_articles}")

            from src.scrapy_crawler.runner import scrapy_crawler

            # 只使用动态爬虫
            articles = scrapy_crawler.crawl_eastmoney_dynamic(
                max_articles=max_articles,
                target_url='https://finance.eastmoney.com/a/czqyw.html'
            )

            logger.info(f"Scrapy动态爬虫运行完成，共获取 {len(articles)} 篇文章")

            if articles:
                sources = {}
                for article in articles:
                    source = article.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1

                logger.info("爬取结果统计:")
                for source, count in sources.items():
                    logger.info(f"  {source}: {count} 篇")

            return len(articles) > 0
        else:
            # Selenium爬虫已移除，强制使用Scrapy动态爬虫
            logger.warning("Selenium爬虫已移除，自动切换到Scrapy动态爬虫")
            return run_crawler(max_articles, use_scrapy=True, use_dynamic=True)

    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        return False


def run_llm_analysis(batch_size=10):
    """运行LLM分析"""
    logger = setup_logger("llm_analysis", LOGGING_CONFIG['level'])

    try:
        logger.info(f"Starting LLM analysis with batch size: {batch_size}")

        from src.llm.analysis_manager import AnalysisManager

        # 创建分析管理器
        manager = AnalysisManager(llm_provider="ark")

        # 获取统计信息
        stats_before = manager.get_analysis_statistics()
        logger.info(f"Before analysis - Total: {stats_before.get('total_news', 0)}, "
                   f"Analyzed: {stats_before.get('analyzed_news', 0)}, "
                   f"Unanalyzed: {stats_before.get('unanalyzed_news', 0)}")

        if stats_before.get('unanalyzed_news', 0) == 0:
            logger.info("No unanalyzed news found")
            return True

        # 执行批量分析 - 使用更小的批次和更好的错误处理
        try:
            # 限制批次大小以减少失败风险
            safe_batch_size = min(batch_size, 5)
            logger.info(f"Using safe batch size: {safe_batch_size}")

            results = manager.analyze_unprocessed_news(batch_size=safe_batch_size)

            if results:
                logger.info(f"Analysis results - Processed: {results.get('total_processed', 0)}, "
                           f"Successful: {results.get('successful', 0)}, Failed: {results.get('failed', 0)}")

                # 获取分析后统计
                stats_after = manager.get_analysis_statistics()
                logger.info(f"After analysis - Total: {stats_after.get('total_news', 0)}, "
                           f"Analyzed: {stats_after.get('analyzed_news', 0)}, "
                           f"Analysis rate: {stats_after.get('analysis_rate', 0):.2%}")

                # 只要有部分成功就认为是成功的
                success_count = results.get('successful', 0)
                if success_count > 0:
                    logger.info(f"LLM analysis partially successful: {success_count} news analyzed")
                    return True
                else:
                    logger.warning("LLM analysis completed but no news was successfully analyzed")
                    return False
            else:
                logger.error("LLM analysis returned no results")
                return False

        except Exception as analysis_error:
            logger.error(f"Batch analysis failed: {analysis_error}")
            logger.info("Analysis completed with errors, but some news may have been processed")
            return False

    except Exception as e:
        logger.error(f"LLM analysis setup failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def run_crawler_and_analyze(max_articles=20):
    """运行爬虫并进行LLM分析"""
    logger = setup_logger("crawler_analyzer", LOGGING_CONFIG['level'])

    try:
        logger.info(f"开始爬取和分析新闻，最大文章数: {max_articles}")

        from src.scrapy_crawler.runner import scrapy_crawler

        articles = scrapy_crawler.crawl_and_analyze(
            max_articles=max_articles,
            target_url='https://finance.eastmoney.com/a/czqyw.html'
        )

        logger.info(f"爬取和分析完成，处理了 {len(articles)} 篇文章")
        return len(articles) > 0

    except Exception as e:
        logger.error(f"爬取和分析失败: {e}")
        return False


def setup_scheduler():
    """设置定时任务"""
    logger = setup_logger("scheduler", LOGGING_CONFIG['level'])

    try:
        logger.info("设置定时任务...")

        # 添加配置中定义的任务
        for job_config in SCHEDULER_CONFIG['jobs']:
            job_id = job_config['id']
            func_path = job_config['func']

            # 解析函数路径
            module_path, func_name = func_path.rsplit(':', 1)

            # 获取函数对象
            if func_name == 'crawl_news_job':
                func = jobs.crawl_news_job
            elif func_name == 'analyze_news_job':
                func = jobs.analyze_news_job
            elif func_name == 'cleanup_old_data_job':
                func = jobs.cleanup_old_data_job
            elif func_name == 'backup_database_job':
                func = jobs.backup_database_job
            else:
                logger.warning(f"未知的任务函数: {func_name}")
                continue

            # 添加任务
            scheduler.add_job(
                job_id=job_id,
                func=func,
                trigger_type=job_config['trigger'],
                max_instances=job_config.get('max_instances', 1),
                hour=job_config.get('hour'),
                minute=job_config.get('minute', 0)
            )

        logger.info("定时任务设置完成")
        return True

    except Exception as e:
        logger.error(f"设置定时任务失败: {e}")
        return False


def run_scheduler():
    """运行调度器"""
    logger = setup_logger("scheduler", LOGGING_CONFIG['level'])

    try:
        logger.info("启动任务调度器...")

        # 设置定时任务
        if not setup_scheduler():
            logger.error("定时任务设置失败")
            return False

        # 启动调度器
        if scheduler.start():
            logger.info("任务调度器启动成功")

            # 显示任务信息
            jobs_info = scheduler.get_jobs()
            logger.info(f"已加载 {len(jobs_info)} 个定时任务:")
            for job_id, job_info in jobs_info.items():
                logger.info(f"  - {job_id}: {job_info['trigger']}")

            return True
        else:
            logger.error("任务调度器启动失败")
            return False

    except Exception as e:
        logger.error(f"调度器运行失败: {e}")
        return False


def run_web_server():
    """运行Web服务器"""
    logger = setup_logger("web", LOGGING_CONFIG['level'])

    try:
        logger.info("启动Web服务器...")
        app = create_app()

        app.run(
            host=WEB_CONFIG['host'],
            port=WEB_CONFIG['port'],
            debug=WEB_CONFIG['debug']
        )

    except Exception as e:
        logger.error(f"Web服务器启动失败: {e}")
        return False


def run_full_service():
    """运行完整服务（调度器 + Web服务器）"""
    logger = setup_logger("service", LOGGING_CONFIG['level'])

    try:
        logger.info("启动完整服务...")

        # 启动调度器
        if not run_scheduler():
            logger.error("调度器启动失败")
            return False

        # 启动Web服务器（这会阻塞主线程）
        logger.info("调度器启动成功，现在启动Web服务器...")
        run_web_server()

    except KeyboardInterrupt:
        logger.info("接收到停止信号，正在关闭服务...")
        scheduler.stop()
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"完整服务运行失败: {e}")
        scheduler.stop()
        return False


def show_status():
    """显示系统状态"""
    logger = setup_logger("status", LOGGING_CONFIG['level'])
    
    try:
        print("\n=== AI选股系统状态 ===")
        
        # 数据库状态
        db_info = db_manager.get_database_info()
        print(f"\n数据库信息:")
        print(f"  路径: {db_info.get('database_path', 'N/A')}")
        print(f"  大小: {db_info.get('database_size_bytes', 0) / 1024 / 1024:.2f} MB")
        print(f"  表数量: {len(db_info.get('tables', []))}")
        
        # 数据统计
        stats = db_manager.get_statistics()
        print(f"\n数据统计:")
        print(f"  新闻总数: {stats.get('total_news', 0)}")
        print(f"  今日新闻: {stats.get('today_news', 0)}")
        print(f"  推荐总数: {stats.get('total_recommendations', 0)}")
        print(f"  今日推荐: {stats.get('today_recommendations', 0)}")
        print(f"  股票总数: {stats.get('total_stocks', 0)}")
        print(f"  板块总数: {stats.get('total_sectors', 0)}")
        print(f"  平均置信度: {stats.get('avg_confidence_score', 0)}%")
        
        # 表记录数
        table_counts = db_info.get('table_counts', {})
        if table_counts:
            print(f"\n表记录数:")
            for table, count in table_counts.items():
                print(f"  {table}: {count}")
        
        print("\n===================")
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI选股系统')
    parser.add_argument('command', choices=['init', 'crawl', 'analyze', 'crawl-analyze', 'web', 'scheduler', 'service', 'status'],
                       help='要执行的命令')
    parser.add_argument('--max-articles', type=int, default=50,
                       help='爬虫最大文章数量 (默认: 50)')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='LLM分析批次大小 (默认: 10)')
    parser.add_argument('--use-scrapy', action='store_true', default=True,
                       help='使用Scrapy爬虫引擎 (默认: True)')
    parser.add_argument('--use-selenium', action='store_true',
                       help='使用Selenium爬虫引擎')
    parser.add_argument('--use-dynamic', action='store_true', default=True,
                       help='使用动态爬虫 (Selenium) 进行JavaScript渲染 (默认: True)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='ERROR', help='日志级别 (默认: ERROR)')
    
    args = parser.parse_args()
    
    # 设置日志级别
    LOGGING_CONFIG['level'] = args.log_level
    
    if args.command == 'init':
        print("正在初始化AI选股系统...")
        if init_project():
            print("Project initialization successful!")
            print("\nNext you can:")
            print("  python main.py crawl         # Run crawler to get data")
            print("  python main.py analyze       # Run LLM analysis")
            print("  python main.py crawl-analyze # Run crawler and LLM analysis")
            print("  python main.py web           # Start Web service")
            print("  python main.py scheduler     # Start scheduled tasks")
            print("  python main.py service       # Start full service (scheduler+Web)")
            print("  python main.py status        # View system status")
        else:
            print("Project initialization failed!")
            sys.exit(1)

    elif args.command == 'crawl':
        if args.use_selenium:
            engine = "Selenium"
            use_scrapy = False
            use_dynamic = False
        else:
            # 默认使用动态爬虫 (唯一选项)
            engine = "Scrapy动态"
            use_scrapy = True
            use_dynamic = True

        print(f"Running {engine} crawler (max articles: {args.max_articles})...")
        if run_crawler(args.max_articles, use_scrapy=use_scrapy, use_dynamic=use_dynamic):
            print("Crawler completed successfully!")
        else:
            print("Crawler failed!")
            sys.exit(1)

    elif args.command == 'analyze':
        print(f"Running LLM analysis (batch size: {args.batch_size})...")
        if run_llm_analysis(args.batch_size):
            print("LLM analysis completed successfully!")
        else:
            print("LLM analysis failed!")
            sys.exit(1)

    elif args.command == 'crawl-analyze':
        print(f"Running Scrapy crawler and LLM analysis (max articles: {args.max_articles})...")
        if run_crawler_and_analyze(args.max_articles):
            print("Crawler and analysis completed successfully!")
        else:
            print("Crawler and analysis failed!")
            sys.exit(1)

    elif args.command == 'web':
        print("Starting Web server...")
        print(f"Access URL: http://{WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
        run_web_server()

    elif args.command == 'scheduler':
        print("Starting scheduled task scheduler...")
        if run_scheduler():
            print("Scheduler started successfully!")
            print("Scheduled tasks are running in background, press Ctrl+C to stop")
            try:
                # 保持程序运行
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                scheduler.stop()
                print("Scheduler stopped")
        else:
            print("Scheduler startup failed!")
            sys.exit(1)

    elif args.command == 'service':
        print("Starting full service (scheduler + Web server)...")
        print(f"Web access URL: http://{WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
        run_full_service()

    elif args.command == 'status':
        show_status()


if __name__ == '__main__':
    main()
