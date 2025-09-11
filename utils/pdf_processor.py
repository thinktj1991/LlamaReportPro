import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
from llama_index.core import Document
from llama_index.readers.file import PDFReader
import pdfplumber
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.pdf_reader = PDFReader()
    
    def process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Process an uploaded PDF file and extract content
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract text using LlamaIndex
            from pathlib import Path
            documents = self.pdf_reader.load_data(Path(tmp_path))
            
            # Extract detailed content using pdfplumber
            detailed_content = self._extract_detailed_content(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            result = {
                'filename': uploaded_file.name,
                'documents': documents,
                'detailed_content': detailed_content,
                'page_count': len(detailed_content['pages']),
                'total_text_length': len(' '.join([doc.text for doc in documents]))
            }
            
            logger.info(f"Successfully processed {uploaded_file.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {uploaded_file.name}: {str(e)}")
            raise e
    
    def _extract_detailed_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract detailed content including metadata using pdfplumber
        """
        content = {
            'pages': [],
            'metadata': {},
            'total_pages': 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                content['metadata'] = pdf.metadata or {}
                content['total_pages'] = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_content = {
                        'page_number': i + 1,
                        'text': page.extract_text() or '',
                        'tables': [],
                        'images': len(page.images),
                        'width': page.width,
                        'height': page.height
                    }
                    
                    # Extract tables from this page
                    tables = page.extract_tables()
                    if tables:
                        for j, table in enumerate(tables):
                            if table and len(table) > 0:
                                page_content['tables'].append({
                                    'table_id': f"page_{i+1}_table_{j+1}",
                                    'data': table,
                                    'rows': len(table),
                                    'cols': len(table[0]) if table[0] else 0
                                })
                    
                    content['pages'].append(page_content)
                    
        except Exception as e:
            logger.error(f"Error extracting detailed content: {str(e)}")
            raise e
        
        return content
    
    def extract_company_info(self, documents: List[Document]) -> Dict[str, str]:
        """
        Extract basic company information from documents
        """
        company_info = {
            'company_name': 'Unknown',
            'year': 'Unknown',
            'document_type': 'Annual Report'
        }
        
        try:
            # Combine first few pages for company info extraction
            text_sample = ' '.join([doc.text[:1000] for doc in documents[:3]])
            text_lower = text_sample.lower()
            
            # Simple extraction patterns (can be enhanced with NLP)
            lines = text_sample.split('\n')
            for line in lines[:20]:  # Check first 20 lines
                line_clean = line.strip()
                line_lower = line_clean.lower()
                if len(line_clean) > 5 and len(line_clean) < 100:
                    # Look for company name patterns
                    if any(keyword in line_lower for keyword in ['corporation', 'inc.', 'ltd.', 'company', 'corp']):
                        company_info['company_name'] = line_clean
                        break
            
            # Extract year
            import re
            year_pattern = r'\b(20\d{2})\b'
            years = re.findall(year_pattern, text_sample)
            if years:
                company_info['year'] = max(years)  # Get the most recent year
                
        except Exception as e:
            logger.error(f"Error extracting company info: {str(e)}")
        
        return company_info
    
    def get_processing_stats(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate processing statistics
        """
        stats = {
            'filename': processed_data['filename'],
            'page_count': processed_data['page_count'],
            'text_length': processed_data['total_text_length'],
            'tables_found': 0,
            'images_found': 0
        }
        
        try:
            for page in processed_data['detailed_content']['pages']:
                stats['tables_found'] += len(page['tables'])
                stats['images_found'] += page['images']
        except Exception as e:
            logger.error(f"Error calculating stats: {str(e)}")
        
        return stats
