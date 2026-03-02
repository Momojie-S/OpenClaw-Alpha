# 产业热度追踪模块 - 需求文档

> 版本: v1.0
> 创建时间: 2026-02-28
> 状态: 待开发
> 目标项目: OneDragon-Alpha

---

## 一、项目背景

### 1.1 业务目标
在 OneDragon-Alpha 项目中新增产业热度追踪模块，通过分析 A股、港股、美股市场数据，识别：
- **高关注度产业** - 当前市场热点
- **升温中产业** - 关注度正在上升的新兴板块
- **降温产业** - 热度下降的板块

### 1.2 目标用户
- 个人投资者
- 需要了解市场热度的研究人员

### 1.3 数据范围
| 市场 | 覆盖范围 |
|------|----------|
| A股 | 沪深主板、科创板、创业板、北交所 |
| 港股 | 港交所主板 |
| 美股 | 纳斯达克、纽交所主要股票 |

---

## 二、技术架构

### 2.1 遵循 OneDragon-Alpha 现有架构

```
src/one_dragon_alpha/
├── core/                    # 已有: 核心模块 (日志等)
├── services/                # 已有: 服务层 (MySQL 连接)
├── server/                  # 已有: FastAPI 服务
├── strategy/                # 已有: 策略模块
│   └── industry/            # 已有: 行业策略 (brokerage.py)
│       └── hot_trend/       # 【新增】产业热度追踪模块
├── agent/                   # 已有: Agent 模块
└── ...
```

### 2.2 新增模块结构

```
src/one_dragon_alpha/
├── strategy/
│   └── industry/
│       └── hot_trend/                     # 产业热度追踪模块
│           ├── __init__.py
│           ├── config.py                   # 模块配置
│           ├── collector/                  # 数据采集
│           │   ├── __init__.py
│           │   ├── base.py                 # 采集器基类
│           │   ├── akshare_collector.py    # AKShare 采集器
│           │   └── tushare_collector.py    # Tushare 采集器
│           ├── models/                     # 数据模型 (SQLAlchemy ORM)
│           │   ├── __init__.py
│           │   ├── board_daily.py          # 板块日线数据
│           │   ├── stock_hot_rank.py       # 股票热度排名
│           │   └── industry_analysis.py    # 行业分析结果
│           ├── analyzer/                   # 数据分析
│           │   ├── __init__.py
│           │   ├── hot_score.py            # 热度计算
│           │   └── trend.py                # 趋势分析
│           ├── repository/                 # 数据访问层
│           │   ├── __init__.py
│           │   ├── board_daily_repo.py
│           │   └── analysis_repo.py
│           └── service.py                  # 业务服务层
│
└── server/
    └── hot_trend/                          # API 路由
        ├── __init__.py
        └── router.py                       # FastAPI 路由
```

---

## 三、技术要求

### 3.1 遵循现有规范

| 规范 | 要求 |
|------|------|
| **编码风格** | 遵循 OneDragon-Alpha development-guide.md |
| **异步编程** | 所有操作使用 async/await |
| **文档注释** | Google 风格中文注释 |
| **类型提示** | 所有函数和类成员必须有类型提示 |
| **编码声明** | 文件开头添加 `# -*- coding: utf-8 -*-` |
| **日志模块** | 使用 `one_dragon_alpha.core.system.log.get_logger()` |
| **数据库操作** | 使用 SQLAlchemy ORM，异步操作 |
| **环境变量** | 通过 `.env` 文件管理 |

### 3.2 依赖管理

新增依赖 (添加到 pyproject.toml):
```toml
dependencies = [
    # 现有依赖...
    "akshare>=1.17.49",    # 已有
    "tushare>=1.4.24",     # 已有
    "aiomysql>=0.3.2",     # 已有
    "sqlalchemy>=2.0.46",  # 已有
]
```

### 3.3 环境变量

在 `.env` 中新增:
```bash
# 产业热度追踪模块配置
HOT_TREND_COLLECT_TIME=18:00    # 每日采集时间
HOT_TREND_REPORT_TOP_N=20       # 报告显示 TOP N

# Tushare Token (已有)
TUSHARE_API_TOKEN=your_token
```

---

## 四、数据模型设计

### 4.1 数据库表结构 (MySQL)

#### 4.1.1 板块日线数据表 (ht_board_daily)

```sql
CREATE TABLE ht_board_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL COMMENT '交易日期',
    board_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    board_name VARCHAR(50) NOT NULL COMMENT '板块名称',
    board_type VARCHAR(20) NOT NULL COMMENT '板块类型: industry/concept',
    market VARCHAR(10) NOT NULL COMMENT '市场: a/hk/us',
    source VARCHAR(20) NOT NULL COMMENT '数据源: akshare/tushare',
    
    -- 行情数据
    change_pct DECIMAL(10,4) COMMENT '涨跌幅(%)',
    turnover_rate DECIMAL(10,4) COMMENT '换手率(%)',
    total_mv DECIMAL(20,4) COMMENT '总市值(亿)',
    circ_mv DECIMAL(20,4) COMMENT '流通市值(亿)',
    
    -- 涨跌统计
    up_count INT COMMENT '上涨家数',
    down_count INT COMMENT '下跌家数',
    flat_count INT COMMENT '平盘家数',
    
    -- 领涨股
    leader_code VARCHAR(20) COMMENT '领涨股代码',
    leader_name VARCHAR(50) COMMENT '领涨股名称',
    leader_change DECIMAL(10,4) COMMENT '领涨股涨幅',
    
    -- 资金流向
    net_inflow DECIMAL(20,4) COMMENT '净流入(亿)',
    main_net_inflow DECIMAL(20,4) COMMENT '主力净流入(亿)',
    
    -- 热度指标
    hot_rank INT COMMENT '热度排名',
    hot_score DECIMAL(10,4) COMMENT '热度分数',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_date_code_source (trade_date, board_code, source),
    INDEX idx_trade_date (trade_date),
    INDEX idx_board_name (board_name),
    INDEX idx_board_type (board_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='板块日线数据表';
```

#### 4.1.2 股票热度排名表 (ht_stock_hot_rank)

```sql
CREATE TABLE ht_stock_hot_rank (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    snapshot_time DATETIME NOT NULL COMMENT '快照时间',
    trade_date DATE NOT NULL COMMENT '交易日期',
    
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    market VARCHAR(10) COMMENT '市场: a/hk/us',
    
    rank_val INT COMMENT '热度排名',
    score DECIMAL(10,4) COMMENT '热度分数',
    source VARCHAR(20) COMMENT '来源: eastmoney/xueqiu',
    
    -- 关联概念 (JSON)
    concepts TEXT COMMENT '关联概念: ["人工智能", "ChatGPT"]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_snapshot_code_source (snapshot_time, stock_code, source),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票热度排名表';
```

#### 4.1.3 行业分析结果表 (ht_industry_analysis)

```sql
CREATE TABLE ht_industry_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL COMMENT '交易日期',
    
    board_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    board_name VARCHAR(50) NOT NULL COMMENT '板块名称',
    board_type VARCHAR(20) NOT NULL COMMENT '板块类型',
    
    -- 热度指标
    hot_score DECIMAL(10,4) COMMENT '热度分数 (0-100)',
    hot_rank INT COMMENT '热度排名',
    hot_change DECIMAL(10,4) COMMENT '热度环比变化(%)',
    
    -- 涨跌幅
    change_pct DECIMAL(10,4) COMMENT '当日涨跌幅(%)',
    change_pct_5d DECIMAL(10,4) COMMENT '5日涨跌幅(%)',
    change_pct_20d DECIMAL(10,4) COMMENT '20日涨跌幅(%)',
    
    -- 资金指标
    net_inflow_5d DECIMAL(20,4) COMMENT '5日净流入(亿)',
    net_inflow_20d DECIMAL(20,4) COMMENT '20日净流入(亿)',
    
    -- 综合评估
    trend_signal VARCHAR(20) COMMENT '趋势信号: heating_up/cooling_down/stable',
    attention_level VARCHAR(20) COMMENT '关注级别: high/medium/low',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_date_code (trade_date, board_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_hot_score (hot_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行业分析结果表';
```

### 4.2 SQLAlchemy ORM 模型示例

```python
# -*- coding: utf-8 -*-
"""板块日线数据模型."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Decimal as SQLDecimal,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 基类."""
    pass


class BoardDaily(Base):
    """板块日线数据模型.

    Attributes:
        id: 主键ID.
        trade_date: 交易日期.
        board_code: 板块代码.
        board_name: 板块名称.
        board_type: 板块类型 (industry/concept).
        market: 市场 (a/hk/us).
        source: 数据源 (akshare/tushare).
        change_pct: 涨跌幅.
        turnover_rate: 换手率.
        total_mv: 总市值.
        circ_mv: 流通市值.
        up_count: 上涨家数.
        down_count: 下跌家数.
        flat_count: 平盘家数.
        leader_code: 领涨股代码.
        leader_name: 领涨股名称.
        leader_change: 领涨股涨幅.
        net_inflow: 净流入.
        main_net_inflow: 主力净流入.
        hot_rank: 热度排名.
        hot_score: 热度分数.
        created_at: 创建时间.
        updated_at: 更新时间.
    """

    __tablename__ = "ht_board_daily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    board_code: Mapped[str] = mapped_column(String(20), nullable=False)
    board_name: Mapped[str] = mapped_column(String(50), nullable=False)
    board_type: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    # 行情数据
    change_pct: Mapped[Decimal | None] = mapped_column(SQLDecimal(10, 4))
    turnover_rate: Mapped[Decimal | None] = mapped_column(SQLDecimal(10, 4))
    total_mv: Mapped[Decimal | None] = mapped_column(SQLDecimal(20, 4))
    circ_mv: Mapped[Decimal | None] = mapped_column(SQLDecimal(20, 4))

    # 涨跌统计
    up_count: Mapped[int | None] = mapped_column()
    down_count: Mapped[int | None] = mapped_column()
    flat_count: Mapped[int | None] = mapped_column()

    # 领涨股
    leader_code: Mapped[str | None] = mapped_column(String(20))
    leader_name: Mapped[str | None] = mapped_column(String(50))
    leader_change: Mapped[Decimal | None] = mapped_column(SQLDecimal(10, 4))

    # 资金流向
    net_inflow: Mapped[Decimal | None] = mapped_column(SQLDecimal(20, 4))
    main_net_inflow: Mapped[Decimal | None] = mapped_column(SQLDecimal(20, 4))

    # 热度指标
    hot_rank: Mapped[int | None] = mapped_column()
    hot_score: Mapped[Decimal | None] = mapped_column(SQLDecimal(10, 4))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        UniqueConstraint("trade_date", "board_code", "source", name="uk_date_code_source"),
        Index("idx_trade_date", "trade_date"),
        Index("idx_board_name", "board_name"),
        Index("idx_board_type", "board_type"),
    )
```

---

## 五、数据采集接口

### 5.1 AKShare 接口清单

#### 5.1.1 A股 - 行业板块 (P0)

| 接口名称 | 函数 | 用途 | 更新频率 |
|----------|------|------|----------|
| 行业板块实时行情 | `stock_board_industry_name_em()` | 所有行业板块行情 | 每日盘后 |
| 行业板块成分股 | `stock_board_industry_cons_em(symbol)` | 行业成分股列表 | 每周 |
| 行业板块指数 | `stock_board_industry_index_em(symbol)` | 行业指数历史 | 每日 |

#### 5.1.2 A股 - 概念板块 (P0)

| 接口名称 | 函数 | 用途 | 更新频率 |
|----------|------|------|----------|
| 概念板块实时行情 | `stock_board_concept_name_em()` | 所有概念板块行情 | 每日盘后 |
| 概念板块成分股 | `stock_board_concept_cons_em(symbol)` | 概念成分股 | 每周 |

#### 5.1.3 A股 - 热度数据 (P0)

| 接口名称 | 函数 | 用途 | 更新频率 |
|----------|------|------|----------|
| 股票热度排名 | `stock_hot_rank_em()` | TOP100热门股票 | 每日 |
| 个股热门关键词 | `stock_hot_keyword_em(symbol)` | 个股关联概念 | 每日 |

#### 5.1.4 沪深港通 (P1)

| 接口名称 | 函数 | 用途 | 更新频率 |
|----------|------|------|----------|
| 沪深港通历史 | `stock_hsgt_hist_em()` | 北向资金历史 | 每日 |

### 5.2 Tushare Pro 接口清单

#### 5.2.1 基础数据 (P0)

| 接口名称 | 函数 | 用途 | 积分要求 |
|----------|------|------|----------|
| 股票列表 | `pro.stock_basic()` | A股股票列表 | 0 |
| 交易日历 | `pro.trade_cal()` | 交易日历 | 0 |

#### 5.2.2 行业分类 (P1)

| 接口名称 | 函数 | 用途 | 积分要求 |
|----------|------|------|----------|
| 申万行业分类 | `pro.index_classify()` | 行业分类 | 120 |
| 行业成分股 | `pro.index_member()` | 行业成分 | 120 |

---

## 六、热度计算模型

### 6.1 综合热度指数公式

```
热度指数 = w1 × 涨跌幅归一化 +
          w2 × 换手率归一化 +
          w3 × 资金净流入归一化 +
          w4 × 热度排名归一化

推荐权重:
- w1 (涨跌幅): 0.30
- w2 (换手率): 0.25
- w3 (资金流向): 0.25
- w4 (热度排名): 0.20
```

### 6.2 趋势信号判断

```python
def get_trend_signal(
    hot_change: float,
    change_pct: float,
    net_inflow: float
) -> str:
    """计算趋势信号.

    Args:
        hot_change: 热度环比变化.
        change_pct: 涨跌幅.
        net_inflow: 资金净流入.

    Returns:
        str: 趋势信号 (heating_up/cooling_down/stable).
    """
    if hot_change > 20 and change_pct > 0 and net_inflow > 0:
        return "heating_up"
    elif hot_change < -20 or (change_pct < -3 and net_inflow < 0):
        return "cooling_down"
    else:
        return "stable"
```

---

## 七、API 设计

### 7.1 RESTful API 接口

#### 7.1.1 获取热度排行

```
GET /api/hot-trend/ranking

Query Parameters:
  - trade_date: 交易日期 (可选, 默认最新)
  - board_type: 板块类型 (industry/concept, 可选)
  - top_n: 返回数量 (默认 20)

Response:
{
  "code": 0,
  "data": {
    "trade_date": "2026-02-28",
    "items": [
      {
        "rank": 1,
        "board_code": "BK0001",
        "board_name": "人工智能",
        "change_pct": 5.23,
        "hot_score": 95.6,
        "trend_signal": "heating_up"
      }
    ]
  }
}
```

#### 7.1.2 获取趋势预警

```
GET /api/hot-trend/alerts

Query Parameters:
  - trade_date: 交易日期 (可选, 默认最新)
  - signal_type: 信号类型 (heating_up/cooling_down, 可选)

Response:
{
  "code": 0,
  "data": {
    "trade_date": "2026-02-28",
    "heating_up": [
      {
        "board_name": "人形机器人",
        "hot_change": 45.2,
        "change_pct": 6.8,
        "net_inflow": 5.2
      }
    ],
    "cooling_down": [
      {
        "board_name": "锂电池",
        "hot_change": -25.3,
        "change_pct": -2.1,
        "net_inflow": -3.1
      }
    ]
  }
}
```

#### 7.1.3 手动触发采集

```
POST /api/hot-trend/collect

Request Body:
{
  "data_type": "board_daily",  // board_daily / hot_rank / all
  "trade_date": "2026-02-28"   // 可选, 默认当天
}

Response:
{
  "code": 0,
  "message": "采集任务已启动",
  "data": {
    "task_id": "xxx"
  }
}
```

---

## 八、开发阶段划分

### Phase 1: MVP (预计 3-5 天)

**目标**: 跑通核心流程，输出基础数据

| 任务 | 文件 | 预计时间 |
|------|------|----------|
| 创建模块目录结构 | `strategy/industry/hot_trend/` | 0.5 天 |
| 数据库表创建脚本 | `models/` | 0.5 天 |
| AKShare 行业板块采集器 | `collector/akshare_collector.py` | 1 天 |
| AKShare 概念板块采集器 | `collector/akshare_collector.py` | 0.5 天 |
| 板块日线数据 ORM | `models/board_daily.py` | 0.5 天 |
| 基础 Repository | `repository/board_daily_repo.py` | 0.5 天 |
| 基础热度计算 | `analyzer/hot_score.py` | 0.5 天 |

**交付物**:
- 可运行的数据采集脚本
- MySQL 数据存储
- 基础 API 接口

### Phase 2: 增强 (预计 3-5 天)

**目标**: 完善分析能力

| 任务 | 文件 | 预计时间 |
|------|------|----------|
| Tushare 采集器 | `collector/tushare_collector.py` | 1 天 |
| 热度趋势分析 | `analyzer/trend.py` | 1 天 |
| 行业分析 ORM | `models/industry_analysis.py` | 0.5 天 |
| 预警 API | `server/hot_trend/router.py` | 0.5 天 |
| 历史数据回填脚本 | `scripts/backfill.py` | 0.5 天 |

### Phase 3: 完善 (预计 2-3 天)

**目标**: 测试和文档

| 任务 | 预计时间 |
|------|----------|
| 单元测试 | 1 天 |
| 集成测试 | 0.5 天 |
| API 文档 | 0.5 天 |

---

## 九、验收标准

### 9.1 Phase 1 验收

- [ ] 能成功采集 A股行业板块数据
- [ ] 能成功采集 A股概念板块数据
- [ ] 数据正确存储到 MySQL
- [ ] 提供基础 API 接口获取数据
- [ ] 代码符合项目规范 (类型提示、文档注释等)

### 9.2 Phase 2 验收

- [ ] 热度趋势计算正确 (环比变化)
- [ ] 升温/降温预警功能正常
- [ ] 能回填历史数据 (至少30天)

### 9.3 Phase 3 验收

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] API 文档完整

---

## 十、注意事项

### 10.1 遵循现有规范

1. **日志**: 使用 `get_logger(__name__)` 获取日志对象
2. **异常处理**: 使用统一的异常处理机制
3. **测试数据**: 测试数据使用 `test_` 前缀，测试后清理
4. **临时文件**: 使用项目根目录 `.temp/` 文件夹

### 10.2 命名约定

- 表名前缀: `ht_` (hot trend)
- 模块目录: `hot_trend/`
- API 路由: `/api/hot-trend/`

### 10.3 现有资源复用

- MySQL 连接服务: `one_dragon_alpha.services.mysql.connection_service`
- 日志模块: `one_dragon_alpha.core.system.log`
- Tushare 工具: 参考 `strategy/industry/brokerage.py`

---

## 附录 A: 参考文件

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 开发流程规范 |
| `docs/development-guide.md` | 编码规范 |
| `docs/project-overview.md` | 项目概述 |
| `src/one_dragon_alpha/services/mysql/` | MySQL 服务参考 |
| `src/one_dragon_alpha/strategy/industry/brokerage.py` | 策略代码参考 |

---

*文档结束*
