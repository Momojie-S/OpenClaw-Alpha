# 技术指标分析 - 设计文档

> 更新日期：2026-03-07

---

## 一、技术选型

### 1.1 数据源

**AKShare stock_zh_a_hist**

| 项目 | 说明 |
|------|------|
| 接口 | `ak.stock_zh_a_hist()` |
| 数据 | 日线历史行情（开高低收量） |
| 优点 | 免费、稳定、数据准确 |
| 限制 | 需控制请求频率（1-2秒间隔） |

### 1.2 技术指标库

**TA-Lib (talib)**

| 项目 | 说明 |
|------|------|
| 优势 | 高性能（C++ 核心）、指标丰富（150+）、广泛使用 |
| 劣势 | Windows 安装复杂 |
| 替代 | 可考虑 `pandas-ta` 或纯 Python 实现 |

**选型决策**：使用 TA-Lib，提供安装文档。如安装失败，可降级使用 `pandas-ta`。

### 1.3 为什么不用其他方案？

| 方案 | 劣势 |
|------|------|
| pandas-ta | 性能较差，指标数量少于 TA-Lib |
| 纯 Python 实现 | 性能差，维护成本高 |
| ta-lib C++ 直接调用 | 集成复杂，不符合 Python 生态 |

---

## 二、架构设计

### 2.1 模块关系

```
用户
  ↓
IndicatorProcessor (命令行入口)
  ↓
HistoryFetcher (获取历史行情)
  ↓
AKShare (数据源)
  ↓
TA-Lib (计算指标)
  ↓
输出结果
```

### 2.2 目录结构

```
skills/technical_indicators/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── history_fetcher/
    │   ├── __init__.py
    │   ├── history_fetcher.py      # 入口
    │   └── akshare.py              # AKShare 实现
    └── indicator_processor/
        ├── __init__.py
        └── indicator_processor.py  # 指标计算 + 信号判断
```

### 2.3 类设计

**HistoryFetcher**

```python
class HistoryFetcher(Fetcher):
    """历史行情数据获取器"""

    name = "history"

    async def fetch(
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        days: int = 60
    ) -> pd.DataFrame:
        """获取历史行情

        Args:
            symbol: 股票代码（如 "000001"）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            days: 天数（默认 60 天）

        Returns:
            DataFrame: 历史行情数据（日期、开高低收量）
        """
        pass
```

**HistoryFetcherAkshare**

```python
class HistoryFetcherAkshare(FetchMethod):
    """AKShare 历史行情实现"""

    name = "history_akshare"
    required_data_source = "akshare"
    priority = 1

    async def fetch(
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        days: int = 60
    ) -> pd.DataFrame:
        # 调用 ak.stock_zh_a_hist()
        # 返回 DataFrame
        pass
```

**IndicatorProcessor**

```python
class IndicatorProcessor:
    """技术指标分析处理器"""

    def __init__(self, symbol: str, days: int = 60):
        self.symbol = symbol
        self.days = days

    async def analyze(
        self,
        indicators: list[str] = None,
        params: dict = None
    ) -> dict:
        """分析技术指标

        Args:
            indicators: 指标列表（默认全部）
            params: 指标参数（可选）

        Returns:
            {
                "symbol": "000001",
                "date": "2026-03-07",
                "indicators": {
                    "macd": {...},
                    "rsi": {...},
                    "kdj": {...},
                    ...
                },
                "signals": [
                    {"indicator": "macd", "signal": "金叉", "score": 1},
                    ...
                ],
                "summary": {
                    "total_score": 2,
                    "recommendation": "买入"
                }
            }
        """
        pass

    def _calculate_macd(self, df: pd.DataFrame, params: dict) -> dict:
        """计算 MACD"""
        pass

    def _calculate_rsi(self, df: pd.DataFrame, params: dict) -> dict:
        """计算 RSI"""
        pass

    def _calculate_kdj(self, df: pd.DataFrame, params: dict) -> dict:
        """计算 KDJ"""
        pass

    def _calculate_boll(self, df: pd.DataFrame, params: dict) -> dict:
        """计算布林带"""
        pass

    def _calculate_ma(self, df: pd.DataFrame, params: dict) -> dict:
        """计算均线"""
        pass

    def _judge_signal(self, indicator: str, values: dict) -> tuple[str, int]:
        """判断信号

        Returns:
            (signal, score): 信号描述和得分
        """
        pass

    def _calculate_summary(self, signals: list) -> dict:
        """计算综合评分"""
        pass
```

---

## 三、接口契约

### 3.1 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| `symbol` | str | ✅ | - | 股票代码 |
| `--days` | int | ❌ | 60 | 历史天数 |
| `--indicators` | str | ❌ | 全部 | 指标列表（逗号分隔） |
| `--params` | str | ❌ | - | 指标参数（JSON） |
| `--top-n` | int | ❌ | 5 | 显示最近 N 天信号 |

### 3.2 输出格式

**控制台输出**（精简）：

```
技术指标分析 - 平安银行(000001)
========================================
分析日期: 2026-03-07
数据范围: 2026-01-07 ~ 2026-03-07 (60天)

【指标值】
MACD: DIF=0.25, DEA=0.18, MACD=0.14 (金叉)
RSI(14): 65.32 (中性)
KDJ: K=72.5, D=68.3, J=80.9 (超买)
布林带: 上轨=13.2, 中轨=12.5, 下轨=11.8
均线: MA5=12.3, MA10=12.1, MA20=11.9, MA60=11.5

【信号判断】
MACD: 金叉 (+1)
KDJ: 超买 (-1)
均线: 多头排列 (+1)

【综合建议】
总评分: +1
建议: 买入
```

**文件输出**（完整）：

```json
{
  "symbol": "000001",
  "name": "平安银行",
  "date": "2026-03-07",
  "data_range": {
    "start": "2026-01-07",
    "end": "2026-03-07",
    "days": 60
  },
  "indicators": {
    "macd": {
      "dif": 0.25,
      "dea": 0.18,
      "macd": 0.14,
      "histogram": [0.12, 0.13, 0.14, ...]
    },
    "rsi": {
      "value": 65.32,
      "series": [60.2, 62.5, 65.32, ...]
    },
    ...
  },
  "signals": [
    {
      "indicator": "macd",
      "signal": "金叉",
      "score": 1,
      "description": "MACD 线上穿信号线"
    },
    ...
  ],
  "summary": {
    "total_score": 1,
    "recommendation": "买入",
    "confidence": "中等"
  }
}
```

---

## 四、数据格式约定

### 4.1 历史行情数据

```python
# DataFrame 列名
columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]

# 使用时重命名为英文
df = df.rename(columns={
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume"
})
```

### 4.2 指标参数

```python
# 默认参数
DEFAULT_PARAMS = {
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "rsi": {"period": 14},
    "kdj": {"n": 9, "m1": 3, "m2": 3},
    "boll": {"period": 20, "std": 2},
    "ma": {"periods": [5, 10, 20, 60]}
}
```

---

## 五、异常处理

### 5.1 异常类型

| 异常 | 场景 | 处理方式 |
|------|------|---------|
| 股票代码无效 | 无法获取历史数据 | 返回错误信息 |
| 历史数据不足 | 少于 30 天 | 提示数据不足 |
| TA-Lib 未安装 | import 失败 | 提示安装方法 |
| 网络错误 | API 请求失败 | 自动重试（3 次） |

---

## 六、性能考虑

| 优化点 | 方案 |
|--------|------|
| 数据获取 | 异步获取，支持缓存 |
| 指标计算 | 使用 TA-Lib（C++ 核心） |
| 输出控制 | 控制台精简，文件完整 |

---

## 七、测试策略

### 7.1 单元测试

- 指标计算逻辑测试（对比已知数据）
- 信号判断逻辑测试（边界值）
- 综合评分逻辑测试

### 7.2 集成测试

- 端到端流程测试（获取数据 → 计算指标 → 输出结果）

---

## 八、后续扩展

| 阶段 | 功能 |
|------|------|
| Phase 2 | 支持周线、月线级别 |
| Phase 2 | 增加更多指标（威廉指标、ATR、CCI） |
| Phase 3 | 支持分时级别 |
| Phase 3 | 图表绘制 |
| Phase 3 | 回测验证 |
