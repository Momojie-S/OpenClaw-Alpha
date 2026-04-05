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
    _output({"message": "create-event 待后续统一设计"})


def _add_common_args(p):
    p.add_argument("--data-dir", help="数据根目录（默认 data/）")


def main():
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

    # create-event (预留)
    p = sub.add_parser("create-event", help="创建事件（预留）")
    p.add_argument("news_id")
    p.add_argument("--summary")
    _add_common_args(p)
    p.set_defaults(func=_cmd_create_event)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
