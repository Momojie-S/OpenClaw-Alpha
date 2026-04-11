# unified-config

## Purpose

统一配置管理，合并 .env 凭据和 config.json 功能/调度配置，提供单一 Settings 入口。

## Requirements，合并 .env 凭据和 config.json 功能/调度配置，提供单一 Settings 入口。
## Requirements
### Requirement: 统一配置入口
系统 SHALL 提供 `Settings` 单例类，从 `.env` 读取凭据、从 `runtime/config.json` 读取功能配置，作为唯一配置访问入口。

#### Scenario: 正常加载配置
- **WHEN** 创建 `settings` 实例且 `.env` 和 `config.json` 都存在
- **THEN** 所有配置项均可通过属性访问

#### Scenario: 必填凭据缺失
- **WHEN** `.env` 中缺少必填凭据（如 TUSHARE_TOKEN）
- **THEN** 首次访问该属性时抛出 `ValueError`，提示具体缺失项

#### Scenario: config.json 不存在
- **WHEN** `runtime/config.json` 不存在
- **THEN** 抛出 `FileNotFoundError`

### Requirement: 凭据属性
`Settings` SHALL 提供以下凭据属性，值来自 `.env`：

- `tushare_token`: str（必填）
- `tushare_credit`: int（默认 0）
- `dashscope_api_key`: str（必填）
- `milvus_uri`: str（必填）
- `milvus_token`: str（必填）

#### Scenario: 读取凭据
- **WHEN** 访问 `settings.tushare_token`
- **THEN** 返回 `.env` 中 `TUSHARE_TOKEN` 的值

#### Scenario: 凭据带默认值
- **WHEN** `.env` 中未设置 `TUSHARE_CREDIT`
- **THEN** `settings.tushare_credit` 返回 0

### Requirement: 功能配置属性
`Settings` SHALL 提供各模块的功能配置属性，值来自 `config.json`。模块配置中 `agent_id`、`model`、`delivery` 三个字段可选，缺失时从顶层 `defaults` 继承。

模块配置：
- `quick_news`: dict
- `feedback`: dict
- `event_review`: dict

公共默认值（`defaults`）：
- `agent_id`: str（可选）
- `model`: str（可选）
- `delivery`: dict（可选）

#### Scenario: 读取模块配置
- **WHEN** 访问 `settings.quick_news`
- **THEN** 返回合并后的配置字典，其中 `agent_id`/`model`/`delivery` 优先使用模块自身值，缺失时使用 `defaults` 中的值

#### Scenario: 模块覆盖默认值
- **WHEN** `feedback` 配置了 `agent_id: "alpha"`，`defaults.agent_id` 为 `"main"`
- **THEN** `settings.feedback["agent_id"]` 返回 `"alpha"`

#### Scenario: 模块使用默认值
- **WHEN** `quick_news` 未配置 `agent_id`，`defaults.agent_id` 为 `"main"`
- **THEN** `settings.quick_news["agent_id"]` 返回 `"main"`

#### Scenario: 无 defaults 配置
- **WHEN** `config.json` 中无 `defaults` 字段
- **THEN** 模块配置保持原样，不做合并

### Requirement: 路径兼容
`Settings` SHALL 支持 `OPENCLAW_ALPHA_ROOT` 环境变量覆盖项目根目录。

#### Scenario: 设置了环境变量
- **WHEN** `OPENCLAW_ALPHA_ROOT` 已设置
- **THEN** `settings.project_root` 返回该路径

#### Scenario: 未设置环境变量
- **WHEN** `OPENCLAW_ALPHA_ROOT` 未设置
- **THEN** `settings.project_root` 从包路径推断

