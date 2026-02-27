# 项目开发指南

你需要按照以下描述进行本项目的开发。

## 项目说明

@docs/project-overview.md

## 开发规范

@docs/standards/development-standard.md

## 文档规范

@docs/standards/documentation-standard.md

## 开发流程规范

### 需求开发流程

1. 当启动一个新的需求修改时，先切换到发开分支。
2. 使用 opsx 草拟方案，并在后续过程按 opsx 规范进行。opsx 相关命令必须在项目根目录下运行。
3. 在设计阶段：
   - 按最少地满足需求的功能点来设计，不要过度设计
   - 使用 context7 了解相关库的能力，特别是以下你不熟悉的代码库：
     - AgentScope
   - 设计阶段需要考虑测试过程产生脏数据和清理方案
3. 在开发阶段：
   3.1. 代码开发
   3.2. 代码的单元测试，使用全 mock 的方式
   3.3. 进行详细的代码 Review
4. 开发测试完成后，使用 `opsx:verify` 进行验证
5. 验证通过后，使用 `opsx:archive` 进行归档（禁止使用 `--no-validate`）
6. 提交到 Github 并创建 PR

### 归档规范

- 禁止使用移动文件夹或者复制文件夹的方式进行归档
- 禁止使用 `--skip-specs`

## 参考命令

### Python

#### 依赖管理
```bash
uv sync --group dev                              # 安装所有依赖（包括开发依赖）
uv sync                                         # 仅安装生产依赖
uv add <package>                                 # 添加新依赖
```

#### 测试
```bash
# 运行测试
uv run --env-file .env pytest tests/                    # 运行所有测试
uv run --env-file .env pytest tests/ -v                 # 详细输出
uv run --env-file .env pytest tests/openclaw_alpha/     # 运行特定模块
uv run --env-file .env pytest tests/ -k "test_xxx"      # 筛选测试（匹配关键词）

# 查看测试覆盖率（如果配置了）
uv run --env-file .env pytest tests/ --cov
```

#### 代码质量
```bash
uv run ruff check src/ tests/               # 代码检查（仅检查不修复）
uv run ruff check --fix src/ tests/         # 代码检查并自动修复
uv run ruff format src/ tests/              # 代码格式化
```

## 工具说明

- opsx - 保持使用 opsx 工具，按 spec-driven 的方式进行开发
- context7 - 积极使用 context7 工具搜索使用文档。例如，设计时需要了解依赖库的能力、开发测试时遇到调用方法不存在、参数个数不一致、参数类型不一致等场景
- tushare-docs-mcp - 对于 tushare 库，使用 tushare-docs-mcp 工具进行搜索文档，而不是 context7
- Bash:
  - 需要临时运行服务时，使用 Bash 工具原生的后台运行能力，而不是在命令中增加 `nohup` 或者后缀 `&` 的方式运行
  - 禁止调用 Bash 时传入多行命令，如果需要，先在临时文件夹生成复杂脚本，再运行
  - 运行 openspec 命令时，必须在项目根目录下
- agent team - 启动 agent team 时，leader 需要同步更新 opsx 状态

## OpenClaw说明

@docs/standards/openclaw-standard.md

