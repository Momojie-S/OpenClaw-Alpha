# 后端服务架构设计

## 概述

OpenClaw-Alpha 后端是一个长期运行的服务进程，负责定时任务调度和自动化分析流程。

**核心能力**：
- APScheduler 定时触发 → TaskQueue 优先级调度 → 单 worker 串行执行
- Gateway HTTP 客户端：提交 Agent session、发送通知
- 运行时配置 API：动态调整模块参数
- 持久化：任务队列断电恢复

## 技术栈

| 组件 | 选型 |
|------|------|
| Web 框架 | FastAPI |
| 调度器 | APScheduler (AsyncIOScheduler)，仅做触发 |
| 任务队列 | asyncio.PriorityQueue + 单 worker 协程 |
| 配置 | runtime/config.json（通过 core.settings 加载） |
| Gateway 通信 | HTTP 客户端（提交 session、发消息、管理 cron） |

## 目录结构

```
src/openclaw_alpha/backend/
├── main.py                    # FastAPI 入口 + lifespan（初始化调度器、队列、模块注册）
├── config.py                  # 服务配置（host/port/log_level/scheduler/task_queue）
├── config_api.py              # /api/config 路由（动态读取/更新 runtime/config.json）
├── scheduler.py               # APScheduler 封装（add_interval_job / add_daily_job）
├── task_queue.py              # TaskQueue + TaskRegistry（优先级调度、去重、持久化）
├── # 🗄️ Milvus 服务（按天轮转、模块独立日志）
│
├── quick_news/                # 新闻分析模块
│   ├── config.py              # 配置（间隔、模型、通知接收人）
│   ├── event_review_config.py # 事件回顾配置
│   ├── jobs.py                # 任务入口（注册 + 执行逻辑）
│   └── task_executor.py       # Agent session 提交
│
├── feedback/                  # 用户反馈模块
│   ├── config.py              # 配置
│   ├── jobs.py                # 反馈处理任务
│   ├── models.py              # 反馈数据模型
│   ├── submit_feedback.py     # 反馈提交
│   └── task_executor.py       # Agent session 提交
│
└── iteration_loop/            # 开发迭代循环模块
    ├── config.py              # 配置
    ├── jobs.py                # 迭代任务调度
    ├── dev_tasks/             # 开发任务管理
    └── feedback/              # 迭代反馈子模块
        ├── jobs.py
        └── __init__.py
```

## 启动流程

`main.py` lifespan 管理整个生命周期：

```
load_config → setup_logging
    → get_gateway_client（连接 Gateway）
    → Scheduler.start()
    → TaskQueue（创建 + 持久化恢复）
    → 注册各模块任务（register_xxx_tasks）
    → TaskQueue.start()（启动 worker 协程）
        ↓
    yield（服务运行中）
        ↓
    TaskQueue.stop → Scheduler.shutdown → close_gateway_client
```

## 任务调度架构

详见 [任务队列设计](task-queue.md)。

**核心流程**：

```
APScheduler 触发 → TaskRegistry.enqueue(type) → PriorityQueue → Worker 串行执行
```

- **Scheduler**：纯触发器，到时间就往队列塞任务
- **TaskQueue**：单 worker 协程串行执行，优先级调度 + 去重
- **TaskRegistry**：注册任务类型 → (执行函数, 优先级)
- **持久化**：JSON 文件，服务重启后自动恢复未执行任务

## 注册的任务

在 `main.py` 中按模块注册：

| 模块 | 注册函数 | 任务 |
|------|---------|------|
| quick_news | `register_quick_news_tasks()` | 新闻拉取+快速分析、深度分析、事件回顾 |
| iteration_loop | `register_iteration_tasks()` | 迭代循环周期执行 |

## 新闻分析流程

```
RSS 拉取 → 过滤已处理 → Agent 快速分析 → 高价值新闻关联事件 → 深度分析 → 通知
```

详见 [新闻系统设计](../news/overview.md)。

## 配置管理

### 服务配置

`config.py` 定义服务级别配置（host、port、log_level），从 `~/.openclaw_alpha/config/service.yaml` 加载。

### 运行时配置

各模块配置从 `runtime/config.json` 加载（通过 `core.settings`）：

```json
{
  "quick_news": {
    "enabled": true,
    "interval_minutes": 30,
    "deep_analysis_interval_minutes": 60,
    "delivery": {
      "recipients": [{"name": "Momojie", "channel": "wecom"}]
    }
  },
  "feedback": { "enabled": true, "interval_minutes": 60 },
  "iteration_loop": { "enabled": true, "interval_minutes": 120 }
}
```

### 配置 API

`config_api.py` 提供 REST API 动态读写 `runtime/config.json`：

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/config/iteration-loop` | GET/PUT | 迭代循环配置 |
| `/api/config/feedback` | GET/PUT | 反馈模块配置 |

## API 端点

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/news/quick-analyse` | POST | 手动触发快速新闻分析（`?limit=N`） |
| `/api/feedback/trigger` | POST | 手动触发反馈处理（`?limit=N`） |
| `/api/iteration/trigger` | POST | 手动触发迭代循环 |
| `/api/config/*` | GET/PUT | 配置管理 |

## Gateway 通信

通过 `openclaw_alpha.openclaw.gateway_client` 与 OpenClaw Gateway 交互：

- **提交 Agent session**：`task_executor.py` 提交分析任务到 Gateway
- **发送通知**：分析完成后通过 Gateway 发送消息给用户
- **管理 Cron**：定时任务的辅助管理

## 启动方式

```bash
uv run --env-file .env uvicorn openclaw_alpha.backend.main:app --reload --port 8765
```
