## ADDED Requirements

### Requirement: 申万行业指数查询脚本执行

系统 SHALL 提供命令行脚本获取 A 股申万行业指数行情数据。

#### Scenario: 成功获取申万行业指数行情
- **WHEN** 执行 `sw_industry.py` 脚本
- **THEN** 系统返回包含 success=true 和申万行业指数列表的 JSON 数据

#### Scenario: 指定返回数量
- **WHEN** 执行脚本带 `--top 10` 参数
- **THEN** 系统返回前 10 个申万行业指数数据

#### Scenario: 指定排序字段
- **WHEN** 执行脚本带 `--sort amount` 参数
- **THEN** 系统按成交额降序返回申万行业指数数据

#### Scenario: 指定日期查询历史数据
- **WHEN** 执行脚本带 `--date 20260228` 参数
- **THEN** 系统返回指定日期的申万行业指数数据

#### Scenario: 指定行业层级
- **WHEN** 执行脚本带 `--level L1` 参数
- **THEN** 系统只返回一级行业指数数据

### Requirement: 申万行业指数数据字段

系统 SHALL 返回包含以下字段的申万行业指数行情数据。

#### Scenario: 输出包含必需字段
- **WHEN** 申万行业指数行情查询成功
- **THEN** 每个指数数据包含：rank、board_code、board_name、change_pct、close、volume、amount、turnover_rate、pe、pb

### Requirement: 申万行业 Skill 定义

系统 SHALL 提供子 skill 定义文件供 OpenClaw 智能体加载和触发。

#### Scenario: Skill 元数据完整
- **WHEN** OpenClaw 加载 sw-industry skill
- **THEN** skill 包含 name、description 和 metadata.openclaw 配置

#### Scenario: Skill 描述准确
- **WHEN** 用户询问申万行业相关问题时
- **THEN** 智能体根据 description 判断触发此 skill

### Requirement: 错误处理

系统 SHALL 正确处理各类错误情况。

#### Scenario: TUSHARE_API_TOKEN 未配置
- **WHEN** TUSHARE_API_TOKEN 环境变量未设置
- **THEN** 系统返回 success=false，error 包含"TUSHARE_API_TOKEN 未配置"

#### Scenario: 积分不足
- **WHEN** Tushare 积分不足（sw_daily 需要 120 积分）
- **THEN** 系统返回 success=false，error 包含积分不足提示

#### Scenario: 非交易日
- **WHEN** 查询日期为非交易日
- **THEN** 系统返回 success=true，count=0，data=[]
