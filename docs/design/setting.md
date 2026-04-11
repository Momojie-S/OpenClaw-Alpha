# 全局配置设计

## 配置架构

```
.env                        ← 凭据（API keys、tokens）
runtime/config.json         ← 功能配置（模块开关、调度、优先级等）
```

- **凭据**：环境变量，通过 `core/settings.py` 的 `Settings` 类读取
- **功能配置**：`runtime/config.json`，各模块从 `settings` 获取自己的配置段

## runtime/config.json 结构

```jsonc
{
  // 服务部署配置
  "service": {
    "host": "0.0.0.0",
    "port": 8765,
    "log_level": "INFO"
  },

  // 全局默认值（agent_id/model/delivery 会被各模块继承）
  "defaults": { ... },

  // Tushare 配额
  "tushare": { ... },

  // 调度器配置（含任务队列）
  "scheduler": { ... },

  // 各功能模块
  "quick_news": { ... },
  "event_review": { ... },
  "feedback": { ... },
  "iteration_loop": { ... }
}
```

## 配置加载流程

```
Settings.__init__()
  ├── project_root = OPENCLAW_ALPHA_ROOT || 自动推断
  └── runtime/config.json → self._config (懒加载)

各模块通过 settings.xxx 获取配置段
  ├── settings.quick_news → _with_defaults(合并 defaults)
  ├── settings.feedback   → _with_defaults(合并 defaults)
  ├── settings.event_review → _with_defaults(合并 defaults)
  └── settings.tushare_config → 直接取
```

### defaults 继承机制

`defaults` 中的 `agent_id`、`model`、`delivery` 三个字段会被自动合并到各模块配置中（模块未显式设置时继承）。

## 配置管理 API

`/api/config/*` 提供运行时读写 `config.json` 的能力：

| 路由 | 说明 |
|------|------|
| `GET /api/config/iteration-loop` | 获取 Iteration Loop 配置 |
| `PUT /api/config/iteration-loop` | 更新 Iteration Loop 配置 |
| `GET /api/config/feedback` | 获取 Feedback 配置 |
| `PUT /api/config/feedback` | 更新 Feedback 配置 |

更新逻辑：读取 JSON → 合并字段 → 写回文件。不需要重启服务即可生效（模块下次加载配置时读取最新值）。

## 配置统一：废弃 service.yaml

所有配置统一到 `runtime/config.json`，不再使用 `service.yaml`。

```jsonc
{
  // 服务部署配置（原 service.yaml）
  "service": {
    "host": "0.0.0.0",
    "port": 8765,
    "log_level": "INFO"
  },

  // 调度器 + 任务队列
  "scheduler": {
    "enabled": true,
    "timezone": "Asia/Shanghai",
    "persistence_path": "task_queue.json",
    "default_priorities": { ... }
  },

  // ...其余模块
}
```

### 改造点

1. `backend/config.py`：`ServiceConfig` 改为从 `settings.service` 加载，不再读 YAML
2. `core/settings.py`：新增 `service` 和 `scheduler` 属性
3. 删除 `DEFAULT_CONFIG_DIR` 和 `load_config()` 的 YAML 加载逻辑
