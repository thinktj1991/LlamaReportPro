"""
AI-Powered Insights Page

This page provides advanced AI-driven insights including:
- Financial anomaly detection
- Risk pattern analysis  
- Automated intelligence generation
- Pattern recognition and forecasting signals
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.insights_engine import InsightsEngine
from utils.forecasting_engine import ForecastingEngine
from utils.forecasting_viz import ForecastingVisualizer
from utils.state import init_state, init_processors
from utils.export_ui import add_export_section
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_insights_page():
    """
    Main insights analysis page with enhanced UI/UX
    """
    try:
        # Enhanced header with AI capabilities showcase
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
            <h2>🤖 AI智能洞察与分析引擎</h2>
            <p>运用先进的机器学习算法和模式识别技术，为您的财务数据提供深度洞察和预测性分析</p>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>🧠 AI能力:</strong> 异常检测 • 风险评估 • 模式识别 • 智能预测 • 自动化洞察
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize session state safely
        init_state()
        
        if not st.session_state.company_data:
            st.warning("没有可用的公司数据。请先在“上传与处理”页面处理文档。")
            st.info("当您有公司数据后，此页面将提供：")
            st.markdown("""
            - 🔍 **异常检测**: 基于机器学习的不寻常财务模式识别
            - ⚠️ **风险分析**: 系统性的财务风险和预警信号评估  
            - 🤖 **AI洞察**: 自动化商业智能生成
            - 📊 **模式识别**: 高级趋势和关系分析
            - 📈 **时间序列预测**: ARIMA建模和增长预测
            """)
            
            # Show preview tabs even without data for better UX
            preview_tab1, preview_tab2, preview_tab3, preview_tab4, preview_tab5 = st.tabs([
                "🔍 异常检测", "⚠️ 风险分析",
                "🤖 AI洞察", "📊 模式分析", "📈 时间序列预测"
            ])
            
            with preview_tab1:
                st.info("**🔍 异常检测预览**\n\n使用孤立森林算法的基于机器学习的不寻常财务模式识别。")

            with preview_tab2:
                st.info("**⚠️ 风险分析预览**\n\n系统性的财务风险评估，包括流动性危机、过度杠杆和运营效率低下模式。")

            with preview_tab3:
                st.info("**🤖 AI洞察预览**\n\n自动生成综合性能、风险、异常和对比分析的商业智能。")

            with preview_tab4:
                st.info("**📊 模式分析预览**\n\n高级模式识别和趋势分析，包含预测信号。")

            with preview_tab5:
                st.info("**📈 预测预览**\n\n使用ARIMA模型的高级时间序列预测、情景分析和增长预测。")
            
            return
        
        # Initialize insights engine
        if not hasattr(st.session_state, 'insights_engine') or st.session_state.insights_engine is None:
            st.session_state.insights_engine = InsightsEngine()
        
        # Initialize forecasting engine
        if not hasattr(st.session_state, 'forecasting_engine') or st.session_state.forecasting_engine is None:
            st.session_state.forecasting_engine = ForecastingEngine()
        
        # Initialize forecasting visualizer
        if not hasattr(st.session_state, 'forecasting_viz') or st.session_state.forecasting_viz is None:
            st.session_state.forecasting_viz = ForecastingVisualizer()
        
        # Enhanced tabs layout with modern styling
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 2rem 0;">
            <h4 style="margin: 0 0 1rem 0; color: #495057;">🧠 AI分析工具箱</h4>
            <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">选择不同的AI分析模块深入洞察您的财务数据</p>
        </div>
        """, unsafe_allow_html=True)
        
        main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs([
            "🔍 异常检测", "⚠️ 风险分析",
            "🤖 AI洞察", "📊 模式分析", "📈 时间序列预测"
        ])
        
        with main_tab1:
            show_anomaly_detection()
        
        with main_tab2:
            show_risk_analysis()

        with main_tab3:
            show_ai_insights()

        with main_tab4:
            show_pattern_analysis()

        with main_tab5:
            show_forecasting_analysis()
            
    except Exception as e:
        logger.error(f"Error in insights page: {str(e)}")
        st.error("加载洞察页面错误。请刷新页面并重试。")
        st.exception(e)

def show_anomaly_detection():
    """
    Show enhanced anomaly detection analysis
    """
    try:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
            <h3 style="margin: 0 0 1rem 0; color: #495057;">🔍 智能异常检测系统</h3>
            <p style="margin: 0; color: #6c757d;">运用孤立森林算法和机器学习技术识别不寻常的财务模式和潜在风险信号</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Run anomaly detection
        with st.spinner("正在分析财务数据以检测异常..."):
            anomalies = st.session_state.insights_engine.detect_financial_anomalies(
                st.session_state.company_data
            )
        
        if not anomalies.get('anomalies'):
            st.success("✅ 财务数据中未检测到显著异常")
            st.info(anomalies.get('analysis', '\u6240\u6709\u516c\u53f8\u5747\u8868\u73b0\u51fa\u6b63\u5e38\u7684\u8d22\u52a1\u6a21\u5f0f'))
            return
        
        # Display anomaly results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Companies Analyzed", anomalies.get('total_companies', 0))
        
        with col2:
            st.metric("Anomalies Detected", len(anomalies['anomalies']))
        
        with col3:
            anomaly_rate = anomalies.get('anomaly_rate', 0)
            st.metric("Anomaly Rate", f"{anomaly_rate:.1%}")
        
        # Analysis summary
        st.write("**Analysis Summary:**")
        st.write(anomalies.get('analysis', 'No analysis available'))
        
        # Anomaly visualization
        anomaly_chart = st.session_state.insights_engine.create_anomaly_visualization(anomalies)
        if anomaly_chart:
            st.plotly_chart(anomaly_chart, use_container_width=True, key="anomaly_detection_chart")
        
        # Detailed anomaly breakdown
        st.subheader("🚨 Detailed Anomaly Analysis")
        
        for anomaly in anomalies['anomalies']:
            with st.expander(f"🔍 {anomaly['company']} - {anomaly['severity']} Risk"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if anomaly['severity'] == 'High':
                        st.error(f"Anomaly Score: {anomaly['anomaly_score']:.3f}")
                    else:
                        st.warning(f"Anomaly Score: {anomaly['anomaly_score']:.3f}")
                    
                    st.write("**Key Contributing Factors:**")
                    for factor in anomaly['top_factors']:
                        st.write(f"• {factor.replace('_', ' ').title()}")
                
                with col2:
                    st.write("**Description:**")
                    st.write(anomaly['description'])
                    
                    if anomaly['severity'] == 'High':
                        st.error("⚠️ **High Priority**: This company requires immediate investigation due to unusual financial patterns")
                    else:
                        st.warning("🔍 **Medium Priority**: Monitor this company for potential risks or unique business characteristics")
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {str(e)}")
        st.error(f"Error in anomaly detection: {str(e)}")

def show_risk_analysis():
    """
    Show risk pattern analysis
    """
    try:
        st.subheader("⚠️ Risk Pattern Analysis")
        st.markdown("Systematic identification of financial risks and red flags")
        
        # Run risk analysis
        with st.spinner("Analyzing risk patterns..."):
            risks = st.session_state.insights_engine.identify_risk_patterns(
                st.session_state.company_data
            )
        
        if not risks.get('company_risks'):
            st.success("✅ No significant risk patterns detected")
            return
        
        # Overall risk assessment
        assessment = risks.get('overall_assessment', {})
        
        if assessment:
            st.subheader("📊 Overall Risk Assessment")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Companies", assessment.get('total_companies', 0))
            
            with col2:
                high_risk = assessment.get('high_risk_count', 0)
                st.metric("High Risk", high_risk, delta=None)
                if high_risk > 0:
                    st.error(f"{high_risk} companies")
            
            with col3:
                medium_risk = assessment.get('medium_risk_count', 0)
                st.metric("Medium Risk", medium_risk, delta=None)
                if medium_risk > 0:
                    st.warning(f"{medium_risk} companies")
            
            with col4:
                low_risk = assessment.get('low_risk_count', 0)
                st.metric("Low Risk", low_risk, delta=None)
                if low_risk > 0:
                    st.success(f"{low_risk} companies")
        
        # Risk heatmap
        risk_heatmap = st.session_state.insights_engine.create_risk_heatmap(risks)
        if risk_heatmap:
            st.plotly_chart(risk_heatmap, use_container_width=True, key="insights_risk_analysis_heatmap_main")
        
        # Risk recommendations
        recommendations = risks.get('recommendations', [])
        if recommendations:
            st.subheader("💡 Risk Mitigation Recommendations")
            for rec in recommendations:
                st.write(f"• {rec}")
        
        # Detailed company risk analysis
        st.subheader("🏢 Company Risk Profiles")
        
        company_risks = risks.get('company_risks', {})
        for company_name, risk_data in company_risks.items():
            risk_level = risk_data.get('risk_level', 'Unknown')
            risk_score = risk_data.get('risk_score', 0)
            company_risk_list = risk_data.get('risks', [])
            
            # Color code by risk level
            if risk_level == 'High Risk':
                status_color = 'error'
            elif risk_level == 'Medium Risk':
                status_color = 'warning'
            else:
                status_color = 'success'
            
            with st.expander(f"🏢 {company_name} - {risk_level} (Score: {risk_score})"):
                if risk_level == 'High Risk':
                    st.error(f"**Risk Level**: {risk_level} | **Risk Score**: {risk_score}")
                elif risk_level == 'Medium Risk':
                    st.warning(f"**Risk Level**: {risk_level} | **Risk Score**: {risk_score}")
                else:
                    st.success(f"**Risk Level**: {risk_level} | **Risk Score**: {risk_score}")
                
                if company_risk_list:
                    st.write("**Identified Risk Patterns:**")
                    
                    for risk in company_risk_list:
                        pattern_name = risk['pattern'].replace('_', ' ').title()
                        severity = risk['severity']
                        description = risk['description']
                        
                        if severity == 'High':
                            st.error(f"🚨 **{pattern_name}** ({severity})")
                        else:
                            st.warning(f"⚠️ **{pattern_name}** ({severity})")
                        
                        st.write(f"*{description}*")
                        
                        # Show affected metrics
                        affected_metrics = risk.get('affected_metrics', {})
                        if affected_metrics:
                            metric_text = ", ".join([f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}" 
                                                   for k, v in affected_metrics.items()])
                            st.write(f"**Affected Metrics**: {metric_text}")
                        
                        st.write("---")
                else:
                    st.success("No significant risk patterns detected for this company")
        
    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        st.error(f"Error in risk analysis: {str(e)}")

def show_ai_insights():
    """
    Show AI-generated insights
    """
    try:
        st.subheader("🤖 AI-Generated Insights")
        st.markdown("Automated intelligence combining multiple analysis dimensions")
        
        # Generate comprehensive insights
        with st.spinner("Generating AI-powered insights..."):
            # Get anomalies and risks first
            anomalies = st.session_state.insights_engine.detect_financial_anomalies(
                st.session_state.company_data
            )
            risks = st.session_state.insights_engine.identify_risk_patterns(
                st.session_state.company_data
            )
            
            # Generate AI insights
            insights = st.session_state.insights_engine.generate_ai_insights(
                st.session_state.company_data, anomalies, risks
            )
        
        if not insights:
            st.info("No specific insights generated for the current data set")
            return
        
        # Display insights
        st.subheader("🧠 Key Intelligence")
        
        for i, insight in enumerate(insights, 1):
            # Parse insight to determine type and styling
            if "High Risk" in insight or "🚨" in insight:
                st.error(f"**{i}.** {insight}")
            elif "Risk" in insight or "⚠️" in insight:
                st.warning(f"**{i}.** {insight}")
            elif "Strong" in insight or "💪" in insight or "🏆" in insight:
                st.success(f"**{i}.** {insight}")
            else:
                st.info(f"**{i}.** {insight}")
        
        # Insight categories
        st.subheader("📋 Insight Categories")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Performance Insights:**")
            performance_insights = [i for i in insights if any(keyword in i for keyword in ["Performance", "Strong", "Top Performer"])]
            for insight in performance_insights[:3]:
                st.write(f"• {insight}")
            
            st.write("**Risk Insights:**")
            risk_insights = [i for i in insights if any(keyword in i for keyword in ["Risk", "Alert", "Pattern"])]
            for insight in risk_insights[:3]:
                st.write(f"• {insight}")
        
        with col2:
            st.write("**Anomaly Insights:**")
            anomaly_insights = [i for i in insights if any(keyword in i for keyword in ["Anomaly", "Anomalous", "Driver"])]
            for insight in anomaly_insights[:3]:
                st.write(f"• {insight}")
            
            st.write("**Comparative Insights:**")
            comparative_insights = [i for i in insights if any(keyword in i for keyword in ["Gap", "difference", "variation"])]
            for insight in comparative_insights[:3]:
                st.write(f"• {insight}")
        
        # Insight summary
        st.subheader("📈 Summary & Recommendations")
        
        risk_count = len([i for i in insights if "Risk" in i])
        performance_count = len([i for i in insights if any(keyword in i for keyword in ["Strong", "Performance", "Top"])])
        anomaly_count = len([i for i in insights if "Anomaly" in i])
        
        if risk_count > performance_count:
            st.warning("⚠️ **Risk-Focused Analysis**: The portfolio shows several risk indicators that require attention")
        elif performance_count > risk_count:
            st.success("💪 **Performance-Focused Analysis**: The portfolio shows strong performance indicators")
        else:
            st.info("⚖️ **Balanced Analysis**: The portfolio shows mixed signals requiring detailed review")
        
        if anomaly_count > 0:
            st.info(f"🔍 **{anomaly_count} anomaly-related insights** detected - investigate unusual patterns")
        
        # Add export functionality for AI insights
        st.divider()
        insights_data = {
            'insights': insights,
            'summary': {
                'risk_count': risk_count,
                'performance_count': performance_count,
                'anomaly_count': anomaly_count
            }
        }
        add_export_section('ai_insights', insights_data, key_namespace='insights')
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        st.error(f"Error generating AI insights: {str(e)}")

def show_pattern_analysis():
    """
    Show pattern analysis and forecasting signals
    """
    try:
        st.subheader("📊 Pattern Analysis & Forecasting Signals")
        st.markdown("Advanced pattern recognition and trend analysis")
        
        # Pattern analysis summary
        st.write("**Available Pattern Analysis:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **🔍 Current Capabilities:**
            - Financial ratio pattern detection
            - Risk pattern identification
            - Anomaly pattern analysis
            - Comparative performance patterns
            """)
        
        with col2:
            st.info("""
            **🚀 Coming Soon:**
            - Time-series trend forecasting
            - Seasonal pattern detection
            - Market cycle analysis
            - Predictive risk modeling
            """)
        
        # Basic pattern statistics
        if st.session_state.company_data:
            st.subheader("📈 Current Pattern Statistics")
            
            company_count = len(st.session_state.company_data)
            total_metrics = 0
            
            for company_data in st.session_state.company_data.values():
                metrics = company_data.get('financial_metrics', {})
                total_metrics += len([v for v in metrics.values() if v is not None])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Companies Analyzed", company_count)
            
            with col2:
                st.metric("Total Data Points", total_metrics)
            
            with col3:
                avg_metrics = total_metrics / company_count if company_count > 0 else 0
                st.metric("Avg Metrics per Company", f"{avg_metrics:.1f}")
            
            # Pattern complexity indicator
            if company_count >= 3 and avg_metrics >= 5:
                st.success("✅ **Sufficient Data Complexity**: Advanced pattern analysis available")
            elif company_count >= 2:
                st.warning("⚠️ **Moderate Data Complexity**: Basic pattern analysis available")
            else:
                st.info("ℹ️ **Limited Data Complexity**: Upload more companies for enhanced pattern analysis")
        
        # Future enhancements preview
        st.subheader("🔮 Advanced Pattern Recognition Preview")
        
        st.markdown("""
        **Future enhancements will include:**
        
        1. **📈 Time-Series Forecasting**
           - Revenue and profit trend predictions
           - Seasonal adjustment analysis
           - Growth trajectory modeling
        
        2. **🔄 Cycle Analysis**
           - Business cycle pattern detection
           - Market timing indicators
           - Economic correlation analysis
        
        3. **🎯 Predictive Risk Modeling**
           - Early warning system for financial distress
           - Probability scoring for various risk scenarios
           - Dynamic risk threshold adjustments
        
        4. **🤖 Advanced ML Patterns**
           - Deep learning pattern recognition
           - Ensemble model predictions
           - Real-time pattern monitoring
        """)
        
    except Exception as e:
        logger.error(f"Error in pattern analysis: {str(e)}")
        st.error(f"Error in pattern analysis: {str(e)}")

def show_forecasting_analysis():
    """
    Show time-series forecasting analysis
    """
    try:
        st.subheader("📈 Time-Series Forecasting & Trend Prediction")
        st.markdown("Advanced forecasting models for financial metrics prediction and growth analysis")
        
        if not st.session_state.company_data:
            st.info("""
            **🔮 Time-Series Forecasting Capabilities:**
            - **ARIMA Models**: Sophisticated time-series modeling for accurate predictions
            - **Trend Analysis**: Linear and non-linear growth trajectory analysis  
            - **Scenario Modeling**: Conservative, moderate, and optimistic growth scenarios
            - **Confidence Intervals**: Statistical uncertainty quantification (80% and 95%)
            - **Growth Metrics**: CAGR calculations and performance projections
            - **Model Diagnostics**: R² scores and fit quality assessment
            
            Upload company data to unlock advanced forecasting capabilities.
            """)
            return
        
        # Forecasting controls
        st.subheader("🎛️ Forecasting Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            forecast_metric = st.selectbox(
                "选择要预测的指标",
                ['revenue', 'profit', 'total_assets', 'operating_income', 'net_income'],
                key="insights_forecast_metric_selector_main",
                help="选择用于时间序列预测的财务指标"
            )

        with col2:
            forecast_periods = st.selectbox(
                "Forecast Periods",
                [6, 12, 18, 24],
                index=1,
                key="insights_forecast_periods_selector_main",
                help="Number of future periods to forecast (months)"
            )

        with col3:
            include_scenarios = st.checkbox(
                "Generate Scenarios",
                value=True,
                key="insights_forecast_scenarios_checkbox_main",
                help="Include conservative, moderate, and optimistic scenarios"
            )
        
        # Generate forecasts
        if st.button("🚀 Generate Forecasts", type="primary"):
            with st.spinner("Generating advanced time-series forecasts..."):
                
                # Prepare time series data
                time_series_df = st.session_state.forecasting_engine.prepare_time_series_data(
                    st.session_state.company_data, forecast_metric
                )
                
                if time_series_df is None or len(time_series_df) == 0:
                    st.warning(f"Insufficient data for {forecast_metric} forecasting. Need historical data for analysis.")
                    return
                
                # Generate forecasts for each company
                forecasts = []
                companies = time_series_df['company'].unique()
                
                forecast_progress = st.progress(0)
                status_text = st.empty()
                
                for i, company in enumerate(companies):
                    status_text.text(f"Forecasting {company}...")
                    
                    forecast = st.session_state.forecasting_engine.forecast_metric(
                        time_series_df, company, forecast_metric, forecast_periods
                    )
                    
                    if forecast:
                        forecasts.append(forecast)
                    
                    forecast_progress.progress((i + 1) / len(companies))
                
                status_text.text("Forecasting complete!")
                
                if not forecasts:
                    st.error("Unable to generate forecasts. Please check your data and try again.")
                    return
                
                # Store forecasts in session state
                st.session_state.forecasts = forecasts
                
                # Generate insights
                forecast_insights = st.session_state.forecasting_engine.generate_forecast_insights(forecasts)
                forecast_summary = st.session_state.forecasting_viz.create_forecast_summary_cards(forecasts)
                
                # Display results
                st.success(f"✅ Successfully generated forecasts for {len(forecasts)} companies!")
                
                # Forecast insights panel
                st.session_state.forecasting_viz.display_forecast_insights_panel(
                    forecast_insights, forecast_summary
                )
        
        # Display existing forecasts if available
        if hasattr(st.session_state, 'forecasts') and st.session_state.forecasts:
            forecasts = st.session_state.forecasts
            
            st.subheader("📊 Forecast Visualizations")
            
            # Multi-company dashboard
            dashboard_chart = st.session_state.forecasting_viz.create_multi_company_forecast_dashboard(forecasts)
            if dashboard_chart:
                st.plotly_chart(dashboard_chart, use_container_width=True, key="forecast_dashboard_chart")

            # Growth trajectory comparison
            growth_chart = st.session_state.forecasting_viz.create_growth_trajectory_comparison(forecasts)
            if growth_chart:
                st.plotly_chart(growth_chart, use_container_width=True, key="growth_trajectory_chart")

            # Model performance metrics
            performance_chart = st.session_state.forecasting_viz.create_forecast_accuracy_metrics(forecasts)
            if performance_chart:
                st.plotly_chart(performance_chart, use_container_width=True, key="forecast_performance_chart")
            
            # Individual company analysis
            st.subheader("🏢 Individual Company Forecasts")
            
            selected_company = st.selectbox(
                "Select Company for Detailed Analysis",
                [f['company'] for f in forecasts],
                key="insights_forecast_company_selector_main"
            )
            
            if selected_company:
                company_forecast = next((f for f in forecasts if f['company'] == selected_company), None)
                
                if company_forecast:
                    # Generate scenarios if requested
                    scenarios = None
                    if include_scenarios:
                        scenarios = st.session_state.forecasting_engine.generate_scenario_analysis(company_forecast)
                    
                    # Create detailed visualization
                    detailed_chart = st.session_state.forecasting_engine.create_forecast_visualization(
                        company_forecast, scenarios
                    )
                    
                    if detailed_chart:
                        st.plotly_chart(detailed_chart, use_container_width=True, key=f"detailed_forecast_chart_{selected_company}")

                    # Scenario analysis
                    if scenarios:
                        scenario_chart = st.session_state.forecasting_viz.create_scenario_analysis_chart(
                            company_forecast, scenarios
                        )
                        if scenario_chart:
                            st.plotly_chart(scenario_chart, use_container_width=True, key=f"scenario_analysis_chart_{selected_company}")
                    
                    # Detailed metrics
                    with st.expander(f"📈 Detailed Forecast Metrics - {selected_company}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🎯 Growth Analysis:**")
                            growth_analysis = company_forecast.get('growth_analysis', {})
                            
                            forecast_cagr = growth_analysis.get('forecast_cagr', 0)
                            st.metric("Forecast CAGR", f"{forecast_cagr:.1f}%")
                            
                            recent_growth = growth_analysis.get('recent_growth_rate', 0)
                            st.metric("Recent Growth Rate", f"{recent_growth:.1f}%")
                            
                            if 'trend_slope' in growth_analysis:
                                trend_slope = growth_analysis['trend_slope']
                                st.metric("Trend Slope", f"{trend_slope:.3f}")
                        
                        with col2:
                            st.write("**🔬 Model Diagnostics:**")
                            diagnostics = company_forecast.get('model_diagnostics', {})
                            
                            model_type = company_forecast.get('model_type', 'Unknown')
                            st.write(f"**Model Type**: {model_type}")
                            
                            if 'r_squared' in diagnostics:
                                r_squared = diagnostics['r_squared']
                                st.metric("Model Fit (R²)", f"{r_squared:.3f}")
                            
                            data_points = diagnostics.get('data_points', 0)
                            st.metric("Data Points Used", data_points)
                            
                            if 'aic' in diagnostics:
                                aic = diagnostics['aic']
                                st.write(f"**AIC Score**: {aic:.2f}")
                    
                    # Scenario comparison table
                    if scenarios:
                        with st.expander("📊 Scenario Comparison Analysis"):
                            scenario_data = []
                            for scenario_name, scenario_info in scenarios.items():
                                scenario_data.append({
                                    'Scenario': scenario_info['name'],
                                    'CAGR': f"{scenario_info['cagr']:.1f}%",
                                    'Total Growth': f"{scenario_info['total_growth']:.1f}%",
                                    'Final Value': f"{scenario_info['values'][-1]:,.0f}" if scenario_info['values'] else "N/A"
                                })
                            
                            scenario_df = pd.DataFrame(scenario_data)
                            st.dataframe(scenario_df, use_container_width=True)
        
        # Forecasting tips and information
        with st.expander("💡 Forecasting Methodology & Tips"):
            st.markdown("""
            **🔬 Forecasting Models Used:**
            
            1. **ARIMA (AutoRegressive Integrated Moving Average)**
               - Advanced time-series modeling for capturing trends and patterns
               - Automatic parameter selection for optimal model fit
               - Suitable for data with trends and seasonal patterns
            
            2. **Linear Trend Analysis**
               - Fallback method for simpler trend patterns
               - Uses linear regression for trend extrapolation
               - Good baseline for growth trajectory analysis
            
            **📊 Confidence Intervals:**
            - **80% Confidence**: Higher probability range for forecasts
            - **95% Confidence**: Wider range accounting for greater uncertainty
            
            **🎯 Scenario Analysis:**
            - **Conservative**: 70% of base forecast with reduced volatility
            - **Moderate**: Base forecast with normal volatility
            - **Optimistic**: 130% of base forecast with increased volatility
            
            **⚠️ Important Notes:**
            - Forecasts are based on historical patterns and may not predict unprecedented events
            - Longer forecast periods have higher uncertainty
            - Consider external factors (market conditions, regulatory changes) not captured in the model
            - Use forecasts as guidance, not absolute predictions
            """)
        
        # Add export functionality for forecasts
        if hasattr(st.session_state, 'forecasts') and st.session_state.forecasts:
            st.divider()
            add_export_section('forecasting', st.session_state.forecasts, key_namespace='insights')
        
    except Exception as e:
        logger.error(f"Error in forecasting analysis: {str(e)}")
        st.error(f"Error in forecasting analysis: {str(e)}")

# Call the main function to render the page when executed by Streamlit's multipage system
if __name__ == "__main__" or True:  # Always execute when this page is loaded
    show_insights_page()