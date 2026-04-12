# 代码格式转换器设计

## 问题背景

项目中多个 fetcher 都有代码格式转换逻辑，存在以下问题：

1. **覆盖不全**：硬编码规则只覆盖 A 股（60/68/00/30 开头），缺少基金、ETF、港股、美股等
2. **维护成本高**：新板块需要手动更新规则，分散在多个文件中
3. **重复代码**：多个 fetcher 重复实现转换逻辑

### 代码类型

| 代码类型 | 示例 | 说明 |
|----------|------|------|
| A 股 | 000001, 600519 | 沪深股票 |
| 指数 | 000001, 399001 | 上证、深证指数 |
| ETF | 510050, 159915 | 场内基金 |
| 港股 | 00700, 09988 | 港交所股票 |
| 美股 | AAPL, TSLA | 美股 |

### 数据源格式

| 数据源 | A 股格式 | 港股格式 | 美股格式 |
|--------|----------|----------|----------|
| Tushare | 000001.SZ | 00700.HK | AAPL |
| AKShare | 000001 | 00700 | AAPL |

---

## 架构设计

### 模块结构

```
src/openclaw_alpha/core/
└── code_converter/
    ├── __init__.py          # 统一入口
    ├── base.py              # 基类定义
    ├── tushare.py           # Tushare 转换器
    ├── akshare.py           # AKShare 转换器
    └── cache.py             # 缓存管理
```

### 类层级

```
CodeConverterRegistry（单例，统一入口）
    ├── register(converter, priority)
    ├── convert(code, target_format, code_type=None)
    └── _select_converter(code_type) → 按 priority 选择

CodeConverter（基类）
    ├── name: str                    # 转换器名称
    ├── data_source: str             # 对应数据源
    ├── supported_types: list[str]   # 支持的代码类型
    ├── convert(code, target_format, code_type) → str
    ├── normalize(code) → str        # 标准化为 6 位代码
    ├── format_code(code, suffix) → str
    └── _refresh_cache()             # 刷新缓存

TushareCodeConverter（实现类）
    ├── 支持类型：stock, index, etf, hk, us
    ├── 通过 stock_basic、index_basic 接口获取列表
    └── 缓存到本地

AKShareCodeConverter（实现类）
    ├── 支持类型：stock, index, etf, hk, us
    └── 通过 AKShare 接口获取列表
```

---

## 接口设计

### 统一入口

```python
from openclaw_alpha.core.code_converter import convert_code, normalize_code

# 转换为目标格式
ts_code = convert_code("000001", "tushare")  # → "000001.SZ"
ak_code = convert_code("000001.SZ", "akshare")  # → "000001"

# 标准化为 6 位代码
normalized = normalize_code("000001.SZ")  # → "000001"

# 指定代码类型（提高匹配准确性）
ts_code = convert_code("510050", "tushare", code_type="etf")  # → "510050.SH"

# 批量转换（性能优化）
ts_codes = convert_codes(["000001", "600519"], "tushare")  # → ["000001.SZ", "600519.SH"]
```

### 转换器接口

```python
class CodeConverter(ABC):
    """代码格式转换器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """转换器名称"""
        pass

    @property
    @abstractmethod
    def data_source(self) -> str:
        """对应数据源"""
        pass

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        """支持的代码类型：stock, index, etf, hk, us"""
        pass

    @abstractmethod
    def convert(self, code: str, target_format: str, code_type: str | None = None) -> str:
        """转换代码格式"""
        pass

    @abstractmethod
    def normalize(self, code: str) -> str:
        """标准化为无后缀代码"""
        pass

    @abstractmethod
    def refresh_cache(self) -> None:
        """刷新缓存"""
        pass
```

---

## 数据源转换器

### Tushare 转换器

**数据来源**：
- A 股：`stock_basic` 接口（包含 ts_code、market 字段）
- 指数：`index_basic` 接口
- ETF：`fund_basic` 接口（fund_type='ETF'）
- 港股：`hk_basic` 接口
- 美股：`us_basic` 接口

**缓存策略**：
- 本地文件缓存：`.openclaw_alpha/cache/tushare_codes_{type}.json`
- 刷新周期：超过 1 天自动刷新
- 手动刷新：支持调用 `refresh_cache()` 强制刷新

**转换规则**：
- 标准化：去掉 `.SZ`/`.SH`/`.HK` 等后缀
- 格式化：根据缓存中的市场信息添加后缀

### AKShare 转换器

**数据来源**：
- A 股：`stock_info_a_code_name()`
- 指数：`index_stock_info()`
- ETF：`fund_etf_spot_em()`
- 港股：`stock_hk_spot()`
- 美股：`stock_us_spot()`

**特点**：
- AKShare 多数接口使用无后缀代码
- 部分接口需要带市场前缀（如港股 `hk00700`）

---

## 使用示例

### 在 Fetcher 中使用

```python
from openclaw_alpha.core.code_converter import convert_code

class StockFetcherTushare(FetchMethod):
    async def _call_api(self, code: str, **kwargs):
        # 转换为 Tushare 格式
        ts_code = convert_code(code, "tushare")

        pro = self.data_source.get_client()
        df = await asyncio.to_thread(
            pro.daily,
            ts_code=ts_code,
            **kwargs
        )
        return df
```

### 批量转换

```python
from openclaw_alpha.core.code_converter import convert_codes

codes = ["000001", "600519", "510050"]
ts_codes = convert_codes(codes, "tushare")
# → ["000001.SZ", "600519.SH", "510050.SH"]
```
