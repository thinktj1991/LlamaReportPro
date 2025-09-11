import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import streamlit as st
import logging
import re
from io import StringIO

# Configure logging
logger = logging.getLogger(__name__)

class TableExtractor:
    def __init__(self):
        self.financial_keywords = [
            'revenue', 'income', 'profit', 'loss', 'assets', 'liabilities',
            'equity', 'cash', 'debt', 'earnings', 'ebitda', 'margin',
            'balance sheet', 'income statement', 'cash flow', 'expenses'
        ]
    
    def extract_and_process_tables(self, processed_documents: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Extract and process all tables from processed documents
        """
        all_tables = {}
        
        for doc_name, doc_data in processed_documents.items():
            try:
                doc_tables = []
                
                # Extract tables from detailed content
                if 'detailed_content' in doc_data:
                    for page in doc_data['detailed_content']['pages']:
                        for table_info in page['tables']:
                            processed_table = self._process_table(
                                table_info['data'], 
                                doc_name, 
                                page['page_number'],
                                table_info['table_id']
                            )
                            if processed_table:
                                doc_tables.append(processed_table)
                
                all_tables[doc_name] = doc_tables
                logger.info(f"Extracted {len(doc_tables)} tables from {doc_name}")
                
            except Exception as e:
                logger.error(f"Error extracting tables from {doc_name}: {str(e)}")
                all_tables[doc_name] = []
        
        return all_tables
    
    def _process_table(self, raw_table: List[List], doc_name: str, page_num: int, table_id: str) -> Optional[Dict]:
        """
        Process a raw table into a structured format
        """
        try:
            if not raw_table or len(raw_table) < 2:
                return None
            
            # Clean the table data
            cleaned_table = self._clean_table_data(raw_table)
            if not cleaned_table:
                return None
            
            # Convert to DataFrame
            try:
                # Ensure we have valid column names
                if len(cleaned_table) > 1 and len(cleaned_table[0]) > 0:
                    columns = [str(col) if col is not None else f'Column_{i}' for i, col in enumerate(cleaned_table[0])]
                    df = pd.DataFrame(cleaned_table[1:], columns=columns)
                else:
                    df = pd.DataFrame(cleaned_table[1:])
            except Exception:
                # Fallback if column names are problematic
                df = pd.DataFrame(cleaned_table[1:])
                df.columns = [f'Column_{i}' for i in range(len(df.columns))]
            
            # Clean column names
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # Remove empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty:
                return None
            
            # Detect if this is a financial table
            is_financial = self._is_financial_table(df)
            
            # Calculate importance score
            importance_score = self._calculate_importance_score(df, is_financial)
            
            table_info = {
                'table_id': table_id,
                'document': doc_name,
                'page_number': page_num,
                'dataframe': df,
                'is_financial': is_financial,
                'importance_score': importance_score,
                'rows': len(df),
                'columns': len(df.columns),
                'summary': self._generate_table_summary(df, is_financial)
            }
            
            return table_info
            
        except Exception as e:
            logger.error(f"Error processing table {table_id}: {str(e)}")
            return None
    
    def _clean_table_data(self, raw_table: List[List]) -> List[List]:
        """
        Clean raw table data
        """
        cleaned = []
        
        for row in raw_table:
            if row is None:
                continue
                
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append('')
                else:
                    # Clean cell content
                    cell_str = str(cell).strip()
                    # Remove extra whitespace
                    cell_str = re.sub(r'\s+', ' ', cell_str)
                    cleaned_row.append(cell_str)
            
            # Only add non-empty rows
            if any(cell.strip() for cell in cleaned_row):
                cleaned.append(cleaned_row)
        
        return cleaned
    
    def _clean_column_name(self, col_name: str) -> str:
        """
        Clean column names
        """
        if not col_name or not isinstance(col_name, str):
            return 'Column'
        
        # Remove special characters and extra spaces
        cleaned = re.sub(r'[^\w\s-]', '', str(col_name))
        cleaned = re.sub(r'\s+', '_', cleaned.strip())
        
        return cleaned if cleaned else 'Column'
    
    def _is_financial_table(self, df: pd.DataFrame) -> bool:
        """
        Determine if a table contains financial data
        """
        try:
            # Validate DataFrame is not empty
            if df.empty or len(df.columns) == 0:
                return False
            
            # Check column names and content for financial keywords
            text_to_check = ' '.join(df.columns.astype(str)).lower()
            
            # Add some cell content for checking
            sample_cells = []
            for col in df.columns[:3]:  # Check first 3 columns
                try:
                    # Safely get column data as Series
                    col_series = df[col]
                    if not col_series.empty:
                        sample_data = col_series.astype(str).head(5).values.tolist()
                        sample_cells.extend(sample_data)
                except Exception as e:
                    logger.warning(f"Error processing column {col}: {str(e)}")
                    continue
            
            text_to_check += ' ' + ' '.join(sample_cells).lower()
            
            # Check for financial keywords
            financial_score = sum(1 for keyword in self.financial_keywords if keyword in text_to_check)
            
            # Check for numeric data (financial tables usually have numbers)
            numeric_cols = 0
            for col in df.columns:
                try:
                    col_series = df[col]
                    if pd.api.types.is_numeric_dtype(col_series):
                        numeric_cols += 1
                except Exception as e:
                    logger.warning(f"Error checking dtype for column {col}: {str(e)}")
                    continue
            
            # Check for currency symbols or number patterns
            currency_pattern = r'[\$¥€£]\s*[\d,.]+'
            percentage_pattern = r'\d+\.?\d*\s*%'
            
            has_currency = any(re.search(currency_pattern, str(cell)) for cell in sample_cells)
            has_percentage = any(re.search(percentage_pattern, str(cell)) for cell in sample_cells)
            
            return (financial_score >= 2) or (numeric_cols >= 2) or has_currency or has_percentage
            
        except Exception as e:
            logger.error(f"Error checking if table is financial: {str(e)}")
            return False
    
    def _calculate_importance_score(self, df: pd.DataFrame, is_financial: bool) -> float:
        """
        Calculate importance score for a table
        """
        try:
            score = 0.0
            
            # Base score for financial tables
            if is_financial:
                score += 0.4
            
            # Size factor (larger tables might be more important)
            size_factor = min(len(df) * len(df.columns) / 100, 0.3)
            score += size_factor
            
            # Data density (non-empty cells)
            total_cells = len(df) * len(df.columns)
            non_empty_cells = df.count().sum()
            density = non_empty_cells / total_cells if total_cells > 0 else 0
            score += density * 0.2
            
            # Keyword relevance
            text_content = ' '.join(df.astype(str).values.flatten()).lower()
            keyword_matches = sum(1 for keyword in self.financial_keywords if keyword in text_content)
            score += min(keyword_matches * 0.02, 0.1)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {str(e)}")
            return 0.5
    
    def _generate_table_summary(self, df: pd.DataFrame, is_financial: bool) -> str:
        """
        Generate a summary description of the table
        """
        try:
            # Validate DataFrame is not empty
            if df.empty or len(df.columns) == 0:
                return "Empty table"
            
            summary_parts = []
            
            # Basic info
            summary_parts.append(f"{len(df)} rows × {len(df.columns)} columns")
            
            if is_financial:
                summary_parts.append("Financial data")
            
            # Column types - safely check numeric columns
            numeric_cols = 0
            for col in df.columns:
                try:
                    col_series = df[col]
                    if pd.api.types.is_numeric_dtype(col_series):
                        numeric_cols += 1
                except Exception as e:
                    logger.warning(f"Error checking column type for {col}: {str(e)}")
                    continue
            
            if numeric_cols > 0:
                summary_parts.append(f"{numeric_cols} numeric columns")
            
            return ", ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating table summary: {str(e)}")
            return "Table summary unavailable"
    
    def get_important_tables(self, all_tables: Dict[str, List[Dict]], min_importance: float = 0.5) -> List[Dict]:
        """
        Filter and return important tables based on importance score
        """
        important_tables = []
        
        for doc_name, tables in all_tables.items():
            for table in tables:
                if table['importance_score'] >= min_importance:
                    important_tables.append(table)
        
        # Sort by importance score
        important_tables.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return important_tables
    
    def create_consolidated_table(self, tables: List[Dict]) -> Optional[pd.DataFrame]:
        """
        Create a consolidated table from multiple extracted tables
        """
        try:
            if not tables:
                return None
            
            consolidated_data = []
            
            for table in tables:
                df = table['dataframe']
                
                # Add metadata columns
                df_copy = df.copy()
                df_copy['source_document'] = table['document']
                df_copy['source_page'] = table['page_number']
                df_copy['table_id'] = table['table_id']
                df_copy['importance_score'] = table['importance_score']
                
                consolidated_data.append(df_copy)
            
            # Concatenate all tables
            if consolidated_data:
                consolidated_df = pd.concat(consolidated_data, ignore_index=True, sort=False)
                return consolidated_df
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating consolidated table: {str(e)}")
            return None
