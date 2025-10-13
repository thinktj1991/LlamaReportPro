"""
年报分析 Agent 工具函数
每个工具负责生成报告的一个章节
"""

import logging
from typing import Dict, Any, List, Optional, Annotated
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from models.report_models import (
    FinancialReview,
    BusinessGuidance,
    BusinessHighlights,
    ProfitForecastAndValuation,
    PerformanceSummary,
    FinancialMetrics,
    FinancialIndicator,
    FinancialCharts,
    PerformanceComparison,
    MetricAttribution,
    BusinessHighlight,
    ConsensusForecas,
    ValuationAnalysis
)
from agents.visualization_agent import generate_visualization_for_query

logger = logging.getLogger(__name__)


# ==================== 数据检索工具 ====================

def create_query_engine_tool(query_engine, name: str, description: str) -> QueryEngineTool:
    """
    创建查询引擎工具
    
    Args:
        query_engine: LlamaIndex 查询引擎
        name: 工具名称
        description: 工具描述
    
    Returns:
        QueryEngineTool 实例
    """
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name=name,
        description=description
    )


# ==================== 财务数据检索工具 ====================

def retrieve_financial_data(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份,如'2023'"],
    metric_type: Annotated[str, "指标类型: revenue(收入), profit(利润), cash_flow(现金流), balance_sheet(资产负债)"],
    query_engine: Any
) -> str:
    """
    检索财务数据
    
    从年报中检索特定的财务指标数据
    
    Args:
        company_name: 公司名称
        year: 年份
        metric_type: 指标类型
        query_engine: 查询引擎
    
    Returns:
        财务数据的文本描述
    """
    try:
        # 构建查询
        query_map = {
            "revenue": f"{company_name} {year}年 营业收入 收入增长率 毛利率",
            "profit": f"{company_name} {year}年 净利润 归母净利润 扣非净利润 利润增长率",
            "cash_flow": f"{company_name} {year}年 经营活动现金流 投资活动现金流 筹资活动现金流",
            "balance_sheet": f"{company_name} {year}年 总资产 总负债 资产负债率 净资产"
        }
        
        query = query_map.get(metric_type, f"{company_name} {year}年 {metric_type}")
        
        # 执行查询
        response = query_engine.query(query)
        
        logger.info(f"✅ 检索财务数据成功: {metric_type}")
        return str(response)
        
    except Exception as e:
        logger.error(f"❌ 检索财务数据失败: {str(e)}")
        return f"检索失败: {str(e)}"


def retrieve_business_data(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份"],
    business_type: Annotated[str, "业务类型,如'主营业务'、'分部业务'、'产品业务'"],
    query_engine: Any
) -> str:
    """
    检索业务数据
    
    从年报中检索业务相关信息
    
    Args:
        company_name: 公司名称
        year: 年份
        business_type: 业务类型
        query_engine: 查询引擎
    
    Returns:
        业务数据的文本描述
    """
    try:
        query = f"{company_name} {year}年 {business_type} 业务收入 业务增长 市场份额"
        response = query_engine.query(query)
        
        logger.info(f"✅ 检索业务数据成功: {business_type}")
        return str(response)
        
    except Exception as e:
        logger.error(f"❌ 检索业务数据失败: {str(e)}")
        return f"检索失败: {str(e)}"


# ==================== 章节生成工具 ====================

async def generate_financial_review(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份,如'2023'"],
    query_engine: Any
) -> Dict[str, Any]:
    """
    生成财务点评章节
    
    包括:
    1. 财务图表描述
    2. 业绩速览
    3. 业绩和预期的比较
    4. 财务指标变动归因
    
    Args:
        company_name: 公司名称
        year: 年份
        query_engine: 查询引擎
    
    Returns:
        财务点评的结构化数据
    """
    try:
        logger.info(f"开始生成财务点评: {company_name} {year}年")
        
        # 1. 检索财务数据
        revenue_data = retrieve_financial_data(company_name, year, "revenue", query_engine)
        profit_data = retrieve_financial_data(company_name, year, "profit", query_engine)
        cash_flow_data = retrieve_financial_data(company_name, year, "cash_flow", query_engine)
        
        # 2. 使用 LLM 生成结构化的财务点评
        llm = Settings.llm

        prompt = f"""
基于以下财务数据,生成{company_name} {year}年的财务点评。

收入数据:
{revenue_data}

利润数据:
{profit_data}

现金流数据:
{cash_flow_data}

请生成结构化的财务点评,包括:
1. 财务图表描述(列出主要的财务图表)
2. 业绩速览(详细的财务指标)
3. 业绩和预期的比较
4. 财务指标变动归因(分析各指标变动的原因)

请以JSON格式输出,符合 FinancialReview 模型的结构。
"""

        # 使用结构化输出
        sllm = llm.as_structured_llm(FinancialReview)
        response = await sllm.achat([
            ChatMessage(role="system", content="你是一个专业的财务分析师,擅长分析年报数据。"),
            ChatMessage(role="user", content=prompt)
        ])

        logger.info(f"✅ 财务点评生成成功")
        # 使用 model_dump() 而不是 dict() (Pydantic v2)
        return response.raw.model_dump()
        
    except Exception as e:
        logger.error(f"❌ 生成财务点评失败: {str(e)}")
        raise


async def generate_business_guidance(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份"],
    query_engine: Any
) -> Dict[str, Any]:
    """
    生成业绩指引章节
    
    包括:
    1. 业绩预告期间
    2. 预计的经营业绩
    3. 各业务的具体指引
    4. 风险提示
    
    Args:
        company_name: 公司名称
        year: 年份
        query_engine: 查询引擎
    
    Returns:
        业绩指引的结构化数据
    """
    try:
        logger.info(f"开始生成业绩指引: {company_name} {year}年")
        
        # 检索业绩指引相关数据
        query = f"{company_name} {year}年 业绩预告 业绩指引 下一年度预期 经营计划"
        guidance_data = query_engine.query(query)
        
        # 使用 LLM 生成结构化的业绩指引
        llm = Settings.llm

        prompt = f"""
基于以下数据,生成{company_name} {year}年的业绩指引。

业绩指引数据:
{str(guidance_data)}

请生成结构化的业绩指引,包括:
1. 业绩预告期间
2. 预计的经营业绩描述
3. 归母净利润范围和增长率范围
4. 各业务的具体指引
5. 风险提示

请以JSON格式输出,符合 BusinessGuidance 模型的结构。
"""

        sllm = llm.as_structured_llm(BusinessGuidance)
        response = await sllm.achat([
            ChatMessage(role="system", content="你是一个专业的财务分析师,擅长分析业绩指引。"),
            ChatMessage(role="user", content=prompt)
        ])

        logger.info(f"✅ 业绩指引生成成功")
        # 使用 model_dump() 而不是 dict() (Pydantic v2)
        return response.raw.model_dump()
        
    except Exception as e:
        logger.error(f"❌ 生成业绩指引失败: {str(e)}")
        raise


async def generate_business_highlights(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份"],
    query_engine: Any
) -> Dict[str, Any]:
    """
    生成业务亮点章节
    
    包括各业务板块的亮点和成就
    
    Args:
        company_name: 公司名称
        year: 年份
        query_engine: 查询引擎
    
    Returns:
        业务亮点的结构化数据
    """
    try:
        logger.info(f"开始生成业务亮点: {company_name} {year}年")
        
        # 检索业务亮点数据
        query = f"{company_name} {year}年 业务亮点 主要成就 重大项目 技术创新 市场拓展"
        highlights_data = query_engine.query(query)
        
        # 使用 LLM 生成结构化的业务亮点
        llm = Settings.llm

        prompt = f"""
基于以下数据,生成{company_name} {year}年的业务亮点。

业务亮点数据:
{str(highlights_data)}

请生成结构化的业务亮点,包括:
1. 各业务类型的亮点描述
2. 主要成就列表
3. 业务亮点总结

请以JSON格式输出,符合 BusinessHighlights 模型的结构。
"""

        sllm = llm.as_structured_llm(BusinessHighlights)
        response = await sllm.achat([
            ChatMessage(role="system", content="你是一个专业的业务分析师,擅长总结业务亮点。"),
            ChatMessage(role="user", content=prompt)
        ])

        logger.info(f"✅ 业务亮点生成成功")
        # 使用 model_dump() 而不是 dict() (Pydantic v2)
        return response.raw.model_dump()
        
    except Exception as e:
        logger.error(f"❌ 生成业务亮点失败: {str(e)}")
        raise


async def generate_profit_forecast_and_valuation(
    company_name: Annotated[str, "公司名称"],
    year: Annotated[str, "年份"],
    query_engine: Any
) -> Dict[str, Any]:
    """
    生成盈利预测和估值章节
    
    包括:
    1. 一致预测
    2. 机构预测
    3. 估值分析
    
    Args:
        company_name: 公司名称
        year: 年份
        query_engine: 查询引擎
    
    Returns:
        盈利预测和估值的结构化数据
    """
    try:
        logger.info(f"开始生成盈利预测和估值: {company_name} {year}年")
        
        # 检索预测和估值数据
        query = f"{company_name} 盈利预测 机构评级 目标价 估值分析 PE PB ROE"
        forecast_data = query_engine.query(query)
        
        # 使用 LLM 生成结构化的盈利预测和估值
        llm = Settings.llm

        prompt = f"""
基于以下数据,生成{company_name}的盈利预测和估值分析。

预测和估值数据:
{str(forecast_data)}

请生成结构化的盈利预测和估值,包括:
1. 一致预测(市场整体评级、目标价、财务指标预测)
2. 一致预期变化
3. 具体机构预测
4. 估值分析(估值方法、当前估值、估值对比)

请以JSON格式输出,符合 ProfitForecastAndValuation 模型的结构。
"""

        sllm = llm.as_structured_llm(ProfitForecastAndValuation)
        response = await sllm.achat([
            ChatMessage(role="system", content="你是一个专业的投资分析师,擅长盈利预测和估值分析。"),
            ChatMessage(role="user", content=prompt)
        ])

        logger.info(f"✅ 盈利预测和估值生成成功")
        # 使用 model_dump() 而不是 dict() (Pydantic v2)
        return response.raw.model_dump()
        
    except Exception as e:
        logger.error(f"❌ 生成盈利预测和估值失败: {str(e)}")
        raise

