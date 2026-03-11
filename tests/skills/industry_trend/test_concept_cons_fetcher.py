# -*- coding: utf-8 -*-
"""概念板块成分股 Fetcher 测试"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from openclaw_alpha.skills.industry_trend.concept_cons_fetcher import (
    fetch,
    ConceptConsFetcher,
)
from openclaw_alpha.skills.industry_trend.concept_cons_fetcher.models import (
    ConceptConsItem,
)
from openclaw_alpha.skills.industry_trend.concept_cons_fetcher.cache import get_cache
from openclaw_alpha.core.exceptions import NoAvailableMethodError


@pytest.fixture(autouse=True)
def clear_cache():
    """每个测试前清除缓存"""
    cache = get_cache()
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sample_df():
    """模拟 AKShare 返回的数据"""
    return pd.DataFrame(
        [
            {
                "代码": "000001",
                "名称": "平安银行",
                "最新价": 10.5,
                "涨跌幅": 2.5,
                "涨跌额": 0.25,
                "成交量": 1000000,
                "成交额": 10500000,
                "换手率": 1.5,
                "市盈率-动态": 10.0,
                "市净率": 1.2,
            },
            {
                "代码": "000002",
                "名称": "万科A",
                "最新价": 15.3,
                "涨跌幅": 3.2,
                "涨跌额": 0.48,
                "成交量": 2000000,
                "成交额": 30600000,
                "换手率": 2.1,
                "市盈率-动态": 15.0,
                "市净率": 1.8,
            },
        ]
    )


class TestConceptConsFetcher:
    """概念板块成分股 Fetcher 测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_success(self, sample_df):
        """测试成功获取成分股"""
        with patch(
            "openclaw_alpha.skills.industry_trend.concept_cons_fetcher.akshare.ak.stock_board_concept_cons_em",
            return_value=sample_df,
        ):
            items = await fetch("人工智能")

            assert len(items) == 2
            assert items[0].code == "000001"
            assert items[0].name == "平安银行"
            assert items[0].board_name == "人工智能"
            assert items[0].change_pct == 2.5

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_empty_result(self):
        """测试获取空结果"""
        with patch(
            "openclaw_alpha.skills.industry_trend.concept_cons_fetcher.akshare.ak.stock_board_concept_cons_em",
            return_value=pd.DataFrame(),
        ):
            items = await fetch("不存在的板块")

            assert len(items) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_with_retry(self, sample_df):
        """测试重试机制"""
        call_count = 0

        def mock_api(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # 前两次失败
                raise ConnectionError("Network error")
            # 第三次成功
            return sample_df

        with patch(
            "openclaw_alpha.skills.industry_trend.concept_cons_fetcher.akshare.ak.stock_board_concept_cons_em",
            side_effect=mock_api,
        ):
            items = await fetch("人工智能")

            assert call_count == 3
            assert len(items) == 2

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_board_not_found(self):
        """测试板块不存在"""
        with patch(
            "openclaw_alpha.skills.industry_trend.concept_cons_fetcher.akshare.ak.stock_board_concept_cons_em",
            side_effect=ValueError("板块不存在"),
        ):
            # Fetcher 基类会捕获所有异常并转换为 NoAvailableMethodError
            with pytest.raises(NoAvailableMethodError, match="不存在"):
                await fetch("不存在的板块")

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_converts_code_to_6_digits(self, sample_df):
        """测试股票代码转换为6位数字"""
        # 修改测试数据，使用不足6位的代码
        sample_df.loc[0, "代码"] = "1"
        sample_df.loc[1, "代码"] = "2"

        with patch(
            "openclaw_alpha.skills.industry_trend.concept_cons_fetcher.akshare.ak.stock_board_concept_cons_em",
            return_value=sample_df,
        ):
            items = await fetch("人工智能")

            assert items[0].code == "000001"
            assert items[1].code == "000002"
