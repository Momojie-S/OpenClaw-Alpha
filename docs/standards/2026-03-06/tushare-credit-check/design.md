# Tushare 积分校验 - 设计文档

## 设计目标

在现有架构上扩展积分校验能力，保持向后兼容。

## 异常类设计

扩展现有异常类：

```
OpenclawAlphaError
└── DataSourceUnavailableError (新增基类)
    ├── MissingConfigError      - 配置缺失（token 等）
    └── InsufficientCreditError - 积分不足
```

### DataSourceUnavailableError

```python
class DataSourceUnavailableError(OpenclawAlphaError):
    """数据源不可用异常基类"""
    data_source_name: str  # 数据源名称
    reason: str            # 具体原因
```

### MissingConfigError

```python
class MissingConfigError(DataSourceUnavailableError):
    """配置缺失异常"""
    missing_keys: list[str]  # 缺失的环境变量
```

### InsufficientCreditError

```python
class InsufficientCreditError(DataSourceUnavailableError):
    """积分不足异常"""
    required: int   # 需要的积分
    actual: int     # 实际积分
```

## TushareDataSource 扩展

### 新增属性

```python
class TushareDataSource(DataSource):
    def __init__(self):
        super().__init__(
            name="tushare",
            required_config=["TUSHARE_TOKEN"],  # token 仍需配置
        )
        self._credit: int | None = None  # 懒加载
    
    @property
    def credit(self) -> int:
        """获取用户积分（懒加载）"""
        if self._credit is None:
            credit_str = os.getenv("TUSHARE_CREDIT", "0")
            self._credit = int(credit_str)
        return self._credit
```

## FetchMethod 扩展

### 新增属性

```python
class FetchMethod(ABC):
    required_credit: int = 0  # 需要的积分，默认 0
```

### is_available() 修改

返回值改为 `tuple[bool, DataSourceUnavailableError | None]`：
- `(True, None)` - 可用
- `(False, error)` - 不可用，附带失败原因

```python
def is_available(self) -> tuple[bool, DataSourceUnavailableError | None]:
    """
    检查方法是否可用。
    
    Returns:
        (是否可用, 失败原因)
    """
    data_source = DataSourceRegistry.get(self.required_data_source)
    
    # 检查数据源配置
    if not data_source.is_available():
        return (False, MissingConfigError(
            data_source_name=self.required_data_source,
            missing_keys=data_source.required_config,
        ))
    
    # 检查积分（仅 Tushare）
    if self.required_credit > 0:
        if hasattr(data_source, "credit") and data_source.credit < self.required_credit:
            return (False, InsufficientCreditError(
                data_source_name=self.required_data_source,
                required=self.required_credit,
                actual=data_source.credit,
            ))
    
    return (True, None)
```

## Fetcher 修改

### _select_available() 修改

收集所有失败原因：

```python
def _select_available(self) -> tuple[FetchMethod | None, list[DataSourceUnavailableError]]:
    """
    选择数据源可用的方法。
    
    Returns:
        (可用方法, 所有失败原因)
    """
    errors: list[DataSourceUnavailableError] = []
    
    # 按优先级排序
    sorted_methods = sorted(self._methods, key=lambda m: m.priority, reverse=True)
    
    for method in sorted_methods:
        available, error = method.is_available()
        if available:
            return (method, errors)
        if error:
            errors.append(error)
    
    return (None, errors)
```

### fetch() 修改

全部失败时整合异常信息：

```python
async def fetch(self, *args, **kwargs):
    method, errors = self._select_available()
    
    if method is None:
        # 整合所有失败原因
        error_msgs = []
        for err in errors:
            if isinstance(err, MissingConfigError):
                error_msgs.append(f"{err.data_source_name}: 缺少配置 {err.missing_keys}")
            elif isinstance(err, InsufficientCreditError):
                error_msgs.append(
                    f"{err.data_source_name}: 积分不足（需要 {err.required}，实际 {err.actual}）"
                )
            else:
                error_msgs.append(f"{err.data_source_name}: {err.reason}")
        
        raise NoAvailableMethodError(
            f"所有数据源均不可用:\n" + "\n".join(f"  - {msg}" for msg in error_msgs)
        )
    
    return await method.fetch(*args, **kwargs)
```

## 使用示例

### 声明积分要求

```python
class ConceptFetcherTushare(FetchMethod):
    name = "concept_tushare"
    required_data_source = "tushare"
    required_credit = 120  # 申万行业指数需要 120 积分
    priority = 10
```

### 异常信息示例

```
NoAvailableMethodError: 所有数据源均不可用:
  - tushare: 积分不足（需要 120，实际 100）
  - akshare: 缺少配置 ['AKSHARE_TOKEN']
```

## 向后兼容

- `required_credit` 默认为 0，现有 FetchMethod 无需修改
- `is_available()` 返回值改为 tuple，但调用方通过解构使用，兼容性好
- 异常类继承自 `OpenclawAlphaError`，与现有异常体系兼容

## 文件修改清单

| 文件 | 修改内容 |
|------|---------|
| `src/openclaw_alpha/core/exceptions.py` | 新增 3 个异常类 |
| `src/openclaw_alpha/core/fetcher.py` | `FetchMethod.is_available()` 返回值修改，`Fetcher._select_available()` 和 `fetch()` 修改 |
| `src/openclaw_alpha/data_sources/tushare.py` | 新增 `credit` 属性 |
| `tests/core/test_fetcher.py` | 新增积分校验测试用例 |
| `tests/core/test_data_source.py` | 新增 TushareDataSource.credit 测试 |
