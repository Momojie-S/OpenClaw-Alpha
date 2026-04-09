# -*- coding: utf-8 -*-
"""Pytest 配置文件"""

import os
import sys
from pathlib import Path

import pytest

# 将项目根目录和 skills 目录添加到 Python 路径
project_root = Path(__file__).parent
skills_dir = project_root / "skills"
src_dir = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(skills_dir) not in sys.path:
    sys.path.insert(0, str(skills_dir))

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def temp_workspace(tmp_path, monkeypatch):
    """临时工作空间（已废弃，不再使用 OPENCLAW_AGENT_WORKSPACE）

    Args:
        tmp_path: pytest 内置的临时目录 fixture
        monkeypatch: pytest 的 monkeypatch fixture

    Yields:
        临时工作空间路径（供测试创建文件）
    """
    # 不再设置 OPENCLAW_AGENT_WORKSPACE，直接使用 get_runtime_dir()
    yield tmp_path
