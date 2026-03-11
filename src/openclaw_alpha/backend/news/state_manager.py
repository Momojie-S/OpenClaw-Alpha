# -*- coding: utf-8 -*-
"""新闻状态文件管理"""

import json
import logging
from datetime import datetime
from pathlib import Path

from .models import NewsItem, NewsItemState, NewsState

logger = logging.getLogger(__name__)

# 默认缓存目录
DEFAULT_CACHE_DIR = Path.home() / ".openclaw_alpha" / "cache" / "news" / "rsshub"


def get_state_path(route_id: str, date: str | None = None) -> Path:
    """
    获取状态文件路径

    Args:
        route_id: 路由 ID
        date: 日期（None 则使用今天）

    Returns:
        状态文件路径
    """
    date = date or datetime.now().strftime("%Y-%m-%d")
    return DEFAULT_CACHE_DIR / route_id / f"{date}.json"


def load_state(route_id: str, date: str | None = None) -> NewsState:
    """
    加载状态文件

    Args:
        route_id: 路由 ID
        date: 日期（None 则使用今天）

    Returns:
        新闻状态对象
    """
    state_path = get_state_path(route_id, date)
    date_str = date or datetime.now().strftime("%Y-%m-%d")

    if not state_path.exists():
        # 创建新的状态文件
        return NewsState(date=date_str, route_id=route_id, items=[])

    try:
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
        return NewsState(**data)
    except Exception as e:
        logger.error(f"加载状态文件失败: {state_path}, 错误: {e}")
        # 返回新状态
        return NewsState(date=date_str, route_id=route_id, items=[])


def save_state(state: NewsState) -> Path:
    """
    保存状态文件

    Args:
        state: 新闻状态对象

    Returns:
        状态文件路径
    """
    state_path = get_state_path(state.route_id, state.date)

    # 确保目录存在
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)

    logger.debug(f"状态文件已保存: {state_path}")
    return state_path


def is_processed(state: NewsState, item_id: str) -> bool:
    """
    检查新闻是否已处理

    Args:
        state: 新闻状态对象
        item_id: 新闻 ID

    Returns:
        是否已处理
    """
    for item in state.items:
        if item.id == item_id:
            return item.processed
    return False


def mark_processed(
    state: NewsState,
    item: NewsItem,
    job_id: str | None = None,
    workspace_dir: str | None = None,
) -> None:
    """
    标记新闻为已处理

    Args:
        state: 新闻状态对象
        item: 新闻对象
        job_id: 分析任务 ID
        workspace_dir: 工作目录路径
    """
    # 查找现有记录
    for existing_item in state.items:
        if existing_item.id == item.id:
            existing_item.processed = True
            existing_item.processed_at = datetime.now().isoformat()
            existing_item.job_id = job_id
            existing_item.workspace_dir = workspace_dir
            return

    # 添加新记录
    state.items.append(
        NewsItemState(
            id=item.id,
            title=item.title,
            link=item.link,
            published=item.published.isoformat() if item.published else None,
            processed=True,
            processed_at=datetime.now().isoformat(),
            job_id=job_id,
            workspace_dir=workspace_dir,
        )
    )


def add_pending(state: NewsState, item: NewsItem) -> None:
    """
    添加待处理新闻（不标记为已处理）

    Args:
        state: 新闻状态对象
        item: 新闻对象
    """
    # 检查是否已存在
    for existing_item in state.items:
        if existing_item.id == item.id:
            return  # 已存在，不重复添加

    # 添加新记录
    state.items.append(
        NewsItemState(
            id=item.id,
            title=item.title,
            link=item.link,
            published=item.published.isoformat() if item.published else None,
            processed=False,
        )
    )


def cleanup_old_states(keep_days: int = 7) -> list[Path]:
    """
    清理过期的状态文件

    Args:
        keep_days: 保留天数

    Returns:
        删除的文件列表
    """
    from datetime import timedelta

    deleted = []
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    if not DEFAULT_CACHE_DIR.exists():
        return deleted

    for route_dir in DEFAULT_CACHE_DIR.iterdir():
        if not route_dir.is_dir():
            continue

        for state_file in route_dir.glob("*.json"):
            try:
                # 从文件名解析日期
                date_str = state_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    state_file.unlink()
                    deleted.append(state_file)
                    logger.info(f"已删除过期状态文件: {state_file}")
            except Exception as e:
                logger.warning(f"清理状态文件失败: {state_file}, 错误: {e}")

    return deleted
