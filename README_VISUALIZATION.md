# 📊 LlamaReportPro 智能可视化功能

## 🎉 功能介绍

LlamaReportPro 现已集成**智能可视化生成Agent**，能够在问答和报告分析过程中自动生成合适的图表，大幅增强数据洞察能力。

### ✨ 核心特性

- 🤖 **智能检测** - 自动判断查询是否需要可视化
- 🎯 **智能推荐** - 基于数据类型推荐最合适的图表
- 📊 **多种图表** - 支持15种图表类型（柱状图、折线图、饼图等）
- 💡 **数据洞察** - 自动生成趋势分析、极值分析等洞察
- 🔌 **无缝集成** - 与现有问答和Agent系统完美集成
- ⚡ **即插即用** - 一行代码启用，无需额外配置

---

## 🚀 快速开始

### 1. 运行测试

```bash
cd llamareport-backend
python test_visualization.py
```

**预期输出**：
```
✅ 可视化生成成功: ChartType.LINE
✅ 可视化生成成功: ChartType.PIE
✅ 所有测试完成
```

### 2. 运行演示

```bash
cd llamareport-backend
python demo_visualization_api.py
```

这将运行5个演示案例，展示不同类型的可视化。

### 3. 启动API服务

```bash
cd llamareport-backend
uvicorn main:app --reload --port 8000
```

### 4. 使用前端界面

**选项A: HTML演示页面**
```
http://localhost:8000/static/visualization_demo.html
```

**选项B: Streamlit页面**
```bash
streamlit run pages/visualization_qa.py
```

---

## 💻 使用示例

### API调用

```python
import requests

response = requests.post(
    "http://localhost:8000/query/ask",
    json={
        "question": "公司2021-2023年的营业收入趋势如何？",
        "enable_visualization": True
    }
)

data = response.json()

# 文本回答
print(data['answer'])

# 可视化配置
if data['visualization']['has_visualization']:
    chart_config = data['visualization']['chart_config']
    print(f"图表类型: {chart_config['chart_type']}")
    print(f"图表标题: {chart_config['layout']['title']}")
```

### Python直接调用

```python
from agents.visualization_agent import VisualizationAgent

viz_agent = VisualizationAgent()

result = await viz_agent.generate_visualization(
    query="公司净利润增长情况如何？",
    answer="公司近三年净利润持续增长：2021年10亿元，2022年12亿元，2023年15亿元"
)

if result.has_visualization:
    print(f"推荐图表: {result.recommendation.recommended_chart_type}")
    print(f"推荐理由: {result.recommendation.reason}")
```

---

## 📊 支持的图表类型

| 图表类型 | 适用场景 | 示例查询 |
|---------|---------|---------|
| 折线图 (LINE) | 时间序列、趋势分析 | "营业收入趋势" |
| 柱状图 (BAR) | 对比分析、分类数据 | "各季度收入对比" |
| 饼图 (PIE) | 占比分析、分布展示 | "业务板块占比" |
| 多折线图 (MULTI_LINE) | 多指标趋势对比 | "收入和利润趋势" |
| 分组柱状图 (GROUPED_BAR) | 多维度对比 | "产品线销售对比" |
| 散点图 (SCATTER) | 相关性分析 | "收入与利润关系" |
| 面积图 (AREA) | 累积趋势 | "累计销售额" |
| 热力图 (HEATMAP) | 矩阵数据 | "相关性矩阵" |
| 瀑布图 (WATERFALL) | 累计变化 | "利润构成分析" |
| 仪表盘 (GAUGE) | 单一指标 | "完成率" |

---

## 📁 项目结构

```
LlamaReportPro/
├── llamareport-backend/
│   ├── models/
│   │   └── visualization_models.py      # 可视化数据模型
│   ├── agents/
│   │   ├── visualization_agent.py       # 可视化Agent
│   │   ├── report_agent.py              # 报告Agent（已集成）
│   │   └── report_tools.py              # 报告工具（已集成）
│   ├── api/
│   │   └── query.py                     # 查询API（已集成）
│   ├── static/
│   │   └── visualization_demo.html      # HTML演示页面
│   ├── test_visualization.py            # 测试文件
│   ├── demo_visualization_api.py        # 演示脚本
│   ├── VISUALIZATION_GUIDE.md           # 详细使用指南
│   └── ...
├── pages/
│   └── visualization_qa.py              # Streamlit页面
├── VISUALIZATION_FEATURE_SUMMARY.md     # 功能总结
├── QUICK_START_VISUALIZATION.md         # 快速启动指南
├── CHANGELOG_VISUALIZATION.md           # 更新日志
└── README_VISUALIZATION.md              # 本文件
```

---

## 🎯 工作流程

```
用户查询
    ↓
RAG引擎查询
    ↓
获取文本回答
    ↓
VisualizationAgent分析
    ↓
1. 判断是否需要可视化
2. 提取数据（使用LLM）
3. 推荐图表类型
4. 生成Plotly配置
5. 生成数据洞察
    ↓
返回完整响应
    ↓
前端渲染（Plotly）
```

---

## 🧪 测试结果

所有测试均已通过 ✅

```
测试用例1: 趋势数据
✅ 成功生成折线图
✅ 推荐理由正确
✅ 洞察生成成功

测试用例2: 对比数据
✅ 成功生成饼图
✅ 推荐理由正确
✅ 洞察生成成功

测试用例3: 无数据文本
✅ 正确判断不需要可视化

测试用例4: 工具函数
✅ 工具调用成功
```

---

## 📚 文档资源

- **详细使用指南**: `llamareport-backend/VISUALIZATION_GUIDE.md`
- **功能总结**: `VISUALIZATION_FEATURE_SUMMARY.md`
- **快速启动**: `QUICK_START_VISUALIZATION.md`
- **更新日志**: `CHANGELOG_VISUALIZATION.md`

---

## 🎨 示例截图

### HTML演示页面
- 现代化UI设计
- 实时图表渲染
- 数据洞察展示
- 图表推荐展示

### Streamlit页面
- 响应式布局
- 配置选项
- 示例问题库
- 美化的展示

---

## 🔧 配置选项

### 启用/禁用可视化

```python
# 启用可视化（默认）
response = requests.post(
    "http://localhost:8000/query/ask",
    json={
        "question": "...",
        "enable_visualization": True
    }
)

# 禁用可视化
response = requests.post(
    "http://localhost:8000/query/ask",
    json={
        "question": "...",
        "enable_visualization": False
    }
)
```

### 自定义LLM

```python
from agents.visualization_agent import VisualizationAgent
from llama_index.llms.deepseek import DeepSeek

custom_llm = DeepSeek(
    model="deepseek-chat",
    api_key="your_key",
    temperature=0.2
)

viz_agent = VisualizationAgent(llm=custom_llm)
```

---

## 💡 最佳实践

### 查询优化

✅ **好的查询**:
- "公司2021-2023年的营业收入趋势如何？"
- "各业务板块的收入占比是多少？"
- "净利润增长情况如何？"

❌ **不太好的查询**:
- "公司怎么样？"（太宽泛）
- "告诉我一切"（没有具体指标）

### 性能优化

- 对于不需要可视化的查询，设置 `enable_visualization=False`
- 批量查询时考虑异步处理

---

## 🐛 常见问题

### Q: 为什么没有生成图表？

**A**: 可能原因：
1. 回答中没有足够的数值数据
2. `enable_visualization` 设置为 `False`
3. 查询不包含可视化关键词

### Q: 图表类型不合适？

**A**: 系统会自动推荐最合适的图表类型，查看推荐理由了解选择依据。

### Q: API调用失败？

**A**: 检查：
- 后端服务是否启动
- API地址是否正确
- DeepSeek API密钥是否配置

---

## 🎉 总结

智能可视化功能为 LlamaReportPro 带来了：

1. **更直观的数据展示** - 图表一目了然
2. **更深入的数据分析** - 自动生成洞察
3. **更简单的集成方式** - 一行代码启用
4. **更流畅的用户体验** - 自动检测，智能推荐

**让数据说话，让洞察可见！** 📊✨

---

## 📞 支持

如有问题或建议，请：
1. 查看详细文档
2. 运行测试和演示
3. 提交Issue或联系开发团队

**感谢使用 LlamaReportPro！** 🚀

