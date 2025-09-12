"""
Export UI Components

This module provides Streamlit UI components for data export functionality:
- Export format selection
- Download buttons and links
- Export progress indicators
- Export configuration panels
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime
from utils.export_engine import DataExportEngine

# Configure logging
logger = logging.getLogger(__name__)

class ExportUI:
    """
    Streamlit UI components for data export functionality
    """
    
    def __init__(self):
        # Initialize export engine
        if not hasattr(st.session_state, 'export_engine') or st.session_state.export_engine is None:
            st.session_state.export_engine = DataExportEngine()
        
        self.export_engine = st.session_state.export_engine
        
        # Export configurations
        self.export_configs = {
            'ratios': {
                'name': 'Financial Ratios Analysis',
                'icon': '📊',
                'description': 'Export calculated financial ratios and analysis results'
            },
            'comparison': {
                'name': 'Company Comparison',
                'icon': '🏢',
                'description': 'Export multi-company comparison and industry benchmarks'
            },
            'forecasting': {
                'name': 'Time-Series Forecasts',
                'icon': '📈',
                'description': 'Export forecasting results and model diagnostics'
            },
            'insights': {
                'name': 'AI Insights & Analysis',
                'icon': '🤖',
                'description': 'Export AI-generated insights and anomaly detection results'
            },
            'comprehensive': {
                'name': 'Comprehensive Report',
                'icon': '📄',
                'description': 'Export complete analysis including all modules'
            }
        }
    
    def show_export_panel(self, data_type: str, data: Any, 
                         available_formats: List[str] = None) -> None:
        """
        Show export panel with format selection and download options
        """
        try:
            if available_formats is None:
                available_formats = ['csv', 'excel', 'pdf']
            
            config = self.export_configs.get(data_type, {})
            icon = config.get('icon', '📁')
            name = config.get('name', 'Data Export')
            description = config.get('description', 'Export analysis results')
            
            st.subheader(f"{icon} Export {name}")
            st.markdown(f"*{description}*")
            
            # Format selection
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                format_options = []
                format_labels = []
                
                for fmt in available_formats:
                    if fmt in self.export_engine.supported_formats:
                        format_info = self.export_engine.supported_formats[fmt]
                        format_options.append(fmt)
                        format_labels.append(f"{format_info['name']} (.{format_info['extension']})")
                
                if not format_options:
                    st.error("No export formats available")
                    return
                
                selected_format = st.selectbox(
                    "Export Format",
                    options=format_options,
                    format_func=lambda x: format_labels[format_options.index(x)] if x in format_options else x,
                    help="Choose the export format for your data"
                )
            
            with col2:
                include_metadata = st.checkbox(
                    "Include Metadata",
                    value=True,
                    help="Include analysis metadata and timestamps"
                )
            
            with col3:
                custom_filename = st.text_input(
                    "Custom Filename",
                    value="",
                    help="Optional custom filename (without extension)"
                )
            
            # Export button
            if st.button(f"🚀 Export as {selected_format.upper()}", type="primary"):
                self._handle_export(data_type, data, selected_format, custom_filename, include_metadata)
        
        except Exception as e:
            logger.error(f"Error showing export panel: {str(e)}")
            st.error(f"Error displaying export options: {str(e)}")
    
    def show_quick_export_buttons(self, data_type: str, data: Any) -> None:
        """
        Show quick export buttons for common formats
        """
        try:
            config = self.export_configs.get(data_type, {})
            icon = config.get('icon', '📁')
            
            st.markdown("**Quick Export:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📄 CSV"):
                    self._handle_export(data_type, data, 'csv')
            
            with col2:
                if st.button(f"📊 Excel"):
                    self._handle_export(data_type, data, 'excel')
            
            with col3:
                if st.button(f"📋 PDF"):
                    self._handle_export(data_type, data, 'pdf')
        
        except Exception as e:
            logger.error(f"Error showing quick export buttons: {str(e)}")
            st.error(f"Error displaying quick export: {str(e)}")
    
    def show_export_status(self, data_types: List[str]) -> None:
        """
        Show export status and available data
        """
        try:
            st.subheader("📋 Export Status")
            
            export_data = []
            for data_type in data_types:
                config = self.export_configs.get(data_type, {})
                
                # Check if data is available
                data_available = self._check_data_availability(data_type)
                
                export_data.append({
                    'Module': config.get('name', data_type.title()),
                    'Icon': config.get('icon', '📁'),
                    'Status': '✅ Ready' if data_available else '⏳ No Data',
                    'Formats': 'CSV, Excel, PDF' if data_available else 'N/A'
                })
            
            # Display as table
            status_df = pd.DataFrame(export_data)
            st.dataframe(status_df, use_container_width=True, hide_index=True)
            
            # Summary
            ready_count = sum(1 for item in export_data if '✅' in item['Status'])
            total_count = len(export_data)
            
            if ready_count == total_count:
                st.success(f"🎉 All {total_count} modules ready for export!")
            elif ready_count > 0:
                st.info(f"📊 {ready_count} of {total_count} modules ready for export")
            else:
                st.warning("⚠️ No data available for export. Please process some documents first.")
        
        except Exception as e:
            logger.error(f"Error showing export status: {str(e)}")
            st.error(f"Error displaying export status: {str(e)}")
    
    def _handle_export(self, data_type: str, data: Any, format_type: str, 
                      custom_filename: str = "", include_metadata: bool = True) -> None:
        """
        Handle the export process
        """
        try:
            with st.spinner(f"Exporting {data_type} as {format_type.upper()}..."):
                
                # Generate filename
                if custom_filename:
                    filename = custom_filename
                else:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{data_type}_analysis_{timestamp}"
                
                # Add metadata if requested
                if include_metadata:
                    enhanced_data = self._add_metadata(data, data_type)
                else:
                    enhanced_data = data
                
                # Export based on data type and format
                if data_type == 'ratios':
                    export_bytes = self.export_engine.export_financial_ratios(enhanced_data, format_type)
                elif data_type == 'comparison':
                    export_bytes = self.export_engine.export_company_comparison(enhanced_data, format_type)
                elif data_type == 'forecasting':
                    export_bytes = self.export_engine.export_forecasts(enhanced_data, format_type)
                else:
                    # Generic export
                    if format_type == 'csv':
                        export_bytes = self.export_engine.export_to_csv(enhanced_data, filename)
                    elif format_type == 'excel':
                        export_bytes = self.export_engine.export_to_excel(enhanced_data, filename)
                    elif format_type == 'pdf':
                        export_bytes = self.export_engine.export_to_pdf(enhanced_data, filename)
                    else:
                        raise ValueError(f"Unsupported format: {format_type}")
                
                # Create download
                format_info = self.export_engine.supported_formats[format_type]
                full_filename = f"{filename}.{format_info['extension']}"
                
                st.download_button(
                    label=f"📥 Download {format_type.upper()} File",
                    data=export_bytes,
                    file_name=full_filename,
                    mime=format_info['mime'],
                    type="primary"
                )
                
                st.success(f"✅ {data_type.title()} exported successfully as {format_type.upper()}!")
                st.info(f"📁 File: {full_filename} ({len(export_bytes):,} bytes)")
        
        except Exception as e:
            logger.error(f"Error handling export: {str(e)}")
            st.error(f"Export failed: {str(e)}")
    
    def _check_data_availability(self, data_type: str) -> bool:
        """
        Check if data is available for export
        """
        try:
            if data_type == 'ratios':
                return hasattr(st.session_state, 'company_data') and bool(st.session_state.company_data)
            elif data_type == 'comparison':
                return hasattr(st.session_state, 'comparison_results') and bool(st.session_state.comparison_results)
            elif data_type == 'forecasting':
                return hasattr(st.session_state, 'forecasts') and bool(st.session_state.forecasts)
            elif data_type == 'insights':
                return hasattr(st.session_state, 'company_data') and bool(st.session_state.company_data)
            else:
                return False
        
        except Exception as e:
            logger.warning(f"Error checking data availability: {str(e)}")
            return False
    
    def _add_metadata(self, data: Any, data_type: str) -> Any:
        """
        Add metadata to export data
        """
        try:
            metadata = {
                'export_timestamp': datetime.now().isoformat(),
                'data_type': data_type,
                'system_version': '1.0.0',
                'analysis_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            if isinstance(data, dict):
                enhanced_data = data.copy()
                enhanced_data['_metadata'] = metadata
                return enhanced_data
            elif isinstance(data, list):
                return data  # Metadata added differently for lists
            else:
                return data
        
        except Exception as e:
            logger.warning(f"Error adding metadata: {str(e)}")
            return data
    
    def show_batch_export_panel(self) -> None:
        """
        Show panel for batch export of multiple data types
        """
        try:
            st.subheader("📦 Batch Export")
            st.markdown("Export multiple analysis modules in a single operation")
            
            # Data type selection
            available_types = []
            for data_type in ['ratios', 'comparison', 'forecasting', 'insights']:
                if self._check_data_availability(data_type):
                    available_types.append(data_type)
            
            if not available_types:
                st.warning("No data available for batch export")
                return
            
            selected_types = st.multiselect(
                "Select Data Types to Export",
                options=available_types,
                default=available_types,
                format_func=lambda x: self.export_configs[x]['name']
            )
            
            if not selected_types:
                st.info("Please select at least one data type to export")
                return
            
            # Format selection
            batch_format = st.selectbox(
                "Export Format",
                options=['excel', 'pdf'],
                format_func=lambda x: self.export_engine.supported_formats[x]['name'],
                help="Batch export supports Excel (multiple sheets) and PDF (comprehensive report)"
            )
            
            # Export button
            if st.button("🚀 Start Batch Export", type="primary"):
                self._handle_batch_export(selected_types, batch_format)
        
        except Exception as e:
            logger.error(f"Error showing batch export panel: {str(e)}")
            st.error(f"Error displaying batch export: {str(e)}")
    
    def _handle_batch_export(self, data_types: List[str], format_type: str) -> None:
        """
        Handle batch export process
        """
        try:
            with st.spinner(f"Preparing batch export as {format_type.upper()}..."):
                
                # Collect all data
                batch_data = {}
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, data_type in enumerate(data_types):
                    status_text.text(f"Collecting {data_type} data...")
                    
                    if data_type == 'ratios' and hasattr(st.session_state, 'company_data'):
                        batch_data['financial_ratios'] = st.session_state.company_data
                    elif data_type == 'comparison' and hasattr(st.session_state, 'comparison_results'):
                        batch_data['company_comparison'] = st.session_state.comparison_results
                    elif data_type == 'forecasting' and hasattr(st.session_state, 'forecasts'):
                        batch_data['time_series_forecasts'] = st.session_state.forecasts
                    elif data_type == 'insights':
                        batch_data['ai_insights'] = {'summary': 'AI insights data collected'}
                    
                    progress_bar.progress((i + 1) / len(data_types))
                
                status_text.text("Generating export file...")
                
                # Generate batch export
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"comprehensive_analysis_{timestamp}"
                
                if format_type == 'excel':
                    export_bytes = self.export_engine.export_to_excel(batch_data, filename, 'comprehensive')
                elif format_type == 'pdf':
                    export_bytes = self.export_engine.export_to_pdf(batch_data, filename, 'comprehensive')
                else:
                    raise ValueError(f"Unsupported batch format: {format_type}")
                
                # Create download
                format_info = self.export_engine.supported_formats[format_type]
                full_filename = f"{filename}.{format_info['extension']}"
                
                st.download_button(
                    label=f"📥 Download Comprehensive {format_type.upper()} Report",
                    data=export_bytes,
                    file_name=full_filename,
                    mime=format_info['mime'],
                    type="primary"
                )
                
                progress_bar.progress(1.0)
                status_text.text("Export complete!")
                
                st.success(f"✅ Batch export completed successfully!")
                st.info(f"📁 File: {full_filename} ({len(export_bytes):,} bytes)")
                st.info(f"📊 Included: {', '.join([self.export_configs[dt]['name'] for dt in data_types])}")
        
        except Exception as e:
            logger.error(f"Error handling batch export: {str(e)}")
            st.error(f"Batch export failed: {str(e)}")

def add_export_section(data_type: str, data: Any, 
                      available_formats: List[str] = None) -> None:
    """
    Convenience function to add export section to any page
    """
    try:
        if not hasattr(st.session_state, 'export_ui') or st.session_state.export_ui is None:
            st.session_state.export_ui = ExportUI()
        
        export_ui = st.session_state.export_ui
        
        with st.expander("📁 Export Data", expanded=False):
            export_ui.show_export_panel(data_type, data, available_formats)
    
    except Exception as e:
        logger.error(f"Error adding export section: {str(e)}")
        st.error(f"Error adding export functionality: {str(e)}")

def add_quick_export_buttons(data_type: str, data: Any) -> None:
    """
    Convenience function to add quick export buttons
    """
    try:
        if not hasattr(st.session_state, 'export_ui') or st.session_state.export_ui is None:
            st.session_state.export_ui = ExportUI()
        
        export_ui = st.session_state.export_ui
        export_ui.show_quick_export_buttons(data_type, data)
    
    except Exception as e:
        logger.error(f"Error adding quick export buttons: {str(e)}")
        st.error(f"Error adding export buttons: {str(e)}")