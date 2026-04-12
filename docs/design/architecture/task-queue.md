# Task Queue - 设计方案

## 架构

```
┌──────────────────────────────────────────────────┐
│  APScheduler (纯触发器)                           │
│                                                  │
│  到时间 → task_queue.enqueue(type) ──┐           │
│                                      ▼           │
│  API 手动触发 ─────────────▶ asyncio.PriorityQueue│
│                         （手动触发不走队列）  │    │
│                                      │           │
│                         Worker coroutine          │
│                         await queue.get()         │
│                                      │           │
│                          ┌───────────▼─────────┐ │
│                          │ registry[type].fn()  │ │
│                          │ 失败 → 丢弃，打日志   │ │
│                          │ 从 persistence 移除   │ │
│                          └──────────────────────┘ │
└──────────────────────────────────────────────────┘

persistence: runtime/task_queue.json
```

## 核心组件

### 1. TaskQueue

位置：`backend/task_queue.py`

```python
class TaskQueue:
    """统一任务队列，单并发约束"""

    def __init__(self, config: TaskQueueConfig, registry: TaskRegistry, runtime_dir: Path)
    async def start()     # 启动 worker + 从 persistence 恢复
    async def stop()      # 优雅停止 worker
    async def enqueue(task_type: str) -> bool  # 入队（去重）
```

**入队流程**：
1. 内存去重集合检查，同 type 已存在 → 返回 False
2. 从 registry 获取优先级
3. 写入 persistence + 放入 PriorityQueue

**去重依据**：仅按 `task_type` 去重。定时任务入口无参数。

**Worker 执行流程**：
1. `await queue.get()`
2. 从 registry 获取执行函数
3. 执行函数（失败则 log error，不重试）
4. 从 persistence 移除该任务

**启动恢复**：读取 persistence 文件，按优先级重新入队。

### 2. TaskRegistry

位置：`backend/task_queue.py`（同文件）

```python
class TaskRegistry:
    def register(task_type, fn, priority)  # 注册任务类型
    def get(task_type) -> (fn, priority)   # 获取执行函数和优先级
```

优先级在代码注册时指定，不可配置。

### 3. 配置

```python
class TaskQueueConfig(BaseModel):
    enabled: bool = True
    persistence_path: str = "task_queue.json"  # 相对 runtime dir
```

### 4. Persistence 文件格式

`runtime/task_queue.json`：

```json
[
  {
    "type": "news_fetch",
    "priority": 2,
    "enqueued_at": "2026-04-10T20:30:00+08:00"
  }
]
```

## 任务注册表

所有注册到任务队列的任务类型、优先级和所属模块：

| task_type | 优先级 | 所属模块 | 模块文档 | 说明 |
|-----------|--------|---------|---------|------|
| `deep_analysis` | 3 (最高) | quick_news | [news/overview.md](news/overview.md) | 深度分析，定时扫描需深入的事件 |
| `news_fetch` | 2 | quick_news | [news/overview.md](news/overview.md) | 快速分析（拉取 + 分析） |
| `event_review` | 1 | quick_news | [news/event-tracking.md](news/event-tracking.md) | 事件回顾 |
| `iteration_loop` | 3 | iteration_loop | [iteration-loop/overview.md](iteration-loop/overview.md) | 迭代循环 |

优先级数字越大越优先。单并发 worker 按优先级顺序执行。

## 任务注册方式

各模块调用 `register_*_tasks(registry, scheduler)`：

```python
# main.py lifespan 中
registry = TaskRegistry()
task_queue = TaskQueue(config.task_queue, registry, runtime_dir)

# 注册任务（入口函数无参数，内部固定参数）
registry.register("deep_analysis", deep_analysis_entry, priority=3)
registry.register("news_fetch", news_fetch_entry, priority=2)
registry.register("event_review", event_review_entry, priority=1)
registry.register("iteration_loop", iteration_loop_entry, priority=3)

# 注册调度触发（APScheduler 只触发入队）
scheduler.add_interval_job(
    lambda: asyncio.create_task(_enqueue_safe("news_fetch")),
    job_id="trigger-news-fetch",
    minutes=30,
)
```

## 任务执行函数签名

所有注册到队列的执行函数统一签名：

```python
async def execute() -> None:
    """无参数，内部自行决定 limit 等参数"""
```

## API 手动触发

现有 API endpoint 保持不变，直接调用执行函数，**不经过队列**。手动触发用于调试。

## 失败处理

- 执行失败：log error，从 persistence 移除，丢弃
- 不重试，不回队列

## 文件结构

```
backend/
├── task_queue.py          # TaskQueue + TaskRegistry + _global_queue
├── scheduler.py           # 不变：只做时间触发
├── config.py              # 新增 TaskQueueConfig
├── main.py                # 改造：lifespan 中启动 queue + 注册
├── quick_news/jobs.py     # 改造：register_quick_news_tasks()
└── iteration_loop/jobs.py # 改造：register_iteration_tasks()
```
