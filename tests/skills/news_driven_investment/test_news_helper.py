# -*- coding: utf-8 -*-
"""新闻驱动投资辅助脚本测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from openclaw_alpha.skills.news_driven_investment.news_helper import (
    save_keywords,
    load_keywords,
    save_analysis,
    save_candidates,
    load_candidates,
)


class TestKeywords:
    """关键词保存/读取测试"""

    def test_save_and_load_keywords(self, tmp_path):
        """保存和读取关键词"""
        keywords = ["AI", "算力", "光模块"]

        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "keywords.json"
            mock_path.return_value = path

            # 保存
            result = save_keywords(keywords, "2026-03-07")
            assert result == str(path)

            # 读取
            loaded = load_keywords("2026-03-07")
            assert loaded == keywords

    def test_load_keywords_not_exists(self, tmp_path):
        """读取不存在的关键词文件"""
        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "not_exists.json"
            mock_path.return_value = path

            loaded = load_keywords("2026-03-07")
            assert loaded == []

    def test_save_empty_keywords(self, tmp_path):
        """保存空关键词列表"""
        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "keywords.json"
            mock_path.return_value = path

            save_keywords([], "2026-03-07")
            loaded = load_keywords("2026-03-07")

            assert loaded == []


class TestAnalysis:
    """分析报告保存测试"""

    def test_save_analysis(self, tmp_path):
        """保存分析报告"""
        report = """# 新闻分析报告

## 关键词
- AI
- 算力

## 建议
建议关注算力板块
"""

        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "analysis.md"
            mock_path.return_value = path

            result = save_analysis(report, "2026-03-07")

            assert result == str(path)
            assert path.read_text() == report


class TestCandidates:
    """候选标的保存/读取测试"""

    def test_save_and_load_candidates(self, tmp_path):
        """保存和读取候选标的"""
        candidates = [
            {"code": "000001", "name": "平安银行", "reason": "AI相关"},
            {"code": "600000", "name": "浦发银行", "reason": "算力相关"},
        ]

        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "candidates.json"
            mock_path.return_value = path

            # 保存
            result = save_candidates(candidates, "2026-03-07")
            assert result == str(path)

            # 读取
            loaded = load_candidates("2026-03-07")
            assert loaded == candidates

    def test_load_candidates_not_exists(self, tmp_path):
        """读取不存在的候选标的文件"""
        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "not_exists.json"
            mock_path.return_value = path

            loaded = load_candidates("2026-03-07")
            assert loaded == []

    def test_save_complex_candidates(self, tmp_path):
        """保存复杂候选标的结构"""
        candidates = [
            {
                "code": "000001",
                "name": "平安银行",
                "scores": {"heat": 80, "flow": 60, "sentiment": 75},
                "tags": ["AI", "金融科技"],
            }
        ]

        with patch(
            "skills.news_driven_investment.scripts.news_helper.get_output_path"
        ) as mock_path:
            path = tmp_path / "candidates.json"
            mock_path.return_value = path

            save_candidates(candidates, "2026-03-07")
            loaded = load_candidates("2026-03-07")

            assert loaded[0]["scores"]["heat"] == 80
            assert "AI" in loaded[0]["tags"]
