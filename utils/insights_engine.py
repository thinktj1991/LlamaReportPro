"""
AI-Powered Insights Engine with Pattern Recognition and Anomaly Detection

This module provides advanced AI-driven analysis capabilities including:
- Pattern recognition in financial data
- Anomaly detection and risk assessment  
- Automated insights generation
- Trend analysis and forecasting signals
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import streamlit as st
import logging
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from utils.financial_calculator import FinancialCalculator

# Configure logging
logger = logging.getLogger(__name__)

class InsightsEngine:
    """
    AI-powered insights engine for financial analysis
    """
    
    def __init__(self):
        self.financial_calculator = FinancialCalculator()
        
        # Risk patterns and thresholds
        self.risk_patterns = {
            'liquidity_crisis': {
                'indicators': ['current_ratio', 'quick_ratio', 'cash_ratio'],
                'thresholds': {'current_ratio': 1.0, 'quick_ratio': 0.7, 'cash_ratio': 0.1},
                'severity': 'High',
                'description': 'Company may struggle to meet short-term obligations'
            },
            'excessive_leverage': {
                'indicators': ['debt_to_equity', 'debt_ratio', 'times_interest_earned'],
                'thresholds': {'debt_to_equity': 2.0, 'debt_ratio': 0.6, 'times_interest_earned': 2.0},
                'severity': 'High',
                'description': 'High debt levels may indicate financial distress risk'
            },
            'declining_profitability': {
                'indicators': ['gross_margin', 'operating_margin', 'net_margin', 'roa', 'roe'],
                'thresholds': {'gross_margin': 0.15, 'operating_margin': 0.05, 'net_margin': 0.02, 'roa': 0.02, 'roe': 0.05},
                'severity': 'Medium',
                'description': 'Profitability metrics are below healthy levels'
            },
            'operational_inefficiency': {
                'indicators': ['asset_turnover', 'inventory_turnover', 'receivables_turnover'],
                'thresholds': {'asset_turnover': 0.5, 'inventory_turnover': 2.0, 'receivables_turnover': 4.0},
                'severity': 'Medium',
                'description': 'Company may be inefficiently using its assets'
            }
        }
        
        # Pattern recognition categories
        self.pattern_categories = {
            'growth_patterns': ['revenue_growth', 'profit_growth', 'asset_growth'],
            'efficiency_patterns': ['margin_trends', 'turnover_trends', 'productivity_trends'],
            'stability_patterns': ['consistency', 'volatility', 'predictability'],
            'competitive_patterns': ['market_position', 'relative_performance', 'industry_comparison']
        }
    
    def detect_financial_anomalies(self, company_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Detect anomalies in financial data using machine learning
        """
        try:
            if not company_data:
                return {'anomalies': [], 'analysis': 'Insufficient data for anomaly detection'}
            
            # Prepare data for anomaly detection
            features_data = []
            company_names = []
            
            for company_name, data in company_data.items():
                ratios_result = self.financial_calculator.calculate_financial_ratios(
                    data.get('financial_metrics', {}), company_name
                )
                
                if ratios_result and ratios_result.get('ratios'):
                    ratios = ratios_result['ratios']
                    # Create feature vector from ratios
                    features = []
                    for metric in ['current_ratio', 'debt_to_equity', 'roa', 'roe', 'gross_margin', 
                                 'operating_margin', 'asset_turnover', 'times_interest_earned']:
                        value = ratios.get(metric, 0)
                        if value is None or np.isnan(value):
                            value = 0
                        features.append(float(value))
                    
                    if len(features) == 8:  # Ensure we have all features
                        features_data.append(features)
                        company_names.append(company_name)
            
            if len(features_data) < 2:
                return {'anomalies': [], 'analysis': 'Need at least 2 companies for anomaly detection'}
            
            # Perform anomaly detection
            features_array = np.array(features_data)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features_array)
            
            # Use Isolation Forest for anomaly detection
            iso_forest = IsolationForest(contamination='auto', random_state=42)
            anomaly_predictions = iso_forest.fit_predict(features_scaled)
            anomaly_scores = iso_forest.decision_function(features_scaled)
            
            # Identify anomalies
            anomalies = []
            for i, (company_name, is_anomaly, score) in enumerate(zip(company_names, anomaly_predictions, anomaly_scores)):
                if is_anomaly == -1:  # Anomaly detected
                    # Determine which metrics are driving the anomaly
                    feature_importance = abs(features_scaled[i])
                    metric_names = ['current_ratio', 'debt_to_equity', 'roa', 'roe', 'gross_margin', 
                                  'operating_margin', 'asset_turnover', 'times_interest_earned']
                    
                    top_factors = sorted(zip(metric_names, feature_importance), 
                                       key=lambda x: x[1], reverse=True)[:3]
                    
                    anomalies.append({
                        'company': company_name,
                        'anomaly_score': float(score),
                        'severity': 'High' if score < -0.5 else 'Medium',
                        'top_factors': [factor[0] for factor in top_factors],
                        'description': f'Anomalous financial pattern detected with score {score:.3f}'
                    })
            
            # Generate analysis summary
            analysis = self._generate_anomaly_analysis(anomalies, len(company_names))
            
            return {
                'anomalies': anomalies,
                'analysis': analysis,
                'total_companies': len(company_names),
                'anomaly_rate': len(anomalies) / len(company_names) if company_names else 0
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return {'anomalies': [], 'analysis': f'Error in anomaly detection: {str(e)}'}
    
    def identify_risk_patterns(self, company_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Identify predefined risk patterns in company data
        """
        try:
            risk_analysis = {
                'company_risks': {},
                'overall_assessment': {},
                'recommendations': []
            }
            
            for company_name, data in company_data.items():
                ratios_result = self.financial_calculator.calculate_financial_ratios(
                    data.get('financial_metrics', {}), company_name
                )
                
                if not ratios_result or not ratios_result.get('ratios'):
                    continue
                
                ratios = ratios_result['ratios']
                company_risks = []
                risk_score = 0
                
                # Check each risk pattern
                for pattern_name, pattern_config in self.risk_patterns.items():
                    pattern_triggered = False
                    triggered_indicators = []
                    
                    for indicator in pattern_config['indicators']:
                        if indicator in ratios and ratios[indicator] is not None:
                            value = ratios[indicator]
                            threshold = pattern_config['thresholds'].get(indicator)
                            
                            if threshold is not None:
                                # Check if risk threshold is breached
                                if pattern_name in ['liquidity_crisis', 'declining_profitability', 'operational_inefficiency']:
                                    # Lower values indicate higher risk
                                    if value < threshold:
                                        pattern_triggered = True
                                        triggered_indicators.append(indicator)
                                elif pattern_name == 'excessive_leverage':
                                    # Higher debt ratios or lower coverage ratios indicate risk
                                    if indicator in ['debt_to_equity', 'debt_ratio'] and value > threshold:
                                        pattern_triggered = True
                                        triggered_indicators.append(indicator)
                                    elif indicator == 'times_interest_earned' and value < threshold:
                                        pattern_triggered = True
                                        triggered_indicators.append(indicator)
                    
                    if pattern_triggered:
                        severity_weight = {'High': 3, 'Medium': 2, 'Low': 1}
                        risk_score += severity_weight.get(pattern_config['severity'], 1)
                        
                        company_risks.append({
                            'pattern': pattern_name,
                            'severity': pattern_config['severity'],
                            'description': pattern_config['description'],
                            'triggered_indicators': triggered_indicators,
                            'affected_metrics': {ind: ratios.get(ind) for ind in triggered_indicators}
                        })
                
                risk_analysis['company_risks'][company_name] = {
                    'risks': company_risks,
                    'risk_score': risk_score,
                    'risk_level': self._categorize_risk_level(risk_score)
                }
            
            # Generate overall assessment
            risk_analysis['overall_assessment'] = self._generate_risk_assessment(risk_analysis['company_risks'])
            risk_analysis['recommendations'] = self._generate_risk_recommendations(risk_analysis['company_risks'])
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error in risk pattern identification: {str(e)}")
            return {'company_risks': {}, 'overall_assessment': {}, 'recommendations': []}
    
    def generate_ai_insights(self, company_data: Dict[str, Dict], 
                           anomalies: Dict[str, Any], risks: Dict[str, Any]) -> List[str]:
        """
        Generate AI-powered insights combining multiple analysis dimensions
        """
        try:
            insights = []
            
            if not company_data:
                return ["Insufficient data for AI insights generation"]
            
            # Performance insights
            performance_insights = self._analyze_performance_patterns(company_data)
            insights.extend(performance_insights)
            
            # Risk insights
            if risks.get('company_risks'):
                risk_insights = self._analyze_risk_insights(risks)
                insights.extend(risk_insights)
            
            # Anomaly insights
            if anomalies.get('anomalies'):
                anomaly_insights = self._analyze_anomaly_insights(anomalies)
                insights.extend(anomaly_insights)
            
            # Comparative insights
            if len(company_data) > 1:
                comparative_insights = self._analyze_comparative_insights(company_data)
                insights.extend(comparative_insights)
            
            # Trend insights
            trend_insights = self._analyze_trend_insights(company_data)
            insights.extend(trend_insights)
            
            return insights[:10]  # Limit to top 10 insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return [f"Error generating insights: {str(e)}"]
    
    def create_anomaly_visualization(self, anomalies: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create visualization for anomaly detection results
        """
        try:
            if not anomalies.get('anomalies'):
                return None
            
            anomaly_data = anomalies['anomalies']
            companies = [a['company'] for a in anomaly_data]
            scores = [a['anomaly_score'] for a in anomaly_data]
            severities = [a['severity'] for a in anomaly_data]
            
            # Color mapping for severity
            color_map = {'High': 'red', 'Medium': 'orange', 'Low': 'yellow'}
            colors = [color_map.get(sev, 'gray') for sev in severities]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=companies,
                y=scores,
                mode='markers',
                marker=dict(
                    size=15,
                    color=colors,
                    line=dict(width=2, color='darkblue')
                ),
                text=[f"Severity: {sev}<br>Score: {score:.3f}" for sev, score in zip(severities, scores)],
                textposition='top center',
                name='Anomaly Detection'
            ))
            
            # Add threshold line
            fig.add_hline(y=-0.5, line_dash="dash", line_color="red", 
                         annotation_text="High Risk Threshold")
            
            fig.update_layout(
                title="Financial Anomaly Detection Results",
                xaxis_title="Companies",
                yaxis_title="Anomaly Score (Lower = More Anomalous)",
                height=500,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating anomaly visualization: {str(e)}")
            return None
    
    def create_risk_heatmap(self, risks: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create risk pattern heatmap
        """
        try:
            if not risks.get('company_risks'):
                return None
            
            company_risks = risks['company_risks']
            companies = list(company_risks.keys())
            risk_patterns = list(self.risk_patterns.keys())
            
            # Create risk matrix
            risk_matrix = []
            for pattern in risk_patterns:
                pattern_row = []
                for company in companies:
                    company_risk_data = company_risks[company]['risks']
                    risk_level = 0
                    for risk in company_risk_data:
                        if risk['pattern'] == pattern:
                            severity_map = {'High': 3, 'Medium': 2, 'Low': 1}
                            risk_level = severity_map.get(risk['severity'], 0)
                            break
                    pattern_row.append(risk_level)
                risk_matrix.append(pattern_row)
            
            fig = go.Figure(data=go.Heatmap(
                z=risk_matrix,
                x=companies,
                y=[p.replace('_', ' ').title() for p in risk_patterns],
                colorscale=[[0, 'green'], [0.33, 'yellow'], [0.66, 'orange'], [1, 'red']],
                colorbar=dict(
                    title="Risk Level",
                    tickvals=[0, 1, 2, 3],
                    ticktext=['None', 'Low', 'Medium', 'High']
                )
            ))
            
            fig.update_layout(
                title="Risk Pattern Heatmap",
                xaxis_title="Companies",
                yaxis_title="Risk Patterns",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating risk heatmap: {str(e)}")
            return None
    
    # Helper methods
    def _generate_anomaly_analysis(self, anomalies: List[Dict], total_companies: int) -> str:
        """Generate analysis summary for anomalies"""
        if not anomalies:
            return "No significant anomalies detected in the financial data."
        
        high_risk = sum(1 for a in anomalies if a['severity'] == 'High')
        medium_risk = len(anomalies) - high_risk
        
        analysis = f"Detected {len(anomalies)} anomalies out of {total_companies} companies. "
        if high_risk > 0:
            analysis += f"{high_risk} companies show high-risk anomalous patterns. "
        if medium_risk > 0:
            analysis += f"{medium_risk} companies show medium-risk patterns. "
        
        analysis += "These anomalies may indicate unique business models, data quality issues, or potential risks requiring investigation."
        
        return analysis
    
    def _categorize_risk_level(self, risk_score: int) -> str:
        """Categorize overall risk level based on score"""
        if risk_score >= 6:
            return 'High Risk'
        elif risk_score >= 3:
            return 'Medium Risk'
        elif risk_score >= 1:
            return 'Low Risk'
        else:
            return 'Low Risk'
    
    def _generate_risk_assessment(self, company_risks: Dict) -> Dict[str, Any]:
        """Generate overall risk assessment"""
        if not company_risks:
            return {}
        
        total_companies = len(company_risks)
        high_risk_companies = sum(1 for data in company_risks.values() if data['risk_level'] == 'High Risk')
        medium_risk_companies = sum(1 for data in company_risks.values() if data['risk_level'] == 'Medium Risk')
        
        # Count pattern frequencies
        pattern_counts = {}
        for company_data in company_risks.values():
            for risk in company_data['risks']:
                pattern = risk['pattern']
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        most_common_risk = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else None
        
        return {
            'total_companies': total_companies,
            'high_risk_count': high_risk_companies,
            'medium_risk_count': medium_risk_companies,
            'low_risk_count': total_companies - high_risk_companies - medium_risk_companies,
            'most_common_risk': most_common_risk[0] if most_common_risk else None,
            'risk_concentration': most_common_risk[1] / total_companies if most_common_risk else 0
        }
    
    def _generate_risk_recommendations(self, company_risks: Dict) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if not company_risks:
            return recommendations
        
        # Analyze common patterns
        pattern_counts = {}
        for company_data in company_risks.values():
            for risk in company_data['risks']:
                pattern = risk['pattern']
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Generate recommendations based on most common risks
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            if pattern == 'liquidity_crisis':
                recommendations.append("🚨 **Liquidity Management**: Companies should improve working capital management and maintain adequate cash reserves")
            elif pattern == 'excessive_leverage':
                recommendations.append("⚖️ **Debt Management**: Review debt structures and consider deleveraging strategies to reduce financial risk")
            elif pattern == 'declining_profitability':
                recommendations.append("📈 **Profitability Enhancement**: Focus on cost optimization and revenue growth strategies")
            elif pattern == 'operational_inefficiency':
                recommendations.append("🔧 **Operational Improvement**: Enhance asset utilization and streamline operational processes")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _analyze_performance_patterns(self, company_data: Dict) -> List[str]:
        """Analyze performance patterns across companies"""
        insights = []
        
        try:
            # Calculate average ratios across companies
            all_ratios = {}
            for company_name, data in company_data.items():
                ratios_result = self.financial_calculator.calculate_financial_ratios(
                    data.get('financial_metrics', {}), company_name
                )
                if ratios_result and ratios_result.get('ratios'):
                    for metric, value in ratios_result['ratios'].items():
                        if value is not None and not np.isnan(value):
                            if metric not in all_ratios:
                                all_ratios[metric] = []
                            all_ratios[metric].append(value)
            
            # Identify strong and weak areas
            strong_areas = []
            weak_areas = []
            
            benchmarks = {
                'roa': 0.05, 'roe': 0.10, 'current_ratio': 1.5,
                'debt_to_equity': 1.0, 'gross_margin': 0.25
            }
            
            for metric, values in all_ratios.items():
                if len(values) > 0:
                    avg_value = np.mean(values)
                    benchmark = benchmarks.get(metric)
                    
                    if benchmark:
                        if metric in ['debt_to_equity']:  # Lower is better
                            if avg_value < benchmark:
                                strong_areas.append(metric)
                            else:
                                weak_areas.append(metric)
                        else:  # Higher is better
                            if avg_value > benchmark:
                                strong_areas.append(metric)
                            else:
                                weak_areas.append(metric)
            
            if strong_areas:
                insights.append(f"💪 **Strong Performance Areas**: Companies excel in {', '.join(strong_areas[:3])}")
            
            if weak_areas:
                insights.append(f"⚠️ **Areas for Improvement**: Companies show weakness in {', '.join(weak_areas[:3])}")
            
        except Exception as e:
            logger.warning(f"Error analyzing performance patterns: {str(e)}")
        
        return insights
    
    def _analyze_risk_insights(self, risks: Dict) -> List[str]:
        """Analyze risk-related insights"""
        insights = []
        
        try:
            assessment = risks.get('overall_assessment', {})
            
            if assessment.get('high_risk_count', 0) > 0:
                insights.append(f"🚨 **High Risk Alert**: {assessment['high_risk_count']} companies identified with high-risk financial patterns")
            
            if assessment.get('most_common_risk'):
                risk_name = assessment['most_common_risk'].replace('_', ' ').title()
                concentration = assessment.get('risk_concentration', 0)
                insights.append(f"📊 **Common Risk Pattern**: {risk_name} affects {concentration:.0%} of analyzed companies")
            
        except Exception as e:
            logger.warning(f"Error analyzing risk insights: {str(e)}")
        
        return insights
    
    def _analyze_anomaly_insights(self, anomalies: Dict) -> List[str]:
        """Analyze anomaly-related insights"""
        insights = []
        
        try:
            anomaly_list = anomalies.get('anomalies', [])
            anomaly_rate = anomalies.get('anomaly_rate', 0)
            
            if anomaly_rate > 0.3:
                insights.append(f"🔍 **High Anomaly Rate**: {anomaly_rate:.0%} of companies show anomalous financial patterns")
            
            # Analyze common anomaly factors
            factor_counts = {}
            for anomaly in anomaly_list:
                for factor in anomaly.get('top_factors', []):
                    factor_counts[factor] = factor_counts.get(factor, 0) + 1
            
            if factor_counts:
                top_factor = max(factor_counts.items(), key=lambda x: x[1])
                insights.append(f"🎯 **Primary Anomaly Driver**: {top_factor[0].replace('_', ' ').title()} is the most common factor in anomalous patterns")
            
        except Exception as e:
            logger.warning(f"Error analyzing anomaly insights: {str(e)}")
        
        return insights
    
    def _analyze_comparative_insights(self, company_data: Dict) -> List[str]:
        """Analyze comparative insights across companies"""
        insights = []
        
        try:
            if len(company_data) < 2:
                return insights
            
            # Compare company performance
            company_scores = {}
            for company_name, data in company_data.items():
                ratios_result = self.financial_calculator.calculate_financial_ratios(
                    data.get('financial_metrics', {}), company_name
                )
                if ratios_result:
                    company_scores[company_name] = ratios_result.get('overall_score', 0)
            
            if company_scores:
                best_performer = max(company_scores.items(), key=lambda x: x[1])
                worst_performer = min(company_scores.items(), key=lambda x: x[1])
                
                score_gap = best_performer[1] - worst_performer[1]
                
                insights.append(f"🏆 **Top Performer**: {best_performer[0]} leads with overall score of {best_performer[1]:.2f}")
                
                if score_gap > 1.0:
                    insights.append(f"📈 **Performance Gap**: {score_gap:.2f} point difference between best and worst performers indicates significant variation")
                
        except Exception as e:
            logger.warning(f"Error analyzing comparative insights: {str(e)}")
        
        return insights
    
    def _analyze_trend_insights(self, company_data: Dict) -> List[str]:
        """Analyze trend-related insights"""
        insights = []
        
        try:
            # Simple trend analysis based on available data
            # This could be enhanced with time-series data when available
            
            for company_name, data in company_data.items():
                metrics = data.get('financial_metrics', {})
                
                # Look for potential growth indicators
                revenue = metrics.get('revenue', 0)
                profit = metrics.get('profit', 0)
                
                if revenue > 0 and profit > 0:
                    profit_margin = profit / revenue
                    if profit_margin > 0.15:
                        insights.append(f"📈 **Growth Indicator**: {company_name} shows strong profitability with {profit_margin:.1%} profit margin")
                        break
            
        except Exception as e:
            logger.warning(f"Error analyzing trend insights: {str(e)}")
        
        return insights