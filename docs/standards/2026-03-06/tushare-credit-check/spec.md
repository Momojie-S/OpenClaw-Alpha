# Tushare 积分校验 - 需求文档

## 背景

Tushare 数据源有积分要求，不同接口需要不同积分。当前只校验 token 是否存在，无法判断用户积分是否满足接口要求。

## 需求

### 积分配置

- 用户积分通过环境变量 `TUSHARE_CREDIT` 配置
- 未配置时默认为 0

### 积分要求声明

- 每个 Tushare FetchMethod 声明 `required_credit` 属性
- `required_credit = 0` 表示需要 token 但无积分要求
- `required_credit = N` 表示需要 token 且积分 ≥ N

### 权限校验

校验时机：`FetchMethod.is_available()` 检查时

校验条件：
1. `TUSHARE_TOKEN` 存在
2. 用户积分 ≥ `required_credit`

### 异常处理

校验失败时：
1. FetchMethod 抛出明确的异常，说明失败原因
2. Fetcher 捕获异常，尝试下一个 Method
3. 全部失败时，抛出 `NoAvailableMethodError`，附带所有失败原因

### 失败原因类型

| 原因 | 说明 |
|------|------|
| Token 缺失 | `TUSHARE_TOKEN` 未配置 |
| 积分不足 | 用户积分 < required_credit |
| 数据源不可用 | 其他原因（网络、服务异常等） |

## 验收标准

- [ ] TushareDataSource 读取 `TUSHARE_CREDIT` 环境变量
- [ ] FetchMethod 可声明 `required_credit` 属性
- [ ] `is_available()` 校验 token + 积分
- [ ] 校验失败抛出明确异常
- [ ] Fetcher 整合所有失败原因
- [ ] 异常信息清晰，便于排查
