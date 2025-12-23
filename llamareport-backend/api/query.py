"""
查询API接口
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from core.rag_engine import RAGEngine
from agents.visualization_agent import VisualizationAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# 全局RAG引擎实例（延迟初始化）
rag_engine = None

def get_rag_engine():
    """获取RAG引擎实例（延迟初始化）"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine

class QueryRequest(BaseModel):
    question: str
    context_filter: Optional[Dict[str, Any]] = None
    enable_visualization: bool = True  # 是否启用可视化

class BatchQueryRequest(BaseModel):
    questions: List[str]
    context_filter: Optional[Dict[str, Any]] = None
    enable_visualization: bool = True  # 是否启用可视化

class SimilarContentRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/ask")
async def ask_question(request: QueryRequest):
    """
    提问接口（支持可视化）

    Args:
        request: 查询请求

    Returns:
        查询结果（可能包含可视化配置）
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")

        if len(question) > 1000:
            raise HTTPException(status_code=400, detail="问题过长，请控制在1000字符以内")

        logger.info(f"收到查询: {question[:50]}...")

        # 获取RAG引擎并执行查询
        rag_engine = get_rag_engine()
        result = rag_engine.query(question, request.context_filter)

        if result.get('error'):
            raise HTTPException(status_code=500, detail=result.get('answer', '查询失败'))

        # 基础响应
        response = {
            "question": question,
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "context_filter": request.context_filter,
            "enhanced_query": result.get('enhanced_query', question)
        }

        # 如果启用可视化，尝试生成图表
        if request.enable_visualization:
            try:
                viz_agent = VisualizationAgent()
                viz_result = await viz_agent.generate_visualization(
                    query=question,
                    answer=result['answer'],
                    sources=result.get('sources', [])
                )

                # 添加可视化数据到响应
                response['visualization'] = viz_result.model_dump()
                logger.info(f"✅ 可视化生成成功: {viz_result.has_visualization}")

            except Exception as viz_error:
                logger.warning(f"可视化生成失败: {str(viz_error)}")
                response['visualization'] = {
                    "has_visualization": False,
                    "error": str(viz_error)
                }

        logger.info(f"查询完成: {question[:50]}...")
        return JSONResponse(status_code=200, content=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.post("/batch")
async def batch_query(request: BatchQueryRequest):
    """
    批量查询接口
    
    Args:
        request: 批量查询请求
        
    Returns:
        批量查询结果
    """
    try:
        questions = request.questions
        if not questions:
            raise HTTPException(status_code=400, detail="问题列表不能为空")
        
        if len(questions) > 10:
            raise HTTPException(status_code=400, detail="一次最多查询10个问题")
        
        # 验证每个问题
        for i, question in enumerate(questions):
            if not question or not question.strip():
                raise HTTPException(status_code=400, detail=f"第{i+1}个问题不能为空")
            if len(question) > 1000:
                raise HTTPException(status_code=400, detail=f"第{i+1}个问题过长")
        
        logger.info(f"收到批量查询: {len(questions)} 个问题")
        
        results = []
        for i, question in enumerate(questions):
            try:
                question = question.strip()
                result = rag_engine.query(question, request.context_filter)
                
                if result.get('error'):
                    results.append({
                        "question_index": i,
                        "question": question,
                        "status": "error",
                        "error": result.get('answer', '查询失败')
                    })
                else:
                    results.append({
                        "question_index": i,
                        "question": question,
                        "status": "success",
                        "answer": result['answer'],
                        "sources": result.get('sources', []),
                        "enhanced_query": result.get('enhanced_query', question)
                    })
                
            except Exception as e:
                results.append({
                    "question_index": i,
                    "question": question,
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"批量查询中第{i+1}个问题失败: {str(e)}")
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = len(results) - success_count
        
        response = {
            "total_questions": len(questions),
            "success_count": success_count,
            "error_count": error_count,
            "context_filter": request.context_filter,
            "results": results
        }
        
        logger.info(f"批量查询完成: {success_count}/{len(questions)} 成功")
        return JSONResponse(status_code=200, content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")

@router.post("/similar")
async def get_similar_content(request: SimilarContentRequest):
    """
    获取相似内容
    
    Args:
        request: 相似内容请求
        
    Returns:
        相似内容列表
    """
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        if request.top_k < 1 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k必须在1-20之间")
        
        logger.info(f"获取相似内容: {query[:50]}...")
        
        # 获取相似内容
        similar_content = rag_engine.get_similar_content(query, request.top_k)
        
        response = {
            "query": query,
            "top_k": request.top_k,
            "total_results": len(similar_content),
            "similar_content": similar_content
        }
        
        logger.info(f"相似内容查询完成: 找到 {len(similar_content)} 个结果")
        return JSONResponse(status_code=200, content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取相似内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取相似内容失败: {str(e)}")

@router.get("/suggestions")
async def get_query_suggestions():
    """
    获取查询建议
    
    Returns:
        查询建议列表
    """
    try:
        suggestions = [
            {
                "category": "财务数据",
                "questions": [
                    "公司的营业收入是多少？",
                    "净利润增长率如何？",
                    "资产负债率是多少？",
                    "现金流状况如何？"
                ]
            },
            {
                "category": "业务分析",
                "questions": [
                    "主要业务板块有哪些？",
                    "市场份额如何？",
                    "竞争优势是什么？",
                    "风险因素有哪些？"
                ]
            },
            {
                "category": "发展趋势",
                "questions": [
                    "未来发展战略是什么？",
                    "投资计划有哪些？",
                    "预期增长率如何？",
                    "行业前景如何？"
                ]
            }
        ]
        
        return JSONResponse(status_code=200, content={
            "message": "查询建议",
            "suggestions": suggestions
        })
        
    except Exception as e:
        logger.error(f"获取查询建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取查询建议失败: {str(e)}")

@router.get("/history")
async def get_query_history():
    """
    获取查询历史（简化版本，实际应该从数据库获取）
    
    Returns:
        查询历史
    """
    try:
        # 这里是简化版本，实际应该从数据库或缓存中获取
        history = {
            "message": "查询历史功能暂未实现",
            "note": "在生产环境中，这里应该返回用户的查询历史记录",
            "recent_queries": []
        }
        
        return JSONResponse(status_code=200, content=history)
        
    except Exception as e:
        logger.error(f"获取查询历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取查询历史失败: {str(e)}")

@router.get("/stats")
async def get_query_stats():
    """
    获取查询统计信息
    
    Returns:
        查询统计
    """
    try:
        # 获取索引统计
        index_stats = rag_engine.get_index_stats()
        
        stats = {
            "index_status": index_stats,
            "query_capabilities": {
                "max_question_length": 1000,
                "max_batch_size": 10,
                "max_similar_results": 20,
                "supported_filters": ["company", "year", "document_type"]
            },
            "performance_info": {
                "average_response_time": "1-3秒",
                "supported_languages": ["中文", "英文"],
                "context_window": "4000 tokens"
            }
        }
        
        return JSONResponse(status_code=200, content=stats)
        
    except Exception as e:
        logger.error(f"获取查询统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取查询统计失败: {str(e)}")

@router.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]):
    """
    提交查询反馈（简化版本）
    
    Args:
        feedback_data: 反馈数据
        
    Returns:
        反馈提交结果
    """
    try:
        # 这里是简化版本，实际应该保存到数据库
        logger.info(f"收到查询反馈: {feedback_data}")
        
        return JSONResponse(status_code=200, content={
            "message": "反馈提交成功",
            "note": "感谢您的反馈，我们会持续改进服务质量"
        })
        
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")

@router.post("/quick-overview")
async def get_quick_overview():
    """
    快速生成企业概况接口
    
    从文档中快速提取关键信息，生成简洁但全面的企业概况
    要求速度快，缺失字段不报错，用"—"或灰色显示
    
    Returns:
        企业概况数据，包含：
        - 核心指标（规模与增长、利润、现金流）
        - 业务结构（Top3业务+占比）
        - 盈利&安全指标（GM/NM/ROE/负债率）
        - Highlights和Risks（chips列表）
        - 缺失字段列表
    """
    try:
        from llama_index.core.llms import ChatMessage
        from llama_index.core import Settings
        from pydantic import BaseModel, Field
        from typing import Optional, List
        
        # 定义快速概况的数据模型
        class QuickOverviewModel(BaseModel):
            """快速概况数据模型"""
            # 核心指标
            revenue: Optional[str] = Field(default=None, description="营业收入，如'6.73亿元'")
            revenue_yoy: Optional[str] = Field(default=None, description="营收同比增长率，如'14.53%'")
            net_profit: Optional[str] = Field(default=None, description="净利润，如'1.2亿元'")
            net_profit_yoy: Optional[str] = Field(default=None, description="净利润同比增长率，如'10.5%'")
            operating_cfo: Optional[str] = Field(default=None, description="经营活动现金流量净额，如'2.5亿元'")
            operating_cfo_yoy: Optional[str] = Field(default=None, description="经营现金流同比增长率，如'8.3%'")
            
            # 业务结构
            top3_business: Optional[List[Dict[str, str]]] = Field(default=None, description="Top3业务，格式：[{'name': '业务名', 'revenue': '收入', 'ratio': '占比'}]")
            
            # 盈利&安全指标
            gross_margin: Optional[str] = Field(default=None, description="毛利率，如'45.2%'")
            net_margin: Optional[str] = Field(default=None, description="净利率，如'18.5%'")
            roe: Optional[str] = Field(default=None, description="ROE，如'12.3%'")
            debt_ratio: Optional[str] = Field(default=None, description="负债率，如'35.6%'")
            
            # Highlights和Risks
            highlights: Optional[List[str]] = Field(default=None, description="业务亮点列表")
            risks: Optional[List[str]] = Field(default=None, description="风险因素列表")
            
            # 缺失字段提示
            missing_fields: Optional[List[str]] = Field(default=None, description="缺失的字段列表，用于前端显示提示")
        
        logger.info("开始生成快速企业概况...")
        
        # 获取RAG引擎
        rag_engine = get_rag_engine()
        
        if not rag_engine.query_engine:
            # 尝试加载现有索引
            if not rag_engine.load_existing_index():
                raise HTTPException(
                    status_code=400,
                    detail="索引未构建，请先处理文档"
                )
        
        # 构建快速查询提示词
        quick_query = """
请从文档中快速提取以下关键信息，如果某个信息缺失，请设置为null，不要报错：

1. 核心指标：
   - 营业收入及同比增长率
   - 净利润及同比增长率
   - 经营活动现金流量净额及同比增长率

2. 业务结构：
   - Top3业务板块及其收入和占比

3. 盈利&安全指标：
   - 毛利率(GM)
   - 净利率(NM)
   - ROE
   - 负债率

4. 业务亮点和风险：
   - 3-5个主要业务亮点
   - 3-5个主要风险因素

请以JSON格式输出，缺失的字段设置为null。要求快速响应，优先提取明确的数据。
"""
        
        # 使用RAG查询获取上下文
        context_result = rag_engine.query(quick_query)
        context_text = context_result.get('answer', '')
        
        # 使用结构化LLM生成概况
        llm = Settings.llm
        sllm = llm.as_structured_llm(QuickOverviewModel)
        
        prompt = f"""
基于以下文档内容，快速提取企业概况信息：

{context_text}

请提取关键信息并填充到QuickOverviewModel中。如果某个字段在文档中找不到，请设置为null，不要报错。
优先提取数值型数据（营收、利润、现金流等），如果找不到具体数值，可以设置为null。
"""
        
        response = await sllm.achat([
            ChatMessage(
                role="system",
                content="你是一个专业的财务分析师。请快速从文档中提取关键信息，缺失的字段设置为null，不要报错。优先提取数值型数据。"
            ),
            ChatMessage(role="user", content=prompt)
        ])
        
        overview_data = response.raw.model_dump()
        
        # 计算缺失字段
        missing_fields = []
        if not overview_data.get('revenue'): missing_fields.append('营收')
        if not overview_data.get('net_profit'): missing_fields.append('净利润')
        if not overview_data.get('operating_cfo'): missing_fields.append('经营现金流')
        if not overview_data.get('top3_business'): missing_fields.append('业务结构')
        if not overview_data.get('gross_margin'): missing_fields.append('毛利率')
        if not overview_data.get('net_margin'): missing_fields.append('净利率')
        if not overview_data.get('roe'): missing_fields.append('ROE')
        if not overview_data.get('debt_ratio'): missing_fields.append('负债率')
        if not overview_data.get('highlights'): missing_fields.append('业务亮点')
        if not overview_data.get('risks'): missing_fields.append('风险因素')
        
        overview_data['missing_fields'] = missing_fields
        
        logger.info(f"✅ 快速概况生成成功，缺失字段: {len(missing_fields)}个")
        
        return JSONResponse(status_code=200, content={
            "status": "success",
            "overview": overview_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成快速概况失败: {str(e)}")
        # 即使失败也返回一个空结构，不报错
        return JSONResponse(status_code=200, content={
            "status": "success",
            "overview": {
                "revenue": None,
                "revenue_yoy": None,
                "net_profit": None,
                "net_profit_yoy": None,
                "operating_cfo": None,
                "operating_cfo_yoy": None,
                "top3_business": None,
                "gross_margin": None,
                "net_margin": None,
                "roe": None,
                "debt_ratio": None,
                "highlights": None,
                "risks": None,
                "missing_fields": ["所有字段"]
            }
        })
