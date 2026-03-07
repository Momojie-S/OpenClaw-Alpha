# 财务健康评分增强研究

> 研究日期：2026-03-08
> 研究目的：增强 fundamental_analysis 的财务健康评分维度

---

## 现状分析

### 当前评分体系

| 维度 | 权重 | 评分依据 |
|------|------|----------|
| 估值 | 25% | PE/PB 评级 |
| 盈利能力 | 30% | ROE 评级 |
| 成长性 | 25% | 营收/利润增长评级 |
| 财务健康 | 20% | **仅资产负债率** |

### 问题

1. **财务健康维度过于简单** - 只用资产负债率
2. **流动比率、速动比率未参与评分** - 有数据但闲置
3. **每股现金流未参与评分** - 盈利质量指标

---

## 改进方案

### 新评分体系

财务健康维度拆分为 3 个子维度：

| 子维度 | 权重 | 指标 | 说明 |
|--------|------|------|------|
| 偿债能力 | 40% | 资产负债率 | 长期偿债能力 |
| 流动性 | 30% | 流动比率 | 短期偿债能力 |
| 盈利质量 | 30% | 每股经营现金流 | 现金流健康度 |

### 评级标准

#### 资产负债率（已有）

| 资产负债率 | 评级 | 分数 |
|-----------|------|------|
| < 40% | 健康 | 100 |
| 40-60% | 正常 | 70 |
| 60-70% | 关注 | 40 |
| > 70% | 风险 | 10 |

**注**：金融行业 >90% 为正常

#### 流动比率（新增）

| 流动比率 | 评级 | 分数 | 说明 |
|---------|------|------|------|
| > 2.0 | 优秀 | 100 | 流动性强 |
| 1.5-2.0 | 良好 | 80 | 流动性充足 |
| 1.0-1.5 | 一般 | 50 | 流动性一般 |
| < 1.0 | 风险 | 10 | 短期偿债压力 |

#### 每股经营现金流（新增）

| 每股现金流 | 评级 | 分数 | 说明 |
|-----------|------|------|------|
| > 0 且同比改善 | 优秀 | 100 | 现金流健康 |
| > 0 | 良好 | 70 | 现金流正常 |
| < 0 但改善中 | 一般 | 40 | 正在好转 |
| < 0 且恶化 | 风险 | 10 | 现金流紧张 |

**注**：由于缺少同比数据，简化为：
- > 0: 良好 (70)
- < 0: 风险 (10)
- None: 未知 (50)

---

## 实现方案

### 修改文件

1. `fundamental_processor.py` - 修改 `_rate_financial_health()` 和 `_calc_overall_score()`

### 代码改动

```python
def _rate_financial_health(
    debt_ratio: Optional[float],
    current_ratio: Optional[float],
    cash_per_share: Optional[float],
    name: str
) -> Dict:
    """财务健康综合评级
    
    包含三个子维度：
    - 偿债能力（资产负债率）
    - 流动性（流动比率）
    - 盈利质量（每股经营现金流）
    """
    # 子维度评分
    scores = {}
    
    # 偿债能力（40%）
    debt_score = _rate_debt_ratio_score(debt_ratio, name)
    scores["debt"] = debt_score
    
    # 流动性（30%）
    liquidity_score = _rate_current_ratio_score(current_ratio)
    scores["liquidity"] = liquidity_score
    
    # 盈利质量（30%）
    cash_score = _rate_cash_flow_score(cash_per_share)
    scores["cash_flow"] = cash_score
    
    # 加权计算
    weights = {"debt": 0.4, "liquidity": 0.3, "cash_flow": 0.3}
    total = sum(scores[k] * weights[k] for k in weights)
    
    # 综合评级
    if total >= 80:
        rating = "健康"
    elif total >= 60:
        rating = "正常"
    elif total >= 40:
        rating = "关注"
    else:
        rating = "风险"
    
    return {
        "rating": rating,
        "score": round(total, 1),
        "debt_score": debt_score,
        "liquidity_score": liquidity_score,
        "cash_flow_score": cash_score,
    }
```

---

## 评分体系调整

### 权重变化

| 维度 | 原权重 | 新权重 | 说明 |
|------|--------|--------|------|
| 估值 | 25% | 20% | 降低 5% |
| 盈利能力 | 30% | 30% | 不变 |
| 成长性 | 25% | 25% | 不变 |
| 财务健康 | 20% | **25%** | 提升 5% |

财务健康权重提升，因为：
1. 原来只用资产负债率，信息量不足
2. 增加流动性、现金流后，信息量更丰富
3. 与盈利能力、成长性重要性相当

---

## 收益

1. **更全面的财务健康评估** - 从单维度变为三维度
2. **利用已有数据** - 流动比率、速动比率、现金流已有数据
3. **更好的风险识别** - 能发现更多财务风险信号

---

## 参考

- Piotroski F-Score - 9 指标财务健康评分
- 杜邦分析 - ROE 分解
- Altman Z-Score - 破产预警模型
