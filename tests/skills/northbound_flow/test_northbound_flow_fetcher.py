# -*- coding: utf-8 -*-
"""北向资金数据获取器测试"""

import json
import pytest
from pathlib import Path

from skills.northbound_flow.scripts.flow_fetcher.akshare_flow import FlowFetcherAkshare


# 加载 fixture 数据
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> list[dict]:
    """加载 fixture 数据"""
    file_path = FIXTURE_DIR / filename
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 将 NaN 转换为 None（JSON 不支持 NaN）
    for item in data:
        for key, value in item.items():
            if isinstance(value, float) and str(value) == "nan":
                item[key] = None
    return data


class TestFlowFetcherAkshare:
    """北向资金数据获取器测试类"""

    @pytest.fixture
    def fetcher(self):
        """创建 fetcher 实例"""
        return FlowFetcherAkshare()

    @pytest.fixture
    def sh_hist_data(self):
        """沪股通历史数据"""
        return load_fixture("sh_hist_response.json")

    @pytest.fixture
    def sz_hist_data(self):
        """深股通历史数据"""
        return load_fixture("sz_hist_response.json")

    @pytest.fixture
    def stocks_data(self):
        """个股持股数据"""
        return load_fixture("stocks_response.json")

    # ========== _transform_hist 测试 ==========

    def test_transform_hist_basic(self, fetcher, sh_hist_data):
        """测试基本转换功能"""
        result = fetcher._transform_hist(sh_hist_data)

        # 验证返回类型
        assert isinstance(result, list)
        assert len(result) > 0

        # 验证数据结构
        for item in result:
            assert "date" in item
            assert "net_buy" in item
            assert isinstance(item["date"], str)
            assert isinstance(item["net_buy"], float)

    def test_transform_hist_field_mapping(self, fetcher, sh_hist_data):
        """测试字段映射正确性"""
        result = fetcher._transform_hist(sh_hist_data)

        # 找到对应的数据
        # 第一条数据：2014-11-17, 净买额 120.8233
        first_item = result[0]
        assert first_item["date"] == "2014-11-17"
        assert abs(first_item["net_buy"] - 120.82) < 0.01  # 四舍五入

    def test_transform_hist_skip_nan(self, fetcher):
        """测试跳过 NaN 数据"""
        # 构造包含 NaN 的测试数据
        raw_data = [
            {"日期": "2024-01-01", "当日成交净买额": 10.5},
            {"日期": "2024-01-02", "当日成交净买额": None},  # None（对应 NaN）
            {"日期": "2024-01-03", "当日成交净买额": 15.3},
        ]

        result = fetcher._transform_hist(raw_data)

        # 验证 NaN 数据被跳过
        assert len(result) == 2
        assert result[0]["date"] == "2024-01-01"
        assert result[1]["date"] == "2024-01-03"

    # ========== _combine_flows 测试 ==========

    def test_combine_flows_basic(self, fetcher, sh_hist_data, sz_hist_data):
        """测试基本合并功能"""
        sh_flows = fetcher._transform_hist(sh_hist_data)
        sz_flows = fetcher._transform_hist(sz_hist_data)

        result = fetcher._combine_flows(sh_flows, sz_flows)

        # 验证返回类型
        assert isinstance(result, list)
        assert len(result) > 0

        # 验证数据结构
        for item in result:
            assert "date" in item
            assert "sh_flow" in item
            assert "sz_flow" in item
            assert "total_flow" in item
            assert "status" in item

    def test_combine_flows_calculation(self, fetcher):
        """测试合并计算正确性"""
        sh_flows = [
            {"date": "2024-01-01", "net_buy": 10.5},
            {"date": "2024-01-02", "net_buy": 20.3},
        ]
        sz_flows = [
            {"date": "2024-01-01", "net_buy": 5.2},
            {"date": "2024-01-02", "net_buy": -3.1},
        ]

        result = fetcher._combine_flows(sh_flows, sz_flows)

        # 验证计算正确
        # 按日期降序排列
        assert result[0]["date"] == "2024-01-02"
        assert result[0]["sh_flow"] == 20.3
        assert result[0]["sz_flow"] == -3.1
        assert result[0]["total_flow"] == 17.2

        assert result[1]["date"] == "2024-01-01"
        assert result[1]["sh_flow"] == 10.5
        assert result[1]["sz_flow"] == 5.2
        assert result[1]["total_flow"] == 15.7

    def test_combine_flows_missing_date(self, fetcher):
        """测试日期缺失时的处理"""
        sh_flows = [
            {"date": "2024-01-01", "net_buy": 10.5},
            {"date": "2024-01-02", "net_buy": 20.3},
        ]
        sz_flows = [
            {"date": "2024-01-01", "net_buy": 5.2},
            # 2024-01-02 缺失
        ]

        result = fetcher._combine_flows(sh_flows, sz_flows)

        # 验证缺失日期用 0 填充
        assert len(result) == 2
        jan_02 = [r for r in result if r["date"] == "2024-01-02"][0]
        assert jan_02["sh_flow"] == 20.3
        assert jan_02["sz_flow"] == 0.0
        assert jan_02["total_flow"] == 20.3

    # ========== _transform_stocks 测试 ==========

    def test_transform_stocks_basic(self, fetcher, stocks_data):
        """测试基本转换功能"""
        result = fetcher._transform_stocks(stocks_data)

        # 验证返回类型
        assert isinstance(result, list)
        assert len(result) > 0

        # 验证数据结构
        for item in result:
            assert "code" in item
            assert "name" in item
            assert "hold_change" in item
            assert "hold_ratio" in item
            assert "direction" in item
            assert "date" in item

    def test_transform_stocks_field_mapping(self, fetcher, stocks_data):
        """测试字段映射正确性"""
        result = fetcher._transform_stocks(stocks_data)

        # 第一条数据：长江电力，5日增持估计-市值 66114.97
        first_item = result[0]
        assert first_item["code"] == "600900"
        assert first_item["name"] == "长江电力"
        assert abs(first_item["hold_change"] - 66114.97) < 0.01
        assert first_item["direction"] == "流入"

    def test_transform_stocks_direction(self, fetcher):
        """测试流入/流出判断"""
        raw_data = [
            {
                "代码": "000001",
                "名称": "平安银行",
                "5日增持估计-市值": 10000.0,
                "5日增持估计-占流通股比": 0.5,
                "日期": "2024-01-01"
            },
            {
                "代码": "000002",
                "名称": "万科A",
                "5日增持估计-市值": -5000.0,
                "5日增持估计-占流通股比": -0.3,
                "日期": "2024-01-01"
            },
        ]

        result = fetcher._transform_stocks(raw_data)

        # 验证流入判断
        assert result[0]["name"] == "平安银行"
        assert result[0]["direction"] == "流入"

        # 验证流出判断
        assert result[1]["name"] == "万科A"
        assert result[1]["direction"] == "流出"

    def test_transform_stocks_handle_null(self, fetcher):
        """测试空值处理"""
        raw_data = [
            {
                "代码": "000001",
                "名称": "平安银行",
                "5日增持估计-市值": None,  # 空值
                "5日增持估计-占流通股比": None,
                "日期": "2024-01-01"
            },
        ]

        result = fetcher._transform_stocks(raw_data)

        # 验证空值转换为 0
        assert result[0]["hold_change"] == 0.0
        assert result[0]["hold_ratio"] == 0.0

    # ========== _get_status 测试 ==========

    def test_get_status_large_inflow(self, fetcher):
        """测试大幅流入判断"""
        assert fetcher._get_status(60.0) == "大幅流入"
        assert fetcher._get_status(100.0) == "大幅流入"

    def test_get_status_inflow(self, fetcher):
        """测试流入判断"""
        assert fetcher._get_status(15.0) == "流入"
        assert fetcher._get_status(50.0) == "流入"

    def test_get_status_balance(self, fetcher):
        """测试平衡判断"""
        assert fetcher._get_status(5.0) == "平衡"
        assert fetcher._get_status(0.0) == "平衡"
        assert fetcher._get_status(-5.0) == "平衡"

    def test_get_status_outflow(self, fetcher):
        """测试流出判断"""
        assert fetcher._get_status(-15.0) == "流出"
        assert fetcher._get_status(-50.0) == "流出"

    def test_get_status_large_outflow(self, fetcher):
        """测试大幅流出判断"""
        assert fetcher._get_status(-60.0) == "大幅流出"
        assert fetcher._get_status(-100.0) == "大幅流出"
