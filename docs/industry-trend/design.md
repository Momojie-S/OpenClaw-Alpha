# 产业热度追踪 - 设计文档

> 版本: v2.0
> 创建时间: 2026-02-28
> 更新时间: 2026-03-03
> 状态: 开发中

---

## 一、架构设计

### 1.1 工作流程

```
用户提问 → Echo 调用脚本 → 脚本计算热度 → 获取结果 → Echo 总结输出
```

### 1.2 职责划分

| 组件 | 职责 |
|------|------|
| **数据脚本** | 获取数据 + 计算热度 + 存储历史 |
| **SQLite** | 存储历史数据，支持环比分析 |
| **Echo** | 调用脚本 + 简单逻辑 + 文字总结 |

### 1.3 设计原则

- **一个 skill**，多个数据脚本
- **代码计算**：热度公式、趋势判断用代码实现
- **大模型总结**：Echo 只做简单逻辑判断和文字组织

---

## 二、目录结构

```
OpenClaw-Alpha/
├── src/openclaw_alpha/commands/  # 数据脚本
│   ├── board_concept.py          # 概念板块 ✅
│   └── sw_industry.py            # 申万行业 ✅
├── src/openclaw_alpha/storage/   # 存储（待开发）
│   ├── __init__.py
│   ├── db.py                     # SQLite 连接
│   └── models.py                 # 数据模型
├── skills/industry-trend/        # skill 定义
├── data/                         # SQLite 数据库（待开发）
│   └── industry_trend.db
├── .env                          # 环境变量
└── CLAUDE.md                     # 项目说明
```

---

## 三、数据源

### 3.1 申万行业

| 项目 | 说明 |
|------|------|
| 数据源 | Tushare Pro |
| 接口 | `sw_daily` |
| 积分要求 | 120 |
| 换手率 | 可计算（成交额/流通市值） |

详见 [sw_daily.md](../references/tushare/sw_daily.md)

### 3.2 概念板块

| 项目 | 说明 |
|------|------|
| 数据源 | 东方财富（AKShare）|
| 接口 | `stock_board_concept_name_em` |
| 积分要求 | 无 |
| 缺失字段 | 净流入（需补充） |

详见 [stock_board_concept_name_em.md](../references/akshare/stock_board_concept_name_em.md)

---

## 四、热度计算实现

### 4.1 热度指数

**输入**：涨跌幅、换手率、净流入、涨跌家数

**算法思路**：
1. 各维度归一化到 0-100（sigmoid 函数）
2. 加权平均：
   - 涨跌幅 × 30%
   - 换手率 × 25%（以 5% 为基准）
   - 净流入 × 25%
   - 涨跌比 × 20%

**输出**：热度指数（0-100）

### 4.2 趋势信号

**输入**：热度环比、涨跌幅、净流入

**判断规则**：
- 加热中：环比 > 20% 且 涨幅 > 0 且 流入 > 0
- 降温中：环比 < -20% 或 (涨幅 < -3% 且 流出)
- 稳定：其他

**输出**：信号标识（heating_up / cooling_down / stable）

### 4.3 环比计算

**输入**：当前热度、上一交易日热度

**算法**：(当前 - 上期) / 上期 × 100%

**依赖**：SQLite 存储历史数据

---

## 五、存储设计

### 5.1 表结构

```sql
CREATE TABLE board_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    board_code TEXT NOT NULL,
    board_name TEXT NOT NULL,
    board_type TEXT NOT NULL,  -- industry/concept/sw
    
    change_pct REAL,
    turnover_rate REAL,
    net_inflow REAL,
    up_count INTEGER,
    down_count INTEGER,
    
    hot_score REAL,
    hot_change REAL,
    trend_signal TEXT,
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(trade_date, board_code, board_type)
);
```

### 5.2 数据保留

- 保留最近 30 个交易日
- 自动清理过期数据

---

## 六、环境配置

### 6.1 环境变量

```bash
# .env
TUSHARE_TOKEN=your_token_here
```

### 6.2 运行命令

```bash
# 申万行业
uv run --env-file .env --directory {baseDir}/.. python src/openclaw_alpha/commands/sw_industry.py

# 概念板块
uv run --directory {baseDir}/.. python src/openclaw_alpha/commands/board_concept.py
```

---

## 七、开发状态

### 7.1 已完成

| 脚本 | 功能 | 数据源 |
|------|------|--------|
| `sw_industry.py` | 申万行业 | Tushare |
| `board_concept.py` | 概念板块 | 东方财富 |
| `industry-trend` skill | skill 定义 | - |

### 7.2 待开发

| 任务 | 优先级 |
|------|:------:|
| SQLite 存储实现 | P0 |
| 热度计算集成 | P0 |
| 趋势信号判断 | P0 |
| 概念板块净流入 | P1 |
| 环比计算 | P1 |

---

## 八、开发状态
