# -*- coding: utf-8 -*-
"""自选股监控 Processor 测试"""

import json
import pytest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor import (
    WatchlistManager,
    WatchlistProcessor,
    WatchlistData,
    WatchlistItem,
    WatchlistSummary,
    StockSpot,
)


# ==================== Fixtures ====================

@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    return tmp_path / "watchlist"


@pytest.fixture
def manager(temp_data_dir):
    """WatchlistManager 实例"""
    return WatchlistManager(data_dir=temp_data_dir)


@pytest.fixture
def processor(manager):
    """WatchlistProcessor 实例"""
    return WatchlistProcessor(manager=manager)


@pytest.fixture
def sample_stocks():
    """示例股票数据"""
    return [
        StockSpot(code="000001", name="平安银行", price=12.50, change_pct=2.35, turnover_rate=3.2, amount=15.6, market_cap=2400),
        StockSpot(code="600000", name="浦发银行", price=8.20, change_pct=-0.50, turnover_rate=1.5, amount=8.2, market_cap=2000),
        StockSpot(code="002475", name="立讯精密", price=35.00, change_pct=5.20, turnover_rate=4.5, amount=25.0, market_cap=2500),
        StockSpot(code="601318", name="中国平安", price=50.00, change_pct=0.00, turnover_rate=0.8, amount=30.0, market_cap=9000),
        StockSpot(code="000002", name="万科A", price=10.50, change_pct=-2.10, turnover_rate=2.0, amount=12.0, market_cap=1200),
    ]


# ==================== WatchlistManager 测试 ====================

class TestWatchlistManager:
    """WatchlistManager 测试"""

    def test_init_creates_data_dir(self, temp_data_dir):
        """初始化时创建数据目录"""
        manager = WatchlistManager(data_dir=temp_data_dir)
        assert manager.data_dir.exists()

    def test_load_empty_file(self, manager):
        """加载空文件"""
        data = manager.load()
        assert data.stocks == []
        assert data.updated_at == ""

    def test_add_stocks(self, manager):
        """添加股票"""
        added, existing = manager.add(["000001", "600000"])
        assert added == ["000001", "600000"]
        assert existing == []

        # 验证已保存
        data = manager.load()
        assert len(data.stocks) == 2
        assert data.stocks[0].code == "000001"
        assert data.stocks[1].code == "600000"

    def test_add_duplicate_stocks(self, manager):
        """添加重复股票"""
        manager.add(["000001"])
        added, existing = manager.add(["000001", "600000"])
        assert added == ["600000"]
        assert existing == ["000001"]

    def test_add_normalize_codes(self, manager):
        """标准化股票代码"""
        # 测试补零
        added, _ = manager.add(["1", "6000"])
        assert "000001" in added
        assert "006000" in added

        # 测试去后缀
        added, _ = manager.add(["000002.SZ"])
        assert "000002" in added

    def test_remove_stocks(self, manager):
        """移除股票"""
        manager.add(["000001", "600000", "002475"])

        watchlist = manager.load()
        original_len = len(watchlist.stocks)
        codes_to_remove = {"000001"}
        watchlist.stocks = [item for item in watchlist.stocks if item.code not in codes_to_remove]
        manager.save(watchlist)

        data = manager.load()
        assert len(data.stocks) == 2
        codes = [s.code for s in data.stocks]
        assert "000001" not in codes
        assert "600000" in codes

    def test_clear(self, manager):
        """清空列表"""
        manager.add(["000001", "600000"])
        manager.clear()
        data = manager.load()
        assert data.stocks == []

    def test_list_codes(self, manager):
        """列出股票代码"""
        manager.add(["000001", "600000"])
        codes = manager.list_codes()
        assert codes == ["000001", "600000"]


# ==================== WatchlistProcessor 测试 ====================

class TestWatchlistProcessor:
    """WatchlistProcessor 测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_watch_empty_list(self, processor):
        """空列表获取行情"""
        stocks = await processor.watch()
        assert stocks == []

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_watch_filters_stocks(self, manager, processor, sample_stocks):
        """筛选自选股"""
        manager.add(["000001", "600000"])

        with patch(
            "skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor.fetch_spot",
            new_callable=AsyncMock,
            return_value=sample_stocks,
        ):
            stocks = await processor.watch()

        assert len(stocks) == 2
        codes = {s.code for s in stocks}
        assert codes == {"000001", "600000"}

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_watch_sorts_by_change(self, manager, processor, sample_stocks):
        """按涨跌幅排序"""
        manager.add(["000001", "600000", "002475"])

        with patch(
            "skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor.fetch_spot",
            new_callable=AsyncMock,
            return_value=sample_stocks,
        ):
            stocks = await processor.watch()

        # 按涨跌幅降序
        assert stocks[0].code == "002475"  # +5.20%
        assert stocks[1].code == "000001"  # +2.35%
        assert stocks[2].code == "600000"  # -0.50%

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_watch_top_n(self, manager, processor, sample_stocks):
        """限制返回数量"""
        manager.add(["000001", "600000", "002475"])

        with patch(
            "skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor.fetch_spot",
            new_callable=AsyncMock,
            return_value=sample_stocks,
        ):
            stocks = await processor.watch(top_n=2)

        assert len(stocks) == 2

    def test_analyze_empty_list(self, processor):
        """空列表分析"""
        summary = processor.analyze([])
        assert summary.total == 0
        assert summary.up_count == 0
        assert summary.avg_change == 0.0
        assert summary.best is None
        assert summary.worst is None

    def test_analyze_statistics(self, processor, sample_stocks):
        """统计分析"""
        summary = processor.analyze(sample_stocks)

        assert summary.total == 5
        assert summary.up_count == 2  # +2.35%, +5.20%
        assert summary.down_count == 2  # -0.50%, -2.10%
        assert summary.flat_count == 1  # 0.00%

        # 平均涨跌幅 = (2.35 - 0.50 + 5.20 + 0 - 2.10) / 5 = 0.99
        assert abs(summary.avg_change - 0.99) < 0.01

    def test_analyze_best_worst(self, processor, sample_stocks):
        """表现最好和最差"""
        summary = processor.analyze(sample_stocks)

        assert summary.best.code == "002475"
        assert summary.best.change_pct == 5.20
        assert summary.worst.code == "000002"
        assert summary.worst.change_pct == -2.10

    def test_analyze_limit_up(self, processor):
        """涨停检测"""
        stocks = [
            StockSpot(code="000001", name="股票1", price=10.0, change_pct=10.0, turnover_rate=1.0, amount=1.0, market_cap=100),
            StockSpot(code="000002", name="股票2", price=10.0, change_pct=9.95, turnover_rate=1.0, amount=1.0, market_cap=100),
            StockSpot(code="000003", name="股票3", price=10.0, change_pct=5.0, turnover_rate=1.0, amount=1.0, market_cap=100),
        ]
        summary = processor.analyze(stocks)

        # 涨停阈值是 9.9%
        assert len(summary.limit_up) == 2
        codes = {s.code for s in summary.limit_up}
        assert "000001" in codes
        assert "000002" in codes

    def test_analyze_limit_down(self, processor):
        """跌停检测"""
        stocks = [
            StockSpot(code="000001", name="股票1", price=10.0, change_pct=-10.0, turnover_rate=1.0, amount=1.0, market_cap=100),
            StockSpot(code="000002", name="股票2", price=10.0, change_pct=-5.0, turnover_rate=1.0, amount=1.0, market_cap=100),
        ]
        summary = processor.analyze(stocks)

        # 跌停阈值是 -9.9%
        assert len(summary.limit_down) == 1
        assert summary.limit_down[0].code == "000001"

    def test_format_watch_empty(self, processor):
        """格式化空列表"""
        output = processor.format_watch([])
        assert "为空" in output

    def test_format_watch_with_stocks(self, processor, sample_stocks):
        """格式化行情输出"""
        output = processor.format_watch(sample_stocks[:3])

        assert "自选股行情" in output
        assert "共 3 只" in output
        assert "000001" in output
        assert "平安银行" in output
        assert "统计" in output

    def test_format_analyze_empty(self, processor):
        """格式化空分析"""
        output = processor.format_analyze([])
        assert "为空" in output

    def test_format_analyze_with_stocks(self, processor, sample_stocks):
        """格式化分析输出"""
        output = processor.format_analyze(sample_stocks)

        assert "自选股分析报告" in output
        assert "市场统计" in output
        assert "表现最好" in output
        assert "表现最差" in output
        # 根据数据，表现最好是立讯精密(002475)，表现最差是万科A(000002)
        assert "立讯精密" in output
        assert "万科A" in output


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """边界情况测试"""

    def test_add_empty_list(self, manager):
        """添加空列表"""
        added, existing = manager.add([])
        assert added == []
        assert existing == []

    def test_add_with_whitespace(self, manager):
        """添加带空格的代码"""
        added, _ = manager.add([" 000001 ", "  600000"])
        assert "000001" in added
        assert "600000" in added

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_watch_code_not_found(self, manager, processor):
        """自选股代码不在行情中"""
        manager.add(["999999"])  # 不存在的代码

        sample = [
            StockSpot(code="000001", name="平安银行", price=12.50, change_pct=2.35, turnover_rate=3.2, amount=15.6, market_cap=2400),
        ]

        with patch(
            "skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor.fetch_spot",
            new_callable=AsyncMock,
            return_value=sample,
        ):
            stocks = await processor.watch()

        assert stocks == []
