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
                    "资产总额是多少？"
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
        rag_engine = get_rag_engine()
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

@router.get("/index-documents")
async def list_index_documents():
    """
    列出索引中的所有文档及其元数据
    
    Returns:
        索引中的所有文档列表
    """
    try:
        rag_engine = get_rag_engine()
        
        if not rag_engine.query_engine:
            if not rag_engine.load_existing_index():
                raise HTTPException(
                    status_code=400,
                    detail="索引未构建，请先处理文档"
                )
        
        if not rag_engine.index:
            return JSONResponse(status_code=200, content={
                "message": "索引未初始化",
                "documents": [],
                "files": []
            })
        
        # 获取所有文档
        all_docs = rag_engine.index.docstore.docs
        
        # 统计文件
        files_dict = {}
        documents_list = []
        
        for doc_id, doc in all_docs.items():
            metadata = doc.metadata or {}
            filename = metadata.get('filename') or metadata.get('source_file', 'unknown')
            doc_type = metadata.get('document_type', 'text')
            
            # 添加到文档列表
            documents_list.append({
                "doc_id": doc_id,
                "filename": filename,
                "document_type": doc_type,
                "page_number": metadata.get('page_number'),
                "table_id": metadata.get('table_id'),
                "text_preview": doc.text[:200] if doc.text else "",
                "text_length": len(doc.text) if doc.text else 0,
                "metadata": metadata
            })
            
            # 统计文件
            if filename not in files_dict:
                files_dict[filename] = {
                    'count': 0,
                    'types': set(),
                    'sample_text': doc.text[:100] if doc.text else ''
                }
            files_dict[filename]['count'] += 1
            files_dict[filename]['types'].add(doc_type)
        
        # 转换为列表格式
        files_list = []
        for filename, info in sorted(files_dict.items()):
            files_list.append({
                "filename": filename,
                "document_count": info['count'],
                "document_types": list(info['types']),
                "sample_text": info['sample_text']
            })
        
        # 检查ChromaDB集合
        chroma_info = {}
        if rag_engine.chroma_collection:
            try:
                all_data = rag_engine.chroma_collection.get()
                if all_data and 'ids' in all_data:
                    chroma_info = {
                        "vector_count": len(all_data['ids']),
                        "metadata_count": len(all_data.get('metadatas', []))
                    }
                    
                    # 统计ChromaDB中的文件名
                    metadatas = all_data.get('metadatas', [])
                    chroma_files = {}
                    for metadata in metadatas:
                        if metadata:
                            filename = metadata.get('filename') or metadata.get('source_file', 'unknown')
                            if filename not in chroma_files:
                                chroma_files[filename] = 0
                            chroma_files[filename] += 1
                    
                    chroma_info["files"] = chroma_files
            except Exception as e:
                chroma_info = {"error": str(e)}
        
        return JSONResponse(status_code=200, content={
            "message": f"索引中共有 {len(all_docs)} 个文档",
            "total_documents": len(all_docs),
            "total_files": len(files_dict),
            "files": files_list,
            "documents": documents_list[:100],  # 限制返回前100个文档，避免响应过大
            "chroma_info": chroma_info
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出索引文档失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"列出索引文档失败: {str(e)}")

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
    快速生成财务概况接口（结构化财务快照）
    
    两阶段生成：
    1. 第一阶段：提取关键财务指标（ROE、营收、净利润、资产总额、净息差、成本收入比）
    2. 第二阶段：基于指标生成一句话结论
    
    注意：只检索上传文档对应公司的数据
    
    Returns:
        财务快照数据，包含：
        - 关键指标（roe, revenue, net_profit, total_assets, net_interest_margin, cost_income_ratio）
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
        
        # ========== 第零阶段：从上传的文档中提取公司名称和年份 ==========
        logger.info("第零阶段：从上传的文档中提取公司名称和年份...")
        
        company_name = None
        year = None
        context_filter = {}
        uploaded_filenames = set()  # 保存上传的文件名列表，用于更严格的过滤
        
        try:
            # 方法1：直接从uploads目录的文件名中提取公司名称（最准确）
            from pathlib import Path
            upload_dir = Path("uploads")
            
            if upload_dir.exists():
                seen_companies = set()
                seen_years = set()
                # 遍历所有上传的文件
                for file_path in upload_dir.iterdir():
                    if file_path.is_file():
                        filename = file_path.name
                        uploaded_filenames.add(filename)  # 保存文件名
                        # 移除文件扩展名
                        name_without_ext = re.sub(r'\.[^.]+$', '', filename)
                        # 移除常见的报表类型关键词
                        name_clean = re.sub(r'(利润表|资产负债表|现金流量表|年报|报告|财务报表|财务报告)', '', name_without_ext, flags=re.IGNORECASE)
                        
                        # 从文件名提取年份（在移除年份之前）
                        if not year:
                            year_match = re.search(r'(\d{4})', filename)
                            if year_match:
                                candidate_year = year_match.group(1)
                                # 验证年份合理性
                                if 2000 <= int(candidate_year) <= 2030:
                                    year = candidate_year
                                    seen_years.add(year)
                                    logger.info(f"  从文件 '{filename}' 提取到年份: {year}")
                        
                        # 移除年份（4位数字）
                        name_clean = re.sub(r'\d{4}年?', '', name_clean)
                        # 移除"年度"和后面的数字（如"年度60"）
                        name_clean = re.sub(r'年度\d+', '', name_clean)
                        # 移除多余的空格和特殊字符
                        name_clean = re.sub(r'[_\-\s\.]+', '', name_clean).strip()
                        
                        if name_clean and len(name_clean) >= 2 and len(name_clean) <= 30:
                            seen_companies.add(name_clean)
                            logger.info(f"  从文件 '{filename}' 提取到公司名: {name_clean}")
                
                # 如果找到多个可能的公司名，选择最常见的
                if seen_companies:
                    from collections import Counter
                    company_counts = Counter(seen_companies)
                    # 选择出现次数最多的
                    company_name = company_counts.most_common(1)[0][0]
                    logger.info(f"✅ 从上传文件提取公司名称: {company_name} (出现 {company_counts[company_name]} 次)")
                    logger.info(f"✅ 上传的文件列表: {list(uploaded_filenames)}")
            
                # 如果找到多个年份，选择最常见的（通常应该只有一个）
                if seen_years:
                    from collections import Counter
                    year_counts = Counter(seen_years)
                    year = year_counts.most_common(1)[0][0]
                    logger.info(f"✅ 从上传文件提取年份: {year} (出现 {year_counts[year]} 次)")
            
            # 方法2：如果还没找到年份，从文档内容中提取
            if not year:
                try:
                    if upload_dir.exists():
                        uploaded_files = [f.name for f in upload_dir.iterdir() if f.is_file()]
                        if uploaded_files:
                            # 尝试从文档内容中提取年份
                            year_query = "报告年度 年份 年度报告 报告年份"
                            try:
                                retriever = rag_engine.index.as_retriever(similarity_top_k=20)
                                nodes = retriever.retrieve(year_query)
                                
                                # 只从当前上传的文件中提取
                                for node in nodes:
                                    filename = node.metadata.get('filename') or node.metadata.get('source_file', '')
                                    if filename in uploaded_filenames:
                                        # 从文本中提取年份
                                        node_text = node.text
                                        year_patterns = [
                                            r'报告年度[：:]\s*(\d{4})',
                                            r'(\d{4})年度',
                                            r'(\d{4})年[度]?报告',
                                        ]
                                        for pattern in year_patterns:
                                            year_match = re.search(pattern, node_text)
                                            if year_match:
                                                candidate_year = year_match.group(1)
                                                # 验证年份合理性
                                                if 2000 <= int(candidate_year) <= 2030:
                                                    year = candidate_year
                                                    logger.info(f"✅ 从文档内容提取年份: {year}")
                                                    break
                                        if year:
                                            break
                            except Exception as e:
                                logger.warning(f"从文档内容提取年份失败: {str(e)}")
                except Exception as e:
                    logger.warning(f"提取年份失败: {str(e)}")
            
            # 方法3：如果还没找到，从索引中的文档元数据中提取（只从当前上传的文件）
            if not company_name and rag_engine.index:
                try:
                    # 获取所有上传的文件名
                    uploaded_filenames = set()
                    if upload_dir.exists():
                        uploaded_filenames = {f.name for f in upload_dir.iterdir() if f.is_file()}
                    
                    if uploaded_filenames:
                        retriever = rag_engine.index.as_retriever(similarity_top_k=50)
                        nodes = retriever.retrieve("公司名称")
                        
                        # 只从当前上传的文件中提取
                        seen_companies = set()
                        for node in nodes:
                            filename = node.metadata.get('filename') or node.metadata.get('source_file', '')
                            # 只处理当前上传的文件
                            if filename in uploaded_filenames:
                                # 移除文件扩展名
                                name_without_ext = re.sub(r'\.[^.]+$', '', filename)
                                # 移除常见的报表类型关键词
                                name_clean = re.sub(r'(利润表|资产负债表|现金流量表|年报|报告|财务报表|财务报告)', '', name_without_ext, flags=re.IGNORECASE)
                                # 移除年份
                                name_clean = re.sub(r'\d{4}年?', '', name_clean)
                                # 移除"年度"和后面的数字
                                name_clean = re.sub(r'年度\d+', '', name_clean)
                                # 移除多余的空格和特殊字符
                                name_clean = re.sub(r'[_\-\s\.]+', '', name_clean).strip()
                                if name_clean and len(name_clean) >= 2 and len(name_clean) <= 30:
                                    seen_companies.add(name_clean)
                        
                        if seen_companies:
                            from collections import Counter
                            company_counts = Counter(seen_companies)
                            company_name = company_counts.most_common(1)[0][0]
                            logger.info(f"✅ 从索引元数据提取公司名称: {company_name}")
                except Exception as e:
                    logger.warning(f"从索引元数据提取公司名称失败: {str(e)}")
            
            # 方法3：如果还没找到，从文档内容中提取（但限制在当前上传的文件）
            if not company_name:
                try:
                    # 如果有上传的文件，使用文件名作为上下文
                    if upload_dir.exists():
                        uploaded_files = [f.name for f in upload_dir.iterdir() if f.is_file()]
                        if uploaded_files:
                            files_context = "、".join(uploaded_files[:5])  # 最多5个文件名
                            extract_query = f"请从以下文件名的文档中提取公司名称（完整的公司全称）：{files_context}。只返回公司名称，不要其他内容。"
                        else:
                            extract_query = "请从文档中提取公司名称（完整的公司全称），只返回公司名称，不要其他内容"
                    else:
                        extract_query = "请从文档中提取公司名称（完整的公司全称），只返回公司名称，不要其他内容"
                    
                    response = rag_engine.query_engine.query(extract_query)
                    response_text = str(response).strip()
                    
                    # 尝试提取公司名称
                    patterns = [
                        r'([^，,。\n]{2,30}(?:股份|有限|公司|集团|银行|证券|保险))',
                        r'公司名称[：:]\s*([^，,。\n]{2,30})',
                        r'([A-Za-z0-9\u4e00-\u9fa5]{2,20}(?:股份|有限|公司|集团))',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, response_text)
                        if match:
                            candidate = match.group(1).strip()
                            # 移除"年度"和后面的数字
                            candidate = re.sub(r'年度\d+', '', candidate).strip()
                            if len(candidate) >= 2 and len(candidate) <= 30:
                                company_name = candidate
                                logger.info(f"✅ 从文档内容提取公司名称: {company_name}")
                                break
                except Exception as e:
                    logger.warning(f"从文档内容提取公司名称失败: {str(e)}")
            
            # 如果找到了公司名称，设置context_filter
            if company_name:
                context_filter['company'] = company_name
                logger.info(f"✅ 设置公司过滤条件: {company_name}")
                
            # 如果找到了年份，设置context_filter
            if year:
                context_filter['year'] = year
                logger.info(f"✅ 设置年份过滤条件: {year}")
                
                # 如果找到了上传的文件名，也添加到过滤条件中（更严格的过滤）
                if uploaded_filenames:
                    # 注意：HybridRetriever的context_filter支持filename列表，但这里我们使用公司名过滤
                    # 文件名过滤会在HybridRetriever内部通过公司名匹配文件名来实现
                    logger.info(f"✅ 上传的文件数量: {len(uploaded_filenames)}")
            else:
                logger.warning("⚠️ 未找到公司名称，将检索所有文档")
                # 即使没有找到公司名，如果有上传的文件名，也可以尝试使用文件名过滤
                if uploaded_filenames and len(uploaded_filenames) == 1:
                    # 如果只有一个文件，可以使用文件名过滤
                    single_filename = list(uploaded_filenames)[0]
                    context_filter['filename'] = single_filename
                    logger.info(f"✅ 使用文件名过滤: {single_filename}")
                
        except Exception as e:
            logger.warning(f"提取公司名称失败: {str(e)}，将检索所有文档")
            import traceback
            logger.warning(f"详细错误: {traceback.format_exc()}")
        
        # 记录使用的过滤条件
        if context_filter:
            logger.info(f"📋 检索过滤条件: {context_filter}")
        
        # ========== 第一阶段：快速提取关键财务指标（优先从Excel表格）==========
        logger.info("第一阶段：快速提取关键财务指标（优先从Excel表格）...")
        
        snapshot_dict = {
            "roe": None,
            "revenue": None,
            "net_profit": None,
            "total_assets": None,
            "net_interest_margin": None,
            "cost_income_ratio": None
        }
        
        import re
        
        # 优化：先使用RAG检索所有文档（PDF和Excel）的表格数据，然后使用结构化输出提取
        try:
            # 使用HybridRetriever检索（与普通查询相同的方法）
            logger.info("🔍 使用HybridRetriever检索财务数据（与普通查询相同的方法）...")
            
            # 检查HybridRetriever是否可用
            use_hybrid = (rag_engine.use_hybrid_retriever and 
                         rag_engine.hybrid_retriever and 
                         rag_engine.hybrid_retriever.text_index and 
                         rag_engine.hybrid_retriever.table_index)
            
            if use_hybrid:
                logger.info("✅ 使用HybridRetriever进行混合检索（多指标分别检索）")
                
                # 定义6个关键指标及其查询关键词
                indicators = {
                    "roe": ["加权平均净资产收益率", "ROE", "净资产收益率"],
                    "revenue": ["营业收入", "营业总收入", "收入"],
                    "net_profit": ["净利润", "归属于母公司所有者的净利润", "归属于本行股东的净利润"],
                    "total_assets": ["资产总额", "总资产", "资产合计"],
                    "net_interest_margin": ["净息差"],
                    "cost_income_ratio": ["成本收入比"]
                }
                
                # 为每个指标单独检索，确保都能找到
                all_hybrid_results = []
                all_table_results = []
                found_indicators = set()
                
                year_prefix = f"{year}年 " if year else ""
                company_prefix = f"{company_name} " if company_name else ""
                
                for indicator_key, keywords in indicators.items():
                    # 为每个指标构建查询
                    query_keywords = " ".join(keywords)
                    if year and company_name:
                        query_text = f"{company_prefix}{year_prefix}{query_keywords} {year}年度数值"
                    elif year:
                        query_text = f"{year_prefix}{query_keywords} {year}年度数值"
                    elif company_name:
                        query_text = f"{company_prefix}{query_keywords} 最新年度数值"
                    else:
                        query_text = f"{query_keywords} 最新年度数值"
                    
                    logger.info(f"  🔍 检索指标: {indicator_key} ({keywords[0]})")
                    indicator_results = rag_engine.hybrid_retriever.retrieve(
                        query_text,
                        top_k=30,  # 每个指标检索30个结果
                        context_filter=context_filter if context_filter else None
                    )
                    
                    if indicator_results:
                        logger.info(f"    ✅ {indicator_key} 检索到 {len(indicator_results)} 个结果")
                        all_hybrid_results.extend(indicator_results)
                        
                        # 检查是否包含表格数据
                        for r in indicator_results:
                            doc = r.get('document')
                            if not doc:
                                continue
                            # 检查metadata
                            is_table = (
                                'table' in str(doc.metadata).lower() or 
                                doc.metadata.get('document_type') == 'table_data' or
                                doc.metadata.get('is_financial', False)
                            )
                            # 检查文本内容
                            text_preview = str(doc.text)[:500] if hasattr(doc, 'text') else ''
                            is_table_by_text = (
                                any(kw in text_preview for kw in keywords) or
                                '资产负债表' in text_preview or
                                '利润表' in text_preview or
                                '|' in text_preview or
                                ('项 目' in text_preview and (year in text_preview if year else True))
                            )
                            if is_table or is_table_by_text:
                                all_table_results.append(r)
                                found_indicators.add(indicator_key)
                    else:
                        logger.warning(f"    ⚠️ {indicator_key} 未检索到结果")
                
                # 去重（基于文档ID或文本内容）
                seen_docs = set()
                unique_hybrid_results = []
                unique_table_results = []
                
                for r in all_hybrid_results:
                    doc = r.get('document')
                    if not doc:
                        continue
                    doc_id = doc.metadata.get('file_path') or doc.metadata.get('filename') or str(doc.text)[:100]
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        unique_hybrid_results.append(r)
                
                for r in all_table_results:
                    doc = r.get('document')
                    if not doc:
                        continue
                    doc_id = doc.metadata.get('file_path') or doc.metadata.get('filename') or str(doc.text)[:100]
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        unique_table_results.append(r)
                
                logger.info(f"✅ 去重后共检索到 {len(unique_hybrid_results)} 个结果，其中 {len(unique_table_results)} 个是表格数据")
                logger.info(f"✅ 找到的指标: {', '.join(found_indicators) if found_indicators else '无'}")
                
                # 优先使用表格数据，如果表格数据不足，补充其他结果
                if unique_table_results:
                    logger.info(f"  ✅ 优先使用 {len(unique_table_results)} 个表格数据")
                    all_context_text = "\n\n".join([r['document'].text for r in unique_table_results[:20]])
                    
                    # 检查是否包含所有指标
                    missing_indicators = []
                    for indicator_key, keywords in indicators.items():
                        if not any(kw in all_context_text for kw in keywords):
                            missing_indicators.append(indicator_key)
                    
                    if missing_indicators:
                        logger.warning(f"  ⚠️ 表格数据中缺少以下指标: {', '.join(missing_indicators)}，补充其他结果")
                        # 补充非表格结果
                        non_table_results = [r for r in unique_hybrid_results if r not in unique_table_results]
                        if non_table_results:
                            additional_text = "\n\n".join([r['document'].text for r in non_table_results[:15]])
                            all_context_text = all_context_text + "\n\n" + additional_text
                    else:
                        logger.info(f"  ✅ 表格数据中包含所有6个指标")
                else:
                    logger.info(f"  ⚠️ 未识别出表格数据，使用所有结果")
                    all_context_text = "\n\n".join([r['document'].text for r in unique_hybrid_results[:30]])
                
                logger.info(f"✅ 构建上下文，长度: {len(all_context_text)}字符")
                
                # 最终检查所有指标
                final_missing = []
                for indicator_key, keywords in indicators.items():
                    if not any(kw in all_context_text for kw in keywords):
                        final_missing.append(indicator_key)
                
                if final_missing:
                    logger.warning(f"  ⚠️ 最终上下文中仍缺少以下指标: {', '.join(final_missing)}")
                else:
                    logger.info(f"  ✅ 最终上下文中包含所有6个指标")
                
                if not all_context_text:
                    logger.warning("⚠️ HybridRetriever未找到结果，使用query_engine")
                    use_hybrid = False
            
            if not use_hybrid:
                # 回退到使用query_engine查询（与普通查询相同）
                logger.info("🔍 使用query_engine查询财务数据...")
                
                # 使用多个查询，每个查询一个指标（这样更准确）
                # 如果有公司名称和年份，在查询中加入公司名称和年份限制
                if company_name and year:
                    queries = [
                        f"{company_name}{year}年的加权平均净资产收益率（ROE）是多少？请给出{year}年度的加权平均净资产收益率百分比",
                        f"{company_name}{year}年的营业收入是多少？请给出{year}年度的营业收入数值，包括单位（元、万元或亿元）",
                        f"{company_name}{year}年的净利润是多少？请给出{year}年度的归属于母公司所有者的净利润数值，包括单位",
                        f"{company_name}{year}年的资产总额是多少？请给出{year}年度的资产总额数值，包括单位（元、万元或亿元）",
                        f"{company_name}{year}年的净息差是多少？请给出{year}年度的净息差百分比",
                        f"{company_name}{year}年的成本收入比是多少？请给出{year}年度的成本收入比百分比"
                    ]
                elif company_name:
                    queries = [
                        f"{company_name}的加权平均净资产收益率（ROE）是多少？请给出最新年度的加权平均净资产收益率百分比",
                        f"{company_name}的营业收入是多少？请给出最新年度的营业收入数值，包括单位（元、万元或亿元）",
                        f"{company_name}的净利润是多少？请给出最新年度的归属于母公司所有者的净利润数值，包括单位",
                        f"{company_name}的资产总额是多少？请给出最新年度的资产总额数值，包括单位（元、万元或亿元）",
                        f"{company_name}的净息差是多少？请给出最新年度的净息差百分比",
                        f"{company_name}的成本收入比是多少？请给出最新年度的成本收入比百分比"
                    ]
                elif year:
                    queries = [
                        f"{year}年的加权平均净资产收益率（ROE）是多少？请给出{year}年度的加权平均净资产收益率百分比",
                        f"{year}年的营业收入是多少？请给出{year}年度的营业收入数值，包括单位（元、万元或亿元）",
                        f"{year}年的净利润是多少？请给出{year}年度的归属于母公司所有者的净利润数值，包括单位",
                        f"{year}年的资产总额是多少？请给出{year}年度的资产总额数值，包括单位（元、万元或亿元）",
                        f"{year}年的净息差是多少？请给出{year}年度的净息差百分比",
                        f"{year}年的成本收入比是多少？请给出{year}年度的成本收入比百分比"
                    ]
                else:
                    queries = [
                        "加权平均净资产收益率（ROE）是多少？请给出最新年度的加权平均净资产收益率百分比",
                        "营业收入是多少？请给出最新年度的营业收入数值，包括单位（元、万元或亿元）",
                        "净利润是多少？请给出最新年度的归属于母公司所有者的净利润数值，包括单位",
                        "资产总额是多少？请给出最新年度的资产总额数值，包括单位（元、万元或亿元）",
                        "净息差是多少？请给出最新年度的净息差百分比",
                        "成本收入比是多少？请给出最新年度的成本收入比百分比"
                    ]
                
                all_context_parts = []
                for query in queries:
                    try:
                        # 如果有context_filter，使用rag_engine.query方法（它会应用过滤）
                        if context_filter:
                            result = rag_engine.query(query, context_filter)
                            response_text = result.get('answer', '')
                        else:
                            response = rag_engine.query_engine.query(query)
                            response_text = str(response).strip()
                        
                        if response_text and len(response_text) > 20:
                            all_context_parts.append(response_text)
                            logger.info(f"  ✅ 查询成功: {query[:30]}...")
                    except Exception as e:
                        logger.warning(f"查询失败: {query[:30]}... - {str(e)}")
                
                # 合并所有查询结果
                all_context_text = "\n\n".join(all_context_parts) if all_context_parts else ""
                
                if not all_context_text:
                    # 如果还是没数据，使用一个综合查询
                    logger.info("🔄 使用综合查询...")
                    try:
                        if company_name and year:
                            comprehensive_query = f"请从{company_name}{year}年的文档中提取以下财务指标的具体数值：1.{year}年加权平均净资产收益率（ROE） 2.{year}年营业收入 3.{year}年净利润 4.{year}年资产总额 5.{year}年净息差 6.{year}年成本收入比。请给出{year}年度的数值和单位。"
                        elif company_name:
                            comprehensive_query = f"请从{company_name}的文档中提取以下财务指标的具体数值：1.加权平均净资产收益率（ROE） 2.营业收入 3.净利润 4.资产总额 5.净息差 6.成本收入比。请给出最新年度的数值和单位。"
                        elif year:
                            comprehensive_query = f"请从{year}年的文档中提取以下财务指标的具体数值：1.{year}年加权平均净资产收益率（ROE） 2.{year}年营业收入 3.{year}年净利润 4.{year}年资产总额 5.{year}年净息差 6.{year}年成本收入比。请给出{year}年度的数值和单位。"
                        else:
                            comprehensive_query = "请从所有文档中提取以下财务指标的具体数值：1.加权平均净资产收益率（ROE） 2.营业收入 3.净利润 4.资产总额 5.净息差 6.成本收入比。请给出最新年度的数值和单位。"
                        
                        # 如果有context_filter，使用rag_engine.query方法
                        if context_filter:
                            result = rag_engine.query(comprehensive_query, context_filter)
                            all_context_text = result.get('answer', '')
                        else:
                            response = rag_engine.query_engine.query(comprehensive_query)
                            all_context_text = str(response).strip()
                        logger.info(f"  ✅ 综合查询成功，长度: {len(all_context_text)}字符")
                    except Exception as e:
                        logger.warning(f"综合查询也失败: {str(e)}")
                        all_context_text = ""
            
            # 如果上下文太短，尝试直接检索表格数据（包括PDF和Excel）
            if len(all_context_text) < 500:
                logger.info("⚠️ 上下文太短，尝试直接检索表格数据（PDF和Excel）...")
                try:
                    retriever = rag_engine.index.as_retriever(similarity_top_k=50)
                    # 构建查询，明确包含资产总额
                    table_query = f"{year}年 资产负债表 资产总额 总资产 资产合计 加权平均净资产收益率 ROE 营业收入 净利润 净息差 成本收入比 {year}年度数值" if year else "资产负债表 资产总额 总资产 资产合计 加权平均净资产收益率 ROE 营业收入 净利润 净息差 成本收入比 最新年度数值"
                    nodes = retriever.retrieve(table_query)
                    
                    # 应用公司过滤
                    if context_filter and 'company' in context_filter:
                        nodes = rag_engine._filter_nodes(nodes, context_filter)
                        logger.info(f"  ✅ 应用公司过滤后，剩余 {len(nodes)} 个节点")
                    
                    # 手动过滤表格数据（包括PDF和Excel表格）
                    table_nodes = [n for n in nodes if (
                        n.metadata.get('document_type') == 'table_data' or 
                        n.metadata.get('is_financial', False) or
                        'table' in str(n.metadata).lower() or
                        '资产负债表' in str(n.text)[:200] or  # 检查文本内容
                        '资产总额' in str(n.text)[:200] or
                        '总资产' in str(n.text)[:200]
                    )]
                    
                    if table_nodes:
                        table_text = "\n\n".join([node.text for node in table_nodes[:15]])  # 增加数量
                        if len(table_text) > len(all_context_text):
                            all_context_text = table_text
                            logger.info(f"  ✅ 从表格数据获取到 {len(table_text)} 字符的上下文")
                            # 检查是否包含资产总额
                            if '资产总额' in table_text or '总资产' in table_text or '资产合计' in table_text:
                                logger.info(f"  ✅ 表格数据中包含资产总额相关信息")
                            else:
                                logger.warning(f"  ⚠️ 表格数据中未找到资产总额相关信息")
                    else:
                        logger.warning(f"  ⚠️ 未找到表格数据节点")
                except Exception as e:
                    logger.warning(f"检索表格数据失败: {str(e)}")
            
            # 构建一次性提取所有指标的提示词
            year_emphasis = f"{year}年" if year else "最新年度"
            extract_prompt = f"""请从以下检索到的文档内容中提取关键财务指标的具体数值。

【重要提示】
1. 这些内容是从PDF和Excel文件中检索到的，已经包含了最相关的数据
2. **特别注意：如果内容中包含表格（Markdown格式或文本表格），请仔细从表格中提取数据**
3. 营业收入可能有多种表述：营业收入、营业总收入、主营业务收入、收入等
4. **重要：请只提取{year_emphasis}的数据，不要使用其他年度的数据**
5. 如果文档中有多个年度数据，请优先使用{year_emphasis}的数据
6. 请仔细查找所有相关数据，特别是表格中的数据

【表格数据示例格式】
如果看到类似这样的表格：
| 项 目 | {year_emphasis} | 2023年 | 本年同比增减 |
|---|---|---|---|
| 营业收入 | 146,695 | 164,699 | (10.9%) |
| 加权平均净资产收益率 | 10.08% | 11.38% | -1.30个百分点 |

请从{year_emphasis}列中提取对应的数值。

【需要提取的指标】
1. 加权平均净资产收益率（ROE，{year_emphasis}，百分比）
   - 可能的表述：加权平均净资产收益率、ROE、净资产收益率等
   - **必须确保是{year_emphasis}的数据，使用年报披露的加权平均净资产收益率**
   - 示例：10.08% 或 10.08
2. 营业收入（{year_emphasis}，单位：元、万元或亿元）
   - 可能的表述：营业收入、营业总收入、主营业务收入、收入总额等
   - **必须确保是{year_emphasis}的数据**
   - 示例：146,695（万元）或 146,695万元
3. 净利润（{year_emphasis}，归属于母公司所有者的净利润，单位：元、万元或亿元）
   - 可能的表述：净利润、归属于母公司所有者的净利润、归母净利润、归属于本行股东的净利润等
   - **必须确保是{year_emphasis}的数据**
   - 示例：44,508（万元）或 44,508万元
4. 资产总额（{year_emphasis}，单位：元、万元或亿元）
   - 可能的表述：资产总额、总资产、资产合计等
   - **必须确保是{year_emphasis}的数据**
5. 净息差（{year_emphasis}，百分比）
   - 可能的表述：净息差、净利息收益率等
   - **必须确保是{year_emphasis}的数据**
   - 示例：1.87% 或 1.87
6. 成本收入比（{year_emphasis}，百分比）
   - 可能的表述：成本收入比、成本收入比率等
   - **必须确保是{year_emphasis}的数据**
   - 示例：27.66% 或 27.66

【提取要求】
- **优先从表格中提取数据**，表格数据最准确
- 仔细查找文档中的所有数据，不要遗漏
- **严格只提取{year_emphasis}的数据，忽略其他年度的数据**
- 只提取数值，不要分析
- 如果有同比变化率，请一并提取（如"+20%"、"-5%"、"下降"、"增长"等）
- 如果某个指标缺失，is_missing设为true
- 数值格式：如"100亿元"、"10.5亿元"、"30.5%"、"146,695万元"、"44,508万元"
- 必须从提供的文档内容中提取，不要编造数据

【检索到的文档内容】
{all_context_text if all_context_text else "未检索到相关文档内容"}

请仔细查找并提取所有能找到的{year_emphasis}财务数据。特别注意表格中的数据！"""
            
            # 优化：优先使用正则表达式从表格中直接提取（最可靠）
            logger.info("🔍 开始提取财务指标（优先使用正则表达式）...")
            logger.info(f"🔍 上下文文本长度: {len(all_context_text)}字符")
            
            # 第一步：使用正则表达式从表格文本中直接提取
            import re
            patterns = {
                "roe": [
                    r'加权平均净资产收益率[|\s]+([\d,\.]+%?)',
                    r'加权平均净资产收益率[：:]\s*([\d,\.]+%?)',
                    r'ROE[|\s]+([\d,\.]+%?)',
                    r'ROE[：:]\s*([\d,\.]+%?)',
                ],
                "revenue": [
                    r'营业收入[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'营业收入[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                    r'营业总收入[|\s]+([\d,\.]+[万千百十亿]?元?)',
                ],
                "net_profit": [
                    r'归属于本行股东的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'归属于母公司所有者的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                ],
                "total_assets": [
                    r'资产总额[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'总资产[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'资产合计[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    r'资产总额[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                ],
                "net_interest_margin": [
                    r'净息差[|\s]+([\d,\.]+%?)',
                    r'净息差[：:]\s*([\d,\.]+%?)',
                ],
                "cost_income_ratio": [
                    r'成本收入比[|\s]+([\d,\.]+%?)',
                    r'成本收入比[：:]\s*([\d,\.]+%?)',
                ]
            }
            
            # 从上下文中提取年份列的数据（如果指定了年份）
            regex_extracted = {}
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = list(re.finditer(pattern, all_context_text, re.IGNORECASE | re.MULTILINE))
                    if matches:
                        # 如果有年份，优先选择年份列的数据
                        best_match = None
                        if year:
                            # 查找表格格式：| 指标名 | 2024年 | 2023年 |
                            # 或者：指标名 | 数值(2024年) | 数值(2023年)
                            for match in matches:
                                # 检查匹配位置附近是否有年份
                                start = max(0, match.start() - 200)
                                end = min(len(all_context_text), match.end() + 200)
                                context_around = all_context_text[start:end]
                                
                                # 检查是否在年份列中（表格格式）
                                # 查找年份列的模式：| 2024年 | 数值 | 或 | 2024 | 数值 |
                                year_in_context = f"{year}年" in context_around or str(year) in context_around
                                
                                # 检查是否在正确的年份列（通过查找表格结构）
                                # 如果匹配值前面有年份，说明是正确的列
                                match_start = match.start()
                                before_match = all_context_text[max(0, match_start-50):match_start]
                                
                                # 检查表格行：| 指标 | 2024年 | 数值 |
                                if year_in_context or (str(year) in before_match and '|' in before_match):
                                    best_match = match
                                    logger.info(f"  ✅ 找到{year}年的数据: {key}")
                                    break
                        
                        if not best_match:
                            best_match = matches[0]  # 使用第一个匹配
                        
                        value = best_match.group(1).strip()
                        # 为百分比指标添加%符号
                        if key in ["roe", "net_interest_margin", "cost_income_ratio"] and not value.endswith('%'):
                            value = value + '%'
                        
                        # 提取同比增减数据（在匹配位置附近查找）
                        change_rate = None
                        change_direction = None
                        match_start = best_match.start()
                        match_end = best_match.end()
                        # 在匹配位置后查找同比增减（通常在表格的下一列）
                        after_match = all_context_text[match_end:match_end+200]
                        
                        # 查找同比增减模式（在表格的"本年同比增减"列中）
                        # 查找表格格式：| 指标 | 2024年 | 2023年 | 同比增减 |
                        change_patterns = [
                            r'([\+\-]?\d+\.?\d*%?)',  # 如 +10.9%、-5.2%
                            r'\(([\+\-]?\d+\.?\d*%?)\)',  # 如 (10.9%)、(-5.2%)
                            r'([\+\-]?\d+\.?\d*)\s*个百分点',  # 如 -1.30个百分点
                            r'(增长|下降|持平)',  # 文字描述
                        ]
                        
                        for change_pattern in change_patterns:
                            change_match = re.search(change_pattern, after_match)
                            if change_match:
                                change_text = change_match.group(1).strip()
                                # 判断是变化率还是方向
                                if any(c in change_text for c in ['+', '-', '%', '百分点']):
                                    change_rate = change_text
                                    # 根据正负号判断方向
                                    if change_text.startswith('+') or ('%' in change_text and not change_text.startswith('-')):
                                        change_direction = '增长'
                                    elif change_text.startswith('-') or ('-' in change_text):
                                        change_direction = '下降'
                                    else:
                                        change_direction = '持平'
                                elif change_text in ['增长', '下降', '持平']:
                                    change_direction = change_text
                                if change_rate or change_direction:
                                    break
                        
                        regex_extracted[key] = {
                            "name": {
                                "roe": "加权平均净资产收益率（ROE）",
                                "revenue": "营业收入",
                                "net_profit": "净利润",
                                "total_assets": "资产总额",
                                "net_interest_margin": "净息差",
                                "cost_income_ratio": "成本收入比"
                            }.get(key, key),
                            "value": value,
                            "change_rate": change_rate,
                            "change_direction": change_direction,
                            "is_missing": False
                        }
                        logger.info(f"  ✅ 正则提取到 {key}: {value}" + (f", 同比: {change_rate}" if change_rate else ""))
                        break
            
            # 更新snapshot_dict
            snapshot_dict.update(regex_extracted)
            logger.info(f"✅ 正则表达式提取完成，提取到 {len(regex_extracted)} 个指标")
            
            # 第二步：如果正则提取不完整，使用JSON格式的LLM提取补充
            missing_keys = [k for k in ["roe", "revenue", "net_profit", "total_assets", "net_interest_margin", "cost_income_ratio"] 
                          if snapshot_dict.get(k) is None]
            
            if missing_keys:
                logger.info(f"⚠️ 以下指标未通过正则提取，使用JSON格式LLM提取: {missing_keys}")
                
                # 使用简化的JSON格式提取
                json_prompt = f"""请从以下文档内容中提取财务指标，以JSON格式返回。

要求：
1. 只提取{year_emphasis}的数据
2. 返回格式必须是有效的JSON，格式如下（必须包含change_rate和change_direction字段）：
{{
  "roe": {{"name": "加权平均净资产收益率（ROE）", "value": "10.08%", "change_rate": "-1.30个百分点", "change_direction": "下降", "is_missing": false}},
  "revenue": {{"name": "营业收入", "value": "146,695万元", "change_rate": "-10.9%", "change_direction": "下降", "is_missing": false}},
  "net_profit": {{"name": "净利润", "value": "44,508万元", "change_rate": "-4.2%", "change_direction": "下降", "is_missing": false}},
  "total_assets": {{"name": "资产总额", "value": "5,000,000万元", "change_rate": "+3.7%", "change_direction": "增长", "is_missing": false}},
  "net_interest_margin": {{"name": "净息差", "value": "1.87%", "change_rate": "-0.51个百分点", "change_direction": "下降", "is_missing": false}},
  "cost_income_ratio": {{"name": "成本收入比", "value": "27.66%", "change_rate": "-0.24个百分点", "change_direction": "下降", "is_missing": false}}
}}

3. 如果找不到某个指标，设置 "is_missing": true, "value": null
4. 如果找不到同比增减数据，change_rate和change_direction可以设为null
5. 只返回JSON，不要其他文字说明
6. 优先从表格中提取数据，特别注意"本年同比增减"或"同比增减"列

文档内容：
{all_context_text[:3000] if len(all_context_text) > 3000 else all_context_text}

请返回JSON格式的数据："""
                
                try:
                    json_response = await llm.acomplete(json_prompt)
                    json_text = str(json_response).strip()
                    
                    # 提取JSON部分
                    json_match = re.search(r'\{[\s\S]*\}', json_text)
                    if json_match:
                        import json
                        json_data = json.loads(json_match.group(0))
                        
                        # 更新缺失的指标
                        for key in missing_keys:
                            if key in json_data and json_data[key]:
                                metric_data = json_data[key]
                                if isinstance(metric_data, dict) and not metric_data.get('is_missing'):
                                    snapshot_dict[key] = metric_data
                                    logger.info(f"  ✅ JSON提取到 {key}: {metric_data.get('value')}")
                except Exception as e:
                    logger.warning(f"  ❌ JSON提取失败: {str(e)}")
            
            # 第三步：如果还有缺失的指标，进行补充检索
            still_missing = [k for k in ["roe", "revenue", "net_profit", "total_assets", "net_interest_margin", "cost_income_ratio"] 
                           if snapshot_dict.get(k) is None]
            
            if still_missing and use_hybrid:
                logger.info(f"⚠️ 以下指标仍未提取到，进行补充检索: {still_missing}")
                
                # 为每个缺失的指标单独进行补充检索
                indicator_keywords = {
                    "roe": ["加权平均净资产收益率", "ROE"],
                    "revenue": ["营业收入", "营业总收入"],
                    "net_profit": ["净利润", "归属于母公司所有者的净利润"],
                    "total_assets": ["资产总额", "总资产", "资产合计"],
                    "net_interest_margin": ["净息差"],
                    "cost_income_ratio": ["成本收入比"]
                }
                
                supplement_contexts = []
                for missing_key in still_missing:
                    keywords = indicator_keywords.get(missing_key, [missing_key])
                    if year and company_name:
                        supplement_query = f"{company_name} {year}年 {' '.join(keywords)} {year}年度数值"
                    elif year:
                        supplement_query = f"{year}年 {' '.join(keywords)} {year}年度数值"
                    elif company_name:
                        supplement_query = f"{company_name} {' '.join(keywords)} 最新年度数值"
                    else:
                        supplement_query = f"{' '.join(keywords)} 最新年度数值"
                    
                    logger.info(f"  🔍 补充检索: {missing_key} ({keywords[0]})")
                    try:
                        supplement_results = rag_engine.hybrid_retriever.retrieve(
                            supplement_query,
                            top_k=20,
                            context_filter=context_filter if context_filter else None
                        )
                        
                        if supplement_results:
                            supplement_text = "\n\n".join([r['document'].text for r in supplement_results[:10]])
                            supplement_contexts.append(supplement_text)
                            logger.info(f"    ✅ {missing_key} 补充检索到 {len(supplement_results)} 个结果")
                        else:
                            logger.warning(f"    ⚠️ {missing_key} 补充检索未找到结果")
                    except Exception as e:
                        logger.warning(f"    ❌ {missing_key} 补充检索失败: {str(e)}")
                
                # 将补充的上下文添加到all_context_text
                if supplement_contexts:
                    all_context_text = all_context_text + "\n\n" + "\n\n".join(supplement_contexts)
                    logger.info(f"✅ 补充检索后，上下文长度: {len(all_context_text)}字符")
                    
                    # 对补充的上下文再次进行正则提取
                    for missing_key in still_missing:
                        keywords = indicator_keywords.get(missing_key, [missing_key])
                        patterns = {
                            "roe": [r'加权平均净资产收益率[|\s]+([\d,\.]+%?)', r'ROE[|\s]+([\d,\.]+%?)'],
                            "revenue": [r'营业收入[|\s]+([\d,\.]+[万千百十亿]?元?)', r'营业总收入[|\s]+([\d,\.]+[万千百十亿]?元?)'],
                            "net_profit": [r'归属于本行股东的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)', r'归属于母公司所有者的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)', r'净利润[|\s]+([\d,\.]+[万千百十亿]?元?)'],
                            "total_assets": [r'资产总额[|\s]+([\d,\.]+[万千百十亿]?元?)', r'总资产[|\s]+([\d,\.]+[万千百十亿]?元?)', r'资产合计[|\s]+([\d,\.]+[万千百十亿]?元?)'],
                            "net_interest_margin": [r'净息差[|\s]+([\d,\.]+%?)'],
                            "cost_income_ratio": [r'成本收入比[|\s]+([\d,\.]+%?)']
                        }
                        
                        key_patterns = patterns.get(missing_key, [])
                        for pattern in key_patterns:
                            matches = list(re.finditer(pattern, all_context_text, re.IGNORECASE | re.MULTILINE))
                            if matches:
                                best_match = matches[0]
                                value = best_match.group(1).strip()
                                if missing_key in ["roe", "net_interest_margin", "cost_income_ratio"] and not value.endswith('%'):
                                    value = value + '%'
                                
                                snapshot_dict[missing_key] = {
                                    "name": {
                                        "roe": "加权平均净资产收益率（ROE）",
                                        "revenue": "营业收入",
                                        "net_profit": "净利润",
                                        "total_assets": "资产总额",
                                        "net_interest_margin": "净息差",
                                        "cost_income_ratio": "成本收入比"
                                    }.get(missing_key, missing_key),
                                    "value": value,
                                    "change_rate": None,
                                    "change_direction": None,
                                    "is_missing": False
                                }
                                logger.info(f"  ✅ 补充检索后正则提取到 {missing_key}: {value}")
                                break
            
            logger.info(f"✅ 提取完成，最终提取到的指标: {[k for k, v in snapshot_dict.items() if v is not None and (not isinstance(v, dict) or not v.get('is_missing'))]}")
            
        except Exception as e:
            logger.warning(f"结构化提取失败: {str(e)}，使用备用方案")
            import traceback
            logger.warning(f"详细错误: {traceback.format_exc()}")
            
            # 备用方案：优先从Excel表格查询，然后使用正则提取
            try:
                logger.info("🔄 使用备用方案：优先检索Excel表格...")
                
                # 优先查询Excel表格，强调年份
                if year:
                    excel_query = f"Excel表格 Excel文件 利润表 资产负债表 现金流量表 {year}年 加权平均净资产收益率 ROE 营业收入 净利润 资产总额 净息差 成本收入比 {year}年度数值"
                else:
                    excel_query = "Excel表格 Excel文件 利润表 资产负债表 现金流量表 加权平均净资产收益率 ROE 营业收入 净利润 资产总额 净息差 成本收入比 最新年度数值"
                
                # 尝试从表格数据中检索（应用公司过滤）
                try:
                    retriever = rag_engine.index.as_retriever(similarity_top_k=30)  # 扩大检索范围以便过滤
                    nodes = retriever.retrieve(excel_query)
                    
                    # 应用公司过滤
                    if context_filter and 'company' in context_filter:
                        nodes = rag_engine._filter_nodes(nodes, context_filter)
                        logger.info(f"  ✅ 应用公司过滤后，剩余 {len(nodes)} 个节点")
                    
                    # 手动过滤表格数据
                    table_nodes = [n for n in nodes if n.metadata.get('document_type') == 'table_data' or n.metadata.get('is_financial', False)]
                    
                    if table_nodes:
                        response_text = "\n".join([node.text for node in table_nodes[:10]])  # 增加表格数量，确保包含资产负债表
                        logger.info(f"  ✅ 从Excel表格检索到 {len(table_nodes)} 个表格数据（已应用公司过滤）")
                        logger.info(f"  📊 表格文本长度: {len(response_text)}字符")
                        # 检查是否包含资产总额相关关键词
                        if '资产总额' in response_text or '总资产' in response_text or '资产合计' in response_text:
                            logger.info(f"  ✅ 表格中包含资产总额相关数据")
                        else:
                            logger.warning(f"  ⚠️ 表格中未找到资产总额相关关键词")
                    elif nodes:
                        # 如果没有表格，使用所有检索到的数据
                        response_text = "\n".join([node.text for node in nodes[:3]])
                        logger.info(f"  ✅ 从文档检索到数据（已应用公司过滤）")
                    else:
                        # 回退到普通查询（应用公司过滤）
                        if context_filter:
                            result = rag_engine.query(excel_query, context_filter)
                            response_text = result.get('answer', '').strip()
                        else:
                            response = rag_engine.query_engine.query(excel_query)
                            response_text = str(response).strip()
                except Exception as e:
                    logger.warning(f"表格检索失败: {str(e)}，使用普通查询")
                    # 如果表格检索失败，使用普通查询（应用公司过滤）
                    if context_filter:
                        result = rag_engine.query(excel_query, context_filter)
                        response_text = result.get('answer', '').strip()
                    else:
                        response = rag_engine.query_engine.query(excel_query)
                        response_text = str(response).strip()
                
                # 使用正则表达式快速提取（增加更多模式，包括表格格式）
                patterns = {
                    "roe": [
                        # 表格格式：| 加权平均净资产收益率 | 10.08% | 11.38% |
                        r'加权平均净资产收益率[|\s]+([\d,\.]+%?)',
                        r'加权平均净资产收益率[：:]\s*([\d,\.]+%?)',
                        r'加权平均净资产收益率\s+([\d,\.]+%?)',
                        r'ROE[|\s]+([\d,\.]+%?)',
                        r'ROE[：:]\s*([\d,\.]+%?)',
                        r'ROE\s+([\d,\.]+%?)',
                        r'净资产收益率[|\s]+([\d,\.]+%?)',
                        r'净资产收益率[：:]\s*([\d,\.]+%?)',
                        r'净资产收益率\s+([\d,\.]+%?)',
                    ],
                    "revenue": [
                        # 表格格式：| 营业收入 | 146,695 | 164,699 |
                        r'营业收入[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'营业收入[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'营收[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'营业总收入[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'主营业务收入[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'收入[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'营业收入\s+([\d,\.]+[万千百十亿]?元?)',
                        r'营业总收入\s+([\d,\.]+[万千百十亿]?元?)',
                        # 表格格式：营业收入 | 数值
                        r'营业收入[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'营业总收入[|\s]+([\d,\.]+[万千百十亿]?元?)',
                    ],
                    "net_profit": [
                        # 表格格式：| 归属于本行股东的净利润 | 44,508 | 46,455 |
                        r'归属于本行股东的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'归属于母公司所有者的净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'归母净利润[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'归母净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'归属于母公司所有者的净利润[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'净利润\s+([\d,\.]+[万千百十亿]?元?)',
                        r'归母净利润\s+([\d,\.]+[万千百十亿]?元?)',
                    ],
                    "total_assets": [
                        # 表格格式：| 资产总额 | 5,000,000 | 4,800,000 |
                        r'资产总额[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'总资产[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'资产合计[|\s]+([\d,\.]+[万千百十亿]?元?)',
                        r'资产总额[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'总资产[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'资产合计[：:]\s*([\d,\.]+[万千百十亿]?元?)',
                        r'资产总额\s+([\d,\.]+[万千百十亿]?元?)',
                        r'总资产\s+([\d,\.]+[万千百十亿]?元?)',
                        r'资产合计\s+([\d,\.]+[万千百十亿]?元?)',
                    ],
                    "net_interest_margin": [
                        # 表格格式：| 净息差 | 1.87% | 2.38% |
                        r'净息差[|\s]+([\d,\.]+%?)',
                        r'净息差[：:]\s*([\d,\.]+%?)',
                        r'净息差\s+([\d,\.]+%?)',
                        r'净利息收益率[|\s]+([\d,\.]+%?)',
                        r'净利息收益率[：:]\s*([\d,\.]+%?)',
                        r'净利息收益率\s+([\d,\.]+%?)',
                    ],
                    "cost_income_ratio": [
                        # 表格格式：| 成本收入比 | 27.66% | 27.90% |
                        r'成本收入比[|\s]+([\d,\.]+%?)',
                        r'成本收入比[：:]\s*([\d,\.]+%?)',
                        r'成本收入比\s+([\d,\.]+%?)',
                        r'成本收入比率[|\s]+([\d,\.]+%?)',
                        r'成本收入比率[：:]\s*([\d,\.]+%?)',
                        r'成本收入比率\s+([\d,\.]+%?)',
                    ]
                }
                
                for key, pattern_list in patterns.items():
                    found = False
                    for pattern in pattern_list:
                        match = re.search(pattern, response_text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            value = match.group(1).strip()
                            # 为百分比指标添加%符号（如果没有）
                            if key in ["roe", "net_interest_margin", "cost_income_ratio"] and not value.endswith('%'):
                                value = value + '%'
                            # 为金额类指标添加单位（如果没有）
                            if key in ["revenue", "net_profit", "total_assets"] and not any(unit in value for unit in ['元', '万元', '亿元', '千元']):
                                # 如果数值很大（超过1000），可能是万元或亿元
                                num_value = value.replace(',', '').replace('，', '')
                                try:
                                    num = float(num_value)
                                    if num >= 100000000:
                                        value = value + '亿元'
                                    elif num >= 10000:
                                        value = value + '万元'
                                    else:
                                        value = value + '元'
                                except:
                                    pass
                            snapshot_dict[key] = {
                                "name": {
                                    "roe": "加权平均净资产收益率（ROE）",
                                    "revenue": "营业收入",
                                    "net_profit": "净利润",
                                    "total_assets": "资产总额",
                                    "net_interest_margin": "净息差",
                                    "cost_income_ratio": "成本收入比"
                                }.get(key, key),
                                "value": value,
                                "is_missing": False
                            }
                            logger.info(f"  ✅ 正则提取到 {key}: {value} (模式: {pattern[:50]}...)")
                            found = True
                            break
                    if not found:
                        logger.warning(f"  ⚠️ 未找到 {key} 的数据")
                
                logger.info(f"✅ 备用方案提取完成")
                
            except Exception as e2:
                logger.warning(f"备用方案也失败: {str(e2)}")
        
        # ========== 第二阶段：快速生成结论（基于已提取的指标）==========
        logger.info("第二阶段：快速生成结论...")
        
        # 构建简化的指标摘要（不计算比率，加快速度）
        metrics_summary = []
        if snapshot_dict.get("roe"):
            roe = snapshot_dict["roe"]
            if isinstance(roe, dict) and not roe.get("is_missing"):
                metrics_summary.append(f"ROE: {roe.get('value', 'N/A')}")
        if snapshot_dict.get("revenue"):
            rev = snapshot_dict["revenue"]
            if isinstance(rev, dict) and not rev.get("is_missing"):
                metrics_summary.append(f"营业收入: {rev.get('value', 'N/A')}")
        if snapshot_dict.get("net_profit"):
            profit = snapshot_dict["net_profit"]
            if isinstance(profit, dict) and not profit.get("is_missing"):
                metrics_summary.append(f"净利润: {profit.get('value', 'N/A')}")
        if snapshot_dict.get("total_assets"):
            assets = snapshot_dict["total_assets"]
            if isinstance(assets, dict) and not assets.get("is_missing"):
                metrics_summary.append(f"资产总额: {assets.get('value', 'N/A')}")
        if snapshot_dict.get("net_interest_margin"):
            nim = snapshot_dict["net_interest_margin"]
            if isinstance(nim, dict) and not nim.get("is_missing"):
                metrics_summary.append(f"净息差: {nim.get('value', 'N/A')}")
        if snapshot_dict.get("cost_income_ratio"):
            cir = snapshot_dict["cost_income_ratio"]
            if isinstance(cir, dict) and not cir.get("is_missing"):
                metrics_summary.append(f"成本收入比: {cir.get('value', 'N/A')}")
        
        metrics_text = "\n".join(metrics_summary) if metrics_summary else "财务数据不足"
        year_info = f"{year}年" if year else "最新年度"
        
        # 构建优化的提示词（强调使用Excel表格数据和年份）
        verdict_prompt = f"""基于以下{year_info}财务指标，快速生成一句话核心结论：

{metrics_text}

【重要提示】
- 这些数据来自Excel表格，是准确的财务数据
- **这些数据是{year_info}的数据，请基于{year_info}的数值进行分析**
- 请基于这些具体数值进行分析，不要猜测

要求：
1. 只输出一句话核心结论，不要详细分析
2. 必须包含三个维度：
   - 公司阶段（增长/稳态/下行）- 根据{year_info}营收和净利润数值判断
   - 赚钱质量（利润质量/资产质量）- 根据{year_info}净利润和资产总额判断
   - 风险级别（低/中/高）- 根据{year_info}财务指标综合判断
3. 格式：公司处于[阶段]阶段，[赚钱质量描述]，风险级别[级别]
4. 不超过60字
5. 如果数据不足，明确说明
6. 快速判断，基于Excel表格中{year_info}的具体数值

示例：公司处于增长阶段，利润质量良好但现金质量一般，风险级别中等。"""
        
        try:
            # 优先从Excel表格检索相关数据来生成结论
            logger.info("🔍 检索Excel表格数据用于生成结论...")
            
            # 先尝试从表格中检索相关数据（应用公司过滤）
            try:
                conclusion_retriever = rag_engine.index.as_retriever(similarity_top_k=30)  # 扩大检索范围以便过滤
                if year:
                    conclusion_query = f"{year}年 财务指标 ROE 加权平均净资产收益率 营业收入 净利润 资产总额 净息差 成本收入比 趋势 变化 {year}年度"
                else:
                    conclusion_query = "财务指标 ROE 加权平均净资产收益率 营业收入 净利润 资产总额 净息差 成本收入比 趋势 变化"
                all_conclusion_nodes = conclusion_retriever.retrieve(conclusion_query)
                
                # 应用公司过滤
                if context_filter and 'company' in context_filter:
                    all_conclusion_nodes = rag_engine._filter_nodes(all_conclusion_nodes, context_filter)
                    logger.info(f"  ✅ 应用公司过滤后，剩余 {len(all_conclusion_nodes)} 个节点")
                
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
            
            # 使用rag_engine.query生成结论（它会应用公司过滤）
            if context_filter:
                result = rag_engine.query(verdict_prompt, context_filter)
                verdict_text = result.get('answer', '').strip()
            else:
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
            "roe": snapshot_dict.get("roe"),
            "revenue": snapshot_dict.get("revenue"),
            "net_profit": snapshot_dict.get("net_profit"),
            "total_assets": snapshot_dict.get("total_assets"),
            "net_interest_margin": snapshot_dict.get("net_interest_margin"),
            "cost_income_ratio": snapshot_dict.get("cost_income_ratio"),
            "verdict": verdict_text,
            "stage": stage,
            "profit_quality": profit_quality,
            "risk_level": risk_level,
            "missing_fields": []
        }
        
        # 添加调试日志：检查每个指标的状态
        logger.info(f"🔍 最终返回数据检查:")
        for key in ["roe", "revenue", "net_profit", "total_assets", "net_interest_margin", "cost_income_ratio"]:
            value = overview_data.get(key)
            if value:
                if isinstance(value, dict):
                    logger.info(f"  {key}: value={value.get('value')}, is_missing={value.get('is_missing')}")
                else:
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: None")
        
        # 检查缺失字段
        if not overview_data.get("revenue") or (isinstance(overview_data["revenue"], dict) and overview_data["revenue"].get("is_missing")):
            overview_data['missing_fields'].append('营业收入')
        if not overview_data.get("net_profit") or (isinstance(overview_data["net_profit"], dict) and overview_data["net_profit"].get("is_missing")):
            overview_data['missing_fields'].append('净利润')
        if not overview_data.get("total_assets") or (isinstance(overview_data["total_assets"], dict) and overview_data["total_assets"].get("is_missing")):
            overview_data['missing_fields'].append('资产总额')
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
                "roe": None,
                "revenue": None,
                "net_profit": None,
                "total_assets": None,
                "verdict": "数据不足，无法生成完整结论。",
                "stage": None,
                "profit_quality": None,
                "risk_level": None,
                "missing_fields": ["所有字段"]
            }
        })
