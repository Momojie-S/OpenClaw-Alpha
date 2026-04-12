# -*- coding: utf-8 -*-
"""News CLI 入口。"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from openclaw_alpha.news import service


def _output(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _cmd_fetch_news(args):
    result = asyncio.run(service.fetch_and_save(
        source=args.source,
        symbol=args.symbol,
        keyword=args.keyword,
        date=args.date,
        limit=args.limit,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    ))
    _output(result)


def _cmd_update_news(args):
    analysis = None
    if args.analysis:
        analysis = json.loads(args.analysis)

    result = service.update_news(
        news_id=args.news_id,
        summary=args.summary,
        analysis=analysis,
        event_id=args.event_id,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_search_similar(args):
    result = service.search_similar(
        news_id=args.news_id,
        top=args.top,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_search_keyword(args):
    result = service.search_keyword(
        keyword=args.keyword,
        top=args.top,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    _output(result)


def _cmd_get_news(args):
    fields = args.fields.split(",") if args.fields else None
    result = service.get_news(
        news_id=args.news_id,
        fields=fields,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_get_event(args):
    result = service.get_event(
        event_id=args.event_id,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_create_event(args):
    result = service.create_event(
        title=args.title,
        news_id=args.news_id,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_close_event(args):
    result = service.close_event(
        event_id=args.event_id,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )
    if "error" in result:
        _output(result)
        sys.exit(1)
    _output(result)


def _cmd_debug_deep_analysis(args):
    """触发深度分析调试流程：扫描需深入事件 → 提交 cron → 等待结果。"""
    from openclaw_alpha.core.logger import setup_logging
    setup_logging(log_level="DEBUG")
    import logging
    logger = logging.getLogger("news.debug-deep-analysis")
    logger.info("=== debug-deep-analysis 开始 ===")

    from openclaw_alpha.backend.quick_news.jobs import execute_deep_analysis
    asyncio.run(execute_deep_analysis())
    logger.info("=== debug-deep-analysis 完成 ===")
    _output({"triggered": True})


def _cmd_debug_quick_news(args):
    """触发快速分析调试流程：拉取 → 扫描待分析 → 提交 cron → 等待结果。"""
    from openclaw_alpha.core.logger import setup_logging
    setup_logging(log_level="DEBUG")
    import logging
    logger = logging.getLogger("news.debug-quick-news")
    logger.info(f"=== debug-quick-news 开始 (limit={args.limit}) ===")

    from openclaw_alpha.backend.quick_news.jobs import fetch_all_quick_news
    asyncio.run(fetch_all_quick_news(limit=args.limit))
    logger.info("=== debug-quick-news 完成 ===")
    _output({"triggered": True, "limit": args.limit})


def _add_common_args(p):
    p.add_argument("--data-dir", help="数据根目录（默认 data/）")


def main():
    import atexit
    from openclaw_alpha.core.milvus import close as _close_milvus
    atexit.register(_close_milvus)

    parser = argparse.ArgumentParser(description="News CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # fetch-news
    p = sub.add_parser("fetch-news", help="拉取新闻并落盘")
    p.add_argument("--source", default="cls_global")
    p.add_argument("--symbol")
    p.add_argument("--keyword")
    p.add_argument("--date")
    p.add_argument("--limit", type=int, default=20)
    _add_common_args(p)
    p.set_defaults(func=_cmd_fetch_news)

    # update-news
    p = sub.add_parser("update-news", help="更新新闻字段")
    p.add_argument("news_id")
    p.add_argument("--summary")
    p.add_argument("--analysis")
    p.add_argument("--event-id")
    _add_common_args(p)
    p.set_defaults(func=_cmd_update_news)

    # search-similar
    p = sub.add_parser("search-similar", help="向量搜索相似新闻")
    p.add_argument("news_id")
    p.add_argument("--top", type=int, default=10)
    _add_common_args(p)
    p.set_defaults(func=_cmd_search_similar)

    # search-keyword
    p = sub.add_parser("search-keyword", help="关键词搜索新闻")
    p.add_argument("keyword")
    p.add_argument("--top", type=int, default=10)
    _add_common_args(p)
    p.set_defaults(func=_cmd_search_keyword)

    # get-news
    p = sub.add_parser("get-news", help="获取新闻信息")
    p.add_argument("news_id")
    p.add_argument("--fields")
    _add_common_args(p)
    p.set_defaults(func=_cmd_get_news)

    # get-event
    p = sub.add_parser("get-event", help="获取事件信息")
    p.add_argument("event_id")
    _add_common_args(p)
    p.set_defaults(func=_cmd_get_event)

    # create-event
    p = sub.add_parser("create-event", help="创建事件并关联首条新闻")
    p.add_argument("news_id")
    p.add_argument("--title", required=True, help="事件标题")
    _add_common_args(p)
    p.set_defaults(func=_cmd_create_event)

    # close-event
    p = sub.add_parser("close-event", help="关闭事件")
    p.add_argument("event_id")
    _add_common_args(p)
    p.set_defaults(func=_cmd_close_event)

    # debug-quick-news (调试)
    p = sub.add_parser("debug-quick-news", help="调试：触发快速新闻分析")
    p.add_argument("--limit", type=int, default=1, help="处理新闻数量（默认 1）")
    _add_common_args(p)
    p.set_defaults(func=_cmd_debug_quick_news)

    # debug-deep-analysis (调试)
    p = sub.add_parser("debug-deep-analysis", help="调试：触发深度分析")
    _add_common_args(p)
    p.set_defaults(func=_cmd_debug_deep_analysis)

    args = parser.parse_args()
    try:
        args.func(args)
    finally:
        from openclaw_alpha.core.milvus import close
        close()


if __name__ == "__main__":
    main()
