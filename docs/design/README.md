# 设计文档

技术架构、业务规则、算法设计、数据模型定义。

## 索引

### 架构 ([architecture/](architecture/))

| 文件 | 说明 |
|------|------|
| [setting.md](architecture/setting.md) | 统一配置管理（.env + config.json） |
| [core-utilities.md](architecture/core-utilities.md) | 核心工具（路径、信号处理） |
| [code-converter.md](architecture/code-converter.md) | 证券代码转换 |

### 后端服务 ([backend/](backend/))

| 文件 | 说明 |
|------|------|
| [backend.md](backend/backend.md) | 后端服务架构（调度、定时任务） |
| [task-queue.md](backend/task-queue.md) | 任务队列（优先级调度、去重） |

### 回测框架 ([backtest/](backtest/))

| 文件 | 说明 |
|------|------|
| [strategy-framework.md](backtest/strategy-framework.md) | 策略框架 |
| [signal-backtest-framework.md](backtest/signal-backtest-framework.md) | 信号回测框架 |

### 新闻系统 ([news/](news/))

| 文件 | 说明 |
|------|------|
| [overview.md](news/overview.md) | 新闻系统总览 |
| [news-fetcher.md](news/news-fetcher.md) | 新闻数据获取 |
| [news-storage.md](news/news-storage.md) | 新闻存储 |
| [news-cli.md](news/news-cli.md) | CLI 工具 |
| [event-tracking.md](news/event-tracking.md) | 事件跟踪系统 |
| [quick-analysis.md](news/quick-analysis.md) | 快速分析 |
| [deep-analysis.md](news/deep-analysis.md) | 深度分析 |

### 迭代循环 ([iteration-loop/](iteration-loop/))

| 文件 | 说明 |
|------|------|
| [overview.md](iteration-loop/overview.md) | 迭代循环总览 |
| [dev-tasks.md](iteration-loop/dev-tasks.md) | 开发任务调度 |
| [feedback.md](iteration-loop/feedback.md) | 用户反馈处理 |

### Skill 设计文档 ([skills/](skills/))

各 skill 的 spec / design / decisions 文档，按 skill 名组织。
