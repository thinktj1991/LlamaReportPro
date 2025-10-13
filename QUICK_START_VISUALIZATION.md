# 🚀 智能可视化功能快速启动指南

## ⚡ 5分钟快速上手

### 步骤1: 确保环境配置正确

检查 `.env` 文件中的API密钥：

```bash
# .env
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 步骤2: 运行测试验证功能

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

### 步骤3: 启动后端API服务

```bash
cd llamareport-backend
uvicorn main:app --reload --port 8000
```

### 步骤4: 测试API调用

**方法A: 使用curl**

```bash
curl -X POST "http://localhost:8000/query/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "公司2021-2023年的营业收入趋势如何？",
    "enable_visualization": true
  }'
```

**方法B: 使用Python**

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
print(f"回答: {data['answer']}")
print(f"有可视化: {data['visualization']['has_visualization']}")
```

### 步骤5: 启动前端界面

**选项A: HTML演示页面**

1. 在浏览器中打开：
   ```
   http://localhost:8000/static/visualization_demo.html
   ```

2. 输入问题，点击"查询"按钮

**选项B: Streamlit页面**

```bash
streamlit run pages/visualization_qa.py
```

---

## 📝 常用示例

### 示例1: 趋势分析

**问题**: "公司2021-2023年的营业收入趋势如何？"

**预期结果**:
- 📝 文本回答：描述营业收入的变化
- 📊 折线图：展示三年的趋势
- 💡 洞察：上升/下降趋势，变化幅度

### 示例2: 占比分析

**问题**: "各业务板块的收入占比是多少？"

**预期结果**:
- 📝 文本回答：列出各板块占比
- 📊 饼图：可视化占比分布
- 💡 洞察：最大/最小板块

### 示例3: 对比分析

**问题**: "各季度营业收入对比"

**预期结果**:
- 📝 文本回答：各季度数据
- 📊 柱状图：季度对比
- 💡 洞察：最高/最低季度

---

## 🔧 配置选项

### 启用/禁用可视化

**API调用**:
```python
# 启用可视化
response = requests.post(
    "http://localhost:8000/query/ask",
    json={
        "question": "...",
        "enable_visualization": True  # 启用
    }
)

# 禁用可视化
response = requests.post(
    "http://localhost:8000/query/ask",
    json={
        "question": "...",
        "enable_visualization": False  # 禁用
    }
)
```

**Streamlit界面**:
- 在侧边栏勾选/取消"启用智能可视化"

### 自定义LLM配置

```python
from agents.visualization_agent import VisualizationAgent
from llama_index.llms.deepseek import DeepSeek

# 自定义LLM
custom_llm = DeepSeek(
    model="deepseek-chat",
    api_key="your_key",
    temperature=0.2  # 调整温度
)

viz_agent = VisualizationAgent(llm=custom_llm)
```

---

## 🎯 最佳实践

### 1. 查询优化

✅ **好的查询**:
- "公司2021-2023年的营业收入趋势如何？"
- "各业务板块的收入占比是多少？"
- "净利润增长情况如何？"

❌ **不太好的查询**:
- "公司怎么样？"（太宽泛）
- "告诉我一切"（没有具体指标）

### 2. 性能优化

- 对于不需要可视化的查询，设置 `enable_visualization=False`
- 批量查询时考虑异步处理

### 3. 错误处理

```python
try:
    response = requests.post(...)
    data = response.json()
    
    if data['visualization']['has_visualization']:
        # 处理可视化
        pass
    else:
        # 仅显示文本
        pass
        
except Exception as e:
    print(f"错误: {e}")
    # 降级到纯文本
```

---

## 🐛 常见问题

### Q1: 为什么没有生成图表？

**可能原因**:
1. 回答中没有足够的数值数据
2. `enable_visualization` 设置为 `False`
3. 查询不包含可视化关键词

**解决方法**:
- 确保查询包含数值、趋势、对比等关键词
- 检查 `enable_visualization` 设置
- 查看日志了解详细原因

### Q2: 图表类型不合适？

**解决方法**:
- 系统会自动推荐最合适的图表类型
- 查看推荐理由了解选择依据
- 如需特定图表，可在查询中明确说明

### Q3: API调用失败？

**检查清单**:
- ✅ 后端服务是否启动
- ✅ API地址是否正确
- ✅ DeepSeek API密钥是否配置
- ✅ 网络连接是否正常

---

## 📚 更多资源

- **详细文档**: `llamareport-backend/VISUALIZATION_GUIDE.md`
- **功能总结**: `VISUALIZATION_FEATURE_SUMMARY.md`
- **测试文件**: `llamareport-backend/test_visualization.py`
- **HTML演示**: `llamareport-backend/static/visualization_demo.html`
- **Streamlit页面**: `pages/visualization_qa.py`

---

## 🎉 开始使用

现在你已经准备好使用智能可视化功能了！

1. ✅ 运行测试验证功能
2. ✅ 启动后端API服务
3. ✅ 打开前端界面
4. ✅ 输入问题，查看可视化结果

**祝你使用愉快！** 🚀

---

## 💡 提示

- 尝试不同类型的问题，探索各种图表
- 查看数据洞察，发现隐藏的规律
- 根据推荐理由了解图表选择逻辑
- 如有问题，查看详细文档或联系支持

**让数据说话，让洞察可见！** 📊✨

