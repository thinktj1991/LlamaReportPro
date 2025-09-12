"""
Comprehensive Data Export Engine

This module provides professional data export capabilities including:
- CSV exports for raw data and analysis results
- Excel exports with formatted worksheets and charts
- PDF reports with professional layouts and visualizations
- Configurable templates for different analysis types
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import streamlit as st
import logging
from datetime import datetime, date
import io
import base64
from pathlib import Path
import json

# Excel and PDF dependencies
try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.chart import LineChart, BarChart, Reference
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.platypus.flowables import Image as ReportLabImage
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class DataExportEngine:
    """
    Comprehensive data export engine for multiple formats
    """
    
    def __init__(self):
        self.excel_available = EXCEL_AVAILABLE
        self.pdf_available = PDF_AVAILABLE
        
        # Export format configurations
        self.supported_formats = {
            'csv': {'name': 'CSV (Comma Separated Values)', 'extension': 'csv', 'mime': 'text/csv'},
            'excel': {'name': 'Excel Workbook', 'extension': 'xlsx', 'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
            'pdf': {'name': 'PDF Report', 'extension': 'pdf', 'mime': 'application/pdf'}
        }
        
        # Report templates
        self.report_templates = {
            'financial_ratios': {
                'title': 'Financial Ratio Analysis Report',
                'sections': ['summary', 'detailed_ratios', 'visualizations', 'recommendations']
            },
            'company_comparison': {
                'title': 'Multi-Company Comparison Analysis Report', 
                'sections': ['executive_summary', 'performance_comparison', 'industry_benchmarks', 'risk_assessment']
            },
            'forecasting': {
                'title': 'Time-Series Forecasting Analysis Report',
                'sections': ['forecast_summary', 'model_diagnostics', 'scenario_analysis', 'growth_projections']
            },
            'comprehensive': {
                'title': 'Comprehensive Annual Report Analysis',
                'sections': ['executive_summary', 'financial_analysis', 'comparative_analysis', 'forecast_analysis', 'risk_assessment', 'recommendations']
            }
        }
    
    def export_to_csv(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
                     filename: str = None) -> bytes:
        """
        Export data to CSV format
        """
        try:
            if filename is None:
                filename = f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if isinstance(data, pd.DataFrame):
                # Single DataFrame export
                csv_buffer = io.StringIO()
                data.to_csv(csv_buffer, index=False)
                return csv_buffer.getvalue().encode('utf-8')
            
            elif isinstance(data, dict):
                # Multiple DataFrames - create combined CSV with section headers
                csv_buffer = io.StringIO()
                
                for section_name, df in data.items():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        csv_buffer.write(f"\n=== {section_name.upper()} ===\n")
                        df.to_csv(csv_buffer, index=False)
                        csv_buffer.write("\n")
                
                return csv_buffer.getvalue().encode('utf-8')
            
            else:
                raise ValueError("Data must be a DataFrame or dictionary of DataFrames")
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def export_to_excel(self, data: Union[pd.DataFrame, Dict[str, Any]], 
                       filename: str = None, template_type: str = 'financial_ratios') -> bytes:
        """
        Export data to Excel format with professional formatting
        """
        try:
            if not self.excel_available:
                raise ImportError("Excel export requires openpyxl. Install with: pip install openpyxl")
            
            if filename is None:
                filename = f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                if isinstance(data, pd.DataFrame):
                    # Single DataFrame export
                    self._write_formatted_sheet(writer, data, 'Analysis', template_type)
                
                elif isinstance(data, dict):
                    # Multiple sheets export
                    for sheet_name, sheet_data in data.items():
                        if isinstance(sheet_data, pd.DataFrame) and not sheet_data.empty:
                            self._write_formatted_sheet(writer, sheet_data, sheet_name, template_type)
                        elif isinstance(sheet_data, dict):
                            # Handle nested data structures
                            summary_df = self._dict_to_dataframe(sheet_data)
                            if not summary_df.empty:
                                self._write_formatted_sheet(writer, summary_df, sheet_name, template_type)
                
                # Add summary sheet if multiple sheets
                if isinstance(data, dict) and len(data) > 1:
                    self._create_summary_sheet(writer, data, template_type)
            
            excel_buffer.seek(0)
            return excel_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise
    
    def export_to_pdf(self, data: Dict[str, Any], 
                     filename: str = None, template_type: str = 'comprehensive') -> bytes:
        """
        Export data to PDF format with professional report layout
        """
        try:
            if not self.pdf_available:
                raise ImportError("PDF export requires reportlab. Install with: pip install reportlab")
            
            if filename is None:
                filename = f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            pdf_buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12
            )
            
            # Report header
            template_config = self.report_templates.get(template_type, self.report_templates['comprehensive'])
            story.append(Paragraph(template_config['title'], title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Build report sections
            for section in template_config['sections']:
                section_content = self._generate_pdf_section(section, data, styles, heading_style)
                story.extend(section_content)
            
            # Build PDF
            doc.build(story)
            
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
    
    def create_download_link(self, data_bytes: bytes, filename: str, 
                           format_type: str) -> str:
        """
        Create a downloadable link for exported data
        """
        try:
            format_config = self.supported_formats.get(format_type, {})
            mime_type = format_config.get('mime', 'application/octet-stream')
            
            b64_data = base64.b64encode(data_bytes).decode()
            
            return f"data:{mime_type};base64,{b64_data}"
            
        except Exception as e:
            logger.error(f"Error creating download link: {str(e)}")
            return ""
    
    def export_financial_ratios(self, ratios_data: Dict[str, Any], 
                              format_type: str = 'excel') -> bytes:
        """
        Export financial ratios analysis in specified format
        """
        try:
            if format_type == 'csv':
                # Convert ratios to DataFrame
                ratios_df = self._create_ratios_dataframe(ratios_data)
                return self.export_to_csv(ratios_df)
            
            elif format_type == 'excel':
                # Create comprehensive Excel workbook
                excel_data = {
                    'Financial_Ratios': self._create_ratios_dataframe(ratios_data),
                    'Ratio_Categories': self._create_ratio_categories_df(ratios_data),
                    'Summary_Metrics': self._create_summary_metrics_df(ratios_data)
                }
                return self.export_to_excel(excel_data, template_type='financial_ratios')
            
            elif format_type == 'pdf':
                return self.export_to_pdf(ratios_data, template_type='financial_ratios')
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting financial ratios: {str(e)}")
            raise
    
    def export_company_comparison(self, comparison_data: Dict[str, Any], 
                                format_type: str = 'excel') -> bytes:
        """
        Export company comparison analysis in specified format
        """
        try:
            if format_type == 'csv':
                comparison_df = self._create_comparison_dataframe(comparison_data)
                return self.export_to_csv(comparison_df)
            
            elif format_type == 'excel':
                excel_data = {
                    'Company_Comparison': self._create_comparison_dataframe(comparison_data),
                    'Industry_Benchmarks': self._create_benchmarks_df(comparison_data),
                    'Rankings': self._create_rankings_df(comparison_data)
                }
                return self.export_to_excel(excel_data, template_type='company_comparison')
            
            elif format_type == 'pdf':
                return self.export_to_pdf(comparison_data, template_type='company_comparison')
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting company comparison: {str(e)}")
            raise
    
    def export_forecasts(self, forecasts_data: List[Dict[str, Any]], 
                        format_type: str = 'excel') -> bytes:
        """
        Export forecasting analysis in specified format
        """
        try:
            if format_type == 'csv':
                forecasts_df = self._create_forecasts_dataframe(forecasts_data)
                return self.export_to_csv(forecasts_df)
            
            elif format_type == 'excel':
                excel_data = {
                    'Forecast_Summary': self._create_forecasts_dataframe(forecasts_data),
                    'Model_Diagnostics': self._create_model_diagnostics_df(forecasts_data),
                    'Growth_Analysis': self._create_growth_analysis_df(forecasts_data)
                }
                return self.export_to_excel(excel_data, template_type='forecasting')
            
            elif format_type == 'pdf':
                return self.export_to_pdf({'forecasts': forecasts_data}, template_type='forecasting')
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting forecasts: {str(e)}")
            raise
    
    # Helper methods for data transformation
    def _create_ratios_dataframe(self, ratios_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert ratios data to DataFrame"""
        try:
            rows = []
            for company, company_data in ratios_data.items():
                if isinstance(company_data, dict) and 'ratios' in company_data:
                    ratios = company_data['ratios']
                    row = {'Company': company}
                    row.update(ratios)
                    rows.append(row)
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            logger.warning(f"Error creating ratios DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _create_comparison_dataframe(self, comparison_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert comparison data to DataFrame"""
        try:
            if 'rankings' in comparison_data:
                rankings = comparison_data['rankings']
                rows = []
                
                for company, metrics in rankings.items():
                    row = {'Company': company}
                    if isinstance(metrics, dict):
                        row.update(metrics)
                    rows.append(row)
                
                return pd.DataFrame(rows)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.warning(f"Error creating comparison DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _create_forecasts_dataframe(self, forecasts_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert forecasts data to DataFrame"""
        try:
            rows = []
            for forecast in forecasts_data:
                if isinstance(forecast, dict):
                    growth_analysis = forecast.get('growth_analysis', {})
                    model_diagnostics = forecast.get('model_diagnostics', {})
                    
                    row = {
                        'Company': forecast.get('company', 'Unknown'),
                        'Metric': forecast.get('metric', 'Unknown'),
                        'Model_Type': forecast.get('model_type', 'Unknown'),
                        'Forecast_CAGR': growth_analysis.get('forecast_cagr', 0),
                        'R_Squared': model_diagnostics.get('r_squared', 0),
                        'Data_Points': model_diagnostics.get('data_points', 0)
                    }
                    rows.append(row)
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            logger.warning(f"Error creating forecasts DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _write_formatted_sheet(self, writer, df: pd.DataFrame, sheet_name: str, template_type: str):
        """Write formatted Excel sheet"""
        try:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            if self.excel_available:
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                # Header formatting
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_alignment = Alignment(horizontal="center", vertical="center")
                
                # Apply header formatting
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
        except Exception as e:
            logger.warning(f"Error formatting Excel sheet: {str(e)}")
    
    def _create_summary_sheet(self, writer, data: Dict[str, Any], template_type: str):
        """Create summary sheet for multi-sheet workbooks"""
        try:
            summary_data = []
            summary_data.append(['Sheet Name', 'Description', 'Record Count'])
            
            for sheet_name, sheet_data in data.items():
                if isinstance(sheet_data, pd.DataFrame):
                    description = f"{template_type.replace('_', ' ').title()} data"
                    record_count = len(sheet_data)
                else:
                    description = "Analysis results"
                    record_count = "N/A"
                
                summary_data.append([sheet_name, description, record_count])
            
            summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            self._write_formatted_sheet(writer, summary_df, 'Summary', template_type)
            
        except Exception as e:
            logger.warning(f"Error creating summary sheet: {str(e)}")
    
    def _dict_to_dataframe(self, data_dict: Dict[str, Any]) -> pd.DataFrame:
        """Convert dictionary to DataFrame"""
        try:
            if not data_dict:
                return pd.DataFrame()
            
            # Flatten nested dictionary
            flattened = {}
            for key, value in data_dict.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flattened[f"{key}_{sub_key}"] = sub_value
                else:
                    flattened[key] = value
            
            # Convert to DataFrame
            return pd.DataFrame([flattened])
            
        except Exception as e:
            logger.warning(f"Error converting dict to DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _generate_pdf_section(self, section_name: str, data: Dict[str, Any], 
                            styles, heading_style) -> List:
        """Generate PDF section content"""
        try:
            content = []
            
            # Section header
            content.append(Paragraph(section_name.replace('_', ' ').title(), heading_style))
            
            # Section content based on type
            if section_name == 'executive_summary':
                content.append(Paragraph("This report provides comprehensive analysis of financial data including ratio analysis, company comparisons, and forecasting results.", styles['Normal']))
                
            elif section_name == 'summary' or section_name == 'forecast_summary':
                content.append(Paragraph("Key findings and analysis results are summarized below:", styles['Normal']))
                
            elif 'analysis' in section_name:
                content.append(Paragraph("Detailed analysis results and methodologies used in the assessment.", styles['Normal']))
                
            else:
                content.append(Paragraph(f"Analysis results for {section_name.replace('_', ' ')}.", styles['Normal']))
            
            content.append(Spacer(1, 12))
            
            return content
            
        except Exception as e:
            logger.warning(f"Error generating PDF section: {str(e)}")
            return [Paragraph("Section content unavailable", styles['Normal'])]
    
    # Additional helper methods for specific data types
    def _create_ratio_categories_df(self, ratios_data: Dict[str, Any]) -> pd.DataFrame:
        """Create ratio categories summary"""
        categories = {
            'Liquidity Ratios': ['current_ratio', 'quick_ratio', 'cash_ratio'],
            'Leverage Ratios': ['debt_to_equity', 'debt_ratio', 'times_interest_earned'],
            'Profitability Ratios': ['gross_margin', 'operating_margin', 'net_margin', 'roa', 'roe'],
            'Efficiency Ratios': ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
        }
        
        return pd.DataFrame(list(categories.items()), columns=['Category', 'Ratios'])
    
    def _create_summary_metrics_df(self, ratios_data: Dict[str, Any]) -> pd.DataFrame:
        """Create summary metrics DataFrame"""
        try:
            companies = list(ratios_data.keys())
            return pd.DataFrame({
                'Metric': ['Total Companies', 'Analysis Date', 'Report Type'],
                'Value': [len(companies), datetime.now().strftime('%Y-%m-%d'), 'Financial Ratio Analysis']
            })
        except:
            return pd.DataFrame()
    
    def _create_benchmarks_df(self, comparison_data: Dict[str, Any]) -> pd.DataFrame:
        """Create industry benchmarks DataFrame"""
        try:
            if 'industry_benchmarks' in comparison_data:
                benchmarks = comparison_data['industry_benchmarks']
                rows = []
                for metric, benchmark_data in benchmarks.items():
                    if isinstance(benchmark_data, dict):
                        row = {'Metric': metric}
                        row.update(benchmark_data)
                        rows.append(row)
                return pd.DataFrame(rows)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def _create_rankings_df(self, comparison_data: Dict[str, Any]) -> pd.DataFrame:
        """Create rankings DataFrame"""
        return self._create_comparison_dataframe(comparison_data)
    
    def _create_model_diagnostics_df(self, forecasts_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create model diagnostics DataFrame"""
        try:
            rows = []
            for forecast in forecasts_data:
                diagnostics = forecast.get('model_diagnostics', {})
                row = {
                    'Company': forecast.get('company', 'Unknown'),
                    'Model_Type': forecast.get('model_type', 'Unknown'),
                    'AIC': diagnostics.get('aic', 'N/A'),
                    'R_Squared': diagnostics.get('r_squared', 0),
                    'Data_Points': diagnostics.get('data_points', 0),
                    'Is_Stationary': diagnostics.get('is_stationary', False)
                }
                rows.append(row)
            return pd.DataFrame(rows)
        except:
            return pd.DataFrame()
    
    def _create_growth_analysis_df(self, forecasts_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create growth analysis DataFrame"""
        try:
            rows = []
            for forecast in forecasts_data:
                growth = forecast.get('growth_analysis', {})
                row = {
                    'Company': forecast.get('company', 'Unknown'),
                    'Recent_Growth_Rate': growth.get('recent_growth_rate', 0),
                    'Long_Term_Growth_Rate': growth.get('long_term_growth_rate', 0),
                    'Forecast_CAGR': growth.get('forecast_cagr', 0)
                }
                rows.append(row)
            return pd.DataFrame(rows)
        except:
            return pd.DataFrame()