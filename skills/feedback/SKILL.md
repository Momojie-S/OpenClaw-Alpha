---
name: openclaw_alpha_feedback
description: "用户反馈收集。适用于：在使用 openclaw_alpha_xxx skill 时提交改进建议、报告 bug、提出新功能需求。不适用于：实时反馈、紧急问题、技术讨论。"
metadata:
  openclaw:
    emoji: "💬"
    requires:
      bins: []
---

# 用户反馈收集

收集用户对 OpenClaw-Alpha 技能的反馈意见。

## 使用说明

### 触发方式

**显式调用**：
```
提交反馈：{反馈内容}
```

**隐式识别**：
用户提出反馈性建议时自动触发。

### 脚本运行

```bash
uv run --env-file .env python -m openclaw_alpha.backend.feedback.submit_feedback \
  --content "反馈内容" \
  --source-user "用户名" \
  --source-channel "渠道" \
  --source-session "session:key"
```

### 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--content` | ✅ | 反馈内容 |
| `--source-user` | 可选 | 提交用户（从 inbound metadata 获取） |
| `--source-channel` | 可选 | 提交渠道（wecom、telegram 等） |
| `--source-session` | 可选 | 来源 session key（处理完成后用于发送结果消息） |

**注意**：`source_user`、`source_channel`、`source_session` 均为可选参数。系统反馈（非用户提交）可以不提供这些参数。

### 输出

```
✅ 反馈已保存
  ID: abc123...
  路径: feedback/2026-03-17-abc123.json
```

## 反馈 JSON 格式

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "source_session": "wecom-agent:alpha:user:Momojie",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "content": "反馈原文内容...",
  "status": "pending"
}
```

## 后续处理

- Backend 每 30 分钟扫描一次 `feedback/` 目录
- 自动触发 Agent Session 处理反馈
- 处理结果会更新到 JSON 文件
- 处理完成后，通过 `source_session` 发送结果消息给提出者

## 注意事项

- 反馈会记录用户身份、来源 session 和内容
- source_session 用于处理完成后发送结果消息
- 处理过程可能需要数小时到数天
- 处理结果会更新到反馈文件并通过 session 发送给用户
- 不适用于实时反馈、紧急问题（如需要立即响应的问题请直接说明）
