"""
年报分析 Agent 主配置
使用 FunctionAgent 协调各个工具生成完整报告
"""

import logging
import warnings
from typing import Dict, Any, Optional
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage

# 忽略Pydantic JSON schema警告（query_engine参数通过partial绑定，不需要序列化）
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.json_schema")
from models.report_models import AnnualReportAnalysis
from agents.report_tools import (
    generate_financial_review,
    generate_business_guidance,
    generate_business_highlights,
    generate_profit_forecast_and_valuation,
    retrieve_financial_data,
    retrieve_business_data
)
from agents.visualization_agent import generate_visualization_for_query
from agents.dupont_tools import generate_dupont_analysis

logger = logging.getLogger(__name__)


class ReportAgent:
    """年报分析 Agent"""

    def __init__(self, query_engine):
        """
        初始化 Agent

        Args:
            query_engine: LlamaIndex 查询引擎
        """
        self.query_engine = query_engine
        self.agent = None
        self._setup_agent()

    def _serialize_tool_output(self, tool_output) -> Any:
        """
        将ToolOutput对象转换为可JSON序列化的格式

        Args:
            tool_output: ToolOutput对象或其他类型

        Returns:
            可序列化的数据（dict, str, list等）
        """
        try:
            # 如果是字符串，检查是否是JSON字符串，如果是则解析
            if isinstance(tool_output, str):
                # 如果字符串看起来像JSON，尝试解析
                if tool_output.strip().startswith(('{', '[')):
                    try:
                        import json
                        parsed = json.loads(tool_output)
                        # 递归处理解析后的内容
                        return self._serialize_tool_output(parsed)
                    except (json.JSONDecodeError, ValueError):
                        pass
                # 普通字符串直接返回
                return tool_output

            # 处理 Decimal 类型（转换为 float 以便 JSON 序列化）
            try:
                from decimal import Decimal
                if isinstance(tool_output, Decimal):
                    return float(tool_output)
            except ImportError:
                pass
            
            # 如果是数字、布尔值、None，直接返回
            if isinstance(tool_output, (int, float, bool, type(None))):
                return tool_output

            # 如果是列表或元组，递归序列化每个元素
            if isinstance(tool_output, (list, tuple)):
                return [self._serialize_tool_output(item) for item in tool_output]

            # 如果是字典，递归序列化每个值
            if isinstance(tool_output, dict):
                return {key: self._serialize_tool_output(value) for key, value in tool_output.items()}

            # 如果有dict()方法（Pydantic模型等）
            if hasattr(tool_output, 'dict'):
                try:
                    return tool_output.dict()
                except Exception as e:
                    logger.debug(f"Failed to call dict() on {type(tool_output)}: {e}")
                    pass

            # 如果有model_dump()方法（Pydantic v2）
            if hasattr(tool_output, 'model_dump'):
                try:
                    return tool_output.model_dump()
                except Exception as e:
                    logger.debug(f"Failed to call model_dump() on {type(tool_output)}: {e}")
                    pass

            # 如果有model_dump_json()方法，先转换为JSON字符串再解析
            if hasattr(tool_output, 'model_dump_json'):
                try:
                    import json
                    json_str = tool_output.model_dump_json()
                    return json.loads(json_str)
                except Exception as e:
                    logger.debug(f"Failed to call model_dump_json() on {type(tool_output)}: {e}")
                    pass

            # 如果有__dict__属性
            if hasattr(tool_output, '__dict__'):
                try:
                    return {k: self._serialize_tool_output(v) for k, v in tool_output.__dict__.items() if not k.startswith('_')}
                except Exception as e:
                    logger.debug(f"Failed to access __dict__ on {type(tool_output)}: {e}")
                    pass

            # 最后尝试转换为字符串
            return str(tool_output)

        except Exception as e:
            logger.warning(f"Failed to serialize tool_output: {str(e)}, converting to string")
            return str(tool_output)
    
    def _setup_agent(self):
        """设置 Agent 和工具"""
        try:
            # 1. 创建 QueryEngineTool (用于基础数据检索)
            query_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engine,
                name="annual_report_query",
                description=(
                    "用于从年报中检索基础信息的工具。"
                    "可以查询财务数据、业务数据、公司信息等。"
                    "输入应该是一个自然语言查询。"
                )
            )
            
            # 2. 创建专门的章节生成工具
            # 注意: 这些工具需要 query_engine 参数,我们使用 partial 来绑定
            from functools import partial
            
            financial_review_tool = FunctionTool.from_defaults(
                fn=partial(generate_financial_review, query_engine=self.query_engine),
                name="generate_financial_review",
                description=(
                    "生成财务点评章节。"
                    "需要参数: company_name(公司名称), year(年份)。"
                    "返回包含财务图表、业绩速览、业绩对比、指标归因的结构化数据。"
                )
            )
            
            business_guidance_tool = FunctionTool.from_defaults(
                fn=partial(generate_business_guidance, query_engine=self.query_engine),
                name="generate_business_guidance",
                description=(
                    "生成业绩指引章节。"
                    "需要参数: company_name(公司名称), year(年份)。"
                    "返回包含业绩预告、经营计划、风险提示的结构化数据。"
                )
            )
            
            business_highlights_tool = FunctionTool.from_defaults(
                fn=partial(generate_business_highlights, query_engine=self.query_engine),
                name="generate_business_highlights",
                description=(
                    "生成业务亮点章节。"
                    "需要参数: company_name(公司名称), year(年份)。"
                    "返回各业务板块的亮点和成就。"
                )
            )
            
            profit_forecast_tool = FunctionTool.from_defaults(
                fn=partial(generate_profit_forecast_and_valuation, query_engine=self.query_engine),
                name="generate_profit_forecast_and_valuation",
                description=(
                    "生成盈利预测和估值章节。"
                    "需要参数: company_name(公司名称), year(年份)。"
                    "返回一致预测、机构预测、估值分析的结构化数据。"
                )
            )
            
            # 3. 创建数据检索辅助工具
            financial_data_tool = FunctionTool.from_defaults(
                fn=partial(retrieve_financial_data, query_engine=self.query_engine),
                name="retrieve_financial_data",
                description=(
                    "检索特定的财务数据。"
                    "需要参数: company_name(公司名称), year(年份), "
                    "metric_type(指标类型: revenue/profit/cash_flow/balance_sheet)。"
                )
            )
            
            business_data_tool = FunctionTool.from_defaults(
                fn=partial(retrieve_business_data, query_engine=self.query_engine),
                name="retrieve_business_data",
                description=(
                    "检索业务相关数据。"
                    "需要参数: company_name(公司名称), year(年份), business_type(业务类型)。"
                )
            )

            # 可视化生成工具
            visualization_tool = FunctionTool.from_defaults(
                fn=generate_visualization_for_query,
                name="generate_visualization",
                description=(
                    "为查询和回答生成可视化图表。"
                    "需要参数: query(用户查询), answer(文本回答)。"
                    "可选参数: data(原始数据), sources(数据来源)。"
                    "返回包含图表配置的可视化响应。"
                )
            )

            # 杜邦分析工具（新增）
            dupont_analysis_tool = FunctionTool.from_defaults(
                fn=partial(generate_dupont_analysis, query_engine=self.query_engine),
                name="generate_dupont_analysis",
                description=(
                    "生成杜邦分析报告。"
                    "杜邦分析将净资产收益率(ROE)分解为资产净利率、资产周转率和权益乘数，"
                    "帮助深入理解公司盈利能力的驱动因素。"
                    "需要参数: company_name(公司名称), year(年份)。"
                    "返回包含ROE分解、各层级指标、可视化图表的结构化数据。"
                )
            )

            # 4. 组装所有工具
            tools = [
                query_tool,
                financial_review_tool,
                business_guidance_tool,
                business_highlights_tool,
                profit_forecast_tool,
                financial_data_tool,
                business_data_tool,
                visualization_tool,  # 可视化工具
                dupont_analysis_tool  # 杜邦分析工具（新增）
            ]
            
            # 5. 创建 FunctionAgent
            system_prompt = """
你是一个资深的财务分析专家和年报分析师，拥有20年以上的行业经验。你的任务是生成高质量、专业、深入的年报分析报告。

## 核心职责
1. **深度理解用户需求**：准确理解用户的分析意图，识别关键分析维度
2. **精准数据检索**：使用工具从年报中提取准确、完整的财务和业务数据
3. **专业分析生成**：基于真实数据生成客观、专业、有洞察力的分析报告
4. **智能可视化**：在适当时机生成图表，直观展示数据趋势和对比
5. **深度财务分析**：当涉及盈利能力分析时，使用杜邦分析工具进行ROE分解

## 报告结构（标准五部分）
一、**财务点评** (使用 generate_financial_review 工具)
   - 财务图表描述：识别并描述主要财务图表
   - 业绩速览：详细分析核心财务指标
   - 业绩对比：与预期、同行业、历史数据对比
   - 指标归因：深入分析各指标变动原因

二、**业绩指引** (使用 generate_business_guidance 工具)
   - 业绩预告期间和预期
   - 各业务板块的具体指引
   - 风险提示和不确定性说明

三、**业务亮点** (使用 generate_business_highlights 工具)
   - 各业务类型的核心亮点
   - 主要成就和里程碑
   - 业务创新和突破

四、**盈利预测和估值** (使用 generate_profit_forecast_and_valuation 工具)
   - 一致预测和市场预期
   - 机构评级和目标价
   - 估值分析和投资建议

五、**综合总结**
   - 基于前四部分生成综合性的投资建议
   - 突出核心观点和关键洞察
   - 提供风险提示和机会分析

## 工作流程（智能执行 - 严格遵循）
⚠️ **关键原则：每个工具内部已经包含了数据检索，不要重复调用检索工具！**

### 🚫 禁止的操作（避免重复检索）
1. **不要**在调用生成工具前先调用 `annual_report_query` 或 `retrieve_financial_data`
2. **不要**在调用 `generate_financial_review` 前先调用 `retrieve_financial_data`（工具内部已包含）
3. **不要**在调用 `generate_business_guidance` 前先调用 `annual_report_query`（工具内部已包含）
4. **不要**为了简单问题调用所有生成工具

### ✅ 正确的调用方式

#### 简单问题（快速响应 - 5秒内完成）
- 如果用户只是询问基本信息（如"公司名称"、"报告年份"、"基本财务数据"），**只调用** `annual_report_query` 工具
- **不要**调用任何生成工具（generate_*），这会增加50-100秒的响应时间

#### 特定分析需求（按需调用 - 30-60秒）
- **财务分析相关**：**只调用** `generate_financial_review`（工具内部会自动检索数据，无需额外调用）
- **业绩指引相关**：**只调用** `generate_business_guidance`（工具内部会自动检索数据）
- **业务亮点相关**：**只调用** `generate_business_highlights`（工具内部会自动检索数据）
- **盈利预测相关**：**只调用** `generate_profit_forecast_and_valuation`（工具内部会自动检索数据）
- **杜邦分析相关**：**只调用** `generate_dupont_analysis`（工具内部会自动检索数据）
- **可视化需求**：在生成分析后，**只调用** `generate_visualization`

#### 完整报告需求（按顺序调用 - 最多调用4个工具）
**只有在用户明确要求"完整报告"、"生成所有章节"、"全面分析"时，才按以下顺序调用：**
1. **直接调用生成工具**（不要先调用 annual_report_query）：
   - `generate_financial_review` → 自动检索并生成财务点评
   - `generate_business_guidance` → 自动检索并生成业绩指引
   - `generate_business_highlights` → 自动检索并生成业务亮点
   - `generate_profit_forecast_and_valuation` → 自动检索并生成盈利预测
2. **可选增强**：
   - 如涉及盈利能力，调用 `generate_dupont_analysis`
   - 识别数值数据，调用 `generate_visualization`

### ⚡ 性能优化原则（严格执行）
- ✅ **直接调用生成工具**：每个生成工具内部已包含数据检索，无需额外调用
- ✅ **避免重复检索**：不要先调用 annual_report_query 再调用生成工具
- ✅ **按需调用**：只调用与用户问题直接相关的工具
- ✅ **快速响应**：简单问题只调用 annual_report_query（5秒内完成）
- ❌ **禁止过度调用**：避免为了简单问题调用所有工具（会增加400秒+的响应时间）
- ❌ **禁止重复调用**：不要重复调用相同工具或检索相同数据

## 可视化策略
- **趋势分析**：折线图或面积图（时间序列数据）
- **对比分析**：柱状图或分组柱状图（多维度对比）
- **占比分析**：饼图或堆叠柱状图（结构分析）
- **财务指标**：分组柱状图（多指标对比）
- **相关性分析**：散点图或热力图（关联性分析）

## 质量要求（严格执行）
1. **数据准确性**
   - 所有数据必须来源于年报原文
   - 数据引用需标注来源和页码
   - 对缺失数据明确说明，不编造

2. **分析专业性**
   - 使用专业财务术语和分析方法
   - 提供数据支撑的结论，避免主观臆断
   - 识别关键财务风险和机会

3. **内容完整性**
   - 覆盖所有关键分析维度
   - 提供充分的背景信息和上下文
   - 确保逻辑清晰、结构完整

4. **表达清晰性**
   - 使用结构化的格式（标题、列表、表格）
   - 关键数据用数字和百分比明确表达
   - 复杂概念用通俗语言解释

5. **洞察深度**
   - 不仅描述数据，更要分析原因和影响
   - 提供前瞻性的判断和建议
   - 识别数据背后的业务逻辑

## 错误处理
- 如果某个工具调用失败，记录错误但继续执行其他部分
- 如果数据缺失，明确说明并基于可用数据进行分析
- 如果分析遇到困难，使用 annual_report_query 获取更多上下文

## 输出格式
- 使用Markdown格式，包含标题、列表、表格等
- 关键数据用**粗体**或数字突出显示
- 使用emoji增强可读性（但不过度使用）
- 确保输出可以直接用于报告或演示
"""
            
            self.agent = FunctionAgent(
                tools=tools,
                llm=Settings.llm,
                system_prompt=system_prompt,
                name="annual_report_analyst",
                verbose=True
            )
            
            logger.info("✅ ReportAgent 初始化成功")
            
        except Exception as e:
            logger.error(f"❌ ReportAgent 初始化失败: {str(e)}")
            raise
    
    async def generate_report(
        self,
        company_name: str,
        year: str,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成完整的年报分析报告
        
        Args:
            company_name: 公司名称
            year: 年份
            user_query: 用户的自定义查询(可选)
        
        Returns:
            完整的年报分析报告
        """
        try:
            logger.info(f"开始生成年报分析: {company_name} {year}年")
            
            # 构建查询
            if user_query:
                query = user_query
            else:
                query = f"请生成{company_name} {year}年的完整年报分析报告,包括财务点评、业绩指引、业务亮点、盈利预测和估值、以及总结。"
            
            # 运行 Agent
            response = await self.agent.run(query)
            
            logger.info(f"✅ 年报分析生成成功")
            
            return {
                "status": "success",
                "company_name": company_name,
                "year": year,
                "report": str(response),
                "structured_response": response.structured_response if hasattr(response, 'structured_response') else None
            }
            
        except Exception as e:
            logger.error(f"❌ 生成年报分析失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "company_name": company_name,
                "year": year
            }
    
    async def generate_section(
        self,
        section_name: str,
        company_name: str,
        year: str
    ) -> Dict[str, Any]:
        """
        生成单个章节
        
        Args:
            section_name: 章节名称 (financial_review, business_guidance, business_highlights, profit_forecast)
            company_name: 公司名称
            year: 年份
        
        Returns:
            章节内容
        """
        try:
            logger.info(f"开始生成章节: {section_name}")
            
            section_map = {
                "financial_review": "财务点评",
                "business_guidance": "业绩指引",
                "business_highlights": "业务亮点",
                "profit_forecast": "盈利预测和估值"
            }
            
            section_chinese = section_map.get(section_name, section_name)
            query = f"请生成{company_name} {year}年的{section_chinese}章节。"
            
            response = await self.agent.run(query)
            
            logger.info(f"✅ 章节生成成功: {section_name}")
            
            return {
                "status": "success",
                "section_name": section_name,
                "content": str(response),
                "structured_response": response.structured_response if hasattr(response, 'structured_response') else None
            }
            
        except Exception as e:
            logger.error(f"❌ 生成章节失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "section_name": section_name
            }
    
    async def query(self, question: str) -> Dict[str, Any]:
        """
        通用查询接口

        Args:
            question: 用户问题

        Returns:
            查询结果（包含可视化数据）
        """
        import time
        query_start_time = time.time()
        try:
            logger.info(f"[Agent Query] 🚀 Starting query: {question[:100]}...")

            # 导入必要的事件类型
            from llama_index.core.agent.workflow import (
                ToolCallResult,
                ToolCall,
                AgentStream
            )
            logger.info("[Agent Query] Successfully imported event types")

            # 运行 Agent 并捕获事件
            handler = self.agent.run(question)
            logger.info("[Agent Query] Got handler, starting event stream")

            # 收集工具调用结果
            visualization_data = None
            tool_results = []

            # 流式处理事件以捕获工具调用结果 - 添加性能监控
            import time
            query_start_time = time.time()
            tool_call_times = {}  # 记录每个工具调用的时间
            
            try:
                async for event in handler.stream_events():
                    event_time = time.time() - query_start_time
                    logger.info(f"[Agent Query] [{event_time:.2f}s] Got event: {type(event).__name__}")

                    if isinstance(event, ToolCall):
                        tool_start_time = time.time()
                        tool_call_times[event.tool_name] = {
                            "start": tool_start_time,
                            "kwargs": event.tool_kwargs
                        }
                        logger.info(f"[Agent Query] [{event_time:.2f}s] 🔧 Tool call: {event.tool_name} with {event.tool_kwargs}")

                    elif isinstance(event, ToolCallResult):
                        tool_end_time = time.time()
                        tool_name = event.tool_name
                        
                        # 计算工具执行时间
                        if tool_name in tool_call_times:
                            tool_duration = tool_end_time - tool_call_times[tool_name]["start"]
                            logger.info(f"[Agent Query] [{event_time:.2f}s] ✅ Tool result: {tool_name} (耗时: {tool_duration:.2f}秒)")
                            
                            # 如果工具执行时间过长，发出警告
                            if tool_duration > 30.0:
                                logger.warning(f"⚠️ [{event_time:.2f}s] 工具 {tool_name} 执行时间过长: {tool_duration:.2f}秒，可能影响整体性能")
                        else:
                            logger.info(f"[Agent Query] [{event_time:.2f}s] ✅ Tool result: {tool_name}")

                        try:
                            # 将ToolOutput转换为可序列化的格式
                            serialize_start = time.time()
                            
                            # 先尝试直接序列化
                            try:
                                tool_output_serializable = self._serialize_tool_output(event.tool_output)
                            except Exception as serialize_error:
                                logger.warning(f"⚠️ [{event_time:.2f}s] 工具 {tool_name} 序列化失败，使用备用方法: {str(serialize_error)}")
                                # 备用序列化方法
                                if hasattr(event.tool_output, '__dict__'):
                                    tool_output_serializable = {k: str(v) for k, v in event.tool_output.__dict__.items() if not k.startswith('_')}
                                else:
                                    tool_output_serializable = {"raw_output": str(event.tool_output), "serialization_error": str(serialize_error)}
                            
                            serialize_duration = time.time() - serialize_start
                            
                            if serialize_duration > 1.0:
                                logger.warning(f"⚠️ [{event_time:.2f}s] 工具 {tool_name} 序列化耗时: {serialize_duration:.2f}秒")

                            # 调试：输出工具输出的详细信息
                            logger.info(f"🔍 [Agent Query] 工具 {tool_name} 输出类型: {type(tool_output_serializable).__name__}")
                            if isinstance(tool_output_serializable, dict):
                                logger.info(f"🔍 [Agent Query] 工具 {tool_name} 输出键: {list(tool_output_serializable.keys())[:10]}")
                                if "error" in tool_output_serializable:
                                    logger.error(f"❌ [{event_time:.2f}s] 工具 {tool_name} 返回错误: {tool_output_serializable.get('error', '未知错误')}")
                                elif "status" in tool_output_serializable and tool_output_serializable.get("status") == "error":
                                    logger.error(f"❌ [{event_time:.2f}s] 工具 {tool_name} 执行失败: {tool_output_serializable.get('error', '未知错误')}")
                            elif isinstance(tool_output_serializable, str):
                                logger.info(f"🔍 [Agent Query] 工具 {tool_name} 输出字符串长度: {len(tool_output_serializable)}")
                                if len(tool_output_serializable) > 0:
                                    logger.info(f"🔍 [Agent Query] 工具 {tool_name} 输出字符串（前200字符）: {tool_output_serializable[:200]}")

                            # 确保工具输出是可序列化的字典格式
                            tool_result = {
                                "tool_name": tool_name,
                                "tool_kwargs": event.tool_kwargs,
                                "tool_output": tool_output_serializable,
                                "execution_time": tool_call_times.get(tool_name, {}).get("duration", None)
                            }
                            
                            if tool_name in tool_call_times:
                                tool_result["execution_time"] = tool_end_time - tool_call_times[tool_name]["start"]
                            
                            tool_results.append(tool_result)
                            
                            logger.info(f"✅ [Agent Query] [{event_time:.2f}s] 工具 {tool_name} 结果已添加到tool_results，当前总数: {len(tool_results)}")

                            # 如果是可视化工具，保存其输出
                            if tool_name == "generate_visualization":
                                logger.info(f"[Agent Query] [{event_time:.2f}s] Found visualization tool call")
                                visualization_data = tool_output_serializable
                        except Exception as serialize_error:
                            error_time = time.time() - query_start_time
                            logger.error(f"❌ [{error_time:.2f}s] Failed to serialize tool output for {tool_name}: {str(serialize_error)}")
                            import traceback
                            logger.error(f"[Agent Query] 序列化错误堆栈:\n{traceback.format_exc()}")
                            # 即使序列化失败，也记录工具调用
                            tool_result = {
                                "tool_name": tool_name,
                                "tool_kwargs": event.tool_kwargs,
                                "tool_output": f"序列化失败: {str(serialize_error)}",
                                "error": str(serialize_error),
                                "error_location": "tool_output_serialization"
                            }
                            tool_results.append(tool_result)

                    elif isinstance(event, AgentStream):
                        # 流式输出（可选）
                        pass

            except Exception as stream_error:
                stream_error_time = time.time() - query_start_time
                logger.error(f"❌ [{stream_error_time:.2f}s] Error during event streaming: {str(stream_error)}")
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"[Agent Query] 事件流错误堆栈:\n{error_traceback}")
                
                # 记录已完成的工具调用
                logger.error(f"[Agent Query] 已完成 {len(tool_results)} 个工具调用:")
                for i, tool_result in enumerate(tool_results, 1):
                    logger.error(f"  {i}. {tool_result.get('tool_name', 'unknown')} - {tool_result.get('execution_time', 'N/A')}秒")
                
                # 重新抛出异常，但包含更多上下文
                raise Exception(f"事件流处理错误（耗时: {stream_error_time:.2f}秒，已完成{len(tool_results)}个工具调用）: {str(stream_error)}")

            # 获取最终响应 - 添加超时保护（1.5分钟，留出缓冲时间）
            logger.info("[Agent Query] Waiting for final response")
            import time
            response_start_time = time.time()
            try:
                import asyncio
                # 设置超时（1.5分钟，给Agent足够时间但不超过总体2分钟限制）
                timeout_seconds = 90.0  # 1.5分钟
                response = await asyncio.wait_for(handler, timeout=timeout_seconds)
                response_elapsed = time.time() - response_start_time
                logger.info(f"[Agent Query] Got final response type: {type(response)}, 耗时: {response_elapsed:.2f}秒")
            except asyncio.TimeoutError:
                response_elapsed = time.time() - response_start_time
                logger.error(f"[Agent Query] Timeout waiting for final response ({timeout_seconds/60:.1f} minutes), 实际耗时: {response_elapsed:.2f}秒")
                raise Exception(f"Agent响应超时（超过{int(timeout_seconds/60)}分钟，实际耗时: {response_elapsed:.2f}秒），请简化查询或使用普通查询模式")
            except Exception as e:
                response_elapsed = time.time() - response_start_time
                logger.error(f"[Agent Query] Error waiting for final response (耗时: {response_elapsed:.2f}秒): {str(e)}")
                import traceback
                logger.error(f"[Agent Query] 错误堆栈:\n{traceback.format_exc()}")
                raise

            # 提取回答内容 - 增强版本，支持更多响应格式
            answer_text = ""
            try:
                if hasattr(response, 'message'):
                    if hasattr(response.message, 'content'):
                        answer_text = str(response.message.content)
                    elif hasattr(response.message, 'text'):
                        answer_text = str(response.message.text)
                    else:
                        answer_text = str(response.message)
                elif hasattr(response, 'content'):
                    answer_text = str(response.content)
                elif hasattr(response, 'response'):
                    answer_text = str(response.response)
                elif hasattr(response, 'text'):
                    answer_text = str(response.text)
                elif hasattr(response, 'answer'):
                    answer_text = str(response.answer)
                else:
                    # 尝试直接转换为字符串
                    answer_text = str(response)
                
                # 如果提取的内容为空，尝试从工具结果中生成总结
                if not answer_text or answer_text.strip() == "":
                    logger.warning("[Agent Query] 响应内容为空，尝试从工具结果生成总结")
                    if tool_results:
                        # 尝试从工具输出中提取文本
                        for tool_result in tool_results:
                            tool_output = tool_result.get("tool_output", {})
                            if isinstance(tool_output, dict):
                                # 查找可能的文本字段
                                for key in ['answer', 'content', 'text', 'summary', 'report']:
                                    if key in tool_output and tool_output[key]:
                                        answer_text = str(tool_output[key])
                                        break
                                if answer_text:
                                    break
            except Exception as extract_error:
                logger.warning(f"[Agent Query] 提取回答内容时出错: {str(extract_error)}，使用默认处理")
                answer_text = str(response) if response else ""
            
            # 如果没有回答内容，但有工具调用结果，生成一个总结
            if not answer_text or answer_text.strip() == "":
                if tool_results:
                    tool_names = [t.get("tool_name", "未知工具") for t in tool_results]
                    answer_text = f"✅ Agent分析完成！\n\n已执行以下工具：\n" + "\n".join([f"- {name}" for name in tool_names])
                    if len(tool_results) > 0:
                        answer_text += f"\n\n共执行了 {len(tool_results)} 个工具调用，请查看下方的结构化数据卡片获取详细分析结果。"
                else:
                    answer_text = "✅ Agent分析完成，但未返回详细内容。"
            
            result = {
                "status": "success",
                "question": question,
                "answer": answer_text,
                "structured_response": response.structured_response if hasattr(response, 'structured_response') else None,
                "tool_calls": tool_results if tool_results else []  # 确保是列表
            }

            # 如果有可视化数据，添加到响应中
            if visualization_data:
                logger.info("[Agent Query] Adding visualization data to response")
                result["visualization"] = visualization_data
            
            # 添加详细的调试日志，确保数据正确传递
            logger.info(f"[Agent Query] 返回结果摘要: status={result['status']}, answer_length={len(answer_text)}, tool_calls_count={len(tool_results)}, has_visualization={bool(visualization_data)}")
            
            # 输出每个工具调用的详细信息
            if tool_results:
                logger.info(f"[Agent Query] 工具调用详情:")
                for i, tool_result in enumerate(tool_results, 1):
                    tool_name = tool_result.get('tool_name', 'unknown')
                    tool_output = tool_result.get('tool_output', {})
                    output_type = type(tool_output).__name__
                    output_size = len(str(tool_output)) if tool_output else 0
                    logger.info(f"  [{i}] {tool_name}: 输出类型={output_type}, 输出大小={output_size}字符")
                    if isinstance(tool_output, dict):
                        logger.info(f"      输出键: {list(tool_output.keys())[:10]}")
                    elif isinstance(tool_output, str):
                        logger.info(f"      输出预览: {tool_output[:200]}")
            
            # 确保tool_calls是列表且不为空
            if not tool_results:
                logger.warning("⚠️ [Agent Query] tool_results为空，但查询已完成")
            else:
                logger.info(f"✅ [Agent Query] 准备返回 {len(tool_results)} 个工具调用结果")

            total_time = time.time() - query_start_time
            logger.info(f"✅ [Agent Query] Query completed successfully in {total_time:.2f}秒 with {len(tool_results)} tool calls")
            
            # 添加性能统计
            if tool_results:
                total_tool_time = sum(t.get("execution_time", 0) for t in tool_results if t.get("execution_time"))
                logger.info(f"[Agent Query] 工具调用总耗时: {total_tool_time:.2f}秒，平均每个工具: {total_tool_time/len(tool_results):.2f}秒")
            
            result["performance"] = {
                "total_seconds": total_time,
                "tool_calls_count": len(tool_results),
                "tool_calls_time": total_tool_time if tool_results else 0
            }
            
            return result

        except Exception as e:
            import time
            total_time = time.time() - query_start_time if 'query_start_time' in locals() else 0
            logger.error(f"❌ [Agent Query] Query failed (总耗时: {total_time:.2f}秒): {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"[Agent Query] 完整错误堆栈:\n{error_traceback}")
            
            # 提取错误位置信息
            error_location = "unknown"
            error_type = type(e).__name__
            
            # 从堆栈中提取关键信息
            if "timeout" in str(e).lower() or "Timeout" in error_type:
                error_location = "timeout"
            elif "serialize" in str(e).lower():
                error_location = "serialization"
            elif "tool" in str(e).lower():
                error_location = "tool_execution"
            elif "stream" in str(e).lower():
                error_location = "event_streaming"
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": error_type,
                "error_location": error_location,
                "question": question,
                "elapsed_seconds": total_time,
                "completed_tool_calls": len(tool_results) if 'tool_results' in locals() else 0,
                "tool_calls": tool_results if 'tool_results' in locals() else []
            }

