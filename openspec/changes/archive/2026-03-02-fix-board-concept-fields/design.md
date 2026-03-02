## Context

当前 `board_concept.py` 实现缺少设计文档定义的 5 个字段：`board_code`、`price`、`change`、`turnover_rate`、`total_mv`。需要补充这些字段以提供完整的板块行情数据。

## Goals / Non-Goals

**Goals:**
- 补充 5 个缺失字段，与设计文档 `docs/design/phase1-board-concept.md` 保持一致
- 更新 SKILL.md 字段说明
- 更新单元测试

**Non-Goals:**
- 不修改其他脚本（如 board_industry.py）
- 不改变 API 接口或排序逻辑

## Decisions

### 字段映射方案
- **选择**：直接从 AKShare 返回的 DataFrame 中提取对应字段
- **字段映射**：
  - 板块代码 → board_code
  - 最新价 → price
  - 涨跌额 → change
  - 换手率 → turnover_rate
  - 总市值 → total_mv

## Risks / Trade-offs

- **字段名不确定**：AKShare 返回的字段名可能与文档描述略有差异 → 运行时验证实际字段名，使用 getattr 的默认值处理缺失字段
