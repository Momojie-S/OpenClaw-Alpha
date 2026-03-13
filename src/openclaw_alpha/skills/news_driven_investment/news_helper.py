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


def append_system_info(task_dir: str, job_id: str, session_id: str, context_path: str, context_path_deleted: str | None = None) -> str:
    """
    在报告末尾追加系统运行信息

    Args:
        task_dir: 任务工作目录
        job_id: Cron 任务 ID
        session_id: 当前 session ID（sessionKey）
        context_path: OpenClaw 上下文存储路径（session file，.jsonl）
        context_path_deleted: Session 备份文件路径模式（.deleted.*），用于 session 被删除后回溯

    Returns:
        报告文件路径

    Raises:
        FileNotFoundError: report.md 不存在

    Note:
        此函数会同时记录两个路径到 report.md，由使用者复盘时根据实际情况查找。
        - context_path: 原始 .jsonl 路径（可能已被删除）
        - context_path_deleted: 备份路径模式 .deleted.*（用于 glob 匹配）
    """
    from pathlib import Path

    report_path = Path(task_dir) / "report.md"

    if not report_path.exists():
        raise FileNotFoundError(f"报告文件不存在: {report_path}")

    # 构造系统运行信息（同时记录两个路径）
    system_info = f"""

---

## 系统运行信息

- **Job ID**: {job_id}
- **Session ID**: {session_id}
- **Session 文件（原始路径）**: {context_path}"""

    # 如果有 deleted 路径模式，也记录下来
    if context_path_deleted:
        system_info += f"""
- **Session 备份路径（删除后）**: {context_path_deleted}
"""
        system_info += f"""
> **说明**: 原始 Session 文件可能已被 OpenClaw 清理。
> 复盘时请先查看原始路径，如不存在则使用备份路径模式 glob 查找最新的 .deleted 文件。
"""

    system_info += f"""
"""

    # 追加到报告末尾
    current_content = report_path.read_text(encoding="utf-8")
    report_path.write_text(current_content + system_info, encoding="utf-8")

    return str(report_path)


def main():
    parser = argparse.ArgumentParser(description="新闻驱动投资分析辅助脚本")
    parser.add_argument("--action", choices=["save_keywords", "load_keywords",
                                              "save_analysis", "save_candidates", "load_candidates",
                                              "append_system_info"],
                       required=True)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--keywords", nargs="*", help="关键词列表")
    parser.add_argument("--report", help="分析报告内容")
    parser.add_argument("--candidates", help="候选标的 JSON")
    parser.add_argument("--task-dir", help="任务工作目录（用于 append_system_info）")
    parser.add_argument("--session-id", help="当前 session ID（用于 append_system_info）")
    parser.add_argument("--context-path", help="OpenClaw 上下文存储路径（用于 append_system_info）")
    parser.add_argument("--context-path-deleted", help="Session 备份文件路径模式（用于 append_system_info）")
    
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

    elif args.action == "append_system_info":
        if args.task_dir and args.session_id and args.context_path:
            try:
                path = append_system_info(args.task_dir, args.session_id, args.context_path, args.context_path_deleted)
                print(f"已追加系统运行信息到: {path}")
            except FileNotFoundError as e:
                print(f"错误: {e}")
        else:
            print("错误: 需要提供 --task-dir, --session-id 和 --context-path")


if __name__ == "__main__":
    main()
