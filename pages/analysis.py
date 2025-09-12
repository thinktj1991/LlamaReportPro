import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_visualizer import DataVisualizer
from utils.table_extractor import TableExtractor
from utils.state import init_state, init_processors
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_analysis_page():
    st.header("📊 数据分析")
    st.markdown("探索和分析从您的文档中提取的内容")
    
    # Initialize session state safely
    init_state()
    
    if not st.session_state.processed_documents:
        st.warning("尚未处理任何文档。请先在“上传与处理”页面上传文档。")
        return
    
    # Initialize processors including visualizer
    if not init_processors():
        st.error("初始化分析组件失败")
        return
    
    # Sidebar for analysis options
    st.sidebar.subheader("分析选项")
    analysis_type = st.sidebar.selectbox(
        "选择分析类型：",
        ["文档概览", "表格分析", "财务指标", "内容浏览器"]
    )
    
    # Main analysis content
    if analysis_type == "文档概览":
        show_document_overview()
    elif analysis_type == "表格分析":
        show_table_analysis()
    elif analysis_type == "财务指标":
        show_financial_metrics()
    elif analysis_type == "内容浏览器":
        show_content_explorer()

def show_document_overview():
    """
    Show overview of processed documents
    """
    st.subheader("📈 文档处理概览")
    
    # Create overview chart
    try:
        overview_fig = st.session_state.visualizer.create_document_overview_chart(
            st.session_state.processed_documents
        )
        st.plotly_chart(overview_fig, use_container_width=True)
    except Exception as e:
        st.error(f"创建概览图表错误：{str(e)}")
    
    # Document details table
    st.subheader("📋 文档详情")
    
    doc_data = []
    for doc_name, doc_info in st.session_state.processed_documents.items():
        company_info = doc_info.get('company_info', {})
        
        doc_data.append({
            '文档': doc_name,
            '公司': company_info.get('company_name', '未知'),
            '年份': company_info.get('year', '未知'),
            '页数': doc_info.get('page_count', 0),
            '文本长度': f"{doc_info.get('total_text_length', 0):,} 字符",
            '表格数': len(st.session_state.extracted_tables.get(doc_name, []))
        })
    
    df = pd.DataFrame(doc_data)
    st.dataframe(df, use_container_width=True)
    
    # Processing statistics
    show_processing_statistics()

def show_table_analysis():
    """
    Show detailed table analysis
    """
    st.subheader("🔍 Table Extraction Analysis")
    
    if not st.session_state.extracted_tables:
        st.warning("No tables extracted yet.")
        return
    
    # Table distribution chart
    try:
        table_fig = st.session_state.visualizer.create_table_distribution_chart(
            st.session_state.extracted_tables
        )
        st.plotly_chart(table_fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating table distribution chart: {str(e)}")
    
    # Table filtering options
    st.subheader("🔧 Table Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_doc = st.selectbox(
            "Select Document:",
            ["All Documents"] + list(st.session_state.extracted_tables.keys())
        )
    
    with col2:
        show_financial_only = st.checkbox("Financial Tables Only", value=False)
    
    with col3:
        min_importance = st.slider("Minimum Importance Score", 0.0, 1.0, 0.3, 0.1)
    
    # Filter and display tables
    filtered_tables = filter_tables(selected_doc, show_financial_only, min_importance)
    
    if filtered_tables:
        st.subheader(f"📊 Filtered Tables ({len(filtered_tables)} found)")
        
        for i, table in enumerate(filtered_tables):
            with st.expander(f"Table {i+1}: {table['table_id']} (Score: {table['importance_score']:.2f})"):
                show_table_details(table)
    else:
        st.info("No tables match the current filters.")

def show_financial_metrics():
    """
    Show financial metrics analysis
    """
    st.subheader("💰 Financial Metrics Analysis")
    
    # Ensure processors are initialized
    if not init_processors():
        st.error("Failed to initialize table extractor")
        return
    
    # Get important financial tables
    important_tables = st.session_state.table_extractor.get_important_tables(
        st.session_state.extracted_tables, min_importance=0.4
    )
    
    financial_tables = [table for table in important_tables if table.get('is_financial', False)]
    
    if not financial_tables:
        st.warning("No financial tables found with sufficient importance score.")
        return
    
    st.info(f"Found {len(financial_tables)} important financial tables")
    
    # Create consolidated table
    consolidated_table = st.session_state.table_extractor.create_consolidated_table(financial_tables)
    
    if consolidated_table is not None and not consolidated_table.empty:
        # Financial metrics visualization
        try:
            financial_fig = st.session_state.visualizer.create_financial_metrics_chart(consolidated_table)
            st.plotly_chart(financial_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating financial metrics chart: {str(e)}")
        
        # Consolidated table display
        st.subheader("📋 Consolidated Financial Data")
        
        # Table filtering
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.multiselect(
                "Filter by Source Document:",
                options=consolidated_table['source_document'].unique() if 'source_document' in consolidated_table.columns else [],
                default=consolidated_table['source_document'].unique() if 'source_document' in consolidated_table.columns else []
            )
        
        with col2:
            max_rows = st.number_input("Max rows to display:", min_value=10, max_value=1000, value=100)
        
        # Apply filters
        display_table = consolidated_table.copy()
        if source_filter and 'source_document' in display_table.columns:
            display_table = display_table[display_table['source_document'].isin(source_filter)]
        
        display_table = display_table.head(max_rows)
        
        st.dataframe(display_table, use_container_width=True, height=400)
        
        # Download option
        csv = display_table.to_csv(index=False)
        st.download_button(
            label="📥 Download Consolidated Data as CSV",
            data=csv,
            file_name="financial_data_consolidated.csv",
            mime="text/csv"
        )
    else:
        st.warning("Unable to create consolidated financial data table.")

def show_content_explorer():
    """
    Show content exploration interface
    """
    st.subheader("🔍 Content Explorer")
    
    # Document selector
    selected_doc = st.selectbox(
        "Select Document to Explore:",
        list(st.session_state.processed_documents.keys())
    )
    
    if not selected_doc:
        return
    
    doc_data = st.session_state.processed_documents[selected_doc]
    
    # Exploration tabs
    tab1, tab2, tab3 = st.tabs(["📄 Text Content", "📊 Tables", "📈 Statistics"])
    
    with tab1:
        show_text_content(doc_data)
    
    with tab2:
        show_document_tables(selected_doc)
    
    with tab3:
        show_document_statistics(doc_data)

def show_text_content(doc_data):
    """
    Show text content from document
    """
    st.subheader("📝 Text Content")
    
    if 'documents' in doc_data:
        # Page selector
        page_num = st.selectbox(
            "Select Page:",
            range(1, len(doc_data['documents']) + 1),
            format_func=lambda x: f"Page {x}"
        )
        
        if page_num and page_num <= len(doc_data['documents']):
            page_content = doc_data['documents'][page_num - 1].text
            
            # Text search
            search_term = st.text_input("Search in text:", placeholder="Enter search term...")
            
            if search_term:
                # Highlight search terms
                import re
                highlighted = re.sub(
                    f'({re.escape(search_term)})',
                    r'**\1**',
                    page_content,
                    flags=re.IGNORECASE
                )
                st.markdown(highlighted)
            else:
                st.text_area("Page Content:", page_content, height=400)

def show_document_tables(doc_name):
    """
    Show tables from a specific document
    """
    tables = st.session_state.extracted_tables.get(doc_name, [])
    
    if not tables:
        st.info("No tables found in this document.")
        return
    
    # Table selector
    table_options = [f"{table['table_id']} (Page {table['page_number']})" for table in tables]
    selected_table_idx = st.selectbox(
        "Select Table:",
        range(len(tables)),
        format_func=lambda x: table_options[x]
    )
    
    if selected_table_idx is not None:
        table = tables[selected_table_idx]
        show_table_details(table)

def show_table_details(table):
    """
    Show detailed information about a table
    """
    # Table metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", table['rows'])
    with col2:
        st.metric("Columns", table['columns'])
    with col3:
        st.metric("Importance Score", f"{table['importance_score']:.2f}")
    
    # Table properties
    properties = []
    if table['is_financial']:
        properties.append("💰 Financial Data")
    
    if properties:
        st.write("**Properties:** " + ", ".join(properties))
    
    st.write(f"**Summary:** {table['summary']}")
    
    # Display table data
    df = table['dataframe']
    st.dataframe(df, use_container_width=True)
    
    # Table statistics
    if not df.empty:
        st.write("**Table Statistics:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Types:**")
            dtype_counts = df.dtypes.value_counts()
            for dtype, count in dtype_counts.items():
                st.write(f"• {dtype}: {count} columns")
        
        with col2:
            st.write("**Data Completeness:**")
            completeness = (df.notna().sum() / len(df) * 100).round(1)
            for col, pct in completeness.head(5).items():
                st.write(f"• {col}: {pct}%")

def show_document_statistics(doc_data):
    """
    Show detailed statistics for a document
    """
    st.subheader("📊 Document Statistics")
    
    # Basic stats
    stats = {
        'Total Pages': doc_data.get('page_count', 0),
        'Total Characters': doc_data.get('total_text_length', 0),
        'Average Characters per Page': doc_data.get('total_text_length', 0) / max(doc_data.get('page_count', 1), 1)
    }
    
    col1, col2, col3 = st.columns(3)
    metrics = list(stats.items())
    
    for i, (label, value) in enumerate(metrics):
        with [col1, col2, col3][i]:
            if isinstance(value, float):
                st.metric(label, f"{value:,.0f}")
            else:
                st.metric(label, f"{value:,}")
    
    # Content analysis
    if 'detailed_content' in doc_data:
        pages_data = doc_data['detailed_content']['pages']
        
        # Page-by-page analysis
        page_stats = []
        for page in pages_data:
            page_stats.append({
                'Page': page['page_number'],
                'Text Length': len(page['text']),
                'Tables': len(page['tables']),
                'Images': page['images']
            })
        
        if page_stats:
            df_stats = pd.DataFrame(page_stats)
            
            # Create page statistics chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_stats['Page'],
                y=df_stats['Text Length'],
                mode='lines+markers',
                name='Text Length',
                line=dict(color='blue')
            ))
            
            fig.update_layout(
                title="Text Length by Page",
                xaxis_title="Page Number",
                yaxis_title="Characters",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show page statistics table
            st.subheader("📋 Page-by-Page Statistics")
            st.dataframe(df_stats, use_container_width=True)

# Main execution for Streamlit multipage
if __name__ == "__main__":
    show_analysis_page()

def show_processing_statistics():
    """
    Show overall processing statistics
    """
    st.subheader("⚡ Processing Statistics")
    
    # Calculate overall stats
    total_pages = sum(doc.get('page_count', 0) for doc in st.session_state.processed_documents.values())
    total_tables = sum(len(tables) for tables in st.session_state.extracted_tables.values())
    financial_tables = sum(
        sum(1 for table in tables if table.get('is_financial', False))
        for tables in st.session_state.extracted_tables.values()
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pages", total_pages)
    with col2:
        st.metric("Total Tables", total_tables)
    with col3:
        st.metric("Financial Tables", financial_tables)
    with col4:
        financial_pct = (financial_tables / max(total_tables, 1)) * 100
        st.metric("Financial %", f"{financial_pct:.1f}%")

def filter_tables(selected_doc, show_financial_only, min_importance):
    """
    Filter tables based on criteria
    """
    filtered_tables = []
    
    # Get tables from selected document or all documents
    if selected_doc == "All Documents":
        all_tables = [table for tables in st.session_state.extracted_tables.values() for table in tables]
    else:
        all_tables = st.session_state.extracted_tables.get(selected_doc, [])
    
    # Apply filters
    for table in all_tables:
        # Financial filter
        if show_financial_only and not table.get('is_financial', False):
            continue
        
        # Importance filter
        if table.get('importance_score', 0) < min_importance:
            continue
        
        filtered_tables.append(table)
    
    # Sort by importance score
    filtered_tables.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
    
    return filtered_tables
