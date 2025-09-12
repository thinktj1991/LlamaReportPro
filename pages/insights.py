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
from utils.state import init_state, init_processors
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_insights_page():
    """
    Main insights analysis page
    """
    try:
        st.header("🤖 AI-Powered Insights & Analysis")
        st.markdown("Advanced pattern recognition, anomaly detection, and automated intelligence")
        
        # Initialize session state safely
        init_state()
        
        if not st.session_state.company_data:
            st.warning("No company data available. Please process documents first in 'Upload & Process'.")
            st.info("Once you have company data, this page will provide:")
            st.markdown("""
            - 🔍 **Anomaly Detection**: ML-powered identification of unusual financial patterns
            - ⚠️ **Risk Analysis**: Systematic assessment of financial risks and red flags  
            - 🤖 **AI Insights**: Automated generation of business intelligence
            - 📊 **Pattern Recognition**: Advanced trend and relationship analysis
            """)
            return
        
        # Initialize insights engine
        if not hasattr(st.session_state, 'insights_engine') or st.session_state.insights_engine is None:
            st.session_state.insights_engine = InsightsEngine()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Anomaly Detection", "⚠️ Risk Analysis", 
            "🤖 AI Insights", "📊 Pattern Analysis"
        ])
        
        with tab1:
            show_anomaly_detection()
        
        with tab2:
            show_risk_analysis()
        
        with tab3:
            show_ai_insights()
        
        with tab4:
            show_pattern_analysis()
            
    except Exception as e:
        logger.error(f"Error in insights page: {str(e)}")
        st.error("Error loading insights page. Please refresh and try again.")
        st.exception(e)

def show_anomaly_detection():
    """
    Show anomaly detection analysis
    """
    try:
        st.subheader("🔍 Financial Anomaly Detection")
        st.markdown("Machine learning-powered detection of unusual financial patterns and outliers")
        
        # Run anomaly detection
        with st.spinner("Analyzing financial data for anomalies..."):
            anomalies = st.session_state.insights_engine.detect_financial_anomalies(
                st.session_state.company_data
            )
        
        if not anomalies.get('anomalies'):
            st.success("✅ No significant anomalies detected in the financial data")
            st.info(anomalies.get('analysis', 'All companies show normal financial patterns'))
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
            st.plotly_chart(anomaly_chart, use_container_width=True)
        
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
            st.plotly_chart(risk_heatmap, use_container_width=True)
        
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

# Call the main function to render the page when executed by Streamlit's multipage system
if __name__ == "__main__" or True:  # Always execute when this page is loaded
    show_insights_page()