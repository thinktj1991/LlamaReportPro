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
    st.header("📁 上传与处理文档")
    st.markdown("上传年报和其他财务文档进行分析")
    
    # Initialize session state safely
    init_state()
    
    # Initialize processors
    if not init_processors():
        st.error("初始化处理组件失败")
        return
    
    # File upload section
    st.subheader("📤 上传文档")
    uploaded_files = st.file_uploader(
        "选择PDF文件",
        type=['pdf'],
        accept_multiple_files=True,
        help="上传年报、财务报表或其他PDF文档"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"已选择 {len(uploaded_files)} 个文件")
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size:,} 字节)")
        
        with col2:
            process_button = st.button("🚀 处理所有文件", type="primary", use_container_width=True)
        
        if process_button:
            process_uploaded_files(uploaded_files)
    
    # Display processing status
    show_processing_status()
    
    # Document management
    show_document_management()

def process_uploaded_files(uploaded_files):
    """
    Process all uploaded files with validation
    """
    total_files = len(uploaded_files)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Track validation and processing results
    validation_results = []
    processing_results = []
    valid_files = []
    
    try:
        # Step 1: Validate all files first
        status_text.text("🔍 正在验证上传的文件...")
        
        for uploaded_file in uploaded_files:
            is_valid, error_message = validate_pdf_file(uploaded_file)
            validation_results.append({
                'filename': uploaded_file.name,
                'is_valid': is_valid,
                'error_message': error_message,
                'file_size': uploaded_file.size
            })
            
            if is_valid:
                valid_files.append(uploaded_file)
        
        # Show validation summary
        show_validation_summary(validation_results)
        
        # If no valid files, stop processing
        if not valid_files:
            st.error("❌ 没有有效的文件可以处理。请检查上方的验证错误并上传有效的PDF文件。")
            return
        
        # Step 2: Process only valid files
        st.info(f"📋 正在处理 {len(valid_files)} 个有效文件（共上传 {total_files} 个文件）...")
        
        for i, uploaded_file in enumerate(valid_files):
            try:
                status_text.text(f"正在处理 {uploaded_file.name}...")
                
                with st.spinner(f"正在处理 {uploaded_file.name}..."):
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
                    
                    processing_results.append({
                        'filename': uploaded_file.name,
                        'success': True,
                        'error_message': None
                    })
                    
            except Exception as file_error:
                error_msg = f"Error processing {uploaded_file.name}: {str(file_error)}"
                logger.error(error_msg)
                processing_results.append({
                    'filename': uploaded_file.name,
                    'success': False,
                    'error_message': error_msg
                })
                st.warning(f"⚠️ 由于处理错误跳过了 {uploaded_file.name}：{str(file_error)}")
            
            # Update progress
            progress = (i + 1) / len(valid_files)
            progress_bar.progress(progress)
        
        # Check if any files were successfully processed
        successful_files = [r for r in processing_results if r['success']]
        
        if not successful_files:
            st.error("❌ 没有文件能够成功处理。请检查上方的错误消息。")
            return
        
        # Step 3: Build RAG index for successfully processed files
        status_text.text("正在构建搜索索引...")
        with st.spinner("正在构建搜索索引..."):
            success = st.session_state.rag_system.build_index(
                st.session_state.processed_documents,
                st.session_state.extracted_tables
            )
            
            if success:
                st.session_state.rag_index = st.session_state.rag_system.index
        
        # Step 4: Prepare company data for comparison
        status_text.text("正在准备公司数据...")
        with st.spinner("正在准备公司数据..."):
            company_data = st.session_state.company_comparator.prepare_company_data(
                st.session_state.processed_documents,
                st.session_state.extracted_tables
            )
            st.session_state.company_data = company_data
        
        progress_bar.progress(1.0)
        status_text.text("✅ 处理完成！")
        
        # Show final summary
        show_final_processing_summary(validation_results, processing_results)
        
        # Show processing summary
        show_processing_summary()
        
        # Auto-rerun to update the interface
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        st.error(f"处理文件错误：{str(e)}")

def show_processing_status():
    """
    Display current processing status
    """
    st.subheader("📊 处理状态")
    
    # Get processing stats safely
    stats = get_processing_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("已处理文档", stats['documents_count'])
    
    with col2:
        st.metric("已提取表格", stats['tables_count'])
    
    with col3:
        rag_status = "✅ 就绪" if stats['rag_ready'] else "❌ 未构建"
        st.metric("搜索索引", rag_status)
    
    with col4:
        st.metric("已识别公司", stats['companies_count'])

def show_processing_summary():
    """
    Show detailed processing summary
    """
    if not st.session_state.processed_documents:
        return
    
    st.subheader("📋 处理摘要")
    
    for doc_name, doc_data in st.session_state.processed_documents.items():
        with st.expander(f"📄 {doc_name}"):
            # Basic statistics
            stats = st.session_state.pdf_processor.get_processing_stats(doc_data)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("页数", stats['page_count'])
            with col2:
                st.metric("文本长度", f"{stats['text_length']:,} 字符")
            with col3:
                st.metric("发现表格", stats['tables_found'])
            
            # Company information
            company_info = doc_data.get('company_info', {})
            if company_info:
                st.write("**公司信息：**")
                for key, value in company_info.items():
                    st.write(f"• {key.title()}: {value}")
            
            # Table details
            doc_tables = st.session_state.extracted_tables.get(doc_name, [])
            if doc_tables:
                st.write("**已提取表格：**")
                for table in doc_tables:
                    financial_badge = "💰 财务" if table['is_financial'] else "📋 一般"
                    importance = table['importance_score']
                    st.write(f"• {table['table_id']} - {financial_badge} - 重要性：{importance:.2f}")

def show_document_management():
    """
    Show document management options
    """
    if not st.session_state.processed_documents:
        return
    
    st.subheader("🗂️ 文档管理")
    
    # Clear all data option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("管理您已处理的文档和数据")
    
    with col2:
        if st.button("🗑️ 清除所有数据", type="secondary", use_container_width=True):
            clear_all_data_local()

def clear_all_data_local():
    """
    Clear all processed data using the centralized function
    """
    try:
        clear_all_data()
        st.success("所有数据已成功清除！")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        st.error(f"清除数据错误：{str(e)}")

# Additional helper functions
def show_validation_summary(validation_results):
    """
    Display validation results for uploaded files
    """
    if not validation_results:
        return
    
    st.subheader("🔍 文件验证结果")
    
    valid_files = [r for r in validation_results if r['is_valid']]
    invalid_files = [r for r in validation_results if not r['is_valid']]
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总文件数", len(validation_results))
    with col2:
        st.metric("✅ 有效文件", len(valid_files), delta=None, delta_color="normal")
    with col3:
        st.metric("❌ 无效文件", len(invalid_files), delta=None, delta_color="inverse")
    
    # Show valid files
    if valid_files:
        with st.expander(f"✅ Valid Files ({len(valid_files)})", expanded=True):
            for result in valid_files:
                st.success(f"✅ {result['filename']} ({result['file_size']:,} bytes)")
    
    # Show invalid files with error details
    if invalid_files:
        with st.expander(f"❌ Invalid Files ({len(invalid_files)})", expanded=True):
            for result in invalid_files:
                st.error(f"❌ {result['filename']}: {result['error_message']}")

def show_final_processing_summary(validation_results, processing_results):
    """
    Display final summary of validation and processing results
    """
    st.subheader("📊 Processing Summary")
    
    # Calculate statistics
    total_uploaded = len(validation_results)
    valid_files = len([r for r in validation_results if r['is_valid']])
    invalid_files = total_uploaded - valid_files
    successful_processing = len([r for r in processing_results if r['success']])
    failed_processing = len([r for r in processing_results if not r['success']])
    
    # Show metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Uploaded", total_uploaded)
    
    with col2:
        st.metric("✅ Valid", valid_files)
    
    with col3:
        st.metric("🚀 Processed", successful_processing)
    
    with col4:
        st.metric("❌ Failed", invalid_files + failed_processing)
    
    # Show processing errors if any
    failed_files = [r for r in processing_results if not r['success']]
    if failed_files:
        with st.expander("⚠️ Processing Errors", expanded=False):
            for result in failed_files:
                st.warning(f"⚠️ {result['filename']}: {result['error_message']}")
    
    # Show success message
    if successful_processing > 0:
        if successful_processing == total_uploaded:
            st.success(f"🎉 All {total_uploaded} files processed successfully!")
        else:
            st.success(f"✅ Successfully processed {successful_processing} out of {total_uploaded} files")

def validate_pdf_file(uploaded_file) -> tuple[bool, str]:
    """
    Validate uploaded PDF file with comprehensive checks
    Returns (is_valid, error_message)
    """
    try:
        # Check file size (limit to 50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            return False, f"File {uploaded_file.name} is too large ({uploaded_file.size:,} bytes). Please upload files smaller than 50MB."
        
        # Check minimum file size (100 bytes)
        if uploaded_file.size < 100:
            return False, f"File {uploaded_file.name} appears to be empty or corrupted."
        
        # Check file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            return False, f"File {uploaded_file.name} is not a PDF file. Only PDF files are supported."
        
        # Validate filename (check for valid characters and length)
        import re
        filename = uploaded_file.name
        if len(filename) > 255:
            return False, f"Filename {filename} is too long. Please use a shorter filename."
        
        # Check for potentially problematic characters
        if re.search(r'[<>:"/\\|?*]', filename):
            return False, f"Filename {filename} contains invalid characters. Please use only letters, numbers, spaces, hyphens, and underscores."
        
        # Validate PDF header by reading first few bytes
        uploaded_file.seek(0)  # Reset file pointer
        header = uploaded_file.read(8)
        uploaded_file.seek(0)  # Reset again for future use
        
        if not header.startswith(b'%PDF-'):
            return False, f"File {uploaded_file.name} does not appear to be a valid PDF (invalid header)."
        
        # Try to open with pdfplumber for basic PDF structure validation
        import pdfplumber
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                # Check if PDF has any pages
                if len(pdf.pages) == 0:
                    return False, f"File {uploaded_file.name} contains no pages."
                
                # Try to access first page to ensure PDF is readable
                first_page = pdf.pages[0]
                _ = first_page.extract_text()  # This will raise an exception if PDF is corrupted
                
        except Exception as pdf_error:
            return False, f"File {uploaded_file.name} appears to be corrupted or unreadable: {str(pdf_error)}"
        finally:
            uploaded_file.seek(0)  # Reset file pointer
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Error validating file {uploaded_file.name}: {str(e)}")
        return False, f"Unexpected error validating {uploaded_file.name}: {str(e)}"

# Main execution for Streamlit multipage
if __name__ == "__main__":
    show_upload_page()
