# 数据源参考

本目录记录项目使用的所有数据接口，每个接口一个文件。

**文档规范**：遵循 [api-doc-standard.md](../standards/api-doc-standard.md)

---

## Tushare Pro

**官网**：https://tushare.pro
**认证**：Token（环境变量 `TUSHARE_TOKEN`）

| 接口 | 用途 | 积分 | 文件 |
|------|------|:----:|------|
| sw_daily | 申万行业日线行情 | **5000** | [sw_daily.md](./tushare/sw_daily.md) |
| index_classify | 申万行业分类 | **2000** | [index_classify.md](./tushare/index_classify.md) |
| index_member_all | 申万行业成分股（分级） | **2000** | [index_member.md](./tushare/index_member.md) |

---

## AKShare

**文档**：https://akshare.akfamily.xyz
**认证**：无需

### 板块行情（东方财富）

| 接口 | 用途 | 文件 |
|------|------|------|
| stock_board_industry_name_em | 行业板块实时行情 | [stock_board_industry_name_em.md](./akshare/stock_board_industry_name_em.md) |
| stock_board_concept_name_em | 概念板块实时行情 | [stock_board_concept_name_em.md](./akshare/stock_board_concept_name_em.md) |
| stock_hot_rank_em | 股票热度排名（前100） | [stock_hot_rank_em.md](./akshare/stock_hot_rank_em.md) |

### 资金流向（同花顺）

| 接口 | 用途 | 文件 |
|------|------|------|
| stock_fund_flow_industry | 行业资金流向 | [stock_fund_flow_industry.md](./akshare/stock_fund_flow_industry.md) |
| stock_fund_flow_concept | 概念资金流向 | [stock_fund_flow_concept.md](./akshare/stock_fund_flow_concept.md) |

---

## 使用建议

| 需求 | 推荐接口 | 理由 |
|------|----------|------|
| 申万行业行情 | Tushare `sw_daily` | 字段完整，有历史数据，需5000积分 |
| 东财行业实时行情 | AKShare `stock_board_industry_name_em` | 免费，实时更新 |
| 东财概念实时行情 | AKShare `stock_board_concept_name_em` | 免费，实时更新 |
| 行业资金流向 | AKShare `stock_fund_flow_industry` | 免费，多时间维度（同花顺） |
| 概念资金流向 | AKShare `stock_fund_flow_concept` | 免费，多时间维度（同花顺） |
| 热门股票 | AKShare `stock_hot_rank_em` | 免费，基于股吧热度 |
| 行业分类查询 | Tushare `index_classify` | 申万2021版，需2000积分 |
| 行业成分股查询 | Tushare `index_member_all` | 分级查询，需2000积分 |

---

## 注意事项

### 积分要求（已核实）

| 接口 | 积分 | 备注 |
|------|:----:|------|
| sw_daily | 5000 | 之前错误记录为 120 |
| index_classify | 2000 | 之前错误记录为 120 |
| index_member_all | 2000 | 接口名修正（原为 index_member） |

### 行业分类差异

不同数据源使用不同的行业分类标准：
- **Tushare**: 申万2021版（31个一级行业）
- **AKShare（东财）**: 东方财富分类
- **AKShare（同花顺）**: 同花顺分类

### 数据源差异

| 数据类型 | 数据源 | 特点 |
|---------|--------|------|
| 板块行情 | 东方财富 | 免费，实时 |
| 资金流向 | 同花顺 | 免费，支持多时间维度 |
| 行业日线 | Tushare | 需积分，有历史数据 |
