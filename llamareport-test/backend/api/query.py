"""
查询API接口
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from decimal import Decimal
from datetime import datetime

from core.rag_engine import RAGEngine
from agents.visualization_agent import VisualizationAgent
from models.report_models import FinancialSnapshot, KeyFinancialMetric
from agents.report_tools import retrieve_financial_data
from agents.dupont_tools import parse_financial_data_response, extract_financial_data_for_dupont, generate_dupont_analysis

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
            # 统一错误响应格式
            return JSONResponse(
                status_code=500,
                content={
                    "error": result.get('answer', '查询失败'),
                    "question": question,
                    "answer": result.get('answer', '查询失败'),
                    "sources": [],
                    "visualization": None
                }
            )

        # 基础响应 - 确保所有字段都存在
        response = {
            "question": question,
            "answer": result.get('answer', ''),
            "sources": result.get('sources', []),
            "context_filter": request.context_filter,
            "enhanced_query": result.get('enhanced_query', question),
            "visualization": None  # 初始化为None，后续可能被填充
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
        
        # 确保响应格式统一
        response_data = {
            "question": response.get("question", question),
            "answer": response.get("answer", ""),
            "sources": response.get("sources", []),
            "context_filter": response.get("context_filter"),
            "enhanced_query": response.get("enhanced_query", question),
            "visualization": response.get("visualization")
        }
        
        return JSONResponse(status_code=200, content=response_data)

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

class DupontAnalysisRequest(BaseModel):
    """杜邦分析请求"""
    company_name: Optional[str] = None  # 可选，如果不提供则从文档中提取
    year: Optional[str] = None  # 可选，如果不提供则从文档中提取
    filename: Optional[str] = None  # 选中的文件名，用于限制查询范围

@router.post("/dupont-analysis")
async def generate_dupont_analysis_api(request: DupontAnalysisRequest):
    """
    生成杜邦分析报告
    
    自动从文档中提取财务数据，生成完整的杜邦分析报告
    如果未提供公司名称和年份，将尝试从文档中自动提取
    
    Returns:
        杜邦分析结果，包含：
        - level1: ROE顶层分解
        - level2: ROA和权益乘数分解
        - level3: 底层财务数据
        - tree_structure: 树状结构
        - insights: AI分析洞察
    """
    try:
        logger.info("收到杜邦分析请求")
        
        # 获取RAG引擎
        rag_engine = get_rag_engine()
        
        if not rag_engine.query_engine:
            if not rag_engine.load_existing_index():
                raise HTTPException(
                    status_code=400,
                    detail="索引未构建，请先处理文档"
                )
        
        query_engine = rag_engine.query_engine
        
        # 提取公司名称和年份
        company_name = request.company_name
        year = request.year
        filename = request.filename
        
        # 构建上下文过滤器，限制查询范围到选中的文件
        context_filter = None
        if filename:
            context_filter = {"filename": filename}
            logger.info(f"限制查询范围到文件: {filename}")
        
        # 如果未提供，尝试从文档中提取
        if not company_name or not year:
            logger.info(f"尝试从文档中提取公司名称和年份... (文件: {filename or '全部'})")
            
            import re
            
            # 第一步：优先从文件名中提取公司名称和年份
            if filename:
                # 从文件名提取公司名称（更智能的匹配）
                # 匹配模式：公司名 + 报表类型 + 年份（可选）
                # 例如："平安银行利润表.xlsx" -> "平安银行"
                # 例如："平安银行2024年年报.pdf" -> "平安银行"
                if not company_name:
                    # 移除文件扩展名
                    name_without_ext = re.sub(r'\.[^.]+$', '', filename)
                    # 移除常见的报表类型关键词
                    name_clean = re.sub(r'(利润表|资产负债表|现金流量表|年报|报告|财务报表|财务报告)', '', name_without_ext, flags=re.IGNORECASE)
                    # 移除年份
                    name_clean = re.sub(r'\d{4}年?', '', name_clean)
                    # 移除多余的空格和特殊字符
                    name_clean = re.sub(r'[_\-\s]+', '', name_clean).strip()
                    if name_clean and len(name_clean) >= 2:
                        company_name = name_clean
                        logger.info(f"从文件名提取公司名称: {company_name}")
                
                # 从文件名提取年份
                if not year:
                    year_match = re.search(r'(\d{4})', filename)
                    if year_match:
                        year = year_match.group(1)
                        logger.info(f"从文件名提取年份: {year}")
            
            # 第二步：如果还没有，从文档内容中提取
            if not company_name or not year:
                try:
                    # 从索引中检索该文件的文档
                    retriever = rag_engine.index.as_retriever(similarity_top_k=10)
                    nodes = retriever.retrieve("公司名称 年份 报告")
                    
                    # 过滤出匹配的文件（检查filename和source_file）
                    matching_nodes = [
                        node for node in nodes 
                        if (not filename) or (node.metadata.get('filename') == filename or 
                           node.metadata.get('source_file') == filename)
                    ]
                    
                    if matching_nodes:
                        # 合并所有匹配节点的文本
                        all_text = "\n".join([node.text for node in matching_nodes[:5]])
                        
                        if not company_name:
                            # 从文本中提取公司名称（多种模式）
                            patterns = [
                                r'([^，,。\n]{2,30}(?:股份|有限|公司|集团|银行|证券|保险))',
                                r'公司名称[：:]\s*([^，,。\n]{2,30})',
                                r'([A-Za-z0-9\u4e00-\u9fa5]{2,20}(?:股份|有限|公司|集团))',
                            ]
                            for pattern in patterns:
                                company_match = re.search(pattern, all_text)
                                if company_match:
                                    candidate = company_match.group(1).strip()
                                    # 过滤掉明显不是公司名的内容
                                    if len(candidate) >= 2 and len(candidate) <= 30:
                                        company_name = candidate
                                        logger.info(f"从文档内容提取公司名称: {company_name}")
                                        break
                        
                        if not year:
                            # 从文本中提取年份
                            year_patterns = [
                                r'(\d{4})年',
                                r'报告年度[：:]\s*(\d{4})',
                                r'(\d{4})年度',
                            ]
                            for pattern in year_patterns:
                                year_match = re.search(pattern, all_text)
                                if year_match:
                                    candidate_year = year_match.group(1)
                                    # 验证年份合理性
                                    if 2000 <= int(candidate_year) <= 2030:
                                        year = candidate_year
                                        logger.info(f"从文档内容提取年份: {year}")
                                        break
                        
                        logger.info(f"从文档内容提取: {company_name or '未找到'} - {year or '未找到'}")
                except Exception as e:
                    logger.warning(f"从文档内容提取失败: {str(e)}")
            
            # 如果仍然没有，使用query_engine查询
            if not company_name or not year:
                extract_query = """
                请从文档中提取以下信息：
                1. 公司名称（完整的公司全称）
                2. 报告年份（如2023、2022等）
                
                请以JSON格式返回，格式：{"company_name": "公司名称", "year": "年份"}
                """
                
                try:
                    # 如果有context_filter，使用retriever限制范围
                    if context_filter and filename:
                        retriever = rag_engine.index.as_retriever(similarity_top_k=10)
                        nodes = retriever.retrieve(extract_query)
                        # 过滤出匹配的文件（检查filename和source_file）
                        matching_nodes = [
                            node for node in nodes 
                            if node.metadata.get('filename') == filename or 
                               node.metadata.get('source_file') == filename
                        ]
                        if matching_nodes:
                            response_text = "\n".join([node.text for node in matching_nodes[:3]])
                        else:
                            response_text = ""
                    else:
                        response = query_engine.query(extract_query)
                        response_text = str(response)
                    
                    # 尝试解析JSON
                    import json
                    import re
                    json_match = re.search(r'\{[^{}]*"company_name"[^{}]*"year"[^{}]*\}', response_text)
                    if json_match:
                        extracted_data = json.loads(json_match.group())
                        if not company_name:
                            company_name = extracted_data.get('company_name', '')
                        if not year:
                            year = extracted_data.get('year', '')
                    
                    # 如果JSON解析失败，尝试正则提取
                    if not company_name:
                        company_match = re.search(r'公司名称[：:]\s*([^\n，,。]+)', response_text)
                        if company_match:
                            company_name = company_match.group(1).strip()
                    
                    if not year:
                        year_match = re.search(r'(\d{4})年', response_text)
                        if year_match:
                            year = year_match.group(1)
                        else:
                            # 尝试从文档元数据中获取
                            year_match = re.search(r'(\d{4})', response_text)
                            if year_match:
                                year = year_match.group(1)
                
                except Exception as e:
                    logger.warning(f"从文档提取公司信息失败: {str(e)}")
        
        # 如果仍然没有，使用默认值
        if not company_name:
            company_name = "未知公司"
            logger.warning("未找到公司名称，使用默认值")
        
        if not year:
            # 使用当前年份的前一年作为默认值
            from datetime import datetime
            year = str(datetime.now().year - 1)
            logger.warning(f"未找到年份，使用默认值: {year}")
        
        logger.info(f"开始生成杜邦分析: {company_name} - {year}")
        
        # 如果有context_filter，需要创建一个带过滤器的query_engine
        # 由于generate_dupont_analysis需要query_engine，我们在这里传递context_filter信息
        # 注意：需要在dupont_tools中支持context_filter，或者在这里先提取数据
        
        # 如果指定了文件，先尝试从该文件提取财务数据
        financial_data = None
        if filename:
            try:
                logger.info(f"从文件 {filename} 中提取财务数据...")
                # 使用retriever从指定文件提取数据
                retriever = rag_engine.index.as_retriever(similarity_top_k=20)
                nodes = retriever.retrieve(f"{company_name} {year}年 净利润 营业收入 总资产 股东权益")
                
                # 过滤出匹配的文件（检查filename和source_file）
                matching_nodes = [
                    node for node in nodes 
                    if node.metadata.get('filename') == filename or 
                       node.metadata.get('source_file') == filename
                ]
                
                if matching_nodes:
                    # 构建查询文本
                    context_text = "\n".join([node.text for node in matching_nodes[:5]])
                    # 使用query_engine查询，但限制在匹配的节点中
                    extract_query = f"""
                    请从以下内容中提取财务数据：
                    {context_text}
                    
                    请提取以下指标的数值（单位：元）：
                    1. 净利润（归属于母公司所有者的净利润）
                    2. 营业收入（营业总收入）
                    3. 总资产
                    4. 股东权益（归属于母公司所有者权益）
                    5. 流动资产
                    6. 非流动资产
                    
                    请以JSON格式返回，键名使用中文。
                    """
                    response = query_engine.query(extract_query)
                    from agents.dupont_tools import parse_financial_data_response_enhanced, validate_and_complement_financial_data
                    financial_data = parse_financial_data_response_enhanced(str(response), context_text)
                    financial_data = validate_and_complement_financial_data(financial_data, context_text)
                    logger.info(f"从文件 {filename} 提取到 {len(financial_data)} 个指标")
            except Exception as e:
                logger.warning(f"从文件提取财务数据失败: {str(e)}，将使用默认提取方法")
        
        # 调用杜邦分析函数（现在是async）
        dupont_result = await generate_dupont_analysis(
            company_name=company_name,
            year=year,
            query_engine=query_engine,
            financial_data=financial_data  # 如果已提取，直接传递
        )
        
        logger.info(f"✅ 杜邦分析生成成功")
        
        # 将Decimal类型转换为float，确保JSON可序列化
        def convert_decimal_to_float(obj):
            """递归地将Decimal转换为float"""
            from decimal import Decimal
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal_to_float(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        # 转换结果
        serializable_result = convert_decimal_to_float(dupont_result)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "company_name": company_name,
                "year": year,
                "analysis": serializable_result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成杜邦分析失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"生成杜邦分析失败: {str(e)}"
        )

@router.post("/quick-overview")
async def get_quick_overview():
    """
    快速生成企业概况接口（结构化财务快照）
    
    两阶段生成：
    1. 第一阶段：提取关键财务指标（营收、净利润、现金流、负债率）
    2. 第二阶段：基于指标生成一句话结论
    
    Returns:
        财务快照数据，包含：
        - 关键指标（revenue, net_profit, operating_cash_flow, asset_liability_ratio）
        - verdict: 一句话结论
        - stage: 公司阶段（增长/稳态/下行）
        - profit_quality: 赚钱质量描述
        - risk_level: 风险级别（低/中/高）
    """
    try:
        from llama_index.core.llms import ChatMessage
        from llama_index.core import Settings
        import re
        
        logger.info("开始生成财务快照（两阶段生成）...")
        
        # 获取RAG引擎
        rag_engine = get_rag_engine()
        
        if not rag_engine.query_engine:
            if not rag_engine.load_existing_index():
                raise HTTPException(
                    status_code=400,
                    detail="索引未构建，请先处理文档"
                )
        
        llm = Settings.llm
        
        # ========== 第一阶段：快速提取关键财务指标（优先从Excel表格）==========
        logger.info("第一阶段：快速提取关键财务指标（优先从Excel表格）...")
        
        snapshot_dict = {
            "revenue": None,
            "net_profit": None,
            "operating_cash_flow": None,
            "asset_liability_ratio": None
        }
        
        import re
        
        # 优化：先使用RAG检索Excel表格数据，然后使用结构化输出提取
        try:
            # 第一步：优先检索Excel表格数据
            logger.info("🔍 优先检索Excel表格数据...")
            
            # 构建专门针对Excel表格的查询
            excel_queries = [
                "Excel表格 营业收入 净利润 经营现金流 资产负债率 最新年度数值",
                "利润表 资产负债表 现金流量表 Excel 营业收入 净利润 现金流 负债率",
                "财务报表表格 Excel 营业收入 净利润 经营现金流 资产负债率"
            ]
            
            excel_context = []
            for query in excel_queries:
                try:
                    # 使用RAG检索，然后手动过滤表格数据
                    retriever = rag_engine.index.as_retriever(similarity_top_k=20)
                    nodes = retriever.retrieve(query)
                    
                    # 优先选择表格数据和Excel相关数据
                    table_nodes = []
                    excel_nodes = []
                    other_nodes = []
                    
                    for node in nodes:
                        metadata = node.metadata
                        # 优先选择Excel表格和财务表格
                        if (metadata.get('document_type') == 'table_data' or 
                            metadata.get('is_financial', False) or
                            metadata.get('is_excel_table', False)):
                            table_nodes.append(node)
                        elif 'Excel' in node.text or '表格' in node.text or '利润表' in node.text:
                            excel_nodes.append(node)
                        else:
                            other_nodes.append(node)
                    
                    # 优先使用表格数据
                    if table_nodes:
                        for node in table_nodes[:5]:  # 最多取5个表格
                            excel_context.append(node.text)
                            table_id = node.metadata.get('table_id', 'unknown')
                            logger.info(f"  ✅ 检索到表格数据: {table_id}")
                    elif excel_nodes:
                        for node in excel_nodes[:3]:  # 最多取3个Excel相关文档
                            excel_context.append(node.text)
                    elif other_nodes:
                        # 最后才使用普通文档
                        for node in other_nodes[:2]:
                            excel_context.append(node.text)
                    
                    if excel_context:
                        break  # 如果找到数据，就不继续查询
                except Exception as e:
                    logger.warning(f"检索Excel数据时出错: {str(e)}")
                    continue
            
            # 合并检索到的Excel表格上下文
            excel_context_text = "\n\n".join(excel_context[:5]) if excel_context else ""
            
            if excel_context_text:
                logger.info(f"✅ 成功检索到Excel表格数据，长度: {len(excel_context_text)}字符")
            else:
                logger.warning("⚠️ 未检索到Excel表格数据，将使用全部文档检索")
            
            # 构建一次性提取所有指标的提示词（强调Excel表格）
            extract_prompt = f"""请从以下文档内容中快速提取关键财务指标的具体数值。

【重要提示】
1. 优先从Excel表格数据中提取（如果提供了表格数据）
2. Excel表格中的数据是最准确的，请优先使用
3. 如果表格中有多个年度数据，请使用最新年度的数据

【需要提取的指标】
1. 营业收入（最新年度，单位：元或亿元）
2. 净利润（最新年度，归属于母公司所有者的净利润，单位：元或亿元）
3. 经营活动产生的现金流量净额（经营现金流，单位：元或亿元）
4. 资产负债率（总负债/总资产，百分比）

【提取要求】
- 只提取数值，不要分析
- 如果有同比变化率，请一并提取（如"+20%"、"-5%"）
- 如果某个指标缺失，is_missing设为true
- 数值格式：如"100亿元"、"10.5亿元"、"30.5%"
- 优先从表格中提取，表格数据更准确

【文档内容】
{excel_context_text if excel_context_text else "请从所有已索引的文档中检索相关数据"}

请快速返回，只提取数据。"""
            
            # 使用结构化输出一次性提取所有指标
            sllm = llm.as_structured_llm(FinancialSnapshot)
            extract_response = await sllm.achat([
                ChatMessage(
                    role="system",
                    content="你是一个专业的财务数据提取助手。请快速从文档中准确提取财务指标数值，特别是Excel表格中的数值。Excel表格中的数据是最准确的，请优先使用表格数据。不要生成或猜测数据。只返回数据，不要分析。"
                ),
                ChatMessage(role="user", content=extract_prompt)
            ])
            
            if hasattr(extract_response, 'raw'):
                snapshot_data = extract_response.raw
            else:
                snapshot_data = extract_response
            
            if hasattr(snapshot_data, 'model_dump'):
                temp_dict = snapshot_data.model_dump()
            elif isinstance(snapshot_data, dict):
                temp_dict = snapshot_data
            else:
                temp_dict = {}
            
            # 更新snapshot_dict
            for key in ["revenue", "net_profit", "operating_cash_flow", "asset_liability_ratio"]:
                if key in temp_dict and temp_dict[key] is not None:
                    if hasattr(temp_dict[key], 'model_dump'):
                        snapshot_dict[key] = temp_dict[key].model_dump()
                    elif isinstance(temp_dict[key], dict):
                        snapshot_dict[key] = temp_dict[key]
            
            logger.info(f"✅ 快速提取完成（单次查询）")
            
        except Exception as e:
            logger.warning(f"结构化提取失败: {str(e)}，使用备用方案")
            
            # 备用方案：优先从Excel表格查询，然后使用正则提取
            try:
                logger.info("🔄 使用备用方案：优先检索Excel表格...")
                
                # 优先查询Excel表格
                excel_query = "Excel表格 Excel文件 利润表 资产负债表 现金流量表 营业收入 净利润 经营现金流 资产负债率 最新年度数值"
                
                # 尝试从表格数据中检索
                try:
                    retriever = rag_engine.index.as_retriever(similarity_top_k=15)
                    nodes = retriever.retrieve(excel_query)
                    
                    # 手动过滤表格数据
                    table_nodes = [n for n in nodes if n.metadata.get('document_type') == 'table_data' or n.metadata.get('is_financial', False)]
                    
                    if table_nodes:
                        response_text = "\n".join([node.text for node in table_nodes[:3]])
                        logger.info(f"  ✅ 从Excel表格检索到 {len(table_nodes)} 个表格数据")
                    elif nodes:
                        # 如果没有表格，使用所有检索到的数据
                        response_text = "\n".join([node.text for node in nodes[:3]])
                        logger.info(f"  ✅ 从文档检索到数据")
                    else:
                        # 回退到普通查询
                        response = rag_engine.query_engine.query(excel_query)
                        response_text = str(response).strip()
                except Exception as e:
                    logger.warning(f"表格检索失败: {str(e)}，使用普通查询")
                    # 如果表格检索失败，使用普通查询
                    response = rag_engine.query_engine.query(excel_query)
                    response_text = str(response).strip()
                
                # 使用正则表达式快速提取
                patterns = {
                    "revenue": [r'营业收入[：:]\s*([\d,\.]+[万千百十亿]?元?)', r'营收[：:]\s*([\d,\.]+[万千百十亿]?元?)'],
                    "net_profit": [r'净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)', r'归母净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)'],
                    "operating_cash_flow": [r'经营.*?现金流[：:]\s*([\d,\.]+[万千百十亿]?元?)', r'经营活动.*?现金流[：:]\s*([\d,\.]+[万千百十亿]?元?)'],
                    "asset_liability_ratio": [r'资产负债率[：:]\s*([\d,\.]+%?)']
                }
                
                for key, pattern_list in patterns.items():
                    for pattern in pattern_list:
                        match = re.search(pattern, response_text)
                        if match:
                            snapshot_dict[key] = {
                                "name": key,
                                "value": match.group(1),
                                "is_missing": False
                            }
                            break
                
                logger.info(f"✅ 备用方案提取完成")
                
            except Exception as e2:
                logger.warning(f"备用方案也失败: {str(e2)}")
        
        # ========== 第二阶段：快速生成结论（基于已提取的指标）==========
        logger.info("第二阶段：快速生成结论...")
        
        # 构建简化的指标摘要（不计算比率，加快速度）
        metrics_summary = []
        if snapshot_dict.get("revenue"):
            rev = snapshot_dict["revenue"]
            if isinstance(rev, dict) and not rev.get("is_missing"):
                metrics_summary.append(f"营业收入: {rev.get('value', 'N/A')}")
        if snapshot_dict.get("net_profit"):
            profit = snapshot_dict["net_profit"]
            if isinstance(profit, dict) and not profit.get("is_missing"):
                metrics_summary.append(f"净利润: {profit.get('value', 'N/A')}")
        if snapshot_dict.get("operating_cash_flow"):
            cash = snapshot_dict["operating_cash_flow"]
            if isinstance(cash, dict) and not cash.get("is_missing"):
                metrics_summary.append(f"经营现金流: {cash.get('value', 'N/A')}")
        if snapshot_dict.get("asset_liability_ratio"):
            ratio = snapshot_dict["asset_liability_ratio"]
            if isinstance(ratio, dict) and not ratio.get("is_missing"):
                metrics_summary.append(f"资产负债率: {ratio.get('value', 'N/A')}")
        
        metrics_text = "\n".join(metrics_summary) if metrics_summary else "财务数据不足"
        
        # 构建优化的提示词（强调使用Excel表格数据）
        verdict_prompt = f"""基于以下财务指标，快速生成一句话核心结论：

{metrics_text}

【重要提示】
- 这些数据来自Excel表格，是准确的财务数据
- 请基于这些具体数值进行分析，不要猜测

要求：
1. 只输出一句话核心结论，不要详细分析
2. 必须包含三个维度：
   - 公司阶段（增长/稳态/下行）- 根据营收和净利润数值判断
   - 赚钱质量（利润质量/现金质量）- 根据净利润和现金流判断
   - 风险级别（低/中/高）- 根据负债率判断
3. 格式：公司处于[阶段]阶段，[赚钱质量描述]，风险级别[级别]
4. 不超过60字
5. 如果数据不足，明确说明
6. 快速判断，基于Excel表格中的具体数值

示例：公司处于增长阶段，利润质量良好但现金质量一般，风险级别中等。"""
        
        try:
            # 优先从Excel表格检索相关数据来生成结论
            logger.info("🔍 检索Excel表格数据用于生成结论...")
            
            # 先尝试从表格中检索相关数据
            try:
                conclusion_retriever = rag_engine.index.as_retriever(similarity_top_k=12)
                all_conclusion_nodes = conclusion_retriever.retrieve("财务指标 营业收入 净利润 现金流 负债率 趋势 变化")
                
                # 手动过滤表格数据
                conclusion_nodes = [n for n in all_conclusion_nodes if n.metadata.get('document_type') == 'table_data' or n.metadata.get('is_financial', False)]
                
                if conclusion_nodes:
                    conclusion_context = "\n\n".join([node.text for node in conclusion_nodes[:3]])
                    verdict_prompt = f"""{verdict_prompt}

【补充的Excel表格数据】
{conclusion_context}

请结合上述Excel表格数据和财务指标，生成更准确的结论。"""
                    logger.info(f"  ✅ 已添加 {len(conclusion_nodes)} 个Excel表格上下文")
            except Exception as e:
                logger.warning(f"检索Excel表格数据失败: {str(e)}")
            
            # 使用query_engine生成结论（它会自动检索相关文档）
            response_obj = rag_engine.query_engine.query(verdict_prompt)
            verdict_text = str(response_obj).strip()
            
            # 清理结论文本
            verdict_text = re.sub(r'^(?:核心结论[：:]|核心结论\*\*[：:])\s*\*?\*?', '', verdict_text)
            verdict_text = re.sub(r'\*\*', '', verdict_text)
            
            # 只取第一句话
            if len(verdict_text) > 150:
                sentences = re.split(r'[。！？\n]', verdict_text)
                if sentences and len(sentences[0]) > 15:
                    verdict_text = sentences[0].strip() + '。'
                else:
                    verdict_text = verdict_text[:100] + '...'
            
            if not verdict_text or len(verdict_text) < 15:
                verdict_text = "数据不足，无法生成完整结论。"
            
            # 解析结论，提取三个维度
            stage = None
            profit_quality = None
            risk_level = None
            
            if '增长' in verdict_text:
                stage = '增长'
            elif '稳态' in verdict_text or '稳定' in verdict_text:
                stage = '稳态'
            elif '下行' in verdict_text or '下降' in verdict_text:
                stage = '下行'
            
            # 提取赚钱质量
            profit_match = re.search(r'利润质量[^，,。、]+', verdict_text)
            cash_match = re.search(r'现金质量[^，,。、]+', verdict_text)
            if profit_match and cash_match:
                profit_quality = profit_match.group(0) + '、' + cash_match.group(0)
            elif profit_match:
                profit_quality = profit_match.group(0)
            elif cash_match:
                profit_quality = cash_match.group(0)
            elif '利润质量差' in verdict_text:
                profit_quality = '利润质量差'
            elif '利润质量良好' in verdict_text:
                profit_quality = '利润质量良好'
            elif '现金质量无法评估' in verdict_text:
                profit_quality = '现金质量无法评估'
            
            # 提取风险级别
            if '风险级别低' in verdict_text or '风险低' in verdict_text:
                risk_level = '低'
            elif '风险级别中' in verdict_text or '风险中等' in verdict_text or '风险级别中等' in verdict_text:
                risk_level = '中'
            elif '风险级别高' in verdict_text or '风险高' in verdict_text:
                risk_level = '高'
            
        except Exception as e:
            logger.warning(f"生成结论失败: {str(e)}")
            verdict_text = "数据不足，无法生成完整结论。"
            stage = None
            profit_quality = None
            risk_level = None
        
        # 构建最终返回数据
        overview_data = {
            "revenue": snapshot_dict.get("revenue"),
            "net_profit": snapshot_dict.get("net_profit"),
            "operating_cash_flow": snapshot_dict.get("operating_cash_flow"),
            "asset_liability_ratio": snapshot_dict.get("asset_liability_ratio"),
            "verdict": verdict_text,
            "stage": stage,
            "profit_quality": profit_quality,
            "risk_level": risk_level,
            "missing_fields": []
        }
        
        # 检查缺失字段
        if not overview_data.get("revenue") or (isinstance(overview_data["revenue"], dict) and overview_data["revenue"].get("is_missing")):
            overview_data['missing_fields'].append('营业收入')
        if not overview_data.get("net_profit") or (isinstance(overview_data["net_profit"], dict) and overview_data["net_profit"].get("is_missing")):
            overview_data['missing_fields'].append('净利润')
        if not overview_data.get("operating_cash_flow") or (isinstance(overview_data["operating_cash_flow"], dict) and overview_data["operating_cash_flow"].get("is_missing")):
            overview_data['missing_fields'].append('经营现金流')
        if not stage:
            overview_data['missing_fields'].append('公司阶段')
        if not profit_quality:
            overview_data['missing_fields'].append('赚钱质量')
        if not risk_level:
            overview_data['missing_fields'].append('风险级别')
        
        logger.info(f"✅ 财务快照生成成功")
        
        return JSONResponse(status_code=200, content={
            "status": "success",
            "overview": overview_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成财务快照失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return JSONResponse(status_code=200, content={
            "status": "success",
            "overview": {
                "revenue": None,
                "net_profit": None,
                "operating_cash_flow": None,
                "asset_liability_ratio": None,
                "verdict": "数据不足，无法生成完整结论。",
                "stage": None,
                "profit_quality": None,
                "risk_level": None,
                "missing_fields": ["所有字段"]
            }
        })
