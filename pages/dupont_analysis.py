"""
杜邦分析页面
提供交互式的杜邦分析功能
"""

import streamlit as st
import sys
from pathlib import Path
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="杜邦分析 - LlamaReportPro",
    page_icon="📊",
    layout="wide"
)

st.title("📊 杜邦分析")
st.markdown("---")

# 侧边栏说明
with st.sidebar:
    st.header("💡 关于杜邦分析")
    st.markdown("""
    **杜邦分析**是一种经典的财务分析方法，将净资产收益率(ROE)分解为三个关键驱动因素：
    
    1. **营业净利润率** - 盈利能力
    2. **资产周转率** - 运营效率
    3. **权益乘数** - 财务杠杆
    
    通过层层分解，帮助您深入理解公司盈利能力的来源。
    """)
    
    st.markdown("---")
    st.markdown("### 📖 使用指南")
    st.markdown("""
    1. 选择数据输入方式
    2. 输入公司信息和财务数据
    3. 点击"生成杜邦分析"
    4. 查看分析结果和可视化图表
    """)

# 主内容区域
tab1, tab2, tab3 = st.tabs(["📝 数据输入", "📊 分析结果", "📈 可视化"])

with tab1:
    st.header("数据输入")
    
    # 选择输入方式
    input_method = st.radio(
        "选择数据输入方式",
        ["手动输入", "从已上传文档提取", "使用示例数据"],
        horizontal=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("公司名称", value="示例科技股份有限公司")
        report_year = st.text_input("报告年份", value="2023")
    
    with col2:
        report_period = st.text_input("报告期间", value="2023年度")
    
    st.markdown("---")
    
    if input_method == "手动输入":
        st.subheader("财务数据输入")
        st.markdown("*请输入以下财务指标（单位：元）*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**利润表数据**")
            net_income = st.number_input(
                "净利润",
                value=1000000000.0,
                step=1000000.0,
                format="%.2f",
                help="归属于母公司所有者的净利润"
            )
            revenue = st.number_input(
                "营业收入",
                value=5000000000.0,
                step=1000000.0,
                format="%.2f",
                help="营业总收入"
            )
            operating_profit = st.number_input(
                "营业利润（可选）",
                value=1200000000.0,
                step=1000000.0,
                format="%.2f"
            )
        
        with col2:
            st.markdown("**资产负债表数据**")
            total_assets = st.number_input(
                "总资产",
                value=10000000000.0,
                step=1000000.0,
                format="%.2f"
            )
            shareholders_equity = st.number_input(
                "股东权益",
                value=6000000000.0,
                step=1000000.0,
                format="%.2f",
                help="归属于母公司所有者权益"
            )
            total_liabilities = st.number_input(
                "总负债（可选）",
                value=4000000000.0,
                step=1000000.0,
                format="%.2f"
            )
        
        with col3:
            st.markdown("**资产明细**")
            current_assets = st.number_input(
                "流动资产",
                value=4000000000.0,
                step=1000000.0,
                format="%.2f"
            )
            non_current_assets = st.number_input(
                "非流动资产",
                value=6000000000.0,
                step=1000000.0,
                format="%.2f"
            )
        
        # 构建财务数据字典
        financial_data = {
            '净利润': net_income,
            '营业收入': revenue,
            '总资产': total_assets,
            '股东权益': shareholders_equity,
            '流动资产': current_assets,
            '非流动资产': non_current_assets,
        }
        
        if operating_profit > 0:
            financial_data['营业利润'] = operating_profit
        if total_liabilities > 0:
            financial_data['总负债'] = total_liabilities
    
    elif input_method == "从已上传文档提取":
        st.info("📄 此功能将从已上传的PDF文档中自动提取财务数据")
        
        # 检查session_state中是否有已上传的文档
        if 'uploaded_documents' in st.session_state and st.session_state.uploaded_documents:
            doc_names = [doc['filename'] for doc in st.session_state.uploaded_documents]
            selected_doc = st.selectbox("选择文档", doc_names)
            
            if st.button("🔍 提取财务数据", type="primary"):
                with st.spinner("正在提取财务数据..."):
                    try:
                        # 这里调用提取函数
                        from llamareport_backend.agents.dupont_tools import extract_financial_data_for_dupont
                        
                        # 获取query_engine
                        if 'query_engine' in st.session_state:
                            financial_data = extract_financial_data_for_dupont(
                                company_name, report_year, st.session_state.query_engine
                            )
                            st.success("✅ 财务数据提取成功！")
                            st.json(financial_data)
                        else:
                            st.error("❌ 请先上传文档并建立索引")
                            financial_data = None
                    except Exception as e:
                        st.error(f"❌ 提取失败: {str(e)}")
                        financial_data = None
        else:
            st.warning("⚠️ 请先在'文档上传'页面上传PDF文档")
            financial_data = None
    
    else:  # 使用示例数据
        st.info("📊 使用预设的示例数据进行演示")
        financial_data = {
            '净利润': 1000000000,  # 10亿
            '营业收入': 5000000000,  # 50亿
            '总资产': 10000000000,  # 100亿
            '股东权益': 6000000000,  # 60亿
            '流动资产': 4000000000,  # 40亿
            '非流动资产': 6000000000,  # 60亿
            '营业利润': 1200000000,  # 12亿
            '总负债': 4000000000,  # 40亿
        }
        
        st.json(financial_data)
    
    st.markdown("---")
    
    # 生成分析按钮
    if st.button("🚀 生成杜邦分析", type="primary", use_container_width=True):
        if financial_data:
            with st.spinner("正在生成杜邦分析..."):
                try:
                    from utils.financial_calculator import DupontAnalyzer
                    
                    # 创建分析器
                    analyzer = DupontAnalyzer()
                    
                    # 执行分析
                    dupont_result = analyzer.calculate_dupont_analysis(
                        financial_data=financial_data,
                        company_name=company_name,
                        report_year=report_year,
                        report_period=report_period
                    )
                    
                    # 保存到session_state
                    st.session_state.dupont_result = dupont_result
                    
                    st.success("✅ 杜邦分析生成成功！请切换到'分析结果'标签页查看")
                    
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        else:
            st.warning("⚠️ 请先输入或提取财务数据")

with tab2:
    st.header("分析结果")
    
    if 'dupont_result' in st.session_state:
        result = st.session_state.dupont_result
        
        # 显示基本信息
        st.subheader(f"{result.company_name} - {result.report_period}")
        
        # 第一层：ROE分解
        st.markdown("### 📊 第一层：ROE分解")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="净资产收益率 (ROE)",
                value=result.level1.roe.formatted_value,
                help=result.level1.roe.formula
            )
        
        with col2:
            st.metric(
                label="资产净利率 (ROA)",
                value=result.level1.roa.formatted_value,
                help=result.level1.roa.formula
            )
        
        with col3:
            st.metric(
                label="权益乘数",
                value=result.level1.equity_multiplier.formatted_value,
                help=result.level1.equity_multiplier.formula
            )
        
        st.markdown("---")
        
        # 第二层：进一步分解
        st.markdown("### 📈 第二层：ROA和权益乘数分解")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="营业净利润率",
                value=result.level2.net_profit_margin.formatted_value,
                help=result.level2.net_profit_margin.formula
            )
        
        with col2:
            st.metric(
                label="资产周转率",
                value=result.level2.asset_turnover.formatted_value,
                help=result.level2.asset_turnover.formula
            )
        
        with col3:
            st.metric(
                label="总资产",
                value=result.level2.total_assets.formatted_value
            )
        
        with col4:
            st.metric(
                label="股东权益",
                value=result.level2.shareholders_equity.formatted_value
            )
        
        st.markdown("---")
        
        # AI洞察
        if result.insights:
            st.markdown("### 💡 AI分析洞察")
            for insight in result.insights:
                st.info(insight)
        
        # 优势和劣势
        col1, col2 = st.columns(2)
        
        with col1:
            if result.strengths:
                st.markdown("### ✅ 优势指标")
                for strength in result.strengths:
                    st.success(strength)
        
        with col2:
            if result.weaknesses:
                st.markdown("### ⚠️ 劣势指标")
                for weakness in result.weaknesses:
                    st.warning(weakness)
        
        # 改进建议
        if result.recommendations:
            st.markdown("### 💼 改进建议")
            for i, rec in enumerate(result.recommendations, 1):
                st.markdown(f"{i}. {rec}")
    
    else:
        st.info("👈 请先在'数据输入'标签页生成杜邦分析")

with tab3:
    st.header("可视化图表")
    
    if 'dupont_result' in st.session_state:
        result = st.session_state.dupont_result
        
        # 选择可视化类型
        viz_type = st.radio(
            "选择可视化类型",
            ["Sankey流程图", "树状图", "指标对比柱状图"],
            horizontal=True
        )
        
        try:
            from utils.dupont_visualizer import (
                create_dupont_sankey,
                create_dupont_tree_chart,
                create_dupont_bar_chart
            )
            
            if viz_type == "Sankey流程图":
                st.markdown("### 📊 杜邦分析Sankey流程图")
                st.markdown("*展示各指标之间的层级关系和影响路径*")
                fig = create_dupont_sankey(result)
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "树状图":
                st.markdown("### 🌳 杜邦分析树状图")
                st.markdown("*以树状结构展示指标分解*")
                fig = create_dupont_tree_chart(result)
                st.plotly_chart(fig, use_container_width=True)
            
            else:  # 指标对比柱状图
                st.markdown("### 📊 关键指标对比")
                st.markdown("*对比各层级关键指标的数值*")
                fig = create_dupont_bar_chart(result)
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ 可视化生成失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    else:
        st.info("👈 请先在'数据输入'标签页生成杜邦分析")

