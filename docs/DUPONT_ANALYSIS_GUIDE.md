# 杜邦分析功能使用指南

## 📊 功能概述

杜邦分析是一种经典的财务分析方法，将净资产收益率(ROE)分解为三个关键驱动因素，帮助深入理解公司盈利能力的来源。

### 核心公式

```
ROE = 资产净利率 × 权益乘数
    = (营业净利润率 × 资产周转率) × (总资产 / 股东权益)
```

### 层级结构

- **第一层**: ROE = ROA × 权益乘数
- **第二层**: ROA = 营业净利润率 × 资产周转率
- **第三层**: 基础财务数据（净利润、营业收入、总资产、股东权益等）

---

## 🚀 快速开始

### 1. 前端使用（Streamlit）

#### 启动应用

```bash
cd D:\Downloads\LlamaReportPro
streamlit run app.py
```

#### 访问杜邦分析页面

1. 在浏览器中打开 Streamlit 应用
2. 在侧边栏选择 "📊 杜邦分析" 页面
3. 选择数据输入方式：
   - **手动输入**: 直接输入财务数据
   - **从已上传文档提取**: 从PDF自动提取
   - **使用示例数据**: 快速演示

#### 输入财务数据

**必需指标**:
- 净利润（元）
- 营业收入（元）
- 总资产（元）
- 股东权益（元）
- 流动资产（元）
- 非流动资产（元）

**可选指标**:
- 营业利润（元）
- 总负债（元）

#### 生成分析

1. 点击 "🚀 生成杜邦分析" 按钮
2. 等待分析完成
3. 切换到 "📊 分析结果" 标签页查看结果
4. 切换到 "📈 可视化" 标签页查看图表

---

### 2. 后端API使用（FastAPI）

#### 启动后端服务

```bash
cd D:\Downloads\LlamaReportPro\llamareport-backend
python main.py
```

#### API端点

**生成杜邦分析**

```http
POST /api/dupont-analysis
Content-Type: application/json

{
  "company_name": "示例科技股份有限公司",
  "report_year": "2023",
  "report_period": "2023年度",
  "financial_data": {
    "净利润": 1000000000,
    "营业收入": 5000000000,
    "总资产": 10000000000,
    "股东权益": 6000000000,
    "流动资产": 4000000000,
    "非流动资产": 6000000000
  }
}
```

**响应示例**

```json
{
  "company_name": "示例科技股份有限公司",
  "report_year": "2023",
  "report_period": "2023年度",
  "level1": {
    "roe": {
      "name": "净资产收益率",
      "value": "16.67",
      "formatted_value": "16.67%",
      "level": 1,
      "formula": "ROE = 净利润 / 股东权益",
      "unit": "%"
    },
    "roa": {...},
    "equity_multiplier": {...}
  },
  "level2": {...},
  "level3": {...},
  "insights": [
    "净资产收益率为16.67%，处于良好水平，表明公司盈利能力较强",
    "ROE主要由资产净利率驱动，建议公司注重资产使用效率和盈利能力"
  ],
  "strengths": [...],
  "weaknesses": [...],
  "recommendations": [...]
}
```

---

### 3. Python代码使用

#### 基本用法

```python
from utils.financial_calculator import DupontAnalyzer

# 创建分析器
analyzer = DupontAnalyzer()

# 准备财务数据
financial_data = {
    '净利润': 1000000000,  # 10亿元
    '营业收入': 5000000000,  # 50亿元
    '总资产': 10000000000,  # 100亿元
    '股东权益': 6000000000,  # 60亿元
    '流动资产': 4000000000,  # 40亿元
    '非流动资产': 6000000000,  # 60亿元
}

# 执行杜邦分析
result = analyzer.calculate_dupont_analysis(
    financial_data=financial_data,
    company_name="示例公司",
    report_year="2023"
)

# 访问结果
print(f"ROE: {result.level1.roe.formatted_value}")
print(f"ROA: {result.level1.roa.formatted_value}")
print(f"权益乘数: {result.level1.equity_multiplier.formatted_value}")

# 查看AI洞察
for insight in result.insights:
    print(f"💡 {insight}")
```

#### 生成可视化

```python
from utils.dupont_visualizer import create_dupont_sankey

# 创建Sankey图
fig = create_dupont_sankey(result)

# 保存为HTML
fig.write_html("dupont_analysis.html")

# 或在Jupyter中显示
fig.show()
```

---

## 🏗️ 技术架构

### 核心组件

1. **Pydantic模型** (`llamareport-backend/models/dupont_models.py`)
   - `DupontMetric`: 单个指标模型
   - `DupontLevel1/2/3`: 三层级指标模型
   - `DupontAnalysis`: 完整分析结果模型
   - `DupontTreeNode`: 树状结构模型

2. **计算引擎** (`utils/financial_calculator.py`)
   - `DupontAnalyzer`: 杜邦分析计算器
   - 自动指标映射和归一化
   - AI洞察生成

3. **工具函数** (`llamareport-backend/agents/dupont_tools.py`)
   - `generate_dupont_analysis()`: Agent工具函数
   - `extract_financial_data_for_dupont()`: 数据提取
   - `parse_financial_data_response()`: 响应解析

4. **可视化组件** (`utils/dupont_visualizer.py`)
   - `create_dupont_sankey()`: Sankey流程图
   - `create_dupont_tree_chart()`: 树状图
   - `create_dupont_bar_chart()`: 柱状图

5. **前端页面** (`pages/dupont_analysis.py`)
   - Streamlit交互界面
   - 三种数据输入方式
   - 实时可视化展示

---

## 📝 数据格式说明

### 输入数据格式

支持多种指标名称（自动映射）：

```python
{
    # 净利润（必需）
    '净利润': 1000000000,
    # 或 'net_income', '归母净利润'
    
    # 营业收入（必需）
    '营业收入': 5000000000,
    # 或 'revenue', '营业总收入'
    
    # 总资产（必需）
    '总资产': 10000000000,
    # 或 'total_assets'
    
    # 股东权益（必需）
    '股东权益': 6000000000,
    # 或 'equity', '所有者权益', 'shareholders_equity'
    
    # 流动资产（必需）
    '流动资产': 4000000000,
    # 或 'current_assets'
    
    # 非流动资产（必需）
    '非流动资产': 6000000000,
    # 或 'non_current_assets'
    
    # 可选指标
    '营业利润': 1200000000,
    '总负债': 4000000000
}
```

### 输出数据结构

```python
DupontAnalysis(
    company_name="公司名称",
    report_year="2023",
    report_period="2023年度",
    level1=DupontLevel1(
        roe=DupontMetric(...),
        roa=DupontMetric(...),
        equity_multiplier=DupontMetric(...)
    ),
    level2=DupontLevel2(...),
    level3=DupontLevel3(...),
    tree_structure=DupontTreeNode(...),
    insights=["洞察1", "洞察2", ...],
    strengths=["优势1", "优势2", ...],
    weaknesses=["劣势1", "劣势2", ...],
    recommendations=["建议1", "建议2", ...],
    data_source="manual_input",
    extraction_method="direct",
    confidence_score=1.0
)
```

---

## 🔧 Agent集成

杜邦分析已集成到FunctionAgent系统中，可通过自然语言调用：

```python
from llamareport_backend.agents.report_agent import ReportAgent

# 创建Agent
agent = ReportAgent(query_engine=query_engine)

# 自然语言调用
response = agent.chat("请为XX公司2023年生成杜邦分析")

# Agent会自动：
# 1. 从query_engine提取财务数据
# 2. 调用generate_dupont_analysis工具
# 3. 返回结构化的杜邦分析结果
```

---

## 📊 可视化类型

### 1. Sankey流程图

展示各指标之间的层级关系和影响路径，最直观地呈现杜邦分析的分解逻辑。

**特点**:
- 节点颜色区分不同层级
- 流量粗细表示影响权重
- 悬停显示详细信息

### 2. 树状图

以树状结构展示指标分解，清晰呈现父子关系。

**特点**:
- 层级清晰
- 递归展示所有子节点
- 适合打印和报告

### 3. 指标对比柱状图

对比各层级关键指标的数值，便于快速识别强弱项。

**特点**:
- 直观对比
- 数值标注
- 颜色编码

---

## ⚠️ 注意事项

1. **数据单位**: 所有财务数据单位为"元"，不要使用"万元"或"亿元"
2. **数据完整性**: 必需的6个指标必须全部提供
3. **数据合理性**: 系统会验证数据的合理性（如总资产 = 流动资产 + 非流动资产）
4. **精度**: 使用Decimal类型确保计算精度
5. **兼容性**: 支持中文和英文指标名称

---

## 🐛 故障排除

### 问题1: 导入错误

```
ModuleNotFoundError: No module named 'llamareport_backend'
```

**解决方案**:
```python
import sys
from pathlib import Path

backend_path = Path(__file__).parent / "llamareport-backend"
sys.path.insert(0, str(backend_path))
```

### 问题2: 数据验证失败

```
ValidationError: 指标值超出合理范围
```

**解决方案**:
- 检查数据单位是否正确（应为"元"）
- 确认数据是否为正数
- 验证总资产 = 流动资产 + 非流动资产

### 问题3: 可视化不显示

**解决方案**:
- 确保安装了plotly: `pip install plotly`
- 检查浏览器是否支持JavaScript
- 尝试使用不同的可视化类型

---

## 📚 参考资料

- [杜邦分析法 - 百度百科](https://baike.baidu.com/item/杜邦分析法)
- [Plotly Sankey Diagrams](https://plotly.com/python/sankey-diagram/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)

---

## 🎉 总结

杜邦分析功能已完整实现，包括：

✅ Pydantic v2数据模型
✅ 完整的计算引擎
✅ Agent系统集成
✅ 三种可视化方式
✅ Streamlit前端界面
✅ FastAPI后端接口
✅ 完整的测试覆盖

**所有测试通过**: 5/5 ✅

**不影响现有功能**: 所有新代码都是增量添加，未修改任何现有功能。

