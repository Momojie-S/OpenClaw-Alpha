# 文档编写规范

## 核心原则

- **简洁优先** - 每句话都要有价值，避免冗余
- **设计导向** - 说明"是什么"和"为什么"，避免实现细节
- **无代码示例** - 代码在仓库里，不粘贴到文档
- **无版本号时间戳** - 通过 git 查看变更历史
- **概念清晰** - 用自然语言描述，避免让读者猜测

---

## 目录组织

```
docs/
├── architecture/           # 架构设计
│   ├── strategy-framework.md
│   └── signal-backtest-framework.md
├── knowledge/              # 投资知识体系（Obsidian 风格）
│   ├── README.md           # Map of Content
│   ├── fundamentals/       # 基础概念
│   ├── analysis/           # 分析方法
│   ├── strategy/           # 投资策略
│   └── risks/              # 风险管理
├── skills/                 # 投资分析框架
│   ├── analysis-framework.md
│   └── daily-analysis-guide.md
├── references/             # API 参考
│   ├── tushare/
│   ├── akshare/
│   └── rsshub/
├── standards/              # 开发规范
│   ├── development-standard.md
│   ├── skill-implementation-standard.md
│   ├── fetcher-implementation-standard.md
│   ├── processor-implementation-standard.md
│   ├── spec-standard.md
│   ├── design-standard.md
│   ├── api-doc-standard.md
│   └── documentation-standard.md
└── project-overview.md     # 项目概述
```

**注意**：skill 的开发文档放在 `skills/{skill_name}/docs/` 下，不在 `docs/skills/`。

---

## Skill 文档结构

**自包含原则**：skill 的所有文档都在 skill 目录下

```
skills/{skill_name}/
├── SKILL.md                # 使用说明（对外，给用户看）
└── docs/                   # 开发文档（对内，开发者看）
    ├── spec.md             # 需求文档
    ├── design.md           # 设计文档
    └── decisions.md        # 关键决策/调研记录
```

### 各文档职责

| 文档 | 读者 | 内容 | 规范 |
|------|------|------|------|
| SKILL.md | 用户 | 如何使用、分析步骤 | - |
| spec.md | 开发者 | 需求、业务规则、验收标准 | [spec-standard.md](spec-standard.md) |
| design.md | 开发者 | 技术方案、接口契约 | [design-standard.md](design-standard.md) |
| decisions.md | 开发者 | 调研记录、关键决策、踩坑经验 | - |

### decisions.md 格式

记录开发过程中的调研、决策、经验教训：

```markdown
# 开发决策记录

## 调研

### 数据源选择
- Tushare: 支持接口 A、B，需要 120 积分
- AKShare: 支持接口 A，免费但不稳定
- 决策：Tushare 优先，AKShare 备用

### API 对比
| 接口 | Tushare | AKShare |
|------|---------|---------|
| 每日行情 | ✅ `daily()` | ✅ `stock_zh_a_hist()` |
| 分钟线 | ✅ `pro_bar()` | ❌ |

## 决策

### 为什么用 name 关联而非 code
- 不同数据源 code 格式不同（000001.SZ vs 000001）
- name 跨数据源更稳定
- 代价：重名股票需特殊处理

### 为什么分离 Fetcher 和 Processor
- Fetcher 只负责获取，不加工
- Processor 负责加工和输出
- 好处：Fetcher 可复用，Processor 可测试

## 踩坑

### Tushare 积分不足
- 现象：接口返回空数据
- 原因：积分不够，接口不可用
- 解决：检查 `required_credit`，提前校验

### AKShare 日期格式
- 现象：`stock_zh_a_hist()` 返回日期是字符串
- 原因：AKShare 不自动转日期
- 解决：使用 `pd.to_datetime()` 转换
```

---

## 开发流程

### 新建 Skill

1. **创建目录结构**
   ```
   skills/{skill_name}/
   ├── SKILL.md
   ├── docs/
   │   ├── spec.md
   │   └── design.md
   └── scripts/
   ```

2. **编写 spec.md**（业务视角）
   - 解决什么问题
   - 业务规则
   - 验收标准

3. **编写 design.md**（技术视角）
   - 数据源选择
   - 接口设计
   - 模块划分

4. **开发代码**

5. **编写 SKILL.md**（用户视角）
   - 如何使用
   - 分析步骤

6. **记录 decisions.md**
   - 调研结果
   - 关键决策
   - 踩坑经验

### 文档维护

- **spec/design**：开发完成后保留，作为历史记录
- **SKILL.md**：持续更新，反映当前功能
- **decisions.md**：随时记录，积累经验

---

## 文档规范引用

| 文档类型 | 规范文件 |
|---------|---------|
| 需求文档 | [spec-standard.md](spec-standard.md) |
| 设计文档 | [design-standard.md](design-standard.md) |
| API 文档 | [api-doc-standard.md](api-doc-standard.md) |
| 知识体系 | 见下方规范 |

---

## 知识体系文档规范

`docs/knowledge/` 下的文档采用 **Obsidian 风格**，便于在 Obsidian 中阅读和导航。

**⚠️ 核心原则：知识体系独立于项目，只记录通用的理论知识，不包含项目特定的实现细节。**

### 知识体系 vs 项目文档

| 内容 | 归属 |
|------|------|
| 概念定义、公式、原理 | ✅ 知识体系 |
| 通用分析方法、策略理论 | ✅ 知识体系 |
| 项目特定的实现规范、接口格式 | ❌ 项目文档（standards/） |
| OpenClaw-Alpha 的信号输出格式 | ❌ processor-implementation-standard.md |

### Frontmatter

```yaml
---
tags:
  - 投资/知识体系
  - 投资/知识体系/子分类
aliases:
  - 别名1
  - 别名2
---
```

### 内容结构

```markdown
# 概念名称

## 定义
<!-- 一句话定义 -->

## 公式
<!-- 计算公式（如有） -->

## 应用场景
<!-- 什么时候用，怎么用 -->

## 注意事项
<!-- 陷阱、局限性 -->

## 相关概念
- [[相关概念1]]
- [[相关概念2]]
```

### 编写原则

1. **客观准确** - 只记录公认的理论知识
2. **结构清晰** - 概念 → 公式 → 应用场景
3. **简明扼要** - 不冗余，可快速查阅
4. **双向链接** - 关联概念用 `[[wikilinks]]`，不用 Markdown 链接

### 层级关系

```
README.md（Map of Content）
    ↓ 包含
子目录笔记（如 fundamentals/）
    ↓ 包含
具体概念（如 估值指标.md）
    ↓ 链接
相关概念（[[财务指标]]）
```

### 示例

`fundamentals/估值指标.md`:

```markdown
---
tags:
  - 投资/知识体系
  - 投资/知识体系/基础概念
aliases:
  - 估值
---

# 估值指标

## 定义
评估股票价格是否合理的指标体系。

## 常见指标
- [[PE]] - 市盈率
- [[PB]] - 市净率
- [[PS]] - 市销率
- [[PCF]] - 市现率

## 应用场景
- [[基本面分析]] - 评估投资价值
- [[行业轮动]] - 对比行业估值水平

## 注意事项
- 不同行业适用不同指标
- 需结合历史估值分位判断
```

---

## 命名规范

- 使用 kebab-case（如 `industry-trend.md`）
- 文件名应清晰反映内容
- 避免缩写和模糊名称

---

## 文档维护

- 保持文档与代码同步
- 定期审查过时内容
- 移除不再适用的文档
