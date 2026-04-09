---
name: openclaw_alpha
description: "OpenClaw Alpha相关Skill的初始化说明，当前版本 0.0.1"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
      env: []
---

# 初始化说明

初次使用OpenClaw Alpha时，或者在版本升级时，进行以下初始化。

## 核心文件记录

在你的核心文件中，增加章节，用于记录OpenClaw-Alpha项目的说明。

你需要自行找到对应的项目根目录。

### 模板

```markdown

## OpenClaw Alpha 说明

- 项目根目录(绝对路径): xxx
- 版本号: x.x.x

### 使用说明

1. 如果当前版本号与OpenClaw Alpha初始化Skill的版本不一致，则检查进行重新初始化。
2. 相关Skill中描述的文件目录路径，如无特殊说明，都是在项目根目录下。
3. OpenClaw Alpha相关的py脚本，统一在项目根目录下运行。且统一使用 `uv run --env-file .env` 的方式加载环境变量运行。

### Backend服务

Backend服务可以使用以下命令启动 `uv run --env-file .env`，其提供能力包括:

1. 定时采集新闻，通过`cron job`触发额外的session来进行分析。

#### 相关配置:

- 新闻分析配置: {project_root}/runtime/quick_news/config.yaml

```

## 运行环境初始化

在项目根目录下运行 `uv sync`

## 环境变量配置

```bash
cd <project-root>
cp .env.sample .env
```

编辑 `.env`，填入以下值：

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `TUSHARE_TOKEN` | Tushare 接口 Token | [Tushare官网](https://tushare.pro/) 注册获取 |
| `TUSHARE_CREDIT` | Tushare 积分要求 | 根据接口需求设置，默认 5000 |
| `PYTHONPATH` | Python 模块搜索路径 | 已通过 pyproject.toml 配置，无需设置 |

## Backend配置

配置过程中，应该和用户咨询相关值是什么

### 新闻分析配置

**路径**：`runtime/quick_news/config.yaml`

**说明**：新闻快速分析的定时采集和推送配置

**配置项**：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `enabled` | 是否启用 | true |
| `interval_minutes` | 采集间隔（分钟） | 30 |
| `agent_id` | 分析 agent ID | main |
| `model` | 模型 | null（使用默认） |
| `delivery.recipients[]` | 接收人列表 | [{name: "Momojie"}] |
| `delivery.channel` | 推送渠道 | wecom |
| `cron.agent_turn_timeout_seconds` | Agent 超时（秒） | 900 |
| `cron.session_poll_timeout_seconds` | 轮询超时（秒） | 900 |
