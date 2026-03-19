# dev_tasks 子模块设计

## 概述

`dev_tasks` 是 Iteration Loop 的开发任务处理子模块，负责自动扫描和处理进度文件中的开发任务。

---

## 架构

```
iteration_loop/
└── dev_tasks/
    └── __init__.py          # process(limit) -> bool
```

---

## 核心逻辑

### 1. 扫描进度文件

```python
def _scan_progress_files() -> list[Path]:
    # 扫描 workspace/../progress/*.md
```

### 2. 解析状态

用正则匹配进度文件中的状态字段：

```python
# 完成状态
COMPLETED_PATTERN = r"当前阶段[：:]\s*(完成|Phase\s*7)"

# 进行中状态
IN_PROGRESS_PATTERN = r"当前阶段[：:]\s*Phase\s*([0-6])"
```

### 3. 判断是否需要处理

```python
def _is_pending(file_path: Path) -> bool:
    # 匹配完成状态，如果匹配到则不需要处理
    content = file_path.read_text()
    return not COMPLETED_PATTERN.search(content)
```

### 4. 触发 Agent

```python
async def process(limit: int = 1) -> bool:
    # 找到一个待处理任务
    task = _find_pending_task()
    if not task:
        return False

    # 构造消息
    message = _build_message(task["path"])

    # 触发 Agent
    result = await submit_cron_task(message, ...)
    return result.success
```

---

## 消息模板

```markdown
请按照开发任务流程（development-workflow）继续完成任务。

进度文件：{progress_path}

这是从上次进度继续。开始前请：
1. 重新阅读项目结构（project-overview.md）
2. 阅读相关设计文档
3. 读取进度文件了解当前状态
4. 继续执行待完成任务

完成后请更新进度文件。
```

---

## 与 feedback 模块的对比

| 维度 | feedback | dev_tasks |
|------|----------|-----------|
| 数据格式 | JSON | Markdown |
| 数据目录 | `workspace/feedback/new/` | `workspace/../progress/` |
| 状态字段 | `status: pending/processing/processed` | `当前阶段：Phase X/完成` |
| 完成标记 | `status: processed` + 移动到 done/ | `当前阶段：完成/Phase 7` |
| 任务执行 | Agent 更新 JSON + 归档 | Agent 更新 Markdown |
| 超时时间 | 300s | 600s（开发任务更长） |

---

## 配置

复用 Iteration Loop 主模块配置，无独立配置。

---

## 错误处理

1. 进度目录不存在 → 返回空列表，不报错
2. 进度文件解析失败 → 跳过该文件，记录警告
3. Agent 提交失败 → 返回 False，主循环继续

---

## 待实现

- [x] 设计文档
- [ ] `dev_tasks/__init__.py` 实现
- [ ] 主模块集成
- [ ] 测试验证
