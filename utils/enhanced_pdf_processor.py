"""
Enhanced PDF Processor using LlamaParse for superior table and chart extraction
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st
from llama_index.core import Document
from llama_index.readers.llama_parse import LlamaParse
from llama_index.readers.file import PDFReader
import pandas as pd
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    """
    Enhanced PDF processor using LlamaParse for superior extraction capabilities
    """
    
    def __init__(self, use_premium_parse: bool = True):
        """
        Initialize the enhanced PDF processor
        
        Args:
            use_premium_parse: Whether to use LlamaParse premium features
        """
        self.use_premium_parse = use_premium_parse
        self.llama_parser = None
        self.fallback_reader = PDFReader()
        self._initialize_parser()
    
    def _initialize_parser(self):
        """Initialize LlamaParse with premium features"""
        try:
            # Get API key from environment
            api_key = os.getenv('LLAMA_CLOUD_API_KEY')
            if not api_key:
                logger.warning("LLAMA_CLOUD_API_KEY not found, falling back to basic PDFReader")
                self.use_premium_parse = False
                return
            
            # Initialize LlamaParse with enhanced features
            self.llama_parser = LlamaParse(
                api_key=api_key,
                result_type="markdown",  # Use markdown for better structure
                num_workers=4,  # Parallel processing
                verbose=True,
                language="ch_sim",  # Chinese simplified support (fixed from "zh")
                # Premium features - using system_prompt instead of deprecated parsing_instruction
                system_prompt="""
                This document contains financial annual reports with complex tables, charts, and financial data.
                Please extract:
                1. All table content with precise structure preservation
                2. Financial metrics and numerical data
                3. Chart descriptions and data points
                4. Company information and metadata
                5. Maintain Chinese text encoding properly
                """
            )
            
            logger.info("LlamaParse initialized successfully with premium features")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaParse: {str(e)}")
            self.use_premium_parse = False
            logger.info("Falling back to basic PDFReader")
    
    async def process_uploaded_file_async(self, uploaded_file) -> Dict[str, Any]:
        """
        Asynchronously process an uploaded PDF file with enhanced extraction
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            result = await self._extract_content_with_llamaparse(tmp_path, uploaded_file.name)

            # Clean up temporary file
            os.unlink(tmp_path)

            method = result.get('extraction_method', '') if isinstance(result, dict) else ''
            if isinstance(method, str) and method.startswith('llamaparse'):
                logger.info(f"Successfully processed {uploaded_file.name} with enhanced extraction")
            else:
                logger.info(f"Processed {uploaded_file.name} via fallback (basic PDFReader)")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {uploaded_file.name}: {str(e)}")
            # Fallback to synchronous processing
            return self._fallback_processing(uploaded_file)
    
    def process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Synchronous wrapper for PDF processing
        """
        try:
            # Use asyncio.run to avoid event loop issues
            if not self.use_premium_parse or not self.llama_parser:
                logger.info("Using fallback processing")
                return self._fallback_processing(uploaded_file)
            
            # Try async processing with proper event loop handling
            try:
                import asyncio
                import nest_asyncio

                # Apply nest_asyncio to allow nested event loops
                nest_asyncio.apply()

                # Check if we're in an existing event loop
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        # We're in a running loop, create a task instead of using asyncio.run
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.process_uploaded_file_async(uploaded_file))
                            result = future.result()
                            return result
                    else:
                        # Loop exists but not running, safe to use asyncio.run
                        result = asyncio.run(self.process_uploaded_file_async(uploaded_file))
                        return result
                except RuntimeError:
                    # No running loop, safe to use asyncio.run
                    result = asyncio.run(self.process_uploaded_file_async(uploaded_file))
                    return result

            except Exception as e:
                if "Event loop is closed" in str(e) or "cannot be called from a running event loop" in str(e):
                    logger.warning(f"Async processing failed ({str(e)}), using fallback")
                    return self._fallback_processing(uploaded_file)
                else:
                    raise
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return self._fallback_processing(uploaded_file)
    
    async def _extract_content_with_llamaparse(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Extract content using LlamaParse with enhanced capabilities
        """
        if not self.llama_parser:
            return self._fallback_processing_from_path(pdf_path, filename)
        
        try:
            # Load documents using LlamaParse
            documents = await self.llama_parser.aload_data(pdf_path)
            
            # Enhanced content extraction
            enhanced_content = await self._extract_enhanced_content(documents, pdf_path)
            
            # Extract metadata and statistics
            metadata = self._extract_enhanced_metadata(documents)
            
            result = {
                'filename': filename,
                'documents': documents,
                'enhanced_content': enhanced_content,
                'metadata': metadata,
                'page_count': len(documents),
                'total_text_length': sum(len(doc.text) for doc in documents),
                'extraction_method': 'llamaparse_premium' if self.use_premium_parse else 'llamaparse_basic',
                'tables_extracted': enhanced_content.get('total_tables', 0),
                'charts_detected': enhanced_content.get('total_charts', 0)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LlamaParse extraction failed: {str(e)}")
            # If credits exhausted / 402, disable premium parse for this session to avoid repeated failures
            err_s = str(e)
            if "402" in err_s or "Payment Required" in err_s or "credits" in err_s:
                logger.warning("Disabling premium LlamaParse due to 402 / credits exhaustion")
                self.use_premium_parse = False
                self.llama_parser = None
            return self._fallback_processing_from_path(pdf_path, filename)
    
    async def _extract_enhanced_content(self, documents: List[Document], pdf_path: str) -> Dict[str, Any]:
        """
        Extract enhanced content with table and chart analysis
        """
        enhanced_content = {
            'pages': [],
            'tables': [],
            'charts': [],
            'financial_sections': [],
            'total_tables': 0,
            'total_charts': 0,
            'quality_score': 0.0
        }
        
        try:
            for i, doc in enumerate(documents):
                page_analysis = await self._analyze_page_content(doc, i + 1)
                enhanced_content['pages'].append(page_analysis)
                
                # Aggregate statistics
                enhanced_content['total_tables'] += page_analysis.get('tables_count', 0)
                enhanced_content['total_charts'] += page_analysis.get('charts_count', 0)
                
                # Extract tables and charts
                if page_analysis.get('tables'):
                    enhanced_content['tables'].extend(page_analysis['tables'])
                if page_analysis.get('charts'):
                    enhanced_content['charts'].extend(page_analysis['charts'])
                if page_analysis.get('financial_data'):
                    enhanced_content['financial_sections'].append(page_analysis['financial_data'])
            
            # Calculate overall quality score
            enhanced_content['quality_score'] = self._calculate_extraction_quality(enhanced_content)
            
        except Exception as e:
            logger.error(f"Error in enhanced content extraction: {str(e)}")
        
        return enhanced_content
    
    async def _analyze_page_content(self, document: Document, page_num: int) -> Dict[str, Any]:
        """
        Analyze individual page content for tables, charts, and financial data
        """
        page_analysis = {
            'page_number': page_num,
            'text_length': len(document.text),
            'tables': [],
            'charts': [],
            'financial_data': {},
            'tables_count': 0,
            'charts_count': 0,
            'content_type': 'text'
        }
        
        try:
            text = document.text
            text_lower = text.lower()
            
            # Detect tables using LlamaParse enhanced parsing
            tables = await self._detect_and_extract_tables(text, page_num)
            if tables:
                page_analysis['tables'] = tables
                page_analysis['tables_count'] = len(tables)
                page_analysis['content_type'] = 'table_rich'
            
            # Detect charts and visualizations
            charts = self._detect_charts_and_visualizations(text, page_num)
            if charts:
                page_analysis['charts'] = charts
                page_analysis['charts_count'] = len(charts)
            
            # Extract financial data patterns
            financial_data = self._extract_financial_patterns(text, page_num)
            if financial_data:
                page_analysis['financial_data'] = financial_data
                page_analysis['content_type'] = 'financial_data'
            
            # Add metadata from document
            if hasattr(document, 'metadata') and document.metadata:
                page_analysis['metadata'] = document.metadata
                
        except Exception as e:
            logger.error(f"Error analyzing page {page_num}: {str(e)}")
        
        return page_analysis
    
    async def _detect_and_extract_tables(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Detect and extract tables using LlamaParse's enhanced table understanding
        """
        tables = []
        
        try:
            # LlamaParse automatically structures tabular data
            # Look for structured patterns in the text
            lines = text.split('\n')
            current_table = []
            in_table = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    if in_table and current_table:
                        # End of table
                        table_data = self._process_table_lines(current_table, page_num, len(tables) + 1)
                        if table_data:
                            tables.append(table_data)
                        current_table = []
                        in_table = False
                    continue
                
                # Detect table patterns (LlamaParse usually formats tables clearly)
                if self._is_table_line(line):
                    in_table = True
                    current_table.append(line)
                elif in_table:
                    current_table.append(line)
            
            # Process final table if exists
            if in_table and current_table:
                table_data = self._process_table_lines(current_table, page_num, len(tables) + 1)
                if table_data:
                    tables.append(table_data)
            
        except Exception as e:
            logger.error(f"Error detecting tables on page {page_num}: {str(e)}")
        
        return tables
    
    def _is_table_line(self, line: str) -> bool:
        """
        Detect if a line is part of a table structure
        """
        # Enhanced table detection patterns
        table_indicators = [
            '|',  # Markdown table separator
            '─', '┌', '└', '┐', '┘', '├', '┤', '┬', '┴', '┼',  # Box drawing characters
            '\t',  # Tab separated values
        ]
        
        # Check for multiple numbers or currency patterns
        import re
        number_pattern = r'[\d,]+\.?\d*'
        currency_pattern = r'[¥$€£]\s*[\d,]+\.?\d*'
        percentage_pattern = r'\d+\.?\d*\s*%'
        
        numbers_found = len(re.findall(number_pattern, line))
        currency_found = len(re.findall(currency_pattern, line))
        percentage_found = len(re.findall(percentage_pattern, line))
        
        # Table line criteria
        has_separators = any(indicator in line for indicator in table_indicators)
        has_multiple_numbers = numbers_found >= 2
        has_financial_data = currency_found > 0 or percentage_found > 0
        
        return has_separators or has_multiple_numbers or has_financial_data
    
    def _process_table_lines(self, lines: List[str], page_num: int, table_num: int) -> Optional[Dict[str, Any]]:
        """
        Process extracted table lines into structured data
        """
        if not lines or len(lines) < 2:
            return None
        
        try:
            
            # Convert lines to structured data
            table_data = []
            for line in lines:
                # Split by common separators
                if '|' in line:
                    row = [cell.strip() for cell in line.split('|') if cell.strip()]
                elif '\t' in line:
                    row = [cell.strip() for cell in line.split('\t')]
                else:
                    # Split by multiple spaces
                    import re
                    row = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
                
                if row and len(row) > 1:
                    table_data.append(row)
            
            if len(table_data) < 2:
                return None
            
            # Create DataFrame
            max_cols = max(len(row) for row in table_data)
            normalized_data = []
            for row in table_data:
                while len(row) < max_cols:
                    row.append('')
                normalized_data.append(row[:max_cols])
            
            # Use first row as headers if it looks like headers
            headers = normalized_data[0]
            data_rows = normalized_data[1:]
            
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Analyze table content
            analysis = self._analyze_table_content(df)
            
            return {
                'table_id': f'llamaparse_page_{page_num}_table_{table_num}',
                'page_number': page_num,
                'dataframe': df,
                'rows': len(df),
                'columns': len(df.columns),
                'is_financial': analysis['is_financial'],
                'confidence_score': analysis['confidence_score'],
                'table_type': analysis['table_type'],
                'summary': analysis['summary'],
                'extraction_method': 'llamaparse'
            }
            
        except Exception as e:
            logger.error(f"Error processing table lines: {str(e)}")
            return None
    
    def _analyze_table_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze table content to determine type and characteristics
        """
        analysis = {
            'is_financial': False,
            'confidence_score': 0.0,
            'table_type': 'general',
            'summary': 'General data table'
        }
        
        try:
            # Check column headers for financial indicators
            headers_text = ' '.join(df.columns.astype(str)).lower()
            
            # Financial keywords
            financial_keywords = [
                '收入', '营业收入', '利润', '资产', '负债', '现金流', '销售额',
                'revenue', 'income', 'profit', 'assets', 'liabilities', 'cash flow',
                '年', '季度', 'year', 'quarter', '金额', 'amount'
            ]
            
            keyword_matches = sum(1 for keyword in financial_keywords if keyword in headers_text)
            
            # Check for numeric data
            numeric_cols = df.select_dtypes(include=['number']).shape[1]
            total_cols = df.shape[1]
            numeric_ratio = numeric_cols / total_cols if total_cols > 0 else 0
            
            # Calculate confidence score
            keyword_score = min(keyword_matches / 5, 1.0) * 0.6
            numeric_score = numeric_ratio * 0.4
            analysis['confidence_score'] = keyword_score + numeric_score
            
            # Determine if financial
            analysis['is_financial'] = analysis['confidence_score'] > 0.5
            
            # Determine table type
            if '损益表' in headers_text or 'income' in headers_text:
                analysis['table_type'] = 'income_statement'
                analysis['summary'] = '利润表/损益表'
            elif '资产负债表' in headers_text or 'balance' in headers_text:
                analysis['table_type'] = 'balance_sheet'
                analysis['summary'] = '资产负债表'
            elif '现金流' in headers_text or 'cash flow' in headers_text:
                analysis['table_type'] = 'cash_flow'
                analysis['summary'] = '现金流量表'
            elif analysis['is_financial']:
                analysis['table_type'] = 'financial_data'
                analysis['summary'] = '财务数据表'
            
        except Exception as e:
            logger.error(f"Error analyzing table content: {str(e)}")
        
        return analysis
    
    def _detect_charts_and_visualizations(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Detect mentions of charts, graphs, and visualizations in the text
        """
        charts = []
        
        try:
            chart_keywords = [
                '图表', '柱状图', '折线图', '饼图', '散点图',
                'chart', 'graph', 'figure', 'diagram',
                '趋势图', '对比图', '分析图'
            ]
            
            text_lower = text.lower()
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in chart_keywords):
                    chart_info = {
                        'page_number': page_num,
                        'line_number': i + 1,
                        'description': line.strip(),
                        'chart_type': self._classify_chart_type(line_lower),
                        'context': self._get_chart_context(lines, i)
                    }
                    charts.append(chart_info)
        
        except Exception as e:
            logger.error(f"Error detecting charts on page {page_num}: {str(e)}")
        
        return charts
    
    def _classify_chart_type(self, text: str) -> str:
        """Classify the type of chart mentioned"""
        if '柱状图' in text or 'bar' in text:
            return 'bar_chart'
        elif '折线图' in text or 'line' in text:
            return 'line_chart'
        elif '饼图' in text or 'pie' in text:
            return 'pie_chart'
        elif '散点图' in text or 'scatter' in text:
            return 'scatter_plot'
        else:
            return 'general_chart'
    
    def _get_chart_context(self, lines: List[str], chart_line_idx: int) -> str:
        """Get context around chart mentions"""
        start_idx = max(0, chart_line_idx - 2)
        end_idx = min(len(lines), chart_line_idx + 3)
        context_lines = lines[start_idx:end_idx]
        return ' '.join(line.strip() for line in context_lines if line.strip())
    
    def _extract_financial_patterns(self, text: str, page_num: int) -> Dict[str, Any]:
        """
        Extract financial patterns and metrics from text
        """
        financial_data = {
            'page_number': page_num,
            'metrics': {},
            'currencies': [],
            'percentages': [],
            'years': [],
            'financial_terms': []
        }
        
        try:
            import re
            
            # Extract currency amounts
            currency_pattern = r'[¥$€£]\s*([\d,]+(?:\.\d{2})?)'
            currencies = re.findall(currency_pattern, text)
            financial_data['currencies'] = currencies[:10]  # Limit to first 10
            
            # Extract percentages
            percentage_pattern = r'(\d+\.?\d*)\s*%'
            percentages = re.findall(percentage_pattern, text)
            financial_data['percentages'] = percentages[:10]
            
            # Extract years
            year_pattern = r'\b(20\d{2})\b'
            years = list(set(re.findall(year_pattern, text)))
            financial_data['years'] = sorted(years)
            
            # Extract financial terms
            financial_terms = [
                '营业收入', '净利润', '总资产', '股东权益', '现金流',
                '毛利率', '净利率', '资产负债率', '流动比率'
            ]
            
            text_lower = text.lower()
            found_terms = [term for term in financial_terms if term in text_lower]
            financial_data['financial_terms'] = found_terms
            
            # Extract specific metrics with values
            metrics = {}
            for term in found_terms:
                # Look for the term followed by numbers
                pattern = rf'{re.escape(term)}[：:\s]*([¥$€£]?\s*[\d,]+(?:\.\d{{2}})?(?:\s*[万亿千百十]?[元人民币]?)?)'
                matches = re.findall(pattern, text)
                if matches:
                    metrics[term] = matches[0]
            
            financial_data['metrics'] = metrics
            
        except Exception as e:
            logger.error(f"Error extracting financial patterns from page {page_num}: {str(e)}")
        
        return financial_data
    
    def _extract_enhanced_metadata(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Extract enhanced metadata from documents
        """
        metadata = {
            'total_documents': len(documents),
            'company_info': {},
            'document_structure': {},
            'content_analysis': {}
        }
        
        try:
            if documents:
                # Combine text from first few documents for analysis
                combined_text = ' '.join([doc.text[:2000] for doc in documents[:5]])
                
                # Extract company information
                company_info = self._extract_company_info_enhanced(combined_text)
                metadata['company_info'] = company_info
                
                # Analyze document structure
                structure = self._analyze_document_structure(documents)
                metadata['document_structure'] = structure
                
                # Content analysis
                content_analysis = self._analyze_content_distribution(documents)
                metadata['content_analysis'] = content_analysis
                
        except Exception as e:
            logger.error(f"Error extracting enhanced metadata: {str(e)}")
        
        return metadata
    
    def _extract_company_info_enhanced(self, text: str) -> Dict[str, str]:
        """
        Extract enhanced company information using pattern matching
        """
        company_info = {
            'company_name': 'Unknown',
            'year': 'Unknown',
            'document_type': 'Annual Report',
            'industry': 'Unknown',
            'stock_code': 'Unknown'
        }
        
        try:
            import re
            
            # Extract company name (enhanced patterns)
            name_patterns = [
                r'([^。\n]*(?:股份有限公司|有限公司|公司|Corporation|Inc\.|Ltd\.|Corp\.)[^。\n]*)',
                r'公司全称[：:\s]*([^。\n]+)',
                r'Company Name[：:\s]*([^。\n]+)'
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    company_info['company_name'] = matches[0].strip()
                    break
            
            # Extract report year
            year_patterns = [
                r'(\d{4})\s*年\s*年度报告',
                r'Annual Report\s*(\d{4})',
                r'(\d{4})\s*年度',
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    company_info['year'] = matches[0]
                    break
            
            # Extract stock code
            stock_patterns = [
                r'股票代码[：:\s]*(\d{6})',
                r'证券代码[：:\s]*(\d{6})',
                r'Stock Code[：:\s]*(\w+)'
            ]
            
            for pattern in stock_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    company_info['stock_code'] = matches[0]
                    break
            
            # Detect document type
            if '年度报告' in text or 'Annual Report' in text:
                company_info['document_type'] = 'Annual Report'
            elif '季度报告' in text or 'Quarterly Report' in text:
                company_info['document_type'] = 'Quarterly Report'
            elif '招股说明书' in text or 'Prospectus' in text:
                company_info['document_type'] = 'Prospectus'
                
        except Exception as e:
            logger.error(f"Error extracting enhanced company info: {str(e)}")
        
        return company_info
    
    def _analyze_document_structure(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Analyze the structure of the document
        """
        structure = {
            'page_count': len(documents),
            'average_page_length': 0,
            'content_sections': [],
            'table_distribution': {},
            'text_quality_score': 0.0
        }
        
        try:
            if not documents:
                return structure
            
            # Calculate average page length
            page_lengths = [len(doc.text) for doc in documents]
            structure['average_page_length'] = sum(page_lengths) / len(page_lengths)
            
            # Identify content sections
            sections = []
            for i, doc in enumerate(documents):
                text = doc.text[:500].lower()  # First 500 chars
                section_type = 'content'
                
                if any(keyword in text for keyword in ['目录', 'contents', '索引']):
                    section_type = 'table_of_contents'
                elif any(keyword in text for keyword in ['摘要', 'summary', 'abstract']):
                    section_type = 'summary'
                elif any(keyword in text for keyword in ['财务', 'financial', '报表']):
                    section_type = 'financial_statements'
                elif any(keyword in text for keyword in ['附注', 'notes', '说明']):
                    section_type = 'notes'
                
                sections.append({
                    'page': i + 1,
                    'type': section_type,
                    'length': len(doc.text)
                })
            
            structure['content_sections'] = sections
            
            # Calculate text quality score
            total_length = sum(page_lengths)
            non_empty_pages = sum(1 for length in page_lengths if length > 100)
            structure['text_quality_score'] = non_empty_pages / len(documents) if documents else 0
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {str(e)}")
        
        return structure
    
    def _analyze_content_distribution(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Analyze content distribution across the document
        """
        analysis = {
            'text_pages': 0,
            'table_heavy_pages': 0,
            'short_pages': 0,
            'content_types': {},
            'language_distribution': {}
        }
        
        try:
            for doc in documents:
                text_length = len(doc.text)
                
                if text_length < 200:
                    analysis['short_pages'] += 1
                elif self._is_table_heavy_page(doc.text):
                    analysis['table_heavy_pages'] += 1
                else:
                    analysis['text_pages'] += 1
                
                # Analyze content type
                content_type = self._classify_page_content_type(doc.text)
                analysis['content_types'][content_type] = analysis['content_types'].get(content_type, 0) + 1
            
        except Exception as e:
            logger.error(f"Error analyzing content distribution: {str(e)}")
        
        return analysis
    
    def _is_table_heavy_page(self, text: str) -> bool:
        """Check if page is primarily tables"""
        lines = text.split('\n')
        table_lines = sum(1 for line in lines if self._is_table_line(line))
        return table_lines > len(lines) * 0.3  # More than 30% table lines
    
    def _classify_page_content_type(self, text: str) -> str:
        """Classify the primary content type of a page"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['资产负债表', 'balance sheet']):
            return 'balance_sheet'
        elif any(keyword in text_lower for keyword in ['利润表', 'income statement', '损益表']):
            return 'income_statement'
        elif any(keyword in text_lower for keyword in ['现金流量表', 'cash flow']):
            return 'cash_flow_statement'
        elif any(keyword in text_lower for keyword in ['附注', 'notes']):
            return 'notes'
        elif self._is_table_heavy_page(text):
            return 'tabular_data'
        else:
            return 'narrative_text'
    
    def _calculate_extraction_quality(self, enhanced_content: Dict[str, Any]) -> float:
        """
        Calculate overall extraction quality score
        """
        try:
            score = 0.0
            
            # Table extraction quality (40%)
            tables_count = enhanced_content.get('total_tables', 0)
            if tables_count > 0:
                score += min(tables_count / 10, 1.0) * 0.4
            
            # Content diversity (30%)
            pages_count = len(enhanced_content.get('pages', []))
            if pages_count > 0:
                content_types = set()
                for page in enhanced_content['pages']:
                    content_types.add(page.get('content_type', 'text'))
                diversity_score = len(content_types) / 4  # Max 4 types expected
                score += min(diversity_score, 1.0) * 0.3
            
            # Financial data detection (20%)
            financial_sections = len(enhanced_content.get('financial_sections', []))
            if financial_sections > 0:
                score += min(financial_sections / 5, 1.0) * 0.2
            
            # Chart detection bonus (10%)
            charts_count = enhanced_content.get('total_charts', 0)
            if charts_count > 0:
                score += min(charts_count / 3, 1.0) * 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating extraction quality: {str(e)}")
            return 0.5
    
    def _fallback_processing(self, uploaded_file) -> Dict[str, Any]:
        """
        Fallback to basic PDFReader processing if LlamaParse fails
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            result = self._fallback_processing_from_path(tmp_path, uploaded_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {str(e)}")
            raise e
    
    def _fallback_processing_from_path(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Fallback processing from file path
        """
        try:
            # Use basic PDFReader for text pages
            documents = self.fallback_reader.load_data(Path(pdf_path))

            # Attempt table extraction with pdfplumber for better fallback quality
            total_tables = 0
            enhanced_pages = []
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_entry = {
                            'page_number': i + 1,
                            'tables': [],
                            'charts': [],
                            'content_type': 'text'
                        }
                        try:
                            tables = page.extract_tables()
                            if tables:
                                import pandas as pd
                                for j, table in enumerate(tables):
                                    if table and len(table) > 0:
                                        # Normalize to DataFrame (best-effort headers)
                                        headers = table[0] if table and len(table) > 1 else [f"col{k+1}" for k in range(len(table[0]) if table and table[0] else 0)]
                                        data_rows = table[1:] if len(table) > 1 else []
                                        try:
                                            df = pd.DataFrame(data_rows, columns=headers)
                                        except Exception:
                                            df = pd.DataFrame(table)
                                        page_entry['tables'].append({
                                            'table_id': f"fallback_page_{i+1}_table_{j+1}",
                                            'page_number': i + 1,
                                            'dataframe': df,
                                            'rows': len(df),
                                            'columns': len(df.columns),
                                            'extraction_method': 'fallback_pdfplumber'
                                        })
                                if page_entry['tables']:
                                    total_tables += len(page_entry['tables'])
                                    page_entry['content_type'] = 'table_rich'
                        except Exception as te:
                            logger.debug(f"pdfplumber table extraction error on page {i+1}: {te}")
                        enhanced_pages.append(page_entry)
            except Exception as pe:
                logger.debug(f"pdfplumber fallback unavailable or failed: {pe}")

            enhanced_content = {
                'pages': enhanced_pages,
                'tables': [t for p in enhanced_pages for t in p.get('tables', [])],
                'charts': [],
                'financial_sections': [],
                'total_tables': total_tables,
                'total_charts': 0,
                'quality_score': 0.3
            }

            result = {
                'filename': filename,
                'documents': documents,
                'enhanced_content': enhanced_content,
                'metadata': {'extraction_method': 'fallback'},
                'page_count': len(documents),
                'total_text_length': sum(len(doc.text) for doc in documents),
                'extraction_method': 'basic_fallback',
                'tables_extracted': total_tables,
                'charts_detected': 0
            }

            logger.warning(f"Used fallback processing for {filename}")
            return result

        except Exception as e:
            logger.error(f"Fallback processing failed: {str(e)}")
            raise e
    
    def get_processing_stats(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced processing statistics
        """
        stats = {
            'filename': processed_data.get('filename', 'Unknown'),
            'page_count': processed_data.get('page_count', 0),
            'text_length': processed_data.get('total_text_length', 0),
            'tables_extracted': processed_data.get('tables_extracted', 0),
            'charts_detected': processed_data.get('charts_detected', 0),
            'extraction_method': processed_data.get('extraction_method', 'unknown'),
            'quality_score': 0.0
        }
        
        try:
            enhanced_content = processed_data.get('enhanced_content', {})
            stats['quality_score'] = enhanced_content.get('quality_score', 0.0)
            
            # Additional statistics from enhanced content
            if 'pages' in enhanced_content:
                content_types = {}
                for page in enhanced_content['pages']:
                    content_type = page.get('content_type', 'unknown')
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                stats['content_distribution'] = content_types
            
        except Exception as e:
            logger.error(f"Error calculating enhanced stats: {str(e)}")
        
        return stats