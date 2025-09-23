"""
Simplified integration of enhanced LlamaIndex components with existing system
"""

import os
import logging
from typing import Dict, Any, Optional
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from utils.enhanced_pdf_processor import EnhancedPDFProcessor
from utils.enhanced_query_engines import EnhancedQueryEngineManager
from utils.pdf_processor import PDFProcessor  # Fallback
from utils.multi_format_processor import MultiFormatProcessor
from utils.rag_system import RAGSystem
from utils.table_extractor import TableExtractor

logger = logging.getLogger(__name__)

class EnhancedSystemIntegrator:
    """
    Simplified integrator for enhanced LlamaIndex components
    """
    
    def __init__(self):
        self.use_enhanced = os.getenv('USE_ENHANCED_LLAMAINDEX', 'false').lower() == 'true'
        self.enhanced_pdf_processor = None
        self.legacy_pdf_processor = None
        self.multi_format_processor = None
        self.enhanced_query_manager = None
        self.rag_system = None
        self.table_extractor = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize components based on configuration"""
        try:
            # Always initialize core components
            self.legacy_pdf_processor = PDFProcessor()
            self.multi_format_processor = MultiFormatProcessor()
            self.rag_system = RAGSystem()
            self.table_extractor = TableExtractor()
            logger.info("✅ Core components initialized")

            # Initialize enhanced components if enabled
            if self.use_enhanced:
                try:
                    self.enhanced_pdf_processor = EnhancedPDFProcessor(use_premium_parse=True)
                    logger.info("✅ Enhanced PDF processor initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize enhanced PDF processor: {str(e)}")
                    self.use_enhanced = False
            
            logger.info(f"System integrator initialized (enhanced: {self.use_enhanced})")
            
        except Exception as e:
            logger.error(f"Error initializing system integrator: {str(e)}")
            # Fall back to legacy only
            self.use_enhanced = False
    
    def process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Process uploaded file with appropriate processor based on file type
        """
        try:
            # 获取文件扩展名
            file_ext = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''

            # 对于PDF文件，优先使用增强处理器
            if file_ext == 'pdf':
                if self.use_enhanced and self.enhanced_pdf_processor is not None:
                    logger.info(f"Processing PDF {uploaded_file.name} with enhanced processor")
                    result = self.enhanced_pdf_processor.process_uploaded_file(uploaded_file)

                    # Add compatibility layer for legacy system
                    if 'enhanced_content' in result:
                        result['detailed_content'] = self._convert_enhanced_to_legacy_format(
                            result['enhanced_content']
                        )

                    result['processing_method'] = 'enhanced_llamaparse'
                    return result
                else:
                    # 使用传统PDF处理器
                    logger.info(f"Processing PDF {uploaded_file.name} with legacy processor")
                    result = self.legacy_pdf_processor.process_uploaded_file(uploaded_file)
                    result['processing_method'] = 'legacy_pdf'
                    return result
            else:
                # 对于其他格式，使用多格式处理器
                logger.info(f"Processing {file_ext.upper()} file {uploaded_file.name} with multi-format processor")
                result = self.multi_format_processor.process_uploaded_file(uploaded_file)
                return result

        except Exception as e:
            logger.error(f"Error in file processing: {str(e)}")
            # 尝试降级处理
            file_ext = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''

            if file_ext == 'pdf' and self.legacy_pdf_processor is not None:
                try:
                    logger.info("Falling back to legacy PDF processor")
                    result = self.legacy_pdf_processor.process_uploaded_file(uploaded_file)
                    result['processing_method'] = 'legacy_fallback'
                    result['processing_error'] = str(e)
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback processing also failed: {str(fallback_error)}")

            # 如果所有处理都失败，抛出原始错误
            raise e
    
    def _convert_enhanced_to_legacy_format(self, enhanced_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert enhanced content format to legacy format for compatibility
        """
        try:
            legacy_format = {
                'pages': [],
                'metadata': {},
                'total_pages': len(enhanced_content.get('pages', []))
            }
            
            # Convert pages
            for page_data in enhanced_content.get('pages', []):
                legacy_page = {
                    'page_number': page_data.get('page_number', 1),
                    'text': page_data.get('text_content', ''),
                    'tables': [],
                    'images': 0,
                    'width': 600,
                    'height': 800
                }
                
                # Convert tables to legacy format
                if 'tables' in page_data:
                    for table in page_data['tables']:
                        legacy_table = {
                            'table_id': table.get('table_id', f"page_{legacy_page['page_number']}_table_1"),
                            'data': self._dataframe_to_nested_list(table.get('dataframe')),
                            'rows': table.get('rows', 0),
                            'cols': table.get('columns', 0)
                        }
                        legacy_page['tables'].append(legacy_table)
                
                legacy_format['pages'].append(legacy_page)
            
            return legacy_format
            
        except Exception as e:
            logger.error(f"Error converting enhanced to legacy format: {str(e)}")
            return {'pages': [], 'metadata': {}, 'total_pages': 0}
    
    def _dataframe_to_nested_list(self, df) -> list:
        """Convert DataFrame to nested list format"""
        try:
            if df is None:
                return []
            
            # Get column headers
            headers = df.columns.tolist()
            
            # Get data rows
            data_rows = df.values.tolist()
            
            # Combine headers and data
            result = [headers] + data_rows
            return result
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to nested list: {str(e)}")
            return []
    
    def build_enhanced_rag_index(self, processed_documents: Dict[str, Any], extracted_tables: Dict[str, Any]) -> bool:
        """
        Build RAG index with enhanced capabilities if available
        """
        try:
            # Build standard RAG index first
            if self.rag_system is None:
                return False
            success = self.rag_system.build_index(processed_documents, extracted_tables)
            
            if success and self.use_enhanced:
                # Try to build enhanced query manager
                try:
                    if self.rag_system is None:
                        return success
                    index = getattr(self.rag_system, 'index', None)
                    if index:
                        llm = getattr(self.rag_system, 'llm', None)
                        self.enhanced_query_manager = EnhancedQueryEngineManager(index, llm)
                        router_engine = self.enhanced_query_manager.build_router_query_engine()
                        if router_engine:
                            logger.info("Enhanced query engine manager built successfully")
                        
                except Exception as e:
                    logger.warning(f"Failed to build enhanced query manager: {str(e)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error building RAG index: {str(e)}")
            return False
    
    def query_system(self, question: str, context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Query the system with enhanced or legacy RAG
        """
        try:
            if self.use_enhanced and self.enhanced_query_manager:
                logger.info("Using enhanced query system")
                result = self.enhanced_query_manager.query(
                    question=question,
                    engine_type="router",
                    context_filter=context_filter
                )
                result['query_method'] = 'enhanced_router'
                return result
            
            else:
                logger.info("Using legacy query system")
                if self.rag_system is None:
                    return {
                        'answer': "RAG system not available",
                        'error': True,
                        'query_method': 'error'
                    }
                result = self.rag_system.query(question, context_filter)
                result['query_method'] = 'legacy_basic'
                return result
                
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}")
            # Fall back to legacy system
            if self.rag_system is not None:
                result = self.rag_system.query(question, context_filter)
                result['query_method'] = 'legacy_fallback'
                result['query_error'] = str(e)
                return result
            else:
                return {
                    'answer': f"Query system error: {str(e)}",
                    'error': True,
                    'query_method': 'error'
                }
    
    def get_processing_stats(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get processing statistics with enhanced information
        """
        try:
            # Get basic stats based on processing method
            processing_method = processed_data.get('processing_method', 'unknown')

            if processing_method == 'multi_format_processor' and self.multi_format_processor is not None:
                stats = self.multi_format_processor.get_processing_stats(processed_data)
            elif (self.enhanced_pdf_processor is not None and
                  processing_method.startswith('enhanced')):
                stats = self.enhanced_pdf_processor.get_processing_stats(processed_data)
            elif self.legacy_pdf_processor is not None:
                stats = self.legacy_pdf_processor.get_processing_stats(processed_data)
            else:
                stats = {'error': 'No processor available', 'integration_info': {}}
            
            # Add integration information
            stats['integration_info'] = {
                'enhanced_mode': self.use_enhanced,
                'processing_method': processed_data.get('processing_method', 'unknown'),
                'has_enhanced_query': self.enhanced_query_manager is not None,
                'components_available': {
                    'enhanced_pdf': self.enhanced_pdf_processor is not None,
                    'enhanced_query': self.enhanced_query_manager is not None,
                    'legacy_pdf': self.legacy_pdf_processor is not None,
                    'multi_format': self.multi_format_processor is not None,
                    'rag_system': self.rag_system is not None
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            return {
                'error': str(e),
                'integration_info': {'enhanced_mode': False}
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status and capabilities
        """
        return {
            'enhanced_mode': self.use_enhanced,
            'components': {
                'enhanced_pdf_processor': self.enhanced_pdf_processor is not None,
                'enhanced_query_manager': self.enhanced_query_manager is not None,
                'legacy_pdf_processor': self.legacy_pdf_processor is not None,
                'rag_system': self.rag_system is not None,
                'table_extractor': self.table_extractor is not None
            },
            'capabilities': {
                'llamaparse_processing': self.use_enhanced and self.enhanced_pdf_processor is not None,
                'advanced_querying': self.use_enhanced and self.enhanced_query_manager is not None,
                'fallback_available': self.legacy_pdf_processor is not None
            },
            'environment': {
                'llamaparse_key_available': bool(os.getenv('LLAMA_CLOUD_API_KEY')),
                'openai_key_available': bool(os.getenv('OPENAI_API_KEY')),
                'enhanced_flag': os.getenv('USE_ENHANCED_LLAMAINDEX', 'false')
            }
        }


# Global integrator instance
_integrator_instance = None

def get_system_integrator() -> EnhancedSystemIntegrator:
    """
    Get the global system integrator instance
    """
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = EnhancedSystemIntegrator()
    return _integrator_instance

def reset_system_integrator():
    """
    Reset the global integrator instance (useful for testing)
    """
    global _integrator_instance
    _integrator_instance = None