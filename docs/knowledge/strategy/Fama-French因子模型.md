---
tags:
  - 投资/知识体系
  - 投资/知识体系/投资策略
aliases:
  - FF3
  - FF5
  - 法玛-弗兰奇模型
---

# Fama-French 因子模型

## 定义

由 Eugene Fama 和 Kenneth French 提出的资产定价模型，从 CAPM 的单因子扩展到多因子，更好地解释股票收益差异。

---

## 模型演进

| 模型 | 年份 | 因子数 | 因子列表 |
|------|------|--------|----------|
| CAPM | 1964 | 1 | 市场风险溢价 |
| FF 三因子 | 1992 | 3 | + 规模、价值 |
| FF 五因子 | 2014 | 5 | + 盈利、投资 |
| FF 六因子 | - | 6 | + 动量 |

---

## 三因子模型（FF3）

### 公式

$$R_i - R_f = \alpha + \beta_1(R_M - R_f) + \beta_2 \cdot SMB + \beta_3 \cdot HML + \epsilon$$

### 因子说明

| 因子 | 符号 | 名称 | 构造方法 |
|------|------|------|----------|
| 市场 | MKT | 市场风险溢价 | $R_M - R_f$ |
| 规模 | SMB | Small Minus Big | 小盘股收益 - 大盘股收益 |
| 价值 | HML | High Minus Low | 高 B/P 股票 - 低 B/P 股票 |

### 因子构造（2×3 分组）

1. 按市值分 2 组：Small (S) / Big (B)
2. 按 B/P 分 3 组：High (H) / Medium (M) / Low (L)
3. 得到 6 个组合：SH/SM/SL/BH/BM/BL

**SMB 计算**：
$$SMB = \frac{1}{3}(Small\ High + Small\ Medium + Small\ Low) - \frac{1}{3}(Big\ High + Big\ Medium + Big\ Low)$$

**HML 计算**：
$$HML = \frac{1}{2}(Small\ High + Big\ High) - \frac{1}{2}(Small\ Low + Big\ Low)$$

### 核心发现

- **小盘效应**：小市值股票长期跑赢大市值
- **价值效应**：高 B/P（低估值）股票长期跑赢低 B/P
- 三因子可解释约 95% 的组合收益差异

---

## 五因子模型（FF5）

### 公式

$$R_i - R_f = \alpha + \beta_1(R_M - R_f) + \beta_2 \cdot SMB + \beta_3 \cdot HML + \beta_4 \cdot RMW + \beta_5 \cdot CMA + \epsilon$$

### 新增因子

| 因子 | 符号 | 名称 | 构造方法 |
|------|------|------|----------|
| 盈利 | RMW | Robust Minus Weak | 高盈利 - 低盈利 |
| 投资 | CMA | Conservative Minus Aggressive | 低投资 - 高投资 |

### RMW（盈利因子）

**定义**：高盈利能力公司的风险溢价

**盈利能力指标**：
- Operating Profitability (OP) = (Revenue - COGS - SG&A - Interest) / Book Equity

**分组**：
- Robust (R)：高 OP
- Weak (W)：低 OP

### CMA（投资因子）

**定义**：保守投资（低资本开支）公司的溢价

**投资指标**：
- Investment = $\frac{Assets_t - Assets_{t-1}}{Assets_{t-1}}$

**分组**：
- Conservative (C)：低投资增速
- Aggressive (A)：高投资增速

### 五因子构造（2×3×2×2）

在原 2×3（规模×价值）基础上，增加盈利和投资维度。

---

## 六因子模型（FF6）

在五因子基础上增加动量因子：

$$FF6 = FF5 + \beta_6 \cdot UMD$$

| 因子 | 符号 | 名称 | 构造方法 |
|------|------|------|----------|
| 动量 | UMD | Up Minus Down | 过去赢家 - 过去输家 |

---

## 模型对比

### 解释力

| 模型 | 解释力（R²） |
|------|-------------|
| CAPM | ~70% |
| FF3 | ~95% |
| FF5 | ~95-97% |

### 因子关系

| 关系 | 说明 |
|------|------|
| HML vs CMA | 高度相关（价值股通常投资保守） |
| SMB vs 其他 | 相对独立 |
| RMW vs HML | 部分替代关系 |

### A 股特点

| 因子 | A 股表现 |
|------|----------|
| MKT | 基础因子，稳定 |
| SMB | 小盘效应强，但波动大 |
| HML | 价值周期明显 |
| RMW | 逐步受重视 |
| CMA | 与价值因子高度相关 |
| UMD | 反转效应更强 |

---

## 应用场景

### 收益归因

分解组合超额收益来源：
$$\alpha = r_p - r_f - \sum \beta_i \cdot f_i$$

### 风险控制

识别组合的因子暴露，控制风格偏离。

### 基金评价

区分基金经理的"因子收益"和"选股 Alpha"。

### Smart Beta

设计因子暴露策略，如红利策略、低波策略。

---

## 局限性

| 局限 | 说明 |
|------|------|
| 因子时变 | 因子有效性会随市场环境变化 |
| 模型风险 | 模型假设可能与实际不符 |
| 数据窥探 | 因子可能是过拟合产物 |
| 交易成本 | 因子轮动带来换手成本 |

---

## 相关概念

- [[量化因子]] - 因子定义与计算
- [[多因子模型]] - Barra 因子体系
- [[因子有效性检验]] - IC/IR 检验
- [[因子轮动]] - 风格轮动策略
- [[组合管理]] - 因子配置应用
