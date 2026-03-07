# 任务：行业景气度分析

## 需求

分析框架中 P1 优先级的最后一个待补充能力。行业景气度反映行业的盈利能力和发展趋势，是行业轮动分析的关键维度。

**分析思路**：
- 使用 Tushare sw_daily 获取行业 PE/PB 估值数据
- 计算估值变化趋势
- 结合热度、拥挤度形成完整的行业轮动框架

## Phase 1: 调研
- [x] 确认 Tushare sw_daily 接口可用（5000 积分）
- [x] 确认输出字段（PE/PB/涨跌幅/市值等）

## Phase 2: 文档
- [x] 编写需求文档
- [x] 编写设计文档

## Phase 3: 开发
- [x] 创建 sector_valuation_fetcher 目录
- [x] 实现 SectorValuationFetcher（Tushare sw_daily）
- [x] 实现 ProsperityProcessor
- [x] 编写单元测试 - 25 个测试

## Phase 4: 验证
- [x] 运行脚本测试 - 正常输出
- [x] 运行单元测试 - 452 passed

## Phase 5: 集成
- [x] 更新 analysis-framework.md
- [x] 更新 industry_trend SKILL.md

## Phase 6: 提交
- [x] git commit
- [x] git push

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 05:40

## 完成总结

### 新增功能

**行业景气度分析** - `prosperity_processor`

**功能**：
1. 获取行业 PE/PB 估值数据（Tushare sw_daily）
2. 计算估值周环比变化
3. 计算景气度综合评分
4. 景气度等级判断

**命令**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.prosperity_processor.prosperity_processor --category L1
```

**输出示例**：
```json
{
  "boards": [
    {
      "name": "电子",
      "pe": 35.2,
      "pb": 3.5,
      "pe_change_week": 2.5,
      "pb_change_week": 1.8,
      "valuation_trend": "稳定",
      "prosperity_score": 75.5,
      "level": "高景气"
    }
  ]
}
```

### 行业轮动黄金三角

**高景气度 + 高热度 + 低拥挤度 = 最佳投资机会**

| 景气度 | 热度 | 拥挤度 | 判断 |
|--------|------|--------|------|
| 高 | 高 | 低 | 黄金三角，强烈推荐 |
| 高 | 高 | 高 | 基本面好但过热，等待回调 |
| 高 | 低 | 低 | 底部潜伏，基本面支撑 |
| 低 | 高 | 高 | 投机炒作，风险较大 |

### 测试

- 新增 25 个测试
- 总测试数：452 passed

### 提交记录

- Commit: 21195ba
- 内容：feat: 添加行业景气度分析能力

## 备注
开始时间：2026-03-08 05:20
完成时间：2026-03-08 05:40

## 设计方案

### 数据源

**Tushare sw_daily** - 申万行业日线行情
- PE：行业市盈率
- PB：行业市净率
- pct_change：涨跌幅
- float_mv/total_mv：市值

### 景气度指标

**估值趋势**：
- PE 周环比变化
- PB 周环比变化

**景气度评分**：
- 估值趋势权重 50%
- 涨跌幅趋势权重 30%
- 市值变化权重 20%

### 输出格式

```json
{
  "boards": [
    {
      "name": "电子",
      "pe": 35.2,
      "pb": 3.5,
      "pe_change_week": 2.5,
      "pb_change_week": 1.8,
      "valuation_trend": "上升",
      "prosperity_score": 75.5
    }
  ]
}
```

## 备注
开始时间：2026-03-08 05:20
