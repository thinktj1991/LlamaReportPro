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
    st.header("🔄 公司对比")
    st.markdown("对比不同公司的财务指标和绩效表现")
    
    # Initialize session state safely
    init_state()
    
    if not st.session_state.company_data:
        st.warning("没有可用的公司数据。请先在“上传与处理”页面处理文档。")
        return
    
    if len(st.session_state.company_data) < 2:
        st.warning("需要至少两家公司进行对比。请上传更多年报。")
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

    # Main comparison content - Enhanced with industry analytics
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 概览", "📈 指标", "📋 数据表", 
        "🔍 洞察", "🏆 排名", "🏭 行业基准"
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
    Setup comparison parameters
    """
    st.subheader("⚙️ 对比设置")
    
    # Company selection
    available_companies = list(st.session_state.company_data.keys())
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_companies = st.multiselect(
            "选择要对比的公司：",
            options=available_companies,
            default=available_companies[:min(3, len(available_companies))],
            help="选择两家或更多公司进行对比"
        )
    
    with col2:
        # Metric selection
        available_metrics = st.session_state.company_comparator.identify_available_metrics(
            st.session_state.company_data
        )
        
        selected_metrics = st.multiselect(
            "选择要对比的指标：",
            options=available_metrics,
            default=available_metrics[:min(5, len(available_metrics))],
            help="选择财务指标进行对比"
        )
    
    # Store selections in session state
    st.session_state.selected_companies = selected_companies
    st.session_state.selected_metrics = selected_metrics
    
    # Metric coverage information
    if available_metrics:
        show_metric_coverage(available_metrics)

def show_metric_coverage(available_metrics):
    """
    Show metric coverage across companies
    """
    with st.expander("📊 指标覆盖范围", expanded=False):
        coverage = st.session_state.company_comparator.calculate_metric_coverage(
            st.session_state.company_data
        )
        
        if coverage:
            # Create coverage chart
            metrics = list(coverage.keys())
            coverage_pcts = list(coverage.values())
            
            fig = go.Figure(data=go.Bar(
                x=metrics,
                y=coverage_pcts,
                text=[f"{pct:.0f}%" for pct in coverage_pcts],
                textposition='auto',
            ))
            
            fig.update_layout(
                title="Metric Availability Across Companies",
                xaxis_title="Metrics",
                yaxis_title="Coverage (%)",
                yaxis=dict(range=[0, 100]),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show metrics with best coverage
            high_coverage_metrics = {k: v for k, v in coverage.items() if v >= 50}
            if high_coverage_metrics:
                st.write("**Metrics with 50%+ coverage:**")
                for metric, pct in sorted(high_coverage_metrics.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {metric}: {pct:.0f}%")

def show_comparison_overview():
    """
    Show overview comparison of companies
    """
    if not hasattr(st.session_state, 'selected_companies') or len(st.session_state.selected_companies) < 2:
        st.warning("Please select at least 2 companies in the setup section.")
        return
    
    st.subheader("🏢 Company Overview")
    
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
