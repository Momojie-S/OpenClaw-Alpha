# OpenClaw 说明

OpenClaw 是一种智能体（Agent），它可以加载多个 skill。

当前项目主要目的是为 OpenClaw 提供 skill，同时尽量兼容其他类型的智能体。

## Skills 扫描机制

OpenClaw 从以下位置加载 skills，按优先级从高到低：

| 位置 | 路径 | 优先级 |
|------|------|--------|
| 工作区 Skills | `<workspace>/skills` | 最高 |
| 托管/本地 Skills | `~/.openclaw/skills` | 中 |
| 内置 Skills | 随安装包发布 | 最低 |

### 扫描规则

OpenClaw **只扫描一层子目录**，不会递归扫描。例如：

```
<workspace>/skills/
├── skill-a/
│   └── SKILL.md          # ✅ 会被加载
├── skill-b/
│   └── SKILL.md          # ✅ 会被加载
└── skill-pack/
    ├── SKILL.md          # ✅ 会被加载（如果存在）
    └── sub-skill/
        └── SKILL.md      # ❌ 不会被扫描（嵌套太深）
```

### 在项目中提供多个 Skill

如果项目需要提供多个 skill，有两种方式：

**方式一：extraDirs 配置**

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "load": {
      "extraDirs": ["~/.openclaw/workspace/skills/OpenClaw-Alpha/skills"]
    }
  }
}
```

**方式二：扁平目录结构**

将多个 skill 平铺在 `<workspace>/skills/` 下：

```
<workspace>/skills/
└── openclaw-alpha/          # 项目容器目录
    ├── quote/
    │   └── SKILL.md
    ├── backtest/
    │   └── SKILL.md
    └── shared/              # 共享代码（无 SKILL.md）
```

### 优先级冲突

如果同名 skill 存在于多个位置，优先级为：

`工作区 > 托管/本地 > 内置`

## SKILL.md

每个 skill 必须包含一个 `SKILL.md` 文件，定义 skill 的元数据和使用说明。

### Frontmatter 要求

`SKILL.md` 必须以 YAML frontmatter 开头，至少包含 `name` 和 `description`：

```yaml
---
name: skill-name
description: 简短描述 skill 的功能，用于智能体判断何时触发
---
```

### 必填字段

| 字段 | 说明 |
|------|------|
| `name` | skill 唯一标识，小写，用连字符分隔 |
| `description` | 功能描述，智能体据此判断是否应该调用此 skill |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `homepage` | string | 在 macOS Skills UI 中显示的网站链接 |
| `user-invocable` | boolean | 是否作为用户斜杠命令暴露（默认 `true`） |
| `disable-model-invocation` | boolean | 是否从模型提示词中排除（默认 `false`） |
| `command-dispatch` | string | 设为 `tool` 时，斜杠命令直接调度到工具 |
| `command-tool` | string | `command-dispatch: tool` 时要调用的工具名称 |
| `command-arg-mode` | string | 参数模式，默认 `raw` |
| `metadata` | object | OpenClaw 特定配置（见下文） |

### metadata.openclaw 配置

`metadata` 的值是一个 JSON 对象，在 YAML frontmatter 中可以换行书写以提高可读性：

```yaml
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["uv"], "env": ["API_TOKEN"] },
        "primaryEnv": "API_TOKEN"
      }
  }
```

**注意：** OpenClaw 解析器只支持单行 frontmatter 键。`metadata` 可以换行，但其他字段（如 `name`、`description`）必须写在同一行。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `emoji` | string | macOS Skills UI 显示的 emoji |
| `homepage` | string | 覆盖顶层的 homepage |
| `skillKey` | string | 自定义配置键（默认使用 `name`） |
| `always` | boolean | 设为 `true` 跳过所有门控检查 |
| `os` | array | 支持的操作系统：`darwin`、`linux`、`win32` |
| `requires.bins` | array | 必须存在于 PATH 的二进制文件 |
| `requires.anyBins` | array | 至少一个必须存在于 PATH |
| `requires.env` | array | 必须存在的环境变量 |
| `requires.config` | array | `openclaw.json` 中必须为真的配置路径 |
| `primaryEnv` | string | 与 `apiKey` 关联的主环境变量名 |
| `install` | array | 安装器规格（brew/node/go/uv/download） |

### 门控机制

OpenClaw 在加载 skill 时会检查门控条件，**所有条件必须满足**才会加载：

1. `requires.bins` - 列表中的每个二进制文件必须在 PATH 中
2. `requires.env` - 列表中的每个环境变量必须存在，或在 `openclaw.json` 中配置
3. `requires.config` - 列表中的每个配置路径必须在 `openclaw.json` 中为真值
4. `os` - 如果设置，当前操作系统必须在列表中

**注意：** 如果 `always: true`，则跳过所有门控检查。
