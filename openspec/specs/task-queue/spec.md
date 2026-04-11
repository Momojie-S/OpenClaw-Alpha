# Task Queue

## Purpose

统一任务队列，为后端服务提供优先级调度、单并发约束、持久化和去重能力。

## Requirements

### Requirement: Task queue enforces single concurrency
系统 SHALL 使用单 worker 协程消费 PriorityQueue，保证同一时刻只执行一个队列任务。

#### Scenario: 多个任务同时入队
- **WHEN** news_fetch、event_review、iteration_loop 三个任务同时入队
- **THEN** worker 按优先级顺序逐个执行，同一时刻只有一个任务在执行

### Requirement: Task registry for task type registration
系统 SHALL 提供 TaskRegistry，支持注册任务类型、执行函数和优先级。

#### Scenario: 注册任务
- **WHEN** 调用 `registry.register("news_fetch", fn, priority=2)`
- **THEN** 该任务类型可被队列识别和执行

### Requirement: Deduplication by task type
系统 SHALL 对同一 task_type 的任务去重，已存在同类型任务时拒绝入队。

#### Scenario: 重复入队
- **WHEN** news_fetch 已在队列中，再次 enqueue("news_fetch")
- **THEN** 返回 False，不重复入队

### Requirement: Persistence and recovery
系统 SHALL 将队列状态持久化到 `runtime/task_queue.json`，服务启动时从文件恢复未执行任务。

#### Scenario: 服务重启后恢复
- **WHEN** 服务重启，persistence 文件中有一条 news_fetch 任务
- **THEN** 该任务被重新入队并执行

#### Scenario: 任务执行完成后移除
- **WHEN** 任务执行完成（无论成功失败）
- **THEN** 从 persistence 文件中移除该任务

### Requirement: Scheduler triggers enqueue only
APScheduler SHALL 只负责时间触发，触发后调用 `task_queue.enqueue(type)` 入队，不直接执行任务函数。

#### Scenario: 定时触发入队
- **WHEN** APScheduler 触发 news_fetch 的 interval 任务
- **THEN** 调用 `task_queue.enqueue("news_fetch")`，任务进入队列

### Requirement: Task entry function signature
所有注册到队列的执行函数 SHALL 签名为 `async def execute() -> None`，内部自行决定参数。

#### Scenario: 执行函数无参数
- **WHEN** worker 取到 news_fetch 任务
- **THEN** 调用 `registry.get("news_fetch")` 获取的函数，无参数执行

### Requirement: No retry on failure
任务执行失败时 SHALL 记录日志并从队列移除，不重试。

#### Scenario: 任务执行失败
- **WHEN** 任务执行函数抛出异常
- **THEN** 记录 error 日志，从 persistence 移除，继续处理下一个任务

### Requirement: Manual trigger bypasses queue
API 手动触发 SHALL 直接调用执行函数，不经过任务队列。

#### Scenario: 手动触发新闻分析
- **WHEN** 调用 `/api/news/quick-analyse`
- **THEN** 直接执行分析函数，不走队列
