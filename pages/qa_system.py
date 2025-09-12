import streamlit as st
import os
import json
import pandas as pd
from utils.rag_system import RAGSystem
from utils.data_visualizer import DataVisualizer
from utils.state import init_state, init_processors
import logging

# Configure logging
logger = logging.getLogger(__name__)

def show_qa_page():
    # Enhanced header with AI capabilities showcase
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2>🤖 AI智能问答助手</h2>
        <p>使用先进的RAG技术，对您的年报文档进行智能问答和深度分析</p>
        <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>🎆 AI能力:</strong> 中文问答 • 上下文理解 • 多文档搜索 • 深度分析
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state safely
    init_state()
    
    # Enhanced empty state checks
    if not st.session_state.processed_documents:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 12px; border: 2px dashed #dee2e6;">
            <h3 style="color: #6c757d;">📁 需要先处理文档</h3>
            <p style="color: #6c757d; font-size: 1.1rem;">请先上传并处理您的PDF文档，然后才能使用AI问答功能</p>
            <div style="margin-top: 2rem;">
                <button style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 2rem; border-radius: 25px; border: none; cursor: pointer;">
                    🚀 去上传文档
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if not st.session_state.rag_index:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffeaa7;">
            <h3 style="color: #856404;">🔍 智能索引正在构建中</h3>
            <p style="color: #856404;">系统正在对您的文档进行智能分析，请稍后刷新页面</p>
            <div style="margin-top: 1rem;">
                <div style="width: 100%; background: #f0f0f0; border-radius: 10px; height: 10px;">
                    <div style="width: 60%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Initialize processors including RAG system and visualizer
    if not init_processors():
        st.error("初始化问答系统组件失败")
        return
    
    # Enhanced API key check
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "default_key":
        st.markdown("""
        <div style="background: #f8d7da; color: #721c24; padding: 2rem; border-radius: 12px; border-left: 4px solid #f5c6cb; text-align: center;">
            <h3 style="margin: 0 0 1rem 0;">🔑 需要配置API密钥</h3>
            <p style="margin: 0;">请联系管理员配置OpenAI API密钥后再使用AI问答功能</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # System status
    show_system_status()
    
    # Question interface
    show_question_interface()
    
    # Query history
    show_query_history()
    
    # Example questions
    show_example_questions()

def show_system_status():
    """
    Display enhanced RAG system status
    """
    try:
        # Get index statistics
        index_stats = st.session_state.rag_system.get_index_stats()
        
        # Enhanced system status display
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
            <h4 style="margin: 0 0 1rem 0; color: #495057;">🔍 AI系统状态监控</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Status metrics with enhanced styling
        col1, col2, col3, col4 = st.columns(4)
        
        # Index status
        with col1:
            status = index_stats.get('status', '未知')
            status_color = "#28a745" if status == "Active" else "#dc3545"
            st.markdown("""
            <div style="background: {}; padding: 1rem; border-radius: 8px; color: white; text-align: center;">
                <h3 style="margin: 0; font-size: 1.2rem;">{}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📊 索引状态</p>
            </div>
            """.format(status_color, status), unsafe_allow_html=True)
        
        # Document count
        with col2:
            doc_count = index_stats.get('total_documents', 0)
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1rem; border-radius: 8px; color: white; text-align: center;">
                <h3 style="margin: 0; font-size: 1.5rem;">{}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📄 索引文档</p>
            </div>
            """.format(doc_count), unsafe_allow_html=True)
        
        # Query engine status
        with col3:
            has_engine = index_stats.get('has_query_engine', False)
            engine_color = "#28a745" if has_engine else "#dc3545"
            engine_text = "✅ 就绪" if has_engine else "❌ 未就绪"
            st.markdown("""
            <div style="background: {}; padding: 1rem; border-radius: 8px; color: white; text-align: center;">
                <h3 style="margin: 0; font-size: 1.2rem;">{}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">🤖 查询引擎</p>
            </div>
            """.format(engine_color, engine_text), unsafe_allow_html=True)
        
        # Document types or additional info
        with col4:
            doc_types = index_stats.get('document_types', {})
            total_types = len(doc_types) if doc_types else 0
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 1rem; border-radius: 8px; color: white; text-align: center;">
                <h3 style="margin: 0; font-size: 1.5rem;">{}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📂 文档类型</p>
            </div>
            """.format(total_types), unsafe_allow_html=True)
            financial_docs = doc_types.get('table_data', 0)
            st.metric("财务表格", financial_docs)
        
        # Show document types breakdown
        if doc_types:
            st.write("**索引中的文档类型：**")
            # Map internal codes to Chinese labels
            doc_type_labels = {
                'table_data': '财务表格',
                'text_content': '文本内容',
                'pdf_content': 'PDF内容'
            }
            for doc_type, count in doc_types.items():
                chinese_label = doc_type_labels.get(doc_type, doc_type)
                st.write(f"• {chinese_label}: {count}")
    
    except Exception as e:
        st.error(f"获取系统状态错误：{str(e)}")

def show_question_interface():
    """
    Enhanced question and answer interface
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">💬 智能问答交互</h3>
        <p style="margin: 0; color: #6c757d;">在下方输入您的问题，AI会基于您的文档内容提供准确的答案</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced query context options
    with st.expander("⚙️ 高级查询选项", expanded=False):
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <strong>🎯 查询精准度提升:</strong> 使用下方选项让AI更精准地理解您的问题
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏢 公司筛选**")
            company_data = st.session_state.get('company_data', {})
            company_options = ["所有公司"] + list(company_data.keys()) if company_data else ["所有公司"]
            company_filter = st.selectbox(
                "聚焦特定公司：",
                company_options,
                help="选择特定公司可以获得更精准的答案"
            )
        
        with col2:
            st.markdown("**📂 数据类型**")
            doc_type_filter = st.selectbox(
                "限制数据源：",
                ["所有类型", "财务表格", "文本内容"],
                help="选择数据源类型可以提高相关性"
            )
        
        with col3:
            st.markdown("**📅 时间范围**")
            year_filter = st.text_input(
                "指定年份：",
                placeholder="例: 2023",
                help="输入年份可以获得该年份的具体数据"
            )
    
    # Enhanced question input interface
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">🎯 输入您的问题</h4>
        <p style="margin: 0 0 1rem 0; color: #6c757d; font-size: 0.9rem;">您可以用中文或英文提问，支持复杂的多层次问题</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for temp question from examples
    initial_question = ""
    if hasattr(st.session_state, 'temp_question'):
        initial_question = st.session_state.temp_question
        del st.session_state.temp_question
    
    # Question input with enhanced styling
    question = st.text_area(
        "请输入您的问题：",
        value=initial_question,
        placeholder="例如：\n• 公司在最新年报中的总收入是多少？\n• 主要的财务指标表现如何？\n• 有哪些风险因素需要关注？\n• What are the key business segments mentioned in the report?",
        height=120,
        help="您可以问关于财务数据、公司表现、或文档中任何内容的具体问题"
    )
    
    # Enhanced action buttons
    button_col1, button_col2, button_col3 = st.columns([2, 1, 1])
    
    with button_col2:
        ask_button = st.button(
            "🎆 发送问题", 
            type="primary", 
            use_container_width=True,
            help="点击发送问题给AI助手"
        )
    
    with button_col3:
        clear_button = st.button(
            "🗑️ 清空", 
            use_container_width=True,
            help="清除当前输入的问题"
        )
    
    # Handle button actions
    if clear_button:
        st.rerun()
    
    if ask_button and question.strip():
        ask_question(question, company_filter, doc_type_filter, year_filter)
    elif ask_button:
        st.markdown("""
        <div style="background: #fff3cd; color: #856404; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffeaa7;">
            <strong>⚠️ 请输入问题</strong><br>
            请在上方文本框中输入您想要咨询的问题
        </div>
        """, unsafe_allow_html=True)

def ask_question(question, company_filter, doc_type_filter, year_filter):
    """
    Process a question through the RAG system
    """
    try:
        # Prepare context filter
        context_filter = {}
        
        if company_filter != "所有公司":
            context_filter['company'] = company_filter
        
        if doc_type_filter != "所有类型":
            # Map Chinese UI labels to internal codes
            if doc_type_filter == "财务表格":
                context_filter['document_type'] = 'table_data'
            elif doc_type_filter == "文本内容":
                context_filter['document_type'] = 'text_content'
        
        if year_filter.strip():
            context_filter['year'] = year_filter.strip()
        
        # Show processing status
        with st.spinner("🔍 Searching documents and generating answer..."):
            # Query the RAG system
            result = st.session_state.rag_system.query(question, context_filter)
        
        # Display results
        display_answer_results(question, result)
        
        # Store in query history
        store_query_in_history(question, result, context_filter)
    
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        st.error(f"Error processing question: {str(e)}")

def display_answer_results(question, result):
    """
    Display the answer and sources
    """
    st.subheader("💡 Answer")
    
    if result.get('error', False):
        st.error(f"Error: {result['answer']}")
        return
    
    # Display the answer
    st.markdown(result['answer'])
    
    # Display sources
    sources = result.get('sources', [])
    if sources:
        st.subheader("📚 Sources")
        
        # Create tabs for different source views
        tab1, tab2 = st.tabs(["Source Details", "Source Visualization"])
        
        with tab1:
            for i, source in enumerate(sources):
                with st.expander(f"Source {i+1} (Relevance: {source.get('score', 0):.3f})"):
                    # Source metadata
                    metadata = source.get('metadata', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Document:** {metadata.get('source_file', 'Unknown')}")
                        st.write(f"**Type:** {metadata.get('document_type', 'Unknown')}")
                    
                    with col2:
                        if 'page_number' in metadata:
                            st.write(f"**Page:** {metadata['page_number']}")
                        if 'table_id' in metadata:
                            st.write(f"**Table ID:** {metadata['table_id']}")
                    
                    # Source content preview
                    st.write("**Content Preview:**")
                    st.text(source.get('content_preview', 'No preview available'))
        
        with tab2:
            # Create visualization of sources
            try:
                source_fig = st.session_state.visualizer.create_rag_response_visualization(sources)
                st.plotly_chart(source_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating source visualization: {str(e)}")
    
    # Related content suggestions
    show_related_content(question)

def show_related_content(question):
    """
    Show related content based on the question
    """
    try:
        with st.expander("🔗 Related Content", expanded=False):
            similar_content = st.session_state.rag_system.get_similar_content(question, top_k=3)
            
            if similar_content:
                for i, content in enumerate(similar_content):
                    st.write(f"**Related {i+1}:**")
                    metadata = content.get('metadata', {})
                    st.write(f"From: {metadata.get('source_file', 'Unknown')} (Score: {content.get('score', 0):.3f})")
                    st.write(content.get('text', '')[:200] + "...")
                    st.divider()
            else:
                st.info("No related content found.")
    
    except Exception as e:
        logger.error(f"Error getting related content: {str(e)}")

def show_query_history():
    """
    Display enhanced query history
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #495057;">📜 查询历史记录</h4>
        <p style="margin: 0; color: #6c757d;">查看您之前的提问和回答，方便追踪分析进度</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if st.session_state.query_history:
        
        # Enhanced history display with management buttons
        history_col1, history_col2 = st.columns([3, 1])
        
        with history_col2:
            if st.button("🗑️ 清空历史", use_container_width=True, help="清除所有查询历史"):
                st.session_state.query_history = []
                st.success("历史记录已清空！")
                st.rerun()
        
        with history_col1:
            st.write(f"📊 共有 **{len(st.session_state.query_history)}** 条查询记录")
        
        # Show recent queries with enhanced styling
        recent_queries = list(reversed(st.session_state.query_history[-5:]))
        
        for i, query_record in enumerate(recent_queries):
            query_num = len(st.session_state.query_history) - i
            question_preview = query_record['question'][:60] + "..." if len(query_record['question']) > 60 else query_record['question']
            
            # Enhanced query card
            status_icon = "✅" if not query_record.get('error', False) else "❌"
            with st.expander(
                f"{status_icon} 问题 {query_num}: {question_preview}",
                expanded=i == 0  # Expand first (most recent) query
            ):
                # Query details with safe formatting
                st.markdown("""
                <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea;">
                    <strong>💬 问题:</strong>
                </div>
                """, unsafe_allow_html=True)
                st.write(query_record['question'])
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                answer_preview = query_record['answer'][:400] + "..." if len(query_record['answer']) > 400 else query_record['answer']
                answer_color = "#28a745" if not query_record.get('error', False) else "#dc3545"
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid {answer_color};">
                    <strong>🤖 回答:</strong>
                </div>
                """, unsafe_allow_html=True)
                st.write(answer_preview)
                
                # Query metadata
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                
                with meta_col1:
                    if query_record.get('context_filter'):
                        st.caption(f"🔍 筛选器: {query_record['context_filter']}")
                
                with meta_col2:
                    sources_count = query_record.get('sources_count', 0)
                    st.caption(f"📁 数据源: {sources_count} 个")
                
                with meta_col3:
                    st.caption(f"⏰ 时间: {query_record['timestamp']}")
                
                # Action buttons
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button(f"🔄 再次提问", key=f"reask_{i}", use_container_width=True):
                        st.session_state.temp_question = query_record['question']
                        st.rerun()
                
                with btn_col2:
                    if st.button(f"📎 复制问题", key=f"copy_{i}", use_container_width=True):
                        st.code(query_record['question'], language=None)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #e9ecef; border-radius: 8px; border: 2px dashed #ced4da;">
            <h4 style="color: #6c757d;">📝 还没有查询历史</h4>
            <p style="color: #6c757d;">您的提问和回答将会显示在这里</p>
        </div>
        """, unsafe_allow_html=True)

def show_example_questions():
    """
    Show enhanced example questions with categories
    """
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0;">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">💡 示例问题指引</h3>
        <p style="margin: 0; color: #6c757d;">以下是一些常见问题示例，点击即可直接使用</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced example questions with better categorization  
    example_categories = {
        "💰 财务数据分析": {
            "icon": "💰",
            "color": "#e8f5e8",
            "questions": [
                "公司在最新财年的总收入是多少？",
                "净利润的同比增长率是多少？",
                "主要的收入来源有哪些？",
                "What were the total operating expenses?",
                "运营成本的变化趋势如何？"
            ]
        },
        "🏢 公司运营表现": {
            "icon": "🏢",
            "color": "#e3f2fd",
            "questions": [
                "公司的主要业务和竞争优势是什么？",
                "What growth strategies does the company discuss?",
                "市场趋势对业务的影响如何？",
                "公司在行业中的地位和竞争力如何？",
                "管理层对未来发展有什么规划？"
            ]
        },
        "⚠️ 风险与合规": {
            "icon": "⚠️",
            "color": "#fff3cd",
            "questions": [
                "报告中提到的主要风险因素有哪些？",
                "How does the company plan to mitigate these risks?",
                "市场竞争和法律环境如何影响业务？",
                "What regulatory changes might impact the business?",
                "ESG相关的风险和机遇有哪些？"
            ]
        },
        "🔮 未来展望": {
            "icon": "🔮",
            "color": "#f3e5f5",
            "questions": [
                "公司对未来的战略规划和投资计划是什么？",
                "What investments is the company making?",
                "预期的挑战和机遇有哪些？",
                "What guidance did management provide?",
                "未来增长的主要驱动力是什么？"
            ]
        }
    }
    
    # Display example questions in enhanced card format
    for category_name, category_data in example_categories.items():
        with st.expander(
            f"{category_data['icon']} {category_name} ({len(category_data['questions'])} 个示例)",
            expanded=False
        ):
            # Category description
            st.markdown(f"""
            <div style="background: {category_data['color']}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <strong>{category_data['icon']} {category_name}相关问题</strong><br>
                <small>点击下方任一问题即可直接提问</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Display questions as clickable buttons
            for i, question in enumerate(category_data['questions']):
                question_key = f"example_{category_name}_{i}"
                if st.button(
                    f"💬 {question}",
                    key=question_key,
                    use_container_width=True,
                    help="点击直接使用这个示例问题"
                ):
                    # Set the example question for use in the interface
                    st.session_state.temp_question = question
                    st.rerun()
            
            st.markdown("<hr style='margin: 1rem 0; border: none; height: 1px; background: #dee2e6;'>", unsafe_allow_html=True)
    
    # Example question selection handled in show_question_interface()

def store_query_in_history(question, result, context_filter):
    """
    Store query in session history
    """
    try:
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        query_record = {
            'question': question,
            'answer': result.get('answer', 'No answer'),
            'context_filter': context_filter,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources_count': len(result.get('sources', [])),
            'error': result.get('error', False)
        }
        
        st.session_state.query_history.append(query_record)
        
        # Keep only last 50 queries
        if len(st.session_state.query_history) > 50:
            st.session_state.query_history = st.session_state.query_history[-50:]
    
    except Exception as e:
        logger.error(f"Error storing query in history: {str(e)}")

# Additional helper functions
def clear_query_history():
    """
    Clear query history
    """
    if st.button("🗑️ Clear History"):
        st.session_state.query_history = []
        st.success("Query history cleared!")
        st.rerun()

def export_query_history():
    """
    Export query history as JSON
    """
    if 'query_history' in st.session_state and st.session_state.query_history:
        history_json = json.dumps(st.session_state.query_history, indent=2)
        st.download_button(
            label="📥 Download Query History",
            data=history_json,
            file_name="query_history.json",
            mime="application/json"
        )

# Main execution for Streamlit multipage
if __name__ == "__main__":
    show_qa_page()
