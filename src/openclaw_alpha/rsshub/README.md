# RSSHub 工具模块

统一的 RSSHub 实例管理和 RSS 文章提取工具。

## 功能

- **实例管理**：维护可用的 RSSHub 公共实例列表
- **自动切换**：失败自动尝试下一个实例
- **统一提取**：提供统一的 RSS 文章提取接口

## 使用方法

### 基本使用

```python
from openclaw_alpha.rsshub import fetch_with_fallback, INVESTMENT_ROUTES

# 拉取单个路由
instance, items = fetch_with_fallback("/cls/telegraph")
print(f"成功实例: {instance}")
print(f"获取 {len(items)} 条新闻")

# 使用预定义的投资相关路由
for route in INVESTMENT_ROUTES:
    instance, items = fetch_with_fallback(route)
    # 处理新闻...
```

### 批量拉取

```python
from openclaw_alpha.rsshub import fetch_all_routes, INVESTMENT_ROUTES

# 批量拉取多个路由
results = fetch_all_routes(INVESTMENT_ROUTES)

for route, (instance, items) in results.items():
    print(f"{route}: 从 {instance} 获取 {len(items)} 条")
```

### 自定义实例

```python
from openclaw_alpha.rsshub import fetch_with_fallback

# 使用自定义实例列表
custom_instances = [
    "https://your-rsshub-instance.com",
    "https://another-instance.com",
]

instance, items = fetch_with_fallback("/cls/telegraph", instances=custom_instances)
```

## 数据结构

### RSSItem

```python
@dataclass
class RSSItem:
    id: str              # 文章唯一标识
    title: str           # 标题
    link: str            # 链接
    published: datetime | None  # 发布时间
    summary: str | None  # 文章内容（feedparser 标准字段名）
```

**summary 字段说明**：

- **来源**：feedparser 标准字段名 `entry.get("summary")`，对应 RSSHub JSON Feed 的 `content_html`
- **实际内容**：取决于数据源
  - 完整正文（部分源）
  - 摘要（大多数源）
  - 简短内容（快讯类）
- **示例**：
  - `wallstreetcn/news`: 248 字符（摘要 + 免责声明）
  - `jin10`: 279 字符（较详细的摘要）

## 配置

### 实例列表

在 `instances.py` 中维护：

```python
RSSHUB_INSTANCES = [
    "https://rsshub.liumingye.cn",
    # "https://rsshub.app",  # 官方实例已限制访问
]
```

### 投资相关路由

```python
INVESTMENT_ROUTES = [
    "/cls/telegraph",      # 财联社电报快讯
    "/jin10",              # 金十数据快讯
    "/wallstreetcn/news",  # 华尔街见闻资讯
    "/yicai/brief",        # 第一财经简报
]
```

## 注意事项

1. **优先级顺序**：实例和路由都按优先级排序，靠前的优先使用
2. **自动切换**：某个实例失败会自动尝试下一个
3. **限制检测**：自动检测 RSSHub 公共实例的访问限制提示
