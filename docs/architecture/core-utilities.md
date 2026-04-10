# 核心工具模块

> 更新日期：2026-04-10

OpenClaw-Alpha 的核心工具模块，提供统一配置、路径管理、数据处理等基础功能。

---

## 模块列表

### settings - 统一配置管理

**位置**：`src/openclaw_alpha/core/settings.py`

**用途**：统一配置入口，合并 `.env` 凭据和 `runtime/config.json` 功能配置。

#### 配置结构

```.env                     → 凭据（TUSHARE_TOKEN, DASHSCOPE_API_KEY, MILVUS_URI, MILVUS_TOKEN）
runtime/config.json      → 功能参数 + 调度配置（quick_news, feedback, event_review, iteration_loop）
```

#### 凭据属性

| 属性 | 环境变量 | 类型 | 必填 | 默认值 |
|------|----------|------|------|--------|
| `tushare_token` | `TUSHARE_TOKEN` | str | ✓ | - |
| `tushare_credit` | `TUSHARE_CREDIT` | int | ✗ | 0 |
| `dashscope_api_key` | `DASHSCOPE_API_KEY` | str | ✓ | - |
| `milvus_uri` | `MILVUS_URI` | str | ✓ | - |
| `milvus_token` | `MILVUS_TOKEN` | str | ✓ | - |

#### 功能配置属性

| 属性 | config.json 节 | 类型 |
|------|-----------------|------|
| `quick_news` | `quick_news` | dict |
| `feedback` | `feedback` | dict |
| `event_review` | `event_review` | dict |
| `project_root` | - | Path（支持 `OPENCLAW_ALPHA_ROOT` 覆盖） |

#### 使用示例

```python
from openclaw_alpha.core.settings import settings

# 读取凭据
token = settings.tushare_token

# 读取模块配置
cfg = settings.quick_news
enabled = cfg.get("enabled", True)
interval = cfg.get("interval_minutes", 30)

# 项目根目录
root = settings.project_root
```

#### 设计原则

1. **凭据与功能分离**：敏感信息只存 `.env`，不进 JSON
2. **零新依赖**：标准库 `json` + `os.getenv()`，无 pydantic-settings
3. **必填校验**：首次访问必填属性时抛出 `ValueError`

---

### path_utils - 路径管理工具

**位置**：`src/openclaw_alpha/core/path_utils.py`

**用途**：统一管理项目路径，避免硬编码路径。

#### 核心函数

| 函数 | 说明 | 返回值示例 |
|------|------|-----------|
| `get_project_root()` | 项目根目录 | `/home/.../OpenClaw-Alpha` |
| `get_config_dir()` | 配置目录 | `~/.openclaw_alpha` |
| `get_cache_dir()` | 缓存目录 | `~/.openclaw_alpha/cache` |
| `get_log_dir()` | 日志目录 | `~/.openclaw_alpha/logs` |
| `get_skills_dir()` | Skills 目录 | `{root}/skills` |
| `get_workspace_dir()` | 项目 runtime 目录 | `runtime` |
| `get_task_template_path(skill, task)` | 任务模板路径 | `{root}/skills/{skill}/tasks/{task}.md` |
| `get_news_analysis_task_dir(date, id)` | 新闻分析任务目录 | `runtime/news_analysis/{date}/{id}` |
| `ensure_dir(path)` | 确保目录存在 | Path 对象 |

#### 命名规范

| 术语 | 说明 | 示例 |
|------|------|------|
| **runtime** | 项目级工作目录 | `{project_root}/runtime/` |
| **task_dir** | 任务级工作目录 | `{runtime}/news_analysis/{date}/{news_id}/` |

**说明**：
- runtime 是项目级目录，用于存放各种任务的工作数据
- task_dir 根据任务类型不同，保存在 runtime 下的不同子目录

#### 路径定位策略

**优先级**：
1. 环境变量 `OPENCLAW_ALPHA_ROOT`
2. 从包路径推断（向上4级）

**环境变量配置**（`.env`）：
```bash
OPENCLAW_ALPHA_ROOT=/home/momojie/.openclaw/workspace/skills/OpenClaw-Alpha
```

#### 使用示例

```python
from openclaw_alpha.core.path_utils import (
    get_project_root,
    get_cache_dir,
    get_runtime_dir,
    get_news_analysis_task_dir,
    get_task_template_path,
    ensure_dir,
)

# 获取项目根目录
root = get_project_root()
# -> /home/momojie/.openclaw/workspace/skills/OpenClaw-Alpha

# 获取缓存目录
cache = get_cache_dir()
# -> /home/momojie/.openclaw_alpha/cache

# 获取 runtime 目录
workspace = get_runtime_dir()
# -> {root}/runtime

# 获取新闻分析任务目录
task_dir = get_news_analysis_task_dir("2026-03-11", "abc123")
# -> {runtime}/news_analysis/2026-03-11/abc123

# 获取任务模板路径
template = get_task_template_path("news_driven_investment", "quick-news-analysis")
# -> {root}/skills/news_driven_investment/tasks/quick-news-analysis.md

# 确保目录存在
ensure_dir(runtime)
```

#### 设计原则

1. **统一管理**：所有路径通过 `path_utils` 获取，避免到处硬编码
2. **环境变量优先**：明确的配置，可灵活调整
3. **自动推断 Fallback**：不配置也能用
4. **类型安全**：返回 `Path` 对象，便于路径操作

---

### processor_utils - Processor 工具

**位置**：`src/openclaw_alpha/core/processor_utils.py`

**用途**：Processor 输出文件管理。

#### 核心函数

| 函数 | 说明 |
|------|------|
| `get_output_path(skill, processor, date, ext)` | 获取 Processor 输出文件路径 |
| `load_output(skill, processor, date, ext)` | 读取 Processor 输出文件 |

#### 使用示例

```python
from openclaw_alpha.core.processor_utils import get_output_path, load_output

# 获取输出路径
output_path = get_output_path(
    skill_name="industry_trend",
    processor_name="concept_heat",
    date="2026-03-11",
    ext="json"
)
# -> runtime/.openclaw_alpha/industry_trend/2026-03-11/concept_heat.json

# 读取输出
data = load_output(
    skill_name="industry_trend",
    processor_name="concept_heat",
    date="2026-03-11"
)
```

---

## 使用场景

### 1. 获取配置文件路径

```python
from openclaw_alpha.core.path_utils import get_config_dir

config_path = get_config_dir() / "config" / "service.yaml"
```

### 2. 创建工作目录

```python
from openclaw_alpha.core.path_utils import get_cache_dir, ensure_dir

workspace = get_cache_dir() / "my_task" / "2026-03-11"
ensure_dir(workspace)
```

### 3. 加载任务模板

```python
from openclaw_alpha.core.path_utils import get_task_template_path

template_path = get_task_template_path("skill_name", "task_name")
content = template_path.read_text(encoding="utf-8")
```

---

## 最佳实践

### ✅ 应该做

- 使用 `path_utils` 获取所有路径
- 使用 `Path` 对象进行路径操作
- 使用 `ensure_dir()` 创建目录

### ❌ 不应该做

- 硬编码路径（如 `"/home/user/.openclaw_alpha"`）
- 使用字符串拼接路径（如 `dir + "/" + file`）
- 直接使用 `os.makedirs()`（使用 `ensure_dir()`）

---

## 扩展指南

### 添加新的路径函数

1. 在 `path_utils.py` 中添加函数
2. 在 `core/__init__.py` 中导出
3. 更新本文档

**示例**：
```python
# path_utils.py
def get_data_dir() -> Path:
    """获取数据目录"""
    return get_cache_dir() / "data"

# core/__init__.py
from .path_utils import get_data_dir

# core-utilities.md
添加到函数列表
```

---

## 参考资料

- [策略框架设计](strategy-framework.md)
- [开发规范](../standards/development-standard.md)
