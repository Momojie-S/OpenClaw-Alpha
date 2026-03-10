# 设计文档 - 新闻驱动投资分析

## 一、技术方案

新闻获取 + 关键词提取 + 多 Skill 协作。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 财联社全球资讯 | AKShare | `stock_news_em_symbol()` |
| 财联社重点资讯 | AKShare | `stock_news_em()` |
| 个股新闻 | AKShare | `stock_news_em()` |

## 三、模块划分

```
news_driven_investment/scripts/
├── news_fetcher/
│   └── news_fetcher.py
└── news_helper.py
```

### news_fetcher

获取新闻数据：
- 支持多个数据源
- 支持关键词筛选
- 支持日期筛选

### news_helper

管理中间数据：
- save_keywords：保存关键词
- load_keywords：读取关键词

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--source` | 数据源 | cls_global |
| `--symbol` | 股票代码（个股新闻） | - |
| `--keyword` | 关键词 | - |
| `--date` | 日期 | - |
| `--limit` | 返回数量 | 10 |

## 五、输出设计

`.openclaw_alpha/news_driven_investment/{date}/`
- `keywords.json`
- `analysis.md`
- `candidates.json`
