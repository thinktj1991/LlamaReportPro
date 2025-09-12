import streamlit as st
import os
from utils.pdf_processor import PDFProcessor
from utils.table_extractor import TableExtractor
from utils.rag_system import RAGSystem
from utils.company_comparator import CompanyComparator
from utils.enhanced_integration import get_system_integrator
from utils.state import init_state, init_processors, get_processing_stats, clear_all_data
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_upload_page():
    # Enhanced header with progress indication
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>📁 文档上传与处理</h2>
        <p>上传您的PDF年报文档，让AI帮您进行智能分析</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>✨ 支持功能:</strong> PDF文本提取 • 财务表格识别 • 公司信息提取 • 智能问答索引
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state safely
    init_state()
    
    # Initialize processors
    if not init_processors():
        st.error("初始化处理组件失败")
        return
    
    # System status and enhancement toggle
    show_system_status()
    
    # Enhanced file upload section
    st.subheader("📤 选择您的文档")
    
    # Upload tips
    with st.expander("💡 上传提示", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **支持的文档类型:**
            - ✅ 年度报告 (Annual Reports)
            - ✅ 财务报告 (Financial Statements) 
            - ✅ 公司报告 (Company Reports)
            - ✅ 中英文PDF文档
            """)
        with col2:
            st.markdown("""
            **最佳实践:**
            - ✨ 文件大小: 小于200MB
            - ✨ 文档质量: 高清PDF文档
            - ✨ 文档结构: 包含财务表格
            - ✨ 命名规范: 使用有意义的文件名
            """)
    
    # File uploader with enhanced styling
    uploaded_files = st.file_uploader(
        "拖放PDF文件到这里，或点击浏览选择",
        type=['pdf'],
        accept_multiple_files=True,
        help="支持多个文件同时上传，系统会自动进行批量处理"
    )
    
    if uploaded_files:
        # Enhanced file preview section
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745; margin: 1rem 0;">
            <h4 style="margin: 0 0 1rem 0; color: #28a745;">✅ 文件上传成功</h4>
            <p style="margin: 0; color: #6c757d;">已选择 {} 个文件，准备进行智能处理</p>
        </div>
        """.format(len(uploaded_files)), unsafe_allow_html=True)
        
        # File details with enhanced UI
        with st.expander(f"📊 查看文件详情 ({len(uploaded_files)} 个文件)", expanded=len(uploaded_files) <= 3):
            for i, file in enumerate(uploaded_files, 1):
                col1, col2, col3 = st.columns([0.5, 3, 1.5])
                with col1:
                    st.markdown(f"**{i}.**")
                with col2:
                    st.markdown(f"**{file.name}**")
                with col3:
                    file_size = file.size / (1024*1024)  # Convert to MB
                    if file_size < 1:
                        st.markdown(f"📄 {file.size:,} 字节")
                    else:
                        st.markdown(f"📄 {file_size:.1f} MB")
        
        # Enhanced action section
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: white;">🚀 准备开始处理</h4>
                <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">点击下方按钮开始智能分析</p>
            </div>
            """, unsafe_allow_html=True)
            
            process_button = st.button(
                "🎆 开始智能分析", 
                type="primary", 
                use_container_width=True,
                help="点击开始对所有上传的PDF文档进行处理"
            )
        
        if process_button:
            process_uploaded_files(uploaded_files)
    
    # Display processing status
    show_processing_status()
    
    # Document management
    show_document_management()

def process_uploaded_files(uploaded_files):
    """
    Process all uploaded files with enhanced user experience
    """
    total_files = len(uploaded_files)
    
    # Enhanced processing header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2rem; border-radius: 12px; color: white; text-align: center; margin: 2rem 0;">
        <h2>🔧 正在处理您的文档</h2>
        <p>请耐心等待，我们正在使用AI技术分析您的文档...</p>
        <p><strong>处理步骤:</strong> 文件验证 → 内容提取 → 表格识别 → 智能索引</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress tracking
    progress_col1, progress_col2 = st.columns([3, 1])
    with progress_col1:
        progress_bar = st.progress(0)
    with progress_col2:
        progress_text = st.empty()
    
    status_text = st.empty()
    
    # Processing stages indicator
    stages_container = st.container()
    with stages_container:
        stage_col1, stage_col2, stage_col3, stage_col4 = st.columns(4)
        stage_indicators = [stage_col1.empty(), stage_col2.empty(), stage_col3.empty(), stage_col4.empty()]
        
        # Initialize stage indicators
        stage_names = ["🔍 文件验证", "📄 内容提取", "📊 表格识别", "🤖 智能索引"]
        for i, indicator in enumerate(stage_indicators):
            indicator.info(stage_names[i])
    
    # Track validation and processing results
    validation_results = []
    processing_results = []
    valid_files = []
    
    try:
        # Step 1: Validate all files first
        stage_indicators[0].success("🔍 正在验证...")
        status_text.info("🔍 正在验证上传的文件...")
        progress_text.text("1/4")
        
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
        
        # Update stage indicators
        stage_indicators[0].success("✅ 验证完成")
        stage_indicators[1].warning("📄 正在处理...")
        progress_text.text("2/4")
        
        # Step 2: Process only valid files
        status_text.success(f"✅ 验证完成！正在处理 {len(valid_files)} 个有效文件")
        
        for i, uploaded_file in enumerate(valid_files):
            try:
                current_progress = (i + 1) / len(valid_files) * 0.6 + 0.1  # 10% to 70%
                progress_bar.progress(current_progress)
                progress_text.text(f"2/4 ({i+1}/{len(valid_files)})")
                
                status_text.info(f"📄 正在处理: {uploaded_file.name}")
                
                with st.spinner(f"🚀 正在处理 {uploaded_file.name}..."):
                    # Process PDF with enhanced or legacy processor
                    integrator = get_system_integrator()
                    processed_data = integrator.process_uploaded_file(uploaded_file)
                    
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
                    
                    # Show progress for current file
                    st.success(f"✅ {uploaded_file.name} 处理完成")
                    
            except Exception as file_error:
                error_msg = f"Error processing {uploaded_file.name}: {str(file_error)}"
                logger.error(error_msg)
                st.error(f"❌ {uploaded_file.name} 处理失败: {str(file_error)}")
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

def show_system_status():
    """
    Display system status and enhancement controls
    """
    with st.expander("🚀 系统增强功能状态", expanded=False):
        integrator = get_system_integrator()
        system_status = integrator.get_system_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔧 当前配置:**")
            
            # Enhanced mode status
            if system_status['enhanced_mode']:
                st.success("✅ 增强模式：已启用 (LlamaIndex)")
            else:
                st.info("ℹ️ 增强模式：使用基础模式")
            
            # API keys status
            if system_status['environment']['llamaparse_key_available']:
                st.success("🔑 LlamaParse API Key: 可用")
            else:
                st.warning("🔑 LlamaParse API Key: 未设置")
                
            if system_status['environment']['openai_key_available']:
                st.success("🔑 OpenAI API Key: 可用")
            else:
                st.error("🔑 OpenAI API Key: 缺失")
        
        with col2:
            st.markdown("**🎯 可用功能:**")
            
            capabilities = system_status['capabilities']
            
            if capabilities['llamaparse_processing']:
                st.success("📄 LlamaParse高级解析: 可用")
            else:
                st.info("📄 PDF解析: 使用基础模式")
                
            if capabilities['advanced_querying']:
                st.success("🧠 智能查询引擎: 可用")
            else:
                st.info("🧠 查询系统: 使用基础模式")
                
            if capabilities['fallback_available']:
                st.success("🛡️ 备用系统: 就绪")
            else:
                st.warning("🛡️ 备用系统: 不可用")
        
        # Enhancement tips
        if not system_status['enhanced_mode']:
            st.markdown("""
            <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107; margin-top: 1rem;">
                <h5 style="margin: 0 0 0.5rem 0; color: #856404;">💡 启用增强功能提示</h5>
                <p style="margin: 0; color: #856404;">
                要启用LlamaIndex增强功能，请设置环境变量 <code>USE_ENHANCED_LLAMAINDEX=true</code> 和 <code>LLAMA_CLOUD_API_KEY</code>
                </p>
            </div>
            """, unsafe_allow_html=True)

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
