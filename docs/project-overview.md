# 项目概述

OpenClaw-Alpha 是一个股票金融数据获取和分析的 Python 技能模块，为 OpenClaw 智能体提供投资分析能力。

## 交付与使用

**安装方式**：
1. Clone 到 OpenClaw agent 的 `workspace/skills/` 目录
2. 在 OpenClaw 配置中注册 `OpenClaw-Alpha/skills/` 目录
3. 主 SKILL.md 和子 skill 自动发现注册

**使用方式**：
- 大模型读取 SKILL.md 了解可用能力
- 根据分析需求，灵活调用 Processor 获取数据
- Processor 负责数据获取和加工，返回精简结果

## 目录结构

```
OpenClaw-Alpha/
├── skills/                         # SKILL 文档目录（只放 SKILL.md 和 tasks）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引（对外）
│       ├── tasks/                  # 任务模板（Agent session prompt）
│       └── docs/                   # 开发文档（对内）
│
├── src/openclaw_alpha/
│   ├── core/                       # 通用基础设施
│   │   ├── fetcher.py              # 数据获取框架
│   │   ├── data_source.py          # 数据源注册
│   │   ├── settings.py             # ⚙️ 统一配置管理（.env + config.json）
│   │   ├── registry.py             # 全局注册表
│   │   ├── code_converter/         # 证券代码转换
│   │   ├── milvus/                 # 🗄️ Milvus 向量数据库服务
│   │   ├── embedding/              # 🧮 向量生成服务（工厂模式）
│   │   └── ...
│   ├── data_sources/               # 数据源实现（Tushare, AKShare）
│   ├── openclaw/                   # 🔧 OpenClaw 框架工具
│   │   ├── gateway_client.py       # Gateway HTTP 客户端（发消息、cron）
│   │   ├── cron_utils.py           # Cron 任务管理
│   │   └── path_utils.py           # 路径工具
│   ├── rsshub/                     # RSSHub 数据获取
│   ├── news/                       # 📰 新闻模块（CLI + 服务层）
│   │   ├── cli.py                  # CLI 入口（fetch-news, update-news, debug-*）
│   │   ├── service.py              # 服务层（CRUD + 事件管理）
│   │   ├── store.py                # Milvus 存储
│   │   └── fetcher/                # 新闻数据获取（AKShare, RSSHub）
│   ├── backend/                    # 🚀 后端服务（定时任务、调度器）
│   │   ├── main.py                 # 服务入口
│   │   ├── scheduler.py            # APScheduler 调度器
│   │   ├── task_queue.py           # 任务队列（优先级调度）
│   │   ├── config.py               # 服务配置
│   │   ├── config_api.py           # 配置 API
│   │   ├── logger.py               # 日志配置
│   │   ├── quick_news/             # 新闻分析任务
│   │   │   ├── jobs.py             # 任务入口（快速分析 + 深度分析 + 事件回顾）
│   │   │   ├── task_executor.py    # Agent session 提交
│   │   │   └── config.py           # 配置（间隔、模型、通知接收人）
│   │   ├── feedback/               # 用户反馈处理
│   │   └── iteration_loop/         # 开发迭代循环
│   │       ├── jobs.py             # 开发任务调度
│   │       └── feedback/           # 反馈子模块
│   ├── skills/                     # Skill 代码目录
│   │   └── {skill_name}/
│   │       ├── {data_type}_fetcher/ # 数据获取（多数据源实现）
│   │       └── {scenario}_processor/ # 数据加工（大模型调用入口）
│   └── utils/                      # 通用工具
│       └── trading_calendar.py     # 交易日历
│
├── runtime/                        # 📁 运行时工作目录（git 忽略）
│   ├── config.json                 # ⚙️ 运行时配置
│   ├── data/                       # 新闻 & 事件数据
│   │   ├── news/{news_id}/         # 新闻详情 + 分析结果
│   │   └── events/{event_id}/      # 事件 + 深度分析报告
│   ├── processor_data/             # Processor 缓存输出
│   ├── logs/                       # 服务日志
│   └── feedback/                   # 反馈数据
│
├── openspec/                       # 📋 OpenSpec 规格管理
│
├── docs/                           # 项目文档
│   ├── design/                     # 设计文档
│   ├── skills/                  # 各 skill 的设计文档（spec/design/decisions）
│   │   ├── architecture/           # 技术架构
│   │   ├── news/                   # 新闻系统设计
│   │   └── iteration-loop/         # 迭代循环设计
│   ├── knowledge/                  # 投资知识体系
│   ├── skills/                     # 投资分析框架
│   ├── references/                 # API 参考
│   ├── research/                   # 调研文档
│   └── standards/                  # 开发规范
│
├── tests/                          # 测试
├── pyproject.toml                   # 包配置
└── .env                             # 环境变量配置
```

## 常用配置

| 配置项 | 文件路径 | 说明 |
|--------|----------|------|
| **统一配置** | `runtime/config.json` | 所有模块的功能参数、调度配置和服务部署配置 |
| **凭据** | `.env` | API Key、Token 等敏感配置（TUSHARE_TOKEN, DASHSCOPE_API_KEY, MILVUS_URI, MILVUS_TOKEN） |
| **路径覆盖** | `.env` | `OPENCLAW_ALPHA_ROOT` 覆盖项目根目录 |

> 详细说明见 [配置设计文档](docs/design/architecture/setting.md)

## 核心概念

### 后端服务

基于 OpenClaw Gateway 的定时任务系统，实现自动化任务调度。架构详见 [后端服务架构设计](docs/design/backend/backend.md)。

**新闻分析流程**：
```
RSS 拉取 → 过滤已处理 → Agent 快速分析 → 高价值新闻关联事件 → 深度分析 → 通知
```
- 快速分析：批量处理，筛选值得深挖的新闻
- 深度分析：以事件为单位，多维度交叉分析（板块趋势 + 资金流向 + 技术指标等）
- 分析完成后自动发送通知
详见 [新闻分析系统设计](docs/design/news/overview.md)。

**用户反馈处理流程**（Iteration Loop 子模块）：
```
用户提交反馈 → Backend 定时扫描 → 触发 Agent Session → 分析决策 → 通知结果 → 归档
```
详见 [Iteration Loop 设计](docs/design/iteration-loop/overview.md)。

### 事件跟踪系统

基于 Milvus 向量数据库的新闻事件跟踪，支持语义去重和关联。

```
新闻 → summary → embedding → Milvus(news_items collection) → 相似搜索
      → 本地文件系统(news/{news_id}/, events/{event_id}/)
```

详见 [事件追踪系统设计](docs/design/news/event-tracking.md)。

### Fetcher（数据获取）
- Fetcher（入口）：调度、选择可用的数据源实现
- FetchMethod（实现）：具体数据获取逻辑，绑定单一数据源
- 支持多数据源（Tushare、AKShare），按优先级自动选择

### Processor（数据加工）
- 大模型的调用入口
- 调用 Fetcher 获取全量数据，加工后返回精简结果
- 每个 Processor 定义自己的结构化参数

### SKILL.md（能力说明）
- 描述该 skill 能做什么
- 列出可用的 Processor 及其参数
- 提供分析思路指引（非固定流程）

## 技术栈

- **包管理**: uv
- **语言**: Python
- **数据源**: AKShare, Tushare
- **向量数据库**: Milvus 2.6
- **Embedding**: 百炼 DashScope text-embedding-v4

## 命令执行规范

本项目使用 **`uv run`** 执行所有 Python 命令，而非直接使用 `python`。

**原因**：
- `uv run` 自动在项目虚拟环境中执行
- 避免环境配置问题
- 确保依赖一致性

**命令格式**：
```bash
# 运行脚本（使用 -m 模块运行方式）
uv run --env-file .env python -m openclaw_alpha.skills.{skill_name}.{processor}.{processor}

# 运行测试
uv run --env-file .env pytest tests/{path}/test_xxx.py
```

**注意**：
- `--env-file .env` 用于加载环境变量
- 所有代码在 `src/openclaw_alpha/` 下，通过 pyproject.toml 注册为包
- 使用 `python -m` 模块运行方式，支持相对导入

## 环境说明

### 临时文件
- 无论是使用工具还是测试代码，需要创建临时文件时，都在项目根目录下的 `.temp` 文件夹下创建

### 环境变量设置
- 项目所需的环境变量都能在 `.env` 文件中找到
- 使用 `uv run` 命令时，必须使用 `--env-file .env` 参数来加载环境变量
