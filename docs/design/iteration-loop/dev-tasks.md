# dev_tasks 子模块设计

## 概述

`dev_tasks` 是 Iteration Loop 的开发任务处理子模块，负责自动扫描和处理 OpenSpec changes。

---

## 架构

```
iteration_loop/
└── dev_tasks/
    └── __init__.py          # process(limit) -> bool
```

---

## 核心逻辑

### 1. 扫描 OpenSpec Changes

```python
def _run_openspec_list() -> list[str]:
    # 调用 openspec list --json
    # 返回活跃的 change 名称列表
```

### 2. 检查完整性

```python
def _check_change_completeness(change_name: str) -> bool:
    # 检查 change 是否完整：
    # 1. 有 proposal.md
    # 2. 有 design.md
    # 3. 有 specs/ 目录且至少一个 spec 文件
    # 4. 有 tasks.md 且包含未完成的 [ ] 任务
```

### 3. 过滤完整 Changes

```python
def _find_complete_changes() -> list[str]:
    # 从活跃 changes 中过滤出完整的
```

### 4. 随机选择

```python
def _select_random_change(changes: list[str]) -> str | None:
    # 随机选择一个 change
```

### 5. 触发 Agent

```python
async def process(limit: int = 1) -> bool:
    # 找到一个完整的 change
    change_name = _select_random_change(_find_complete_changes())
    
    # 构造消息
    message = _build_message(change_name)
    
    # 触发 Agent
    result = await submit_cron_task(message, ...)
    return result.success
```

---

## 消息模板

```markdown
使用 OpenSpec apply 流程完成 change {change_name}
```

---

## 与旧实现的对比

| 维度 | 旧实现 | 新实现 |
|------|--------|--------|
| 数据来源 | `progress/*.md` | `openspec list --json` |
| 状态判断 | 解析 `## 状态` 部分 | 检查 tasks.md 中 `[ ]` |
| 完成标记 | `当前阶段：完成/Phase 7` | tasks.md 全部 `[x]` |
| 消息格式 | 引用 development-workflow | OpenSpec apply 流程 |

---

## 配置

- `OPENSPEC_PROJECT_DIR`: OpenSpec 项目目录
- `SESSION_POLL_INTERVAL_SECONDS`: Session 轮询间隔（30s）
- `SESSION_INACTIVE_THRESHOLD_SECONDS`: Session 不活跃阈值（120s）

---

## 错误处理

1. `openspec` CLI 未安装 → 返回空列表，不报错
2. JSON 解析失败 → 返回空列表，记录警告
3. CLI 执行超时 → 返回空列表，记录错误
4. Agent 提交失败 → 返回 False，主循环继续

---

## 状态

- [x] 设计文档更新
- [x] `dev_tasks/__init__.py` 重构
- [x] 测试验证（22 个测试用例通过）
