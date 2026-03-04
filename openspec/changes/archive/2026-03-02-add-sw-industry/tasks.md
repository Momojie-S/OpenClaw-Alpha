## 1. 申万行业指数脚本开发

- [x] 1.1 创建 src/openclaw_alpha/commands/sw_industry.py 脚本
- [x] 1.2 实现 Tushare Pro 客户端初始化和 API 调用
- [x] 1.3 实现 get_sw_industry_data() 函数，支持 date、level、top、sort 参数
- [x] 1.4 实现行业层级筛选逻辑（L1/L2/L3）
- [x] 1.5 实现字段映射和数据转换
- [x] 1.6 实现 CLI 入口 main() 函数
- [x] 1.7 实现错误处理（TOKEN 未配置、积分不足、非交易日）

## 2. Skill 配置

- [x] 2.1 创建 skills/sw-industry/SKILL.md 文件
- [x] 2.2 配置 frontmatter 元数据和使用说明

## 3. 单元测试

- [x] 3.1 编写单元测试（Mock Tushare API）
- [x] 3.2 测试成功获取数据场景
- [x] 3.3 测试各类错误处理场景

## 4. 测试验证

- [x] 4.1 运行单元测试确保通过
- [x] 4.2 手动测试脚本执行验证输出格式
