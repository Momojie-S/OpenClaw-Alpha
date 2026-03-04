## Context

为 `industry-trend` skill 增加申万行业指数数据源。使用 Tushare Pro `sw_daily` 接口获取申万行业指数日行情数据，支持按日期和行业层级查询。

## Goals / Non-Goals

**Goals:**
- 创建申万行业指数查询脚本，使用 Tushare Pro 数据源
- 支持 `--date` 参数查询历史数据
- 支持 `--level` 参数切换行业层级（L1/L2/L3）
- 支持 `--sort` 参数按不同字段排序

**Non-Goals:**
- 不修改现有的 board_industry.py（同花顺数据源）
- 不实现缓存机制（后续可独立优化）

## Decisions

### 数据源选择：Tushare Pro
- **选择**：使用 Tushare Pro `sw_daily` 接口
- **原因**：申万行业指数是机构投资的标准分类体系，Tushare 提供完整的历史数据
- **要求**：需要 120 积分权限

### 行业层级筛选
- **L1**：一级行业（代码以 801 开头，约 30 个）
- **L2**：二级行业（代码以 801 开头，约 100+ 个）
- **L3**：三级行业（代码以 85 开头，约 200+ 个）

### 字段映射
| sw_daily 字段 | 输出字段 | 转换逻辑 |
|---------------|----------|----------|
| ts_code | board_code | 直接使用 |
| name | board_name | 直接使用 |
| pct_chg | change_pct | 直接使用 |
| close | close | 直接使用 |
| vol | volume | / 10000（手→万手）|
| amount | amount | / 100000000（元→亿）|
| turnover_rate | turnover_rate | 直接使用 |
| pe | pe | 直接使用 |
| pb | pb | 直接使用 |

## Risks / Trade-offs

- **积分要求**：sw_daily 需要 120 积分 → 检测积分不足并给出提示
- **非交易日**：返回空数据 → 返回 success=true, count=0, data=[]
- **API 限流**：Tushare 有调用频率限制 → 单次查询设计，避免频繁调用
