## MODIFIED Requirements

### Requirement: 概念板块数据字段

系统 SHALL 返回包含以下字段的概念板块行情数据。

#### Scenario: 输出包含必需字段
- **WHEN** 概念板块行情查询成功
- **THEN** 每个板块数据包含：rank、board_code、board_name、price、change_pct、change、volume、amount、turnover_rate、up_count、down_count、leader_name、leader_change、total_mv
