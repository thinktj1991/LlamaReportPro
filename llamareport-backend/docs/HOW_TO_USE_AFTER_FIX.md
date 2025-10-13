# RAG修复后使用指南

## 修复内容概述

本次修复解决了系统在回答财务数据问题时"检索成功但理解失败"的问题。主要改进：

1. ✅ **优化表格转文本格式** - 使用Markdown表格，更易于LLM理解
2. ✅ **增强查询引擎配置** - 增加检索数量，改进响应模式
3. ✅ **改进查询增强逻辑** - 明确要求LLM使用检索到的数据

详细修复说明请查看：[RAG_FIX_SUMMARY.md](./RAG_FIX_SUMMARY.md)

## 重要提示 ⚠️

**修复后必须重新处理文档才能生效！**

因为表格转文本的格式改变了，已有的索引使用的是旧格式，需要清空并重建。

## 使用步骤

### 方法一：使用自动化脚本（推荐）

1. **确保API密钥已配置**

   检查 `.env` 文件中的配置：
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ```

2. **运行重建索引脚本**

   ```bash
   cd llamareport-backend
   python scripts/rebuild_index.py
   ```

   或者指定上传目录：
   ```bash
   python scripts/rebuild_index.py --upload-dir ./uploads
   ```

3. **等待处理完成**

   脚本会自动：
   - 清空现有索引
   - 扫描上传目录中的PDF文件
   - 重新处理所有文档
   - 提取表格数据
   - 构建新的向量索引
   - 运行测试查询

4. **启动服务**

   ```bash
   python main.py
   ```

### 方法二：通过Web界面

1. **启动后端服务**

   ```bash
   cd llamareport-backend
   python main.py
   ```

2. **启动前端服务**

   ```bash
   cd llamareport-frontend
   npm run dev
   ```

3. **访问Web界面**

   打开浏览器访问：`http://localhost:5173`

4. **清空并重新上传文档**

   - 在"文档处理"页面，点击"清空索引"按钮
   - 重新上传PDF文件
   - 点击"处理文档"按钮

5. **测试查询**

   在"智能问答"页面测试查询，例如：
   ```
   请帮我分析中公教育科技股份有限公司2023年年度营业收入情况，并且告诉我趋势
   ```

## 验证修复效果

### 1. 运行单元测试

```bash
cd llamareport-backend
python test_rag_fix.py
```

预期输出：
```
✅ 表格转文本测试通过！
✅ 查询增强测试通过！
🎉 所有测试通过！RAG修复成功！
```

### 2. 检查表格格式

查询后，在"参考来源"中应该能看到：
- 📊 表格数据标题
- 💰 财务数据标记
- Markdown格式的表格
- 具体的数值数据

### 3. 检查回答质量

系统回答应该：
- ✅ 包含具体的数值（如：36,643,230.73元）
- ✅ 引用数据来源（如：第20页，表格page_20_table_1）
- ✅ 进行趋势分析（对比不同时期的数据）
- ✅ 提供变动幅度（如：-76.51%）

## 常见问题

### Q1: 重建索引后查询仍然有问题？

**可能原因**：
- API密钥未正确配置
- 文档未正确处理
- 表格提取失败

**解决方法**：
1. 检查日志中的错误信息
2. 确认 `OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY` 已设置
3. 重新上传PDF文件并处理

### Q2: 如何查看索引状态？

**方法1 - 通过API**：
```bash
curl http://localhost:8000/api/status
```

**方法2 - 通过Python**：
```python
from core.rag_engine import RAGEngine
rag = RAGEngine()
stats = rag.get_index_stats()
print(stats)
```

### Q3: 表格数据显示不完整？

**说明**：
- 默认显示最多30行数据
- 如果表格超过30行，会显示"共有X行数据"

**如需显示更多行**：
修改 `llamareport-backend/core/rag_engine.py` 中的 `max_rows` 参数（第298行）

### Q4: 如何清空索引？

**方法1 - 使用脚本**：
```bash
python scripts/rebuild_index.py
```

**方法2 - 使用Python**：
```python
from core.rag_engine import RAGEngine
rag = RAGEngine()
rag.clear_index()
```

**方法3 - 手动删除**：
删除 `storage/chroma` 目录

## 性能优化建议

### 1. 调整检索数量

如果查询结果不够准确，可以增加 `similarity_top_k`：

```python
# 在 rag_engine.py 中
self.query_engine = self.index.as_query_engine(
    similarity_top_k=15,  # 从10增加到15
    response_mode="compact",
    text_qa_template=qa_prompt,
    verbose=True
)
```

### 2. 调整响应模式

可以尝试不同的响应模式：
- `compact` - 当前使用，适合大多数情况
- `refine` - 逐步精炼答案，更准确但较慢
- `tree_summarize` - 树状总结，适合长文档

### 3. 优化表格显示行数

根据实际需求调整显示的表格行数：

```python
# 在 rag_engine.py 的 _table_to_text 方法中
max_rows = min(len(data_rows), 50)  # 从30增加到50
```

## 监控和日志

### 查看详细日志

启动服务时启用详细日志：

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### 日志位置

- 应用日志：控制台输出
- 查询日志：包含查询问题、增强查询、检索结果等

### 关键日志标记

- `✅` - 成功操作
- `❌` - 错误
- `⚠️` - 警告
- `📊` - 表格数据
- `💰` - 财务数据

## 下一步

1. **测试更多查询** - 尝试不同类型的财务问题
2. **收集反馈** - 记录哪些查询效果好，哪些还需改进
3. **持续优化** - 根据实际使用情况调整参数

## 技术支持

如有问题，请查看：
- [RAG修复总结](./RAG_FIX_SUMMARY.md)
- [项目README](../../README.md)
- 或提交Issue到GitHub仓库

---

**最后更新**: 2025-01-13
**版本**: v1.0

