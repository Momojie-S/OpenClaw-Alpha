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

- 功能配置: {project_root}/runtime/config.json

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

## 功能配置

```bash
cd <project-root>
cp runtime/config.json.example runtime/config.json
```

编辑 `runtime/config.json`。所有模块功能配置统一在此文件中，凭据（Token 等）请放在 `.env` 中。

### 配置结构

```json
{
  "defaults": {
    "agent_id": "main",          // 公共 agent ID
    "model": "...",               // 公共模型
    "delivery": { "recipients": [] }  // 公共推送配置
  },
  "quick_news": { ... },
  "feedback": { ... },
  "event_review": { ... },
  "iteration_loop": { ... }
}
```

### defaults（公共默认值）

模块未设置 `agent_id`/`model`/`delivery` 时，自动从 `defaults` 继承。

| 字段 | 说明 |
|------|------|
| `agent_id` | 执行 agent ID |
| `model` | 模型标识 |
| `delivery.recipients[]` | 推送接收人列表 |

### 模块配置

| 模块 | 说明 | 特有字段 |
|------|------|----------|
| `quick_news` | 新闻定时采集分析 | `enabled`, `interval_minutes`, `cron.*` |
| `feedback` | 用户反馈处理 | `enabled`, `feedback_new_dir`, `feedback_done_dir`, `cron.*` |
| `event_review` | 公告事件回顾 | `enabled`, `schedule_time`, `concurrency` |
| `iteration_loop` | 迭代循环 | `enabled`, `interval_minutes`, `dev_tasks.*` |
