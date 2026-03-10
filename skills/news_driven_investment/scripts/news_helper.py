# -*- coding: utf-8 -*-
"""新闻驱动投资分析 - 辅助脚本

用于保存和读取中间结果，支持跨 Skill 数据传递。
"""

import json
import argparse
from datetime import datetime
from openclaw_alpha.core.processor_utils import get_output_path


def save_keywords(keywords: list[str], date: str = None):
    """保存提取的关键词"""
    path = get_output_path("news_driven_investment", "keywords", date, ext="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(keywords, ensure_ascii=False, indent=2))
    return str(path)


def load_keywords(date: str = None) -> list[str]:
    """读取关键词"""
    path = get_output_path("news_driven_investment", "keywords", date, ext="json")
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_analysis(report: str, date: str = None):
    """保存分析报告"""
    path = get_output_path("news_driven_investment", "analysis", date, ext="md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    return str(path)


def save_candidates(candidates: list[dict], date: str = None):
    """保存候选标的"""
    path = get_output_path("news_driven_investment", "candidates", date, ext="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    return str(path)


def load_candidates(date: str = None) -> list[dict]:
    """读取候选标的"""
    path = get_output_path("news_driven_investment", "candidates", date, ext="json")
    if path.exists():
        return json.loads(path.read_text())
    return []


def main():
    parser = argparse.ArgumentParser(description="新闻驱动投资分析辅助脚本")
    parser.add_argument("--action", choices=["save_keywords", "load_keywords", 
                                              "save_analysis", "save_candidates", "load_candidates"],
                       required=True)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--keywords", nargs="*", help="关键词列表")
    parser.add_argument("--report", help="分析报告内容")
    parser.add_argument("--candidates", help="候选标的 JSON")
    
    args = parser.parse_args()
    
    if args.action == "save_keywords":
        if args.keywords:
            path = save_keywords(args.keywords, args.date)
            print(f"已保存关键词到: {path}")
        else:
            print("错误: 需要提供 --keywords")
    
    elif args.action == "load_keywords":
        keywords = load_keywords(args.date)
        print(json.dumps(keywords, ensure_ascii=False, indent=2))
    
    elif args.action == "save_analysis":
        if args.report:
            path = save_analysis(args.report, args.date)
            print(f"已保存报告到: {path}")
        else:
            print("错误: 需要提供 --report")
    
    elif args.action == "save_candidates":
        if args.candidates:
            candidates = json.loads(args.candidates)
            path = save_candidates(candidates, args.date)
            print(f"已保存候选标的到: {path}")
        else:
            print("错误: 需要提供 --candidates")
    
    elif args.action == "load_candidates":
        candidates = load_candidates(args.date)
        print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
