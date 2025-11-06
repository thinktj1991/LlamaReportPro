"""
新浪财经数据源
通过爬虫获取新浪财经的实时数据
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import re
from .base import BaseDataSource

logger = logging.getLogger(__name__)


class SinaFinanceDataSource(BaseDataSource):
    """
    新浪财经数据源
    
    通过 API 或爬虫获取实时行情数据
    优势: 免费、实时性好、无需 token
    """
    
    def __init__(self):
        """初始化新浪财经数据源"""
        super().__init__("SinaFinance")
        self.base_url = "http://hq.sinajs.cn/list="
    
    def initialize(self) -> bool:
        """初始化连接"""
        try:
            # 新浪财经不需要特殊初始化
            self.is_initialized = True
            logger.info("✅ 新浪财经数据源初始化成功")
            return True
        except Exception as e:
            error = f"新浪财经初始化失败: {str(e)}"
            self._record_request(False, error)
            logger.error(error)
            return False
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情数据
        """
        try:
            import requests
            
            if not self.is_initialized:
                self.initialize()
            
            # 转换股票代码为新浪格式
            sina_code = self._to_sina_code(stock_code)
            
            # 请求数据
            url = f"{self.base_url}{sina_code}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # 解析数据
            content = response.text
            if not content or "FAILED" in content:
                logger.warning(f"新浪财经未返回数据: {stock_code}")
                self._record_request(False, "No data returned")
                return None
            
            # 提取数据
            match = re.search(r'="(.+)";', content)
            if not match:
                logger.warning(f"无法解析新浪财经数据: {stock_code}")
                self._record_request(False, "Parse failed")
                return None
            
            data_str = match.group(1)
            data_parts = data_str.split(',')
            
            if len(data_parts) < 32:
                logger.warning(f"新浪财经数据格式异常: {stock_code}")
                self._record_request(False, "Invalid data format")
                return None
            
            # 解析各字段
            quote_data = {
                "stock_code": stock_code,
                "stock_name": data_parts[0],
                "current_price": float(data_parts[3]),
                "open_price": float(data_parts[1]),
                "close_price": float(data_parts[2]),  # 昨收
                "high_price": float(data_parts[4]),
                "low_price": float(data_parts[5]),
                "volume": float(data_parts[8]) / 100,  # 成交量(手)
                "amount": float(data_parts[9]),  # 成交额(元)
                "timestamp": datetime.now(),
                "data_source": "SinaFinance"
            }
            
            # 计算涨跌
            if quote_data["close_price"] > 0:
                change_amount = quote_data["current_price"] - quote_data["close_price"]
                change_percent = (change_amount / quote_data["close_price"]) * 100
                quote_data["change_amount"] = round(change_amount, 2)
                quote_data["change_percent"] = round(change_percent, 2)
            
            self._record_request(True)
            return quote_data
            
        except ImportError:
            error = "requests package not installed. Run: pip install requests"
            self._record_request(False, error)
            logger.error(error)
            return None
        except Exception as e:
            error = f"获取新浪财经行情失败: {str(e)}"
            self._record_request(False, error)
            logger.error(error)
            return None
    
    def get_company_news(
        self, 
        company_name: str, 
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取公司新闻
        
        新浪财经新闻需要通过网页爬取，建议使用专门的新闻数据源
        
        Args:
            company_name: 公司名称
            limit: 返回数量
            start_date: 开始日期
            
        Returns:
            新闻列表
        """
        logger.warning("新浪财经新闻爬取功能待实现，建议使用 NewsDataSource")
        return []
    
    def get_announcements(
        self, 
        stock_code: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取公司公告
        
        新浪财经公告需要通过网页爬取
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            公告列表
        """
        logger.warning("新浪财经公告爬取功能待实现，建议使用巨潮资讯")
        return []
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览
        
        Returns:
            市场概览数据（上证、深证、创业板指数）
        """
        try:
            import requests
            
            # 获取主要指数
            indices = {
                "上证指数": "s_sh000001",
                "深证成指": "s_sz399001",
                "创业板指": "s_sz399006"
            }
            
            overview = {}
            for name, code in indices.items():
                url = f"{self.base_url}{code}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    match = re.search(r'="(.+)";', response.text)
                    if match:
                        data = match.group(1).split(',')
                        if len(data) >= 6:
                            overview[name] = {
                                "index_name": name,
                                "index_code": code,
                                "current_value": float(data[1]),
                                "change_amount": float(data[2]),
                                "change_percent": float(data[3]),
                                "volume": float(data[4]) if len(data) > 4 else None,
                                "amount": float(data[5]) if len(data) > 5 else None,
                                "timestamp": datetime.now()
                            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {}
    
    def _to_sina_code(self, stock_code: str) -> str:
        """
        转换股票代码为新浪格式
        
        Args:
            stock_code: 标准股票代码
            
        Returns:
            新浪格式代码（如 'sh600000' 或 'sz000001'）
        """
        # 移除空格和点号
        code = stock_code.strip().replace('.', '').upper()
        
        # 提取纯数字代码
        if code.endswith('SH'):
            return f"sh{code[:-2]}"
        elif code.endswith('SZ'):
            return f"sz{code[:-2]}"
        elif code.endswith('BJ'):
            return f"bj{code[:-2]}"
        else:
            # 根据代码判断市场
            if code.startswith('6'):
                return f"sh{code}"
            elif code.startswith(('0', '3')):
                return f"sz{code}"
            else:
                return f"sh{code}"  # 默认上海

