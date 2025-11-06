# LlamaReport Backend - 简化版

> 专注于文档处理和RAG问答的轻量级财务报告分析后端

## 🎯 项目概述

LlamaReport Backend 是原LlamaReportPro项目的简化版本，移除了复杂的前端界面和可视化功能，专注于核心的文档处理和智能问答能力。

### 核心功能

- 📄 **PDF文档处理** - 文本提取和预处理
- 📊 **表格数据提取** - 财务表格识别和分析
- 🤖 **RAG智能问答** - 基于文档内容的智能问答
- 🔍 **向量检索** - 高效的语义搜索
- 📈 **实时数据查询** - ⭐ NEW 实时股价、新闻、公告
- ⚠️ **智能预警** - ⭐ NEW 异常检测和风险提示

### 技术栈

- **Web框架**: FastAPI
- **文档处理**: LlamaIndex + PDFPlumber
- **向量数据库**: ChromaDB
- **LLM服务**: DeepSeek + OpenAI Embedding
- **数据处理**: Pandas
- **实时数据**: ⭐ Tushare + 新浪财经 + 新闻聚合

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- OpenAI API Key

### 2. 安装依赖

```bash
cd llamareport-backend
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件：

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 4. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
python start.py

# 方式2: 直接启动
python main.py

# 方式3: 使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问API

- **API文档**: http://localhost:8000/docs
- **主页**: http://localhost:8000
- **健康检查**: http://localhost:8000/health

## 📚 API接口

### 文件上传

```bash
# 上传单个文件
curl -X POST "http://localhost:8000/upload/file" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@report.pdf"

# 查看已上传文件
curl "http://localhost:8000/upload/list"
```

### 文档处理

```bash
# 处理文档并构建索引
curl -X POST "http://localhost:8000/process/file" \
  -H "Content-Type: application/json" \
  -d '{"filename": "report.pdf", "build_index": true}'

# 查看处理状态
curl "http://localhost:8000/process/status"
```

### 智能问答

```bash
# 提问
curl -X POST "http://localhost:8000/query/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "公司的营业收入是多少？"}'

# 获取相似内容
curl -X POST "http://localhost:8000/query/similar" \
  -H "Content-Type: application/json" \
  -d '{"query": "财务数据", "top_k": 5}'
```

### 实时数据查询 ⭐ NEW

```bash
# 获取实时股价
curl "http://localhost:8000/realtime/quote/600519.SH"

# 获取最新新闻
curl -X POST "http://localhost:8000/realtime/news" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "贵州茅台", "limit": 5}'

# 检查股票预警
curl "http://localhost:8000/realtime/alerts/600519.SH"

# 获取市场概览
curl "http://localhost:8000/realtime/market/overview"

# 通过 Agent 综合查询
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "贵州茅台现在值得投资吗？"}'
```

## 🏗️ 项目结构

```
llamareport-backend/
├── main.py              # FastAPI主应用
├── config.py            # 配置管理
├── requirements.txt     # 依赖包列表
├── .env                 # 环境变量
├── start.py             # 启动脚本
├── test_backend.py      # 测试脚本
├── README.md            # 项目文档
├── core/                # 核心模块
│   ├── __init__.py
│   ├── document_processor.py  # 文档处理器
│   ├── table_extractor.py     # 表格提取器
│   └── rag_engine.py          # RAG引擎
├── api/                 # API接口
│   ├── __init__.py
│   ├── upload.py        # 文件上传接口
│   ├── process.py       # 文档处理接口
│   ├── query.py         # 查询接口
│   ├── agent.py         # Agent接口
│   └── realtime.py      # ⭐ 实时数据接口
├── agents/              # ⭐ Agent系统
│   ├── report_agent.py  # 报告Agent
│   ├── report_tools.py  # 报告工具
│   ├── realtime_tools.py # ⭐ 实时数据工具
│   └── ...
├── data_sources/        # ⭐ 数据源适配器
│   ├── base.py          # 基类
│   ├── tushare_source.py # Tushare数据源
│   ├── sina_source.py   # 新浪财经数据源
│   └── news_source.py   # 新闻数据源
├── models/              # ⭐ 数据模型
│   ├── report_models.py # 报告模型
│   └── realtime_models.py # ⭐ 实时数据模型
├── uploads/             # 上传文件目录
└── storage/             # 数据存储目录
    └── chroma/          # ChromaDB数据
```

## 🧪 测试

```bash
# 运行完整测试
python test_backend.py

# 测试特定功能
python -c "from test_backend import test_imports; test_imports()"
```

## 📖 使用示例

### 完整工作流程

```python
import requests

base_url = "http://localhost:8000"

# 1. 上传文件
with open("financial_report.pdf", "rb") as f:
    response = requests.post(f"{base_url}/upload/file", files={"file": f})
    print(response.json())

# 2. 处理文档
response = requests.post(f"{base_url}/process/file", 
    json={"filename": "financial_report.pdf", "build_index": True})
print(response.json())

# 3. 智能问答
response = requests.post(f"{base_url}/query/ask",
    json={"question": "公司去年的净利润是多少？"})
print(response.json())
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必需 |
| `OPENAI_MODEL` | 使用的模型 | `gpt-4o-mini` |

### 系统限制

- 最大文件大小: 50MB
- 支持格式: PDF
- 批量处理: 最多10个文件
- 查询长度: 最多1000字符

## 🔧 故障排除

### 常见问题

1. **ImportError: No module named 'xxx'**
   ```bash
   pip install -r requirements.txt
   ```

2. **OpenAI API错误**
   - 检查API密钥是否正确设置
   - 确认账户有足够余额

3. **文件上传失败**
   - 检查文件大小是否超过50MB
   - 确认文件格式为PDF

4. **索引构建失败**
   - 检查存储目录权限
   - 确认ChromaDB正常工作

### 日志查看

```bash
# 查看应用日志
tail -f llamareport-backend.log

# 查看详细错误
python main.py --log-level debug
```

## 📈 性能优化

### 建议配置

- **内存**: 最少4GB，推荐8GB+
- **存储**: SSD推荐，至少10GB可用空间
- **网络**: 稳定的互联网连接（OpenAI API）

### 优化建议

1. 使用SSD存储提升文件处理速度
2. 增加内存以处理大型文档
3. 考虑使用本地LLM减少API调用

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交Issue或联系开发团队。

---

**核心特点**:
- ✅ 移除了Streamlit前端
- ✅ 专注核心功能
- ✅ 代码量减少70%
- ✅ 依赖减少60%
- ✅ 启动速度提升80%
- ✅ ⭐ NEW 实时数据集成（股价、新闻、公告）
- ✅ ⭐ NEW 智能预警系统
- ✅ ⭐ NEW 历史与实时数据联动分析

---

## ⭐ 实时数据功能 (NEW)

### 功能简介

实时数据功能将系统从"历史年报分析"升级为"全方位财务智能平台":

- 📈 **实时股价**: 获取最新价格、涨跌幅、成交量、估值指标
- 📰 **财经新闻**: 追踪公司最新动态和行业新闻
- 📢 **公司公告**: 获取官方公告、业绩预告等
- ⚠️ **智能预警**: 自动检测价格异常、成交量异常等
- 📊 **市场概览**: 查看主要指数实时情况
- 🔄 **综合分析**: 结合历史和实时数据的深度分析

### 快速开始

#### 1. 配置（可选）

在 `.env` 文件中添加（可选但推荐）:
```env
TUSHARE_API_TOKEN=your-token-here  # 获取: https://tushare.pro/register
ENABLE_REALTIME_DATA=true
```

**说明**: 不配置 Tushare Token 时，系统会使用免费的新浪财经数据源。

#### 2. 使用示例

**通过 Agent 使用（推荐）**:
```python
# 综合分析 - Agent 会自动调用合适的工具
response = await agent.query("贵州茅台现在值得投资吗？")

# Agent 执行流程:
# 1. get_realtime_stock_price → 获取当前价格和估值
# 2. annual_report_query → 查询历史业绩
# 3. get_latest_financial_news → 了解最新动态
# 4. check_stock_alerts → 检查风险
# 5. 综合分析 → 给出投资建议
```

**直接使用工具**:
```python
from agents.realtime_tools import (
    get_realtime_stock_price,
    get_latest_financial_news
)

# 获取实时股价
price_info = get_realtime_stock_price("600519.SH")

# 获取最新新闻
news = get_latest_financial_news("贵州茅台", 5)
```

### 详细文档

- 📖 [实时数据使用指南](./REALTIME_DATA_GUIDE.md) - 完整配置和使用说明
- 📚 [功能示例文档](./REALTIME_FEATURE_EXAMPLES.md) - 详细使用示例
- 📊 [功能总结](./REALTIME_FEATURE_SUMMARY.md) - 技术实现总结

### 数据源说明

| 数据源 | 用途 | 成本 | 特点 |
|--------|------|------|------|
| **新浪财经** | 实时行情 | 免费 | 无需Token，实时性好 |
| **Tushare** | 全面数据 | 免费/付费 | 可选，数据更全 |
| **新闻聚合** | 新闻/公告 | 免费 | 多源聚合 |

---
