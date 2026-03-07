# 任务：预警推送系统开发

## 需求

基于已完成的预警推送系统设计文档（docs/research/alert-push-system-design.md），开发 alert_monitor skill。

**核心功能**：
1. 持仓风险预警（业绩暴雷、连续下跌、资金流出）
2. 市场异动监控（北向资金、板块热度）
3. 综合风险扫描报告
4. 支持配置化推送

## Phase 1: 开发
- [x] 创建 alert_monitor skill 目录
- [x] 实现配置文件解析（config_parser）
- [x] 实现持仓风险检测器（risk_scanner）
- [x] 实现市场异动检测器（market_scanner）
- [x] 实现综合扫描处理器（alert_processor）
- [x] 编写 SKILL.md

## Phase 2: 测试
- [x] 编写单元测试 - 25 个测试
- [x] 运行测试 - 491 passed

## Phase 3: 集成
- [x] 更新分析框架文档
- [ ] 配置 cron 任务（需用户手动配置）

## Phase 4: 提交
- [x] git commit
- [x] git push

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 06:45

## 完成总结

### 新增 Skill

**alert_monitor** - 预警推送系统

**功能**：
1. 配置化监控标的（alert_config.yaml）
2. 持仓风险扫描（复用 risk_alert）
3. 市场异动监控（北向资金、板块热度）
4. 综合预警报告（简报/完整两种模式）

**命令**：
```bash
# 综合扫描
uv run --env-file .env python -m skills.alert_monitor.scripts.alert_processor.alert_processor

# 仅风险扫描
uv run --env-file .env python -m skills.alert_monitor.scripts.alert_processor.alert_processor --type risk

# 仅市场扫描
uv run --env-file .env python -m skills.alert_monitor.scripts.alert_processor.alert_processor --type market

# 简报模式
uv run --env-file .env python -m skills.alert_monitor.scripts.alert_processor.alert_processor --brief
```

**配置文件**：
- 位置：`~/.openclaw/workspace-alpha/alert_config.yaml`
- 内容：自选股列表、预警规则、阈值设置

### 测试

- 新增 25 个测试
- 总测试数：491 passed

### 分析框架更新

- 添加"预警层"到分析层次
- P2 高级功能全部完成

## 备注
开始时间：2026-03-08 06:30
完成时间：2026-03-08 06:45
