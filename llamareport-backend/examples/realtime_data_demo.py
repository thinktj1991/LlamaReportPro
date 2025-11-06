"""
实时数据功能演示脚本
展示如何使用实时数据工具和 API
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def demo_1_direct_tool_usage():
    """演示 1: 直接使用工具函数"""
    print("\n" + "=" * 80)
    print("演示 1: 直接使用实时数据工具")
    print("=" * 80 + "\n")
    
    from agents.realtime_tools import (
        get_realtime_stock_price,
        get_latest_financial_news,
        get_company_announcements,
        check_stock_alerts,
        get_market_overview
    )
    
    # 1. 获取实时股价
    print("1️⃣ 获取实时股价")
    print("-" * 60)
    result = get_realtime_stock_price("600519.SH")
    print(result)
    
    # 2. 获取最新新闻
    print("\n\n2️⃣ 获取最新新闻")
    print("-" * 60)
    result = get_latest_financial_news("贵州茅台", 5)
    print(result)
    
    # 3. 获取公司公告
    print("\n\n3️⃣ 获取公司公告")
    print("-" * 60)
    result = get_company_announcements("600519.SH", 5)
    print(result)
    
    # 4. 智能预警检查
    print("\n\n4️⃣ 智能预警检查")
    print("-" * 60)
    result = check_stock_alerts("600519.SH")
    print(result)
    
    # 5. 市场概览
    print("\n\n5️⃣ 市场概览")
    print("-" * 60)
    result = get_market_overview()
    print(result)


async def demo_2_agent_usage():
    """演示 2: 通过 Agent 使用实时数据"""
    print("\n" + "=" * 80)
    print("演示 2: 通过 Agent 使用实时数据工具")
    print("=" * 80 + "\n")
    
    from core.rag_engine import RAGEngine
    from agents.report_agent import ReportAgent
    
    # 初始化
    rag = RAGEngine()
    
    # 尝试加载现有索引（如果有）
    if not rag.query_engine:
        rag.load_existing_index()
    
    # 创建 Agent（已包含实时数据工具）
    agent = ReportAgent(rag.query_engine)
    
    # 测试查询
    queries = [
        "帮我查一下贵州茅台现在的股价",
        "贵州茅台最近有什么新闻吗？",
        "检查一下中国平安有没有异常情况",
        "今天大盘走势怎么样？"
    ]
    
    for i, question in enumerate(queries, 1):
        print(f"\n{i}. 问题: {question}")
        print("-" * 60)
        
        try:
            result = await agent.query(question)
            
            if result['status'] == 'success':
                print(f"回答: {result['answer'][:500]}...")  # 截取前500字
                
                # 显示使用的工具
                if result.get('tool_calls'):
                    print(f"\n使用的工具: {len(result['tool_calls'])} 个")
                    for tool_call in result['tool_calls'][:3]:  # 显示前3个
                        print(f"  - {tool_call['tool_name']}")
            else:
                print(f"错误: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"查询失败: {e}")


async def demo_3_api_usage():
    """演示 3: 使用 REST API"""
    print("\n" + "=" * 80)
    print("演示 3: 使用 REST API 接口")
    print("=" * 80 + "\n")
    
    import httpx
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. 健康检查
        print("1️⃣ 健康检查")
        print("-" * 60)
        response = await client.get(f"{base_url}/realtime/health")
        print(f"状态: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 2. 获取实时行情
        print("\n\n2️⃣ 获取实时行情 API")
        print("-" * 60)
        response = await client.get(f"{base_url}/realtime/quote/600519.SH")
        print(f"状态: {response.status_code}")
        data = response.json()
        print(f"数据预览: {data['data'][:200]}...")
        
        # 3. 获取新闻
        print("\n\n3️⃣ 获取新闻 API")
        print("-" * 60)
        response = await client.post(
            f"{base_url}/realtime/news",
            json={"company_name": "贵州茅台", "limit": 3}
        )
        print(f"状态: {response.status_code}")
        data = response.json()
        print(f"数据预览: {data['data'][:200]}...")
        
        # 4. 市场概览
        print("\n\n4️⃣ 市场概览 API")
        print("-" * 60)
        response = await client.get(f"{base_url}/realtime/market/overview")
        print(f"状态: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 5. 统计信息
        print("\n\n5️⃣ 统计信息 API")
        print("-" * 60)
        response = await client.get(f"{base_url}/realtime/statistics")
        print(f"状态: {response.status_code}")
        stats = response.json()
        print(f"总请求数: {stats.get('total_requests', 0)}")


def demo_4_data_source_comparison():
    """演示 4: 数据源对比"""
    print("\n" + "=" * 80)
    print("演示 4: 数据源对比测试")
    print("=" * 80 + "\n")
    
    from data_sources.tushare_source import TushareDataSource
    from data_sources.sina_source import SinaFinanceDataSource
    import time
    
    stock_code = "600000.SH"
    
    # 测试新浪财经
    print("1️⃣ 测试新浪财经")
    print("-" * 60)
    sina = SinaFinanceDataSource()
    sina.initialize()
    
    start_time = time.time()
    sina_quote = sina.get_realtime_quote(stock_code)
    sina_time = time.time() - start_time
    
    if sina_quote:
        print(f"✅ 成功获取数据")
        print(f"   股票: {sina_quote['stock_name']}")
        print(f"   价格: {sina_quote['current_price']} 元")
        print(f"   耗时: {sina_time:.3f} 秒")
    else:
        print(f"❌ 获取失败")
    
    print(f"\n统计: {sina.get_statistics()}")
    
    # 测试 Tushare
    print("\n\n2️⃣ 测试 Tushare")
    print("-" * 60)
    
    token = os.getenv("TUSHARE_API_TOKEN")
    if not token:
        print("⚠️ 未配置 TUSHARE_API_TOKEN，跳过测试")
    else:
        tushare = TushareDataSource(api_token=token)
        tushare.initialize()
        
        start_time = time.time()
        tushare_quote = tushare.get_realtime_quote(stock_code)
        tushare_time = time.time() - start_time
        
        if tushare_quote:
            print(f"✅ 成功获取数据")
            print(f"   股票: {tushare_quote['stock_name']}")
            print(f"   价格: {tushare_quote['current_price']} 元")
            print(f"   耗时: {tushare_time:.3f} 秒")
        else:
            print(f"❌ 获取失败")
        
        print(f"\n统计: {tushare.get_statistics()}")
    
    # 对比总结
    print("\n\n📊 数据源对比总结")
    print("-" * 60)
    print(f"新浪财经: 响应时间 {sina_time:.3f}s, 成功率 {sina.get_statistics()['success_rate']}")
    if token and tushare_quote:
        print(f"Tushare:   响应时间 {tushare_time:.3f}s, 成功率 {tushare.get_statistics()['success_rate']}")


def main():
    """主函数"""
    print("\n")
    print("🚀" * 40)
    print("LlamaReport Backend - 实时数据功能演示")
    print("🚀" * 40)
    
    # 选择演示
    demos = {
        "1": ("直接使用工具", demo_1_direct_tool_usage, False),
        "2": ("通过 Agent 使用", demo_2_agent_usage, True),
        "3": ("使用 REST API", demo_3_api_usage, True),
        "4": ("数据源对比", demo_4_data_source_comparison, False),
        "all": ("运行所有演示", None, True)
    }
    
    print("\n可用的演示:")
    for key, (name, _, _) in demos.items():
        print(f"  {key}. {name}")
    
    choice = input("\n请选择演示 (1-4 或 all, 直接回车运行演示1): ").strip() or "1"
    
    if choice == "all":
        # 运行所有演示
        demo_1_direct_tool_usage()
        asyncio.run(demo_2_agent_usage())
        print("\n⚠️ 演示3需要服务器运行，请先启动: python main.py")
        demo_4_data_source_comparison()
    elif choice in demos:
        name, func, is_async = demos[choice]
        print(f"\n运行演示: {name}")
        if is_async:
            if choice == "3":
                print("\n⚠️ 此演示需要服务器运行")
                print("请先在另一个终端运行: python main.py")
                print("然后按回车继续...")
                input()
            asyncio.run(func())
        else:
            func()
    else:
        print("无效选择")
    
    print("\n")
    print("=" * 80)
    print("演示完成！")
    print("=" * 80)
    print("\n提示:")
    print("- 查看完整 API 文档: http://localhost:8000/docs")
    print("- 查看使用指南: REALTIME_DATA_GUIDE.md")
    print("- 查看配置说明: README.md")
    print()


if __name__ == "__main__":
    main()

