# -*- coding: utf-8 -*-
"""Processor 工具函数"""

import json
import os
from pathlib import Path
from typing import Any


def get_output_path(
    skill_name: str,
    processor_name: str,
    date: str | None = None,
    ext: str = "json",
) -> Path:
    """获取 Processor 输出文件路径

    Args:
        skill_name: skill 名称
        processor_name: processor 名称
        date: 日期，默认今天（YYYY-MM-DD）
        ext: 文件扩展名，默认 json

    Returns:
        输出文件的完整路径
    """
    # 优先使用环境变量，否则使用当前工作目录
    workspace = os.getenv("OPENCLAW_AGENT_WORKSPACE")
    if not workspace:
        workspace = os.getcwd()

    if date is None:
        from datetime import datetime

        date = datetime.now().strftime("%Y-%m-%d")

    output_dir = Path(workspace) / ".openclaw_alpha" / skill_name / date
    return output_dir / f"{processor_name}.{ext}"


def load_output(
    skill_name: str,
    processor_name: str,
    date: str | None = None,
    ext: str = "json",
) -> Any | None:
    """读取 Processor 输出文件

    Args:
        skill_name: skill 名称
        processor_name: processor 名称
        date: 日期，默认今天（YYYY-MM-DD）
        ext: 文件扩展名，默认 json

    Returns:
        文件内容，或 None（文件不存在）
    """
    output_path = get_output_path(skill_name, processor_name, date, ext)

    if not output_path.exists():
        return None

    # 根据扩展名选择加载方式
    if ext == "json":
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif ext == "csv":
        import csv

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        # 其他格式直接返回文本内容
        with open(output_path, "r", encoding="utf-8") as f:
            return f.read()
