"""
年报分析报告的 Pydantic 数据模型
基于模板结构定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


# ==================== 财务指标模型 ====================

class FinancialIndicator(BaseModel):
    """单个财务指标"""
    name: str = Field(description="指标名称,如'营业收入'、'净利润'")
    value: str = Field(description="指标值,如'6.73亿元'")
    change_rate: Optional[str] = Field(default=None, description="同比变化率,如'14.53%'")
    change_direction: Optional[str] = Field(default=None, description="变化方向,如'增长'、'下降'")


class FinancialMetrics(BaseModel):
    """财务指标集合"""
    # 利润表指标
    revenue: FinancialIndicator = Field(description="营业收入")
    gross_margin: FinancialIndicator = Field(description="毛利率")
    operating_profit: FinancialIndicator = Field(description="营业利润")
    net_profit: FinancialIndicator = Field(description="净利润")
    non_recurring_net_profit: Optional[FinancialIndicator] = Field(default=None, description="扣非净利润")
    parent_net_profit: FinancialIndicator = Field(description="归母净利润")
    eps: FinancialIndicator = Field(description="摊薄每股收益")
    
    # 现金流量指标
    operating_cash_flow: Optional[FinancialIndicator] = Field(default=None, description="经营活动现金流量净额")
    investing_cash_flow: Optional[FinancialIndicator] = Field(default=None, description="投资活动现金流量净额")
    financing_cash_flow: Optional[FinancialIndicator] = Field(default=None, description="筹资活动现金流量净额")
    
    # 资产负债指标
    total_assets: Optional[FinancialIndicator] = Field(default=None, description="总资产")
    total_liabilities: Optional[FinancialIndicator] = Field(default=None, description="总负债")
    asset_liability_ratio: Optional[FinancialIndicator] = Field(default=None, description="资产负债率")


class SegmentData(BaseModel):
    """分部数据"""
    segment_name: str = Field(description="分部名称,如'房地产类'、'园区产业类'")
    revenue: str = Field(description="收入金额")
    change_rate: Optional[str] = Field(default=None, description="同比变化率")
    description: Optional[str] = Field(default=None, description="补充说明")


class BusinessData(BaseModel):
    """业务数据"""
    item_name: str = Field(description="业务项目名称")
    metrics: Dict[str, str] = Field(description="业务指标,如可出租面积、销售金额等")


# ==================== 财务点评模型 ====================

class FinancialCharts(BaseModel):
    """财务图表描述"""
    charts: List[str] = Field(description="图表描述列表,如'收入和归母净利润增速'、'利润率'等")


class PerformanceSummary(BaseModel):
    """业绩速览"""
    company_name: str = Field(description="公司名称")
    report_year: str = Field(description="报告年份")
    
    # 年初累计数据
    financial_metrics: FinancialMetrics = Field(description="财务指标")
    
    # 分部数据
    segment_data_by_product: Optional[List[SegmentData]] = Field(default=None, description="按产品分部数据")
    segment_data_by_region: Optional[List[SegmentData]] = Field(default=None, description="按地区分部数据")
    
    # 业务数据
    business_data: Optional[List[BusinessData]] = Field(default=None, description="业务数据列表")
    
    # 总结
    summary: str = Field(description="业绩速览总结,分析整体表现")


class PerformanceComparison(BaseModel):
    """业绩和预期的比较"""
    comparison_table: List[Dict[str, str]] = Field(
        description="对比表格,包含项目、实际值、预告值、比较结果"
    )
    summary: str = Field(description="对比总结")


class MetricAttribution(BaseModel):
    """单个指标变动归因"""
    metric_name: str = Field(description="指标名称")
    change_description: str = Field(description="变动情况描述")
    change_reasons: str = Field(description="变动原因分析")


class FinancialReview(BaseModel):
    """财务点评(第一部分)"""
    charts: FinancialCharts = Field(description="财务图表")
    performance_summary: PerformanceSummary = Field(description="业绩速览")
    performance_comparison: PerformanceComparison = Field(description="业绩和预期的比较")
    metrics_attribution: List[MetricAttribution] = Field(description="财务指标变动归因列表")


# ==================== 业绩指引模型 ====================

class BusinessGuidance(BaseModel):
    """业绩指引(第二部分)"""
    guidance_period: str = Field(description="业绩预告期间")
    expected_performance: str = Field(description="预计的经营业绩描述")
    
    # 整体业绩指引
    parent_net_profit_range: Optional[str] = Field(default=None, description="归母净利润范围")
    parent_net_profit_growth_range: Optional[str] = Field(default=None, description="归母净利润增长率范围")
    non_recurring_profit_range: Optional[str] = Field(default=None, description="扣非净利润范围")
    eps_range: Optional[str] = Field(default=None, description="基本每股收益范围")
    revenue_range: Optional[str] = Field(default=None, description="营业收入范围")
    
    # 各业务的具体指引
    business_specific_guidance: Optional[List[str]] = Field(default=None, description="各业务具体指引")
    
    # 风险提示
    risk_warnings: Optional[List[str]] = Field(default=None, description="风险提示及其他相关说明")


# ==================== 业务亮点模型 ====================

class BusinessHighlight(BaseModel):
    """单个业务亮点"""
    business_type: str = Field(description="业务类型,如'智慧交通业务'、'未来社区业务'")
    highlights: str = Field(description="业务亮点详细描述")
    achievements: Optional[List[str]] = Field(default=None, description="主要成就列表")


class BusinessHighlights(BaseModel):
    """业务亮点(第三部分)"""
    highlights: List[BusinessHighlight] = Field(description="各业务亮点列表")
    overall_summary: str = Field(description="业务亮点总结")


# ==================== 盈利预测和估值模型 ====================

class ConsensusForecas(BaseModel):
    """一致预测"""
    market_rating: str = Field(description="市场整体投资评级,如'持有'、'买入'")
    target_price: Optional[str] = Field(default=None, description="一致目标价")
    upside_potential: Optional[str] = Field(default=None, description="上涨空间")
    
    # 关键财务指标预测
    revenue_forecast: Dict[str, str] = Field(description="营业总收入预测,按年份")
    revenue_growth_forecast: Dict[str, str] = Field(description="营业收入增长率预测,按年份")
    parent_profit_forecast: Dict[str, str] = Field(description="归母净利润预测,按年份")
    eps_forecast: Dict[str, str] = Field(description="EPS预测,按年份")
    roe_forecast: Dict[str, str] = Field(description="ROE预测,按年份")
    roa_forecast: Dict[str, str] = Field(description="ROA预测,按年份")


class ValuationAnalysis(BaseModel):
    """估值分析"""
    valuation_method: str = Field(description="估值方法,如'PE TTM'")
    current_valuation: Optional[str] = Field(default=None, description="当前估值")
    valuation_comparison: Optional[str] = Field(default=None, description="估值对比分析")


class ProfitForecastAndValuation(BaseModel):
    """盈利预测和估值(第四部分)"""
    consensus_forecast: ConsensusForecas = Field(description="一致预测")
    consensus_changes: Optional[str] = Field(default=None, description="一致预期变化描述")
    institutional_forecasts: Optional[str] = Field(default=None, description="具体机构预测描述")
    valuation_analysis: ValuationAnalysis = Field(description="估值分析")


# ==================== 完整报告模型 ====================

class AnnualReportAnalysis(BaseModel):
    """完整的年报分析报告"""
    # 基本信息
    company_name: str = Field(description="公司名称")
    report_year: str = Field(description="报告年份")
    generation_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="报告生成日期"
    )
    
    # 五大部分
    financial_review: FinancialReview = Field(description="一、财务点评")
    business_guidance: BusinessGuidance = Field(description="二、业绩指引")
    business_highlights: BusinessHighlights = Field(description="三、业务亮点")
    profit_forecast_and_valuation: ProfitForecastAndValuation = Field(description="四、盈利预测和估值")
    
    # 总结
    overall_summary: str = Field(description="五、总结 - 综合所有部分的总结")
    
    # 参考来源
    references: Optional[List[str]] = Field(default=None, description="参考来源列表")


# ==================== 辅助模型 ====================

class ReportGenerationStatus(BaseModel):
    """报告生成状态"""
    status: str = Field(description="状态: pending, processing, completed, failed")
    progress: int = Field(description="进度百分比 0-100")
    current_step: str = Field(description="当前步骤描述")
    sections_completed: List[str] = Field(default_factory=list, description="已完成的章节")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class ReportSection(BaseModel):
    """单个报告章节"""
    section_name: str = Field(description="章节名称")
    section_content: str = Field(description="章节内容")
    generation_time: float = Field(description="生成耗时(秒)")
    tokens_used: Optional[int] = Field(default=None, description="使用的token数")

