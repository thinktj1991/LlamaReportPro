"""
实时数据 API 接口
提供实时股价、新闻、公告等数据的 REST API
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from agents.realtime_tools import (
    get_realtime_stock_price,
    get_latest_financial_news,
    get_company_announcements,
    check_stock_alerts,
    get_market_overview
)
from data_sources.tushare_source import TushareDataSource
from data_sources.sina_source import SinaFinanceDataSource
from data_sources.news_source import NewsDataSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])


# ==================== 请求模型 ====================

class StockQuoteRequest(BaseModel):
    """股票行情请求"""
    stock_code: str = Field(description="股票代码，如 '600000.SH'")


class NewsRequest(BaseModel):
    """新闻请求"""
    company_name: str = Field(description="公司名称")
    limit: int = Field(default=10, ge=1, le=50, description="返回数量")


class AnnouncementRequest(BaseModel):
    """公告请求"""
    stock_code: str = Field(description="股票代码")
    limit: int = Field(default=10, ge=1, le=50, description="返回数量")


# ==================== API 端点 ====================

@router.get("/quote/{stock_code}")
async def get_quote(stock_code: str):
    """
    获取股票实时行情
    
    Args:
        stock_code: 股票代码（如 600000.SH）
        
    Returns:
        实时行情数据
    """
    try:
        logger.info(f"API请求 - 获取实时行情: {stock_code}")
        
        # 调用工具函数
        result = get_realtime_stock_price(stock_code)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stock_code": stock_code,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.post("/news")
async def get_news(request: NewsRequest):
    """
    获取公司最新新闻
    
    Args:
        request: 新闻请求
        
    Returns:
        新闻列表
    """
    try:
        logger.info(f"API请求 - 获取新闻: {request.company_name}")
        
        # 调用工具函数
        result = get_latest_financial_news(request.company_name, request.limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "company_name": request.company_name,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.post("/announcements")
async def get_announcements(request: AnnouncementRequest):
    """
    获取公司公告
    
    Args:
        request: 公告请求
        
    Returns:
        公告列表
    """
    try:
        logger.info(f"API请求 - 获取公告: {request.stock_code}")
        
        # 调用工具函数
        result = get_company_announcements(request.stock_code, request.limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stock_code": request.stock_code,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取公告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取公告失败: {str(e)}")


@router.get("/alerts/{stock_code}")
async def get_alerts(stock_code: str):
    """
    检查股票预警
    
    Args:
        stock_code: 股票代码
        
    Returns:
        预警信息
    """
    try:
        logger.info(f"API请求 - 检查预警: {stock_code}")
        
        # 调用工具函数
        result = check_stock_alerts(stock_code)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stock_code": stock_code,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"检查预警失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查预警失败: {str(e)}")


@router.get("/market/overview")
async def market_overview():
    """
    获取市场概览
    
    Returns:
        市场概览数据
    """
    try:
        logger.info("API请求 - 获取市场概览")
        
        # 调用工具函数
        result = get_market_overview()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    实时数据服务健康检查
    
    Returns:
        各数据源的健康状态
    """
    try:
        from agents.realtime_tools import get_tushare_source, get_sina_source, get_news_source
        
        # 获取各数据源状态
        tushare = get_tushare_source()
        sina = get_sina_source()
        news = get_news_source()
        
        health_status = {
            "service": "realtime-data",
            "status": "healthy",
            "data_sources": {
                "tushare": tushare.health_check(),
                "sina_finance": sina.health_check(),
                "news_aggregator": news.health_check()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查是否有数据源不可用
        unavailable_sources = []
        for source_name, source_status in health_status["data_sources"].items():
            if not source_status.get("is_initialized", False):
                unavailable_sources.append(source_name)
        
        if unavailable_sources:
            health_status["status"] = "degraded"
            health_status["unavailable_sources"] = unavailable_sources
            return JSONResponse(status_code=206, content=health_status)
        
        return JSONResponse(status_code=200, content=health_status)
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "realtime-data",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/statistics")
async def get_statistics():
    """
    获取实时数据服务统计信息
    
    Returns:
        统计数据
    """
    try:
        from agents.realtime_tools import get_tushare_source, get_sina_source, get_news_source
        
        # 获取各数据源统计
        tushare = get_tushare_source()
        sina = get_sina_source()
        news = get_news_source()
        
        statistics = {
            "service": "realtime-data",
            "data_sources": {
                "tushare": tushare.get_statistics(),
                "sina_finance": sina.get_statistics(),
                "news_aggregator": news.get_statistics()
            },
            "total_requests": sum([
                tushare.request_count,
                sina.request_count,
                news.request_count
            ]),
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(status_code=200, content=statistics)
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

