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
- [ ] git commit
- [ ] git push

## 状态
- **当前阶段**：Phase 6
- **进度**：正常
- **下一步**：git commit

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
