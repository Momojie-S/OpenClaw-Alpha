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
    """创建临时工作空间并设置环境变量

    Args:
        tmp_path: pytest 内置的临时目录 fixture
        monkeypatch: pytest 的 monkeypatch fixture

    Yields:
        临时工作空间路径
    """
    # 设置环境变量指向临时目录
    monkeypatch.setenv("OPENCLAW_AGENT_WORKSPACE", str(tmp_path))
    yield tmp_path
