# 设计文档 - industry_trend

## 一、技术方案

从 Tushare 获取申万行业数据，从 AKShare 获取概念板块数据，计算热度指数、拥挤度、景气度等多个维度，综合分析板块轮动机会。

## 二、数据源

| 数据 | 来源 | 积分要求 |
|------|------|---------|
| 申万行业行情 | Tushare `sw_daily` | 120 |
| 申万行业分类 | Tushare `index_classify` | 基础 |
| 概念板块行情 | AKShare | 免费 |
| 行业估值 | Tushare `daily_basic` | 2000 |

## 三、模块划分

```
industry_trend/
├── scripts/
│   ├── concept_fetcher/          # 概念板块数据获取
│   ├── industry_fetcher/         # 申万行业数据获取
│   ├── sector_valuation_fetcher/ # 行业估值数据获取
│   ├── industry_trend_processor/ # 热度分析
│   ├── crowdedness_processor/    # 拥挤度分析
│   ├── prosperity_processor/     # 景气度分析
│   └── rotation_score_processor/ # 轮动评分
└── docs/
```

### Fetchers

| Fetcher | 职责 |
|---------|------|
| `industry_fetcher` | 获取申万行业日线行情 |
| `concept_fetcher` | 获取概念板块行情 |
| `sector_valuation_fetcher` | 获取行业估值数据 |

### Processors

| Processor | 职责 | 输出 |
|-----------|------|------|
| `industry_trend_processor` | 计算热度指数 | 热度排名、趋势信号 |
| `crowdedness_processor` | 计算拥挤度 | 拥挤度排名 |
| `prosperity_processor` | 计算景气度 | 景气度评分 |
| `rotation_score_processor` | 计算轮动评分 | 黄金组合识别 |

## 四、注意事项

- 申万行业数据需要 120+ 积分
- 估值数据需要 2000 积分
- 概念板块使用 AKShare 免费获取
