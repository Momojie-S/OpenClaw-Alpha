# 项目概述

## 项目概述

OpenClaw-Alpha 是一个股票金融数据获取和分析的 Python 技能模块，为 OpenClaw 智能体提供多个分析能力 skill。

## 技术栈

- **包管理**: uv
- **语言**: Python
- **数据源**: AKShare, Tushare

## 目录结构

```text
OpenClaw-Alpha/
├── SKILL.md                    # 主入口（汇总说明）
├── skills/                     # 子 skill 目录
│   ├── industry-trend/         # 产业趋势分析
│   │   └── SKILL.md
│   └── stock-quote/            # 股票行情查询
│       └── SKILL.md
├── src/openclaw_alpha/         # Python 代码
│   ├── core/                   # 核心框架（strategy, registry）
│   ├── strategies/             # 策略实现
│   └── data_sources/           # 数据源实现
├── docs/                       # 项目文档
└── .env                        # 环境变量配置
```

## Skill 架构

项目采用"主入口 + 子 skill"的架构：

- **主 SKILL.md**：作为汇总入口，描述项目整体能力
- **skills/ 目录**：每个子目录是一个独立的 skill，包含 SKILL.md（元数据 + 分析思路）
- **src/ 目录**：所有 Python 代码实现，被 skill 调用

OpenClaw 通过 `extraDirs` 配置加载 `skills/` 目录下的子 skill，实现精确触发。

## 环境说明

### 数据库环境
- 当前项目没有区分开发和生产数据库，所有环境共用同一个数据库实例
- 测试数据清理尤为重要，必须确保测试后正确清理，避免影响开发和使用体验

### 临时文件
- 无论是使用工具还是测试代码，需要创建临时文件时，都在项目根目录下的 `.temp` 文件夹下创建

### 环境变量设置
- 项目所需的环境变量都能在 `.env` 文件中找到
- 使用 `uv run` 命令时，必须使用 `--env-file .env` 参数来加载环境变量
- 不要手动设置 `PYTHONPATH`，使用 `.env` 来加载
