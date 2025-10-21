import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
                # Handle different value types
                try:
                    if isinstance(value, dict):
                        # Try to extract numeric value from dict
                        if 'value' in value:
                            numeric_value = value['value']
                        elif 'amount' in value:
                            numeric_value = value['amount']
                        elif 'total' in value:
                            numeric_value = value['total']
                        else:
                            # Skip if no recognizable numeric field
                            continue
                    elif isinstance(value, (int, float)):
                        numeric_value = value
                    elif isinstance(value, str):
                        # Try to convert string to float
                        try:
                            numeric_value = float(value.replace(',', '').replace('%', '').replace('$', ''))
                        except ValueError:
                            continue
                    else:
                        continue

                    # Validate numeric value
                    if isinstance(numeric_value, (int, float)) and np.isfinite(numeric_value):
                        normalized[standard_name] = float(numeric_value)

                except Exception as e:
                    logger.debug(f"Error normalizing metric {standard_name} with value {value}: {str(e)}")
                    continue
        
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


# ==================== 杜邦分析计算器 ====================

class DupontAnalyzer:
    """
    杜邦分析计算器
    基于FinancialCalculator扩展，实现完整的杜邦分析
    """

    def __init__(self, financial_calculator: Optional[FinancialCalculator] = None):
        """
        初始化杜邦分析器

        Args:
            financial_calculator: 可选的FinancialCalculator实例
        """
        self.calculator = financial_calculator or FinancialCalculator()

        # 杜邦分析指标映射
        self.dupont_metric_mapping = {
            'net_income': ['净利润', 'net_income', 'net_profit', '归母净利润', '归属于母公司所有者的净利润'],
            'revenue': ['营业收入', 'revenue', 'sales', 'net_sales', '营业总收入', '总收入'],
            'total_assets': ['总资产', 'total_assets', 'assets', '资产总计'],
            'shareholders_equity': ['股东权益', 'equity', 'shareholders_equity', '所有者权益', '净资产', '归属于母公司所有者权益'],
            'current_assets': ['流动资产', 'current_assets'],
            'non_current_assets': ['非流动资产', 'non_current_assets', '长期资产', '非流动资产合计'],
            'operating_profit': ['营业利润', 'operating_profit', 'operating_income', 'ebit'],
            'total_liabilities': ['总负债', 'total_liabilities', 'liabilities', '负债合计']
        }

    def calculate_dupont_analysis(
        self,
        financial_data: Dict[str, float],
        company_name: str,
        report_year: str,
        report_period: Optional[str] = None
    ) -> 'DupontAnalysis':
        """
        执行完整杜邦分析

        Args:
            financial_data: 财务数据字典，键为指标名称，值为数值
            company_name: 公司名称
            report_year: 报告年份
            report_period: 报告期间（可选）

        Returns:
            DupontAnalysis Pydantic模型实例
        """
        # 动态导入以避免循环依赖
        try:
            from llamareport_backend.models.dupont_models import (
                DupontAnalysis, DupontLevel1, DupontLevel2, DupontLevel3,
                DupontMetric, DupontTreeNode
            )
        except ImportError:
            # 如果在utils目录运行，尝试相对导入
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent.parent / 'llamareport-backend'
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            from models.dupont_models import (
                DupontAnalysis, DupontLevel1, DupontLevel2, DupontLevel3,
                DupontMetric, DupontTreeNode
            )

        # 标准化财务数据
        normalized_data = self._normalize_financial_data(financial_data)

        # 提取关键指标
        net_income = normalized_data.get('net_income', 0)
        revenue = normalized_data.get('revenue', 0)
        total_assets = normalized_data.get('total_assets', 0)
        shareholders_equity = normalized_data.get('shareholders_equity', 0)
        current_assets = normalized_data.get('current_assets', 0)
        non_current_assets = normalized_data.get('non_current_assets', 0)
        operating_profit = normalized_data.get('operating_profit', None)
        total_liabilities = normalized_data.get('total_liabilities', None)

        # 第三层：底层数据
        level3_net_income = self._create_metric(
            "净利润", net_income, 3, "净利润", None, "元"
        )
        level3_revenue = self._create_metric(
            "营业收入", revenue, 3, "营业收入", None, "元"
        )
        level3_current_assets = self._create_metric(
            "流动资产", current_assets, 3, "流动资产", "总资产", "元"
        )
        level3_non_current_assets = self._create_metric(
            "非流动资产", non_current_assets, 3, "非流动资产", "总资产", "元"
        )

        # 第二层：计算比率
        net_profit_margin = (net_income / revenue * 100) if revenue > 0 else 0
        asset_turnover = (revenue / total_assets) if total_assets > 0 else 0

        level2_net_profit_margin = self._create_metric(
            "营业净利润率", net_profit_margin, 2,
            "营业净利润率 = 净利润 / 营业收入", "资产净利率", "%"
        )
        level2_asset_turnover = self._create_metric(
            "资产周转率", asset_turnover, 2,
            "资产周转率 = 营业收入 / 总资产", "资产净利率", "倍"
        )
        level2_total_assets = self._create_metric(
            "总资产", total_assets, 2,
            "总资产 = 流动资产 + 非流动资产", "权益乘数", "元"
        )
        level2_shareholders_equity = self._create_metric(
            "股东权益", shareholders_equity, 2,
            "股东权益", "权益乘数", "元"
        )

        # 第一层：ROA和权益乘数
        roa = (net_income / total_assets * 100) if total_assets > 0 else 0
        equity_multiplier = (total_assets / shareholders_equity) if shareholders_equity > 0 else 0

        level1_roa = self._create_metric(
            "资产净利率", roa, 1,
            "资产净利率 = 净利润 / 总资产", "净资产收益率", "%"
        )
        level1_equity_multiplier = self._create_metric(
            "权益乘数", equity_multiplier, 1,
            "权益乘数 = 总资产 / 股东权益", "净资产收益率", "倍"
        )

        # 顶层：ROE
        roe = (net_income / shareholders_equity * 100) if shareholders_equity > 0 else 0

        level1_roe = self._create_metric(
            "净资产收益率", roe, 1,
            "ROE = 资产净利率 × 权益乘数", None, "%"
        )

        # 构建层级结构
        level1 = DupontLevel1(
            roe=level1_roe,
            roa=level1_roa,
            equity_multiplier=level1_equity_multiplier
        )

        level2 = DupontLevel2(
            net_profit_margin=level2_net_profit_margin,
            asset_turnover=level2_asset_turnover,
            total_assets=level2_total_assets,
            shareholders_equity=level2_shareholders_equity
        )

        level3_dict = {
            'net_income': level3_net_income,
            'revenue': level3_revenue,
            'current_assets': level3_current_assets,
            'non_current_assets': level3_non_current_assets
        }

        if operating_profit is not None:
            level3_dict['operating_profit'] = self._create_metric(
                "营业利润", operating_profit, 3, "营业利润", None, "元"
            )

        if total_liabilities is not None:
            level3_dict['total_liabilities'] = self._create_metric(
                "总负债", total_liabilities, 3, "总负债", None, "元"
            )

        level3 = DupontLevel3(**level3_dict)

        # 构建树状结构
        tree_structure = self._build_tree_structure(level1, level2, level3)

        # 生成分析洞察
        insights = self._generate_insights(level1, level2, level3)
        strengths = self._identify_strengths(level1, level2)
        weaknesses = self._identify_weaknesses(level1, level2)
        recommendations = self._generate_recommendations(strengths, weaknesses)

        # 创建DupontAnalysis实例
        return DupontAnalysis(
            company_name=company_name,
            report_year=report_year,
            report_period=report_period or f"{report_year}年度",
            level1=level1,
            level2=level2,
            level3=level3,
            tree_structure=tree_structure,
            insights=insights,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            data_source="财务数据提取",
            extraction_method="calculation",
            confidence_score=1.0
        )

    def _normalize_financial_data(self, financial_data: Dict[str, float]) -> Dict[str, float]:
        """
        标准化财务数据，将各种可能的指标名称映射到标准名称

        Args:
            financial_data: 原始财务数据

        Returns:
            标准化后的财务数据
        """
        normalized = {}

        for standard_name, possible_names in self.dupont_metric_mapping.items():
            for key, value in financial_data.items():
                # 检查是否匹配任何可能的名称
                if any(name.lower() in key.lower() or key.lower() in name.lower()
                       for name in possible_names):
                    normalized[standard_name] = float(value)
                    break

        return normalized

    def _create_metric(
        self,
        name: str,
        value: float,
        level: int,
        formula: str,
        parent: Optional[str] = None,
        unit: str = "%"
    ) -> 'DupontMetric':
        """
        创建单个杜邦指标

        Args:
            name: 指标名称
            value: 指标值
            level: 层级
            formula: 计算公式
            parent: 父指标名称
            unit: 单位

        Returns:
            DupontMetric实例
        """
        # 使用已导入的模块
        try:
            from llamareport_backend.models.dupont_models import DupontMetric
        except ImportError:
            from models.dupont_models import DupontMetric

        # 格式化显示值
        if unit == "%":
            formatted_value = f"{value:.2f}%"
        elif unit == "倍":
            formatted_value = f"{value:.2f}"
        elif unit == "元":
            # 转换为亿元显示
            if abs(value) >= 1e8:
                formatted_value = f"{value/1e8:.2f}亿元"
            elif abs(value) >= 1e4:
                formatted_value = f"{value/1e4:.2f}万元"
            else:
                formatted_value = f"{value:.2f}元"
        else:
            formatted_value = f"{value:.2f}"

        return DupontMetric(
            name=name,
            value=Decimal(str(value)),
            formatted_value=formatted_value,
            level=level,
            formula=formula,
            parent_metric=parent,
            unit=unit
        )

    def _build_tree_structure(
        self,
        level1: 'DupontLevel1',
        level2: 'DupontLevel2',
        level3: 'DupontLevel3'
    ) -> 'DupontTreeNode':
        """
        构建杜邦分析树状结构

        Args:
            level1: 第一层数据
            level2: 第二层数据
            level3: 第三层数据

        Returns:
            DupontTreeNode根节点
        """
        try:
            from llamareport_backend.models.dupont_models import DupontTreeNode
        except ImportError:
            from models.dupont_models import DupontTreeNode

        # 第三层节点
        net_income_node = DupontTreeNode(
            id="net_income",
            name=level3.net_income.name,
            value=level3.net_income.value,
            formatted_value=level3.net_income.formatted_value,
            level=3,
            children=[],
            formula=level3.net_income.formula
        )

        revenue_node = DupontTreeNode(
            id="revenue",
            name=level3.revenue.name,
            value=level3.revenue.value,
            formatted_value=level3.revenue.formatted_value,
            level=3,
            children=[],
            formula=level3.revenue.formula
        )

        current_assets_node = DupontTreeNode(
            id="current_assets",
            name=level3.current_assets.name,
            value=level3.current_assets.value,
            formatted_value=level3.current_assets.formatted_value,
            level=3,
            children=[],
            formula=level3.current_assets.formula
        )

        non_current_assets_node = DupontTreeNode(
            id="non_current_assets",
            name=level3.non_current_assets.name,
            value=level3.non_current_assets.value,
            formatted_value=level3.non_current_assets.formatted_value,
            level=3,
            children=[],
            formula=level3.non_current_assets.formula
        )

        # 第二层节点
        net_profit_margin_node = DupontTreeNode(
            id="net_profit_margin",
            name=level2.net_profit_margin.name,
            value=level2.net_profit_margin.value,
            formatted_value=level2.net_profit_margin.formatted_value,
            level=2,
            children=[net_income_node, revenue_node],
            formula=level2.net_profit_margin.formula
        )

        asset_turnover_node = DupontTreeNode(
            id="asset_turnover",
            name=level2.asset_turnover.name,
            value=level2.asset_turnover.value,
            formatted_value=level2.asset_turnover.formatted_value,
            level=2,
            children=[revenue_node],
            formula=level2.asset_turnover.formula
        )

        total_assets_node = DupontTreeNode(
            id="total_assets",
            name=level2.total_assets.name,
            value=level2.total_assets.value,
            formatted_value=level2.total_assets.formatted_value,
            level=2,
            children=[current_assets_node, non_current_assets_node],
            formula=level2.total_assets.formula
        )

        shareholders_equity_node = DupontTreeNode(
            id="shareholders_equity",
            name=level2.shareholders_equity.name,
            value=level2.shareholders_equity.value,
            formatted_value=level2.shareholders_equity.formatted_value,
            level=2,
            children=[],
            formula=level2.shareholders_equity.formula
        )

        # 第一层节点
        roa_node = DupontTreeNode(
            id="roa",
            name=level1.roa.name,
            value=level1.roa.value,
            formatted_value=level1.roa.formatted_value,
            level=1,
            children=[net_profit_margin_node, asset_turnover_node],
            formula=level1.roa.formula
        )

        equity_multiplier_node = DupontTreeNode(
            id="equity_multiplier",
            name=level1.equity_multiplier.name,
            value=level1.equity_multiplier.value,
            formatted_value=level1.equity_multiplier.formatted_value,
            level=1,
            children=[total_assets_node, shareholders_equity_node],
            formula=level1.equity_multiplier.formula
        )

        # 根节点（ROE）
        roe_node = DupontTreeNode(
            id="roe",
            name=level1.roe.name,
            value=level1.roe.value,
            formatted_value=level1.roe.formatted_value,
            level=1,
            children=[roa_node, equity_multiplier_node],
            formula=level1.roe.formula
        )

        return roe_node

    def _generate_insights(
        self,
        level1: 'DupontLevel1',
        level2: 'DupontLevel2',
        level3: 'DupontLevel3'
    ) -> List[str]:
        """
        生成AI分析洞察

        Args:
            level1: 第一层数据
            level2: 第二层数据
            level3: 第三层数据

        Returns:
            洞察列表
        """
        insights = []

        roe_value = float(level1.roe.value)
        roa_value = float(level1.roa.value)
        equity_multiplier_value = float(level1.equity_multiplier.value)
        net_profit_margin_value = float(level2.net_profit_margin.value)
        asset_turnover_value = float(level2.asset_turnover.value)

        # ROE水平分析
        if roe_value > 15:
            insights.append(f"净资产收益率为{level1.roe.formatted_value}，处于优秀水平，表明公司盈利能力强")
        elif roe_value > 10:
            insights.append(f"净资产收益率为{level1.roe.formatted_value}，处于良好水平")
        elif roe_value > 5:
            insights.append(f"净资产收益率为{level1.roe.formatted_value}，处于一般水平，有提升空间")
        else:
            insights.append(f"净资产收益率为{level1.roe.formatted_value}，偏低，需要关注盈利能力")

        # ROE驱动因素分析
        if roa_value > equity_multiplier_value:
            insights.append("ROE主要由资产净利率驱动，公司注重资产使用效率和盈利能力")
        else:
            insights.append("ROE主要由权益乘数驱动，公司采用较高的财务杠杆策略")

        # 净利润率分析
        if net_profit_margin_value > 20:
            insights.append(f"营业净利润率达{level2.net_profit_margin.formatted_value}，盈利能力突出")
        elif net_profit_margin_value < 5:
            insights.append(f"营业净利润率仅{level2.net_profit_margin.formatted_value}，成本控制有待加强")

        # 资产周转率分析
        if asset_turnover_value > 1.5:
            insights.append(f"资产周转率为{level2.asset_turnover.formatted_value}，资产使用效率高")
        elif asset_turnover_value < 0.5:
            insights.append(f"资产周转率为{level2.asset_turnover.formatted_value}，资产使用效率偏低")

        # 财务杠杆分析
        if equity_multiplier_value > 3:
            insights.append(f"权益乘数为{level1.equity_multiplier.formatted_value}，财务杠杆较高，需关注财务风险")
        elif equity_multiplier_value < 1.5:
            insights.append(f"权益乘数为{level1.equity_multiplier.formatted_value}，财务结构稳健，杠杆使用保守")

        return insights

    def _identify_strengths(
        self,
        level1: 'DupontLevel1',
        level2: 'DupontLevel2'
    ) -> List[str]:
        """
        识别优势指标

        Args:
            level1: 第一层数据
            level2: 第二层数据

        Returns:
            优势列表
        """
        strengths = []

        # 行业基准（可以后续从数据库或配置文件读取）
        benchmarks = {
            'roe': 12.0,  # 12%
            'roa': 8.0,   # 8%
            'net_profit_margin': 10.0,  # 10%
            'asset_turnover': 1.0,  # 1倍
            'equity_multiplier': 2.0  # 2倍
        }

        roe_value = float(level1.roe.value)
        roa_value = float(level1.roa.value)
        equity_multiplier_value = float(level1.equity_multiplier.value)
        net_profit_margin_value = float(level2.net_profit_margin.value)
        asset_turnover_value = float(level2.asset_turnover.value)

        if roe_value > benchmarks['roe']:
            strengths.append(f"净资产收益率{level1.roe.formatted_value}高于行业平均水平")

        if roa_value > benchmarks['roa']:
            strengths.append(f"资产净利率{level1.roa.formatted_value}表现优异")

        if net_profit_margin_value > benchmarks['net_profit_margin']:
            strengths.append(f"营业净利润率{level2.net_profit_margin.formatted_value}高于行业水平")

        if asset_turnover_value > benchmarks['asset_turnover']:
            strengths.append(f"资产周转率{level2.asset_turnover.formatted_value}显示资产使用效率高")

        return strengths

    def _identify_weaknesses(
        self,
        level1: 'DupontLevel1',
        level2: 'DupontLevel2'
    ) -> List[str]:
        """
        识别劣势指标

        Args:
            level1: 第一层数据
            level2: 第二层数据

        Returns:
            劣势列表
        """
        weaknesses = []

        # 行业基准
        benchmarks = {
            'roe': 12.0,
            'roa': 8.0,
            'net_profit_margin': 10.0,
            'asset_turnover': 1.0,
            'equity_multiplier': 2.0
        }

        roe_value = float(level1.roe.value)
        roa_value = float(level1.roa.value)
        equity_multiplier_value = float(level1.equity_multiplier.value)
        net_profit_margin_value = float(level2.net_profit_margin.value)
        asset_turnover_value = float(level2.asset_turnover.value)

        if roe_value < benchmarks['roe']:
            weaknesses.append(f"净资产收益率{level1.roe.formatted_value}低于行业平均水平")

        if roa_value < benchmarks['roa']:
            weaknesses.append(f"资产净利率{level1.roa.formatted_value}有待提升")

        if net_profit_margin_value < benchmarks['net_profit_margin']:
            weaknesses.append(f"营业净利润率{level2.net_profit_margin.formatted_value}偏低，成本控制需加强")

        if asset_turnover_value < benchmarks['asset_turnover']:
            weaknesses.append(f"资产周转率{level2.asset_turnover.formatted_value}较低，资产使用效率有待提高")

        if equity_multiplier_value > 3.0:
            weaknesses.append(f"权益乘数{level1.equity_multiplier.formatted_value}过高，财务风险较大")

        return weaknesses

    def _generate_recommendations(
        self,
        strengths: List[str],
        weaknesses: List[str]
    ) -> List[str]:
        """
        基于优劣势生成改进建议

        Args:
            strengths: 优势列表
            weaknesses: 劣势列表

        Returns:
            建议列表
        """
        recommendations = []

        # 基于劣势生成建议
        for weakness in weaknesses:
            if "净资产收益率" in weakness:
                recommendations.append("建议从提升资产净利率和优化资本结构两方面入手，提高ROE")
            elif "资产净利率" in weakness:
                recommendations.append("建议提高净利润率或加快资产周转，提升资产净利率")
            elif "净利润率" in weakness:
                recommendations.append("建议优化成本结构，提高产品附加值，提升净利润率")
            elif "资产周转率" in weakness:
                recommendations.append("建议加快存货和应收账款周转，提高资产使用效率")
            elif "权益乘数" in weakness and "过高" in weakness:
                recommendations.append("建议优化资本结构，适当降低财务杠杆，控制财务风险")

        # 基于优势生成建议
        if len(strengths) > 0:
            recommendations.append("建议继续保持现有优势，巩固竞争地位")

        # 通用建议
        if len(recommendations) == 0:
            recommendations.append("建议持续关注财务指标变化，保持稳健经营")

        return recommendations