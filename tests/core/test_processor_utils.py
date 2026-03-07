# -*- coding: utf-8 -*-
"""processor_utils 测试"""

import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from openclaw_alpha.core.processor_utils import get_output_path, load_output


class TestGetOutputPath:
    """get_output_path 测试类"""

    def test_basic_path(self, temp_workspace):
        """测试基本路径生成"""
        path = get_output_path("test_skill", "test_processor")

        # 验证路径结构
        assert str(temp_workspace) in str(path)
        assert ".openclaw_alpha" in str(path)
        assert "test_skill" in str(path)
        assert "test_processor.json" in str(path)

    def test_default_date_is_today(self, temp_workspace):
        """测试默认日期是今天"""
        path = get_output_path("test_skill", "test_processor")
        today = datetime.now().strftime("%Y-%m-%d")

        assert today in str(path)

    def test_custom_date(self, temp_workspace):
        """测试自定义日期"""
        path = get_output_path("test_skill", "test_processor", date="2026-03-06")

        assert "2026-03-06" in str(path)
        assert path.name == "test_processor.json"

    def test_custom_extension(self, temp_workspace):
        """测试自定义扩展名"""
        path = get_output_path("test_skill", "test_processor", ext="csv")

        assert path.name == "test_processor.csv"

    def test_no_workspace_env(self, monkeypatch):
        """测试未设置环境变量时使用当前工作目录"""
        monkeypatch.delenv("OPENCLAW_AGENT_WORKSPACE", raising=False)

        # 不应抛出异常，而是使用当前工作目录
        path = get_output_path("test_skill", "test_processor")

        # 验证路径结构仍然正确
        assert ".openclaw_alpha" in str(path)
        assert "test_skill" in str(path)
        assert "test_processor.json" in str(path)

    def test_path_structure(self, temp_workspace):
        """测试路径结构完整"""
        path = get_output_path("my_skill", "my_processor", date="2026-01-15", ext="csv")

        # 验证路径各部分
        parts = path.parts
        assert "my_skill" in parts
        assert "2026-01-15" in parts
        assert path.name == "my_processor.csv"


class TestLoadOutput:
    """load_output 测试类"""

    def test_load_json_file(self, temp_workspace):
        """测试加载 JSON 文件"""
        # 创建测试文件
        path = get_output_path("test_skill", "test_processor", date="2026-03-06", ext="json")
        path.parent.mkdir(parents=True, exist_ok=True)

        test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 加载并验证
        result = load_output("test_skill", "test_processor", date="2026-03-06", ext="json")

        assert result == test_data

    def test_load_csv_file(self, temp_workspace):
        """测试加载 CSV 文件"""
        # 创建测试文件
        path = get_output_path("test_skill", "test_processor", date="2026-03-06", ext="csv")
        path.parent.mkdir(parents=True, exist_ok=True)

        test_data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "age"])
            writer.writeheader()
            writer.writerows(test_data)

        # 加载并验证
        result = load_output("test_skill", "test_processor", date="2026-03-06", ext="csv")

        assert result == test_data

    def test_load_text_file(self, temp_workspace):
        """测试加载其他格式文件（返回文本）"""
        # 创建测试文件
        path = get_output_path("test_skill", "test_processor", date="2026-03-06", ext="txt")
        path.parent.mkdir(parents=True, exist_ok=True)

        test_content = "Hello, World!"
        with open(path, "w", encoding="utf-8") as f:
            f.write(test_content)

        # 加载并验证
        result = load_output("test_skill", "test_processor", date="2026-03-06", ext="txt")

        assert result == test_content

    def test_load_nonexistent_file(self, temp_workspace):
        """测试加载不存在的文件返回 None"""
        result = load_output("test_skill", "not_exist", date="2026-03-06")

        assert result is None

    def test_load_with_default_date(self, temp_workspace):
        """测试使用默认日期加载"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 创建今天的文件
        path = get_output_path("test_skill", "today_processor", ext="json")
        path.parent.mkdir(parents=True, exist_ok=True)

        test_data = {"today": True}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 不传日期参数加载
        result = load_output("test_skill", "today_processor")

        assert result == test_data

    def test_load_json_with_chinese(self, temp_workspace):
        """测试加载包含中文的 JSON 文件"""
        path = get_output_path("test_skill", "chinese_processor", ext="json")
        path.parent.mkdir(parents=True, exist_ok=True)

        test_data = {"name": "测试名称", "description": "这是中文描述"}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False)

        result = load_output("test_skill", "chinese_processor")

        assert result == test_data
        assert result["name"] == "测试名称"

    def test_no_workspace_env(self, monkeypatch):
        """测试未设置环境变量时使用当前工作目录"""
        monkeypatch.delenv("OPENCLAW_AGENT_WORKSPACE", raising=False)

        # 不应抛出异常，而是使用当前工作目录
        path = get_output_path("test_skill", "test_processor")

        # 验证路径结构仍然正确
        assert ".openclaw_alpha" in str(path)
        assert "test_skill" in str(path)
