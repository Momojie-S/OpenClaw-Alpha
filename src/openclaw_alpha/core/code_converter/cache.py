# -*- coding: utf-8 -*-
"""代码格式转换器缓存管理"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class CodeCache:
    """代码缓存管理器

    负责管理代码列表的本地缓存，支持自动刷新。
    """

    def __init__(self, cache_dir: Path | None = None, refresh_interval_days: int = 1):
        """初始化缓存管理器

        Args:
            cache_dir: 缓存目录，默认为 .openclaw_alpha/cache/
            refresh_interval_days: 缓存刷新间隔（天）
        """
        if cache_dir is None:
            # 默认缓存目录
            workspace = Path.home() / ".openclaw" / "workspace-alpha"
            cache_dir = workspace / ".openclaw_alpha" / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.refresh_interval = timedelta(days=refresh_interval_days)

    def get_cache_path(self, converter_name: str, code_type: str) -> Path:
        """获取缓存文件路径

        Args:
            converter_name: 转换器名称
            code_type: 代码类型

        Returns:
            缓存文件路径
        """
        return self.cache_dir / f"{converter_name}_{code_type}.json"

    def load(self, converter_name: str, code_type: str) -> dict[str, Any] | None:
        """加载缓存

        Args:
            converter_name: 转换器名称
            code_type: 代码类型

        Returns:
            缓存数据，如果不存在或过期则返回 None
        """
        cache_path = self.get_cache_path(converter_name, code_type)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 检查是否过期
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            if datetime.now() - cached_at > self.refresh_interval:
                return None

            return data.get("codes", {})

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def save(
        self, converter_name: str, code_type: str, codes: dict[str, Any]
    ) -> None:
        """保存缓存

        Args:
            converter_name: 转换器名称
            code_type: 代码类型
            codes: 代码数据
        """
        cache_path = self.get_cache_path(converter_name, code_type)

        data = {
            "cached_at": datetime.now().isoformat(),
            "codes": codes,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear(self, converter_name: str | None = None, code_type: str | None = None) -> None:
        """清除缓存

        Args:
            converter_name: 转换器名称，为 None 则清除所有
            code_type: 代码类型，为 None 则清除该转换器的所有缓存
        """
        if converter_name is None:
            # 清除所有缓存
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        elif code_type is None:
            # 清除该转换器的所有缓存
            for cache_file in self.cache_dir.glob(f"{converter_name}_*.json"):
                cache_file.unlink()
        else:
            # 清除指定缓存
            cache_path = self.get_cache_path(converter_name, code_type)
            if cache_path.exists():
                cache_path.unlink()
