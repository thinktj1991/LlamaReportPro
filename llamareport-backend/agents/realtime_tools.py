"""
实时数据工具
基于 LlamaIndex FunctionTool 模式创建实时金融数据工具
参考文档: llamaindex_intelligent_agent_system/03_Agent_Tools.md
"""

from typing import Annotated, Optional, List, Dict, Any
from llama_index.core.tools import FunctionTool
from datetime import datetime
import logging
import os

from data_sources.tushare_source import TushareDataSource
from data_sources.sina_source import SinaFinanceDataSource
from data_sources.news_source import NewsDataSource
from models.realtime_models import (
    RealtimeQuote, 
    NewsItem, 
    Announcement,
    Alert,
    AlertLevel
)

logger = logging.getLogger(__name__)


# ==================== 初始化数据源 ====================

# 全局数据源实例（延迟初始化）
_tushare_source: Optional[TushareDataSource] = None
_sina_source: Optional[SinaFinanceDataSource] = None
_news_source: Optional[NewsDataSource] = None


def get_tushare_source() -> TushareDataSource:
    """获取 Tushare 数据源实例"""
    global _tushare_source
    if _tushare_source is None:
        token = os.getenv("TUSHARE_API_TOKEN")
        _tushare_source = TushareDataSource(api_token=token)
        _tushare_source.initialize()
    return _tushare_source


def get_sina_source() -> SinaFinanceDataSource:
    """获取新浪财经数据源实例"""
    global _sina_source
    if _sina_source is None:
        _sina_source = SinaFinanceDataSource()
        _sina_source.initialize()
    return _sina_source


def get_news_source() -> NewsDataSource:
    """获取新闻数据源实例"""
    global _news_source
    if _news_source is None:
        _news_source = NewsDataSource()
        _news_source.initialize()
    return _news_source


# ==================== 工具函数定义 ====================

def get_realtime_stock_price(
    stock_code: Annotated[str, "股票代码，如 '600000.SH' 或 '000001.SZ'"]
) -> str:
    """
    获取股票实时价格和基本信息
    
    这个工具用于获取股票的实时行情数据，包括：
    - 最新价格、涨跌幅、成交量
    - 开盘价、最高价、最低价
    - 市盈率、市净率、市值等估值指标
    
    Args:
        stock_code: 股票代码（支持上海、深圳、北京市场）
        
    Returns:
        格式化的实时行情信息
    """
    try:
        logger.info(f"获取实时股价: {stock_code}")
        
        # 优先使用新浪财经（免费且实时）
        sina_source = get_sina_source()
        quote_data = sina_source.get_realtime_quote(stock_code)
        
        # 如果新浪失败，尝试 Tushare
        if not quote_data:
            logger.info("新浪财经数据获取失败，尝试 Tushare")
            tushare_source = get_tushare_source()
            quote_data = tushare_source.get_realtime_quote(stock_code)
        
        if not quote_data:
            return f"❌ 无法获取 {stock_code} 的实时数据，请检查股票代码是否正确。"
        
        # 格式化输出
        result = f"""
📊 **{quote_data['stock_name']} ({quote_data['stock_code']})** 实时行情

💰 **价格信息**
- 最新价: {quote_data['current_price']:.2f} 元
- 涨跌额: {quote_data.get('change_amount', 0):.2f} 元
- 涨跌幅: {quote_data.get('change_percent', 0):.2f}%
- 今开: {quote_data.get('open_price', 0):.2f} 元
- 昨收: {quote_data.get('close_price', 0):.2f} 元
- 最高: {quote_data.get('high_price', 0):.2f} 元
- 最低: {quote_data.get('low_price', 0):.2f} 元

📈 **成交信息**
- 成交量: {quote_data.get('volume', 0):,.0f} 手
- 成交额: {quote_data.get('amount', 0)/100000000:.2f} 亿元
- 换手率: {quote_data.get('turnover_rate', 0):.2f}%

💎 **估值信息**
- 市盈率: {quote_data.get('pe_ratio', 'N/A')}
- 市净率: {quote_data.get('pb_ratio', 'N/A')}
- 总市值: {quote_data.get('total_market_cap', 0):.2f} 亿元
- 流通市值: {quote_data.get('circulating_market_cap', 0):.2f} 亿元

🕐 更新时间: {quote_data.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
📡 数据来源: {quote_data.get('data_source', 'Unknown')}
"""
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"获取实时股价失败: {e}")
        return f"❌ 获取实时数据时发生错误: {str(e)}"


def get_latest_financial_news(
    company_name: Annotated[str, "公司名称，如 '贵州茅台' 或 '中国平安'"],
    limit: Annotated[int, "返回新闻数量，默认 10 条"] = 10
) -> str:
    """
    获取公司最新财经新闻
    
    这个工具用于获取公司的最新新闻动态，包括：
    - 公司新闻、行业动态
    - 新闻标题、摘要、来源
    - 发布时间、情绪分析
    
    Args:
        company_name: 公司名称
        limit: 返回新闻数量（1-20）
        
    Returns:
        格式化的新闻列表
    """
    try:
        logger.info(f"获取最新新闻: {company_name}, 数量: {limit}")
        
        # 限制数量范围
        limit = max(1, min(limit, 20))
        
        news_source = get_news_source()
        news_list = news_source.get_company_news(company_name, limit)
        
        if not news_list:
            return f"📰 暂无 {company_name} 的最新新闻"
        
        # 格式化输出
        result = f"📰 **{company_name}** 最新新闻 (共 {len(news_list)} 条)\n\n"
        
        for i, news in enumerate(news_list, 1):
            publish_time = news.get('publish_time', datetime.now())
            time_str = publish_time.strftime('%Y-%m-%d %H:%M') if isinstance(publish_time, datetime) else str(publish_time)
            
            result += f"""
{i}. **{news.get('title', '无标题')}**
   - 来源: {news.get('source', '未知')}
   - 时间: {time_str}
   - 摘要: {news.get('summary', '暂无摘要')[:100]}...
   - 分类: {news.get('category', '未分类')}
"""
        
        result += f"\n🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        return f"❌ 获取新闻时发生错误: {str(e)}"


def get_company_announcements(
    stock_code: Annotated[str, "股票代码，如 '600000.SH'"],
    limit: Annotated[int, "返回公告数量，默认 10 条"] = 10
) -> str:
    """
    获取公司最新公告
    
    这个工具用于获取公司的官方公告，包括：
    - 定期报告、业绩预告
    - 重大事项、股东大会
    - 其他重要公告
    
    Args:
        stock_code: 股票代码
        limit: 返回公告数量（1-20）
        
    Returns:
        格式化的公告列表
    """
    try:
        logger.info(f"获取公司公告: {stock_code}, 数量: {limit}")
        
        # 限制数量范围
        limit = max(1, min(limit, 20))
        
        # 优先使用 Tushare
        tushare_source = get_tushare_source()
        announcements = tushare_source.get_announcements(stock_code, limit)
        
        # 如果 Tushare 失败，尝试新闻源
        if not announcements:
            logger.info("Tushare 公告获取失败，尝试其他数据源")
            news_source = get_news_source()
            announcements = news_source.get_announcements(stock_code, limit)
        
        if not announcements:
            return f"📢 暂无 {stock_code} 的最新公告"
        
        # 格式化输出
        result = f"📢 **{stock_code}** 最新公告 (共 {len(announcements)} 条)\n\n"
        
        for i, ann in enumerate(announcements, 1):
            publish_date = ann.get('publish_date', datetime.now())
            date_str = publish_date.strftime('%Y-%m-%d') if isinstance(publish_date, datetime) else str(publish_date)
            
            important_mark = "⭐ " if ann.get('is_important', False) else ""
            
            result += f"""
{i}. {important_mark}**{ann.get('title', '无标题')}**
   - 类型: {ann.get('announcement_type', '未知')}
   - 日期: {date_str}
   - 公司: {ann.get('stock_name', '')}
"""
            
            if ann.get('pdf_url'):
                result += f"   - 链接: {ann['pdf_url']}\n"
        
        result += f"\n🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"获取公告失败: {e}")
        return f"❌ 获取公告时发生错误: {str(e)}"


def check_stock_alerts(
    stock_code: Annotated[str, "股票代码，如 '600000.SH'"]
) -> str:
    """
    检查股票异常预警
    
    这个工具用于智能检测股票的异常情况，包括：
    - 价格异常（大幅波动）
    - 成交量异常（放量或缩量）
    - 新闻预警（重大负面新闻）
    
    Args:
        stock_code: 股票代码
        
    Returns:
        预警信息列表
    """
    try:
        logger.info(f"检查股票预警: {stock_code}")
        
        alerts = []
        
        # 1. 获取实时行情
        sina_source = get_sina_source()
        quote = sina_source.get_realtime_quote(stock_code)
        
        if not quote:
            return f"❌ 无法获取 {stock_code} 的行情数据，无法进行预警检查"
        
        # 2. 检查价格异常
        change_percent = quote.get('change_percent', 0)
        if abs(change_percent) >= 5:
            level = AlertLevel.CRITICAL if abs(change_percent) >= 7 else AlertLevel.WARNING
            alerts.append({
                "level": level,
                "type": "价格异常",
                "message": f"涨跌幅达到 {change_percent:.2f}%，超过正常波动范围",
                "suggestion": "建议密切关注，查看相关公告和新闻"
            })
        
        # 3. 检查换手率异常
        turnover_rate = quote.get('turnover_rate', 0)
        if turnover_rate >= 10:
            alerts.append({
                "level": AlertLevel.WARNING,
                "type": "换手率异常",
                "message": f"换手率达到 {turnover_rate:.2f}%，交易异常活跃",
                "suggestion": "可能存在资金大幅进出，注意风险"
            })
        
        # 4. 检查估值异常
        pe_ratio = quote.get('pe_ratio', 0)
        if pe_ratio and pe_ratio > 100:
            alerts.append({
                "level": AlertLevel.INFO,
                "type": "估值提示",
                "message": f"市盈率为 {pe_ratio:.2f}，估值较高",
                "suggestion": "高估值需谨慎，关注盈利增长是否匹配"
            })
        elif pe_ratio and pe_ratio < 0:
            alerts.append({
                "level": AlertLevel.WARNING,
                "type": "盈利预警",
                "message": "市盈率为负，公司处于亏损状态",
                "suggestion": "关注公司扭亏计划和经营改善情况"
            })
        
        # 格式化输出
        if not alerts:
            return f"✅ {quote['stock_name']} ({stock_code}) 当前无异常预警"
        
        result = f"⚠️ **{quote['stock_name']} ({stock_code})** 预警信息\n\n"
        result += f"📊 当前价格: {quote['current_price']:.2f} 元 ({change_percent:+.2f}%)\n\n"
        
        for i, alert in enumerate(alerts, 1):
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🚨"
            }
            emoji = level_emoji.get(alert['level'], "⚠️")
            
            result += f"""
{i}. {emoji} **{alert['type']}** ({alert['level'].value})
   - 详情: {alert['message']}
   - 建议: {alert['suggestion']}
"""
        
        result += f"\n🕐 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"预警检查失败: {e}")
        return f"❌ 预警检查时发生错误: {str(e)}"


def get_market_overview() -> str:
    """
    获取市场概览
    
    这个工具用于获取主要市场指数的实时情况，包括：
    - 上证指数、深证成指、创业板指
    - 当前点位、涨跌幅
    - 成交量、成交额
    
    Returns:
        市场概览信息
    """
    try:
        logger.info("获取市场概览")
        
        sina_source = get_sina_source()
        overview = sina_source.get_market_overview()
        
        if not overview:
            return "❌ 无法获取市场概览数据"
        
        result = "📈 **A股市场概览**\n\n"
        
        for index_name, data in overview.items():
            change_emoji = "📈" if data['change_percent'] >= 0 else "📉"
            
            result += f"""
{change_emoji} **{index_name}**
- 当前点位: {data['current_value']:.2f}
- 涨跌幅: {data['change_percent']:+.2f}% ({data['change_amount']:+.2f})
- 成交额: {data.get('amount', 0)/100000000:.2f} 亿元
"""
        
        result += f"\n🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        return f"❌ 获取市场概览时发生错误: {str(e)}"


# ==================== 创建 LlamaIndex 工具 ====================

def create_realtime_data_tools() -> List[FunctionTool]:
    """
    创建实时数据工具列表
    
    基于 LlamaIndex FunctionTool 模式
    参考: llamaindex_intelligent_agent_system/03_Agent_Tools.md
    
    Returns:
        工具列表
    """
    tools = [
        # 1. 实时股价工具
        FunctionTool.from_defaults(
            fn=get_realtime_stock_price,
            name="get_realtime_stock_price",
            description=(
                "获取股票实时价格和基本信息。"
                "包括最新价、涨跌幅、成交量、市盈率、市净率等。"
                "适用于查询当前股价、实时行情等问题。"
            )
        ),
        
        # 2. 最新新闻工具
        FunctionTool.from_defaults(
            fn=get_latest_financial_news,
            name="get_latest_financial_news",
            description=(
                "获取公司最新财经新闻。"
                "包括新闻标题、摘要、来源、发布时间等。"
                "适用于查询最新动态、新闻资讯等问题。"
            )
        ),
        
        # 3. 公司公告工具
        FunctionTool.from_defaults(
            fn=get_company_announcements,
            name="get_company_announcements",
            description=(
                "获取公司最新官方公告。"
                "包括定期报告、业绩预告、重大事项等。"
                "适用于查询公司公告、官方信息等问题。"
            )
        ),
        
        # 4. 智能预警工具
        FunctionTool.from_defaults(
            fn=check_stock_alerts,
            name="check_stock_alerts",
            description=(
                "智能检测股票异常情况。"
                "包括价格异常、成交量异常、估值预警等。"
                "适用于风险检查、异常监控等问题。"
            )
        ),
        
        # 5. 市场概览工具
        FunctionTool.from_defaults(
            fn=get_market_overview,
            name="get_market_overview",
            description=(
                "获取A股市场概览。"
                "包括主要指数（上证、深证、创业板）的实时情况。"
                "适用于查询大盘走势、市场整体情况等问题。"
            )
        ),
    ]
    
    logger.info(f"✅ 创建了 {len(tools)} 个实时数据工具")
    
    return tools


# ==================== 工具测试函数 ====================

def test_realtime_tools():
    """
    测试实时数据工具
    
    用于验证工具功能是否正常
    """
    print("=" * 60)
    print("测试实时数据工具")
    print("=" * 60)
    
    # 测试 1: 实时股价
    print("\n1. 测试实时股价工具:")
    print(get_realtime_stock_price("600000.SH"))
    
    # 测试 2: 最新新闻
    print("\n2. 测试最新新闻工具:")
    print(get_latest_financial_news("贵州茅台", 5))
    
    # 测试 3: 公司公告
    print("\n3. 测试公司公告工具:")
    print(get_company_announcements("600000.SH", 5))
    
    # 测试 4: 智能预警
    print("\n4. 测试智能预警工具:")
    print(check_stock_alerts("600000.SH"))
    
    # 测试 5: 市场概览
    print("\n5. 测试市场概览工具:")
    print(get_market_overview())
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 运行测试
    test_realtime_tools()

