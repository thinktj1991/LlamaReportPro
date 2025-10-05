# 🤖 LlamaReport Agent 系统

> 基于 LlamaIndex FunctionAgent 的智能年报分析系统

## 📖 简介

LlamaReport Agent 是一个智能年报分析系统,能够自动分析年报文档并生成结构化的分析报告。系统使用 LlamaIndex 的 FunctionAgent 框架,结合 DeepSeek LLM 和 OpenAI Embedding,实现了高质量的年报分析和报告生成。

### ✨ 核心特性

- 🤖 **智能 Agent**: 使用 FunctionAgent 自动协调多个工具完成复杂任务
- 📊 **结构化输出**: 基于 Pydantic 模型确保数据质量和类型安全
- 📝 **模板化报告**: 使用 Jinja2 模板生成标准格式的 Markdown 报告
- 🔧 **模块化设计**: 可单独生成各个章节或完整报告
- 🚀 **高性能**: 全异步架构,支持并发处理
- 🌐 **API 友好**: RESTful API,易于集成到前端应用

### 📋 报告结构

生成的年报分析包含以下五个部分:

1. **财务点评** - 财务图表、业绩速览、业绩对比、指标归因
2. **业绩指引** - 业绩预告、经营计划、风险提示
3. **业务亮点** - 各业务板块的亮点和成就
4. **盈利预测和估值** - 一致预测、机构预测、估值分析
5. **总结** - 综合所有部分的总结

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd llamareport-backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件:

```env
# OpenAI API (用于 Embedding)
OPENAI_API_KEY=your_openai_api_key

# DeepSeek API (用于对话模型)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 运行测试

```bash
# 测试系统组件
python test_agent_system.py

# 快速启动向导
python quick_start_agent.py
```

### 4. 启动服务器

```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动。

### 5. 生成报告

#### 方法 1: 使用 API

```bash
curl -X POST "http://localhost:8000/agent/generate-report" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ST数源",
    "year": "2023",
    "save_to_file": true
  }'
```

#### 方法 2: 使用 Python

```python
import asyncio
from core.rag_engine import RAGEngine
from agents.report_agent import ReportAgent

async def generate_report():
    # 初始化
    rag = RAGEngine()
    rag.load_existing_index()
    agent = ReportAgent(rag.query_engine)
    
    # 生成报告
    result = await agent.generate_report(
        company_name="ST数源",
        year="2023"
    )
    
    print(result["report"])

asyncio.run(generate_report())
```

---

## 📚 文档

- **[使用指南](AGENT_SYSTEM_GUIDE.md)** - 详细的使用说明和 API 文档
- **[实施总结](AGENT_IMPLEMENTATION_SUMMARY.md)** - 技术实现细节和架构说明
- **[模板参考](../参考文档/02/模板.md)** - 报告模板格式参考

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户请求                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI (Agent API)                        │
│  /agent/generate-report  /agent/generate-section            │
│  /agent/query           /agent/status                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ReportAgent (FunctionAgent)                     │
│  - 协调工具调用                                              │
│  - 管理工作流程                                              │
│  - 生成结构化输出                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│QueryEngine  │  │Financial    │  │Business     │
│Tool         │  │ReviewTool   │  │GuidanceTool │
│             │  │             │  │             │
│RAG检索      │  │财务点评     │  │业绩指引     │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Pydantic 结构化输出                         │
│  AnnualReportAnalysis                                        │
│  ├─ FinancialReview                                         │
│  ├─ BusinessGuidance                                        │
│  ├─ BusinessHighlights                                      │
│  └─ ProfitForecastAndValuation                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            TemplateRenderer (Jinja2)                         │
│  annual_report_template.md.jinja2                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Markdown 报告                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
llamareport-backend/
├── models/
│   └── report_models.py              # Pydantic 数据模型
├── agents/
│   ├── report_tools.py               # 工具函数
│   ├── report_agent.py               # Agent 配置
│   └── template_renderer.py          # 模板渲染器
├── templates/
│   └── annual_report_template.md.jinja2  # Jinja2 模板
├── api/
│   └── agent.py                      # Agent API 接口
├── core/
│   └── rag_engine.py                 # RAG 引擎
├── test_agent_system.py              # 测试脚本
├── quick_start_agent.py              # 快速启动脚本
├── AGENT_SYSTEM_GUIDE.md             # 使用指南
├── AGENT_IMPLEMENTATION_SUMMARY.md   # 实施总结
└── AGENT_README.md                   # 本文档
```

---

## 🔧 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | API 服务器 |
| LLM | DeepSeek | 对话生成 |
| Embedding | OpenAI | 文本嵌入 |
| Agent 框架 | LlamaIndex FunctionAgent | 智能决策 |
| 数据验证 | Pydantic | 类型安全 |
| 模板引擎 | Jinja2 | 报告渲染 |
| 向量数据库 | ChromaDB | 文档存储 |
| PDF 处理 | pdfplumber | 文档解析 |

---

## 📊 API 端点

### 生成完整报告

```http
POST /agent/generate-report
Content-Type: application/json

{
    "company_name": "公司名称",
    "year": "2023",
    "save_to_file": true,
    "output_path": "reports/report.md"
}
```

### 生成单个章节

```http
POST /agent/generate-section
Content-Type: application/json

{
    "section_name": "financial_review",
    "company_name": "公司名称",
    "year": "2023"
}
```

章节名称:
- `financial_review` - 财务点评
- `business_guidance` - 业绩指引
- `business_highlights` - 业务亮点
- `profit_forecast` - 盈利预测和估值

### 通用查询

```http
POST /agent/query
Content-Type: application/json

{
    "question": "公司的主要业务是什么?"
}
```

### 系统状态

```http
GET /agent/status
```

---

## 🧪 测试

### 运行所有测试

```bash
python test_agent_system.py
```

### 测试结果

```
✅ 通过 - 导入测试
✅ 通过 - 模板渲染器测试
✅ 通过 - RAG 引擎测试
✅ 通过 - Report Agent 测试

总计: 4 个测试通过, 0 个测试失败
🎉 所有测试通过! Agent 系统已准备就绪!
```

---

## 🐛 故障排除

### 问题: "RAG 引擎未初始化"

**解决方案**:
1. 上传 PDF 文档: `POST /upload`
2. 处理文档: `POST /process/{document_id}`
3. 确认索引已创建: `GET /agent/status`

### 问题: "API Key 未设置"

**解决方案**:
检查 `.env` 文件,确保包含:
```env
OPENAI_API_KEY=...
DEEPSEEK_API_KEY=...
```

### 问题: Agent 生成失败

**解决方案**:
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看日志: `llamareport-backend.log`
4. 确保文档已正确处理

---

## 📈 性能优化

### 当前性能

- 单章节生成: ~30-60秒
- 完整报告生成: ~2-5分钟
- 模板渲染: <1秒

### 优化建议

1. **并行生成**: 使用 `asyncio.gather` 并行生成章节
2. **缓存**: 缓存常用的查询结果
3. **流式输出**: 支持 SSE 流式返回
4. **批处理**: 批量处理多个报告请求

---

## 🤝 贡献

欢迎贡献!请遵循以下步骤:

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 👥 作者

- **AI Agent** - *初始开发* - Claude 4.0 Sonnet

---

## 🙏 致谢

- [LlamaIndex](https://www.llamaindex.ai/) - Agent 框架
- [DeepSeek](https://www.deepseek.com/) - LLM 服务
- [OpenAI](https://openai.com/) - Embedding 服务
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Jinja2](https://jinja.palletsprojects.com/) - 模板引擎

---

**版本**: 1.0.0  
**最后更新**: 2025-10-01  
**状态**: ✅ 生产就绪

