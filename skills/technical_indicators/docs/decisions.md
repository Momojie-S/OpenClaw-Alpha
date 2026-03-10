# 决策记录 - technical_indicators

## 调研

### 技术指标计算库

**TA-Lib vs 自己实现**：
- TA-Lib：C 语言实现，性能高，算法标准
- 自己实现：灵活但容易出错

**决策**：使用 TA-Lib

### 数据源

**AKShare vs Tushare**：
- AKShare：免费，稳定，历史数据完整
- Tushare：需要积分，但数据更规范

**决策**：AKShare 为主，Tushare 备用

## 决策

### 为什么分两个 Processor？

- `indicator_processor`：技术指标分析（趋势、动量）
- `volume_price_processor`：量价关系分析

**原因**：
1. 职责分离，便于维护
2. 用户可能只想看其中一个
3. 量价分析不需要 TA-Lib

### 为什么支持信号输出？

**原因**：
1. 支持回测框架
2. 历史信号可追溯
3. 便于策略验证

## 踩坑

### TA-Lib 安装问题

**现象**：pip install TA-Lib 失败

**原因**：需要先安装 C 语言依赖

**解决**：先编译安装 ta-lib C 库，再 pip install

### 数据对齐问题

**现象**：指标计算结果和预期不符

**原因**：TA-Lib 输出长度与输入不同

**解决**：使用 DataFrame 对齐，填充 NaN

### 最小数据要求

**现象**：数据太少时指标计算失败

**原因**：部分指标需要足够的历史数据

**解决**：至少需要 30 天数据，提前校验
