## 1. 核心基类实现

- [x] 1.1 实现 DataFetcher 基类（core/fetcher.py）
- [x] 1.2 实现 FetcherRegistry（core/fetcher_registry.py）
- [x] 1.3 实现 DataProcessor 基类（core/processor.py）
- [x] 1.4 新增异常类（NoAvailableFetcherError, DuplicateFetcherError）

## 2. 核心基类单元测试

- [x] 2.1 DataFetcher 单元测试
- [x] 2.2 FetcherRegistry 单元测试
- [x] 2.3 DataProcessor 单元测试

## 3. Fetcher 实现迁移

- [x] 3.1 创建 fetchers 目录结构
- [x] 3.2 实现 ConceptBoard Tushare Fetcher
- [x] 3.3 实现 ConceptBoard AKShare Fetcher
- [x] 3.4 实现 SwIndustry Tushare Fetcher

## 4. Fetcher 单元测试

- [x] 4.1 ConceptBoard Fetcher 单元测试
- [x] 4.2 SwIndustry Fetcher 单元测试

## 5. Processor 实现

- [x] 5.1 创建 processors 目录结构
- [x] 5.2 实现 IndustryTrend Processor

## 6. Processor 单元测试

- [x] 6.1 IndustryTrend Processor 单元测试

## 7. 命令层迁移

- [ ] 7.1 更新 board_concept 命令使用 Fetcher
- [ ] 7.2 更新 sw_industry 命令使用 Processor

## 8. 文档更新

- [ ] 8.1 更新 strategy-framework.md 合并新设计
- [ ] 8.2 删除 strategy-refactor.md 设计文档（已合并）

## 9. 清理

- [ ] 9.1 移除废弃的 Strategy 实现代码
- [ ] 9.2 代码 Review
