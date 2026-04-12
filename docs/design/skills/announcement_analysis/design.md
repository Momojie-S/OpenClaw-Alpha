# 设计文档 - 公告解读

## 一、技术方案

使用 AKShare 的东方财富公告接口。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 公司公告 | AKShare | `stock_notice_report()` |

## 三、模块划分

```
announcement_analysis/scripts/
└── announcement_processor/
    └── announcement_processor.py
```

### announcement_processor

获取公告数据：
- 支持按类型筛选
- 支持按代码搜索
- 支持按关键词搜索

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 日期 | 今日 |
| `--type` | 公告类型 | 全部 |
| `--code` | 股票代码 | - |
| `--keyword` | 关键词 | - |
| `--top-n` | 返回数量 | 20 |

## 五、输出设计

`.openclaw_alpha/announcement_analysis/{date}/announcements.json`
