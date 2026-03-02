## ADDED Requirements

### Requirement: 概念板块行情查询脚本执行

系统 SHALL 提供命令行脚本获取 A 股概念板块实时行情数据。

#### Scenario: 成功获取概念板块行情
- **WHEN** 执行 `board_concept.py` 脚本
- **THEN** 系统返回包含 success=true 和概念板块列表的 JSON 数据

#### Scenario: 指定返回数量
- **WHEN** 执行脚本带 `--top 10` 参数
- **THEN** 系统返回前 10 个概念板块数据

#### Scenario: 指定排序字段
- **WHEN** 执行脚本带 `--sort amount` 参数
- **THEN** 系统按成交额降序返回概念板块数据

### Requirement: 概念板块数据字段

系统 SHALL 返回包含以下字段的概念板块行情数据。

#### Scenario: 输出包含必需字段
- **WHEN** 概念板块行情查询成功
- **THEN** 每个板块数据包含：rank、board_code、board_name、price、change_pct、change、volume、amount、turnover_rate、up_count、down_count、leader_name、leader_change、total_mv

### Requirement: 概念板块 Skill 定义

系统 SHALL 提供子 skill 定义文件供 OpenClaw 智能体加载和触发。

#### Scenario: Skill 元数据完整
- **WHEN** OpenClaw 加载 board-concept skill
- **THEN** skill 包含 name、description 和 metadata.openclaw 配置

#### Scenario: Skill 描述准确
- **WHEN** 用户询问概念板块相关问题时
- **THEN** 智能体根据 description 判断触发此 skill
