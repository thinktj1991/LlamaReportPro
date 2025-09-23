import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import logging
from utils.data_visualizer import DataVisualizer

# Configure logging
logger = logging.getLogger(__name__)

class CompanyComparator:
    def __init__(self):
        self.visualizer = DataVisualizer()
        self.financial_metrics = [
            'revenue', 'income', 'profit', 'loss', 'assets', 'liabilities',
            'equity', 'cash', 'debt', 'earnings', 'ebitda', 'margin',
            'expenses', 'sales', 'operating income', 'net income'
        ]
    
    def prepare_company_data(self, processed_documents: Dict[str, Any], 
                           extracted_tables: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """
        Prepare and organize company data for comparison
        """
        company_data = {}
        
        try:
            for doc_name, doc_data in processed_documents.items():
                # Extract company information
                company_info = doc_data.get('company_info', {})
                company_name = company_info.get('company_name', doc_name)
                
                # Prepare company entry
                company_entry = {
                    'name': company_name,
                    'year': company_info.get('year', 'Unknown'),
                    'document_file': doc_name,
                    'basic_info': company_info,
                    'financial_metrics': {},
                    'tables': extracted_tables.get(doc_name, []),
                    'key_statistics': {}
                }
                
                # Extract financial metrics from tables
                financial_data = self._extract_financial_metrics(extracted_tables.get(doc_name, []))
                company_entry['financial_metrics'] = financial_data
                
                # Calculate key statistics
                key_stats = self._calculate_key_statistics(doc_data, extracted_tables.get(doc_name, []))
                company_entry['key_statistics'] = key_stats
                
                company_data[company_name] = company_entry
                
            logger.info(f"Prepared data for {len(company_data)} companies")
            return company_data
            
        except Exception as e:
            logger.error(f"Error preparing company data: {str(e)}")
            return {}
    
    def _extract_financial_metrics(self, tables: List[Dict]) -> Dict[str, float]:
        """
        Extract financial metrics from company tables
        """
        metrics = {}
        
        try:
            for table in tables:
                if not table.get('is_financial', False):
                    continue
                
                df = table['dataframe']
                
                # Search for financial metrics in the table
                for metric in self.financial_metrics:
                    if metric in metrics:  # Skip if already found
                        continue
                    
                    # Search in column names
                    for col in df.columns:
                        if metric.lower() in col.lower():
                            # Try to extract numeric value
                            values = self._extract_numeric_values(df[col])
                            if values:
                                metrics[metric] = values[0]  # Take first value
                                break
                    
                    # Search in cell content if not found in columns
                    if metric not in metrics:
                        for _, row in df.iterrows():
                            for cell in row:
                                if isinstance(cell, str) and metric.lower() in cell.lower():
                                    # Look for numbers in nearby cells
                                    row_values = self._extract_numeric_values(row)
                                    if row_values:
                                        metrics[metric] = row_values[0]
                                        break
                            if metric in metrics:
                                break
                
        except Exception as e:
            logger.error(f"Error extracting financial metrics: {str(e)}")
        
        return metrics
    
    def _extract_numeric_values(self, data) -> List[float]:
        """
        Extract numeric values from data series or individual values
        """
        values = []
        
        try:
            if hasattr(data, '__iter__') and not isinstance(data, str):
                # It's a series or list
                for item in data:
                    value = self._parse_numeric_value(item)
                    if value is not None:
                        values.append(value)
            else:
                # Single value
                value = self._parse_numeric_value(data)
                if value is not None:
                    values.append(value)
                    
        except Exception as e:
            logger.error(f"Error extracting numeric values: {str(e)}")
        
        return values
    
    def _parse_numeric_value(self, value) -> Optional[float]:
        """
        Parse a single value to extract numeric content
        """
        try:
            if pd.isna(value):
                return None
            
            # Convert to string for processing
            str_value = str(value).strip()
            
            if not str_value:
                return None
            
            # Remove common formatting
            cleaned = str_value.replace(',', '').replace('$', '').replace('%', '')
            cleaned = cleaned.replace('(', '-').replace(')', '')  # Handle negative numbers in parentheses
            
            # Try to extract number
            import re
            number_pattern = r'-?\d+\.?\d*'
            matches = re.findall(number_pattern, cleaned)
            
            if matches:
                return float(matches[0])
            
            return None
            
        except Exception:
            return None
    
    def _calculate_key_statistics(self, doc_data: Dict, tables: List[Dict]) -> Dict[str, Any]:
        """
        Calculate key statistics for a company
        """
        stats = {
            'document_pages': doc_data.get('page_count', 0),
            'total_tables': len(tables),
            'financial_tables': sum(1 for table in tables if table.get('is_financial', False)),
            'avg_table_importance': 0.0,
            'data_richness_score': 0.0
        }
        
        try:
            # Calculate average importance
            if tables:
                importance_scores = [table.get('importance_score', 0) for table in tables]
                stats['avg_table_importance'] = np.mean(importance_scores)
            
            # Calculate data richness score
            richness_factors = [
                min(stats['document_pages'] / 50, 1.0) * 0.3,  # Page factor
                min(stats['total_tables'] / 20, 1.0) * 0.3,     # Table factor
                min(stats['financial_tables'] / 10, 1.0) * 0.4  # Financial table factor
            ]
            stats['data_richness_score'] = sum(richness_factors)
            
        except Exception as e:
            logger.error(f"Error calculating key statistics: {str(e)}")
        
        return stats
    
    def create_comparison_table(self, company_data: Dict[str, Dict],
                              metrics_to_compare: List[str]) -> pd.DataFrame:
        """
        Create a comparison table for selected metrics with proper data type handling
        """
        try:
            if not company_data or not metrics_to_compare:
                return pd.DataFrame()

            comparison_data = []

            for company_name, data in company_data.items():
                row = {'Company': company_name, 'Year': data.get('year', 'Unknown')}

                # Add requested metrics with proper type conversion
                for metric in metrics_to_compare:
                    raw_value = data.get('financial_metrics', {}).get(metric)
                    cleaned_value = self._clean_financial_value(raw_value)
                    row[metric.title()] = cleaned_value

                # Add key statistics
                key_stats = data.get('key_statistics', {})
                row['Document Pages'] = key_stats.get('document_pages', 0)
                row['Financial Tables'] = key_stats.get('financial_tables', 0)
                row['Data Richness'] = f"{key_stats.get('data_richness_score', 0):.2f}"

                comparison_data.append(row)

            df = pd.DataFrame(comparison_data)

            # Ensure proper data types for Arrow compatibility
            df = self._ensure_arrow_compatibility(df)

            return df

        except Exception as e:
            logger.error(f"Error creating comparison table: {str(e)}")
            return pd.DataFrame()

    def _clean_financial_value(self, value):
        """
        Clean and standardize financial values for DataFrame compatibility
        """
        try:
            if value is None:
                return np.nan

            # Handle dictionary values
            if isinstance(value, dict):
                if 'value' in value:
                    return self._clean_financial_value(value['value'])
                elif 'amount' in value:
                    return self._clean_financial_value(value['amount'])
                elif 'total' in value:
                    return self._clean_financial_value(value['total'])
                else:
                    return np.nan

            # Handle numeric values
            if isinstance(value, (int, float)):
                if np.isfinite(value):
                    return float(value)
                else:
                    return np.nan

            # Handle string values
            if isinstance(value, str):
                # Check for N/A variants
                if value.strip().lower() in ['n/a', 'na', 'none', '', 'null']:
                    return np.nan

                # Try to convert string to number
                try:
                    # Remove common formatting
                    cleaned = value.replace(',', '').replace('%', '').replace('$', '').replace('¥', '').strip()
                    return float(cleaned)
                except ValueError:
                    return np.nan

            # Handle other types
            return np.nan

        except Exception as e:
            logger.debug(f"Error cleaning financial value {value}: {str(e)}")
            return np.nan

    def _ensure_arrow_compatibility(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame is compatible with Arrow serialization
        """
        try:
            # Make a copy to avoid modifying original
            df_clean = df.copy()

            # Process each column
            for col in df_clean.columns:
                if col in ['Company', 'Year', 'Data Richness']:
                    # Keep string columns as-is
                    continue
                else:
                    # Convert numeric columns
                    try:
                        # Replace any remaining problematic values
                        df_clean[col] = df_clean[col].replace(['N/A', 'None', None], np.nan)

                        # Try to convert to numeric
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

                    except Exception as e:
                        logger.debug(f"Could not convert column {col} to numeric: {str(e)}")
                        # If conversion fails, replace with NaN
                        df_clean[col] = np.nan

            return df_clean

        except Exception as e:
            logger.error(f"Error ensuring Arrow compatibility: {str(e)}")
            return df

    def identify_available_metrics(self, company_data: Dict[str, Dict]) -> List[str]:
        """
        Identify metrics that are available across companies
        """
        all_metrics = set()
        
        try:
            for company_name, data in company_data.items():
                financial_metrics = data.get('financial_metrics', {})
                all_metrics.update(financial_metrics.keys())
            
            return sorted(list(all_metrics))
            
        except Exception as e:
            logger.error(f"Error identifying available metrics: {str(e)}")
            return []
    
    def calculate_metric_coverage(self, company_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate how many companies have each metric (coverage percentage)
        """
        metric_coverage = {}
        
        try:
            if not company_data:
                return metric_coverage
            
            total_companies = len(company_data)
            all_metrics = self.identify_available_metrics(company_data)
            
            for metric in all_metrics:
                companies_with_metric = 0
                for company_name, data in company_data.items():
                    if metric in data.get('financial_metrics', {}):
                        companies_with_metric += 1
                
                coverage_pct = (companies_with_metric / total_companies) * 100
                metric_coverage[metric] = coverage_pct
            
        except Exception as e:
            logger.error(f"Error calculating metric coverage: {str(e)}")
        
        return metric_coverage
    
    def generate_comparison_insights(self, company_data: Dict[str, Dict], 
                                   selected_metrics: List[str]) -> List[str]:
        """
        Generate insights from company comparison
        """
        insights = []
        
        try:
            if len(company_data) < 2:
                insights.append("Need at least 2 companies for meaningful comparison.")
                return insights
            
            company_names = list(company_data.keys())
            
            # Data availability insights
            total_metrics = len(self.identify_available_metrics(company_data))
            insights.append(f"Found {total_metrics} different financial metrics across all companies.")
            
            # Data richness comparison
            richness_scores = {name: data.get('key_statistics', {}).get('data_richness_score', 0) 
                             for name, data in company_data.items()}
            
            if richness_scores:
                best_data_company = max(richness_scores.keys(), key=lambda k: richness_scores[k])
                insights.append(f"{best_data_company} has the richest data set with a score of {richness_scores[best_data_company]:.2f}")
            
            # Metric-specific insights
            for metric in selected_metrics:
                metric_values = {}
                for company_name, data in company_data.items():
                    value = data.get('financial_metrics', {}).get(metric)
                    if value is not None and isinstance(value, (int, float)):
                        metric_values[company_name] = value
                
                if len(metric_values) >= 2:
                    highest = max(metric_values.keys(), key=lambda k: metric_values[k])
                    lowest = min(metric_values.keys(), key=lambda k: metric_values[k])
                    
                    if highest != lowest:
                        ratio = metric_values[highest] / metric_values[lowest] if metric_values[lowest] != 0 else float('inf')
                        insights.append(f"For {metric}: {highest} leads with {metric_values[highest]:,.0f}, {ratio:.1f}x higher than {lowest}")
            
            # Year comparison
            years = {name: data.get('year', 'Unknown') for name, data in company_data.items()}
            unique_years = set(years.values())
            if len(unique_years) > 1:
                insights.append(f"Comparing data across different years: {', '.join(sorted(unique_years))}")
            
        except Exception as e:
            logger.error(f"Error generating comparison insights: {str(e)}")
            insights.append("Error generating insights.")
        
        return insights
    
    def create_metric_trend_analysis(self, company_data: Dict[str, Dict], metric: str) -> Dict[str, Any]:
        """
        Analyze trends for a specific metric across companies
        """
        analysis = {
            'metric': metric,
            'companies_with_data': 0,
            'values': {},
            'statistics': {},
            'ranking': []
        }
        
        try:
            values = {}
            
            for company_name, data in company_data.items():
                value = data.get('financial_metrics', {}).get(metric)
                if value is not None and isinstance(value, (int, float)):
                    values[company_name] = value
            
            analysis['companies_with_data'] = len(values)
            analysis['values'] = values
            
            if values:
                vals = list(values.values())
                analysis['statistics'] = {
                    'mean': np.mean(vals),
                    'median': np.median(vals),
                    'std': np.std(vals),
                    'min': min(vals),
                    'max': max(vals)
                }
                
                # Create ranking
                sorted_companies = sorted(values.items(), key=lambda x: x[1], reverse=True)
                analysis['ranking'] = [(rank + 1, company, value) 
                                     for rank, (company, value) in enumerate(sorted_companies)]
            
        except Exception as e:
            logger.error(f"Error analyzing metric trend for {metric}: {str(e)}")
        
        return analysis
