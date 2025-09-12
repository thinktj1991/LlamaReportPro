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
    # Enhanced header with data insights
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>📊 数据分析中心</h2>
        <p>探索和分析您文档中的关键信息，发现数据背后的洞察</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>🎆 分析能力:</strong> 文档概览 • 表格深度分析 • 财务指标计算 • 内容智能探索
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state safely
    init_state()
    
    # Enhanced empty state with better guidance
    if not st.session_state.processed_documents:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 12px; border: 2px dashed #dee2e6;">
            <h3 style="color: #6c757d;">📁 尚未处理任何文档</h3>
            <p style="color: #6c757d; font-size: 1.1rem;">请先上传PDF文档开始分析之旅</p>
            <div style="margin-top: 2rem;">
                <a href="#" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 2rem; border-radius: 25px; text-decoration: none; display: inline-block;">
                    🚀 去上传文档
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Initialize processors including visualizer
    if not init_processors():
        st.markdown("""
        <div style="background: #f8d7da; color: #721c24; padding: 1rem; border-radius: 8px; border-left: 4px solid #f5c6cb;">
            <strong>⚠️ 系统初始化失败</strong><br>
            无法初始化分析组件，请刷新页面或重新上传文档
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Data overview metrics at the top
    show_data_overview_metrics()
    
    # Enhanced analysis options with modern tabs
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">🎯 选择分析类型</h4>
        <p style="margin: 0; color: #6c757d;">选择下方一种分析模式，深入探索您的数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Modern tab-style analysis selection
    analysis_options = [
        {
            "name": "文档概览",
            "icon": "📄",
            "desc": "查看所有文档的整体状态和统计信息"
        },
        {
            "name": "表格分析",
            "icon": "📊",
            "desc": "深度分析提取的表格数据和结构"
        },
        {
            "name": "财务指标",
            "icon": "💰",
            "desc": "分析财务表格和关键指标趋势"
        },
        {
            "name": "内容浏览器",
            "icon": "🔍",
            "desc": "逐页浏览和搜索文档内容"
        }
    ]
    
    # Create columns for analysis options
    cols = st.columns(len(analysis_options))
    
    selected_analysis = None
    for i, option in enumerate(analysis_options):
        with cols[i]:
            if st.button(
                f"{option['icon']}\n\n**{option['name']}**\n\n{option['desc']}",
                key=f"analysis_{i}",
                use_container_width=True,
                help=option['desc']
            ):
                selected_analysis = option['name']
    
    # Default to first option if none selected
    if 'selected_analysis_type' not in st.session_state:
        st.session_state.selected_analysis_type = analysis_options[0]['name']
    
    if selected_analysis:
        st.session_state.selected_analysis_type = selected_analysis
    
    analysis_type = st.session_state.selected_analysis_type
    
    # Show current selection
    current_option = next(opt for opt in analysis_options if opt['name'] == analysis_type)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
        <strong>{current_option['icon']} 当前分析: {current_option['name']}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Main analysis content
    if analysis_type == "文档概览":
        show_document_overview()
    elif analysis_type == "表格分析":
        show_table_analysis()
    elif analysis_type == "财务指标":
        show_financial_metrics()
    elif analysis_type == "内容浏览器":
        show_content_explorer()

def show_data_overview_metrics():
    """
    Show key data metrics at the top of the page
    """
    # Calculate key metrics
    total_docs = len(st.session_state.processed_documents)
    total_tables = sum(len(tables) for tables in st.session_state.extracted_tables.values())
    financial_tables = sum(
        sum(1 for table in tables if table.get('is_financial', False))
        for tables in st.session_state.extracted_tables.values()
    )
    total_pages = sum(doc.get('page_count', 0) for doc in st.session_state.processed_documents.values())
    
    # Display metrics in enhanced cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;">
            <h3 style="margin: 0; font-size: 2rem;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📄 已处理文档</p>
        </div>
        """.format(total_docs), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;">
            <h3 style="margin: 0; font-size: 2rem;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📊 提取表格</p>
        </div>
        """.format(total_tables), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 1.5rem; border-radius: 12px; color: #333; text-align: center;">
            <h3 style="margin: 0; font-size: 2rem;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">💰 财务表格</p>
        </div>
        """.format(financial_tables), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%); padding: 1.5rem; border-radius: 12px; color: #333; text-align: center;">
            <h3 style="margin: 0; font-size: 2rem;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">📝 总页数</p>
        </div>
        """.format(total_pages), unsafe_allow_html=True)

def show_document_overview():
    """
    Show overview of processed documents
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">📈 文档处理概览</h3>
        <p style="margin: 0; color: #6c757d;">查看所有已处理文档的详细信息和统计数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced overview chart with error handling
    chart_container = st.container()
    with chart_container:
        try:
            with st.spinner("📈 正在生成概览图表..."):
                overview_fig = st.session_state.visualizer.create_document_overview_chart(
                    st.session_state.processed_documents
                )
                st.plotly_chart(overview_fig, use_container_width=True)
        except Exception as e:
            st.markdown("""
            <div style="background: #fff3cd; color: #856404; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffeaa7;">
                <strong>⚠️ 图表生成问题</strong><br>
                无法创建概览图表：{}<br>
                请检查数据格式或刷新页面重试
            </div>
            """.format(str(e)), unsafe_allow_html=True)
    
    # Enhanced document details section
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">📋 文档详情列表</h4>
        <p style="margin: 0 0 1.5rem 0; color: #6c757d;">以下是所有已处理文档的详细信息</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Build enhanced document data
    doc_data = []
    for doc_name, doc_info in st.session_state.processed_documents.items():
        company_info = doc_info.get('company_info', {})
        tables = st.session_state.extracted_tables.get(doc_name, [])
        financial_count = sum(1 for t in tables if t.get('is_financial', False))
        
        doc_data.append({
            '📄 文档名称': doc_name[:50] + '...' if len(doc_name) > 50 else doc_name,
            '🏢 公司': company_info.get('company_name', '未识别'),
            '📅 年份': company_info.get('year', '-'),
            '📝 页数': doc_info.get('page_count', 0),
            '📊 表格数': len(tables),
            '💰 财务表': financial_count,
            '📈 文本量': f"{doc_info.get('total_text_length', 0):,}"
        })
    
    if doc_data:
        df = pd.DataFrame(doc_data)
        
        # Enhanced dataframe display
        st.dataframe(
            df, 
            use_container_width=True,
            height=400,
            column_config={
                '📄 文档名称': st.column_config.TextColumn(width="large"),
                '📈 文本量': st.column_config.TextColumn(width="small")
            }
        )
        
        # Add download option
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 下载文档详情表",
            data=csv_data,
            file_name="document_overview.csv",
            mime="text/csv",
            help="下载所有文档的详细信息为CSV文件"
        )
    else:
        st.info("暂无文档数据")
    
    # Processing statistics
    show_processing_statistics()

def show_table_analysis():
    """
    Show detailed table analysis with enhanced UI
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">🔍 表格深度分析</h3>
        <p style="margin: 0; color: #6c757d;">分析所有提取的表格，识别财务数据和关键信息</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.extracted_tables:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #fff3cd; border-radius: 12px; border: 2px dashed #ffeaa7;">
            <h3 style="color: #856404;">📊 尚未提取表格数据</h3>
            <p style="color: #856404; font-size: 1.1rem;">系统正在处理您的文档，请稍后刷新页面</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Enhanced table distribution visualization
    visualization_container = st.container()
    with visualization_container:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 1rem 0;">
            <h4 style="margin: 0 0 1rem 0; color: #495057;">📉 表格分布情况</h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            with st.spinner("📈 正在生成表格分布图表..."):
                table_fig = st.session_state.visualizer.create_table_distribution_chart(
                    st.session_state.extracted_tables
                )
                st.plotly_chart(table_fig, use_container_width=True)
        except Exception as e:
            st.markdown("""
            <div style="background: #fff3cd; color: #856404; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffeaa7;">
                <strong>⚠️ 可视化生成问题</strong><br>
                无法创建表格分布图：{}<br>
                数据可能还在处理中，请稍后刷新页面
            </div>
            """.format(str(e)), unsafe_allow_html=True)
    
    # Enhanced table filtering section
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">🔧 智能表格筛选器</h4>
        <p style="margin: 0; color: #6c757d;">使用下方的筛选条件找到最重要的表格数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced filtering controls
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        st.markdown("**📄 文档选择**")
        selected_doc = st.selectbox(
            "选择目标文档：",
            ["所有文档"] + list(st.session_state.extracted_tables.keys()),
            help="选择要分析的特定文档，或查看所有文档"
        )
    
    with filter_col2:
        st.markdown("**💰 内容类型**")
        show_financial_only = st.checkbox(
            "仅显示财务表格", 
            value=False,
            help="勾选后只显示被识别为财务相关的表格"
        )
    
    with filter_col3:
        st.markdown("**⭐ 重要性筛选**")
        min_importance = st.slider(
            "最低重要性评分：", 
            0.0, 1.0, 0.3, 0.1,
            help="设置表格重要性的最低阈值，值越高表示表格越重要"
        )
    
    # Filter and display tables
    filtered_tables = filter_tables(selected_doc, show_financial_only, min_importance)
    
    # Enhanced filtered results display
    if filtered_tables:
        # Results header with statistics
        st.markdown("""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 1rem; border-radius: 8px; color: white; margin: 1rem 0;">
            <strong>🎉 筛选结果: 找到 {} 个符合条件的表格</strong>
        </div>
        """.format(len(filtered_tables)), unsafe_allow_html=True)
        
        # Display tables with enhanced styling
        for i, table in enumerate(filtered_tables):
            importance_color = "#28a745" if table['importance_score'] >= 0.7 else "#ffc107" if table['importance_score'] >= 0.4 else "#dc3545"
            importance_icon = "🏆" if table['importance_score'] >= 0.7 else "⭐" if table['importance_score'] >= 0.4 else "🔵"
            financial_badge = "💰 财务" if table.get('is_financial', False) else "📄 一般"
            
            with st.expander(
                f"{importance_icon} 表格 {i+1}: {table['table_id'][:30]}... | 评分: {table['importance_score']:.2f} | {financial_badge}",
                expanded=i < 2  # Auto-expand first 2 tables
            ):
                show_enhanced_table_details(table, i+1)
    else:
        st.markdown("""
        <div style="background: #e9ecef; padding: 2rem; border-radius: 8px; text-align: center; border: 2px dashed #ced4da;">
            <h4 style="color: #6c757d;">🔍 未找到符合条件的表格</h4>
            <p style="color: #6c757d;">请调整筛选条件或稍后再试</p>
        </div>
        """, unsafe_allow_html=True)

def show_enhanced_table_details(table, table_num):
    """
    Show enhanced table details with better formatting
    """
    # Table header with key metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("📏 行数", table['rows'])
    with metric_col2:
        st.metric("📊 列数", table['columns'])
    with metric_col3:
        st.metric("⭐ 重要性", f"{table['importance_score']:.2f}")
    with metric_col4:
        page_info = f"第{table.get('page_number', '?')}页"
        st.metric("📝 位置", page_info)
    
    # Table properties and summary
    properties = []
    if table.get('is_financial', False):
        properties.append("💰 财务数据")
    if table.get('importance_score', 0) >= 0.7:
        properties.append("🏆 高重要性")
    
    if properties:
        st.markdown(f"**标签:** {' • '.join(properties)}")
    
    if table.get('summary'):
        st.markdown(f"**摘要:** {table['summary']}")
    
    # Enhanced table display
    try:
        df = table['dataframe']
        if not df.empty:
            st.markdown("**表格数据:**")
            st.dataframe(df, use_container_width=True, height=300)
            
            # Quick data insights
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                st.markdown("**数据类型分布:**")
                dtype_counts = df.dtypes.value_counts()
                for dtype, count in dtype_counts.items():
                    st.write(f"• {dtype}: {count} 列")
            
            with insights_col2:
                st.markdown("**数据完整性:**")
                completeness = (df.notna().sum() / len(df) * 100).round(1)
                for col, pct in completeness.head(3).items():
                    color = "green" if pct >= 90 else "orange" if pct >= 70 else "red"
                    st.markdown(f"• {col}: <span style='color: {color}'>{pct}%</span>", unsafe_allow_html=True)
        else:
            st.warning("表格数据为空")
    except Exception as e:
        st.error(f"无法显示表格数据: {str(e)}")

def show_financial_metrics():
    """
    Show financial metrics analysis with enhanced UI
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">💰 财务指标分析</h3>
        <p style="margin: 0; color: #6c757d;">分析财务表格数据，计算关键指标和趋势</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            st.error(f"创建财务指标图表错误：{str(e)}")
        
        # Consolidated table display
        st.subheader("📋 综合财务数据")
        
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
        "选择要探索的文档：",
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
    if selected_doc == "所有文档":
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
