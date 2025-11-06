# 升级到实时数据版本指南

## 📋 升级概述

本文档指导您将现有的 LlamaReport Backend 升级到支持实时数据的新版本。

**升级类型**: 功能增强（向后兼容）  
**影响范围**: 无破坏性变更，现有功能保持不变  
**升级时间**: 5-10 分钟  

---

## ✅ 升级前检查

### 1. 版本要求

- ✅ Python 3.8+
- ✅ 现有系统运行正常
- ✅ 已配置 `OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY`

### 2. 备份（可选）

```bash
# 备份当前配置
cp .env .env.backup

# 备份数据
cp -r storage storage_backup
cp -r uploads uploads_backup
```

---

## 🚀 升级步骤

### 步骤 1: 更新依赖

```bash
cd llamareport-backend
pip install -r requirements.txt
```

新增的依赖包:
- `tushare>=1.2.89`
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`
- `lxml>=4.9.0`

### 步骤 2: 配置环境变量（可选）

编辑 `.env` 文件，添加实时数据配置:

```env
# 实时数据配置（可选）
TUSHARE_API_TOKEN=your-token-here
ENABLE_REALTIME_DATA=true
```

**重要提示**:
- `TUSHARE_API_TOKEN` 是**可选**的
- 不配置时会自动使用免费的新浪财经数据源
- 系统会优雅降级，不会影响使用

### 步骤 3: 重启服务

```bash
# 停止当前服务 (Ctrl+C)

# 重新启动
python main.py

# 或使用启动脚本
python start.py
```

### 步骤 4: 验证升级

#### 检查服务状态
```bash
# 检查主服务健康
curl http://localhost:8000/health

# 检查实时数据服务健康
curl http://localhost:8000/realtime/health
```

#### 测试功能
```bash
# 测试实时股价
curl http://localhost:8000/realtime/quote/600519.SH

# 测试 Agent（会自动使用实时数据工具）
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"question": "帮我查一下贵州茅台现在的股价"}'
```

#### 查看 API 文档
访问 http://localhost:8000/docs

在文档中应该能看到:
- `/realtime/*` 新增的 7 个端点
- Agent 工具列表中包含实时数据工具

---

## 🎯 升级验证清单

### 功能验证

- [ ] 实时股价查询正常
- [ ] 新闻获取正常
- [ ] 公告获取正常
- [ ] 智能预警正常
- [ ] 市场概览正常
- [ ] Agent 能正确调用实时数据工具
- [ ] 原有功能（年报分析）不受影响

### 性能验证

- [ ] API 响应时间 < 3 秒
- [ ] 数据源健康检查通过
- [ ] 无明显错误日志
- [ ] 内存占用正常

---

## 🔧 配置选项详解

### 1. 基础配置（免费）

```env
# 只使用免费数据源
ENABLE_REALTIME_DATA=true
# 不配置 TUSHARE_API_TOKEN
```

**特点**:
- ✅ 完全免费
- ✅ 实时性好
- ⚠️ 数据范围有限
- ⚠️ 无历史财务指标

**适合**: 个人用户、功能验证

### 2. 推荐配置（免费 Tushare）

```env
ENABLE_REALTIME_DATA=true
TUSHARE_API_TOKEN=your-free-token
```

**如何获取免费 Token**:
1. 访问 https://tushare.pro/register
2. 注册账号（免费）
3. 登录后在"个人中心"获取 Token
4. 填入 `.env` 文件

**特点**:
- ✅ 完全免费
- ✅ 数据更全面
- ✅ 支持财务指标
- ⚠️ 有调用限制（200次/分钟）

**适合**: 中小团队、日常使用

### 3. 专业配置（付费 Tushare）

```env
ENABLE_REALTIME_DATA=true
TUSHARE_API_TOKEN=your-pro-token
```

**如何升级到专业版**:
1. 在 Tushare 网站购买积分（500-1000元/月）
2. 使用相同的 Token

**特点**:
- ✅ 无调用限制
- ✅ 数据最全面
- ✅ 响应更稳定
- 💰 需要付费

**适合**: 企业用户、高频使用

---

## 📊 升级后功能对比

### Agent 能力对比

#### 升级前
```
用户: "贵州茅台值得投资吗？"
Agent: 
├── 分析年报数据（2023年报）
└── 基于历史数据给建议

局限性:
❌ 数据滞后（可能已过去半年）
❌ 无法知道当前价格
❌ 不了解最新动态
```

#### 升级后
```
用户: "贵州茅台值得投资吗？"
Agent:
├── 分析年报数据（历史业绩）
├── 查询实时股价（当前价格和估值）⭐
├── 获取最新新闻（最近动态）⭐
├── 检查预警信息（风险提示）⭐
└── 综合分析给建议

优势:
✅ 历史 + 实时，全面分析
✅ 了解当前价格和估值
✅ 掌握最新动态
✅ 风险意识更强
```

### API 能力对比

#### 升级前
```
可用端点:
├── /upload/* - 文件上传
├── /process/* - 文档处理
├── /query/* - RAG 问答
└── /agent/* - Agent 分析
```

#### 升级后
```
可用端点:
├── /upload/* - 文件上传
├── /process/* - 文档处理
├── /query/* - RAG 问答
├── /agent/* - Agent 分析（已增强）⭐
└── /realtime/* - 实时数据 ⭐ NEW
    ├── GET /quote/{code}
    ├── POST /news
    ├── POST /announcements
    ├── GET /alerts/{code}
    ├── GET /market/overview
    ├── GET /health
    └── GET /statistics
```

---

## 🐛 故障排除

### 问题 1: "Module 'tushare' not found"

**原因**: 未安装新依赖

**解决**:
```bash
pip install -r requirements.txt
```

### 问题 2: "TUSHARE_API_TOKEN not provided"

**原因**: 未配置 Tushare Token

**解决**:
- 方案 1: 获取并配置 Token（推荐）
- 方案 2: 忽略此警告，系统会使用新浪财经

**说明**: 这是警告而非错误，系统仍可正常运行。

### 问题 3: 实时数据获取失败

**检查步骤**:

```bash
# 1. 检查数据源健康
curl http://localhost:8000/realtime/health

# 2. 查看统计信息
curl http://localhost:8000/realtime/statistics

# 3. 查看日志
tail -f llamareport-backend.log | grep realtime

# 4. 测试数据源
python -c "from agents.realtime_tools import test_realtime_tools; test_realtime_tools()"
```

### 问题 4: Agent 不使用实时数据工具

**可能原因**:
1. 用户问题不明确（Agent 不知道需要实时数据）
2. 工具初始化失败

**解决**:
1. 明确指定要实时数据: "帮我查一下**现在**的股价"
2. 检查日志查看工具加载情况
3. 重启服务

### 问题 5: 新闻/公告返回空

**原因**: 
- 示例实现返回模拟数据
- 或实际数据源暂无数据

**说明**: 
- 新闻功能当前为示例实现
- 生产环境需要实现真实的爬虫或使用付费 API

---

## 📈 性能优化建议

### 1. 使用缓存

对于不常变化的数据（如公司基本信息），可以添加缓存:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_stock_basic_info(stock_code: str):
    # 缓存基本信息
    pass
```

### 2. 批量请求

如果需要查询多只股票:

```python
# 不推荐 - 串行请求
for code in stock_codes:
    get_realtime_stock_price(code)

# 推荐 - 批量请求
import asyncio
results = await asyncio.gather(*[
    get_quote_async(code) for code in stock_codes
])
```

### 3. 监控和告警

```bash
# 定期检查数据源健康
curl http://localhost:8000/realtime/health

# 查看调用统计
curl http://localhost:8000/realtime/statistics
```

---

## 🔄 回滚步骤

如果需要回滚到升级前版本:

### 步骤 1: 禁用实时数据功能

编辑 `.env`:
```env
ENABLE_REALTIME_DATA=false
```

### 步骤 2: 重启服务

```bash
python main.py
```

### 步骤 3: 验证

实时数据端点应该返回禁用提示，但不影响其他功能。

**注意**: 
- 不需要卸载依赖
- 不需要删除代码
- Agent 会自动适应（不使用实时数据工具）

---

## 📚 更多资源

### 官方文档

- [实时数据使用指南](./REALTIME_DATA_GUIDE.md)
- [功能示例](./REALTIME_FEATURE_EXAMPLES.md)
- [技术总结](./REALTIME_FEATURE_SUMMARY.md)
- [Agent 系统文档](./AGENT_README.md)

### 演示脚本

```bash
# 运行交互式演示
python examples/realtime_data_demo.py

# 选择演示:
# 1. 直接使用工具
# 2. 通过 Agent 使用
# 3. 使用 REST API
# 4. 数据源对比
```

### API 文档

- 在线文档: http://localhost:8000/docs
- 查看 `/realtime` 标签下的所有端点

---

## 💬 常见问题

### Q: 升级后会影响现有功能吗？

**A**: 不会。升级是**增量式**的，所有现有功能保持不变。

### Q: 必须配置 Tushare Token 吗？

**A**: 不必须。不配置时会自动使用新浪财经（免费）。

### Q: 实时数据的成本是多少？

**A**: 
- 基础方案: 0 元/月（新浪财经）
- 推荐方案: 0 元/月（Tushare 免费版）
- 专业方案: 500-1000 元/月（Tushare 专业版）

### Q: 数据准确性如何？

**A**: 
- 新浪财经: 实时性好，延迟 < 3 秒
- Tushare: 官方数据，准确可靠
- 建议重要数据交叉验证

### Q: 如何知道 Agent 使用了哪些工具？

**A**: 
查看 Agent 查询响应中的 `tool_calls` 字段:

```python
result = await agent.query("贵州茅台现在多少钱？")
print(result['tool_calls'])  # 显示使用的工具列表
```

---

## 🎓 升级后的新玩法

### 1. 实时监控仪表板

```python
# 创建实时监控脚本
import asyncio
from agents.realtime_tools import (
    get_realtime_stock_price,
    check_stock_alerts
)

async def monitor_dashboard():
    """实时监控仪表板"""
    while True:
        print("\n" + "="*60)
        print("实时监控仪表板")
        print("="*60)
        
        # 监控的股票列表
        watchlist = ["600519.SH", "000858.SZ", "601318.SH"]
        
        for stock in watchlist:
            quote = get_realtime_stock_price(stock)
            alerts = check_stock_alerts(stock)
            
            print(f"\n{stock}:")
            print(f"  行情: {quote[:100]}...")
            if "异常" in alerts:
                print(f"  预警: {alerts}")
        
        # 每5分钟刷新
        await asyncio.sleep(300)

asyncio.run(monitor_dashboard())
```

### 2. 新闻订阅服务

```python
# 订阅关注公司的新闻
companies = ["贵州茅台", "中国平安", "比亚迪"]

for company in companies:
    news = get_latest_financial_news(company, 3)
    print(f"\n{company} 最新动态:")
    print(news)
```

### 3. 智能投资助手

```python
async def investment_advisor(stock_code: str):
    """智能投资顾问"""
    from agents.report_agent import ReportAgent
    from core.rag_engine import RAGEngine
    
    rag = RAGEngine()
    rag.load_existing_index()
    agent = ReportAgent(rag.query_engine)
    
    question = f"""
请对 {stock_code} 进行全面的投资分析，包括:
1. 历史业绩表现（从年报）
2. 当前价格和估值（实时数据）
3. 最新新闻动态
4. 风险评估
5. 投资建议和目标价
"""
    
    result = await agent.query(question)
    return result['answer']

# 使用
report = await investment_advisor("600519.SH")
print(report)
```

---

## 📊 升级效果预期

### 用户体验提升

| 功能 | 升级前 | 升级后 | 提升 |
|------|--------|--------|------|
| 数据时效性 | 滞后3-12月 | 实时 | ✅✅✅ |
| 信息完整度 | 仅历史 | 历史+实时 | ✅✅ |
| 使用频率 | 年度 | 日度 | ✅✅✅ |
| 功能丰富度 | 4个核心功能 | 10个功能 | ✅✅ |

### 技术指标

| 指标 | 数值 |
|------|------|
| 新增代码行数 | ~1,200 行 |
| 新增 Agent 工具 | 5 个 |
| 新增 API 端点 | 7 个 |
| 新增依赖包 | 4 个 |
| 向后兼容性 | 100% |
| 升级时间 | < 10 分钟 |

---

## ✅ 升级完成确认

升级成功后，您应该能够:

1. ✅ 访问 http://localhost:8000/docs 看到 `/realtime` 端点
2. ✅ 调用 `/realtime/health` 返回健康状态
3. ✅ 通过 Agent 查询实时数据
4. ✅ 原有的年报分析功能正常工作
5. ✅ 日志中显示"加载了 5 个实时数据工具"

---

## 📞 需要帮助？

### 查看文档

- **使用指南**: [REALTIME_DATA_GUIDE.md](./REALTIME_DATA_GUIDE.md)
- **示例文档**: [REALTIME_FEATURE_EXAMPLES.md](./REALTIME_FEATURE_EXAMPLES.md)
- **技术总结**: [REALTIME_FEATURE_SUMMARY.md](./REALTIME_FEATURE_SUMMARY.md)

### 运行演示

```bash
python examples/realtime_data_demo.py
```

### 查看日志

```bash
tail -f llamareport-backend.log
```

---

**升级版本**: v1.0.0 → v1.1.0  
**发布日期**: 2024-01-15  
**状态**: ✅ 稳定版本

