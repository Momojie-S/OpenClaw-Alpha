# -*- coding: utf-8 -*-
"""测试共享配置"""

import pytest
from pathlib import Path
import sys

# 确保 src 目录在 Python 路径中
src_dir = Path(__file__).parent.parent.parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
