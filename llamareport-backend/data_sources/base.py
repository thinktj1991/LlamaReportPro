"""
数据源基类
定义统一的数据源接口，参考 LlamaIndex 文档的最佳实践
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseDataSource(ABC):
    """
    数据源基类
    
    参考 LlamaIndex 文档中的 BaseReader 模式设计
    提供统一的数据获取接口
    """
    
    def __init__(self, source_name: str):
        """
        初始化数据源
        
        Args:
            source_name: 数据源名称
        """
        self.source_name = source_name
        self.is_initialized = False
        self.last_error: Optional[str] = None
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化数据源连接
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            行情数据字典
        """
        pass
    
    @abstractmethod
    def get_company_news(
        self, 
        company_name: str, 
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取公司新闻
        
        Args:
            company_name: 公司名称
            limit: 返回数量
            start_date: 开始日期
            
        Returns:
            新闻列表
        """
        pass
    
    @abstractmethod
    def get_announcements(
        self, 
        stock_code: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取公司公告
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            公告列表
        """
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        return {
            "source_name": self.source_name,
            "is_initialized": self.is_initialized,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / max(self.request_count, 1),
            "last_error": self.last_error
        }
    
    def _record_request(self, success: bool, error: Optional[str] = None):
        """
        记录请求统计
        
        Args:
            success: 是否成功
            error: 错误信息
        """
        self.request_count += 1
        if success:
            self.success_count += 1
            self.last_error = None
        else:
            self.error_count += 1
            self.last_error = error
            logger.error(f"{self.source_name} request failed: {error}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        return {
            "source_name": self.source_name,
            "total_requests": self.request_count,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": f"{(self.success_count / max(self.request_count, 1) * 100):.2f}%",
            "is_healthy": self.error_count < self.success_count
        }

