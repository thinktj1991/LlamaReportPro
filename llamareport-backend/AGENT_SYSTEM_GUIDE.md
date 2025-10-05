# Agent 系统使用指南

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [快速开始](#快速开始)
4. [API 接口](#api-接口)
5. [使用示例](#使用示例)
6. [故障排除](#故障排除)

---

## 系统概述

### 功能特性

✅ **智能年报分析**: 使用 FunctionAgent 自动分析年报并生成结构化报告  
✅ **模板化输出**: 基于 Jinja2 模板生成标准格式的 Markdown 报告  
✅ **结构化数据**: 使用 Pydantic 模型确保数据质量和类型安全  
✅ **模块化设计**: 可单独生成各个章节或完整报告  
✅ **DeepSeek + OpenAI**: 对话使用 DeepSeek,嵌入使用 OpenAI  

### 报告结构

生成的年报分析包含以下五个部分:

1. **财务点评** - 财务图表、业绩速览、业绩对比、指标归因
2. **业绩指引** - 业绩预告、经营计划、风险提示
3. **业务亮点** - 各业务板块的亮点和成就
4. **盈利预测和估值** - 一致预测、机构预测、估值分析
5. **总结** - 综合所有部分的总结

---

## 架构设计

### 系统架构

```
用户请求
    ↓
FastAPI (Agent API)
    ↓
ReportAgent (FunctionAgent)
    ↓
工具层:
├─ QueryEngineTool (RAG 数据检索)
│   └─ RAG Engine (DeepSeek + OpenAI Embedding)
├─ FinancialReviewTool (财务点评生成)
│   └─ Pydantic 结构化输出
├─ BusinessGuidanceTool (业绩指引生成)
│   └─ Pydantic 结构化输出
├─ BusinessHighlightsTool (业务亮点生成)
│   └─ Pydantic 结构化输出
└─ ProfitForecastTool (盈利预测生成)
    └─ Pydantic 结构化输出
    ↓
TemplateRenderer (Jinja2)
    ↓
Markdown 报告
```

### 核心组件

#### 1. 数据模型 (`models/report_models.py`)

- `AnnualReportAnalysis` - 完整报告模型
- `FinancialReview` - 财务点评模型
- `BusinessGuidance` - 业绩指引模型
- `BusinessHighlights` - 业务亮点模型
- `ProfitForecastAndValuation` - 盈利预测和估值模型

#### 2. 工具函数 (`agents/report_tools.py`)

- `generate_financial_review()` - 生成财务点评
- `generate_business_guidance()` - 生成业绩指引
- `generate_business_highlights()` - 生成业务亮点
- `generate_profit_forecast_and_valuation()` - 生成盈利预测和估值
- `retrieve_financial_data()` - 检索财务数据
- `retrieve_business_data()` - 检索业务数据

#### 3. Agent 配置 (`agents/report_agent.py`)

- `ReportAgent` - 主 Agent 类
- 集成所有工具
- 管理工作流程

#### 4. 模板渲染 (`agents/template_renderer.py`)

- `TemplateRenderer` - Jinja2 模板渲染器
- 将结构化数据转换为 Markdown

#### 5. API 接口 (`api/agent.py`)

- `/agent/generate-report` - 生成完整报告
- `/agent/generate-section` - 生成单个章节
- `/agent/query` - 通用查询
- `/agent/status` - 系统状态

---

## 快速开始

### 1. 安装依赖

```bash
cd llamareport-backend
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `.env` 文件中配置:

```env
# OpenAI API (用于 Embedding)
OPENAI_API_KEY=your_openai_api_key

# DeepSeek API (用于对话模型)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 上传并处理文档

首先需要上传年报 PDF 并处理:

```bash
# 启动服务器
python main.py

# 上传文档 (使用 API 或前端)
# POST /upload
# POST /process/{document_id}
```

### 4. 测试系统

```bash
python test_agent_system.py
```

### 5. 生成报告

```python
import requests

# 生成完整报告
response = requests.post("http://localhost:8000/agent/generate-report", json={
    "company_name": "ST数源",
    "year": "2023",
    "save_to_file": True,
    "output_path": "reports/ST数源_2023_report.md"
})

print(response.json())
```

---

## API 接口

### 1. 生成完整报告

**端点**: `POST /agent/generate-report`

**请求体**:
```json
{
    "company_name": "公司名称",
    "year": "2023",
    "custom_query": "可选的自定义查询",
    "save_to_file": true,
    "output_path": "reports/report.md"
}
```

**响应**:
```json
{
    "status": "success",
    "company_name": "公司名称",
    "year": "2023",
    "report": "生成的报告文本...",
    "structured_response": {...},
    "saved_to": "reports/report.md"
}
```

### 2. 生成单个章节

**端点**: `POST /agent/generate-section`

**请求体**:
```json
{
    "section_name": "financial_review",
    "company_name": "公司名称",
    "year": "2023"
}
```

**章节名称**:
- `financial_review` - 财务点评
- `business_guidance` - 业绩指引
- `business_highlights` - 业务亮点
- `profit_forecast` - 盈利预测和估值

### 3. 通用查询

**端点**: `POST /agent/query`

**请求体**:
```json
{
    "question": "公司的主要业务是什么?"
}
```

### 4. 系统状态

**端点**: `GET /agent/status`

**响应**:
```json
{
    "rag_engine_initialized": true,
    "report_agent_initialized": true,
    "template_renderer_initialized": true,
    "ready": true,
    "index_loaded": true
}
```

### 5. 列出模板

**端点**: `GET /agent/templates`

**响应**:
```json
{
    "templates": ["annual_report_template.md.jinja2"],
    "count": 1
}
```

---

## 使用示例

### Python 示例

```python
import asyncio
from core.rag_engine import RAGEngine
from agents.report_agent import ReportAgent
from agents.template_renderer import TemplateRenderer

async def generate_report_example():
    # 1. 初始化 RAG 引擎
    rag = RAGEngine()
    rag.load_existing_index()
    
    # 2. 初始化 Agent
    agent = ReportAgent(rag.query_engine)
    
    # 3. 生成报告
    result = await agent.generate_report(
        company_name="ST数源",
        year="2023"
    )
    
    # 4. 渲染模板
    if result["status"] == "success" and result.get("structured_response"):
        renderer = TemplateRenderer()
        markdown = renderer.render_report(result["structured_response"])
        
        # 5. 保存到文件
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print("✅ 报告生成成功!")
    else:
        print(f"❌ 生成失败: {result.get('error')}")

# 运行
asyncio.run(generate_report_example())
```

### cURL 示例

```bash
# 生成完整报告
curl -X POST "http://localhost:8000/agent/generate-report" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ST数源",
    "year": "2023",
    "save_to_file": true
  }'

# 生成单个章节
curl -X POST "http://localhost:8000/agent/generate-section" \
  -H "Content-Type: application/json" \
  -d '{
    "section_name": "financial_review",
    "company_name": "ST数源",
    "year": "2023"
  }'

# 查询
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "公司的营业收入是多少?"
  }'
```

---

## 故障排除

### 问题 1: "RAG 引擎未初始化"

**原因**: 没有上传和处理文档

**解决方案**:
1. 上传 PDF 文档: `POST /upload`
2. 处理文档: `POST /process/{document_id}`
3. 确认索引已创建: `GET /agent/status`

### 问题 2: "模板目录不存在"

**原因**: `templates` 目录缺失

**解决方案**:
```bash
mkdir -p llamareport-backend/templates
# 确保 annual_report_template.md.jinja2 存在
```

### 问题 3: "API Key 未设置"

**原因**: 环境变量未配置

**解决方案**:
```bash
# 检查 .env 文件
cat .env

# 确保包含:
# OPENAI_API_KEY=...
# DEEPSEEK_API_KEY=...
```

### 问题 4: Agent 生成失败

**原因**: LLM 调用失败或数据不足

**解决方案**:
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看日志文件: `llamareport-backend.log`
4. 确保文档已正确处理

---

## 技术栈

- **Web 框架**: FastAPI
- **LLM**: DeepSeek (对话) + OpenAI (嵌入)
- **Agent 框架**: LlamaIndex FunctionAgent
- **数据验证**: Pydantic
- **模板引擎**: Jinja2
- **向量数据库**: ChromaDB
- **PDF 处理**: pdfplumber

---

## 下一步

1. ✅ 基础系统已完成
2. 🔄 添加更多测试用例
3. 🔄 优化 Agent 的 system_prompt
4. 🔄 添加流式输出支持
5. 🔄 添加报告质量评估
6. 🔄 支持多种报告模板

---

**文档版本**: 1.0.0  
**最后更新**: 2025-10-01

