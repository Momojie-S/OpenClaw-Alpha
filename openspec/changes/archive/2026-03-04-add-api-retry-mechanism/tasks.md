## 1. 依赖配置

- [x] 1.1 添加 tenacity 依赖到 pyproject.toml

## 2. 异常类定义

- [x] 2.1 在 `src/openclaw_alpha/core/exceptions.py` 中定义 `RetryableError` 基类
- [x] 2.2 定义可重试异常：RateLimitError、TimeoutError、ServerError、NetworkError
- [x] 2.3 定义不可重试异常：AuthenticationError、PermissionError、NotFoundError、ValidationError

## 3. 现有 Fetcher 改造

- [x] 3.1 重构 `ConceptBoardTushareFetcher`：分离 API 请求方法，添加 `@retry` 装饰器
- [x] 3.2 重构 `ConceptBoardAKShareFetcher`：分离 API 请求方法，添加 `@retry` 装饰器
- [x] 3.3 重构 `SwIndustryTushareFetcher`：分离 API 请求方法，添加 `@retry` 装饰器

## 4. 测试

- [x] 4.1 真实调试 ConceptBoardTushareFetcher API 请求
- [x] 4.2 真实调试 ConceptBoardAKShareFetcher API 请求
- [x] 4.3 真实调试 SwIndustryTushareFetcher API 请求
