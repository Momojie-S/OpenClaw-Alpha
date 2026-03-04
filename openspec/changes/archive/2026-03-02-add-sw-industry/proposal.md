## Why

为 `industry-trend` skill 增加申万行业指数数据源，用于追踪标准化行业分类的热度变化，支持历史数据对比判断升温/降温趋势。申万行业分类是国内机构投资的标准分类体系。

## What Changes

- 新增申万行业指数查询脚本 `src/openclaw_alpha/commands/sw_industry.py`
- 新增子 skill `skills/sw-industry/SKILL.md`
- 使用 Tushare Pro `sw_daily` 接口（需要 TUSHARE_API_TOKEN）
- 支持按日期、行业层级（L1/L2/L3）查询

## Capabilities

### New Capabilities

- `sw-industry-query`: A 股申万行业指数行情查询能力，支持历史数据和行业层级筛选

### Modified Capabilities

无

## Impact

- 新增代码文件，不影响现有功能
- 数据源：Tushare Pro（需要 120 积分权限）
- 需要配置 TUSHARE_API_TOKEN 环境变量
