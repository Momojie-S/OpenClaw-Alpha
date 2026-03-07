# 公告解读 Skill - 设计文档

## 技术方案

### 数据源

使用 AKShare `stock_notice_report` 接口：
- 来源：东方财富网
- 免费、稳定
- 支持按类型和日期筛选

### 架构

简化架构：直接在 Processor 中调用 AKShare，无需独立 Fetcher。

```
用户 → Processor → AKShare → 输出
```

**理由**：
- 单一数据源（AKShare）
- 数据处理逻辑简单
- 参考基金分析 skill 的简化架构

## 接口设计

### AKShare 接口

```python
stock_notice_report(symbol: str, date: str) -> DataFrame
```

**参数**：
- `symbol`: 公告类型（"全部"、"重大事项"、"财务报告"等）
- `date`: 日期（YYYYMMDD 格式）

**返回字段**：
- 代码
- 名称
- 公告标题
- 公告类型
- 日期
- 链接

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 日期 | 今日 |
| `--type` | 公告类型 | 全部 |
| `--code` | 股票代码 | - |
| `--keyword` | 关键词 | - |
| `--top-n` | 返回数量 | 20 |

## 数据处理

### 筛选逻辑

1. 获取原始数据
2. 按类型筛选（API 支持）
3. 按代码筛选（本地过滤）
4. 按关键词筛选（本地搜索）
5. 排序（按重要性）
6. 返回 Top N

### 类型重要性映射

```python
TYPE_PRIORITY = {
    "风险提示": 3,
    "重大事项": 3,
    "财务报告": 3,
    "资产重组": 2,
    "融资公告": 2,
    "持股变动": 2,
    "信息变更": 1,
}
```

## 输出格式

```
【公告列表】2026-03-07

⭐⭐⭐ 重大事项
1. 000001 平安银行：关于重大资产购买...
   https://xxx

⭐⭐ 资产重组
2. 600000 浦发银行：关于重大资产重组...
   https://xxx

---
共 50 条公告，显示 20 条
```

## 文件结构

```
skills/announcement_analysis/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── announcement_processor/
        ├── __init__.py
        ├── announcement_processor.py
        └── models.py
```

## 测试计划

| 测试项 | 数量 |
|--------|------|
| 类型筛选 | 2 |
| 代码筛选 | 2 |
| 关键词搜索 | 2 |
| 排序逻辑 | 2 |
| 格式化输出 | 2 |
| **总计** | ~10 |
