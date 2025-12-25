"""
Agent API 接口
提供基于 Agent 的年报分析功能
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import logging
import asyncio
from pathlib import Path

from core.rag_engine import RAGEngine
from agents.report_agent import ReportAgent
from agents.template_renderer import TemplateRenderer
from models.report_models import ReportGenerationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


def _clean_decimal_types(obj: Any) -> Any:
    """
    递归清理数据中的 Decimal 类型，转换为 float 以便 JSON 序列化
    
    Args:
        obj: 需要清理的对象（可以是 dict, list, Decimal, 或其他类型）
    
    Returns:
        清理后的对象，所有 Decimal 类型都转换为 float
    """
    try:
        from decimal import Decimal
        
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: _clean_decimal_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [_clean_decimal_types(item) for item in obj]
        else:
            return obj
    except ImportError:
        # 如果 decimal 模块不可用，直接返回原对象
        return obj

# 全局实例(延迟初始化)
rag_engine = None
report_agent = None
template_renderer = None

def get_rag_engine():
    """获取 RAG 引擎实例"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine

def get_report_agent():
    """获取 Report Agent 实例"""
    global report_agent
    if report_agent is None:
        try:
            rag = get_rag_engine()
            if not rag.query_engine:
                # 尝试加载现有索引
                logger.info("🔄 RAG查询引擎未初始化，尝试加载现有索引...")
                if not rag.load_existing_index():
                    error_msg = (
                        "RAG 引擎未初始化，请先上传并处理文档。\n"
                        "请确保：\n"
                        "1. 已上传PDF文档\n"
                        "2. 已处理文档并构建索引\n"
                        "3. ChromaDB索引文件存在"
                    )
                    logger.error(f"❌ {error_msg}")
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
            logger.info("✅ RAG查询引擎已就绪，初始化ReportAgent...")
            report_agent = ReportAgent(rag.query_engine)
            logger.info("✅ ReportAgent初始化成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ ReportAgent初始化失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"ReportAgent初始化失败: {str(e)}"
            )
    return report_agent

def get_template_renderer():
    """获取模板渲染器实例"""
    global template_renderer
    if template_renderer is None:
        template_renderer = TemplateRenderer()
    return template_renderer


# ==================== 请求/响应模型 ====================

class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    company_name: str = Field(description="公司名称")
    year: str = Field(description="年份,如'2023'")
    custom_query: Optional[str] = Field(default=None, description="自定义查询(可选)")
    save_to_file: bool = Field(default=False, description="是否保存到文件")
    output_path: Optional[str] = Field(default=None, description="输出文件路径(可选)")


class GenerateSectionRequest(BaseModel):
    """生成章节请求"""
    section_name: str = Field(
        description="章节名称: financial_review, business_guidance, business_highlights, profit_forecast"
    )
    company_name: str = Field(description="公司名称")
    year: str = Field(description="年份")


class AgentQueryRequest(BaseModel):
    """Agent 查询请求"""
    question: str = Field(description="用户问题")


# ==================== API 端点 ====================

@router.post("/generate-report")
async def generate_report(request: GenerateReportRequest, background_tasks: BackgroundTasks):
    """
    生成完整的年报分析报告
    
    使用 Agent 自动分析年报并生成结构化报告
    """
    try:
        logger.info(f"收到生成报告请求: {request.company_name} {request.year}年")
        
        # 获取 Agent
        agent = get_report_agent()
        
        # 生成报告
        result = await agent.generate_report(
            company_name=request.company_name,
            year=request.year,
            user_query=request.custom_query
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 如果需要保存到文件
        if request.save_to_file:
            renderer = get_template_renderer()
            output_path = request.output_path or f"reports/{request.company_name}_{request.year}_report.md"
            
            # 在后台任务中保存文件
            if result.get("structured_response"):
                background_tasks.add_task(
                    renderer.save_report,
                    result["structured_response"],
                    output_path
                )
        
        response_data = {
            "status": "success",
            "company_name": request.company_name,
            "year": request.year,
            "report": result["report"],
            "structured_response": result.get("structured_response"),
            "saved_to": request.output_path if request.save_to_file else None
        }
        # 清理 Decimal 类型
        response_data = _clean_decimal_types(response_data)
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ 生成报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-section")
async def generate_section(request: GenerateSectionRequest):
    """
    生成单个报告章节
    
    可以单独生成财务点评、业绩指引、业务亮点或盈利预测章节
    """
    try:
        logger.info(f"收到生成章节请求: {request.section_name}")
        
        # 验证章节名称
        valid_sections = ["financial_review", "business_guidance", "business_highlights", "profit_forecast"]
        if request.section_name not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"无效的章节名称。有效值: {', '.join(valid_sections)}"
            )
        
        # 获取 Agent
        agent = get_report_agent()
        
        # 生成章节
        result = await agent.generate_section(
            section_name=request.section_name,
            company_name=request.company_name,
            year=request.year
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 清理 Decimal 类型
        cleaned_result = _clean_decimal_types(result)
        return JSONResponse(content=cleaned_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 生成章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def agent_query(request: AgentQueryRequest):
    """
    Agent 通用查询接口
    
    使用 Agent 回答关于年报的任何问题
    
    返回格式:
    {
        "status": "success" | "error",
        "question": str,
        "answer": str,
        "tool_calls": List[Dict],  # 工具调用结果列表
        "structured_response": Dict,  # 结构化响应（可选）
        "visualization": Dict  # 可视化数据（可选）
    }
    """
    try:
        logger.info(f"收到 Agent 查询: {request.question[:50]}...")
        
        # 获取 Agent
        agent = get_report_agent()
        
        # 执行查询，添加整体超时保护（10分钟，提高响应速度）
        import time
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                agent.query(request.question),
                timeout=600.0  # 10分钟整体超时
            )
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Agent查询完成，耗时: {elapsed_time:.2f}秒")
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Agent查询整体超时（10分钟），实际耗时: {elapsed_time:.2f}秒")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": f"Agent查询超时（超过10分钟），实际耗时: {elapsed_time:.2f}秒。请简化查询或使用普通查询模式",
                    "question": request.question,
                    "timeout_seconds": 600.0,
                    "elapsed_seconds": elapsed_time
                }
            )
        
        if result["status"] == "error":
            # 统一错误响应格式
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": result.get("error", "未知错误"),
                    "question": result.get("question", request.question)
                }
            )
        
        # 确保返回格式统一，包含所有必要字段
        response_data = {
            "status": result.get("status", "success"),
            "question": result.get("question", request.question),
            "answer": result.get("answer", ""),
            "tool_calls": result.get("tool_calls", []),  # 确保是列表
            "structured_response": result.get("structured_response"),
            "visualization": result.get("visualization")
        }
        
        # 清理响应数据中的 Decimal 类型，确保 JSON 可序列化
        response_data = _clean_decimal_types(response_data)
        
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Agent 查询失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "question": request.question
            }
        )


@router.get("/status")
async def agent_status():
    """
    获取 Agent 状态

    检查 Agent 是否已初始化并可用
    """
    try:
        # 尝试初始化 RAG 引擎
        rag = get_rag_engine()

        # 尝试加载索引
        index_loaded = False
        if rag.query_engine:
            index_loaded = True
        else:
            # 尝试加载现有索引
            index_loaded = rag.load_existing_index()

        status = {
            "rag_engine_initialized": rag_engine is not None,
            "report_agent_initialized": report_agent is not None,
            "template_renderer_initialized": template_renderer is not None,
            "index_loaded": index_loaded,
            "ready": index_loaded
        }

        if not index_loaded:
            status["message"] = "请先上传并处理文档以初始化 RAG 引擎"
        else:
            status["message"] = "Agent 系统已就绪"
            # 如果索引已加载,尝试初始化 Agent
            if report_agent is None:
                try:
                    get_report_agent()
                    status["report_agent_initialized"] = True
                except Exception as e:
                    logger.warning(f"⚠️ Agent 初始化失败: {str(e)}")

        return JSONResponse(content=status)

    except Exception as e:
        logger.error(f"❌ 获取 Agent 状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates():
    """
    列出所有可用的报告模板
    """
    try:
        renderer = get_template_renderer()
        templates = renderer.list_templates()
        
        return JSONResponse(content={
            "templates": templates,
            "count": len(templates)
        })
        
    except Exception as e:
        logger.error(f"❌ 列出模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render-template")
async def render_template(report_data: Dict[str, Any], template_name: str = "annual_report_template.md.jinja2"):
    """
    使用指定模板渲染报告数据
    
    Args:
        report_data: 报告数据(JSON格式)
        template_name: 模板文件名
    
    Returns:
        渲染后的 Markdown 文本
    """
    try:
        logger.info(f"收到模板渲染请求: {template_name}")
        
        renderer = get_template_renderer()
        rendered = renderer.render_report(report_data, template_name)
        
        return JSONResponse(content={
            "status": "success",
            "template": template_name,
            "rendered": rendered
        })
        
    except Exception as e:
        logger.error(f"❌ 模板渲染失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "agent-api",
        "version": "1.0.0"
    })

