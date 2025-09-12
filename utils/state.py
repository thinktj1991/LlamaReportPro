"""
Session State Management Utility

This module provides centralized session state initialization
to prevent crashes from uninitialized state variables.
"""

import streamlit as st
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def init_state():
    """
    Initialize all session state variables with safe defaults.
    Call this at the top of every page to prevent AttributeError crashes.
    """
    try:
        # Ensure session_state exists and is properly initialized
        if not hasattr(st, 'session_state'):
            logger.error("Streamlit session_state not available")
            return False
        
        # Document processing state
        if not hasattr(st.session_state, 'processed_documents') or st.session_state.processed_documents is None:
            st.session_state.processed_documents = {}
        
        if not hasattr(st.session_state, 'extracted_tables') or st.session_state.extracted_tables is None:
            st.session_state.extracted_tables = {}
        
        # RAG system state
        if not hasattr(st.session_state, 'rag_index'):
            st.session_state.rag_index = None
        
        if not hasattr(st.session_state, 'query_history') or st.session_state.query_history is None:
            st.session_state.query_history = []
        
        # Company analysis state
        if not hasattr(st.session_state, 'company_data') or st.session_state.company_data is None:
            st.session_state.company_data = {}
        
        # Processing components - initialize lazily to avoid import errors
        if not hasattr(st.session_state, 'pdf_processor'):
            st.session_state.pdf_processor = None
        
        if not hasattr(st.session_state, 'table_extractor'):
            st.session_state.table_extractor = None
        
        if not hasattr(st.session_state, 'rag_system'):
            st.session_state.rag_system = None
        
        if not hasattr(st.session_state, 'company_comparator'):
            st.session_state.company_comparator = None
        
        if not hasattr(st.session_state, 'data_visualizer'):
            st.session_state.data_visualizer = None
        
        # Backward compatibility - some pages use 'visualizer' key
        if not hasattr(st.session_state, 'visualizer'):
            st.session_state.visualizer = None
        
        # Processing status flags
        if not hasattr(st.session_state, 'processing_complete'):
            st.session_state.processing_complete = False
        
        if not hasattr(st.session_state, 'last_upload_time'):
            st.session_state.last_upload_time = None
            
        logger.debug("Session state initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        # Try to show error only if st.error is available
        try:
            st.error("Error initializing application state")
        except:
            pass
        return False

def init_processors():
    """
    Initialize processing components lazily when needed.
    This avoids import errors during initial page load.
    """
    try:
        if st.session_state.pdf_processor is None:
            from utils.pdf_processor import PDFProcessor
            st.session_state.pdf_processor = PDFProcessor()
        
        if st.session_state.table_extractor is None:
            from utils.table_extractor import TableExtractor
            st.session_state.table_extractor = TableExtractor()
        
        if st.session_state.rag_system is None:
            from utils.rag_system import RAGSystem
            st.session_state.rag_system = RAGSystem()
        
        if st.session_state.company_comparator is None:
            from utils.company_comparator import CompanyComparator
            st.session_state.company_comparator = CompanyComparator()
        
        if st.session_state.data_visualizer is None:
            from utils.data_visualizer import DataVisualizer
            visualizer_instance = DataVisualizer()
            st.session_state.data_visualizer = visualizer_instance
            st.session_state.visualizer = visualizer_instance  # Backward compatibility
        
        logger.debug("Processors initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing processors: {str(e)}")
        st.error(f"Error initializing processing components: {str(e)}")
        return False

def get_processing_stats() -> Dict[str, Any]:
    """
    Get current processing statistics safely.
    """
    stats = {
        'documents_count': len(st.session_state.processed_documents),
        'tables_count': sum(len(tables) for tables in st.session_state.extracted_tables.values()),
        'companies_count': len(st.session_state.company_data),
        'rag_ready': st.session_state.rag_index is not None,
        'processing_complete': st.session_state.processing_complete
    }
    return stats

def clear_all_data():
    """
    Clear all processed data from session state.
    """
    try:
        st.session_state.processed_documents = {}
        st.session_state.extracted_tables = {}
        st.session_state.rag_index = None
        st.session_state.company_data = {}
        st.session_state.query_history = []
        st.session_state.processing_complete = False
        st.session_state.last_upload_time = None
        
        # Reset RAG system if it exists
        if st.session_state.rag_system:
            st.session_state.rag_system.index = None
            st.session_state.rag_system.query_engine = None
        
        logger.info("All data cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        raise