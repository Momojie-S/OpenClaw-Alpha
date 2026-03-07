# 设计文档：行业景气度分析

> 版本: v1.0
> 创建时间: 2026-03-08

---

## 一、技术选型

### 数据源

**Tushare sw_daily** - 申万行业日线行情

**选择原因**：
- 直接提供行业 PE/PB 数据
- 无需聚合个股数据
- 数据稳定可靠

**积分要求**：5000

**输出字段**：
- ts_code：指数代码
- name：指数名称
- pe：市盈率
- pb：市净率
- pct_change：涨跌幅
- float_mv：流通市值
- total_mv：总市值

详见：[API 文档](../../references/api/tushare/sw_daily.md)

### 实现位置

**放在 industry_trend skill 中**，作为新的 processor。

**原因**：
- 和热度、拥挤度构成完整框架
- 复用行业分类逻辑
- 保持 skill 内聚性

---

## 二、架构设计

### 目录结构

```
industry_trend/
├── scripts/
│   ├── sector_valuation_fetcher/    # 新增：行业估值数据获取
│   │   ├── __init__.py
│   │   ├── sector_valuation_fetcher.py
│   │   └── tushare.py
│   └── prosperity_processor/        # 新增：景气度分析
│       ├── __init__.py
│       └── prosperity_processor.py
```

### 数据流

```
Tushare sw_daily
    ↓
SectorValuationFetcher
    ↓
ProsperityProcessor
    ├── 计算估值趋势
    ├── 计算景气度评分
    └── 输出结果
```

---

## 三、接口设计

### SectorValuationFetcher

**职责**：获取行业估值数据（PE/PB）

**输入参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | str | 否 | 查询日期（YYYY-MM-DD），默认当日 |
| category | str | 否 | L1（一级行业）/ concept（概念），默认 L1 |

**输出字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| code | str | 行业代码 |
| name | str | 行业名称 |
| pe | float | 市盈率 |
| pb | float | 市净率 |
| pct_change | float | 涨跌幅（%） |
| float_mv | float | 流通市值（万元） |
| total_mv | float | 总市值（万元） |
| trade_date | str | 交易日期 |

### ProsperityProcessor

**职责**：计算行业景气度评分

**命令行参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --date | str | 否 | 查询日期，默认当日 |
| --category | str | 否 | L1/concept，默认 L1 |
| --top-n | int | 否 | 返回 TOP N，默认 10 |

**输出示例**：

```json
{
  "date": "2026-03-08",
  "category": "L1",
  "boards": [
    {
      "name": "电子",
      "pe": 35.2,
      "pb": 3.5,
      "pe_change_week": 2.5,
      "pb_change_week": 1.8,
      "valuation_trend": "上升",
      "price_trend": 3.2,
      "prosperity_score": 75.5,
      "level": "高景气"
    }
  ]
}
```

---

## 四、计算逻辑

### 4.1 估值趋势计算

**周环比计算**：
```
pe_change_week = (当前 PE - 一周前 PE) / 一周前 PE * 100
pb_change_week = (当前 PB - 一周前 PB) / 一周前 PB * 100
```

**趋势判断**：

| 指标 | 上升 | 稳定 | 下降 |
|------|------|------|------|
| PE 变化 | > +5% | -5% ~ +5% | < -5% |
| PB 变化 | > +3% | -3% ~ +3% | < -3% |

**综合估值趋势**：
- PE 和 PB 都上升 → "上升"
- PE 和 PB 都下降 → "下降"
- 其他 → "稳定"

### 4.2 景气度评分计算

**评分维度**：

| 维度 | 权重 | 计算方式 |
|------|------|----------|
| 估值趋势分 | 40% | 上升=100，稳定=60，下降=20 |
| 价格趋势分 | 40% | 基于涨跌幅归一化（0-100） |
| 市值变化分 | 20% | 基于市值环比归一化（0-100） |

**归一化公式**：
```
score = (value - min) / (max - min) * 100
```

**综合评分**：
```
prosperity_score = 估值趋势分 * 0.4 + 价格趋势分 * 0.4 + 市值变化分 * 0.2
```

### 4.3 等级判断

| 分数 | 等级 |
|------|------|
| ≥ 70 | 高景气 |
| 50-69 | 中等景气 |
| < 50 | 低景气 |

---

## 五、边界处理

### 无历史数据

- 首次查询无上周数据时，估值趋势标记为 "新"
- 景气度评分仅基于当前数据

### 数据缺失

- PE/PB 为空时，跳过该板块
- 部分字段缺失时，用可用字段计算

### 日期处理

- 自动获取最近交易日
- 循环回溯最多 5 天查找历史数据

---

## 六、测试策略

### 单元测试

| 测试项 | 数量 |
|--------|------|
| SectorValuationFetcher 转换逻辑 | 3-5 |
| 估值趋势计算 | 3 |
| 景气度评分计算 | 3 |
| 边界情况 | 2 |

### 集成测试

- 真实 API 调试（通过 __main__）
- 数据文件保存验证

---

## 七、依赖

- Tushare token（需 5000 积分）
- openclaw_alpha.core 框架
- 行业分类映射（与 heat_processor 共享）
