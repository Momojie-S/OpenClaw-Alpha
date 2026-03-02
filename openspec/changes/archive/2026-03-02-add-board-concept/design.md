## Context

当前项目已有 `board_industry.py` 用于行业板块行情查询，使用 AKShare 的同花顺数据源。概念板块行情查询需要使用 AKShare 的东方财富数据源 `stock_board_concept_name_em()` 接口。

## Goals / Non-Goals

**Goals:**
- 创建概念板块行情查询脚本，复用 `board_industry.py` 的架构模式
- 输出结构化 JSON，字段命名风格与行业板块保持一致
- 创建对应的子 skill 供 OpenClaw 智能体调用

**Non-Goals:**
- 不重构现有的 board_industry.py
- 不实现概念板块的历史数据查询
- 不实现策略框架迁移（后续可独立变更）

## Decisions

### 数据源选择：东方财富
- **选择**：使用 AKShare 的 `stock_board_concept_name_em()` 接口
- **原因**：东方财富概念板块数据覆盖全面，更新及时，且该接口无需认证
- **替代方案**：同花顺概念板块接口，但东方财富接口数据更丰富

### 架构模式：复用 board_industry.py
- **选择**：保持与 board_industry.py 相同的架构模式
- **原因**：降低维护成本，保持代码风格一致
- **实现**：CLI 入口 + 函数式处理 + JSON 输出

## Risks / Trade-offs

- **接口字段差异**：东方财富接口字段可能与同花顺不完全一致 → 做字段映射适配
- **数据延迟**：免费接口可能有一定延迟 → 在输出中标注数据源
