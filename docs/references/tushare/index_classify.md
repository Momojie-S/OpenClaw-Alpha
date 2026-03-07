# 申万行业分类 - index_classify

> 更新日期：2026-03-06
> 来源地址：https://tushare.pro/document/2?doc_id=181

---

## 官方说明

接口：index_classify

描述：获取申万行业分类，可以获取申万2014年版本（28个一级分类，104个二级分类，227个三级分类）和2021年本版（31个一级分类，134个二级分类，346个三级分类）列表信息

权限：用户需2000积分可以调取

### 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|:----:|------|
| index_code | str | N | 指数代码 |
| level | str | N | 行业分级（L1/L2/L3） |
| parent_code | str | N | 父级代码（一级为0） |
| src | str | N | 指数来源（SW2014：申万2014年版本，SW2021：申万2021年版本） |

### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
|------|------|:--------:|------|
| index_code | str | Y | 指数代码 |
| industry_name | str | Y | 行业名称 |
| parent_code | str | Y | 父级代码 |
| level | str | Y | 行业层级 |
| industry_code | str | Y | 行业代码 |
| is_pub | str | Y | 是否发布了指数 |
| src | str | N | 行业分类（SW申万） |

### 接口示例

```python
# 获取申万一级行业列表
df = pro.index_classify(level='L1', src='SW2021')

# 获取申万二级行业列表
df = pro.index_classify(level='L2', src='SW2021')

# 获取申万三级行业列表
df = pro.index_classify(level='L3', src='SW2021')
```

### 数据示例

```
index_code  industry_name  level
801020.SI   采掘           L1
801030.SI   化工           L1
801040.SI   钢铁           L1
801050.SI   有色金属       L1
801710.SI   建筑材料       L1
...
```

---

## 额外说明

### 积分要求

- 2000 积分

### 版本说明

- **SW2014**：28个一级、104个二级、227个三级
- **SW2021**：31个一级、134个二级、346个三级（推荐使用）

### 注意事项

- 指数成分股小于5条该指数行情不发布（`is_pub=0`）
- 使用 `parent_code` 可以查询子级行业
