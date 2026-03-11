# Web 服务架构设计

## 目标

为 OpenClaw-Alpha 提供 Web 服务能力，支持：
- 定时任务调度（内置 APScheduler）
- 扩展的服务模块（新闻订阅、后续其他模块）

## 技术栈

- **框架**：FastAPI
- **调度**：APScheduler（AsyncIOScheduler）
- **配置**：YAML 文件
- **日志**：统一日志模块

## 目录结构

```
~/.openclaw_alpha/
├── config/
│   └── service.yaml           # 服务配置（端口、调度等）
├── cache/                     # 各模块缓存（按模块划分子目录）
└── logs/
    └── alpha-service.log      # 服务日志

src/openclaw_alpha/backend/
├── __init__.py
├── main.py                    # FastAPI 入口 + 调度器初始化
├── config.py                  # 配置加载
├── logger.py                  # 统一日志模块
├── scheduler.py               # APScheduler 封装
└── {module}/                  # 各功能模块
    ├── __init__.py
    ├── router.py              # FastAPI 路由
    ├── jobs.py                # 定时任务
    └── ...
```

## 统一日志模块

**文件**：`src/openclaw_alpha/backend/logger.py`

**功能**：
- 统一日志格式
- 按天轮转，保留 7 天
- 支持不同模块独立日志文件
- 支持日志级别配置

**接口设计**：

```python
def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称（通常用 __name__）
        log_file: 日志文件名（None 则使用默认文件）
    
    Returns:
        配置好的日志器
    """
    pass

def setup_logging(log_level: str = "INFO", log_dir: Path | None = None):
    """
    初始化日志系统
    
    Args:
        log_level: 日志级别（DEBUG / INFO / WARNING / ERROR）
        log_dir: 日志目录（None 则使用默认目录 ~/.openclaw_alpha/logs/）
    """
    pass
```

**使用示例**：

```python
from openclaw_alpha.backend.logger import get_logger, setup_logging

# 初始化（通常在 main.py 中调用一次）
setup_logging(log_level="INFO")

# 获取日志器
logger = get_logger(__name__)
logger.info("服务启动")

# 获取模块独立日志文件
news_logger = get_logger(__name__, log_file="news.log")
news_logger.info("新闻拉取完成")
```

**日志格式**：
```
2026-03-12 10:30:00 [INFO] module.name - 日志消息
```

**文件轮转**：
- 按天轮转：`alpha-service.log` → `alpha-service.log.2026-03-11`
- 保留 7 天，自动清理过期文件

## 配置文件

**路径**：`~/.openclaw_alpha/config/service.yaml`

```yaml
host: "0.0.0.0"
port: 8765
log_level: "INFO"

scheduler:
  enabled: true
  timezone: "Asia/Shanghai"

# 各模块配置（按模块扩展）
modules:
  news:
    enabled: true
    # 模块特定配置...
```

## API 路由

按模块扩展，每个模块注册自己的路由前缀：

### 基础接口

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/news/trigger` | POST | 手动触发新闻拉取任务 |

### 手动触发新闻拉取

**接口**：`POST /api/news/trigger`

**说明**：立即执行一次所有配置的 RSS 路由拉取任务

**响应**：
```json
{
  "success": true,
  "message": "新闻拉取任务已执行",
  "routes_processed": 4
}
```

**使用场景**：
- 调试和测试
- 手动触发即时拉取
- 验证配置是否正确

**示例**：
```bash
# 手动触发
curl -X POST http://localhost:8765/api/news/trigger

# 响应
{"success":true,"message":"新闻拉取任务已执行","routes_processed":4}
```

### 模块路由（规划）

| 模块 | 路由前缀 | 说明 |
|------|---------|------|
| news | `/api/v1/news` | 新闻订阅（待实现） |
| ... | ... | 后续模块 |

## 启动方式

```bash
uv run --env-file .env uvicorn openclaw_alpha.backend.main:app --reload --port 8765
```

## 模块扩展

每个模块目录包含：

```
{module}/
├── __init__.py         # 模块初始化，注册路由和任务
├── router.py           # FastAPI 路由
├── jobs.py             # 定时任务定义
├── config.py           # 模块配置模型
└── ...
```

**模块注册**（在 `main.py` 中）：

```python
from .news import router as news_router, setup_news_jobs

app.include_router(news_router, prefix="/api/v1/news")
setup_news_jobs(scheduler)
```

## 待办

- [ ] 新闻订阅模块（见 `news-subscription.md`）
- [ ] 后续模块扩展...
