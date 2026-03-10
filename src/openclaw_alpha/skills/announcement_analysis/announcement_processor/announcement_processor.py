# -*- coding: utf-8 -*-
"""公告解读 Processor - 获取和分析上市公司公告"""

import argparse
import asyncio
from datetime import datetime
from typing import Optional

import akshare as ak

from .models import Announcement


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="公告解读")
    parser.add_argument("--date", default=None, help="日期（YYYY-MM-DD），默认今日")
    parser.add_argument(
        "--type",
        default="全部",
        choices=[
            "全部",
            "重大事项",
            "财务报告",
            "融资公告",
            "风险提示",
            "资产重组",
            "信息变更",
            "持股变动",
        ],
        help="公告类型",
    )
    parser.add_argument("--code", default=None, help="股票代码筛选")
    parser.add_argument("--keyword", default=None, help="关键词搜索")
    parser.add_argument("--top-n", type=int, default=20, help="返回数量")
    return parser.parse_args()


async def fetch_announcements(date: str, announcement_type: str) -> list[Announcement]:
    """获取公告数据

    Args:
        date: 日期（YYYYMMDD 格式）
        announcement_type: 公告类型

    Returns:
        公告列表
    """
    try:
        df = ak.stock_notice_report(symbol=announcement_type, date=date)

        if df.empty:
            return []

        announcements = []
        for _, row in df.iterrows():
            ann = Announcement(
                code=str(row.get("代码", "")),
                name=str(row.get("名称", "")),
                title=str(row.get("公告标题", "")),
                type=str(row.get("公告类型", announcement_type)),
                date=str(row.get("公告日期", date)),
                url=str(row.get("公告链接", "")),
            )
            announcements.append(ann)

        return announcements

    except Exception as e:
        print(f"获取公告失败: {e}")
        return []


def filter_by_code(announcements: list[Announcement], code: str) -> list[Announcement]:
    """按股票代码筛选"""
    if not code:
        return announcements
    return [a for a in announcements if code in a.code]


def filter_by_keyword(
    announcements: list[Announcement], keyword: str
) -> list[Announcement]:
    """按关键词搜索"""
    if not keyword:
        return announcements
    keyword_lower = keyword.lower()
    return [a for a in announcements if keyword_lower in a.title.lower()]


def sort_by_priority(announcements: list[Announcement]) -> list[Announcement]:
    """按重要性排序"""
    return sorted(announcements, key=lambda a: a.priority, reverse=True)


def format_output(announcements: list[Announcement], date: str, top_n: int) -> str:
    """格式化输出"""
    lines = [f"【公告列表】{date}", ""]

    if not announcements:
        lines.append("暂无公告")
        return "\n".join(lines)

    # 按类型分组
    grouped: dict[str, list[Announcement]] = {}
    for ann in announcements[:top_n]:
        if ann.type not in grouped:
            grouped[ann.type] = []
        grouped[ann.type].append(ann)

    # 按类型重要性排序
    type_order = ["风险提示", "重大事项", "财务报告", "资产重组", "融资公告", "持股变动", "信息变更"]
    sorted_types = sorted(
        grouped.keys(), key=lambda t: type_order.index(t) if t in type_order else 999
    )

    # 输出
    total_shown = 0
    for ann_type in sorted_types:
        anns = grouped[ann_type]
        if not anns:
            continue

        # 取该类型的第一条公告获取重要性
        priority_stars = anns[0].priority_stars
        lines.append(f"{priority_stars} {ann_type}")

        for ann in anns:
            total_shown += 1
            lines.append(f"{total_shown}. {ann.code} {ann.name}：{ann.title}")
            if ann.url:
                lines.append(f"   {ann.url}")

        lines.append("")

    lines.append("---")
    lines.append(f"共 {len(announcements)} 条公告，显示 {min(len(announcements), top_n)} 条")

    return "\n".join(lines)


async def process(
    date: Optional[str] = None,
    announcement_type: str = "全部",
    code: Optional[str] = None,
    keyword: Optional[str] = None,
    top_n: int = 20,
) -> list[Announcement]:
    """处理公告查询

    Args:
        date: 日期（YYYY-MM-DD）
        announcement_type: 公告类型
        code: 股票代码
        keyword: 关键词
        top_n: 返回数量

    Returns:
        公告列表
    """
    # 处理日期
    if date:
        date_str = date.replace("-", "")
    else:
        date_str = datetime.now().strftime("%Y%m%d")

    # 获取数据
    announcements = await fetch_announcements(date_str, announcement_type)

    # 筛选
    announcements = filter_by_code(announcements, code)
    announcements = filter_by_keyword(announcements, keyword)

    # 排序
    announcements = sort_by_priority(announcements)

    return announcements


def main():
    """主入口"""
    args = parse_args()

    # 处理日期显示
    display_date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")

    # 获取并处理数据
    announcements = asyncio.run(
        process(
            date=args.date,
            announcement_type=args.type,
            code=args.code,
            keyword=args.keyword,
            top_n=args.top_n,
        )
    )

    # 输出
    output = format_output(announcements, display_date, args.top_n)
    print(output)


if __name__ == "__main__":
    main()
