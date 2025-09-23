# 🚀 LlamaReportPro - 智能财务报告分析系统

基于LlamaIndex的企业级财务报告AI分析平台，支持多格式文档处理、智能问答和深度分析。

## ✨ 核心功能

### 📄 多格式文档支持
- **PDF文档**: 使用LlamaParse高级解析，支持复杂表格和布局
- **Excel文件**: 智能表格识别和财务数据提取
- **Word文档**: 文本内容和表格的统一处理
- **PowerPoint**: 演示文稿内容提取
- **图片文件**: OCR文本识别
- **CSV/TXT**: 结构化数据处理

### 🤖 AI智能分析
- **RAG问答系统**: 基于LlamaIndex的检索增强生成
- **多引擎路由**: 财务数据、趋势分析、对比分析专门引擎
- **混合检索**: 向量检索 + BM25 + LLM重排序
- **结构化输出**: Pydantic模型驱动的结构化分析

### 📊 财务分析功能
- **比率分析**: 盈利能力、偿债能力、运营效率分析
- **趋势预测**: 基于历史数据的智能预测
- **行业对比**: 同行业公司对比分析
- **风险评估**: 多维度风险因素识别

### 📈 数据可视化
- **交互式图表**: Plotly驱动的动态图表
- **财务仪表板**: 关键指标实时监控
- **趋势分析图**: 时间序列数据可视化
- **对比分析图**: 多维度数据对比

## 🛠️ 技术架构

### 核心技术栈
- **前端框架**: Streamlit 1.28.1
- **AI框架**: LlamaIndex 0.14.0+
- **语言模型**: OpenAI GPT-4o
- **嵌入模型**: text-embedding-3-large
- **向量数据库**: ChromaDB
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly

### LlamaIndex技术组件
```python
# 核心组件
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import QueryFusionRetriever
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- OpenAI API Key
- LlamaParse API Key (可选，用于高级PDF解析)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/LlamaReportPro.git
cd LlamaReportPro
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
创建 `.env` 文件：
```env
OPENAI_API_KEY=your_openai_api_key_here
LLAMA_CLOUD_API_KEY=your_llamaparse_api_key_here  # 可选
```

4. **启动应用**
```bash
streamlit run app.py
```

### Docker部署 (可选)
```bash
# 构建镜像
docker build -t llamareportpro .

# 运行容器
docker run -p 8501:8501 --env-file .env llamareportpro
```

## 📖 使用指南

### 1. 文档上传
- 支持拖拽上传或点击选择文件
- 自动识别文件格式并选择最优处理策略
- 实时显示处理进度和结果

### 2. AI问答
- 自然语言提问，支持中英文
- 智能路由到最合适的查询引擎
- 提供详细的来源引用和相关性评分

### 3. 财务分析
- 自动提取财务指标
- 计算关键财务比率
- 生成趋势分析和预测

### 4. 数据导出
- 支持Excel、PDF、CSV格式导出
- 包含分析结果和可视化图表
- 自定义导出内容和格式

## 🔧 配置说明

### 模型配置
```python
# LLM配置
Settings.llm = OpenAI(
    model="gpt-4o",
    temperature=0.1
)

# 嵌入模型配置
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-large"
)
```

### 检索配置
```python
# 混合检索配置
fusion_retriever = QueryFusionRetriever(
    [vector_retriever, bm25_retriever],
    similarity_top_k=10,
    mode="reciprocal_rerank"
)
```

## 📁 项目结构

```
LlamaReportPro/
├── app.py                 # 主应用入口
├── requirements.txt       # 依赖列表
├── .env.example          # 环境变量模板
├── pages/                # Streamlit页面
│   ├── upload.py         # 文档上传页面
│   ├── qa_system.py      # AI问答页面
│   ├── analysis.py       # 财务分析页面
│   ├── comparison.py     # 对比分析页面
│   ├── insights.py       # 洞察分析页面
│   └── export.py         # 数据导出页面
├── utils/                # 核心工具模块
│   ├── rag_system.py     # RAG系统核心
│   ├── enhanced_query_engines.py  # 增强查询引擎
│   ├── multi_format_processor.py  # 多格式处理器
│   ├── financial_calculator.py    # 财务计算器
│   ├── data_visualizer.py         # 数据可视化
│   └── export_engine.py           # 导出引擎
└── storage/              # 数据存储目录
    └── rag_data/         # RAG索引数据
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LlamaIndex](https://github.com/run-llama/llama_index) - 强大的RAG框架
- [Streamlit](https://streamlit.io/) - 优秀的Web应用框架
- [OpenAI](https://openai.com/) - 先进的语言模型服务

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](https://github.com/yourusername/LlamaReportPro/issues)
- 发送邮件至: your.email@example.com

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
