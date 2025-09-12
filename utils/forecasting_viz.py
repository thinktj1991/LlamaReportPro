"""
Advanced Forecasting Visualization Components

This module provides specialized visualization components for:
- Time-series forecast charts with confidence intervals
- Scenario comparison analysis
- Growth trajectory visualizations
- Forecast performance dashboards
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ForecastingVisualizer:
    """
    Advanced visualization components for forecasting analysis
    """
    
    def __init__(self):
        self.color_palette = {
            'historical': '#1f77b4',
            'forecast': '#ff7f0e', 
            'conservative': '#2ca02c',
            'moderate': '#d62728',
            'optimistic': '#9467bd',
            'confidence_80': 'rgba(255,127,14,0.3)',
            'confidence_95': 'rgba(255,127,14,0.1)'
        }
    
    def create_multi_company_forecast_dashboard(self, forecasts: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """
        Create comprehensive dashboard comparing forecasts across multiple companies
        """
        try:
            if not forecasts:
                return None
            
            num_companies = len(forecasts)
            rows = (num_companies + 1) // 2  # 2 companies per row
            
            fig = make_subplots(
                rows=rows,
                cols=2,
                subplot_titles=[f"{f['company']} - {f['metric'].title()} Forecast" for f in forecasts],
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            for i, forecast in enumerate(forecasts):
                row = (i // 2) + 1
                col = (i % 2) + 1
                
                # Historical data
                historical_dates = forecast['historical_data']['dates']
                historical_values = forecast['historical_data']['values']
                
                fig.add_trace(
                    go.Scatter(
                        x=historical_dates,
                        y=historical_values,
                        mode='lines+markers',
                        name=f'{forecast["company"]} Historical',
                        line=dict(color=self.color_palette['historical'], width=2),
                        marker=dict(size=3),
                        showlegend=(i == 0)
                    ),
                    row=row, col=col
                )
                
                # Forecast data
                forecast_dates = forecast['forecast_dates']
                forecast_values = forecast['forecast_values']
                
                fig.add_trace(
                    go.Scatter(
                        x=forecast_dates,
                        y=forecast_values,
                        mode='lines+markers',
                        name=f'{forecast["company"]} Forecast',
                        line=dict(color=self.color_palette['forecast'], width=2, dash='dash'),
                        marker=dict(size=3),
                        showlegend=(i == 0)
                    ),
                    row=row, col=col
                )
                
                # Confidence intervals
                confidence_intervals = forecast.get('confidence_intervals', {})
                if '80%' in confidence_intervals:
                    upper_80 = confidence_intervals['80%']['upper']
                    lower_80 = confidence_intervals['80%']['lower']
                    
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_dates + forecast_dates[::-1],
                            y=upper_80 + lower_80[::-1],
                            fill='toself',
                            fillcolor=self.color_palette['confidence_80'],
                            line=dict(color='rgba(255,255,255,0)'),
                            name='80% Confidence' if i == 0 else None,
                            showlegend=(i == 0),
                            hoverinfo='skip'
                        ),
                        row=row, col=col
                    )
            
            fig.update_layout(
                title="Multi-Company Forecast Dashboard",
                height=300 * rows,
                template='plotly_white',
                legend=dict(x=0.01, y=0.99)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating multi-company forecast dashboard: {str(e)}")
            return None
    
    def create_growth_trajectory_comparison(self, forecasts: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """
        Create growth trajectory comparison chart
        """
        try:
            if not forecasts:
                return None
            
            fig = go.Figure()
            
            colors = px.colors.qualitative.Set1
            
            for i, forecast in enumerate(forecasts):
                company = forecast['company']
                forecast_values = forecast['forecast_values']
                forecast_dates = forecast['forecast_dates']
                
                # Calculate cumulative growth from first forecast value
                if forecast_values and len(forecast_values) > 0:
                    base_value = forecast_values[0]
                    growth_percentages = [(val / base_value - 1) * 100 for val in forecast_values]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_dates,
                            y=growth_percentages,
                            mode='lines+markers',
                            name=f'{company}',
                            line=dict(color=colors[i % len(colors)], width=3),
                            marker=dict(size=6)
                        )
                    )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                         annotation_text="Baseline (0% Growth)")
            
            fig.update_layout(
                title="Growth Trajectory Comparison",
                xaxis_title="Forecast Period",
                yaxis_title="Cumulative Growth (%)",
                template='plotly_white',
                height=500,
                legend=dict(x=0.01, y=0.99)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating growth trajectory comparison: {str(e)}")
            return None
    
    def create_scenario_analysis_chart(self, base_forecast: Dict[str, Any], 
                                     scenarios: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create scenario analysis visualization
        """
        try:
            if not base_forecast or not scenarios:
                return None
            
            fig = go.Figure()
            
            forecast_dates = base_forecast['forecast_dates']
            
            # Add base forecast
            fig.add_trace(
                go.Scatter(
                    x=forecast_dates,
                    y=base_forecast['forecast_values'],
                    mode='lines+markers',
                    name='Base Forecast',
                    line=dict(color=self.color_palette['forecast'], width=3),
                    marker=dict(size=6)
                )
            )
            
            # Add scenarios
            scenario_colors = {
                'conservative': self.color_palette['conservative'],
                'moderate': self.color_palette['moderate'],
                'optimistic': self.color_palette['optimistic']
            }
            
            for scenario_name, scenario_data in scenarios.items():
                color = scenario_colors.get(scenario_name, '#666666')
                
                fig.add_trace(
                    go.Scatter(
                        x=forecast_dates,
                        y=scenario_data['values'],
                        mode='lines+markers',
                        name=scenario_data['name'],
                        line=dict(color=color, width=2, dash='dot'),
                        marker=dict(size=4)
                    )
                )
            
            fig.update_layout(
                title=f"Scenario Analysis - {base_forecast['company']}",
                xaxis_title="Forecast Period",
                yaxis_title=f"{base_forecast['metric'].title()}",
                template='plotly_white',
                height=500,
                legend=dict(x=0.01, y=0.99)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating scenario analysis chart: {str(e)}")
            return None
    
    def create_forecast_accuracy_metrics(self, forecasts: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """
        Create forecast accuracy and model performance metrics visualization
        """
        try:
            if not forecasts:
                return None
            
            # Extract model performance metrics
            companies = []
            r_squared_values = []
            data_points = []
            forecast_cagr = []
            
            for forecast in forecasts:
                companies.append(forecast['company'])
                
                diagnostics = forecast.get('model_diagnostics', {})
                growth_analysis = forecast.get('growth_analysis', {})
                
                r_squared_values.append(diagnostics.get('r_squared', 0))
                data_points.append(diagnostics.get('data_points', 0))
                forecast_cagr.append(growth_analysis.get('forecast_cagr', 0))
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Model Fit Quality (R²)',
                    'Data Availability',
                    'Forecast Growth Rate (CAGR)',
                    'Model Performance Summary'
                ],
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"type": "table"}]]
            )
            
            # R² values
            fig.add_trace(
                go.Bar(
                    x=companies,
                    y=r_squared_values,
                    name='R² Score',
                    marker_color='lightblue'
                ),
                row=1, col=1
            )
            
            # Data points
            fig.add_trace(
                go.Bar(
                    x=companies,
                    y=data_points,
                    name='Data Points',
                    marker_color='lightgreen'
                ),
                row=1, col=2
            )
            
            # CAGR
            colors = ['red' if cagr < 0 else 'green' for cagr in forecast_cagr]
            fig.add_trace(
                go.Bar(
                    x=companies,
                    y=forecast_cagr,
                    name='Forecast CAGR (%)',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            # Summary table
            summary_data = []
            for i, company in enumerate(companies):
                summary_data.append([
                    company,
                    f"{r_squared_values[i]:.3f}",
                    str(data_points[i]),
                    f"{forecast_cagr[i]:.1f}%"
                ])
            
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=['Company', 'R² Score', 'Data Points', 'Forecast CAGR'],
                        fill_color='lightgray',
                        align='center'
                    ),
                    cells=dict(
                        values=list(zip(*summary_data)),
                        fill_color='white',
                        align='center'
                    )
                ),
                row=2, col=2
            )
            
            fig.update_layout(
                title="Forecast Model Performance Metrics",
                height=600,
                template='plotly_white',
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating forecast accuracy metrics: {str(e)}")
            return None
    
    def create_forecast_summary_cards(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary statistics for forecasts
        """
        try:
            if not forecasts:
                return {}
            
            summary = {
                'total_companies': len(forecasts),
                'avg_forecast_cagr': 0,
                'growth_companies': 0,
                'declining_companies': 0,
                'model_types': {},
                'avg_r_squared': 0,
                'total_data_points': 0
            }
            
            cagr_values = []
            r_squared_values = []
            
            for forecast in forecasts:
                # Growth analysis
                growth_analysis = forecast.get('growth_analysis', {})
                cagr = growth_analysis.get('forecast_cagr', 0)
                cagr_values.append(cagr)
                
                if cagr > 0:
                    summary['growth_companies'] += 1
                else:
                    summary['declining_companies'] += 1
                
                # Model diagnostics
                diagnostics = forecast.get('model_diagnostics', {})
                r_squared = diagnostics.get('r_squared', 0)
                if r_squared > 0:
                    r_squared_values.append(r_squared)
                
                data_points = diagnostics.get('data_points', 0)
                summary['total_data_points'] += data_points
                
                # Model types
                model_type = forecast.get('model_type', 'Unknown')
                summary['model_types'][model_type] = summary['model_types'].get(model_type, 0) + 1
            
            # Calculate averages
            if cagr_values:
                summary['avg_forecast_cagr'] = np.mean(cagr_values)
            
            if r_squared_values:
                summary['avg_r_squared'] = np.mean(r_squared_values)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating forecast summary: {str(e)}")
            return {}
    
    def display_forecast_insights_panel(self, insights: List[str], summary: Dict[str, Any]):
        """
        Display formatted forecast insights panel in Streamlit
        """
        try:
            st.subheader("🔮 Forecast Intelligence")
            
            # Summary metrics
            if summary:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Companies Analyzed", summary.get('total_companies', 0))
                
                with col2:
                    avg_cagr = summary.get('avg_forecast_cagr', 0)
                    st.metric("Average Forecast CAGR", f"{avg_cagr:.1f}%")
                
                with col3:
                    growth_companies = summary.get('growth_companies', 0)
                    st.metric("Growth Companies", growth_companies)
                
                with col4:
                    avg_r_squared = summary.get('avg_r_squared', 0)
                    st.metric("Average Model Fit", f"{avg_r_squared:.3f}")
            
            # Insights
            if insights:
                st.write("**🧠 Key Forecast Insights:**")
                for i, insight in enumerate(insights, 1):
                    if "Strong Growth" in insight or "🚀" in insight:
                        st.success(f"**{i}.** {insight}")
                    elif "Declining" in insight or "📉" in insight or "Risk" in insight:
                        st.error(f"**{i}.** {insight}")
                    elif "Variability" in insight or "⚠️" in insight:
                        st.warning(f"**{i}.** {insight}")
                    else:
                        st.info(f"**{i}.** {insight}")
            else:
                st.info("No specific forecast insights available")
            
        except Exception as e:
            logger.error(f"Error displaying forecast insights panel: {str(e)}")
            st.error(f"Error displaying insights: {str(e)}")