"""
Industry Analytics and Benchmarking Module

This module provides advanced industry benchmarking, percentile rankings,
and comprehensive multi-company comparative analytics.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import streamlit as st
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from utils.financial_calculator import FinancialCalculator

# Configure logging
logger = logging.getLogger(__name__)

class IndustryAnalytics:
    """
    Advanced industry analytics and benchmarking system
    """
    
    def __init__(self):
        self.financial_calculator = FinancialCalculator()
        
        # Define metric orientation - True means higher is better, False means lower is better
        self.metric_orientation = {
            # Liquidity ratios - higher is better
            'current_ratio': True,
            'quick_ratio': True,
            'cash_ratio': True,
            
            # Profitability ratios - higher is better
            'gross_margin': True,
            'operating_margin': True,
            'net_margin': True,
            'roa': True,
            'roe': True,
            'roic': True,
            
            # Efficiency ratios - higher is better
            'asset_turnover': True,
            'inventory_turnover': True,
            'receivables_turnover': True,
            
            # Leverage ratios - lower is better (except coverage ratios)
            'debt_to_equity': False,
            'debt_ratio': False,
            'debt_to_assets': False,
            'financial_leverage': False,
            'times_interest_earned': True,  # Coverage ratio - higher is better
            'debt_service_coverage': True,  # Coverage ratio - higher is better
            
            # Market ratios - context dependent, assuming higher is better for most
            'pe_ratio': True,
            'price_to_book': True,
            'dividend_yield': True,
            'earnings_yield': True
        }
        
        # Industry benchmark data - predefined benchmarks for different sectors
        self.industry_benchmarks = {
            'Technology': {
                'current_ratio': {'excellent': 2.5, 'good': 1.8, 'average': 1.2, 'poor': 0.8},
                'roa': {'excellent': 0.15, 'good': 0.10, 'average': 0.06, 'poor': 0.03},
                'roe': {'excellent': 0.20, 'good': 0.15, 'average': 0.10, 'poor': 0.05},
                'debt_to_equity': {'excellent': 0.3, 'good': 0.5, 'average': 0.8, 'poor': 1.2},
                'gross_margin': {'excellent': 0.70, 'good': 0.50, 'average': 0.35, 'poor': 0.20}
            },
            'Manufacturing': {
                'current_ratio': {'excellent': 2.0, 'good': 1.5, 'average': 1.0, 'poor': 0.7},
                'roa': {'excellent': 0.12, 'good': 0.08, 'average': 0.05, 'poor': 0.02},
                'roe': {'excellent': 0.18, 'good': 0.12, 'average': 0.08, 'poor': 0.04},
                'debt_to_equity': {'excellent': 0.4, 'good': 0.6, 'average': 0.9, 'poor': 1.3},
                'gross_margin': {'excellent': 0.45, 'good': 0.30, 'average': 0.20, 'poor': 0.10}
            },
            'Retail': {
                'current_ratio': {'excellent': 1.8, 'good': 1.3, 'average': 0.9, 'poor': 0.6},
                'roa': {'excellent': 0.10, 'good': 0.06, 'average': 0.04, 'poor': 0.02},
                'roe': {'excellent': 0.15, 'good': 0.10, 'average': 0.06, 'poor': 0.03},
                'debt_to_equity': {'excellent': 0.5, 'good': 0.8, 'average': 1.2, 'poor': 1.8},
                'gross_margin': {'excellent': 0.50, 'good': 0.35, 'average': 0.25, 'poor': 0.15}
            },
            'Financial Services': {
                'current_ratio': {'excellent': 1.5, 'good': 1.2, 'average': 0.9, 'poor': 0.6},
                'roa': {'excellent': 0.08, 'good': 0.05, 'average': 0.03, 'poor': 0.01},
                'roe': {'excellent': 0.12, 'good': 0.08, 'average': 0.05, 'poor': 0.02},
                'debt_to_equity': {'excellent': 8.0, 'good': 12.0, 'average': 16.0, 'poor': 20.0},
                'gross_margin': {'excellent': 0.80, 'good': 0.60, 'average': 0.40, 'poor': 0.20}
            },
            'General': {  # Default fallback benchmarks
                'current_ratio': {'excellent': 2.0, 'good': 1.5, 'average': 1.0, 'poor': 0.7},
                'roa': {'excellent': 0.10, 'good': 0.07, 'average': 0.04, 'poor': 0.02},
                'roe': {'excellent': 0.15, 'good': 0.10, 'average': 0.07, 'poor': 0.03},
                'debt_to_equity': {'excellent': 0.4, 'good': 0.7, 'average': 1.0, 'poor': 1.5},
                'gross_margin': {'excellent': 0.50, 'good': 0.35, 'average': 0.25, 'poor': 0.15}
            }
        }
    
    def calculate_industry_percentiles(self, company_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Calculate percentile rankings for each company across all financial metrics
        """
        try:
            if len(company_data) < 2:
                logger.warning("Need at least 2 companies for percentile calculation")
                return {}
            
            # Calculate financial ratios for all companies
            company_ratios = {}
            for company_name, data in company_data.items():
                try:
                    ratios = self.financial_calculator.calculate_financial_ratios(data.get('financial_metrics', {}))
                    if ratios and ratios.get('ratios'):
                        company_ratios[company_name] = ratios['ratios']
                except Exception as e:
                    logger.warning(f"Error calculating ratios for {company_name}: {str(e)}")
                    continue
            
            if not company_ratios:
                logger.warning("No valid ratios calculated for any company")
                return {}
            
            # Get all available metrics
            all_metrics = set()
            for ratios in company_ratios.values():
                all_metrics.update(ratios.keys())
            
            # Calculate percentiles for each metric
            percentile_rankings = {}
            for company_name in company_ratios.keys():
                percentile_rankings[company_name] = {}
            
            for metric in all_metrics:
                # Get values for this metric across all companies
                metric_values = []
                company_metric_map = {}
                
                for company_name, ratios in company_ratios.items():
                    if metric in ratios and ratios[metric] is not None:
                        ratio_data = ratios[metric]

                        # Extract value from ratio data structure
                        if isinstance(ratio_data, dict):
                            value = ratio_data.get('value')
                        else:
                            value = ratio_data

                        if value is not None and isinstance(value, (int, float)) and not np.isnan(value):
                            metric_values.append(value)
                            company_metric_map[company_name] = value
                
                # Calculate percentiles if we have enough data
                if len(metric_values) >= 2:
                    for company_name, value in company_metric_map.items():
                        # Determine if higher is better for this metric
                        higher_is_better = self.metric_orientation.get(metric, True)
                        
                        # Calculate percentile rank based on metric orientation
                        if higher_is_better:
                            percentile = stats.percentileofscore(metric_values, value, kind='rank')
                            rank = sorted(metric_values, reverse=True).index(value) + 1
                        else:
                            # For "lower is better" metrics, use negated values for correct percentile calculation
                            negated_values = [-v for v in metric_values]
                            percentile = stats.percentileofscore(negated_values, -value, kind='rank')
                            rank = sorted(metric_values).index(value) + 1
                        
                        percentile_rankings[company_name][metric] = {
                            'value': value,
                            'percentile': percentile,
                            'rank': rank,
                            'total_companies': len(metric_values),
                            'orientation': 'Higher is Better' if higher_is_better else 'Lower is Better'
                        }
            
            logger.info(f"Calculated percentiles for {len(percentile_rankings)} companies")
            return percentile_rankings
            
        except Exception as e:
            logger.error(f"Error calculating industry percentiles: {str(e)}")
            return {}
    
    def determine_industry_sector(self, company_name: str, company_data: Dict) -> str:
        """
        Determine the industry sector for a company based on available data
        """
        try:
            # Check if industry is explicitly mentioned in company info
            basic_info = company_data.get('basic_info', {})
            if 'industry' in basic_info:
                industry = basic_info['industry'].lower()
                if 'tech' in industry or 'software' in industry:
                    return 'Technology'
                elif 'manufactur' in industry or 'industrial' in industry:
                    return 'Manufacturing'
                elif 'retail' in industry or 'consumer' in industry:
                    return 'Retail'
                elif 'financial' in industry or 'bank' in industry:
                    return 'Financial Services'
            
            # Simple heuristic based on company name
            name_lower = company_name.lower()
            if any(term in name_lower for term in ['tech', 'software', 'systems', 'data']):
                return 'Technology'
            elif any(term in name_lower for term in ['bank', 'financial', 'capital', 'investment']):
                return 'Financial Services'
            elif any(term in name_lower for term in ['retail', 'store', 'shop']):
                return 'Retail'
            elif any(term in name_lower for term in ['manufacturing', 'industrial', 'corp']):
                return 'Manufacturing'
            
            return 'General'
            
        except Exception as e:
            logger.warning(f"Error determining industry for {company_name}: {str(e)}")
            return 'General'
    
    def benchmark_against_industry(self, company_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Benchmark each company against industry standards
        """
        try:
            benchmarking_results = {}
            
            for company_name, data in company_data.items():
                # Determine industry sector
                industry = self.determine_industry_sector(company_name, data)
                benchmarks = self.industry_benchmarks.get(industry, self.industry_benchmarks['General'])
                
                # Calculate company ratios
                try:
                    ratios = self.financial_calculator.calculate_financial_ratios(data.get('financial_metrics', {}))
                    if not ratios or not ratios.get('ratios'):
                        continue
                    
                    company_ratios = ratios['ratios']
                    
                    # Compare against benchmarks
                    benchmark_comparison = {
                        'industry': industry,
                        'metrics': {},
                        'overall_score': 0,
                        'category_scores': {}
                    }
                    
                    total_score = 0
                    metrics_compared = 0
                    
                    for metric, value in company_ratios.items():
                        if metric in benchmarks and value is not None:
                            benchmark = benchmarks[metric]

                            # Type validation and conversion
                            try:
                                # Handle different value types
                                if isinstance(value, dict):
                                    # If value is a dict, try to extract a numeric value
                                    if 'value' in value:
                                        numeric_value = value['value']
                                    elif 'amount' in value:
                                        numeric_value = value['amount']
                                    else:
                                        # Skip this metric if we can't extract a numeric value
                                        logger.debug(f"Skipping metric {metric} - value is dict without numeric field: {value}")
                                        continue
                                elif isinstance(value, (int, float)):
                                    numeric_value = float(value)
                                elif isinstance(value, str):
                                    # Try to convert string to float
                                    try:
                                        numeric_value = float(value.replace(',', '').replace('%', ''))
                                    except ValueError:
                                        logger.debug(f"Skipping metric {metric} - cannot convert string to number: {value}")
                                        continue
                                else:
                                    logger.debug(f"Skipping metric {metric} - unsupported type {type(value)}: {value}")
                                    continue

                                # Validate that we have a valid numeric value
                                if not isinstance(numeric_value, (int, float)) or not np.isfinite(numeric_value):
                                    logger.debug(f"Skipping metric {metric} - invalid numeric value: {numeric_value}")
                                    continue

                            except Exception as e:
                                logger.debug(f"Error processing metric {metric} with value {value}: {str(e)}")
                                continue

                            # Determine if higher is better for this metric
                            higher_is_better = self.metric_orientation.get(metric, True)

                            # Determine performance level based on metric orientation
                            if higher_is_better:
                                # Standard comparison - higher values are better
                                if numeric_value >= benchmark['excellent']:
                                    performance = 'Excellent'
                                    score = 4
                                elif numeric_value >= benchmark['good']:
                                    performance = 'Good'
                                    score = 3
                                elif numeric_value >= benchmark['average']:
                                    performance = 'Average'
                                    score = 2
                                elif numeric_value >= benchmark['poor']:
                                    performance = 'Below Average'
                                    score = 1
                                else:
                                    performance = 'Poor'
                                    score = 0
                            else:
                                # Inverse comparison - lower values are better
                                if numeric_value <= benchmark['excellent']:
                                    performance = 'Excellent'
                                    score = 4
                                elif numeric_value <= benchmark['good']:
                                    performance = 'Good'
                                    score = 3
                                elif numeric_value <= benchmark['average']:
                                    performance = 'Average'
                                    score = 2
                                elif numeric_value <= benchmark['poor']:
                                    performance = 'Below Average'
                                    score = 1
                                else:
                                    performance = 'Poor'
                                    score = 0
                            
                            benchmark_comparison['metrics'][metric] = {
                                'value': numeric_value,
                                'original_value': value,
                                'performance': performance,
                                'score': score,
                                'benchmarks': benchmark
                            }
                            
                            total_score += score
                            metrics_compared += 1
                    
                    if metrics_compared > 0:
                        benchmark_comparison['overall_score'] = total_score / metrics_compared
                    
                    benchmarking_results[company_name] = benchmark_comparison
                    
                except Exception as e:
                    logger.warning(f"Error benchmarking {company_name}: {str(e)}")
                    continue
            
            logger.info(f"Benchmarked {len(benchmarking_results)} companies")
            return benchmarking_results
            
        except Exception as e:
            logger.error(f"Error in industry benchmarking: {str(e)}")
            return {}
    
    def create_competitive_positioning_chart(self, percentile_data: Dict[str, Dict]) -> Optional[go.Figure]:
        """
        Create a competitive positioning radar chart
        """
        try:
            if not percentile_data:
                return None
            
            # Select key metrics for positioning
            key_metrics = ['current_ratio', 'roa', 'roe', 'debt_to_equity', 'gross_margin']
            
            fig = go.Figure()
            
            # Color palette for companies
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            
            for i, (company_name, metrics) in enumerate(percentile_data.items()):
                # Extract percentiles for key metrics
                percentiles = []
                metric_labels = []
                
                for metric in key_metrics:
                    if metric in metrics:
                        percentiles.append(metrics[metric]['percentile'])
                        metric_labels.append(metric.replace('_', ' ').title())
                
                if percentiles:
                    # Close the radar chart
                    percentiles.append(percentiles[0])
                    metric_labels.append(metric_labels[0])
                    
                    fig.add_trace(go.Scatterpolar(
                        r=percentiles,
                        theta=metric_labels,
                        fill='toself',
                        name=company_name,
                        line_color=colors[i % len(colors)]
                    ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Competitive Positioning Analysis<br><sub>Percentile Rankings Across Key Metrics</sub>",
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating positioning chart: {str(e)}")
            return None
    
    def create_industry_benchmark_chart(self, benchmark_data: Dict[str, Dict]) -> Optional[go.Figure]:
        """
        Create industry benchmark comparison chart
        """
        try:
            if not benchmark_data:
                return None
            
            # Prepare data for plotting
            companies = list(benchmark_data.keys())
            overall_scores = [data['overall_score'] for data in benchmark_data.values()]
            industries = [data['industry'] for data in benchmark_data.values()]
            
            fig = go.Figure()
            
            # Create bar chart with industry color coding
            industry_colors = {
                'Technology': 'blue',
                'Manufacturing': 'green', 
                'Retail': 'orange',
                'Financial Services': 'red',
                'General': 'gray'
            }
            
            colors = [industry_colors.get(industry, 'gray') for industry in industries]
            
            fig.add_trace(go.Bar(
                x=companies,
                y=overall_scores,
                marker_color=colors,
                text=[f"{score:.2f}" for score in overall_scores],
                textposition='auto',
                name='Overall Score'
            ))
            
            # Add benchmark lines
            fig.add_hline(y=4.0, line_dash="dash", line_color="green", 
                         annotation_text="Excellent (4.0)")
            fig.add_hline(y=3.0, line_dash="dash", line_color="blue", 
                         annotation_text="Good (3.0)")
            fig.add_hline(y=2.0, line_dash="dash", line_color="orange", 
                         annotation_text="Average (2.0)")
            fig.add_hline(y=1.0, line_dash="dash", line_color="red", 
                         annotation_text="Below Average (1.0)")
            
            fig.update_layout(
                title="Industry Benchmark Performance",
                xaxis_title="Companies",
                yaxis_title="Overall Benchmark Score",
                yaxis=dict(range=[0, 4.5]),
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating benchmark chart: {str(e)}")
            return None
    
    def generate_competitive_insights(self, percentile_data: Dict[str, Dict], 
                                    benchmark_data: Dict[str, Dict]) -> List[str]:
        """
        Generate AI-powered competitive insights
        """
        try:
            insights = []
            
            if not percentile_data or not benchmark_data:
                return ["Insufficient data for competitive analysis."]
            
            # Overall performance analysis
            company_scores = [(name, data['overall_score']) for name, data in benchmark_data.items()]
            company_scores.sort(key=lambda x: x[1], reverse=True)
            
            if company_scores:
                best_performer = company_scores[0]
                worst_performer = company_scores[-1]
                
                insights.append(f"🏆 **Top Performer**: {best_performer[0]} leads with an overall benchmark score of {best_performer[1]:.2f}/4.0")
                
                if len(company_scores) > 1:
                    insights.append(f"📉 **Needs Improvement**: {worst_performer[0]} has the lowest score at {worst_performer[1]:.2f}/4.0")
            
            # Industry distribution
            industries = [data['industry'] for data in benchmark_data.values()]
            industry_counts = {}
            for industry in industries:
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
            
            if industry_counts:
                dominant_industry = max(industry_counts.items(), key=lambda x: x[1])
                insights.append(f"🏭 **Industry Mix**: {dominant_industry[0]} sector dominates with {dominant_industry[1]} companies")
            
            # Metric-specific insights
            if percentile_data:
                # Find companies excelling in specific areas
                high_performers = {}
                for company, metrics in percentile_data.items():
                    for metric, data in metrics.items():
                        if data['percentile'] >= 80:  # Top 20%
                            if metric not in high_performers:
                                high_performers[metric] = []
                            high_performers[metric].append(company)
                
                for metric, companies in high_performers.items():
                    if len(companies) == 1:
                        insights.append(f"⭐ **{metric.replace('_', ' ').title()} Leader**: {companies[0]} ranks in the top 20%")
            
            # Performance gaps analysis
            if len(company_scores) > 1:
                score_gap = company_scores[0][1] - company_scores[-1][1]
                if score_gap > 1.5:
                    insights.append(f"📊 **Significant Performance Gap**: {score_gap:.2f} points separate the top and bottom performers")
                elif score_gap < 0.5:
                    insights.append("🤝 **Competitive Market**: Companies show similar performance levels across benchmarks")
            
            return insights[:6]  # Limit to 6 key insights
            
        except Exception as e:
            logger.error(f"Error generating competitive insights: {str(e)}")
            return ["Error generating competitive insights."]