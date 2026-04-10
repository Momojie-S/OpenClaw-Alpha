## REMOVED Requirements

### Requirement: Append review to news
**Reason**: 旧的 `--review` CLI 参数已删除。回顾机制改为事件级别的每日回顾，Agent 直接写 `responses/{date}.md` 文件。
**Migration**: 使用事件回顾功能替代，回顾内容写入 `data/events/{event_id}/responses/{date}.md`。

### Requirement: Review data structure
**Reason**: 不再使用 news.json 的 analysis.reviews[] 结构。回顾数据以 markdown 文件形式存储在事件目录下。
**Migration**: 回顾内容格式见任务模板 `event-reviews.md`。
