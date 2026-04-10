# -*- coding: utf-8 -*-
"""统一配置管理

合并 .env 凭据 + runtime/config.json 功能配置，提供单一 Settings 入口。
"""

import json
import os
from pathlib import Path
from typing import Any


def _find_project_root() -> Path:
    """从包路径推断项目根目录"""
    # settings.py -> core -> openclaw_alpha -> src -> 项目根
    return Path(__file__).parent.parent.parent.parent


class Settings:
    """统一配置管理类

    从环境变量读取凭据，从 runtime/config.json 读取功能配置。
    """

    def __init__(self) -> None:
        env_root = os.getenv("OPENCLAW_ALPHA_ROOT")
        self._root = Path(env_root) if env_root else _find_project_root()
        self._config: dict[str, Any] | None = None

    @property
    def project_root(self) -> Path:
        return self._root

    @property
    def _data(self) -> dict[str, Any]:
        if self._config is None:
            config_path = self._root / "runtime" / "config.json"
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            self._config = json.loads(config_path.read_text(encoding="utf-8"))
        return self._config

    # --- 凭据（来自环境变量）---

    @property
    def tushare_token(self) -> str:
        value = os.getenv("TUSHARE_TOKEN")
        if not value:
            raise ValueError("缺少必填配置: TUSHARE_TOKEN（请在 .env 中设置）")
        return value

    @property
    def tushare_credit(self) -> int:
        try:
            return int(os.getenv("TUSHARE_CREDIT", "0"))
        except ValueError:
            return 0

    @property
    def dashscope_api_key(self) -> str:
        value = os.getenv("DASHSCOPE_API_KEY")
        if not value:
            raise ValueError("缺少必填配置: DASHSCOPE_API_KEY（请在 .env 中设置）")
        return value

    @property
    def milvus_uri(self) -> str:
        value = os.getenv("MILVUS_URI")
        if not value:
            raise ValueError("缺少必填配置: MILVUS_URI（请在 .env 中设置）")
        return value

    @property
    def milvus_token(self) -> str:
        value = os.getenv("MILVUS_TOKEN")
        if not value:
            raise ValueError("缺少必填配置: MILVUS_TOKEN（请在 .env 中设置）")
        return value

    _INHERITABLE_KEYS = ("agent_id", "model", "delivery")

    def _with_defaults(self, module_data: dict[str, Any]) -> dict[str, Any]:
        """将 defaults 中的 agent_id/model/delivery 合并到模块配置"""
        defaults = self._data.get("defaults", {})
        result = dict(module_data)
        for key in self._INHERITABLE_KEYS:
            if key not in result and key in defaults:
                result[key] = defaults[key]
        return result

    # --- 功能配置（来自 config.json）---

    @property
    def quick_news(self) -> dict[str, Any]:
        return self._with_defaults(self._data.get("quick_news", {}))

    @property
    def feedback(self) -> dict[str, Any]:
        return self._with_defaults(self._data.get("feedback", {}))

    @property
    def event_review(self) -> dict[str, Any]:
        return self._with_defaults(self._data.get("event_review", {}))

    @property
    def tushare_config(self) -> dict[str, Any]:
        return self._data.get("tushare", {})


settings = Settings()
