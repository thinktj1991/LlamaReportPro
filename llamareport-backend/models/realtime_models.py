"""
实时数据模型
基于 Pydantic v2 定义实时金融数据的结构化模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class NewsSentiment(str, Enum):
    """新闻情绪"""
    POSITIVE = "positive"      # 正面
    NEUTRAL = "neutral"        # 中性
    NEGATIVE = "negative"      # 负面


class AlertLevel(str, Enum):
    """预警级别"""
    INFO = "info"              # 信息
    WARNING = "warning"        # 警告
    CRITICAL = "critical"      # 严重


# ==================== 实时行情模型 ====================

class RealtimeQuote(BaseModel):
    """实时行情数据"""
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    
    # 价格信息
    current_price: float = Field(description="最新价")
    open_price: Optional[float] = Field(default=None, description="今开")
    high_price: Optional[float] = Field(default=None, description="最高")
    low_price: Optional[float] = Field(default=None, description="最低")
    close_price: Optional[float] = Field(default=None, description="昨收")
    
    # 涨跌信息
    change_amount: Optional[float] = Field(default=None, description="涨跌额")
    change_percent: Optional[float] = Field(default=None, description="涨跌幅(%)")
    
    # 成交信息
    volume: Optional[float] = Field(default=None, description="成交量(手)")
    amount: Optional[float] = Field(default=None, description="成交额(元)")
    turnover_rate: Optional[float] = Field(default=None, description="换手率(%)")
    
    # 估值信息
    pe_ratio: Optional[float] = Field(default=None, description="市盈率(动态)")
    pb_ratio: Optional[float] = Field(default=None, description="市净率")
    total_market_cap: Optional[float] = Field(default=None, description="总市值(亿)")
    circulating_market_cap: Optional[float] = Field(default=None, description="流通市值(亿)")
    
    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.now, description="数据时间")
    data_source: str = Field(default="unknown", description="数据来源")


class MarketOverview(BaseModel):
    """市场概览"""
    index_name: str = Field(description="指数名称")
    index_code: str = Field(description="指数代码")
    current_value: float = Field(description="当前点位")
    change_percent: float = Field(description="涨跌幅(%)")
    volume: Optional[float] = Field(default=None, description="成交量")
    amount: Optional[float] = Field(default=None, description="成交额")
    timestamp: datetime = Field(default_factory=datetime.now, description="数据时间")


# ==================== 新闻模型 ====================

class NewsItem(BaseModel):
    """新闻条目"""
    news_id: str = Field(description="新闻ID")
    title: str = Field(description="新闻标题")
    summary: Optional[str] = Field(default=None, description="新闻摘要")
    content: Optional[str] = Field(default=None, description="新闻正文")
    
    # 分类信息
    category: Optional[str] = Field(default=None, description="新闻分类")
    tags: List[str] = Field(default_factory=list, description="新闻标签")
    
    # 来源信息
    source: str = Field(description="新闻来源")
    author: Optional[str] = Field(default=None, description="作者")
    url: Optional[str] = Field(default=None, description="新闻链接")
    
    # 时间信息
    publish_time: datetime = Field(description="发布时间")
    crawl_time: datetime = Field(default_factory=datetime.now, description="爬取时间")
    
    # 情绪分析
    sentiment: Optional[NewsSentiment] = Field(default=None, description="情绪倾向")
    sentiment_score: Optional[float] = Field(default=None, description="情绪分数(-1到1)")
    
    # 关联信息
    related_stocks: List[str] = Field(default_factory=list, description="相关股票代码")
    importance_score: Optional[float] = Field(default=None, description="重要性分数(0-1)")


class NewsList(BaseModel):
    """新闻列表"""
    total_count: int = Field(description="新闻总数")
    news_items: List[NewsItem] = Field(description="新闻条目列表")
    query_params: Optional[Dict[str, Any]] = Field(default=None, description="查询参数")
    timestamp: datetime = Field(default_factory=datetime.now, description="查询时间")


# ==================== 公告模型 ====================

class Announcement(BaseModel):
    """公司公告"""
    announcement_id: str = Field(description="公告ID")
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    
    # 公告信息
    title: str = Field(description="公告标题")
    announcement_type: str = Field(description="公告类型")
    
    # 内容
    summary: Optional[str] = Field(default=None, description="公告摘要")
    content: Optional[str] = Field(default=None, description="公告正文")
    
    # 时间信息
    publish_date: datetime = Field(description="发布日期")
    
    # 文件信息
    pdf_url: Optional[str] = Field(default=None, description="PDF链接")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    
    # 重要性
    is_important: bool = Field(default=False, description="是否重要公告")
    importance_score: Optional[float] = Field(default=None, description="重要性分数")


class AnnouncementList(BaseModel):
    """公告列表"""
    total_count: int = Field(description="公告总数")
    announcements: List[Announcement] = Field(description="公告列表")
    stock_code: str = Field(description="股票代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="查询时间")


# ==================== 行业对比模型 ====================

class CompanyComparison(BaseModel):
    """公司对比数据"""
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    
    # 估值指标
    pe_ratio: Optional[float] = Field(default=None, description="市盈率")
    pb_ratio: Optional[float] = Field(default=None, description="市净率")
    ps_ratio: Optional[float] = Field(default=None, description="市销率")
    
    # 盈利指标
    roe: Optional[float] = Field(default=None, description="净资产收益率(%)")
    roa: Optional[float] = Field(default=None, description="总资产收益率(%)")
    gross_margin: Optional[float] = Field(default=None, description="毛利率(%)")
    net_margin: Optional[float] = Field(default=None, description="净利率(%)")
    
    # 规模指标
    total_revenue: Optional[float] = Field(default=None, description="营业收入(亿)")
    net_profit: Optional[float] = Field(default=None, description="净利润(亿)")
    total_assets: Optional[float] = Field(default=None, description="总资产(亿)")
    market_cap: Optional[float] = Field(default=None, description="市值(亿)")
    
    # 排名
    industry_rank: Optional[int] = Field(default=None, description="行业排名")


class IndustryComparison(BaseModel):
    """行业对比"""
    industry_name: str = Field(description="行业名称")
    industry_code: Optional[str] = Field(default=None, description="行业代码")
    
    companies: List[CompanyComparison] = Field(description="公司对比数据")
    
    # 行业平均值
    avg_pe: Optional[float] = Field(default=None, description="行业平均市盈率")
    avg_pb: Optional[float] = Field(default=None, description="行业平均市净率")
    avg_roe: Optional[float] = Field(default=None, description="行业平均ROE")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="数据时间")


# ==================== 智能预警模型 ====================

class Alert(BaseModel):
    """预警信息"""
    alert_id: str = Field(description="预警ID")
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    
    # 预警信息
    alert_type: str = Field(description="预警类型")
    alert_level: AlertLevel = Field(description="预警级别")
    title: str = Field(description="预警标题")
    message: str = Field(description="预警详情")
    
    # 触发数据
    trigger_value: Optional[float] = Field(default=None, description="触发值")
    threshold_value: Optional[float] = Field(default=None, description="阈值")
    
    # 时间信息
    trigger_time: datetime = Field(default_factory=datetime.now, description="触发时间")
    
    # 建议
    suggestion: Optional[str] = Field(default=None, description="处理建议")


class AlertList(BaseModel):
    """预警列表"""
    total_count: int = Field(description="预警总数")
    alerts: List[Alert] = Field(description="预警列表")
    stock_code: Optional[str] = Field(default=None, description="股票代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="查询时间")


# ==================== 综合分析模型 ====================

class ComprehensiveAnalysis(BaseModel):
    """综合分析结果"""
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    
    # 实时数据
    realtime_quote: Optional[RealtimeQuote] = Field(default=None, description="实时行情")
    
    # 最新动态
    latest_news: Optional[List[NewsItem]] = Field(default=None, description="最新新闻")
    latest_announcements: Optional[List[Announcement]] = Field(default=None, description="最新公告")
    
    # 行业对比
    industry_position: Optional[Dict[str, Any]] = Field(default=None, description="行业地位")
    
    # 预警信息
    active_alerts: Optional[List[Alert]] = Field(default=None, description="活跃预警")
    
    # 情绪分析
    market_sentiment: Optional[str] = Field(default=None, description="市场情绪")
    sentiment_score: Optional[float] = Field(default=None, description="情绪分数")
    
    # 综合评分
    overall_score: Optional[float] = Field(default=None, description="综合评分(0-100)")
    risk_level: Optional[str] = Field(default=None, description="风险等级")
    
    # 投资建议
    investment_suggestion: Optional[str] = Field(default=None, description="投资建议")
    
    # 分析时间
    analysis_time: datetime = Field(default_factory=datetime.now, description="分析时间")


# ==================== API 响应模型 ====================

class RealtimeDataResponse(BaseModel):
    """实时数据响应"""
    status: str = Field(description="状态: success/error")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    data_source: Optional[str] = Field(default=None, description="数据来源")


class DataSourceStatus(BaseModel):
    """数据源状态"""
    source_name: str = Field(description="数据源名称")
    is_available: bool = Field(description="是否可用")
    last_update: Optional[datetime] = Field(default=None, description="最后更新时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    api_quota_remaining: Optional[int] = Field(default=None, description="剩余API配额")

