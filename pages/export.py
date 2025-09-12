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
        st.header("📁 Data Export Center")
        st.markdown("Centralized export hub for all analysis results and reports")
        
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
            st.warning("⚠️ No analysis data available for export")
            st.info("""
            **To enable data export, please:**
            
            1. 📄 **Upload & Process** documents in the Upload & Process page
            2. 📊 **Generate Analysis** using the various analysis modules
            3. 🔍 **Run Comparisons** in the Company Comparison page
            4. 📈 **Create Forecasts** in the AI Insights forecasting tab
            
            Once you have analysis results, return here to export your data in multiple formats.
            """)
            
            # Show capabilities preview
            st.subheader("📋 Export Capabilities")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **📊 Supported Formats:**
                - **CSV**: Raw data and calculations
                - **Excel**: Formatted workbooks with multiple sheets
                - **PDF**: Professional analysis reports
                """)
            
            with col2:
                st.info("""
                **📈 Available Data Types:**
                - Financial ratio analysis
                - Multi-company comparisons
                - Time-series forecasts
                - AI insights and anomalies
                """)
            
            return
        
        # Main export interface
        tab1, tab2, tab3 = st.tabs(["📊 Export Status", "📦 Batch Export", "🔧 Individual Exports"])
        
        with tab1:
            show_export_status_tab(export_ui)
        
        with tab2:
            show_batch_export_tab(export_ui)
        
        with tab3:
            show_individual_exports_tab(export_ui)
        
        # Export tips and information
        with st.expander("💡 Export Tips & Information"):
            st.markdown("""
            **📝 Export Format Guidelines:**
            
            **CSV (Comma Separated Values):**
            - Best for: Data analysis in other tools (Excel, R, Python)
            - Contains: Raw numerical data and calculations
            - Size: Smallest file size
            - Use case: Further analysis, database imports
            
            **Excel (XLSX):**
            - Best for: Formatted reports and presentations
            - Contains: Multiple worksheets, formatted tables, basic charts
            - Size: Medium file size
            - Use case: Business reports, stakeholder presentations
            
            **PDF (Portable Document Format):**
            - Best for: Final reports and documentation
            - Contains: Professional layout with analysis narratives
            - Size: Largest file size (includes text and layout)
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
        st.subheader("🎯 Batch Export Benefits")
        
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