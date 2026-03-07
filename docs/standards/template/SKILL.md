---
name: openclaw_alpha_<功能名>
description: "[功能概述]。适用于：(1) 场景A，(2) 场景B。不适用于：场景X、场景Y。"
metadata:
  openclaw:
    emoji: "📊"
---

# <功能名称>

## 使用说明

### 脚本运行

```bash
uv run --env-file {baseDir}/../.env --directory {baseDir}/.. python src/openclaw_alpha/<模块>/<脚本>.py [参数]
```

如遇到环境问题，参考 `openclaw_alpha_init` skill。

### 运行记录

使用本 skill 进行分析时，需要创建进度文件和结果文件，避免信息丢失。

#### 目录结构

```
{workspace}/.openclaw_alpha/
└── <SKILL名称>/
    └── YYYY-MM-DD/
        ├── progress.md    # 进度追踪
        ├── report.md      # 最终报告
        ├── *.json         # 中途数据保存 可多份
        └── *.md           # 中途信息保存 可多份
```

#### 进度追踪

- 根据分析所需要做的任务，填写 progress.md 的任务列表
- 某些任务需要前置步骤完成后才能确定 → 写"待 xx 完成后，再判断补充 yy 任务"
- 积极增加更新 report.md 的任务，尽量每做一步就更新一次
- 保持进度文件更新，这是你的记忆延续

#### progress.md 模板

```markdown
# 当前状态

- 当前阶段：Phase X
- 下一步：[具体动作]
- 阻塞：[如有阻塞说明]

# 任务列表

## Phase 1: [阶段名]
- [x] 已完成项 1
- [ ] 获取数据 xxx
- [ ] 分析 xxx → 更新 report.md
- [ ] 根据分析结果和本 skill 指示，判断生成 Phase 2 任务
```

## 分析步骤

### Step 1: [步骤名称]

**输入**：[需要什么数据/前置条件]

**动作**：
```bash
uv run --env-file {baseDir}/../.env --directory {baseDir}/.. python src/openclaw_alpha/<模块>/<脚本>.py [参数]
```

**输出**：[产生什么结果，保存到哪里]

---

### Step 2: [步骤名称]

...

---

（可选）继续深入分析：引用 `openclaw_alpha_<其他skill>` skill
