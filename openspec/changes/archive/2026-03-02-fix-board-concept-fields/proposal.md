## Why

当前 `board_concept.py` 实现的输出字段与设计文档 `docs/design/phase1-board-concept.md` 不一致，缺少 5 个必需字段，导致输出数据不完整。

## What Changes

- 修改 `board_concept.py` 添加缺失字段：`board_code`、`price`、`change`、`turnover_rate`、`total_mv`
- 同步更新 `skills/board-concept/SKILL.md` 的字段说明

## Capabilities

### New Capabilities

无

### Modified Capabilities

- `board-concept-query`: 修改数据字段要求，新增 5 个输出字段

## Impact

- 影响文件：`src/openclaw_alpha/commands/board_concept.py`、`skills/board-concept/SKILL.md`
- 需更新单元测试以验证新字段
- 输出 JSON 格式变更，调用方需适配
