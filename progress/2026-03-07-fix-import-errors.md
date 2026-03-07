# 任务：修复测试导入问题

## 问题描述

在运行测试时遇到导入错误：
```
ModuleNotFoundError: No module named 'skills.industry_trend'
```

## 根本原因

1. **目录名包含连字符**：`industry-trend` 包含 `-`，但 Python 模块名不能包含连字符
2. **错误的导入路径**：`DataSourceRegistry` 从错误的模块导入
3. **Fetcher 初始化错误**：调用 `super().__init__(name=self.name)` 但父类不接受参数

## 修复步骤

### 1. 重命名目录

```bash
mv skills/industry-trend skills/industry_trend
mv tests/skills/industry-trend tests/skills/industry_trend
```

### 2. 修复导入路径

**错误**：
```python
from openclaw_alpha.core.data_source import DataSourceRegistry
```

**正确**：
```python
from openclaw_alpha.core.registry import DataSourceRegistry
```

修改文件：
- `skills/industry_trend/scripts/industry_fetcher/tushare.py`
- `skills/industry_trend/scripts/concept_fetcher/akshare.py`

### 3. 修复 Fetcher 初始化

**错误**：
```python
def __init__(self):
    super().__init__(name=self.name)
```

**正确**：
```python
def __init__(self):
    super().__init__()
```

修改文件：
- `skills/industry_trend/scripts/industry_fetcher/industry_fetcher.py`
- `skills/industry_trend/scripts/concept_fetcher/concept_fetcher.py`

### 4. 添加测试路径配置

在 `pytest.ini` 中添加：
```ini
pythonpath = . src skills
```

在 `tests/conftest.py` 中动态添加路径：
```python
project_root = Path(__file__).parent
skills_dir = project_root / "skills"
src_dir = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(skills_dir) not in sys.path:
    sys.path.insert(0, str(skills_dir))

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
```

## 验证结果

```bash
$ uv run --env-file .env pytest tests/skills/industry_trend/ -v
===================================== test session starts ==============================
...
=============================== 13 passed in 0.05s ===============================
```

## 经验教训

1. **Python 模块名规范**：必须使用下划线 `_`，不能使用连字符 `-`
2. **单例模式注册表**：避免重复注册，测试时需要重置
3. **导入路径一致性**：确认基类和注册表的正确位置

## 下一步

继续完成 IndustryTrendProcessor 测试
