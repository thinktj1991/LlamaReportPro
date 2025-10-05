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
            
            # 4. 组装所有工具
            tools = [
                query_tool,
                financial_review_tool,
                business_guidance_tool,
                business_highlights_tool,
                profit_forecast_tool,
                financial_data_tool,
                business_data_tool
            ]
            
            # 5. 创建 FunctionAgent
            system_prompt = """
你是一个专业的年报分析 Agent,负责生成结构化的年报分析报告。

你的任务是:
1. 理解用户的年报分析需求
2. 使用提供的工具检索和分析年报数据
3. 按照标准模板生成完整的年报分析报告

报告结构包括五个部分:
一、财务点评 (使用 generate_financial_review 工具)
二、业绩指引 (使用 generate_business_guidance 工具)
三、业务亮点 (使用 generate_business_highlights 工具)
四、盈利预测和估值 (使用 generate_profit_forecast_and_valuation 工具)
五、总结 (基于前四部分综合生成)

工作流程:
1. 首先使用 annual_report_query 工具了解年报的基本信息(公司名称、年份等)
2. 依次调用各章节生成工具
3. 最后综合所有章节生成总结

注意事项:
- 确保所有数据来源于年报原文
- 保持分析的客观性和专业性
- 使用结构化的格式输出
- 如果某些数据缺失,明确说明
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
            查询结果
        """
        try:
            response = await self.agent.run(question)
            
            return {
                "status": "success",
                "question": question,
                "answer": str(response),
                "structured_response": response.structured_response if hasattr(response, 'structured_response') else None
            }
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "question": question
            }

