## ADDED Requirements

### Requirement: 每日回顾调度
系统 SHALL 每日定时扫描所有 status=ongoing 的事件，逐个触发 Agent 回顾任务。

#### Scenario: 正常每日调度
- **WHEN** 到达配置的每日回顾时间
- **THEN** 系统扫描所有 status=ongoing 的事件，对每个事件触发一个 Agent Session 执行回顾任务

#### Scenario: 无 ongoing 事件
- **WHEN** 到达每日回顾时间，但没有 status=ongoing 的事件
- **THEN** 跳过，不触发任何 Agent Session

#### Scenario: 手动触发单个事件回顾
- **WHEN** 用户请求回顾某个事件
- **THEN** 系统对该事件触发一个 Agent Session 执行回顾任务，不受定时调度限制

### Requirement: Agent 回顾任务
Agent 回顾任务 SHALL 按任务模板执行：读事件历史→查市场数据→评价预测→写 responses/{date}.md。

#### Scenario: 回顾写入文件
- **WHEN** Agent 完成事件回顾
- **THEN** 在 `data/events/{event_id}/responses/{YYYY-MM-DD}.md` 写入回顾内容（markdown 格式）

#### Scenario: 同日重复回顾
- **WHEN** 同一天对同一事件再次触发回顾
- **THEN** 覆盖已有的 responses/{date}.md 文件

### Requirement: 回顾配置
系统 SHALL 从 `runtime/config/event-review.yaml` 读取回顾配置。

#### Scenario: 读取配置
- **WHEN** 系统启动回顾调度
- **THEN** 从 `runtime/config/event-review.yaml` 读取 enabled、schedule_time、concurrency 等配置

#### Scenario: 配置缺失
- **WHEN** 配置文件不存在
- **THEN** 使用默认值（enabled=true, schedule_time="08:00", concurrency=1）

### Requirement: 回顾任务模板
系统 SHALL 提供任务模板 `skills/news_driven_investment/tasks/event-reviews.md`，定义 Agent 回顾流程。

#### Scenario: 模板内容
- **WHEN** Agent 收到回顾任务
- **THEN** 按模板执行：读取事件信息、关联新闻的 prediction.md、已有 responses/、查市场数据、评价预测、写入 responses/{date}.md
