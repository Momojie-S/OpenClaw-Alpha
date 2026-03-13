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
├── skills/                         # SKILL 文档目录（只放 SKILL.md 和 docs）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引（对外）
│       └── docs/                   # 开发文档（对内）
│           ├── spec.md             # 需求文档
│           ├── design.md           # 设计文档
│           └── decisions.md        # 调研/决策记录
│
├── src/openclaw_alpha/
│   ├── core/                       # 框架核心（Fetcher, FetchMethod 等）
│   ├── data_sources/               # 数据源实现（Tushare, AKShare）
│   ├── openclaw/                   # 🔧 OpenClaw 框架工具（路径、cron 等）
│   │   ├── __init__.py
│   │   ├── path_utils.py           # OpenClaw 路径工具
│   │   └── cron_utils.py           # OpenClaw cron 工具
│   └── skills/                     # Skill 代码目录
│       └── {skill_name}/
│           ├── __init__.py
│           ├── {data_type}_fetcher/
│           │   ├── __init__.py
│           │   ├── {data_type}_fetcher.py
│           │   ├── tushare.py
│           │   └── akshare.py
│           └── {scenario}_processor/
│               ├── __init__.py
│               └── {scenario}_processor.py
│
├── docs/                           # 项目文档
│   ├── architecture/               # 架构设计
│   │   ├── core-utilities.md       # 核心工具模块（路径管理等）
│   │   ├── strategy-framework.md   # 策略框架设计
│   │   └── ...
│   ├── knowledge/                  # 投资知识体系（理论底座）
│   ├── openclaw/                   # 🔧 OpenClaw 高级用法调研（见下方说明）
│   ├── references/                 # API 参考文档
│   │   ├── akshare/
│   │   ├── rsshub/
│   │   └── tushare/
│   ├── research/                   # 调研文档
│   ├── skills/                     # 投资分析框架（实践方法）
│   └── standards/                  # 开发规范
│
├── tests/                          # 测试
│   └── skills/{skill_name}/
│
├── pyproject.toml                  # 包配置
└── .env                            # 环境变量配置
```

**分离关注点**：
- `skills/{skill_name}/` - 只放文档（SKILL.md + docs/）
- `src/openclaw_alpha/skills/{skill_name}/` - 放代码（fetcher + processor）
- `src/openclaw_alpha/` - 通过 pyproject.toml 注册为包，所有代码统一导入

**知识 vs 框架**：
- `docs/knowledge/` - 投资知识体系，理论底座（概念、定义、公式）
- `docs/skills/` - 投资分析框架，实践方法（流程、决策逻辑）

**OpenClaw 高级用法**：
- `docs/openclaw/` - OpenClaw 框架高级用法的调研结果
- 包含 cron、sessions 等功能的深入研究和使用技巧
- 用于指导项目中使用 OpenClaw 框架的最佳实践

## 核心概念

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
- 不要手动设置 `PYTHONPATH`，使用 `.env` 来加载
