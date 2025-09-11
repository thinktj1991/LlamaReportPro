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
        # Document processing state
        if 'processed_documents' not in st.session_state:
            st.session_state.processed_documents = {}
        
        if 'extracted_tables' not in st.session_state:
            st.session_state.extracted_tables = {}
        
        # RAG system state
        if 'rag_index' not in st.session_state:
            st.session_state.rag_index = None
        
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        # Company analysis state
        if 'company_data' not in st.session_state:
            st.session_state.company_data = {}
        
        # Processing components - initialize lazily to avoid import errors
        if 'pdf_processor' not in st.session_state:
            st.session_state.pdf_processor = None
        
        if 'table_extractor' not in st.session_state:
            st.session_state.table_extractor = None
        
        if 'rag_system' not in st.session_state:
            st.session_state.rag_system = None
        
        if 'company_comparator' not in st.session_state:
            st.session_state.company_comparator = None
        
        if 'data_visualizer' not in st.session_state:
            st.session_state.data_visualizer = None
        
        # Backward compatibility - some pages use 'visualizer' key
        if 'visualizer' not in st.session_state:
            st.session_state.visualizer = None
        
        # Processing status flags
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        
        if 'last_upload_time' not in st.session_state:
            st.session_state.last_upload_time = None
            
        logger.debug("Session state initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        st.error("Error initializing application state")

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