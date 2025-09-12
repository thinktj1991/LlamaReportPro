import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class FinancialCalculator:
    def __init__(self):
        # Define financial ratio categories and formulas
        self.ratio_definitions = {
            'liquidity': {
                'current_ratio': {
                    'formula': 'current_assets / current_liabilities',
                    'description': 'Company\'s ability to pay short-term obligations',
                    'benchmark': {'good': 2.0, 'acceptable': 1.5, 'poor': 1.0}
                },
                'quick_ratio': {
                    'formula': '(current_assets - inventory) / current_liabilities',
                    'description': 'Immediate liquidity without relying on inventory',
                    'benchmark': {'good': 1.5, 'acceptable': 1.0, 'poor': 0.7}
                },
                'cash_ratio': {
                    'formula': 'cash / current_liabilities',
                    'description': 'Most conservative liquidity measure',
                    'benchmark': {'good': 0.5, 'acceptable': 0.2, 'poor': 0.1}
                }
            },
            'profitability': {
                'gross_margin': {
                    'formula': '(revenue - cost_of_goods_sold) / revenue',
                    'description': 'Gross profit as percentage of revenue',
                    'benchmark': {'good': 0.4, 'acceptable': 0.25, 'poor': 0.15}
                },
                'operating_margin': {
                    'formula': 'operating_income / revenue',
                    'description': 'Operating efficiency and pricing power',
                    'benchmark': {'good': 0.2, 'acceptable': 0.1, 'poor': 0.05}
                },
                'net_margin': {
                    'formula': 'net_income / revenue',
                    'description': 'Overall profitability after all expenses',
                    'benchmark': {'good': 0.15, 'acceptable': 0.08, 'poor': 0.03}
                },
                'roa': {
                    'formula': 'net_income / total_assets',
                    'description': 'Return on Assets - efficiency in using assets',
                    'benchmark': {'good': 0.1, 'acceptable': 0.05, 'poor': 0.02}
                },
                'roe': {
                    'formula': 'net_income / shareholders_equity',
                    'description': 'Return on Equity - returns to shareholders',
                    'benchmark': {'good': 0.15, 'acceptable': 0.1, 'poor': 0.05}
                }
            },
            'leverage': {
                'debt_to_equity': {
                    'formula': 'total_debt / shareholders_equity',
                    'description': 'Financial leverage and capital structure',
                    'benchmark': {'good': 0.3, 'acceptable': 0.6, 'poor': 1.0}
                },
                'debt_ratio': {
                    'formula': 'total_debt / total_assets',
                    'description': 'Proportion of assets financed by debt',
                    'benchmark': {'good': 0.3, 'acceptable': 0.5, 'poor': 0.7}
                },
                'times_interest_earned': {
                    'formula': 'ebit / interest_expense',
                    'description': 'Ability to meet interest obligations',
                    'benchmark': {'good': 5.0, 'acceptable': 2.5, 'poor': 1.5}
                }
            },
            'efficiency': {
                'asset_turnover': {
                    'formula': 'revenue / total_assets',
                    'description': 'Efficiency in using assets to generate sales',
                    'benchmark': {'good': 1.5, 'acceptable': 1.0, 'poor': 0.5}
                },
                'inventory_turnover': {
                    'formula': 'cost_of_goods_sold / inventory',
                    'description': 'How quickly inventory is sold',
                    'benchmark': {'good': 8.0, 'acceptable': 4.0, 'poor': 2.0}
                },
                'receivables_turnover': {
                    'formula': 'revenue / accounts_receivable',
                    'description': 'Efficiency in collecting receivables',
                    'benchmark': {'good': 12.0, 'acceptable': 8.0, 'poor': 4.0}
                }
            }
        }
        
        # Metric mapping - maps extracted metrics to calculation components
        self.metric_mapping = {
            'revenue': ['revenue', 'sales', 'net_sales', 'total_revenue'],
            'net_income': ['net_income', 'net_profit', 'profit', 'earnings'],
            'total_assets': ['total_assets', 'assets'],
            'current_assets': ['current_assets'],
            'cash': ['cash', 'cash_equivalents'],
            'inventory': ['inventory', 'inventories'],
            'accounts_receivable': ['accounts_receivable', 'receivables'],
            'current_liabilities': ['current_liabilities'],
            'total_debt': ['total_debt', 'debt', 'liabilities'],
            'shareholders_equity': ['shareholders_equity', 'equity', 'stockholders_equity'],
            'operating_income': ['operating_income', 'ebit'],
            'cost_of_goods_sold': ['cost_of_goods_sold', 'cogs'],
            'interest_expense': ['interest_expense', 'interest']
        }
    
    def calculate_financial_ratios(self, financial_metrics: Dict[str, float], 
                                 company_name: str = "Company") -> Dict[str, Any]:
        """
        Calculate financial ratios from extracted metrics
        """
        try:
            calculated_ratios = {
                'company': company_name,
                'ratios': {},
                'categories': {},
                'overall_score': 0.0,
                'strengths': [],
                'weaknesses': [],
                'missing_data': []
            }
            
            # Normalize metric names for easier lookup
            normalized_metrics = self._normalize_metrics(financial_metrics)
            
            category_scores = {}
            
            # Calculate ratios by category
            for category, ratios in self.ratio_definitions.items():
                category_results = {}
                
                for ratio_name, ratio_info in ratios.items():
                    result = self._calculate_single_ratio(
                        ratio_name, ratio_info, normalized_metrics
                    )
                    category_results[ratio_name] = result
                    calculated_ratios['ratios'][ratio_name] = result
                
                # Calculate category score
                valid_ratios = [r for r in category_results.values() if r['value'] is not None]
                if valid_ratios:
                    category_score = np.mean([r['score'] for r in valid_ratios])
                    category_scores[category] = category_score
                    calculated_ratios['categories'][category] = {
                        'score': category_score,
                        'ratios': category_results
                    }
            
            # Calculate overall score
            if category_scores:
                calculated_ratios['overall_score'] = np.mean(list(category_scores.values()))
            
            # Identify strengths and weaknesses
            calculated_ratios['strengths'], calculated_ratios['weaknesses'] = self._analyze_performance(
                calculated_ratios['ratios']
            )
            
            # Identify missing critical data
            calculated_ratios['missing_data'] = self._identify_missing_data(normalized_metrics)
            
            return calculated_ratios
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {str(e)}")
            return {
                'company': company_name,
                'ratios': {},
                'categories': {},
                'overall_score': 0.0,
                'strengths': [],
                'weaknesses': [],
                'missing_data': [],
                'error': str(e)
            }
    
    def _normalize_metrics(self, financial_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize metric names to standard format for calculation
        """
        normalized = {}
        
        for standard_name, possible_names in self.metric_mapping.items():
            value = None
            
            # Look for metric in various name formats
            for metric_name, metric_value in financial_metrics.items():
                metric_lower = metric_name.lower().replace(' ', '_')
                
                for possible_name in possible_names:
                    if possible_name.lower() in metric_lower:
                        value = metric_value
                        break
                
                if value is not None:
                    break
            
            if value is not None:
                normalized[standard_name] = float(value)
        
        return normalized
    
    def _calculate_single_ratio(self, ratio_name: str, ratio_info: Dict, 
                              metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate a single financial ratio
        """
        try:
            formula = ratio_info['formula']
            benchmark = ratio_info['benchmark']
            
            # Parse formula and calculate
            value = self._evaluate_formula(formula, metrics)
            
            result = {
                'value': value,
                'score': 0.0,
                'benchmark_status': 'unknown',
                'description': ratio_info['description'],
                'formula': formula,
                'missing_components': []
            }
            
            if value is not None:
                # Calculate score based on benchmarks
                result['score'] = self._calculate_ratio_score(value, benchmark)
                result['benchmark_status'] = self._get_benchmark_status(value, benchmark)
            else:
                # Identify missing components
                result['missing_components'] = self._find_missing_components(formula, metrics)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ratio {ratio_name}: {str(e)}")
            return {
                'value': None,
                'score': 0.0,
                'benchmark_status': 'error',
                'description': ratio_info.get('description', ''),
                'formula': ratio_info.get('formula', ''),
                'missing_components': [],
                'error': str(e)
            }
    
    def _evaluate_formula(self, formula: str, metrics: Dict[str, float]) -> Optional[float]:
        """
        Safely evaluate a financial formula with given metrics
        """
        try:
            # Replace metric names in formula with values
            expression = formula
            
            for metric_name, value in metrics.items():
                if metric_name in expression:
                    expression = expression.replace(metric_name, str(value))
            
            # Check if all variables were replaced (no alphabetic characters remaining)
            import re
            if re.search(r'[a-zA-Z_]', expression):
                return None  # Missing data
            
            # Safely evaluate the expression
            try:
                result = eval(expression)
                return float(result) if result is not None and not np.isnan(result) else None
            except (ZeroDivisionError, ValueError):
                return None
                
        except Exception as e:
            logger.warning(f"Error evaluating formula {formula}: {str(e)}")
            return None
    
    def _calculate_ratio_score(self, value: float, benchmark: Dict[str, float]) -> float:
        """
        Calculate a score (0-1) based on benchmark comparison
        """
        try:
            good = benchmark['good']
            acceptable = benchmark['acceptable']
            poor = benchmark['poor']
            
            # Determine if higher or lower is better based on benchmark ordering
            higher_is_better = good > acceptable > poor
            
            if higher_is_better:
                if value >= good:
                    return 1.0
                elif value >= acceptable:
                    return 0.5 + 0.5 * (value - acceptable) / (good - acceptable)
                elif value >= poor:
                    return 0.25 + 0.25 * (value - poor) / (acceptable - poor)
                else:
                    return 0.1  # Very poor
            else:
                # Lower is better (like debt ratios)
                if value <= good:
                    return 1.0
                elif value <= acceptable:
                    return 0.5 + 0.5 * (acceptable - value) / (acceptable - good)
                elif value <= poor:
                    return 0.25 + 0.25 * (poor - value) / (poor - acceptable)
                else:
                    return 0.1  # Very poor
                    
        except Exception:
            return 0.5  # Default neutral score
    
    def _get_benchmark_status(self, value: float, benchmark: Dict[str, float]) -> str:
        """
        Get text status based on benchmark comparison
        """
        try:
            good = benchmark['good']
            acceptable = benchmark['acceptable']
            poor = benchmark['poor']
            
            # Determine if higher or lower is better
            higher_is_better = good > acceptable > poor
            
            if higher_is_better:
                if value >= good:
                    return 'excellent'
                elif value >= acceptable:
                    return 'good'
                elif value >= poor:
                    return 'acceptable'
                else:
                    return 'poor'
            else:
                if value <= good:
                    return 'excellent'
                elif value <= acceptable:
                    return 'good'
                elif value <= poor:
                    return 'acceptable'
                else:
                    return 'poor'
                    
        except Exception:
            return 'unknown'
    
    def _find_missing_components(self, formula: str, metrics: Dict[str, float]) -> List[str]:
        """
        Find which components are missing for formula calculation
        """
        missing = []
        
        # Extract variable names from formula
        import re
        variables = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula)
        
        for var in variables:
            if var not in metrics:
                missing.append(var)
        
        return missing
    
    def _analyze_performance(self, ratios: Dict[str, Dict]) -> Tuple[List[str], List[str]]:
        """
        Analyze overall performance to identify strengths and weaknesses
        """
        strengths = []
        weaknesses = []
        
        for ratio_name, ratio_data in ratios.items():
            if ratio_data['value'] is not None:
                status = ratio_data['benchmark_status']
                if status in ['excellent', 'good']:
                    strengths.append(f"{ratio_name.replace('_', ' ').title()}: {status}")
                elif status == 'poor':
                    weaknesses.append(f"{ratio_name.replace('_', ' ').title()}: {status}")
        
        return strengths, weaknesses
    
    def _identify_missing_data(self, metrics: Dict[str, float]) -> List[str]:
        """
        Identify critical missing financial data
        """
        critical_metrics = [
            'revenue', 'net_income', 'total_assets', 'current_assets',
            'current_liabilities', 'shareholders_equity'
        ]
        
        missing = []
        for metric in critical_metrics:
            if metric not in metrics:
                missing.append(metric.replace('_', ' ').title())
        
        return missing
    
    def create_ratio_trend_analysis(self, company_ratios_timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trends in financial ratios over time
        """
        try:
            if not company_ratios_timeline:
                return {'error': 'No timeline data provided'}
            
            trend_analysis = {
                'periods': len(company_ratios_timeline),
                'ratio_trends': {},
                'improvement_trends': [],
                'declining_trends': [],
                'volatility_analysis': {},
                'overall_trend': 'stable'
            }
            
            # Extract ratio values over time
            ratio_names = set()
            for period_data in company_ratios_timeline:
                if 'ratios' in period_data:
                    ratio_names.update(period_data['ratios'].keys())
            
            # Analyze each ratio's trend
            for ratio_name in ratio_names:
                values = []
                periods = []
                
                for i, period_data in enumerate(company_ratios_timeline):
                    ratio_data = period_data.get('ratios', {}).get(ratio_name, {})
                    if ratio_data.get('value') is not None:
                        values.append(ratio_data['value'])
                        periods.append(i)
                
                if len(values) >= 2:
                    trend_info = self._analyze_single_ratio_trend(ratio_name, values, periods)
                    trend_analysis['ratio_trends'][ratio_name] = trend_info
                    
                    # Categorize trends
                    if trend_info['direction'] == 'improving':
                        trend_analysis['improvement_trends'].append(ratio_name)
                    elif trend_info['direction'] == 'declining':
                        trend_analysis['declining_trends'].append(ratio_name)
            
            # Overall trend assessment
            improving = len(trend_analysis['improvement_trends'])
            declining = len(trend_analysis['declining_trends'])
            
            if improving > declining * 1.5:
                trend_analysis['overall_trend'] = 'improving'
            elif declining > improving * 1.5:
                trend_analysis['overall_trend'] = 'declining'
            else:
                trend_analysis['overall_trend'] = 'stable'
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error creating trend analysis: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_single_ratio_trend(self, ratio_name: str, values: List[float], 
                                  periods: List[int]) -> Dict[str, Any]:
        """
        Analyze trend for a single ratio
        """
        try:
            if len(values) < 2:
                return {'direction': 'insufficient_data', 'volatility': 0.0}
            
            # Calculate linear trend
            slope = np.polyfit(periods, values, 1)[0]
            
            # Calculate volatility (coefficient of variation)
            mean_val = np.mean(values)
            std_val = np.std(values)
            volatility = std_val / mean_val if mean_val != 0 else 0
            
            # Determine trend direction
            threshold = 0.01  # 1% change threshold
            if abs(slope) < threshold:
                direction = 'stable'
            elif slope > 0:
                direction = 'improving'
            else:
                direction = 'declining'
            
            return {
                'direction': direction,
                'slope': slope,
                'volatility': volatility,
                'values': values,
                'periods': periods,
                'change_rate': slope / mean_val if mean_val != 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {ratio_name}: {str(e)}")
            return {'direction': 'error', 'volatility': 0.0}
    
    def create_ratio_visualization(self, ratio_calculations: Dict[str, Any]) -> go.Figure:
        """
        Create comprehensive visualization of financial ratios
        """
        try:
            if not ratio_calculations.get('ratios'):
                return self._create_error_figure("No ratio data available")
            
            # Create subplots for different ratio categories
            categories = list(ratio_calculations.get('categories', {}).keys())
            if not categories:
                categories = ['all']
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Ratio Scores by Category', 'Individual Ratio Performance', 
                              'Benchmark Comparison', 'Score Distribution'),
                specs=[[{"type": "bar"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "histogram"}]]
            )
            
            # 1. Category scores
            if 'categories' in ratio_calculations:
                cat_names = list(ratio_calculations['categories'].keys())
                cat_scores = [ratio_calculations['categories'][cat]['score'] 
                            for cat in cat_names]
                
                fig.add_trace(
                    go.Bar(x=cat_names, y=cat_scores, name="Category Scores",
                          marker_color='lightblue'),
                    row=1, col=1
                )
            
            # 2. Individual ratio performance
            ratios = ratio_calculations['ratios']
            ratio_names = []
            ratio_scores = []
            
            for name, data in ratios.items():
                if data.get('value') is not None:
                    ratio_names.append(name.replace('_', ' ').title()[:15])
                    ratio_scores.append(data['score'])
            
            if ratio_names:
                colors = ['green' if score >= 0.7 else 'orange' if score >= 0.4 else 'red' 
                         for score in ratio_scores]
                
                fig.add_trace(
                    go.Bar(x=ratio_names, y=ratio_scores, name="Ratio Scores",
                          marker_color=colors),
                    row=1, col=2
                )
            
            # 3. Benchmark comparison scatter
            values = []
            benchmarks = []
            status_colors = []
            
            for name, data in ratios.items():
                if data.get('value') is not None:
                    values.append(data['value'])
                    
                    # Get benchmark info if available
                    ratio_def = self._find_ratio_definition(name)
                    if ratio_def:
                        benchmarks.append(ratio_def['benchmark']['good'])
                        status = data.get('benchmark_status', 'unknown')
                        color_map = {'excellent': 'green', 'good': 'lightgreen',
                                   'acceptable': 'orange', 'poor': 'red', 'unknown': 'gray'}
                        status_colors.append(color_map.get(status, 'gray'))
                    else:
                        benchmarks.append(1.0)
                        status_colors.append('gray')
            
            if values:
                fig.add_trace(
                    go.Scatter(x=benchmarks, y=values, mode='markers',
                             marker=dict(color=status_colors, size=10),
                             name="Actual vs Benchmark"),
                    row=2, col=1
                )
                
                # Add diagonal line for reference
                max_val = max(max(values), max(benchmarks))
                fig.add_trace(
                    go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines',
                             line=dict(dash='dash', color='gray'),
                             name="Perfect Match", showlegend=False),
                    row=2, col=1
                )
            
            # 4. Score distribution
            if ratio_scores:
                fig.add_trace(
                    go.Histogram(x=ratio_scores, nbinsx=10, name="Score Distribution",
                               marker_color='lightcoral'),
                    row=2, col=2
                )
            
            fig.update_layout(
                title=f"Financial Ratio Analysis - {ratio_calculations.get('company', 'Company')}",
                height=600,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating ratio visualization: {str(e)}")
            return self._create_error_figure(f"Error creating visualization: {str(e)}")
    
    def create_trend_visualization(self, trend_analysis: Dict[str, Any]) -> go.Figure:
        """
        Create time-series visualization of ratio trends
        """
        try:
            if not trend_analysis.get('ratio_trends'):
                return self._create_error_figure("No trend data available")
            
            fig = go.Figure()
            
            # Plot trends for each ratio
            for ratio_name, trend_data in trend_analysis['ratio_trends'].items():
                if 'values' in trend_data and 'periods' in trend_data:
                    values = trend_data['values']
                    periods = trend_data['periods']
                    
                    # Determine line color based on trend direction
                    direction = trend_data.get('direction', 'stable')
                    color_map = {'improving': 'green', 'declining': 'red', 'stable': 'blue'}
                    color = color_map.get(direction, 'gray')
                    
                    fig.add_trace(go.Scatter(
                        x=periods,
                        y=values,
                        mode='lines+markers',
                        name=ratio_name.replace('_', ' ').title(),
                        line=dict(color=color, width=2),
                        marker=dict(size=8)
                    ))
            
            fig.update_layout(
                title="Financial Ratio Trends Over Time",
                xaxis_title="Time Period",
                yaxis_title="Ratio Value",
                height=500,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating trend visualization: {str(e)}")
            return self._create_error_figure(f"Error creating trend visualization: {str(e)}")
    
    def _find_ratio_definition(self, ratio_name: str) -> Optional[Dict]:
        """
        Find ratio definition by name
        """
        for category_ratios in self.ratio_definitions.values():
            if ratio_name in category_ratios:
                return category_ratios[ratio_name]
        return None
    
    def _create_error_figure(self, message: str) -> go.Figure:
        """
        Create error figure with message
        """
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="Visualization Error",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig