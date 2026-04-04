# openspec-task-scanner

## Purpose

扫描活跃的 OpenSpec changes，过滤出完整的 change，随机选择一个用于后续处理。

这是 dev_tasks 模块的核心能力，用于替代原来的 progress/ 文件扫描。

---

## Requirements

### Requirement: Scan Active Changes

系统 SHALL 调用 `openspec list --json` 获取所有活跃的（非归档）changes。

#### Scenario: Active changes exist
- **WHEN** openspec/changes/ 目录下有活跃的 change 目录
- **THEN** 系统返回 JSON 数组，包含所有活跃 change 名称

#### Scenario: No active changes
- **WHEN** openspec/changes/ 目录为空或只包含 archive
- **THEN** 系统返回空数组 `{"changes": []}`

### Requirement: Filter Complete Changes

系统 SHALL 过滤出"完整的" change。

完整性标准：
1. 有 `proposal.md` 文件
2. 有 `design.md` 文件
3. 有 `specs/` 目录且至少包含一个 spec 文件
4. 有 `tasks.md` 文件且包含未完成的 `[ ]` 任务

#### Scenario: Complete change with all artifacts
- **WHEN** change "add-api-retry" 包含 proposal.md, design.md, specs/api-retry/spec.md, tasks.md（有 `[ ]` 任务）
- **THEN** 系统将该 change 列入完整列表

#### Scenario: Incomplete change missing tasks
- **WHEN** change "wip-feature" 有 proposal.md, design.md, specs/ 但没有 tasks.md
- **THEN** 系统不将该 change 列入完整列表

#### Scenario: Complete change but all tasks done
- **WHEN** change "finished-feature" 所有文件都有，但 tasks.md 中所有任务都是 `[x]`
- **THEN** 系统不将该 change 列入完整列表（因为没有待完成任务）

### Requirement: Select Change Randomly

系统 SHALL 从完整的 changes 中随机选择一个。

#### Scenario: Multiple complete changes
- **WHEN** 有 3 个完整的 changes: ["add-api-retry", "fix-bug", "new-feature"]
- **THEN** 系统使用 `random.choice()` 随机选择其中一个

#### Scenario: Single complete change
- **WHEN** 只有 1 个完整的 change
- **THEN** 系统选择该 change

#### Scenario: No complete changes
- **WHEN** 没有完整的 change
- **THEN** 系统返回 None

### Requirement: Build OpenSpec Apply Message

系统 SHALL 构造消息触发 OpenSpec apply 流程。

消息格式：`使用 OpenSpec apply 流程完成 change {change_name}`

#### Scenario: Build message for selected change
- **WHEN** 选中 change 名称为 "add-api-retry-mechanism"
- **THEN** 消息内容为：`使用 OpenSpec apply 流程完成 change add-api-retry-mechanism`

### Requirement: Handle Failures Gracefully

系统 SHALL 在 CLI 调用失败时优雅处理，跳过当前任务。

#### Scenario: openspec CLI not found
- **WHEN** `openspec` 命令不存在或执行失败
- **THEN** 系统捕获异常，记录日志，返回 False

#### Scenario: JSON parse error
- **WHEN** CLI 输出不是有效 JSON
- **THEN** 系统捕获异常，记录日志，返回 False
