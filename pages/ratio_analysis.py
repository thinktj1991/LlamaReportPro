import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.financial_calculator import FinancialCalculator
from utils.state import init_state, init_processors
from utils.export_ui import add_export_section
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_ratio_analysis_page():
    try:
        st.header("📊 财务比率分析")
        st.markdown("高级财务比率计算和趋势分析")
        
        # Initialize session state safely with error handling
        state_initialized = init_state()
        if not state_initialized:
            st.error("初始化会话状态失败。一些功能可能无法正常工作。")
            # Continue with limited functionality
        
        # Ensure company_data exists with fallback
        if not hasattr(st.session_state, 'company_data') or st.session_state.company_data is None:
            st.session_state.company_data = {}
        
        # Check for company data
        if not st.session_state.company_data:
            st.warning("没有可用的公司数据。请先在“上传与处理”页面处理文档。")
            st.info("您仍然可以在“📋 比率库”标签中查看比率库并了解财务比率。")
        
        # Initialize financial calculator with error handling
        try:
            if not hasattr(st.session_state, 'financial_calculator') or st.session_state.financial_calculator is None:
                st.session_state.financial_calculator = FinancialCalculator()
        except Exception as e:
            logger.error(f"Error initializing financial calculator: {str(e)}")
            st.error(f"初始化财务计算器错误：{str(e)}")
            st.session_state.financial_calculator = None
        
        # Main content tabs - always show them
        tab1, tab2, tab3, tab4 = st.tabs(["🧮 比率计算器", "📈 趋势分析", "🏢 公司对比", "📋 比率库"])
        
        with tab1:
            try:
                show_ratio_calculator()
            except Exception as e:
                logger.error(f"Error in ratio calculator: {str(e)}")
                st.error(f"加载比率计算器错误：{str(e)}")
        
        with tab2:
            try:
                show_trend_analysis()
            except Exception as e:
                logger.error(f"Error in trend analysis: {str(e)}")
                st.error(f"加载趋势分析错误：{str(e)}")
        
        with tab3:
            try:
                show_ratio_comparison()
            except Exception as e:
                logger.error(f"Error in ratio comparison: {str(e)}")
                st.error(f"加载比率对比错误：{str(e)}")
        
        with tab4:
            try:
                show_ratio_library()
            except Exception as e:
                logger.error(f"Error in ratio library: {str(e)}")
                st.error(f"加载比率库错误：{str(e)}")
        
        # Add export functionality for calculated ratios
        if hasattr(st.session_state, 'calculated_ratios') and st.session_state.calculated_ratios:
            st.divider()
            add_export_section('ratios', st.session_state.calculated_ratios)
                
    except Exception as e:
        logger.error(f"Critical error in ratio analysis page: {str(e)}")
        st.error("加载比率分析页面时发生严重错误。请刷新页面并重试。")
        st.exception(e)

def show_ratio_calculator():
    """
    Show financial ratio calculator for individual companies
    """
    st.subheader("🧮 Financial Ratio Calculator")
    
    # Company selection
    available_companies = list(st.session_state.company_data.keys())
    
    selected_company = st.selectbox(
        "Select Company for Ratio Analysis:",
        options=available_companies,
        help="Choose a company to analyze financial ratios"
    )
    
    if selected_company:
        company_data = st.session_state.company_data[selected_company]
        
        # Get financial metrics
        financial_metrics = company_data.get('financial_metrics', {})
        
        if not financial_metrics:
            st.warning(f"No financial metrics available for {selected_company}. Please ensure the document contains financial tables.")
            return
        
        # Calculate ratios
        with st.spinner("Calculating financial ratios..."):
            ratio_results = st.session_state.financial_calculator.calculate_financial_ratios(
                financial_metrics, selected_company
            )
        
        # Display results
        display_ratio_results(ratio_results)

def display_ratio_results(ratio_results):
    """
    Display comprehensive ratio calculation results
    """
    if 'error' in ratio_results:
        st.error(f"Error calculating ratios: {ratio_results['error']}")
        return
    
    company_name = ratio_results.get('company', 'Company')
    overall_score = ratio_results.get('overall_score', 0.0)
    
    # Overall performance summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_color = "green" if overall_score >= 0.7 else "orange" if overall_score >= 0.4 else "red"
        st.metric(
            "Overall Financial Health",
            f"{overall_score:.1%}",
            help="Composite score based on all calculated ratios"
        )
        st.markdown(f"<div style='color: {score_color}'>Rating: {get_rating_text(overall_score)}</div>", 
                   unsafe_allow_html=True)
    
    with col2:
        strengths = ratio_results.get('strengths', [])
        st.metric("Financial Strengths", len(strengths))
        if strengths:
            with st.expander("View Strengths"):
                for strength in strengths:
                    st.success(f"✅ {strength}")
    
    with col3:
        weaknesses = ratio_results.get('weaknesses', [])
        st.metric("Areas for Improvement", len(weaknesses))
        if weaknesses:
            with st.expander("View Weaknesses"):
                for weakness in weaknesses:
                    st.warning(f"⚠️ {weakness}")
    
    # Category performance
    st.subheader("📊 Performance by Category")
    
    categories = ratio_results.get('categories', {})
    if categories:
        # Create category performance chart
        cat_names = list(categories.keys())
        cat_scores = [categories[cat]['score'] for cat in cat_names]
        
        fig_categories = go.Figure(data=go.Bar(
            x=[name.replace('_', ' ').title() for name in cat_names],
            y=cat_scores,
            text=[f"{score:.1%}" for score in cat_scores],
            textposition='auto',
            marker_color=['green' if score >= 0.7 else 'orange' if score >= 0.4 else 'red' 
                         for score in cat_scores]
        ))
        
        fig_categories.update_layout(
            title="Financial Performance by Category",
            yaxis_title="Performance Score",
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            height=400
        )
        
        st.plotly_chart(fig_categories, use_container_width=True)
        
        # Detailed category breakdown
        st.subheader("📋 Detailed Ratio Analysis")
        
        for category, cat_data in categories.items():
            with st.expander(f"{category.replace('_', ' ').title()} Ratios (Score: {cat_data['score']:.1%})"):
                display_category_ratios(cat_data['ratios'])
    
    # Missing data warning
    missing_data = ratio_results.get('missing_data', [])
    if missing_data:
        st.subheader("⚠️ Missing Critical Data")
        st.warning("The following critical financial data is missing, which may affect ratio accuracy:")
        for missing in missing_data:
            st.write(f"• {missing}")
    
    # Comprehensive visualization
    st.subheader("📈 Comprehensive Ratio Visualization")
    
    try:
        fig_comprehensive = st.session_state.financial_calculator.create_ratio_visualization(ratio_results)
        st.plotly_chart(fig_comprehensive, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")

def display_category_ratios(ratios):
    """
    Display ratios for a specific category
    """
    ratio_data = []
    
    for ratio_name, ratio_info in ratios.items():
        if ratio_info.get('value') is not None:
            ratio_data.append({
                'Ratio': ratio_name.replace('_', ' ').title(),
                'Value': f"{ratio_info['value']:.3f}",
                'Status': ratio_info.get('benchmark_status', 'unknown').title(),
                'Score': f"{ratio_info['score']:.1%}",
                'Description': ratio_info.get('description', '')
            })
        else:
            missing_components = ratio_info.get('missing_components', [])
            ratio_data.append({
                'Ratio': ratio_name.replace('_', ' ').title(),
                'Value': 'N/A',
                'Status': 'Missing Data',
                'Score': 'N/A',
                'Description': f"Missing: {', '.join(missing_components)}" if missing_components else 'Data unavailable'
            })
    
    if ratio_data:
        df = pd.DataFrame(ratio_data)
        st.dataframe(df, use_container_width=True)

def get_rating_text(score):
    """
    Convert score to rating text
    """
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Fair"
    elif score >= 0.2:
        return "Poor"
    else:
        return "Very Poor"

def show_trend_analysis():
    """
    Show trend analysis for financial ratios over time
    """
    st.subheader("📈 Financial Ratio Trend Analysis")
    
    # This feature would require historical data
    st.info("📊 Trend analysis requires multiple time periods of financial data.")
    st.markdown("""
    **To use trend analysis:**
    1. Upload annual reports from multiple years for the same company
    2. Ensure consistent company naming across documents
    3. Return to this tab to view trends over time
    
    **Trend analysis features:**
    - Ratio performance over time
    - Improvement/decline identification
    - Volatility analysis
    - Comparative timeline charts
    """)
    
    # Check if we have multi-period data
    multi_period_companies = {}
    for company_name, company_data in st.session_state.company_data.items():
        base_name = company_name.split('_')[0]  # Assume naming convention: Company_2023, Company_2024
        if base_name not in multi_period_companies:
            multi_period_companies[base_name] = []
        multi_period_companies[base_name].append((company_name, company_data))
    
    # Find companies with multiple periods
    companies_with_trends = {k: v for k, v in multi_period_companies.items() if len(v) > 1}
    
    if companies_with_trends:
        st.success(f"Found trend data for {len(companies_with_trends)} companies!")
        
        # Company selection for trend analysis
        selected_base_company = st.selectbox(
            "Select Company for Trend Analysis:",
            options=list(companies_with_trends.keys())
        )
        
        if selected_base_company:
            show_company_trend_analysis(companies_with_trends[selected_base_company])
    else:
        st.warning("No multi-period data found. Upload documents from different years with consistent naming.")

def show_company_trend_analysis(company_periods):
    """
    Show trend analysis for a company across multiple periods
    """
    try:
        # Calculate ratios for each period
        timeline_ratios = []
        
        for company_name, company_data in sorted(company_periods):
            financial_metrics = company_data.get('financial_metrics', {})
            if financial_metrics:
                ratio_results = st.session_state.financial_calculator.calculate_financial_ratios(
                    financial_metrics, company_name
                )
                
                # Extract year from company name (assuming format like Company_2023)
                year = company_name.split('_')[-1] if '_' in company_name else 'Unknown'
                ratio_results['year'] = year
                timeline_ratios.append(ratio_results)
        
        if len(timeline_ratios) >= 2:
            # Create trend analysis
            trend_analysis = st.session_state.financial_calculator.create_ratio_trend_analysis(timeline_ratios)
            
            # Display trend summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Analysis Periods", trend_analysis.get('periods', 0))
            
            with col2:
                improving_count = len(trend_analysis.get('improvement_trends', []))
                st.metric("Improving Ratios", improving_count)
            
            with col3:
                declining_count = len(trend_analysis.get('declining_trends', []))
                st.metric("Declining Ratios", declining_count)
            
            # Overall trend assessment
            overall_trend = trend_analysis.get('overall_trend', 'stable')
            trend_color = {'improving': 'green', 'declining': 'red', 'stable': 'blue'}
            st.markdown(f"**Overall Trend:** <span style='color: {trend_color.get(overall_trend, 'black')}'>{overall_trend.title()}</span>", 
                       unsafe_allow_html=True)
            
            # Trend visualization
            try:
                fig_trend = st.session_state.financial_calculator.create_trend_visualization(trend_analysis)
                st.plotly_chart(fig_trend, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating trend visualization: {str(e)}")
            
            # Detailed trend analysis
            if trend_analysis.get('ratio_trends'):
                st.subheader("📊 Detailed Trend Analysis")
                
                for ratio_name, trend_data in trend_analysis['ratio_trends'].items():
                    direction = trend_data.get('direction', 'stable')
                    volatility = trend_data.get('volatility', 0.0)
                    
                    with st.expander(f"{ratio_name.replace('_', ' ').title()} - {direction.title()}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Direction:** {direction.title()}")
                            st.write(f"**Volatility:** {volatility:.2%}")
                        
                        with col2:
                            if 'values' in trend_data:
                                values = trend_data['values']
                                st.write(f"**Latest Value:** {values[-1]:.3f}")
                                if len(values) >= 2:
                                    change = (values[-1] - values[0]) / values[0] * 100
                                    st.write(f"**Total Change:** {change:+.1f}%")
        
    except Exception as e:
        st.error(f"Error in trend analysis: {str(e)}")

def show_ratio_comparison():
    """
    Show ratio comparison across multiple companies
    """
    st.subheader("🏢 Company Ratio Comparison")
    
    # Company selection
    available_companies = list(st.session_state.company_data.keys())
    
    if len(available_companies) < 2:
        st.warning("Need at least 2 companies for comparison. Please upload more annual reports.")
        return
    
    selected_companies = st.multiselect(
        "Select Companies for Ratio Comparison:",
        options=available_companies,
        default=available_companies[:min(3, len(available_companies))],
        help="Choose 2 or more companies to compare financial ratios"
    )
    
    if len(selected_companies) >= 2:
        # Calculate ratios for all selected companies
        company_ratios = {}
        
        with st.spinner("Calculating ratios for comparison..."):
            for company_name in selected_companies:
                company_data = st.session_state.company_data[company_name]
                financial_metrics = company_data.get('financial_metrics', {})
                
                if financial_metrics:
                    ratio_results = st.session_state.financial_calculator.calculate_financial_ratios(
                        financial_metrics, company_name
                    )
                    company_ratios[company_name] = ratio_results
        
        if company_ratios:
            display_ratio_comparison(company_ratios)
        else:
            st.warning("No financial ratios could be calculated for the selected companies.")

def display_ratio_comparison(company_ratios):
    """
    Display comprehensive ratio comparison across companies
    """
    # Overall performance comparison
    st.subheader("📊 Overall Performance Comparison")
    
    companies = list(company_ratios.keys())
    overall_scores = [company_ratios[company].get('overall_score', 0.0) for company in companies]
    
    fig_overall = go.Figure(data=go.Bar(
        x=companies,
        y=overall_scores,
        text=[f"{score:.1%}" for score in overall_scores],
        textposition='auto',
        marker_color=['green' if score >= 0.7 else 'orange' if score >= 0.4 else 'red' 
                     for score in overall_scores]
    ))
    
    fig_overall.update_layout(
        title="Overall Financial Health Comparison",
        yaxis_title="Financial Health Score",
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        height=400
    )
    
    st.plotly_chart(fig_overall, use_container_width=True)
    
    # Category comparison
    st.subheader("📈 Performance by Category")
    
    # Get all ratio categories
    all_categories = set()
    for company_ratios_data in company_ratios.values():
        if 'categories' in company_ratios_data:
            all_categories.update(company_ratios_data['categories'].keys())
    
    all_categories = sorted(list(all_categories))
    
    if all_categories:
        # Create category comparison chart
        fig_categories = go.Figure()
        
        for company in companies:
            company_data = company_ratios[company]
            categories_data = company_data.get('categories', {})
            
            scores = []
            for category in all_categories:
                score = categories_data.get(category, {}).get('score', 0.0)
                scores.append(score)
            
            fig_categories.add_trace(go.Bar(
                name=company,
                x=[cat.replace('_', ' ').title() for cat in all_categories],
                y=scores
            ))
        
        fig_categories.update_layout(
            title="Category Performance Comparison",
            yaxis_title="Performance Score",
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_categories, use_container_width=True)
    
    # Detailed ratio comparison table
    st.subheader("📋 Detailed Ratio Comparison")
    
    create_ratio_comparison_table(company_ratios)

def create_ratio_comparison_table(company_ratios):
    """
    Create detailed comparison table of ratios across companies
    """
    try:
        # Collect all ratios across companies
        all_ratios = set()
        for company_data in company_ratios.values():
            if 'ratios' in company_data:
                all_ratios.update(company_data['ratios'].keys())
        
        all_ratios = sorted(list(all_ratios))
        
        if not all_ratios:
            st.warning("No ratios available for comparison.")
            return
        
        # Create comparison data
        comparison_data = []
        
        for ratio_name in all_ratios:
            row = {'Ratio': ratio_name.replace('_', ' ').title()}
            
            for company_name, company_data in company_ratios.items():
                ratio_data = company_data.get('ratios', {}).get(ratio_name, {})
                
                if ratio_data.get('value') is not None:
                    value = ratio_data['value']
                    status = ratio_data.get('benchmark_status', 'unknown')
                    
                    # Format value with status indicator
                    status_emoji = {
                        'excellent': '🟢',
                        'good': '🟡',
                        'acceptable': '🟠',
                        'poor': '🔴',
                        'unknown': '⚪'
                    }
                    
                    formatted_value = f"{value:.3f} {status_emoji.get(status, '⚪')}"
                    row[company_name] = formatted_value
                else:
                    row[company_name] = 'N/A'
            
            comparison_data.append(row)
        
        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            st.dataframe(df_comparison, use_container_width=True)
            
            # Legend
            st.markdown("""
            **Status Legend:**
            🟢 Excellent | 🟡 Good | 🟠 Acceptable | 🔴 Poor | ⚪ Unknown/No Benchmark
            """)
    
    except Exception as e:
        st.error(f"Error creating comparison table: {str(e)}")

def show_ratio_library():
    """
    Show comprehensive ratio library and definitions
    """
    st.subheader("📋 Financial Ratio Library")
    st.markdown("Complete reference guide for all supported financial ratios")
    
    calculator = st.session_state.financial_calculator
    
    for category, ratios in calculator.ratio_definitions.items():
        with st.expander(f"{category.replace('_', ' ').title()} Ratios", expanded=False):
            
            for ratio_name, ratio_info in ratios.items():
                st.markdown(f"**{ratio_name.replace('_', ' ').title()}**")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**Formula:** `{ratio_info['formula']}`")
                    st.write(f"**Description:** {ratio_info['description']}")
                
                with col2:
                    benchmark = ratio_info['benchmark']
                    st.write("**Benchmarks:**")
                    st.write(f"- Excellent: {benchmark['good']}")
                    st.write(f"- Good: {benchmark['acceptable']}")
                    st.write(f"- Poor: {benchmark['poor']}")
                
                st.markdown("---")

# Call the main function to render the page when executed by Streamlit's multipage system
if __name__ == "__main__" or True:  # Always execute when this page is loaded
    show_ratio_analysis_page()