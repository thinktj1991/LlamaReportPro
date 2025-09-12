import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import streamlit as st
import logging

# Configure logging
logger = logging.getLogger(__name__)

class DataVisualizer:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_document_overview_chart(self, processed_documents: Dict[str, Any]) -> go.Figure:
        """
        Create an overview chart of processed documents
        """
        try:
            doc_names = []
            page_counts = []
            text_lengths = []
            
            for doc_name, doc_data in processed_documents.items():
                doc_names.append(doc_name)
                page_counts.append(doc_data.get('page_count', 0))
                text_lengths.append(doc_data.get('total_text_length', 0))
            
            # Create subplot
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Document Page Counts', 'Text Content Length'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Page counts bar chart
            fig.add_trace(
                go.Bar(
                    x=doc_names,
                    y=page_counts,
                    name="Pages",
                    marker_color=self.color_palette[0]
                ),
                row=1, col=1
            )
            
            # Text length bar chart
            fig.add_trace(
                go.Bar(
                    x=doc_names,
                    y=text_lengths,
                    name="Characters",
                    marker_color=self.color_palette[1]
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title="Document Processing Overview",
                showlegend=False,
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating document overview chart: {str(e)}")
            return self._create_error_figure("Error creating document overview")
    
    def create_table_distribution_chart(self, extracted_tables: Dict[str, List[Dict]]) -> go.Figure:
        """
        Create a chart showing table distribution across documents
        """
        try:
            doc_names = []
            table_counts = []
            financial_counts = []
            importance_scores = []
            
            for doc_name, tables in extracted_tables.items():
                doc_names.append(doc_name)
                table_counts.append(len(tables))
                
                financial_count = sum(1 for table in tables if table.get('is_financial', False))
                financial_counts.append(financial_count)
                
                avg_importance = np.mean([table.get('importance_score', 0) for table in tables]) if tables else 0
                importance_scores.append(avg_importance)
            
            # Create subplot
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Total Tables per Document',
                    'Financial Tables per Document', 
                    'Average Importance Score',
                    'Table Type Distribution'
                )
            )
            
            # Total tables
            fig.add_trace(
                go.Bar(x=doc_names, y=table_counts, name="Total Tables", marker_color=self.color_palette[0]),
                row=1, col=1
            )
            
            # Financial tables
            fig.add_trace(
                go.Bar(x=doc_names, y=financial_counts, name="Financial Tables", marker_color=self.color_palette[2]),
                row=1, col=2
            )
            
            # Importance scores
            fig.add_trace(
                go.Scatter(x=doc_names, y=importance_scores, mode='markers+lines', 
                          name="Avg Importance", marker_color=self.color_palette[4]),
                row=2, col=1
            )
            
            # Table type pie chart
            all_tables = [table for tables in extracted_tables.values() for table in tables]
            financial_total = sum(1 for table in all_tables if table.get('is_financial', False))
            non_financial_total = len(all_tables) - financial_total
            
            fig.add_trace(
                go.Pie(labels=['Financial', 'Non-Financial'], 
                      values=[financial_total, non_financial_total],
                      name="Table Types"),
                row=2, col=2
            )
            
            fig.update_layout(
                title="Table Extraction Analysis",
                showlegend=False,
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating table distribution chart: {str(e)}")
            return self._create_error_figure("Error creating table distribution chart")
    
    def create_financial_metrics_chart(self, consolidated_table: pd.DataFrame) -> go.Figure:
        """
        Create charts for financial metrics from consolidated table
        """
        try:
            if consolidated_table is None or consolidated_table.empty:
                return self._create_error_figure("No financial data available")
            
            # Try to identify numeric columns that might be financial metrics
            numeric_cols = consolidated_table.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                return self._create_error_figure("No numeric financial data found")
            
            # Create subplots for different metrics
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Numeric Data Distribution',
                    'Data by Source Document',
                    'Financial Table Importance',
                    'Data Quality Overview'
                )
            )
            
            # Distribution of numeric values (first numeric column)
            if len(numeric_cols) > 0:
                first_col = numeric_cols[0]
                values = consolidated_table[first_col].dropna()
                if len(values) > 0:
                    fig.add_trace(
                        go.Histogram(x=values, name=f"{first_col} Distribution", 
                                   marker_color=self.color_palette[0]),
                        row=1, col=1
                    )
            
            # Data by source document
            if 'source_document' in consolidated_table.columns:
                doc_counts = consolidated_table['source_document'].value_counts()
                fig.add_trace(
                    go.Bar(x=doc_counts.index, y=doc_counts.values, 
                          name="Rows by Document", marker_color=self.color_palette[1]),
                    row=1, col=2
                )
            
            # Importance scores
            if 'importance_score' in consolidated_table.columns:
                importance_data = consolidated_table['importance_score'].dropna()
                if len(importance_data) > 0:
                    fig.add_trace(
                        go.Box(y=importance_data, name="Importance Scores",
                              marker_color=self.color_palette[2]),
                        row=2, col=1
                    )
            
            # Data quality (completeness)
            completeness = []
            col_names = []
            for col in consolidated_table.columns:
                non_null_pct = (consolidated_table[col].notna().sum() / len(consolidated_table)) * 100
                completeness.append(non_null_pct)
                col_names.append(col[:20])  # Truncate long column names
            
            fig.add_trace(
                go.Bar(x=col_names, y=completeness, name="Data Completeness %",
                      marker_color=self.color_palette[3]),
                row=2, col=2
            )
            
            fig.update_layout(
                title="Financial Data Analysis",
                showlegend=False,
                height=700
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating financial metrics chart: {str(e)}")
            return self._create_error_figure("Error analyzing financial data")
    
    def create_company_comparison_chart(self, company_data: Dict[str, Any], metric: str) -> go.Figure:
        """
        Create comparison chart between companies
        """
        try:
            if not company_data or len(company_data) < 2:
                return self._create_error_figure("Need at least 2 companies for comparison")
            
            companies = list(company_data.keys())
            
            # Extract metric data for each company
            metric_values = []
            years = []
            
            for company in companies:
                company_info = company_data[company]
                # This is a simplified extraction - in practice, you'd need more sophisticated parsing
                if 'tables' in company_info:
                    # Try to find metric in tables
                    value = self._extract_metric_from_tables(company_info['tables'], metric)
                    metric_values.append(value)
                else:
                    metric_values.append(0)
                
                years.append(company_info.get('year', 'Unknown'))
            
            # Create comparison chart
            fig = go.Figure()
            
            fig.add_trace(
                go.Bar(
                    x=companies,
                    y=metric_values,
                    text=[f"{value:,.0f}" if value > 1000 else f"{value:.2f}" for value in metric_values],
                    textposition='auto',
                    marker_color=self.color_palette[:len(companies)]
                )
            )
            
            fig.update_layout(
                title=f"Company Comparison: {metric}",
                xaxis_title="Companies",
                yaxis_title=metric,
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating company comparison chart: {str(e)}")
            return self._create_error_figure("Error creating comparison chart")
    
    def _extract_metric_from_tables(self, tables: List[Dict], metric: str) -> float:
        """
        Extract a specific metric from tables (simplified implementation)
        """
        try:
            metric_lower = metric.lower()
            
            for table in tables:
                if table.get('is_financial', False):
                    df = table['dataframe']
                    
                    # Look for metric in column names or data
                    for col in df.columns:
                        if metric_lower in col.lower():
                            # Try to find a numeric value
                            try:
                                # Convert column to pandas Series if needed
                                col_data = df[col] if isinstance(df[col], pd.Series) else pd.Series(df[col])
                                
                                # Convert to numeric, handling errors gracefully
                                numeric_series = pd.to_numeric(col_data, errors='coerce')
                                
                                # Ensure we have a Series after numeric conversion
                                if not isinstance(numeric_series, pd.Series):
                                    numeric_series = pd.Series(numeric_series)
                                
                                # Remove NaN values and check if we have any numeric data
                                clean_values = numeric_series.dropna()
                                
                                # Check if we have valid numeric data using len() to avoid boolean evaluation issues
                                if isinstance(clean_values, pd.Series) and len(clean_values.index) > 0:
                                    # Get the first non-null value safely
                                    try:
                                        first_val = clean_values.iat[0]  # Use .iat for scalar access
                                        if pd.notna(first_val):
                                            return float(first_val)
                                    except (IndexError, ValueError):
                                        continue
                                        
                            except (ValueError, TypeError, IndexError, AttributeError):
                                continue
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting metric {metric}: {str(e)}")
            return 0.0
    
    def create_rag_response_visualization(self, sources: List[Dict]) -> go.Figure:
        """
        Create visualization for RAG system response sources
        """
        try:
            if not sources:
                return self._create_error_figure("No sources to visualize")
            
            # Extract data from sources
            source_docs = []
            scores = []
            doc_types = []
            
            for source in sources:
                metadata = source.get('metadata', {})
                source_docs.append(metadata.get('source_file', 'Unknown')[:20])
                scores.append(source.get('score', 0.0))
                doc_types.append(metadata.get('document_type', 'unknown'))
            
            # Create subplot
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Source Relevance Scores', 'Source Types'),
                specs=[[{"secondary_y": False}, {"type": "pie"}]]
            )
            
            # Relevance scores
            fig.add_trace(
                go.Bar(x=source_docs, y=scores, name="Relevance Score",
                      marker_color=self.color_palette[0]),
                row=1, col=1
            )
            
            # Source types pie chart
            type_counts = pd.Series(doc_types).value_counts()
            fig.add_trace(
                go.Pie(labels=type_counts.index, values=type_counts.values, name="Source Types"),
                row=1, col=2
            )
            
            fig.update_layout(
                title="RAG Response Source Analysis",
                showlegend=False,
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating RAG visualization: {str(e)}")
            return self._create_error_figure("Error visualizing RAG sources")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """
        Create a simple error figure
        """
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="Visualization Error",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300
        )
        return fig
