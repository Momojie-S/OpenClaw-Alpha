# -*- coding: utf-8 -*-
"""框架核心模块"""

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import DuplicateDataSourceError, NoAvailableMethodError
from openclaw_alpha.core.fetcher import FetchMethod, Fetcher
from openclaw_alpha.core.path_utils import (
    ensure_dir,
    get_cache_dir,
    get_config_dir,
    get_log_dir,
    get_news_analysis_task_dir,
    get_project_root,
    get_skills_dir,
    get_task_template_path,
    get_workspace_dir,
)
from openclaw_alpha.core.processor_utils import get_output_path, load_output
from openclaw_alpha.core.registry import DataSourceRegistry

__all__ = [
    # 数据源
    "DataSource",
    "DataSourceRegistry",
    "DuplicateDataSourceError",
    # Fetcher
    "Fetcher",
    "FetchMethod",
    "NoAvailableMethodError",
    # Processor 工具
    "get_output_path",
    "load_output",
    # 路径工具
    "get_project_root",
    "get_config_dir",
    "get_cache_dir",
    "get_log_dir",
    "get_skills_dir",
    "get_workspace_dir",
    "get_task_template_path",
    "get_news_analysis_task_dir",
    "ensure_dir",
]
