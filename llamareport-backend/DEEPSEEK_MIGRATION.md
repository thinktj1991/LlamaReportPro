# DeepSeek LLM 迁移指南

## 📋 概述

本项目已成功将对话模型从 OpenAI 迁移到 DeepSeek,同时保持 OpenAI Embedding 模型不变。

### 迁移原因
- **成本优化**: DeepSeek 提供更具性价比的对话服务
- **性能保持**: DeepSeek-V3 提供与 GPT-4 相当的性能
- **灵活性**: 保持 OpenAI Embedding 确保向量检索质量

## 🔧 技术架构

### 当前配置
```
┌─────────────────────────────────────┐
│   LlamaReport Backend Architecture  │
├─────────────────────────────────────┤
│                                     │
│  对话模型 (LLM)                      │
│  ├─ Provider: DeepSeek              │
│  ├─ Model: deepseek-chat            │
│  └─ Package: llama-index-llms-deepseek │
│                                     │
│  嵌入模型 (Embedding)                │
│  ├─ Provider: OpenAI                │
│  ├─ Model: text-embedding-3-small  │
│  └─ Package: llama-index-embeddings-openai │
│                                     │
│  向量数据库                          │
│  └─ ChromaDB                        │
└─────────────────────────────────────┘
```

## 📦 依赖变更

### 新增依赖
```txt
llama-index-llms-deepseek>=0.2.0
```

### 完整依赖列表
参见 `requirements.txt`:
- `llama-index-core>=0.14.0`
- `llama-index-llms-deepseek>=0.2.0` ⭐ 新增
- `llama-index-llms-openai>=0.4.0`
- `llama-index-embeddings-openai>=0.5.0`
- `chromadb>=1.1.0`

## 🔑 环境变量配置

### 必需的环境变量

#### `.env` 文件示例
```env
# OpenAI API Configuration (用于 Embedding)
OPENAI_API_KEY=sk-proj-your-openai-key-here

# DeepSeek API Configuration (用于对话模型)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 其他配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 环境变量说明

| 变量名 | 用途 | 默认值 | 必需 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI Embedding 模型 | - | ✅ |
| `DEEPSEEK_API_KEY` | DeepSeek 对话模型 | - | ✅ |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-chat` | ❌ |
| `DEEPSEEK_BASE_URL` | DeepSeek API 端点 | `https://api.deepseek.com` | ❌ |

## 📝 代码变更

### 1. `core/rag_engine.py`

#### 导入变更
```python
# 之前
from llama_index.llms.openai import OpenAI

# 之后
from llama_index.llms.deepseek import DeepSeek
```

#### LLM 初始化变更
```python
# 之前
Settings.llm = OpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    api_key=openai_api_key,
    temperature=0.1
)

# 之后
Settings.llm = DeepSeek(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    api_key=deepseek_api_key,
    temperature=0.1
)
```

#### Embedding 配置 (保持不变)
```python
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=openai_api_key
)
```

### 2. `config.py`

新增 DeepSeek 配置项:
```python
# DeepSeek 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
```

### 3. `main.py`

更新环境变量检查和系统信息:
```python
required_env_vars = {
    "OPENAI_API_KEY": "用于 Embedding 模型",
    "DEEPSEEK_API_KEY": "用于对话模型"
}
```

## 🧪 测试验证

### 运行测试脚本
```bash
cd llamareport-backend
python test_deepseek.py
```

### 测试覆盖
1. ✅ 环境变量检查
2. ✅ DeepSeek API 直接调用
3. ✅ LlamaIndex 集成测试
4. ✅ RAG 引擎配置测试

### 预期输出
```
🎉 所有测试通过! DeepSeek 配置正常!
```

## 🚀 部署步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
创建或更新 `.env` 文件,添加 DeepSeek API Key:
```env
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

### 3. 验证配置
```bash
python test_deepseek.py
```

### 4. 启动服务
```bash
# 方式1: 使用启动脚本
python start.py

# 方式2: 直接启动
python main.py
```

## 📊 性能对比

### DeepSeek vs OpenAI

| 指标 | DeepSeek-V3 | GPT-4o-mini | 说明 |
|------|-------------|-------------|------|
| 成本 | 💰 更低 | 💰💰 较高 | DeepSeek 更具性价比 |
| 性能 | ⚡⚡⚡ 优秀 | ⚡⚡⚡ 优秀 | 性能相当 |
| 中文支持 | 🇨🇳 优秀 | 🇨🇳 良好 | DeepSeek 中文更强 |
| API 兼容性 | ✅ OpenAI 兼容 | ✅ 原生 | 无缝迁移 |

## 🔍 API 使用示例

### DeepSeek Chat API
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-deepseek-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好!"}
    ]
)
```

### LlamaIndex 集成
```python
from llama_index.core import Settings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.openai import OpenAIEmbedding

# 配置 DeepSeek LLM
Settings.llm = DeepSeek(
    model="deepseek-chat",
    api_key="sk-your-deepseek-key",
    temperature=0.1
)

# 配置 OpenAI Embedding
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key="sk-your-openai-key"
)
```

## ⚠️ 注意事项

### 1. API Key 管理
- ✅ 使用环境变量存储 API Key
- ✅ 不要将 API Key 提交到版本控制
- ✅ 定期轮换 API Key

### 2. 模型选择
- `deepseek-chat`: 标准对话模型 (推荐)
- `deepseek-reasoner`: 推理模型 (适合复杂推理任务)

### 3. 成本控制
- 监控 API 使用量
- 设置合理的 `max_tokens` 限制
- 使用缓存减少重复调用

## 🐛 故障排除

### 问题 1: DeepSeek API 调用失败
**症状**: `Authentication failed` 错误

**解决方案**:
1. 检查 `DEEPSEEK_API_KEY` 是否正确设置
2. 验证 API Key 是否有效
3. 确认账户余额充足

### 问题 2: LlamaIndex 集成失败
**症状**: `Unknown model 'deepseek-chat'` 错误

**解决方案**:
1. 确保安装了 `llama-index-llms-deepseek` 包
2. 使用 `DeepSeek` 类而不是 `OpenAI` 类
3. 检查包版本是否兼容

### 问题 3: Embedding 失败
**症状**: OpenAI Embedding 错误

**解决方案**:
1. 检查 `OPENAI_API_KEY` 是否正确
2. 确认 OpenAI 账户状态正常
3. 验证网络连接

## 📚 参考资源

### 官方文档
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [LlamaIndex DeepSeek 集成](https://developers.llamaindex.ai/python/examples/llm/deepseek/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)

### 相关链接
- [DeepSeek 官网](https://www.deepseek.com/)
- [DeepSeek GitHub](https://github.com/deepseek-ai)
- [LlamaIndex GitHub](https://github.com/run-llama/llama_index)

## 📞 支持

如有问题,请:
1. 查看本文档的故障排除部分
2. 运行 `python test_deepseek.py` 诊断问题
3. 查看日志文件 `llamareport-backend.log`
4. 提交 Issue 到项目仓库

---

**最后更新**: 2025-10-01  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪

