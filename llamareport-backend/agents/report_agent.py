"""
年报分析 Agent 主配置
使用 FunctionAgent 协调各个工具生成完整报告
"""

import logging
from typing import Dict, Any, Optional
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
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
from agents.realtime_tools import create_realtime_data_tools

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
            # 如果是字符串、数字、布尔值、None，直接返回
            if isinstance(tool_output, (str, int, float, bool, type(None))):
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
                except Exception:
                    pass

            # 如果有model_dump()方法（Pydantic v2）
            if hasattr(tool_output, 'model_dump'):
                try:
                    return tool_output.model_dump()
                except Exception:
                    pass

            # 如果有__dict__属性
            if hasattr(tool_output, '__dict__'):
                try:
                    return {k: self._serialize_tool_output(v) for k, v in tool_output.__dict__.items() if not k.startswith('_')}
                except Exception:
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
            
            # 4. 创建实时数据工具
            realtime_tools = create_realtime_data_tools()
            logger.info(f"✅ 加载了 {len(realtime_tools)} 个实时数据工具")

            # 5. 组装所有工具（历史数据 + 实时数据）
            tools = [
                # 历史数据工具（年报分析）
                query_tool,
                financial_review_tool,
                business_guidance_tool,
                business_highlights_tool,
                profit_forecast_tool,
                financial_data_tool,
                business_data_tool,
                visualization_tool,  # 可视化工具
                dupont_analysis_tool,  # 杜邦分析工具
                
                # 实时数据工具（新增）⭐
            ] + realtime_tools
            
            # 6. 创建 FunctionAgent（更新系统提示词）
            system_prompt = """
你是一个专业的年报分析 Agent,负责生成结构化的年报分析报告。

【核心能力】
1. 历史数据分析: 从年报中提取和分析历史财务数据
2. 实时数据查询: 获取最新的股价、新闻、公告等实时信息
3. 综合分析: 结合历史和实时数据提供全面的投资分析
4. 可视化生成: 为数据创建直观的图表
5. 智能预警: 检测和提示异常情况

【工具使用策略】⭐ 重要
- 历史表现分析 → 使用年报分析工具（annual_report_query, generate_*）
- 当前状况查询 → 使用实时数据工具（get_realtime_stock_price, get_market_overview）
- 最新动态追踪 → 使用新闻/公告工具（get_latest_financial_news, get_company_announcements）
- 风险监控 → 使用预警工具（check_stock_alerts）
- 综合分析 → 同时使用历史和实时工具

【报告结构】（生成完整报告时使用）
一、财务点评 (使用 generate_financial_review 工具)
二、业绩指引 (使用 generate_business_guidance 工具)
三、业务亮点 (使用 generate_business_highlights 工具)
四、盈利预测和估值 (使用 generate_profit_forecast_and_valuation 工具)
五、总结 (基于前四部分综合生成)

【工作流程】
1. 判断用户需求类型（历史分析 vs 实时查询 vs 综合分析）
2. 选择合适的工具组合
3. 执行查询并收集数据
4. 对于数值数据，使用 generate_visualization 生成图表
5. 整合信息，提供清晰的分析结论

【数据时效性提示】⭐ 关键
- 年报数据: 历史数据，可能滞后3-12个月，但更全面深入
- 实时数据: 当前数据，实时性强，但缺少历史深度
- 最佳实践: 结合两者使用 —— 用年报看趋势，用实时看现状

【回答示例】
用户问: "贵州茅台现在值得投资吗？"
正确做法:
1. 使用 get_realtime_stock_price 获取当前股价和估值
2. 使用 annual_report_query 查询年报中的业绩和财务状况
3. 使用 get_latest_financial_news 了解最新动态
4. 使用 check_stock_alerts 检查异常情况
5. 综合分析给出投资建议

注意事项:
- 明确区分历史数据和实时数据
- 数据来源要清晰（来自年报 vs 来自实时行情）
- 保持客观和专业
- 实时数据工具可能会失败（API限制），需要优雅处理
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
        try:
            logger.info(f"[Agent Query] Starting query: {question[:100]}...")

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

            # 流式处理事件以捕获工具调用结果
            try:
                async for event in handler.stream_events():
                    logger.info(f"[Agent Query] Got event: {type(event).__name__}")

                    if isinstance(event, ToolCall):
                        logger.info(f"[Agent Query] Tool call: {event.tool_name} with {event.tool_kwargs}")

                    elif isinstance(event, ToolCallResult):
                        logger.info(f"[Agent Query] Tool call result: {event.tool_name}")

                        # 将ToolOutput转换为可序列化的格式
                        tool_output_serializable = self._serialize_tool_output(event.tool_output)

                        tool_results.append({
                            "tool_name": event.tool_name,
                            "tool_kwargs": event.tool_kwargs,
                            "tool_output": tool_output_serializable
                        })

                        # 如果是可视化工具，保存其输出
                        if event.tool_name == "generate_visualization":
                            logger.info("[Agent Query] Found visualization tool call")
                            visualization_data = tool_output_serializable

                    elif isinstance(event, AgentStream):
                        # 流式输出（可选）
                        pass

            except Exception as stream_error:
                logger.error(f"[Agent Query] Error during event streaming: {str(stream_error)}")
                import traceback
                logger.error(traceback.format_exc())

            # 获取最终响应
            logger.info("[Agent Query] Waiting for final response")
            response = await handler
            logger.info(f"[Agent Query] Got final response type: {type(response)}")

            result = {
                "status": "success",
                "question": question,
                "answer": str(response),
                "structured_response": response.structured_response if hasattr(response, 'structured_response') else None,
                "tool_calls": tool_results
            }

            # 如果有可视化数据，添加到响应中
            if visualization_data:
                logger.info("[Agent Query] Adding visualization data to response")
                result["visualization"] = visualization_data

            logger.info(f"[Agent Query] Query completed successfully with {len(tool_results)} tool calls")
            return result

        except Exception as e:
            logger.error(f"[Agent Query] Query failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "question": question
            }

