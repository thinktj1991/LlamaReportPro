"""
Comprehensive Data Export Page

This page provides centralized export functionality for all analysis results:
- Export status overview
- Batch export capabilities
- Format selection and customization
- Download management
"""

import streamlit as st
import pandas as pd
from utils.export_ui import ExportUI
from utils.state import init_state
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_export_page():
    """
    Main export page
    """
    try:
        st.header("📁 数据导出中心")
        st.markdown("所有分析结果和报告的集中导出中心")
        
        # Initialize session state
        init_state()
        
        # Initialize export UI
        if not hasattr(st.session_state, 'export_ui') or st.session_state.export_ui is None:
            st.session_state.export_ui = ExportUI()
        
        export_ui = st.session_state.export_ui
        
        # Check overall data availability
        has_any_data = (
            hasattr(st.session_state, 'company_data') and bool(st.session_state.company_data) or
            hasattr(st.session_state, 'comparison_results') and bool(st.session_state.comparison_results) or
            hasattr(st.session_state, 'forecasts') and bool(st.session_state.forecasts)
        )
        
        if not has_any_data:
            st.warning("⚠️ 没有可用于导出的分析数据")
            st.info("""
            **要启用数据导出，请：**
            
            1. 📄 **上传与处理** 在上传与处理页面上传文档
            2. 📊 **生成分析** 使用各种分析模块
            3. 🔍 **运行对比** 在公司对比页面进行对比
            4. 📈 **创建AI预测** 在AI洞察页面的预测标签中生成预测
            
            一旦您有了分析结果，请返回此处以多种格式导出您的数据。
            """)
            
            # Show capabilities preview
            st.subheader("📋 导出功能")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **📊 支持的格式：**
                - **CSV**: 原始数据和计算结果
                - **Excel**: 格式化的工作簿，包含多个工作表
                - **PDF**: 专业分析报告
                """)
            
            with col2:
                st.info("""
                **📈 可用数据类型：**
                - 财务比率分析
                - 多公司对比
                - 时间序列预测
                - AI洞察和异常检测
                """)
            
            return
        
        # Main export interface
        tab1, tab2, tab3 = st.tabs(["📊 导出状态", "📦 批量导出", "🔧 单独导出"])
        
        with tab1:
            show_export_status_tab(export_ui)
        
        with tab2:
            show_batch_export_tab(export_ui)
        
        with tab3:
            show_individual_exports_tab(export_ui)
        
        # Export tips and information
        with st.expander("💡 导出提示与信息"):
            st.markdown("""
            **📝 导出格式指南：**
            
            **CSV (逗号分隔值)：**
            - 适用于：在其他工具中进行数据分析（Excel、R、Python）
            - 包含：原始数值数据和计算结果
            - 大小：最小文件大小
            - Use case: Further analysis, database imports
            
            **Excel (XLSX):**
            - 适用于：格式化报告和演示
            - 包含：多个工作表、格式化表格、基本图表
            - 大小：中等文件大小
            - Use case: Business reports, stakeholder presentations
            
            **PDF (Portable Document Format):**
            - 适用于：最终报告和文档
            - 包含：专业布局和分析论述
            - 大小：最大文件大小（包含文本和布局）
            - Use case: Executive summaries, formal documentation
            
            **💡 Best Practices:**
            - Use **CSV** for raw data analysis
            - Use **Excel** for formatted business reports
            - Use **PDF** for final presentation documents
            - Include metadata for better data tracking
            - Use descriptive filenames with timestamps
            """)
    
    except Exception as e:
        logger.error(f"Error in export page: {str(e)}")
        st.error("Error loading export page. Please refresh and try again.")
        st.exception(e)

def show_export_status_tab(export_ui: ExportUI):
    """
    Show export status and data availability
    """
    try:
        # Available data types
        data_types = ['ratios', 'comparison', 'forecasting', 'insights']
        export_ui.show_export_status(data_types)
        
        # Quick statistics
        st.subheader("📈 Data Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            company_count = len(st.session_state.company_data) if hasattr(st.session_state, 'company_data') and st.session_state.company_data else 0
            st.metric("Companies Processed", company_count)
        
        with col2:
            forecast_count = len(st.session_state.forecasts) if hasattr(st.session_state, 'forecasts') and st.session_state.forecasts else 0
            st.metric("Forecasts Generated", forecast_count)
        
        with col3:
            comparison_available = 1 if hasattr(st.session_state, 'comparison_results') and st.session_state.comparison_results else 0
            st.metric("Comparison Analysis", comparison_available)
        
        with col4:
            total_data_points = company_count + forecast_count + comparison_available
            st.metric("Total Data Points", total_data_points)
        
        # Recent activity
        if hasattr(st.session_state, 'processing_history'):
            st.subheader("📅 Recent Activity")
            history_df = pd.DataFrame(st.session_state.processing_history)
            if not history_df.empty:
                st.dataframe(history_df.tail(5), use_container_width=True)
            else:
                st.info("No recent processing activity")
    
    except Exception as e:
        logger.error(f"Error showing export status: {str(e)}")
        st.error(f"Error displaying export status: {str(e)}")

def show_batch_export_tab(export_ui: ExportUI):
    """
    Show batch export functionality
    """
    try:
        st.markdown("Export multiple analysis modules in a single comprehensive report")
        
        # Batch export panel
        export_ui.show_batch_export_panel()
        
        # Batch export benefits
        st.subheader("🎯 批量导出优势")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("""
            **✅ Comprehensive Reports:**
            - All analysis modules in one file
            - Consistent formatting and styling
            - Executive summary included
            - Professional presentation ready
            """)
        
        with col2:
            st.info("""
            **⚡ Efficiency Benefits:**
            - Single download operation
            - Reduced file management
            - Complete analysis package
            - Streamlined sharing process
            """)
    
    except Exception as e:
        logger.error(f"Error showing batch export: {str(e)}")
        st.error(f"Error displaying batch export: {str(e)}")

def show_individual_exports_tab(export_ui: ExportUI):
    """
    Show individual export options for each data type
    """
    try:
        st.markdown("Export specific analysis modules individually")
        
        # Financial Ratios Export
        if hasattr(st.session_state, 'company_data') and st.session_state.company_data:
            st.subheader("📊 Financial Ratios Analysis")
            export_ui.show_export_panel('ratios', st.session_state.company_data)
            st.divider()
        
        # Company Comparison Export
        if hasattr(st.session_state, 'comparison_results') and st.session_state.comparison_results:
            st.subheader("🏢 Company Comparison Analysis")
            export_ui.show_export_panel('comparison', st.session_state.comparison_results)
            st.divider()
        
        # Forecasting Export
        if hasattr(st.session_state, 'forecasts') and st.session_state.forecasts:
            st.subheader("📈 Time-Series Forecasting")
            export_ui.show_export_panel('forecasting', st.session_state.forecasts)
            st.divider()
        
        # AI Insights Export
        if hasattr(st.session_state, 'company_data') and st.session_state.company_data:
            st.subheader("🤖 AI Insights & Analysis")
            insights_data = {'company_data': st.session_state.company_data}
            export_ui.show_export_panel('insights', insights_data, ['csv', 'excel', 'pdf'])
        
        # No data message
        if not any([
            hasattr(st.session_state, 'company_data') and st.session_state.company_data,
            hasattr(st.session_state, 'comparison_results') and st.session_state.comparison_results,
            hasattr(st.session_state, 'forecasts') and st.session_state.forecasts
        ]):
            st.info("No individual analysis results available for export")
    
    except Exception as e:
        logger.error(f"Error showing individual exports: {str(e)}")
        st.error(f"Error displaying individual exports: {str(e)}")

# Call the main function to render the page when executed by Streamlit's multipage system
if __name__ == "__main__" or True:  # Always execute when this page is loaded
    show_export_page()