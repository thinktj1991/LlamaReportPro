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
        # Categorized financial keywords with weights
        self.financial_keywords = {
            'income_statement': {
                'keywords': [
                    'revenue', 'sales', 'income', 'profit', 'loss', 'earnings', 'ebitda', 'ebit',
                    'margin', 'expenses', 'cost of goods sold', 'cogs', 'operating income',
                    'net income', 'gross profit', 'operating expenses', 'interest expense',
                    'tax expense', 'depreciation', 'amortization', 'sga', 'r&d',
                    'selling general administrative'
                ],
                'weight': 1.0,
                'patterns': [r'\bq[1-4]\b', r'\b\d{4}\b', r'year ended', r'ytd', r'quarterly']
            },
            'balance_sheet': {
                'keywords': [
                    'assets', 'liabilities', 'equity', 'cash', 'debt', 'inventory',
                    'accounts receivable', 'accounts payable', 'current assets',
                    'current liabilities', 'long term debt', 'shareholders equity',
                    'retained earnings', 'property plant equipment', 'ppe',
                    'goodwill', 'intangible assets', 'working capital'
                ],
                'weight': 0.9,
                'patterns': [r'as of', r'balance sheet', r'statement of.*position']
            },
            'cash_flow': {
                'keywords': [
                    'cash flow', 'operating activities', 'investing activities',
                    'financing activities', 'free cash flow', 'fcf', 'capex',
                    'capital expenditures', 'dividends paid', 'share repurchases',
                    'proceeds from', 'payments for', 'cash and equivalents',
                    'net change in cash', 'beginning cash', 'ending cash'
                ],
                'weight': 0.8,
                'patterns': [r'cash flow', r'statement of.*cash', r'for.*year.*ended']
            },
            'ratios': {
                'keywords': [
                    'ratio', 'margin', 'return', 'roe', 'roa', 'debt to equity',
                    'current ratio', 'quick ratio', 'asset turnover', 'pe ratio',
                    'price to earnings', 'ev ebitda', 'gross margin', 'operating margin',
                    'net margin', 'debt ratio', 'leverage', 'coverage ratio',
                    'times interest earned', 'dso', 'days sales outstanding'
                ],
                'weight': 0.7,
                'patterns': [r'%', r'ratio', r'x', r'times']
            },
            'footnotes': {
                'keywords': [
                    'note', 'footnote', 'see note', 'refer to', 'basis of presentation',
                    'accounting policies', 'subsequent events', 'commitments',
                    'contingencies', 'fair value', 'segment', 'geographic'
                ],
                'weight': 0.3,
                'patterns': [r'note \d+', r'\(\d+\)', r'see.*note']
            }
        }
        
        # Currency and number patterns
        self.currency_patterns = [
            r'[\$¥€£]\s*[\d,.]+'  # Currency symbols
        ]
        self.percentage_patterns = [
            r'\d+\.?\d*\s*%',      # Percentage values
            r'\(\d+\.?\d*%\)'      # Parenthesized percentages
        ]
        self.large_number_patterns = [
            r'\b\d{1,3}(?:,\d{3})+\b',  # Comma-separated numbers
            r'\b\d+\.?\d*[kmb]\b'        # Numbers with k/m/b suffixes
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
                    df = pd.DataFrame(data=cleaned_table[1:])
                    df.columns = columns
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
            
            # Perform comprehensive table analysis and categorization
            categorization = self._categorize_table(df)
            
            # Calculate enhanced importance score using categorization
            importance_score = self._calculate_importance_score(df, categorization)
            
            # Detect if this is a financial table (backwards compatibility)
            is_financial = self._is_financial_table(df)
            
            # Generate enhanced summary
            enhanced_summary = self._generate_enhanced_table_summary(df, categorization)
            
            table_info = {
                'table_id': table_id,
                'document': doc_name,
                'page_number': page_num,
                'dataframe': df,
                'is_financial': is_financial,  # Keep for backwards compatibility
                'importance_score': importance_score,
                'rows': len(df),
                'columns': len(df.columns),
                'summary': enhanced_summary,
                # New enhanced fields
                'category': categorization.get('category', 'other'),
                'category_confidence': categorization.get('confidence', 0.0),
                'category_scores': categorization.get('category_scores', {}),
                'analysis_details': {
                    'header_analysis': categorization.get('analysis_summary', {}).get('header_analysis', {}),
                    'numeric_analysis': categorization.get('analysis_summary', {}).get('numeric_analysis', {}),
                    'shape_analysis': categorization.get('analysis_summary', {}).get('shape_analysis', {})
                }
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
    
    def _analyze_headers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze table headers for semantic meaning and financial keywords
        Returns analysis with scores for each financial statement category
        """
        try:
            analysis = {
                'category_scores': {},
                'total_score': 0.0,
                'dominant_category': 'other',
                'confidence': 0.0,
                'financial_keywords_found': [],
                'header_quality': 0.0
            }
            
            if df.empty or len(df.columns) == 0:
                return analysis
            
            # Combine header text with first few rows for context
            header_text = ' '.join(df.columns.astype(str)).lower()
            
            # Add sample data from first 3 rows for better context
            sample_data = []
            try:
                for i in range(min(3, len(df))):
                    row_data = df.iloc[i].astype(str).tolist()
                    sample_data.extend(row_data)
                header_text += ' ' + ' '.join(sample_data).lower()
            except Exception as e:
                logger.warning(f"Error adding sample data to header analysis: {str(e)}")
            
            # Score each financial statement category
            for category, category_data in self.financial_keywords.items():
                category_score = 0.0
                matched_keywords = []
                
                # Check keywords
                for keyword in category_data['keywords']:
                    if keyword.lower() in header_text:
                        category_score += category_data['weight']
                        matched_keywords.append(keyword)
                
                # Check patterns
                for pattern in category_data['patterns']:
                    if re.search(pattern, header_text, re.IGNORECASE):
                        category_score += category_data['weight'] * 0.5
                
                # Normalize score based on number of possible matches
                if category_data['keywords']:
                    category_score = category_score / len(category_data['keywords'])
                
                analysis['category_scores'][category] = category_score
                if matched_keywords:
                    analysis['financial_keywords_found'].extend(matched_keywords)
            
            # Determine dominant category
            if analysis['category_scores']:
                dominant_cat = max(analysis['category_scores'], key=analysis['category_scores'].get)
                dominant_score = analysis['category_scores'][dominant_cat]
                
                if dominant_score > 0.1:  # Minimum threshold for categorization
                    analysis['dominant_category'] = dominant_cat
                    analysis['confidence'] = min(dominant_score * 2, 1.0)  # Scale confidence
                
                analysis['total_score'] = sum(analysis['category_scores'].values())
            
            # Calculate header quality score
            analysis['header_quality'] = self._calculate_header_quality(df)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing headers: {str(e)}")
            return {
                'category_scores': {},
                'total_score': 0.0,
                'dominant_category': 'other',
                'confidence': 0.0,
                'financial_keywords_found': [],
                'header_quality': 0.0
            }
    
    def _calculate_header_quality(self, df: pd.DataFrame) -> float:
        """
        Calculate quality score for table headers
        """
        try:
            if df.empty or len(df.columns) == 0:
                return 0.0
            
            quality_score = 0.0
            
            # Check for meaningful header names (not Column_0, Column_1, etc.)
            meaningful_headers = sum(1 for col in df.columns if not col.startswith('Column'))
            quality_score += (meaningful_headers / len(df.columns)) * 0.4
            
            # Check header length (not too short or too long)
            avg_header_length = sum(len(str(col)) for col in df.columns) / len(df.columns)
            if 3 <= avg_header_length <= 30:  # Reasonable header length
                quality_score += 0.3
            
            # Check for duplicate headers
            unique_headers = len(set(df.columns))
            uniqueness_ratio = unique_headers / len(df.columns)
            quality_score += uniqueness_ratio * 0.3
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating header quality: {str(e)}")
            return 0.5
    
    def _calculate_numeric_density(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate numeric density and analyze financial number patterns
        """
        try:
            analysis = {
                'numeric_density': 0.0,
                'financial_patterns': {
                    'currency_count': 0,
                    'percentage_count': 0,
                    'large_numbers_count': 0,
                    'negative_numbers_count': 0
                },
                'data_quality': 0.0,
                'financial_score': 0.0,
                'column_types': {}
            }
            
            if df.empty:
                return analysis
            
            total_cells = len(df) * len(df.columns)
            numeric_cells = 0
            text_cells = 0
            currency_count = 0
            percentage_count = 0
            large_numbers_count = 0
            negative_numbers_count = 0
            
            # Analyze each column
            for col in df.columns:
                try:
                    col_series = df[col].astype(str)
                    col_analysis = {
                        'type': 'text',
                        'numeric_ratio': 0.0,
                        'financial_patterns': 0
                    }
                    
                    col_numeric_count = 0
                    col_pattern_count = 0
                    
                    for cell_value in col_series:
                        if pd.isna(cell_value) or cell_value.strip() == '' or str(cell_value).lower() in ['nan', 'none']:
                            continue
                            
                        cell_str = str(cell_value).strip()
                        
                        # Check if cell contains numeric data
                        try:
                            # Try to extract numbers from the cell
                            numbers_in_cell = re.findall(r'-?\d+\.?\d*', cell_str)
                            if numbers_in_cell:
                                numeric_cells += 1
                                col_numeric_count += 1
                                
                                # Check for negative numbers (common in financial data)
                                if any(float(num) < 0 for num in numbers_in_cell if num):
                                    negative_numbers_count += 1
                            else:
                                text_cells += 1
                        except:
                            text_cells += 1
                        
                        # Check for financial patterns
                        for pattern in self.currency_patterns:
                            if re.search(pattern, cell_str):
                                currency_count += 1
                                col_pattern_count += 1
                                break
                        
                        for pattern in self.percentage_patterns:
                            if re.search(pattern, cell_str):
                                percentage_count += 1
                                col_pattern_count += 1
                                break
                        
                        for pattern in self.large_number_patterns:
                            if re.search(pattern, cell_str):
                                large_numbers_count += 1
                                col_pattern_count += 1
                                break
                    
                    # Determine column type and metrics
                    non_empty_cells = len(col_series) - col_series.isin(['', 'nan', 'none']).sum()
                    if non_empty_cells > 0:
                        col_analysis['numeric_ratio'] = col_numeric_count / non_empty_cells
                        col_analysis['financial_patterns'] = col_pattern_count
                        
                        if col_analysis['numeric_ratio'] > 0.7:
                            col_analysis['type'] = 'numeric'
                        elif col_analysis['numeric_ratio'] > 0.3:
                            col_analysis['type'] = 'mixed'
                    
                    analysis['column_types'][col] = col_analysis
                    
                except Exception as e:
                    logger.warning(f"Error analyzing column {col}: {str(e)}")
                    continue
            
            # Calculate overall metrics
            if total_cells > 0:
                analysis['numeric_density'] = numeric_cells / total_cells
            
            analysis['financial_patterns'] = {
                'currency_count': currency_count,
                'percentage_count': percentage_count,
                'large_numbers_count': large_numbers_count,
                'negative_numbers_count': negative_numbers_count
            }
            
            # Calculate data quality score
            analysis['data_quality'] = self._calculate_data_quality(df, analysis)
            
            # Calculate financial score based on patterns
            pattern_score = 0.0
            if currency_count > 0:
                pattern_score += 0.3
            if percentage_count > 0:
                pattern_score += 0.2
            if large_numbers_count > 0:
                pattern_score += 0.2
            if negative_numbers_count > 0:  # Financial data often has negative numbers
                pattern_score += 0.1
            if analysis['numeric_density'] > 0.5:
                pattern_score += 0.2
            
            analysis['financial_score'] = min(pattern_score, 1.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating numeric density: {str(e)}")
            return {
                'numeric_density': 0.0,
                'financial_patterns': {'currency_count': 0, 'percentage_count': 0, 'large_numbers_count': 0, 'negative_numbers_count': 0},
                'data_quality': 0.0,
                'financial_score': 0.0,
                'column_types': {}
            }
    
    def _calculate_data_quality(self, df: pd.DataFrame, numeric_analysis: Dict) -> float:
        """
        Calculate data quality score based on consistency and completeness
        """
        try:
            quality_score = 0.0
            
            # Check data completeness
            total_cells = len(df) * len(df.columns)
            empty_cells = df.isnull().sum().sum()
            completeness = (total_cells - empty_cells) / total_cells if total_cells > 0 else 0
            quality_score += completeness * 0.4
            
            # Check numeric consistency
            numeric_cols = sum(1 for col_data in numeric_analysis['column_types'].values() 
                             if col_data['type'] == 'numeric')
            if len(df.columns) > 0:
                numeric_consistency = numeric_cols / len(df.columns)
                quality_score += numeric_consistency * 0.3
            
            # Check for reasonable data distribution
            if not df.empty:
                # Check if data has reasonable variance (not all identical)
                variance_score = 0.0
                for col in df.columns:
                    try:
                        col_series = df[col].astype(str)
                        unique_values = len(col_series.unique())
                        if len(col_series) > 0:
                            uniqueness = unique_values / len(col_series)
                            variance_score += min(uniqueness * 2, 1.0)  # Scale appropriately
                    except:
                        continue
                
                if len(df.columns) > 0:
                    variance_score = variance_score / len(df.columns)
                    quality_score += variance_score * 0.3
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {str(e)}")
            return 0.5
    
    def _analyze_shape(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze table dimensions and structure for financial table characteristics
        """
        try:
            analysis = {
                'rows': len(df),
                'columns': len(df.columns),
                'aspect_ratio': 0.0,
                'density_score': 0.0,
                'structure_score': 0.0,
                'optimal_financial_shape': False,
                'table_type_hint': 'other'
            }
            
            if df.empty:
                return analysis
            
            rows, cols = len(df), len(df.columns)
            analysis['rows'] = rows
            analysis['columns'] = cols
            
            # Calculate aspect ratio (rows to columns)
            if cols > 0:
                analysis['aspect_ratio'] = rows / cols
            
            # Analyze structure characteristics for financial tables
            structure_score = 0.0
            
            # Income Statement characteristics: Usually many rows, moderate columns (3-7)
            if 10 <= rows <= 50 and 3 <= cols <= 7:
                structure_score += 0.3
                analysis['table_type_hint'] = 'income_statement'
            
            # Balance Sheet characteristics: Moderate rows, fewer columns (2-5)
            elif 8 <= rows <= 30 and 2 <= cols <= 5:
                structure_score += 0.25
                analysis['table_type_hint'] = 'balance_sheet'
            
            # Cash Flow characteristics: Many rows, moderate columns (3-6)
            elif 15 <= rows <= 40 and 3 <= cols <= 6:
                structure_score += 0.2
                analysis['table_type_hint'] = 'cash_flow'
            
            # Ratio/metrics table: Fewer rows, fewer columns
            elif 3 <= rows <= 15 and 2 <= cols <= 4:
                structure_score += 0.15
                analysis['table_type_hint'] = 'ratios'
            
            # Footnote table: Variable, but usually smaller
            elif rows <= 10 and cols <= 3:
                structure_score += 0.1
                analysis['table_type_hint'] = 'footnotes'
            
            # Bonus for optimal financial table dimensions
            if (5 <= rows <= 100) and (2 <= cols <= 10):
                structure_score += 0.2
                analysis['optimal_financial_shape'] = True
            
            # Penalty for tables that are too wide or too narrow
            if cols > 15:  # Too many columns
                structure_score -= 0.2
            elif cols < 2:  # Too few columns
                structure_score -= 0.3
            
            if rows > 200:  # Extremely long tables
                structure_score -= 0.1
            elif rows < 2:  # Too short
                structure_score -= 0.3
            
            analysis['structure_score'] = max(0.0, min(structure_score, 1.0))
            
            # Calculate density score (measure of information density)
            total_cells = rows * cols
            if total_cells > 0:
                # Ideal density range for financial tables
                if 20 <= total_cells <= 500:
                    density_score = 1.0
                elif 10 <= total_cells <= 1000:
                    density_score = 0.8
                elif total_cells <= 2000:
                    density_score = 0.6
                else:
                    density_score = 0.4
                
                # Adjust based on aspect ratio
                if 0.5 <= analysis['aspect_ratio'] <= 10:  # Reasonable aspect ratio
                    density_score += 0.1
                
                analysis['density_score'] = min(density_score, 1.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing table shape: {str(e)}")
            return {
                'rows': 0,
                'columns': 0,
                'aspect_ratio': 0.0,
                'density_score': 0.0,
                'structure_score': 0.0,
                'optimal_financial_shape': False,
                'table_type_hint': 'other'
            }
    
    def _categorize_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Automatically categorize table with confidence scoring using all analysis methods
        """
        try:
            categorization = {
                'category': 'other',
                'confidence': 0.0,
                'category_scores': {},
                'analysis_summary': {}
            }
            
            if df.empty:
                return categorization
            
            # Get all analysis components
            header_analysis = self._analyze_headers(df)
            numeric_analysis = self._calculate_numeric_density(df)
            shape_analysis = self._analyze_shape(df)
            
            # Store analysis summary for debugging/transparency
            categorization['analysis_summary'] = {
                'header_analysis': header_analysis,
                'numeric_analysis': numeric_analysis,
                'shape_analysis': shape_analysis
            }
            
            # Calculate scores for each category
            category_scores = {}
            
            for category in ['income_statement', 'balance_sheet', 'cash_flow', 'ratios', 'footnotes']:
                score = 0.0
                
                # Header analysis contribution (40% weight)
                header_score = header_analysis['category_scores'].get(category, 0.0)
                score += header_score * 0.4
                
                # Shape analysis contribution (30% weight)
                if shape_analysis['table_type_hint'] == category:
                    score += shape_analysis['structure_score'] * 0.3
                elif shape_analysis['optimal_financial_shape'] and category != 'footnotes':
                    score += 0.1  # Bonus for financial-shaped tables
                
                # Numeric analysis contribution (20% weight)
                if category != 'footnotes':  # Financial tables should have good numeric density
                    if numeric_analysis['numeric_density'] > 0.5:
                        score += numeric_analysis['financial_score'] * 0.2
                else:  # Footnotes may have less numeric data
                    if numeric_analysis['numeric_density'] < 0.3:
                        score += 0.1
                
                # Data quality contribution (10% weight)
                quality_score = numeric_analysis['data_quality']
                if quality_score > 0.7:
                    score += quality_score * 0.1
                
                category_scores[category] = score
            
            # Add 'other' category score
            category_scores['other'] = 0.2  # Base score for unrecognized tables
            
            # Determine best category and confidence
            if category_scores:
                best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
                best_score = category_scores[best_category]
                
                # Calculate confidence based on score separation
                sorted_scores = sorted(category_scores.values(), reverse=True)
                if len(sorted_scores) > 1:
                    score_gap = sorted_scores[0] - sorted_scores[1]
                    confidence = min(best_score + score_gap, 1.0)
                else:
                    confidence = best_score
                
                # Apply minimum thresholds
                if best_score < 0.2:  # Very low score
                    best_category = 'other'
                    confidence = 0.3
                elif best_category == 'other' and best_score > 0.4:
                    # If 'other' wins but with high score, reduce confidence
                    confidence = min(confidence, 0.6)
                
                categorization['category'] = best_category
                categorization['confidence'] = max(0.0, min(confidence, 1.0))
                categorization['category_scores'] = category_scores
            
            return categorization
            
        except Exception as e:
            logger.error(f"Error categorizing table: {str(e)}")
            return {
                'category': 'other',
                'confidence': 0.0,
                'category_scores': {'other': 0.2},
                'analysis_summary': {}
            }
    
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
    
    def _calculate_importance_score(self, df: pd.DataFrame, categorization: Dict[str, Any]) -> float:
        """
        Calculate enhanced importance score using comprehensive table analysis
        """
        try:
            if df.empty:
                return 0.0
            
            # Extract analysis components from categorization
            analysis_summary = categorization.get('analysis_summary', {})
            header_analysis = analysis_summary.get('header_analysis', {})
            numeric_analysis = analysis_summary.get('numeric_analysis', {})
            shape_analysis = analysis_summary.get('shape_analysis', {})
            
            # Initialize score components
            score_components = {
                'header_score': 0.0,
                'numeric_score': 0.0,
                'shape_score': 0.0,
                'category_score': 0.0,
                'quality_score': 0.0
            }
            
            # 1. Header Analysis Score (30% weight)
            if header_analysis:
                # Total keyword relevance score
                header_total_score = header_analysis.get('total_score', 0.0)
                header_quality = header_analysis.get('header_quality', 0.0)
                
                score_components['header_score'] = (header_total_score * 0.7 + header_quality * 0.3) * 0.3
            
            # 2. Numeric Analysis Score (25% weight)
            if numeric_analysis:
                numeric_density = numeric_analysis.get('numeric_density', 0.0)
                financial_score = numeric_analysis.get('financial_score', 0.0)
                data_quality = numeric_analysis.get('data_quality', 0.0)
                
                # Combine numeric factors
                numeric_combined = (numeric_density * 0.4 + financial_score * 0.4 + data_quality * 0.2)
                score_components['numeric_score'] = numeric_combined * 0.25
            
            # 3. Shape Analysis Score (20% weight)
            if shape_analysis:
                structure_score = shape_analysis.get('structure_score', 0.0)
                density_score = shape_analysis.get('density_score', 0.0)
                optimal_shape = shape_analysis.get('optimal_financial_shape', False)
                
                shape_combined = (structure_score * 0.6 + density_score * 0.4)
                if optimal_shape:
                    shape_combined += 0.1  # Bonus for optimal shape
                
                score_components['shape_score'] = min(shape_combined, 1.0) * 0.20
            
            # 4. Category Confidence Score (15% weight)
            category_confidence = categorization.get('confidence', 0.0)
            category = categorization.get('category', 'other')
            
            # Higher weight for important financial statement categories
            category_weights = {
                'income_statement': 1.0,
                'balance_sheet': 0.9,
                'cash_flow': 0.8,
                'ratios': 0.7,
                'footnotes': 0.4,
                'other': 0.3
            }
            
            category_weight = category_weights.get(category, 0.3)
            score_components['category_score'] = category_confidence * category_weight * 0.15
            
            # 5. Overall Quality Score (10% weight)
            if numeric_analysis:
                overall_quality = numeric_analysis.get('data_quality', 0.5)
                score_components['quality_score'] = overall_quality * 0.10
            
            # Calculate final score
            final_score = sum(score_components.values())
            
            # Apply bonuses and penalties
            
            # Bonus for high-confidence, high-importance categories
            if category in ['income_statement', 'balance_sheet', 'cash_flow'] and category_confidence > 0.8:
                final_score += 0.05
            
            # Penalty for very small tables (likely not main financial statements)
            if len(df) < 3 or len(df.columns) < 2:
                final_score *= 0.8
            
            # Penalty for very large tables (might be detailed breakdowns)
            if len(df) > 100 or len(df.columns) > 12:
                final_score *= 0.9
            
            # Ensure score is within bounds
            final_score = max(0.0, min(final_score, 1.0))
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating enhanced importance score: {str(e)}")
            # Fallback to basic scoring
            try:
                basic_score = 0.5
                if not df.empty:
                    # Simple fallback based on table size and density
                    size_factor = min(len(df) * len(df.columns) / 100, 0.3)
                    density = (df.count().sum() / (len(df) * len(df.columns))) if len(df) > 0 and len(df.columns) > 0 else 0
                    basic_score = min(0.3 + size_factor + density * 0.2, 1.0)
                return basic_score
            except:
                return 0.3
    
    def _generate_enhanced_table_summary(self, df: pd.DataFrame, categorization: Dict[str, Any]) -> str:
        """
        Generate enhanced summary using comprehensive table analysis
        """
        try:
            if df.empty or len(df.columns) == 0:
                return "Empty table"
            
            summary_parts = []
            
            # Basic dimensions
            summary_parts.append(f"{len(df)} rows × {len(df.columns)} columns")
            
            # Category information
            category = categorization.get('category', 'other')
            confidence = categorization.get('confidence', 0.0)
            
            if category != 'other' and confidence > 0.3:
                category_name = category.replace('_', ' ').title()
                confidence_level = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
                summary_parts.append(f"{category_name} ({confidence_level} confidence)")
            elif category == 'other':
                summary_parts.append("General table")
            
            # Analysis insights
            analysis_summary = categorization.get('analysis_summary', {})
            
            # Numeric analysis insights
            numeric_analysis = analysis_summary.get('numeric_analysis', {})
            if numeric_analysis:
                numeric_density = numeric_analysis.get('numeric_density', 0.0)
                financial_patterns = numeric_analysis.get('financial_patterns', {})
                
                if numeric_density > 0.7:
                    summary_parts.append("Mostly numeric data")
                elif numeric_density > 0.3:
                    summary_parts.append("Mixed numeric/text data")
                
                # Highlight financial patterns
                pattern_notes = []
                if financial_patterns.get('currency_count', 0) > 0:
                    pattern_notes.append("currency values")
                if financial_patterns.get('percentage_count', 0) > 0:
                    pattern_notes.append("percentages")
                if financial_patterns.get('large_numbers_count', 0) > 0:
                    pattern_notes.append("large numbers")
                
                if pattern_notes:
                    summary_parts.append(f"Contains {', '.join(pattern_notes)}")
            
            # Shape analysis insights
            shape_analysis = analysis_summary.get('shape_analysis', {})
            if shape_analysis:
                if shape_analysis.get('optimal_financial_shape', False):
                    summary_parts.append("Optimal financial table dimensions")
                
                structure_score = shape_analysis.get('structure_score', 0.0)
                if structure_score > 0.7:
                    summary_parts.append("Well-structured")
            
            # Header quality
            header_analysis = analysis_summary.get('header_analysis', {})
            if header_analysis:
                header_quality = header_analysis.get('header_quality', 0.0)
                if header_quality > 0.8:
                    summary_parts.append("High-quality headers")
                elif header_quality < 0.4:
                    summary_parts.append("Generic headers")
            
            return ", ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary: {str(e)}")
            # Fallback to basic summary
            return self._generate_table_summary(df, categorization.get('category') != 'other')
    
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
