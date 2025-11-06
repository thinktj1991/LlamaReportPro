"""
实时数据页面
提供实时股价、新闻、公告、预警等查询功能
"""

import streamlit as st
import requests
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Backend API 地址
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def show_realtime_page():
    """显示实时数据页面"""
    
    # 页面标题
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6f00 0%, #ff9800 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>📈 实时数据查询</h2>
        <p>获取股票实时行情、最新新闻、公司公告、智能预警等实时信息</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>✨ 功能:</strong> 实时股价 • 财经新闻 • 公司公告 • 智能预警 • 市场概览
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 检查 Backend 连接
    backend_status = check_backend_connection()
    
    if not backend_status['connected']:
        st.error(f"""
        ⚠️ 无法连接到 Backend 服务
        
        请确保 Backend 服务正在运行:
        ```bash
        cd llamareport-backend
        python main.py
        ```
        
        Backend 地址: {BACKEND_URL}
        错误信息: {backend_status['error']}
        """)
        return
    
    # 显示 Backend 状态
    with st.expander("🔍 查看 Backend 状态", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("服务状态", "✅ 在线")
        with col2:
            st.metric("数据源", backend_status.get('data_sources', 'N/A'))
        with col3:
            st.metric("API 版本", backend_status.get('version', '1.0.0'))
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 实时股价", 
        "📰 财经新闻", 
        "📢 公司公告", 
        "⚠️ 智能预警", 
        "📊 市场概览"
    ])
    
    with tab1:
        show_realtime_quote_tab()
    
    with tab2:
        show_latest_news_tab()
    
    with tab3:
        show_announcements_tab()
    
    with tab4:
        show_alerts_tab()
    
    with tab5:
        show_market_overview_tab()


def check_backend_connection():
    """检查 Backend 连接状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/realtime/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # 统计可用的数据源
            available_sources = 0
            if data.get('data_sources'):
                for source_name, source_info in data['data_sources'].items():
                    if source_info.get('is_initialized'):
                        available_sources += 1
            
            return {
                'connected': True,
                'status': data.get('status', 'unknown'),
                'data_sources': f"{available_sources}/3 可用",
                'version': '1.1.0'
            }
        else:
            return {
                'connected': False,
                'error': f'HTTP {response.status_code}'
            }
    except requests.exceptions.ConnectionError:
        return {
            'connected': False,
            'error': '连接被拒绝，Backend 可能未启动'
        }
    except requests.exceptions.Timeout:
        return {
            'connected': False,
            'error': '连接超时'
        }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e)
        }


def show_realtime_quote_tab():
    """实时股价查询标签页"""
    st.subheader("💰 实时股价查询")
    
    # 快捷选择
    st.markdown("#### ⚡ 快捷选择")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    quick_stocks = [
        ("贵州茅台", "600519.SH"),
        ("五粮液", "000858.SZ"),
        ("中国平安", "601318.SH"),
        ("招商银行", "600036.SH"),
        ("万科A", "000002.SZ")
    ]
    
    selected_stock = None
    with col1:
        if st.button("🍷 贵州茅台", use_container_width=True):
            selected_stock = "600519.SH"
    with col2:
        if st.button("🍶 五粮液", use_container_width=True):
            selected_stock = "000858.SZ"
    with col3:
        if st.button("🏦 中国平安", use_container_width=True):
            selected_stock = "601318.SH"
    with col4:
        if st.button("🏧 招商银行", use_container_width=True):
            selected_stock = "600036.SH"
    with col5:
        if st.button("🏘️ 万科A", use_container_width=True):
            selected_stock = "000002.SZ"
    
    st.markdown("---")
    
    # 股票代码输入
    st.markdown("#### 📝 输入股票代码")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_code = st.text_input(
            "股票代码",
            value=selected_stock if selected_stock else "",
            placeholder="例如: 600519.SH (贵州茅台) 或 000001.SZ (平安银行)",
            help="上海市场: .SH, 深圳市场: .SZ, 北京市场: .BJ"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 对齐按钮
        query_button = st.button("🔍 查询股价", type="primary", use_container_width=True)
    
    # 查询逻辑
    if query_button or selected_stock:
        if not stock_code:
            st.warning("请输入股票代码")
            return
        
        with st.spinner(f"正在查询 {stock_code} 的实时行情..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/realtime/quote/{stock_code}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        # 显示结果
                        st.success("✅ 查询成功")
                        
                        # 使用 markdown 显示格式化的结果
                        st.markdown(result['data'])
                        
                        # 显示数据时间
                        st.caption(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.error(f"查询失败: {result.get('message', '未知错误')}")
                else:
                    st.error(f"API 请求失败: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，请检查网络连接或稍后重试")
            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接到 Backend 服务，请确保服务已启动")
            except Exception as e:
                st.error(f"❌ 查询失败: {str(e)}")


def show_latest_news_tab():
    """最新新闻查询标签页"""
    st.subheader("📰 财经新闻查询")
    
    st.markdown("#### 📝 输入查询信息")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        company_name = st.text_input(
            "公司名称",
            placeholder="例如: 贵州茅台、中国平安、比亚迪",
            help="输入公司的中文名称"
        )
    
    with col2:
        news_limit = st.number_input(
            "新闻数量",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        query_button = st.button("🔍 查询新闻", type="primary", use_container_width=True)
    
    # 查询逻辑
    if query_button:
        if not company_name:
            st.warning("请输入公司名称")
            return
        
        with st.spinner(f"正在获取 {company_name} 的最新新闻..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/realtime/news",
                    json={
                        "company_name": company_name,
                        "limit": news_limit
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        st.success("✅ 查询成功")
                        st.markdown(result['data'])
                        st.caption(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.error(f"查询失败: {result.get('message', '未知错误')}")
                else:
                    st.error(f"API 请求失败: HTTP {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ 查询失败: {str(e)}")


def show_announcements_tab():
    """公司公告查询标签页"""
    st.subheader("📢 公司公告查询")
    
    st.markdown("#### 📝 输入查询信息")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="例如: 600519.SH (贵州茅台)",
            key="announcement_stock_code"
        )
    
    with col2:
        announcement_limit = st.number_input(
            "公告数量",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        query_button = st.button("🔍 查询公告", type="primary", use_container_width=True)
    
    # 查询逻辑
    if query_button:
        if not stock_code:
            st.warning("请输入股票代码")
            return
        
        with st.spinner(f"正在获取 {stock_code} 的公司公告..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/realtime/announcements",
                    json={
                        "stock_code": stock_code,
                        "limit": announcement_limit
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        st.success("✅ 查询成功")
                        st.markdown(result['data'])
                        st.caption(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.error(f"查询失败: {result.get('message', '未知错误')}")
                else:
                    st.error(f"API 请求失败: HTTP {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ 查询失败: {str(e)}")


def show_alerts_tab():
    """智能预警查询标签页"""
    st.subheader("⚠️ 智能预警检测")
    
    st.info("""
    💡 **功能说明**: 
    - 自动检测价格异常（涨跌幅 > 5%）
    - 成交量异常（换手率 > 10%）
    - 估值风险（PE < 0 或 > 100）
    """)
    
    st.markdown("#### 📝 输入股票代码")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="例如: 600519.SH (贵州茅台)",
            key="alert_stock_code"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        check_button = st.button("🔍 检查预警", type="primary", use_container_width=True)
    
    # 查询逻辑
    if check_button:
        if not stock_code:
            st.warning("请输入股票代码")
            return
        
        with st.spinner(f"正在检查 {stock_code} 的异常情况..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/realtime/alerts/{stock_code}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        data = result['data']
                        
                        # 判断是否有预警
                        if "无异常预警" in data:
                            st.success(data)
                        else:
                            st.warning("⚠️ 发现异常情况")
                            st.markdown(data)
                        
                        st.caption(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.error(f"检查失败: {result.get('message', '未知错误')}")
                else:
                    st.error(f"API 请求失败: HTTP {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ 检查失败: {str(e)}")


def show_market_overview_tab():
    """市场概览标签页"""
    st.subheader("📊 A股市场概览")
    
    st.info("""
    💡 **功能说明**: 
    - 查看主要指数实时情况
    - 上证指数、深证成指、创业板指
    - 实时点位、涨跌幅、成交额
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🔍 查询市场概览", type="primary", use_container_width=True):
            with st.spinner("正在获取市场概览..."):
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/realtime/market/overview",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result['status'] == 'success':
                            st.success("✅ 查询成功")
                            st.markdown(result['data'])
                            st.caption(f"⏰ 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            st.error(f"查询失败: {result.get('message', '未知错误')}")
                    else:
                        st.error(f"API 请求失败: HTTP {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ 查询失败: {str(e)}")


def show_comprehensive_analysis():
    """显示综合分析"""
    st.markdown("---")
    st.subheader("🎯 综合投资分析 (使用 Agent)")
    
    st.info("""
    💡 **Agent 综合分析**: 
    - 结合历史年报数据和实时数据
    - 自动调用多个工具进行分析
    - 给出投资建议和风险提示
    """)
    
    # 输入
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analysis_query = st.text_area(
            "请输入您的分析需求",
            placeholder="例如: 贵州茅台值得投资吗？\n或: 对比分析贵州茅台和五粮液",
            height=100
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🤖 开始分析", type="primary", use_container_width=True):
            if not analysis_query:
                st.warning("请输入分析需求")
                return
            
            with st.spinner("Agent 正在进行深度分析，这可能需要10-30秒..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/agent/query",
                        json={"question": analysis_query},
                        timeout=60  # Agent 分析可能需要更长时间
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result['status'] == 'success':
                            st.success("✅ 分析完成")
                            
                            # 显示分析结果
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; color: white; margin: 1rem 0;">
                                <h3>🤖 Agent 综合分析结果</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(result['answer'])
                            
                            # 显示使用的工具
                            if result.get('tool_calls'):
                                with st.expander(f"🔧 使用的工具 ({len(result['tool_calls'])} 个)", expanded=False):
                                    for i, tool_call in enumerate(result['tool_calls'], 1):
                                        st.write(f"{i}. **{tool_call['tool_name']}**")
                            
                            st.caption(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            st.error(f"分析失败: {result.get('error', '未知错误')}")
                    else:
                        st.error(f"API 请求失败: HTTP {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ 分析失败: {str(e)}")


def show_data_source_status():
    """显示数据源状态"""
    st.markdown("---")
    st.subheader("📡 数据源状态")
    
    try:
        response = requests.get(f"{BACKEND_URL}/realtime/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('data_sources'):
                col1, col2, col3 = st.columns(3)
                
                sources_list = list(data['data_sources'].items())
                
                for idx, (source_name, source_info) in enumerate(sources_list):
                    col = [col1, col2, col3][idx % 3]
                    
                    with col:
                        status = "✅ 正常" if source_info.get('is_initialized') else "❌ 不可用"
                        success_rate = source_info.get('success_rate', 0)
                        
                        st.metric(
                            label=source_name,
                            value=status,
                            delta=f"成功率: {success_rate:.1%}" if success_rate > 0 else None
                        )
        else:
            st.warning("无法获取数据源状态")
            
    except Exception as e:
        st.warning(f"无法连接到 Backend: {str(e)}")


# 在页面底部添加综合分析和数据源状态
def show_realtime_page():
    """显示实时数据页面（完整版本）"""
    
    # 页面标题
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6f00 0%, #ff9800 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>📈 实时数据查询</h2>
        <p>获取股票实时行情、最新新闻、公司公告、智能预警等实时信息</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>✨ 功能:</strong> 实时股价 • 财经新闻 • 公司公告 • 智能预警 • 市场概览
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 检查 Backend 连接
    backend_status = check_backend_connection()
    
    if not backend_status['connected']:
        st.error(f"""
        ⚠️ **无法连接到 Backend 服务**
        
        请确保 Backend 服务正在运行:
        ```bash
        cd llamareport-backend
        python main.py
        ```
        
        Backend 地址: `{BACKEND_URL}`  
        错误信息: {backend_status['error']}
        """)
        
        # 提供配置说明
        with st.expander("📖 Backend 启动指南"):
            st.markdown("""
            ### 启动 Backend 服务
            
            1. **打开新终端**
            2. **进入 Backend 目录**:
               ```bash
               cd llamareport-backend
               ```
            3. **启动服务**:
               ```bash
               python main.py
               ```
            4. **等待启动完成**，看到:
               ```
               ✅ LlamaReport Backend 启动完成
               ✅ 加载了 5 个实时数据工具
               ```
            5. **刷新本页面**
            """)
        return
    
    # 显示 Backend 状态
    with st.expander("🔍 Backend 服务状态", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("服务状态", "✅ 在线")
        with col2:
            st.metric("可用数据源", backend_status.get('data_sources', 'N/A'))
        with col3:
            st.metric("API 版本", backend_status.get('version', '1.0.0'))
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 实时股价", 
        "📰 财经新闻", 
        "📢 公司公告", 
        "⚠️ 智能预警", 
        "📊 市场概览",
        "🤖 综合分析"
    ])
    
    with tab1:
        show_realtime_quote_tab()
    
    with tab2:
        show_latest_news_tab()
    
    with tab3:
        show_announcements_tab()
    
    with tab4:
        show_alerts_tab()
    
    with tab5:
        show_market_overview_tab()
    
    with tab6:
        show_comprehensive_analysis()
    
    # 页面底部 - 数据源状态
    st.markdown("<br><br>", unsafe_allow_html=True)
    show_data_source_status()


# 主函数（用于独立运行测试）
if __name__ == "__main__":
    show_realtime_page()

