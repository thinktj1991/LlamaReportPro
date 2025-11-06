"""
数据源模块
提供多种财务数据源的统一接口
"""

from .base import BaseDataSource
from .tushare_source import TushareDataSource
from .sina_source import SinaFinanceDataSource
from .news_source import NewsDataSource

__all__ = [
    'BaseDataSource',
    'TushareDataSource',
    'SinaFinanceDataSource',
    'NewsDataSource',
]

