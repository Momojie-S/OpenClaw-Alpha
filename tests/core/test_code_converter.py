# -*- coding: utf-8 -*-
"""代码格式转换器测试"""

import pytest
from pathlib import Path

from openclaw_alpha.core.code_converter import (
    convert_code,
    normalize_code,
    convert_codes,
    CodeConverterRegistry,
)
from openclaw_alpha.core.code_converter.cache import CodeCache
from openclaw_alpha.core.code_converter.tushare import TushareCodeConverter
from openclaw_alpha.core.code_converter.akshare import AKShareCodeConverter


class TestCodeCache:
    """CodeCache 测试"""

    def test_cache_path(self, tmp_path: Path):
        """测试缓存路径生成"""
        cache = CodeCache(cache_dir=tmp_path)
        path = cache.get_cache_path("tushare", "stock")
        assert path == tmp_path / "tushare_stock.json"

    def test_save_and_load(self, tmp_path: Path):
        """测试保存和加载缓存"""
        cache = CodeCache(cache_dir=tmp_path)

        # 保存
        codes = {"000001": {"market": "SZ", "name": "平安银行"}}
        cache.save("tushare", "stock", codes)

        # 加载
        loaded = cache.load("tushare", "stock")
        assert loaded == codes

    def test_load_not_exists(self, tmp_path: Path):
        """测试加载不存在的缓存"""
        cache = CodeCache(cache_dir=tmp_path)
        loaded = cache.load("tushare", "stock")
        assert loaded is None

    def test_clear_all(self, tmp_path: Path):
        """测试清除所有缓存"""
        cache = CodeCache(cache_dir=tmp_path)
        cache.save("tushare", "stock", {})
        cache.save("tushare", "index", {})

        cache.clear()

        assert not (tmp_path / "tushare_stock.json").exists()
        assert not (tmp_path / "tushare_index.json").exists()


class TestTushareCodeConverter:
    """TushareCodeConverter 测试"""

    def test_normalize(self):
        """测试标准化"""
        converter = TushareCodeConverter()

        assert converter.normalize("000001.SZ") == "000001"
        assert converter.normalize("600519.SH") == "600519"
        assert converter.normalize("000001") == "000001"
        assert converter.normalize("000001.sz") == "000001"  # 大小写不敏感

    def test_convert_to_tushare_stock(self):
        """测试转换为 Tushare 格式（股票）"""
        converter = TushareCodeConverter()

        # 使用规则推断
        assert converter.convert("000001", "tushare") == "000001.SZ"
        assert converter.convert("600519", "tushare") == "600519.SH"
        assert converter.convert("300001", "tushare") == "300001.SZ"

    def test_convert_to_tushare_index(self):
        """测试转换为 Tushare 格式（指数）"""
        converter = TushareCodeConverter()

        # 指数也使用规则推断
        assert converter.convert("000001", "tushare", "index") == "000001.SZ"
        assert converter.convert("399001", "tushare", "index") == "399001.SZ"

    def test_format_code(self):
        """测试格式化代码"""
        converter = TushareCodeConverter()

        assert converter.format_code("000001", ".SZ") == "000001.SZ"
        assert converter.format_code("600519", ".SH") == "600519.SH"


class TestAKShareCodeConverter:
    """AKShareCodeConverter 测试"""

    def test_normalize(self):
        """测试标准化"""
        converter = AKShareCodeConverter()

        assert converter.normalize("000001.SZ") == "000001"
        assert converter.normalize("hk00700") == "00700"
        assert converter.normalize("00700.HK") == "00700"

    def test_convert_to_akshare(self):
        """测试转换为 AKShare 格式"""
        converter = AKShareCodeConverter()

        # AKShare 使用无后缀代码
        assert converter.convert("000001.SZ", "akshare") == "000001"
        assert converter.convert("600519.SH", "akshare") == "600519"


class TestCodeConverterRegistry:
    """CodeConverterRegistry 测试"""

    def test_singleton(self):
        """测试单例"""
        registry1 = CodeConverterRegistry()
        registry2 = CodeConverterRegistry()
        assert registry1 is registry2

    def test_convert_code(self):
        """测试代码转换"""
        # Tushare 格式
        assert convert_code("000001", "tushare") == "000001.SZ"
        assert convert_code("600519", "tushare") == "600519.SH"

        # AKShare 格式
        assert convert_code("000001.SZ", "akshare") == "000001"
        assert convert_code("600519.SH", "akshare") == "600519"

    def test_normalize_code(self):
        """测试代码标准化"""
        assert normalize_code("000001.SZ") == "000001"
        assert normalize_code("600519.SH") == "600519"

    def test_convert_codes_batch(self):
        """测试批量转换"""
        codes = ["000001", "600519", "300001"]
        result = convert_codes(codes, "tushare")
        assert result == ["000001.SZ", "600519.SH", "300001.SZ"]

    def test_unsupported_format(self):
        """测试不支持的格式"""
        with pytest.raises(ValueError, match="不支持的代码格式"):
            convert_code("000001", "unknown")
