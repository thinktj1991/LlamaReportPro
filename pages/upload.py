import streamlit as st
import os
from utils.pdf_processor import PDFProcessor
from utils.table_extractor import TableExtractor
from utils.rag_system import RAGSystem
from utils.company_comparator import CompanyComparator
from utils.state import init_state, init_processors, get_processing_stats, clear_all_data
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_upload_page():
    st.header("📁 Upload & Process Documents")
    st.markdown("Upload annual reports and other financial documents for analysis")
    
    # Initialize session state safely
    init_state()
    
    # Initialize processors
    if not init_processors():
        st.error("Failed to initialize processing components")
        return
    
    # File upload section
    st.subheader("📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload annual reports, financial statements, or other PDF documents"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Selected {len(uploaded_files)} file(s)")
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size:,} bytes)")
        
        with col2:
            process_button = st.button("🚀 Process All Files", type="primary", use_container_width=True)
        
        if process_button:
            process_uploaded_files(uploaded_files)
    
    # Display processing status
    show_processing_status()
    
    # Document management
    show_document_management()

def process_uploaded_files(uploaded_files):
    """
    Process all uploaded files
    """
    total_files = len(uploaded_files)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # Process PDF
                processed_data = st.session_state.pdf_processor.process_uploaded_file(uploaded_file)
                
                # Extract company information
                company_info = st.session_state.pdf_processor.extract_company_info(processed_data['documents'])
                processed_data['company_info'] = company_info
                
                # Store processed document
                st.session_state.processed_documents[uploaded_file.name] = processed_data
                
                # Extract tables
                doc_tables = st.session_state.table_extractor.extract_and_process_tables(
                    {uploaded_file.name: processed_data}
                )
                st.session_state.extracted_tables.update(doc_tables)
                
                # Update progress
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
        
        # Build RAG index
        status_text.text("Building search index...")
        with st.spinner("Building search index..."):
            success = st.session_state.rag_system.build_index(
                st.session_state.processed_documents,
                st.session_state.extracted_tables
            )
            
            if success:
                st.session_state.rag_index = st.session_state.rag_system.index
        
        # Prepare company data for comparison
        status_text.text("Preparing company data...")
        with st.spinner("Preparing company data..."):
            company_data = st.session_state.company_comparator.prepare_company_data(
                st.session_state.processed_documents,
                st.session_state.extracted_tables
            )
            st.session_state.company_data = company_data
        
        progress_bar.progress(1.0)
        status_text.text("✅ Processing complete!")
        
        st.success(f"Successfully processed {total_files} document(s)!")
        
        # Show processing summary
        show_processing_summary()
        
        # Auto-rerun to update the interface
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        st.error(f"Error processing files: {str(e)}")

def show_processing_status():
    """
    Display current processing status
    """
    st.subheader("📊 Processing Status")
    
    # Get processing stats safely
    stats = get_processing_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents Processed", stats['documents_count'])
    
    with col2:
        st.metric("Tables Extracted", stats['tables_count'])
    
    with col3:
        rag_status = "✅ Ready" if stats['rag_ready'] else "❌ Not Built"
        st.metric("Search Index", rag_status)
    
    with col4:
        st.metric("Companies Identified", stats['companies_count'])

def show_processing_summary():
    """
    Show detailed processing summary
    """
    if not st.session_state.processed_documents:
        return
    
    st.subheader("📋 Processing Summary")
    
    for doc_name, doc_data in st.session_state.processed_documents.items():
        with st.expander(f"📄 {doc_name}"):
            # Basic statistics
            stats = st.session_state.pdf_processor.get_processing_stats(doc_data)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pages", stats['page_count'])
            with col2:
                st.metric("Text Length", f"{stats['text_length']:,} chars")
            with col3:
                st.metric("Tables Found", stats['tables_found'])
            
            # Company information
            company_info = doc_data.get('company_info', {})
            if company_info:
                st.write("**Company Information:**")
                for key, value in company_info.items():
                    st.write(f"• {key.title()}: {value}")
            
            # Table details
            doc_tables = st.session_state.extracted_tables.get(doc_name, [])
            if doc_tables:
                st.write("**Extracted Tables:**")
                for table in doc_tables:
                    financial_badge = "💰 Financial" if table['is_financial'] else "📋 General"
                    importance = table['importance_score']
                    st.write(f"• {table['table_id']} - {financial_badge} - Importance: {importance:.2f}")

def show_document_management():
    """
    Show document management options
    """
    if not st.session_state.processed_documents:
        return
    
    st.subheader("🗂️ Document Management")
    
    # Clear all data option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("Manage your processed documents and data")
    
    with col2:
        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            clear_all_data_local()

def clear_all_data_local():
    """
    Clear all processed data using the centralized function
    """
    try:
        clear_all_data()
        st.success("All data cleared successfully!")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        st.error(f"Error clearing data: {str(e)}")

# Additional helper functions
def validate_pdf_file(uploaded_file) -> bool:
    """
    Validate uploaded PDF file
    """
    try:
        # Check file size (limit to 50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            st.error(f"File {uploaded_file.name} is too large. Please upload files smaller than 50MB.")
            return False
        
        # Check file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            st.error(f"File {uploaded_file.name} is not a PDF file.")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating file {uploaded_file.name}: {str(e)}")
        return False

# Main execution for Streamlit multipage
if __name__ == "__main__":
    show_upload_page()
