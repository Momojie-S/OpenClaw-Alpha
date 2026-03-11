# -*- coding: utf-8 -*-
"""概念板块成分股缓存管理"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from openclaw_alpha.core.path_utils import get_cache_dir, ensure_dir

logger = logging.getLogger(__name__)


class ConceptConsCache:
    """概念板块成分股缓存管理器

    负责管理概念板块成分股的本地缓存，减少网络请求。
    """

    # 缓存有效期：1小时
    CACHE_TTL = timedelta(hours=1)

    def __init__(self):
        """初始化缓存管理器"""
        self.cache_dir = get_cache_dir() / "concept_cons"
        ensure_dir(self.cache_dir)

    def _get_cache_path(self, board_name: str) -> Path:
        """获取缓存文件路径

        Args:
            board_name: 概念板块名称

        Returns:
            缓存文件路径
        """
        # 对板块名称进行简单编码，避免特殊字符
        safe_name = board_name.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_name}.json"

    def get(self, board_name: str) -> list[dict[str, Any]] | None:
        """获取缓存的成分股数据

        Args:
            board_name: 概念板块名称

        Returns:
            成分股数据列表，如果不存在或过期则返回 None
        """
        cache_path = self._get_cache_path(board_name)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 检查是否过期
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            if datetime.now() - cached_at > self.CACHE_TTL:
                logger.debug(f"缓存已过期: {board_name}")
                return None

            logger.info(f"命中缓存: {board_name}, 成分股数量: {len(data.get('items', []))}")
            return data.get("items", [])

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"读取缓存失败: {board_name}, 错误: {e}")
            return None

    def set(self, board_name: str, items: list[dict[str, Any]]) -> None:
        """保存成分股数据到缓存

        Args:
            board_name: 概念板块名称
            items: 成分股数据列表
        """
        cache_path = self._get_cache_path(board_name)

        data = {
            "cached_at": datetime.now().isoformat(),
            "board_name": board_name,
            "items": items,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存缓存: {board_name}, 成分股数量: {len(items)}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {board_name}, 错误: {e}")

    def clear(self, board_name: str | None = None) -> None:
        """清除缓存

        Args:
            board_name: 概念板块名称，为 None 则清除所有
        """
        if board_name is None:
            # 清除所有缓存
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("清除所有概念板块成分股缓存")
        else:
            # 清除指定缓存
            cache_path = self._get_cache_path(board_name)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"清除缓存: {board_name}")


# 全局单例
_cache: ConceptConsCache | None = None


def get_cache() -> ConceptConsCache:
    """获取缓存管理器单例

    Returns:
        缓存管理器实例
    """
    global _cache
    if _cache is None:
        _cache = ConceptConsCache()
    return _cache
