# 综合分析 Skill 设计文档

> 版本: v1.0
> 创建时间: 2026-03-08

---

## 一、技术选型

### 1.1 架构决策

**不开发新 Fetcher**：复用现有 skill 的 Processor 输出，避免重复造轮子。

**Processor 串联**：通过读取各 skill 的 JSON 输出文件，整合分析结果。

### 1.2 数据流

```
MarketOverviewProcessor
    │
    ├── 读取 index_analysis 输出 → 宏观数据
    ├── 读取 market_sentiment 输出 → 情绪数据
    ├── 读取 industry_trend 输出 → 板块数据
    ├── 读取 fund_flow_analysis 输出 → 资金流向数据
    └── 读取 northbound_flow 输出 → 外资数据
         │
         ▼
    整合分析 → 生成报告
         │
         ├── 控制台：Markdown 文本
         └── 文件：JSON 数据
```

---

## 二、接口设计

### 2.1 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--date` | str | 今天 | 分析日期 |
| `--mode` | str | full | 快速版(quick)/完整版(full) |
| `--skip` | str | 无 | 跳过的 skill（逗号分隔） |

### 2.2 输出格式

**控制台输出（Markdown）**：

```markdown
# 市场分析报告 - 2026-03-08

## 一、市场概览

**整体判断**：震荡上涨

| 指数 | 收盘 | 涨跌幅 | 趋势 |
|------|------|--------|------|
| 上证指数 | 3345.67 | +0.5% | 震荡 |
| 创业板指 | 2256.78 | +1.2% | 震荡上涨 |

**市场温度**：正常 (55/100)

## 二、情绪分析

**情绪状态**：偏热

- 涨停：85 家
- 跌停：12 家
- 主力净流入：+25.3 亿

## 三、板块热点

**行业 Top 3**：
1. 电子 (+3.5%) - 加热中
2. 计算机 (+2.8%) - 加热中
3. 通信 (+2.1%) - 稳定

**概念 Top 3**：
1. 人工智能 (+4.2%)
2. 机器人 (+3.8%)
3. 芯片 (+3.1%)

## 四、外资动向

**北向资金**：流入 +44.0 亿

**买入 Top 3**：
1. 贵州茅台 (+8.5 亿)
2. 宁德时代 (+6.2 亿)
3. 比亚迪 (+4.8 亿)

## 五、综合结论

1. 指数震荡偏强，创业板领涨
2. 情绪偏热，涨停家数较多
3. 科技板块（电子、计算机）领涨
4. 外资持续流入，看好科技龙头

**关注**：人工智能、机器人、芯片
```

**文件输出（JSON）**：

```json
{
  "date": "2026-03-08",
  "mode": "full",
  "generated_at": "2026-03-08T00:05:00",
  "overall": {
    "judgment": "震荡上涨",
    "confidence": 0.75
  },
  "macro": {
    "indices": [...],
    "temperature": 55,
    "trend": "震荡"
  },
  "sentiment": {
    "status": "偏热",
    "limit_up": 85,
    "limit_down": 12,
    "main_flow": 25.3
  },
  "sectors": {
    "industry_top": [...],
    "concept_top": [...],
    "fund_flow_top": [...]
  },
  "northbound": {
    "total_flow": 44.0,
    "status": "流入",
    "top_inflow": [...],
    "top_outflow": [...]
  },
  "conclusion": {
    "summary": "指数震荡偏强，科技板块领涨...",
    "highlights": ["人工智能", "机器人", "芯片"],
    "risks": []
  }
}
```

---

## 三、模块设计

### 3.1 目录结构

```
skills/market_overview/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── overview_processor/
        ├── __init__.py
        └── overview_processor.py
```

### 3.2 类设计

**MarketOverviewProcessor**：

```python
class MarketOverviewProcessor:
    """市场综合分析 Processor"""
    
    def __init__(self):
        self.date: str
        self.mode: str  # quick / full
    
    async def process(self) -> dict:
        """主入口：生成综合报告"""
        pass
    
    async def load_macro_data(self) -> dict:
        """加载宏观层数据（index_analysis）"""
        pass
    
    async def load_sentiment_data(self) -> dict:
        """加载情绪数据（market_sentiment）"""
        pass
    
    async def load_sector_data(self) -> dict:
        """加载板块数据（industry_trend, fund_flow_analysis）"""
        pass
    
    async def load_northbound_data(self) -> dict:
        """加载外资数据（northbound_flow）"""
        pass
    
    def generate_judgment(self) -> str:
        """生成综合判断"""
        pass
    
    def format_report(self, data: dict) -> str:
        """格式化 Markdown 报告"""
        pass
```

---

## 四、实现细节

### 4.1 数据加载策略

**优先读取缓存文件**：
- 各 skill 已有 JSON 输出（`.openclaw_alpha/{skill}/{date}/xxx.json`）
- 读取缓存文件，避免重复调用 API
- 缓存不存在时，调用对应的 Processor 生成

**容错处理**：
- 单个 skill 失败不影响整体
- 失败的 skill 在报告中标注"数据获取失败"
- 记录错误日志

### 4.2 快速版 vs 完整版

| 版本 | 包含内容 | 耗时 |
|------|----------|------|
| quick | 宏观 + 情绪 | < 10s |
| full | 全部四个层次 | < 30s |

### 4.3 综合判断算法

```python
def generate_judgment(self) -> str:
    # 1. 计算指数平均涨跌幅
    avg_change = mean([i['change_pct'] for i in indices])
    
    # 2. 获取情绪温度
    temp = sentiment['temperature']
    
    # 3. 获取外资流向
    flow = northbound['total_flow']
    
    # 4. 综合判断
    if avg_change > 1 and temp > 60 and flow > 10:
        return "强势上涨"
    elif avg_change > 0 and temp > 40:
        return "震荡上涨"
    elif avg_change < -1 and temp < 40 and flow < -10:
        return "弱势下跌"
    elif avg_change < 0 and temp < 60:
        return "震荡下跌"
    else:
        return "震荡"
```

---

## 五、依赖关系

### 5.1 依赖的 Skill

| Skill | 数据内容 | 必需 |
|-------|----------|------|
| index_analysis | 指数行情、市场温度 | ✅ |
| market_sentiment | 情绪温度、涨跌停 | ✅ |
| industry_trend | 板块热度排名 | ❌ |
| fund_flow_analysis | 资金流向 | ❌ |
| northbound_flow | 北向资金 | ❌ |

### 5.2 文件路径约定

```
.openclaw_alpha/
├── index_analysis/{date}/index.json
├── market_sentiment/{date}/sentiment.json
├── industry_trend/{date}/heat.json
├── fund_flow_analysis/{date}/fund_flow.json
├── northbound_flow/{date}/northbound.json
└── market_overview/{date}/report.json
```

---

## 六、测试策略

### 6.1 单元测试

- 数据加载逻辑
- 综合判断算法
- 报告格式化

### 6.2 集成测试

- 使用 fixture 数据模拟各 skill 输出
- 测试完整流程

---

## 七、注意事项

1. **首次运行**：各 skill 的 JSON 输出可能不存在，需要先调用对应 Processor
2. **数据一致性**：不同 skill 的日期参数需保持一致
3. **容错设计**：部分数据缺失不影响整体报告生成
