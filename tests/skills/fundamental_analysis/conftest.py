# -*- coding: utf-8 -*-
"""fundamental_analysis 测试配置"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
skills_dir = project_root / "skills"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(skills_dir) not in sys.path:
    sys.path.insert(0, str(skills_dir))


@pytest.fixture
def fixtures_dir():
    """测试 fixtures 目录"""
    return Path(__file__).parent / "fixtures"
