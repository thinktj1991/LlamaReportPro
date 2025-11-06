"""
Tushare 数据源
提供 Tushare API 的数据接入
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from .base import BaseDataSource

logger = logging.getLogger(__name__)


class TushareDataSource(BaseDataSource):
    """
    Tushare 数据源
    
    支持免费版和专业版 API
    参考: https://tushare.pro/
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        初始化 Tushare 数据源
        
        Args:
            api_token: Tushare API Token
        """
        super().__init__("Tushare")
        self.api_token = api_token
        self.pro_api = None
    
    def initialize(self) -> bool:
        """初始化 Tushare 连接"""
        try:
            if not self.api_token:
                logger.warning("Tushare API token not provided, using limited features")
                self.is_initialized = True
                return True
            
            import tushare as ts
            
            # 设置 token
            ts.set_token(self.api_token)
            self.pro_api = ts.pro_api()
            
            self.is_initialized = True
            logger.info("✅ Tushare 数据源初始化成功")
            return True
            
        except ImportError:
            error = "Tushare package not installed. Run: pip install tushare"
            self._record_request(False, error)
            logger.error(error)
            return False
        except Exception as e:
            error = f"Tushare initialization failed: {str(e)}"
            self._record_request(False, error)
            logger.error(error)
            return False
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码（如 '600000.SH' 或 '000001.SZ'）
            
        Returns:
            实时行情数据
        """
        try:
            if not self.is_initialized:
                self.initialize()
            
            if not self.pro_api:
                logger.warning("Tushare Pro API not available")
                return None
            
            # 标准化股票代码
            ts_code = self._normalize_stock_code(stock_code)
            
            # 获取实时行情（使用日线数据作为替代）
            today = datetime.now().strftime('%Y%m%d')
            df = self.pro_api.daily(ts_code=ts_code, start_date=today, end_date=today)
            
            if df.empty:
                logger.warning(f"No realtime data for {ts_code}")
                self._record_request(False, "No data available")
                return None
            
            # 获取基本信息
            stock_basic = self.pro_api.stock_basic(ts_code=ts_code, fields='ts_code,name')
            stock_name = stock_basic.iloc[0]['name'] if not stock_basic.empty else "未知"
            
            # 转换为标准格式
            row = df.iloc[0]
            quote_data = {
                "stock_code": ts_code,
                "stock_name": stock_name,
                "current_price": float(row['close']),
                "open_price": float(row['open']),
                "high_price": float(row['high']),
                "low_price": float(row['low']),
                "close_price": float(row['pre_close']),
                "change_amount": float(row['change']),
                "change_percent": float(row['pct_chg']),
                "volume": float(row['vol']) * 100,  # 转换为手
                "amount": float(row['amount']) * 1000,  # 转换为元
                "timestamp": datetime.now(),
                "data_source": "Tushare"
            }
            
            # 获取估值数据
            try:
                daily_basic = self.pro_api.daily_basic(
                    ts_code=ts_code, 
                    start_date=today, 
                    end_date=today,
                    fields='ts_code,pe,pb,total_mv,circ_mv,turnover_rate'
                )
                
                if not daily_basic.empty:
                    basic_row = daily_basic.iloc[0]
                    quote_data.update({
                        "pe_ratio": float(basic_row['pe']) if basic_row['pe'] else None,
                        "pb_ratio": float(basic_row['pb']) if basic_row['pb'] else None,
                        "total_market_cap": float(basic_row['total_mv']) / 10000 if basic_row['total_mv'] else None,  # 转换为亿
                        "circulating_market_cap": float(basic_row['circ_mv']) / 10000 if basic_row['circ_mv'] else None,
                        "turnover_rate": float(basic_row['turnover_rate']) if basic_row['turnover_rate'] else None
                    })
            except Exception as e:
                logger.warning(f"Failed to get basic metrics: {e}")
            
            self._record_request(True)
            return quote_data
            
        except Exception as e:
            error = f"Failed to get realtime quote: {str(e)}"
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
        
        注意: Tushare 免费版不提供新闻数据
        此方法返回空列表，建议使用其他数据源
        
        Args:
            company_name: 公司名称
            limit: 返回数量
            start_date: 开始日期
            
        Returns:
            新闻列表（Tushare 暂不支持）
        """
        logger.warning("Tushare does not provide news data, use NewsDataSource instead")
        return []
    
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
        try:
            if not self.is_initialized:
                self.initialize()
            
            if not self.pro_api:
                logger.warning("Tushare Pro API not available")
                return []
            
            ts_code = self._normalize_stock_code(stock_code)
            
            # 获取最近30天的公告
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.pro_api.anns(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.info(f"No announcements found for {ts_code}")
                return []
            
            # 转换为标准格式
            announcements = []
            for idx, row in df.head(limit).iterrows():
                announcement = {
                    "announcement_id": str(row.get('ann_id', idx)),
                    "stock_code": ts_code,
                    "stock_name": row.get('name', ''),
                    "title": row.get('title', ''),
                    "announcement_type": row.get('type', '未知'),
                    "publish_date": datetime.strptime(str(row['ann_date']), '%Y%m%d') if 'ann_date' in row else datetime.now(),
                    "pdf_url": row.get('url', None),
                    "is_important": row.get('level', 0) > 0,
                    "data_source": "Tushare"
                }
                announcements.append(announcement)
            
            self._record_request(True)
            return announcements
            
        except Exception as e:
            error = f"Failed to get announcements: {str(e)}"
            self._record_request(False, error)
            logger.error(error)
            return []
    
    def get_financial_indicator(
        self, 
        stock_code: str, 
        period: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务指标
        
        Args:
            stock_code: 股票代码
            period: 报告期（格式：YYYYMMDD），默认最新
            
        Returns:
            财务指标数据
        """
        try:
            if not self.is_initialized:
                self.initialize()
            
            if not self.pro_api:
                return None
            
            ts_code = self._normalize_stock_code(stock_code)
            
            # 获取财务指标
            df = self.pro_api.fina_indicator(
                ts_code=ts_code,
                period=period,
                fields='ts_code,end_date,roe,roa,gross_margin,net_margin,debt_to_assets,current_ratio'
            )
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                "stock_code": ts_code,
                "period": row['end_date'],
                "roe": float(row['roe']) if row['roe'] else None,
                "roa": float(row['roa']) if row['roa'] else None,
                "gross_margin": float(row['gross_margin']) if row['gross_margin'] else None,
                "net_margin": float(row['net_margin']) if row['net_margin'] else None,
                "debt_to_assets": float(row['debt_to_assets']) if row['debt_to_assets'] else None,
                "current_ratio": float(row['current_ratio']) if row['current_ratio'] else None,
                "data_source": "Tushare"
            }
            
        except Exception as e:
            logger.error(f"Failed to get financial indicator: {e}")
            return None
    
    def _normalize_stock_code(self, stock_code: str) -> str:
        """
        标准化股票代码为 Tushare 格式
        
        Args:
            stock_code: 输入的股票代码
            
        Returns:
            标准化后的代码（如 '600000.SH'）
        """
        # 移除空格
        code = stock_code.strip()
        
        # 如果已经是标准格式，直接返回
        if '.' in code:
            return code.upper()
        
        # 判断市场
        if code.startswith('6'):
            return f"{code}.SH"  # 上海
        elif code.startswith(('0', '3')):
            return f"{code}.SZ"  # 深圳
        elif code.startswith('8') or code.startswith('4'):
            return f"{code}.BJ"  # 北京
        else:
            # 默认上海
            return f"{code}.SH"

