# news-skill-guide

SKILL.md 的结构和内容规范，确保 Agent 能快速理解 skill 能力并正确使用。

## Purpose

定义 SKILL.md 的必要内容和组织方式，使 Agent 无需猜测即可了解可用工具、使用原则和典型场景。

## Requirements

### Requirement: SKILL.md 包含完整 CLI 工具清单

SKILL.md SHALL 按用途分类列出全部 CLI 命令，每个命令包含一句话说明和使用时机。详细参数 SHALL 引用 `references/cli-reference.md`。输出中包含 `news_dir` 的命令 SHALL 说明该字段的用途（数据目录绝对路径，用于写入 report.md 等）。

#### Scenario: Agent 查看 SKILL.md 了解可用工具
- **WHEN** Agent 加载新闻分析 skill
- **THEN** SKILL.md 中列出所有可用 CLI 命令，按用途分类（获取/写入/搜索/查看），Agent 可快速了解工具能力

#### Scenario: Agent 需要查看命令详细参数
- **WHEN** Agent 需要了解某个 CLI 命令的完整参数和示例
- **THEN** Agent 可查阅 `references/cli-reference.md` 获取详细信息

### Requirement: SKILL.md 说明写入闭环原则

SKILL.md SHALL 包含"分析即写入"原则的说明：每次分析后通过 CLI 写入数据（summary → embedding + Milvus，analysis → entities），使后续分析可检索历史上下文。

#### Scenario: Agent 理解为什么需要写入
- **WHEN** Agent 阅读分析原则
- **THEN** 能理解"分析不写入 = 孤立分析，分析+写入 = 知识积累"的闭环逻辑

### Requirement: SKILL.md 包含场景指引（仅方向，不含步骤）

SKILL.md SHALL 包含使用场景的方向性指引：快速分析（参考任务模板）、手动分析（fetch → 分析 → 写入）、追踪线索（搜索历史）。每个场景只指引方向和入口工具，不包含具体操作步骤。

#### Scenario: Agent 收到快速分析请求
- **WHEN** Agent 需要执行快速分析
- **THEN** SKILL.md 指引参考 `tasks/quick-news-analysis.md`，具体步骤由任务模板定义

#### Scenario: Agent 手动分析新闻
- **WHEN** 用户请求分析某条新闻
- **THEN** SKILL.md 指引用 fetch-news 或 get-news 获取数据，然后用 update-news 写入结果

### Requirement: CLI 参考文档独立维护

`references/cli-reference.md` SHALL 包含所有 CLI 命令的完整参数说明、输出格式（含新增的 news_dir 字段）和使用示例。

#### Scenario: Agent 查阅 CLI 参考文档
- **WHEN** Agent 需要了解命令的参数格式
- **THEN** cli-reference.md 提供完整的参数列表、JSON 输出格式和调用示例

### Requirement: 任务模板只定义产出要求

`tasks/quick-news-analysis.md` SHALL 只包含产出清单（summary、analysis、report.md）、分析要求和分析原则。不包含参数占位符、CLI 用法、运行目录、数据获取方式。

#### Scenario: Backend cron 触发分析
- **WHEN** Backend 通过 build_message 注入 news_id、news_dir、content 等参数
- **THEN** Agent 从注入参数获取数据，按任务模板的产出要求执行分析

#### Scenario: Agent 主动使用 skill 分析
- **WHEN** Agent 自己触发分析
- **THEN** Agent 通过 fetch-news 或 get-news 获取 news_id、news_dir、content，然后按任务模板的产出要求执行分析

### Requirement: 全局统一术语 news_dir

代码变量名、CLI 输出字段、文档中 SHALL 统一使用 `news_dir` 表示新闻数据目录。`task_dir`、`DATA_DIR`、`data_dir` SHALL NOT 使用。

#### Scenario: Backend build_message 注入参数
- **WHEN** Backend 构造分析消息
- **THEN** 使用 `news_dir` 字段名（非 DATA_DIR 或 task_dir）

#### Scenario: CLI 输出包含数据目录
- **WHEN** fetch-news 或 get-news 输出包含数据目录
- **THEN** 字段名为 `news_dir`
