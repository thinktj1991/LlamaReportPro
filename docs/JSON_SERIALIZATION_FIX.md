# JSON序列化问题修复文档

## 🐛 问题描述

### 错误信息

```
Object of type ToolOutput is not JSON serializable
```

### 错误发生位置

- **文件**: `llamareport-backend/agents/report_agent.py`
- **方法**: `async def query(self, question: str)`
- **行号**: 第355行和第382行

### 错误原因

在Agent查询过程中，`ToolCallResult`事件的`tool_output`属性是一个`ToolOutput`对象。当这个对象被直接添加到返回的字典中时，FastAPI尝试将其序列化为JSON响应时会失败，因为`ToolOutput`对象不是JSON可序列化的类型。

### 错误堆栈

```python
# 原始代码（有问题）
elif isinstance(event, ToolCallResult):
    tool_results.append({
        "tool_name": event.tool_name,
        "tool_kwargs": event.tool_kwargs,
        "tool_output": event.tool_output  # ❌ ToolOutput对象不可序列化
    })
    
    if event.tool_name == "generate_visualization":
        visualization_data = event.tool_output  # ❌ 直接赋值ToolOutput对象

# 返回时
result["visualization"] = visualization_data  # ❌ 导致JSON序列化失败
```

---

## ✅ 解决方案

### 1. 添加序列化方法

在`ReportAgent`类中添加了`_serialize_tool_output`方法，用于将任何类型的对象转换为JSON可序列化的格式。

```python
def _serialize_tool_output(self, tool_output) -> Any:
    """
    将ToolOutput对象转换为可JSON序列化的格式
    
    支持的转换：
    1. 基本类型（str, int, float, bool, None）- 直接返回
    2. 列表/元组 - 递归序列化每个元素
    3. 字典 - 递归序列化每个值
    4. Pydantic模型 - 使用model_dump()或dict()
    5. 自定义对象 - 使用__dict__属性
    6. 其他类型 - 转换为字符串
    """
    try:
        # 基本类型
        if isinstance(tool_output, (str, int, float, bool, type(None))):
            return tool_output
        
        # 列表或元组
        if isinstance(tool_output, (list, tuple)):
            return [self._serialize_tool_output(item) for item in tool_output]
        
        # 字典
        if isinstance(tool_output, dict):
            return {key: self._serialize_tool_output(value) 
                    for key, value in tool_output.items()}
        
        # Pydantic v2模型
        if hasattr(tool_output, 'model_dump'):
            try:
                return tool_output.model_dump()
            except Exception:
                pass
        
        # Pydantic v1模型
        if hasattr(tool_output, 'dict'):
            try:
                return tool_output.dict()
            except Exception:
                pass
        
        # 自定义对象
        if hasattr(tool_output, '__dict__'):
            try:
                return {k: self._serialize_tool_output(v) 
                        for k, v in tool_output.__dict__.items() 
                        if not k.startswith('_')}
            except Exception:
                pass
        
        # 最后尝试转换为字符串
        return str(tool_output)
        
    except Exception as e:
        logger.warning(f"Failed to serialize tool_output: {str(e)}")
        return str(tool_output)
```

### 2. 修改事件处理代码

在处理`ToolCallResult`事件时，使用新的序列化方法：

```python
elif isinstance(event, ToolCallResult):
    logger.info(f"[Agent Query] Tool call result: {event.tool_name}")
    
    # ✅ 将ToolOutput转换为可序列化的格式
    tool_output_serializable = self._serialize_tool_output(event.tool_output)
    
    tool_results.append({
        "tool_name": event.tool_name,
        "tool_kwargs": event.tool_kwargs,
        "tool_output": tool_output_serializable  # ✅ 使用序列化后的数据
    })

    # 如果是可视化工具，保存其输出
    if event.tool_name == "generate_visualization":
        logger.info("[Agent Query] Found visualization tool call")
        visualization_data = tool_output_serializable  # ✅ 使用序列化后的数据
```

---

## 🧪 测试验证

### 测试脚本

创建了`test_json_serialization.py`测试脚本，验证序列化方法的正确性。

### 测试用例

1. **基本类型**
   - ✅ 字符串
   - ✅ 整数
   - ✅ 浮点数
   - ✅ 布尔值
   - ✅ None

2. **集合类型**
   - ✅ 列表
   - ✅ 字典
   - ✅ 嵌套字典

3. **Pydantic模型**
   - ✅ Pydantic v2模型（使用model_dump()）
   - ✅ Pydantic v1模型（使用dict()）

4. **自定义对象**
   - ✅ 带有__dict__属性的对象
   - ✅ 自动过滤私有属性（_开头）

### 测试结果

```
============================================================
测试JSON序列化
============================================================
✅ 字符串: 序列化成功
✅ 整数: 序列化成功
✅ 浮点数: 序列化成功
✅ 布尔值: 序列化成功
✅ None: 序列化成功
✅ 列表: 序列化成功
✅ 字典: 序列化成功
✅ 嵌套字典: 序列化成功
✅ Pydantic模型: 序列化成功
✅ 自定义对象: 序列化成功

============================================================
🎉 所有测试通过！
============================================================
```

---

## 📝 修改文件清单

### 修改的文件

1. **`llamareport-backend/agents/report_agent.py`**
   - 添加了`_serialize_tool_output`方法（第40-90行）
   - 修改了`query`方法中的事件处理逻辑（第344-359行）

### 新增的文件

1. **`test_json_serialization.py`**
   - JSON序列化测试脚本

2. **`docs/JSON_SERIALIZATION_FIX.md`**
   - 本文档

---

## 🔍 技术细节

### LlamaIndex ToolOutput结构

根据LlamaIndex官方文档，`ToolOutput`对象通常包含以下属性：

- `content`: 工具输出的内容
- `tool_name`: 工具名称
- `raw_input`: 原始输入
- `raw_output`: 原始输出

这些属性可能是复杂对象，需要递归序列化。

### Pydantic模型序列化

- **Pydantic v2**: 使用`model_dump()`方法
- **Pydantic v1**: 使用`dict()`方法

我们的序列化方法同时支持两个版本，确保兼容性。

### 递归序列化

对于嵌套结构（如列表中的字典，字典中的对象），我们使用递归方法确保所有层级都被正确序列化。

---

## ⚠️ 注意事项

1. **性能考虑**
   - 序列化方法会递归处理嵌套结构，对于非常深的嵌套可能影响性能
   - 建议工具输出保持合理的复杂度

2. **数据丢失**
   - 私有属性（_开头）会被过滤
   - 无法序列化的复杂对象会被转换为字符串
   - 可能丢失部分类型信息

3. **兼容性**
   - 支持Pydantic v1和v2
   - 支持Python标准库的基本类型
   - 支持自定义类（通过__dict__）

---

## 🚀 使用建议

### 对于工具开发者

如果您正在开发新的Agent工具，建议：

1. **返回简单类型**
   - 优先返回dict、list、str等基本类型
   - 避免返回复杂的自定义对象

2. **使用Pydantic模型**
   - 如果需要结构化输出，使用Pydantic模型
   - 确保模型可以正确序列化

3. **测试序列化**
   - 在工具开发时测试输出是否可以JSON序列化
   - 使用`json.dumps()`验证

### 对于API用户

如果您在使用Agent API时遇到序列化问题：

1. **检查工具输出**
   - 查看`tool_results`中的`tool_output`字段
   - 确认数据格式是否符合预期

2. **报告问题**
   - 如果发现新的序列化问题，请提供详细的错误信息
   - 包括工具名称和输出示例

---

## 📚 参考资料

- [LlamaIndex Agent Documentation](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/)
- [Pydantic Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [Python JSON Module](https://docs.python.org/3/library/json.html)
- [FastAPI JSON Response](https://fastapi.tiangolo.com/advanced/custom-response/)

---

## ✅ 验证清单

- [x] 添加了`_serialize_tool_output`方法
- [x] 修改了事件处理逻辑
- [x] 创建了测试脚本
- [x] 所有测试通过
- [x] 支持Pydantic v1和v2
- [x] 支持基本类型和集合类型
- [x] 支持自定义对象
- [x] 递归处理嵌套结构
- [x] 错误处理和日志记录
- [x] 文档完整

---

## 🎉 总结

通过添加`_serialize_tool_output`方法，我们成功解决了`Object of type ToolOutput is not JSON serializable`错误。这个方法：

1. ✅ 支持多种数据类型
2. ✅ 递归处理嵌套结构
3. ✅ 兼容Pydantic v1和v2
4. ✅ 提供完善的错误处理
5. ✅ 经过充分测试验证

现在Agent API可以正常返回包含工具输出的JSON响应，不会再出现序列化错误。

