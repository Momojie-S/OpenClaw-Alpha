# -*- coding: utf-8 -*-
"""资金流向 Processor 测试"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor import (
    FundFlowData,
    fetch_fund_flow,
    transform_data,
    process_data,
    format_output,
    save_to_file,
)


# Fixture 数据
@pytest.fixture
def sample_industry_df():
    """示例行业资金流向数据"""
    return pd.DataFrame({
        "序号": [1, 2, 3, 4, 5],
        "行业": ["农化制品", "化学原料", "养殖业", "贸易", "综合"],
        "行业指数": [6206.82, 3932.07, 3243.11, 3329.63, 2753.07],
        "行业-涨跌幅": [4.44, 3.78, 3.40, 3.19, 3.13],
        "流入资金": [146.98, 127.65, 59.86, 9.12, 61.14],
        "流出资金": [116.03, 104.90, 34.09, 6.87, 65.85],
        "净额": [30.95, 22.75, 25.77, 2.25, -4.71],
        "公司家数": [62, 60, 38, 15, 17],
        "领涨股": ["农大科技", "江天化学", "湘佳股份", "苏美达", "交运股份"],
        "领涨股-涨跌幅": [11.44, 13.13, 7.52, 8.46, 10.03],
        "当前价": [47.25, 34.90, 15.16, 15.00, 8.45],
    })


@pytest.fixture
def sample_concept_df():
    """示例概念资金流向数据"""
    return pd.DataFrame({
        "序号": [1, 2, 3],
        "行业": ["草甘膦", "环氧丙烷", "高压氧舱"],
        "行业指数": [1816.78, 1755.63, 1492.05],
        "行业-涨跌幅": [4.82, 4.49, 4.38],
        "流入资金": [30.80, 64.77, 12.85],
        "流出资金": [21.85, 49.10, 14.34],
        "净额": [8.95, 15.67, -1.49],
        "公司家数": [18, 26, 11],
        "领涨股": ["江天化学", "卫星化学", "国际医学"],
        "领涨股-涨跌幅": [13.13, 10.02, 10.11],
        "当前价": [34.90, 26.91, 5.01],
    })


class TestFundFlowData:
    """测试 FundFlowData 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        data = FundFlowData(
            rank=1,
            name="农化制品",
            index_value=6206.82,
            change_pct=4.44,
            inflow=146.98,
            outflow=116.03,
            net_amount=30.95,
            company_count=62,
            leading_stock="农大科技",
            leading_change=11.44,
            current_price=47.25,
        )
        result = data.to_dict()
        assert result["rank"] == 1
        assert result["name"] == "农化制品"
        assert result["net_amount"] == 30.95


class TestFetchFundFlow:
    """测试获取资金流向数据"""

    @patch("skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor.ak.stock_fund_flow_industry")
    def test_fetch_industry(self, mock_api, sample_industry_df):
        """测试获取行业资金流向"""
        mock_api.return_value = sample_industry_df
        result = fetch_fund_flow("industry", "今日")
        assert len(result) == 5
        assert list(result.columns) == list(sample_industry_df.columns)

    @patch("skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor.ak.stock_fund_flow_concept")
    def test_fetch_concept(self, mock_api, sample_concept_df):
        """测试获取概念资金流向"""
        mock_api.return_value = sample_concept_df
        result = fetch_fund_flow("concept", "今日")
        assert len(result) == 3


class TestTransformData:
    """测试数据转换"""

    def test_transform_basic(self, sample_industry_df):
        """测试基本转换"""
        result = transform_data(sample_industry_df)
        assert len(result) == 5
        assert result[0].name == "农化制品"
        assert result[0].net_amount == 30.95
        assert result[0].change_pct == 4.44

    def test_transform_with_string_pct(self):
        """测试字符串涨跌幅转换"""
        df = pd.DataFrame({
            "序号": [1],
            "行业": ["测试"],
            "行业指数": [1000],
            "行业-涨跌幅": ["5.5%"],
            "流入资金": [100],
            "流出资金": [50],
            "净额": [50],
            "公司家数": [10],
            "领涨股": ["领涨"],
            "领涨股-涨跌幅": ["10%"],
            "当前价": [10],
        })
        result = transform_data(df)
        assert result[0].change_pct == 5.5
        assert result[0].leading_change == 10.0


class TestProcessData:
    """测试数据处理"""

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return [
            FundFlowData(1, "A", 1000, 1.0, 100, 50, 50, 10, "股A", 5, 10),
            FundFlowData(2, "B", 1000, 2.0, 200, 100, 100, 20, "股B", 10, 20),
            FundFlowData(3, "C", 1000, -1.0, 50, 80, -30, 5, "股C", -5, 5),
        ]

    def test_sort_by_net(self, sample_data):
        """测试按净额排序"""
        result = process_data(sample_data, sort_by="net", top_n=3)
        assert result[0].net_amount == 100
        assert result[1].net_amount == 50
        assert result[2].net_amount == -30

    def test_sort_by_change(self, sample_data):
        """测试按涨幅排序"""
        result = process_data(sample_data, sort_by="change", top_n=3)
        assert result[0].change_pct == 2.0
        assert result[1].change_pct == 1.0
        assert result[2].change_pct == -1.0

    def test_filter_by_min_net(self, sample_data):
        """测试净额筛选"""
        result = process_data(sample_data, min_net=0, sort_by="net", top_n=10)
        assert len(result) == 2  # 只有 2 个净额 >= 0
        assert all(d.net_amount >= 0 for d in result)

    def test_top_n(self, sample_data):
        """测试 Top N"""
        result = process_data(sample_data, sort_by="net", top_n=2)
        assert len(result) == 2

    def test_rank_update(self, sample_data):
        """测试排名更新"""
        result = process_data(sample_data, sort_by="net", top_n=3)
        for i, d in enumerate(result, start=1):
            assert d.rank == i


class TestFormatOutput:
    """测试输出格式化"""

    @pytest.fixture
    def sample_data(self):
        return [
            FundFlowData(1, "农化制品", 6206.82, 4.44, 146.98, 116.03, 30.95, 62, "农大科技", 11.44, 47.25),
            FundFlowData(2, "化学原料", 3932.07, 3.78, 127.65, 104.90, 22.75, 60, "江天化学", 13.13, 34.90),
        ]

    def test_format_industry(self, sample_data):
        """测试行业格式化"""
        result = format_output(sample_data, "industry", "今日")
        assert "行业资金流向" in result
        assert "农化制品" in result
        assert "30.95" in result

    def test_format_concept(self, sample_data):
        """测试概念格式化"""
        result = format_output(sample_data, "concept", "今日")
        assert "概念资金流向" in result


class TestSaveToFile:
    """测试文件保存"""

    def test_save_to_custom_path(self):
        """测试保存到指定路径"""
        data = [
            FundFlowData(1, "测试", 1000, 1.0, 100, 50, 50, 10, "股A", 5, 10),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            result = save_to_file(data, "industry", "今日", str(path))
            assert result.exists()
            
            with open(result, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["type"] == "industry"
            assert saved["period"] == "今日"
            assert len(saved["data"]) == 1

    def test_save_structure(self):
        """测试保存数据结构"""
        data = [
            FundFlowData(1, "测试", 1000, 1.0, 100, 50, 50, 10, "股A", 5, 10),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            save_to_file(data, "industry", "今日", str(path))
            
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            
            assert "type" in saved
            assert "period" in saved
            assert "timestamp" in saved
            assert "count" in saved
            assert "data" in saved
            assert saved["count"] == 1
