# 设计文档 - technical_indicators

## 一、技术方案

使用 **TA-Lib** 计算技术指标，原因：
- 性能高（C 语言实现）
- 算法标准（业界认可）
- 支持多种指标

**数据获取**：AKShare（免费、稳定）

**输出方式**：
- 控制台：精简结果（指标值 + 信号 + 建议）
- 文件：完整数据（含历史序列）
- 信号文件：历史买卖信号（用于回测）

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 历史行情 | AKShare | `stock_zh_a_hist()` |
| 历史行情 | Tushare | `daily()`（备用）|

## 三、模块划分

```
technical_indicators/
├── scripts/
│   ├── history_fetcher/       # 历史行情获取
│   │   ├── history_fetcher.py # Fetcher 入口
│   │   ├── akshare_impl.py    # AKShare 实现
│   │   └── tushare_impl.py    # Tushare 实现
│   ├── indicator_processor/   # 技术指标分析
│   │   └── indicator_processor.py
│   └── volume_price_processor/ # 量价关系分析
│       └── volume_price_processor.py
└── docs/
```

### history_fetcher

**职责**：获取股票历史行情数据

**输出字段**：
- date, open, high, low, close, volume, amount

### indicator_processor

**职责**：计算技术指标，判断买卖信号

**输入**：股票代码、天数、指标参数

**输出**：
- 指标值（MACD、RSI、KDJ、布林带、均线）
- 信号评分
- 综合建议

**信号输出**：
- 支持 `--signal-only` 输出历史买卖信号
- 信号类型：ma_cross, rsi, bollinger

### volume_price_processor

**职责**：分析量价关系

**输入**：股票代码、天数

**输出**：
- OBV 趋势
- 量价相关系数
- 成交量状态
- 量比

## 四、依赖

### TA-Lib

**安装**：
```bash
# Linux
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

## 五、接口契约

### indicator_processor

```bash
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py <symbol> [--days N] [--indicators X,Y] [--signal-only]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| symbol | 股票代码 | 必填 |
| --days | 历史天数 | 60 |
| --indicators | 指标列表 | 全部 |
| --signal-only | 只输出信号 | false |

### volume_price_processor

```bash
uv run --env-file .env python skills/technical_indicators/scripts/volume_price_processor/volume_price_processor.py <symbol> [--days N]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| symbol | 股票代码 | 必填 |
| --days | 历史天数 | 60 |

## 六、信号输出格式

**路径**：`.openclaw_alpha/signals/technical/{symbol}/ma_cross_5_20.json`

```json
{
  "signal_id": "ma_cross_5_20",
  "signal_type": "technical",
  "stock_code": "000001",
  "signals": [
    {
      "date": "2026-03-10",
      "action": "buy",
      "score": 1,
      "reason": "金叉",
      "metadata": {"fast_ma": 12.50, "slow_ma": 12.30}
    }
  ]
}
```
