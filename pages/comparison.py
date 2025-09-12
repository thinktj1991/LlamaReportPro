import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from utils.company_comparator import CompanyComparator
from utils.data_visualizer import DataVisualizer
from utils.state import init_state, init_processors
from utils.industry_analytics import IndustryAnalytics
from utils.export_ui import add_export_section
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_comparison_page():
    # Enhanced header with comparison capabilities showcase
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>🔄 智能公司对比分析</h2>
        <p>全面对比多家公司的财务数据、绩效指标和行业地位，发现投资机会</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>🎆 对比能力:</strong> 多维度对比 • 行业基准 • 动态排名 • 智能洞察 • 个性化分析
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state safely
    init_state()
    
    # Enhanced empty state checks
    if not st.session_state.company_data:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 12px; border: 2px dashed #dee2e6;">
            <h3 style="color: #6c757d;">📁 需要公司数据</h3>
            <p style="color: #6c757d; font-size: 1.1rem;">请先在上传与处理页面处理至少两家公司的年报文档</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if len(st.session_state.company_data) < 2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffeaa7;">
            <h3 style="color: #856404;">🏢 需要更多公司</h3>
            <p style="color: #856404;">对比分析需要至少两家公司的数据。当前只有 <strong>{}</strong> 家公司</p>
            <p style="color: #856404;">请上传更多年报文档后再进行对比分析</p>
        </div>
        """.format(len(st.session_state.company_data)), unsafe_allow_html=True)
        return
    
    # Initialize processors including comparator and visualizer
    if not init_processors():
        st.error("初始化对比组件失败")
        return
    
    # Company selection and comparison setup
    show_comparison_setup()
    
    # Initialize industry analytics
    if not hasattr(st.session_state, 'industry_analytics') or st.session_state.industry_analytics is None:
        st.session_state.industry_analytics = IndustryAnalytics()

    # Enhanced comparison tabs with modern styling
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">📈 全面对比分析</h4>
        <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">选择下方标签页查看不同维度的对比分析结果</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 公司概览", "📈 指标对比", "📋 详细数据", 
        "🔍 AI洞察", "🏆 竞争排名", "🏭 行业基准"
    ])
    
    with tab1:
        show_comparison_overview()
    
    with tab2:
        show_metric_comparison()
    
    with tab3:
        show_comparison_table()
    
    with tab4:
        show_comparison_insights()
    
    with tab5:
        show_percentile_rankings()
    
    with tab6:
        show_industry_benchmarks()
    
    # Add export functionality
    if hasattr(st.session_state, 'comparison_results') and st.session_state.comparison_results:
        st.divider()
        add_export_section('comparison', st.session_state.comparison_results)

def show_comparison_setup():
    """
    Enhanced comparison setup with modern UI
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">⚙️ 对比参数设置</h3>
        <p style="margin: 0; color: #6c757d;">选择您想要对比的公司和关键指标，系统将生成全面的对比分析报告</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Company selection with enhanced info
    available_companies = list(st.session_state.company_data.keys())
    
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 1rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">🏢 公司选择</h4>
        <p style="margin: 0 0 1rem 0; color: #6c757d; font-size: 0.9rem;">可用公司: {}</p>
    </div>
    """.format(len(available_companies)), unsafe_allow_html=True)
    
    # Enhanced layout with better organization
    setup_col1, setup_col2 = st.columns(2)
    
    with setup_col1:
        st.markdown("**🏢 选择对比公司**")
        selected_companies = st.multiselect(
            "选择要对比的公司：",
            options=available_companies,
            default=available_companies[:min(3, len(available_companies))],
            help="选择两家或更多公司进行对比分析"
        )
        
        # Show selected company info
        if selected_companies:
            st.markdown(f"**✅ 已选择:** {len(selected_companies)} 家公司")
            for company in selected_companies:
                company_info = st.session_state.company_data[company]
                year = company_info.get('year', '未知')
                st.caption(f"• {company} ({year})") 
    
    with setup_col2:
        st.markdown("**📈 选择对比指标**")
        # Metric selection
        available_metrics = st.session_state.company_comparator.identify_available_metrics(
            st.session_state.company_data
        )
        
        selected_metrics = st.multiselect(
            "选择财务指标：",
            options=available_metrics,
            default=available_metrics[:min(5, len(available_metrics))],
            help="选择关键财务指标进行深度对比"
        )
        
        # Show metric info
        if selected_metrics:
            st.markdown(f"**✅ 已选择:** {len(selected_metrics)} 个指标")
            if len(selected_metrics) > 8:
                st.warning("ℹ️ 指标较多，可能影响显示效果")
    
    # Store selections in session state
    st.session_state.selected_companies = selected_companies
    st.session_state.selected_metrics = selected_metrics
    
    # Metric coverage information
    if available_metrics:
        show_metric_coverage(available_metrics)

def show_metric_coverage(available_metrics):
    """
    Show enhanced metric coverage visualization
    """
    with st.expander("📊 数据质量与指标覆盖情况", expanded=False):
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <strong>📈 数据质量分析:</strong> 了解各指标在不同公司中的可用性，选择覆盖率高的指标可获得更准确的对比结果
        </div>
        """, unsafe_allow_html=True)
        coverage = st.session_state.company_comparator.calculate_metric_coverage(
            st.session_state.company_data
        )
        
        if coverage:
            # Enhanced coverage visualization
            metrics = list(coverage.keys())
            coverage_pcts = list(coverage.values())
            
            # Create color-coded coverage chart
            colors = ['#e74c3c' if pct < 30 else '#f39c12' if pct < 70 else '#27ae60' for pct in coverage_pcts]
            
            fig = go.Figure(data=go.Bar(
                x=metrics,
                y=coverage_pcts,
                text=[f"{pct:.0f}%" for pct in coverage_pcts],
                textposition='auto',
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(0,0,0,0.2)', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>Coverage: %{y:.1f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title={
                    'text': "📈 指标在各公司中的覆盖情况",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="财务指标",
                yaxis_title="覆盖率 (%)",
                yaxis=dict(range=[0, 100]),
                height=450,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Coverage statistics
            coverage_stats_col1, coverage_stats_col2, coverage_stats_col3 = st.columns(3)
            
            with coverage_stats_col1:
                high_coverage = sum(1 for pct in coverage_pcts if pct >= 70)
                st.metric("🟢 高覆盖指标", f"{high_coverage} 个", help="覆盖率 ≥ 70%")
            
            with coverage_stats_col2:
                medium_coverage = sum(1 for pct in coverage_pcts if 30 <= pct < 70)
                st.metric("🟡 中等覆盖指标", f"{medium_coverage} 个", help="30% ≤ 覆盖率 < 70%")
            
            with coverage_stats_col3:
                low_coverage = sum(1 for pct in coverage_pcts if pct < 30)
                st.metric("🔴 低覆盖指标", f"{low_coverage} 个", help="覆盖率 < 30%")
            
            # Enhanced metrics recommendations
            high_coverage_metrics = {k: v for k, v in coverage.items() if v >= 50}
            if high_coverage_metrics:
                st.markdown("**👍 推荐对比指标（覆盖率 ≥ 50%）:**")
                
                # Group metrics by coverage level
                excellent_metrics = [(k, v) for k, v in high_coverage_metrics.items() if v >= 80]
                good_metrics = [(k, v) for k, v in high_coverage_metrics.items() if 50 <= v < 80]
                
                if excellent_metrics:
                    st.markdown("**✅ 优秀覆盖（≥ 80%）:**")
                    for metric, pct in sorted(excellent_metrics, key=lambda x: x[1], reverse=True):
                        st.markdown(f"• **{metric}**: {pct:.0f}%")
                
                if good_metrics:
                    st.markdown("**👌 良好覆盖（50-80%）:**")
                    for metric, pct in sorted(good_metrics, key=lambda x: x[1], reverse=True):
                        st.markdown(f"• {metric}: {pct:.0f}%")
            else:
                st.markdown("""
                <div style="background: #fff3cd; color: #856404; padding: 1rem; border-radius: 8px;">
                    <strong>⚠️ 数据覆盖不足</strong><br>
                    建议上传更多公司数据或检查数据质量以获得更好的对比效果
                </div>
                """, unsafe_allow_html=True)

def show_comparison_overview():
    """
    Show enhanced company overview comparison
    """
    if not hasattr(st.session_state, 'selected_companies') or len(st.session_state.selected_companies) < 2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #f5c6cb;">
            <h4 style="color: #721c24;">⚠️ 需要选择公司</h4>
            <p style="color: #721c24;">请在上方的设置区域选择至少 2 家公司进行对比</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">🏢 公司基本情况对比</h4>
        <p style="margin: 0; color: #6c757d;">对比选中公司的基本信息和数据质量</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create overview comparison
    selected_data = {k: v for k, v in st.session_state.company_data.items() 
                    if k in st.session_state.selected_companies}
    
    # Basic company information
    overview_data = []
    for company_name, data in selected_data.items():
        overview_data.append({
            'Company': company_name,
            'Year': data.get('year', 'Unknown'),
            'Document File': data.get('document_file', 'Unknown'),
            'Pages': data.get('key_statistics', {}).get('document_pages', 0),
            'Total Tables': data.get('key_statistics', {}).get('total_tables', 0),
            'Financial Tables': data.get('key_statistics', {}).get('financial_tables', 0),
            'Data Richness': f"{data.get('key_statistics', {}).get('data_richness_score', 0):.2f}"
        })
    
    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True)
    
    # Visual comparison of key statistics
    create_overview_charts(selected_data)

def create_overview_charts(selected_data):
    """
    Create overview charts for company comparison
    """
    try:
        companies = list(selected_data.keys())
        
        # Extract data for charts
        pages = [data.get('key_statistics', {}).get('document_pages', 0) for data in selected_data.values()]
        financial_tables = [data.get('key_statistics', {}).get('financial_tables', 0) for data in selected_data.values()]
        richness_scores = [data.get('key_statistics', {}).get('data_richness_score', 0) for data in selected_data.values()]
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Document Pages', 'Financial Tables', 'Data Richness Score'),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
        )
        
        # Pages chart
        fig.add_trace(
            go.Bar(x=companies, y=pages, name="Pages", marker_color='lightblue'),
            row=1, col=1
        )
        
        # Financial tables chart
        fig.add_trace(
            go.Bar(x=companies, y=financial_tables, name="Financial Tables", marker_color='lightgreen'),
            row=1, col=2
        )
        
        # Richness score chart
        fig.add_trace(
            go.Bar(x=companies, y=richness_scores, name="Data Richness", marker_color='lightcoral'),
            row=1, col=3
        )
        
        fig.update_layout(
            title="Company Data Overview Comparison",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error creating overview charts: {str(e)}")
        st.error("Error creating overview charts")

def show_metric_comparison():
    """
    Show detailed metric comparison
    """
    if (not hasattr(st.session_state, 'selected_companies') or 
        not hasattr(st.session_state, 'selected_metrics') or
        len(st.session_state.selected_companies) < 2):
        st.warning("Please select companies and metrics in the setup section.")
        return
    
    st.subheader("📈 Financial Metrics Comparison")
    
    selected_data = {k: v for k, v in st.session_state.company_data.items() 
                    if k in st.session_state.selected_companies}
    
    # Metric selection for detailed analysis
    if st.session_state.selected_metrics:
        selected_metric = st.selectbox(
            "Select metric for detailed analysis:",
            st.session_state.selected_metrics
        )
        
        if selected_metric:
            # Perform metric trend analysis
            trend_analysis = st.session_state.company_comparator.create_metric_trend_analysis(
                selected_data, selected_metric
            )
            
            show_metric_trend_analysis(trend_analysis)
            
            # Create metric comparison chart
            create_metric_comparison_chart(selected_data, selected_metric)
    
    # Multi-metric comparison
    if len(st.session_state.selected_metrics) > 1:
        show_multi_metric_comparison(selected_data)

def show_metric_trend_analysis(trend_analysis):
    """
    Show detailed analysis for a specific metric
    """
    metric = trend_analysis['metric']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Companies with Data", trend_analysis['companies_with_data'])
    
    with col2:
        if trend_analysis['statistics']:
            mean_val = trend_analysis['statistics'].get('mean', 0)
            st.metric("Average Value", f"{mean_val:,.0f}" if mean_val > 1000 else f"{mean_val:.2f}")
    
    with col3:
        if trend_analysis['statistics']:
            std_val = trend_analysis['statistics'].get('std', 0)
            st.metric("Std Deviation", f"{std_val:,.0f}" if std_val > 1000 else f"{std_val:.2f}")
    
    # Show ranking
    if trend_analysis['ranking']:
        st.write(f"**{metric.title()} Ranking:**")
        for rank, company, value in trend_analysis['ranking']:
            st.write(f"{rank}. {company}: {value:,.0f}" if value > 1000 else f"{rank}. {company}: {value:.2f}")

def create_metric_comparison_chart(selected_data, metric):
    """
    Create chart for specific metric comparison
    """
    try:
        companies = []
        values = []
        
        for company_name, data in selected_data.items():
            value = data.get('financial_metrics', {}).get(metric)
            if value is not None and isinstance(value, (int, float)):
                companies.append(company_name)
                values.append(value)
        
        if len(companies) >= 2:
            # Create bar chart
            fig = go.Figure(data=go.Bar(
                x=companies,
                y=values,
                text=[f"{v:,.0f}" if v > 1000 else f"{v:.2f}" for v in values],
                textposition='auto',
                marker_color=px.colors.qualitative.Set3[:len(companies)]
            ))
            
            fig.update_layout(
                title=f"{metric.title()} Comparison",
                xaxis_title="Companies",
                yaxis_title=metric.title(),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Not enough data available for {metric} comparison.")
    
    except Exception as e:
        logger.error(f"Error creating metric comparison chart: {str(e)}")
        st.error("Error creating comparison chart")

def show_multi_metric_comparison(selected_data):
    """
    Show comparison across multiple metrics
    """
    st.subheader("📊 Multi-Metric Comparison")
    
    try:
        # Create radar chart for multi-metric comparison
        companies = list(selected_data.keys())
        metrics = st.session_state.selected_metrics
        
        # Normalize data for radar chart
        normalized_data = {}
        for metric in metrics:
            values = []
            for company in companies:
                value = selected_data[company].get('financial_metrics', {}).get(metric)
                values.append(value if isinstance(value, (int, float)) else 0)
            
            if max(values) > 0:
                normalized_values = [v / max(values) for v in values]
                normalized_data[metric] = normalized_values
        
        if normalized_data:
            # Create radar chart
            fig = go.Figure()
            
            for i, company in enumerate(companies):
                company_values = [normalized_data[metric][i] for metric in normalized_data.keys()]
                
                fig.add_trace(go.Scatterpolar(
                    r=company_values,
                    theta=list(normalized_data.keys()),
                    fill='toself',
                    name=company
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                showlegend=True,
                title="Multi-Metric Comparison (Normalized)",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("Note: Values are normalized to 0-1 scale for comparison. Larger area indicates better relative performance.")
    
    except Exception as e:
        logger.error(f"Error creating multi-metric comparison: {str(e)}")
        st.error("Error creating multi-metric comparison")

def show_comparison_table():
    """
    Show detailed comparison table
    """
    if (not hasattr(st.session_state, 'selected_companies') or 
        not hasattr(st.session_state, 'selected_metrics') or
        len(st.session_state.selected_companies) < 2):
        st.warning("Please select companies and metrics in the setup section.")
        return
    
    st.subheader("📋 Detailed Comparison Table")
    
    # Create comparison table
    comparison_df = st.session_state.company_comparator.create_comparison_table(
        {k: v for k, v in st.session_state.company_data.items() 
         if k in st.session_state.selected_companies},
        st.session_state.selected_metrics
    )
    
    if not comparison_df.empty:
        st.dataframe(comparison_df, use_container_width=True)
        
        # Export option
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Comparison as CSV",
            data=csv,
            file_name="company_comparison.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data available for the selected companies and metrics.")

def show_comparison_insights():
    """
    Show AI-generated insights from comparison
    """
    if (not hasattr(st.session_state, 'selected_companies') or 
        not hasattr(st.session_state, 'selected_metrics') or
        len(st.session_state.selected_companies) < 2):
        st.warning("Please select companies and metrics in the setup section.")
        return
    
    st.subheader("🔍 Comparison Insights")
    
    # Generate insights
    selected_data = {k: v for k, v in st.session_state.company_data.items() 
                    if k in st.session_state.selected_companies}
    
    insights = st.session_state.company_comparator.generate_comparison_insights(
        selected_data, st.session_state.selected_metrics
    )
    
    if insights:
        st.write("**Key Insights:**")
        for i, insight in enumerate(insights, 1):
            st.write(f"{i}. {insight}")
    else:
        st.info("No insights available for the selected comparison.")


def show_percentile_rankings():
    """
    Show percentile rankings and competitive positioning
    """
    if (not hasattr(st.session_state, 'selected_companies') or 
        len(st.session_state.selected_companies) < 2):
        st.warning("Please select at least 2 companies in the setup section for rankings analysis.")
        return
    
    st.subheader("🏆 Percentile Rankings & Competitive Positioning")
    st.markdown("Advanced statistical analysis of company performance relative to peers")
    
    # Get selected company data
    selected_data = {k: v for k, v in st.session_state.company_data.items() 
                    if k in st.session_state.selected_companies}
    
    # Calculate percentile rankings
    with st.spinner("Calculating percentile rankings..."):
        percentile_data = st.session_state.industry_analytics.calculate_industry_percentiles(selected_data)
    
    if not percentile_data:
        st.warning("Insufficient data for percentile analysis. Companies need financial metrics for ranking.")
        return
    
    # Display rankings table
    st.subheader("📊 Percentile Rankings Table")
    st.markdown("**Legend**: 📈 Higher is Better | 📉 Lower is Better")
    
    rankings_data = []
    for company_name, metrics in percentile_data.items():
        for metric, data in metrics.items():
            # Add orientation indicator
            orientation_symbol = "📈" if data['orientation'] == 'Higher is Better' else "📉"
            rankings_data.append({
                'Company': company_name,
                'Metric': f"{orientation_symbol} {metric.replace('_', ' ').title()}",
                'Value': f"{data['value']:.3f}" if isinstance(data['value'], float) else str(data['value']),
                'Percentile': f"{data['percentile']:.1f}%",
                'Rank': f"{data['rank']}/{data['total_companies']}"
            })
    
    if rankings_data:
        rankings_df = pd.DataFrame(rankings_data)
        
        # Color code by percentile
        def color_percentile(val):
            try:
                percentile = float(val.replace('%', ''))
                if percentile >= 80:
                    return 'background-color: #d4edda'  # Green
                elif percentile >= 60:
                    return 'background-color: #fff3cd'  # Yellow
                elif percentile >= 40:
                    return 'background-color: #f8d7da'  # Light red
                else:
                    return 'background-color: #f5c6cb'  # Red
            except:
                return ''
        
        styled_df = rankings_df.style.applymap(color_percentile, subset=['Percentile'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Competitive positioning chart
        st.subheader("🎯 Competitive Positioning Radar")
        positioning_chart = st.session_state.industry_analytics.create_competitive_positioning_chart(percentile_data)
        if positioning_chart:
            st.plotly_chart(positioning_chart, use_container_width=True)
        
        # Performance summary
        st.subheader("📈 Performance Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            # Top performers
            st.write("**🏆 Top Performers by Metric:**")
            top_performers = {}
            for company_name, metrics in percentile_data.items():
                for metric, data in metrics.items():
                    if data['percentile'] >= 80:
                        if metric not in top_performers:
                            top_performers[metric] = []
                        top_performers[metric].append(company_name)
            
            for metric, companies in top_performers.items():
                st.write(f"• **{metric.replace('_', ' ').title()}**: {', '.join(companies)}")
        
        with col2:
            # Company strengths
            st.write("**💪 Company Strengths:**")
            for company_name, metrics in percentile_data.items():
                strengths = [metric.replace('_', ' ').title() for metric, data in metrics.items() 
                           if data['percentile'] >= 70]
                if strengths:
                    st.write(f"• **{company_name}**: {', '.join(strengths[:3])}")


def show_industry_benchmarks():
    """
    Show industry benchmark analysis
    """
    if (not hasattr(st.session_state, 'selected_companies') or 
        len(st.session_state.selected_companies) < 1):
        st.warning("Please select companies in the setup section for industry benchmarking.")
        return
    
    st.subheader("🏭 Industry Benchmark Analysis")
    st.markdown("Compare companies against industry-standard performance benchmarks")
    
    # Get selected company data
    selected_data = {k: v for k, v in st.session_state.company_data.items() 
                    if k in st.session_state.selected_companies}
    
    # Calculate industry benchmarks
    with st.spinner("Analyzing industry benchmarks..."):
        benchmark_data = st.session_state.industry_analytics.benchmark_against_industry(selected_data)
    
    if not benchmark_data:
        st.warning("Unable to perform industry benchmarking. Companies need financial metrics.")
        return
    
    # Industry overview
    st.subheader("🏢 Industry Classification")
    industry_summary = {}
    for company_name, data in benchmark_data.items():
        industry = data['industry']
        if industry not in industry_summary:
            industry_summary[industry] = []
        industry_summary[industry].append(company_name)
    
    for industry, companies in industry_summary.items():
        st.write(f"**{industry}**: {', '.join(companies)}")
    
    # Overall benchmark performance chart
    st.subheader("📊 Overall Benchmark Performance")
    benchmark_chart = st.session_state.industry_analytics.create_industry_benchmark_chart(benchmark_data)
    if benchmark_chart:
        st.plotly_chart(benchmark_chart, use_container_width=True)
    
    # Detailed benchmark results
    st.subheader("📋 Detailed Benchmark Results")
    
    for company_name, data in benchmark_data.items():
        with st.expander(f"📈 {company_name} - {data['industry']} (Score: {data['overall_score']:.2f}/4.0)"):
            
            # Performance overview
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Score display
                score = data['overall_score']
                if score >= 3.5:
                    st.success(f"Overall Score: {score:.2f}/4.0 🌟")
                elif score >= 2.5:
                    st.info(f"Overall Score: {score:.2f}/4.0 ✅")
                elif score >= 1.5:
                    st.warning(f"Overall Score: {score:.2f}/4.0 ⚠️")
                else:
                    st.error(f"Overall Score: {score:.2f}/4.0 ❌")
            
            with col2:
                # Quick summary
                excellent_count = sum(1 for m in data['metrics'].values() if m['performance'] == 'Excellent')
                good_count = sum(1 for m in data['metrics'].values() if m['performance'] == 'Good')
                total_metrics = len(data['metrics'])
                
                st.write(f"**Performance Breakdown:**")
                st.write(f"• Excellent: {excellent_count}/{total_metrics}")
                st.write(f"• Good: {good_count}/{total_metrics}")
                st.write(f"• Total Metrics Analyzed: {total_metrics}")
            
            # Detailed metrics
            if data['metrics']:
                metrics_data = []
                for metric, metric_data in data['metrics'].items():
                    metrics_data.append({
                        'Metric': metric.replace('_', ' ').title(),
                        'Value': f"{metric_data['value']:.3f}" if isinstance(metric_data['value'], float) else str(metric_data['value']),
                        'Performance': metric_data['performance'],
                        'Score': f"{metric_data['score']}/4"
                    })
                
                metrics_df = pd.DataFrame(metrics_data)
                
                # Color code by performance
                def color_performance(val):
                    if val == 'Excellent':
                        return 'background-color: #d4edda'  # Green
                    elif val == 'Good':
                        return 'background-color: #d1ecf1'  # Blue
                    elif val == 'Average':
                        return 'background-color: #fff3cd'  # Yellow
                    elif val == 'Below Average':
                        return 'background-color: #f8d7da'  # Light red
                    else:
                        return 'background-color: #f5c6cb'  # Red
                
                styled_metrics = metrics_df.style.applymap(color_performance, subset=['Performance'])
                st.dataframe(styled_metrics, use_container_width=True)
    
    # Generate competitive insights
    st.subheader("🔍 Competitive Intelligence")
    
    # Also get percentile data for comprehensive insights
    percentile_data = st.session_state.industry_analytics.calculate_industry_percentiles(selected_data)
    
    competitive_insights = st.session_state.industry_analytics.generate_competitive_insights(
        percentile_data, benchmark_data
    )
    
    if competitive_insights:
        for insight in competitive_insights:
            st.write(f"• {insight}")
    else:
        st.info("No competitive insights available.")

def show_additional_analysis(selected_data):
    """
    Show additional analysis options
    """
    st.subheader("🔬 Additional Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Generate Performance Summary"):
            generate_performance_summary(selected_data)
    
    with col2:
        if st.button("🎯 Identify Best Practices"):
            identify_best_practices(selected_data)

def generate_performance_summary(selected_data):
    """
    Generate performance summary for companies
    """
    st.subheader("📈 Performance Summary")
    
    try:
        for company_name, data in selected_data.items():
            with st.expander(f"📊 {company_name}"):
                # Basic info
                st.write(f"**Year:** {data.get('year', 'Unknown')}")
                st.write(f"**Document:** {data.get('document_file', 'Unknown')}")
                
                # Key statistics
                key_stats = data.get('key_statistics', {})
                st.write("**Data Quality:**")
                st.write(f"• Document Pages: {key_stats.get('document_pages', 0)}")
                st.write(f"• Financial Tables: {key_stats.get('financial_tables', 0)}")
                st.write(f"• Data Richness Score: {key_stats.get('data_richness_score', 0):.2f}")
                
                # Financial metrics
                financial_metrics = data.get('financial_metrics', {})
                if financial_metrics:
                    st.write("**Available Financial Metrics:**")
                    for metric, value in list(financial_metrics.items())[:10]:  # Show top 10
                        if isinstance(value, (int, float)):
                            formatted_value = f"{value:,.0f}" if value > 1000 else f"{value:.2f}"
                            st.write(f"• {metric.title()}: {formatted_value}")
    
    except Exception as e:
        logger.error(f"Error generating performance summary: {str(e)}")
        st.error("Error generating performance summary")

def identify_best_practices(selected_data):
    """
    Identify best practices from comparison
    """
    st.subheader("🎯 Best Practices")
    
    try:
        # Find companies with highest data richness
        richness_scores = {name: data.get('key_statistics', {}).get('data_richness_score', 0) 
                          for name, data in selected_data.items()}
        
        if richness_scores:
            best_company = max(richness_scores.keys(), key=lambda k: richness_scores[k])
            
            st.write("**Data Quality Best Practices:**")
            st.write(f"🏆 **{best_company}** has the highest data richness score ({richness_scores[best_company]:.2f})")
        else:
            st.write("**Data Quality Best Practices:**")
            st.write("No data available for comparison.")
            return
        
        best_data = selected_data[best_company]
        best_stats = best_data.get('key_statistics', {})
        
        st.write("**What makes this company's data stand out:**")
        st.write(f"• Document Length: {best_stats.get('document_pages', 0)} pages")
        st.write(f"• Financial Tables: {best_stats.get('financial_tables', 0)} tables")
        st.write(f"• Available Metrics: {len(best_data.get('financial_metrics', {}))}")
        
        # Metric coverage analysis
        available_metrics = st.session_state.company_comparator.identify_available_metrics(selected_data)
        coverage = st.session_state.company_comparator.calculate_metric_coverage(selected_data)
        
        high_coverage_metrics = [metric for metric, pct in coverage.items() if pct >= 75]
        
        if high_coverage_metrics:
            st.write("**Metrics with High Coverage (75%+):**")
            for metric in high_coverage_metrics[:5]:
                st.write(f"• {metric.title()}")
    
    except Exception as e:
        logger.error(f"Error identifying best practices: {str(e)}")
        st.error("Error identifying best practices")

# Main execution for Streamlit multipage
if __name__ == "__main__":
    show_comparison_page()
