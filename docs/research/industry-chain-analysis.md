# 产业链分析研究

> 研究日期：2026-03-08
> 研究目的：探索产业链分析的数据源和实现方案

---

## 需求分析

### 用户场景

1. **行业研究**
   - 了解某个行业的上下游关系
   - 识别产业链中的关键公司
   - 分析产业传导逻辑

2. **投资决策**
   - 找到产业链中受益最大的环节
   - 判断原材料涨价对下游的影响
   - 识别替代品风险

### 功能需求

| 功能 | 描述 | 优先级 |
|------|------|:------:|
| 产业链图谱 | 展示行业上下游关系 | P0 |
| 关键公司 | 产业链各环节的龙头公司 | P0 |
| 传导分析 | 价格/供需传导逻辑 | P1 |
| 关联强度 | 上下游关联程度 | P2 |

---

## 数据源调研

### AKShare

**结论**：无直接产业链接口

相关接口：
- `stock_board_industry_*` - 行业板块数据（行情、成分股）
- `stock_industry_category_cninfo` - 行业分类
- 不提供产业链上下游关系

### Tushare

**结论**：无直接产业链接口

### 东方财富

**观察**：东方财富 APP 有"产业链"功能，但 API 未公开

**浏览器调研结果**：
- 访问东方财富产业链页面需要登录
- 数据以图表形式展示，无直接 API

### 同花顺

**观察**：同花顺 iFinD 有产业链数据，但需要付费

---

## 替代方案

### 方案 A：静态知识库

**思路**：维护产业链关系知识库

**优点**：
- 不依赖外部 API
- 可以人工校验

**缺点**：
- 维护成本高
- 更新不及时

**实现**：
```yaml
# data/industry_chain.yaml
semiconductor:  # 半导体
  upstream:
    - name: 硅片
      companies: ["沪硅产业", "TCL中环"]
    - name: 光刻胶
      companies: ["南大光电", "晶瑞电材"]
  midstream:
    - name: 晶圆制造
      companies: ["中芯国际", "华虹公司"]
    - name: 封装测试
      companies: ["长电科技", "通富微电"]
  downstream:
    - name: 消费电子
      companies: ["立讯精密", "歌尔股份"]
    - name: 汽车
      companies: ["比亚迪", "宁德时代"]
```

### 方案 B：浏览器抓取

**思路**：使用 browser 抓取东方财富产业链页面

**优点**：
- 数据实时
- 覆盖面广

**缺点**：
- 依赖页面结构
- 可能触发反爬

### 方案 C：LLM 生成

**思路**：使用大模型生成产业链知识

**优点**：
- 灵活性高
- 可以结合最新信息

**缺点**：
- 准确性需验证
- 可能产生幻觉

---

## 推荐方案

### 短期（MVP）

**方案 A + C 结合**：
1. 维护核心行业的产业链知识库（5-10 个热门行业）
2. 使用 LLM 补充细节
3. 人工校验关键信息

### 长期

**方案 B**：
- 开发浏览器抓取 skill
- 定期更新产业链数据

---

## 实现步骤

### Phase 1: 知识库构建

- [ ] 设计产业链数据格式
- [ ] 收集核心行业产业链信息
- [ ] 建立知识库文件

### Phase 2: 查询接口

- [ ] 开发产业链查询 Fetcher
- [ ] 实现上下游关联查询
- [ ] 返回结构化数据

### Phase 3: 可视化（可选）

- [ ] 产业链图谱展示
- [ ] 关键节点标注

---

## 数据格式设计

### 产业链节点

```python
@dataclass
class IndustryChainNode:
    """产业链节点"""
    name: str           # 环节名称
    level: str          # upstream/midstream/downstream
    companies: list[str]  # 相关公司
    description: str | None = None  # 描述
```

### 产业链数据

```python
@dataclass
class IndustryChain:
    """产业链数据"""
    industry: str       # 行业名称
    nodes: list[IndustryChainNode]  # 各环节节点
    relations: list[tuple[str, str]]  # 节点间关系
    
    def get_upstream(self) -> list[IndustryChainNode]:
        """获取上游"""
        return [n for n in self.nodes if n.level == "upstream"]
    
    def get_downstream(self) -> list[IndustryChainNode]:
        """获取下游"""
        return [n for n in self.nodes if n.level == "downstream"]
```

---

## 示例：半导体产业链

```
上游（原材料）
├── 硅片：沪硅产业、TCL中环
├── 光刻胶：南大光电、晶瑞电材
├── 特种气体：华特气体、金宏气体
└── 掩膜版：清溢光电、菲利华

中游（制造）
├── 设计：韦尔股份、兆易创新
├── 制造：中芯国际、华虹公司
└── 封测：长电科技、通富微电

下游（应用）
├── 消费电子：立讯精密、歌尔股份
├── 通信：中兴通讯、烽火通信
├── 汽车：比亚迪、宁德时代
└── 工业：汇川技术、信捷电气
```

---

## 结论

1. **数据源现状**：主流免费 API 无产业链数据
2. **推荐方案**：静态知识库 + LLM 补充
3. **优先级**：P3（低优先级，可延后）
4. **替代思路**：可以先用 LLM 按需生成产业链分析

---

## 参考资料

- [东方财富 - 产业链分析](https://data.eastmoney.com/)
- [同花顺 - 行业研究](https://www.10jqka.com.cn/)
