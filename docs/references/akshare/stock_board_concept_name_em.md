# 概念板块列表 - stock_board_concept_name_em

> 更新日期：2026-03-06
> 来源地址：https://akshare-hh.readthedocs.io/en/latest/data/stock/stock.html

---

## 官方说明

接口：stock_board_concept_name_em

描述：获取东方财富网的股票概念板块列表

来源：东方财富网

### 输入参数

无

### 输出参数

| 名称 | 类型 | 描述 |
|------|------|------|
| 板块名称 | str | 概念板块名称 |
| 板块代码 | str | 概念板块代码 |
| 最新价 | float | 板块指数最新价 |
| 涨跌幅 | float | 涨跌幅（%） |
| 涨跌额 | float | 涨跌额 |
| 成交量 | float | 成交量（手） |
| 成交额 | float | 成交额（元） |
| 换手率 | float | 换手率（%） |
| 上涨家数 | int | 板块内上涨股票数量 |
| 下跌家数 | int | 板块内下跌股票数量 |
| 领涨股票 | str | 板块内涨幅最大的股票名称 |
| 领涨股票-涨跌幅 | float | 领涨股票涨跌幅（%） |

### 接口示例

```python
import akshare as ak

# 获取概念板块列表
df = ak.stock_board_concept_name_em()
print(df)
```

### 数据示例

```
  板块名称    板块代码    最新价    涨跌幅   涨跌额    成交量        成交额         换手率  上涨家数  下跌家数  领涨股票   领涨股票-涨跌幅
0 AI      BK0001  1234.56  3.5   42.1  123456  1234567890  2.5  45    12    XX科技   9.8
1 芯片      BK0002  2345.67  2.1   48.3  234567  2345678901  3.1  56    18    YY电子   7.5
...
```

---

## 相关接口

### 获取概念板块成分股

接口：stock_board_concept_cons_em

```python
# 获取AI概念板块的成分股
df = ak.stock_board_concept_cons_em(symbol="AI")
```

### 获取概念板块历史行情

接口：stock_board_concept_hist_em

```python
# 获取AI概念板块的历史日线数据
df = ak.stock_board_concept_hist_em(symbol="AI", period="daily", start_date="20230101", end_date="20231231")
```

---

## 额外说明

### 积分要求

- 无（免费接口）

### 数据来源

- 东方财富网

### 注意事项

- 接口返回数据可能被限制（有时只返回100-200条）
- 与东方财富网页实时数据可能存在缓存延迟
- 涨跌家数可以直接获取，无需额外计算
