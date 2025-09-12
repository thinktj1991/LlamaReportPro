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
    Main question and answer interface
    """
    st.subheader("💬 提问问题")
    
    # Query context options
    with st.expander("🔧 查询选项", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_filter = st.selectbox(
                "聚焦公司：",
                ["所有公司"] + list(st.session_state.company_data.keys()),
                help="筛选回答以聚焦特定公司"
            )
        
        with col2:
            doc_type_filter = st.selectbox(
                "文档类型：",
                ["所有类型", "财务表格", "文本内容"],
                help="按文档类型筛选"
            )
        
        with col3:
            year_filter = st.text_input(
                "年份聚焦：",
                placeholder="例：2023",
                help="如果有的话，聚焦特定年份"
            )
    
    # Question input
    question = st.text_area(
        "Enter your question:",
        placeholder="e.g., What was the company's revenue in the latest annual report?",
        height=100,
        help="Ask specific questions about financial data, company performance, or any content in the documents"
    )
    
    # Ask button
    col1, col2 = st.columns([3, 1])
    with col2:
        ask_button = st.button("🚀 Ask Question", type="primary", use_container_width=True)
    
    if ask_button and question.strip():
        ask_question(question, company_filter, doc_type_filter, year_filter)
    elif ask_button:
        st.warning("Please enter a question first.")

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
    Display query history
    """
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if st.session_state.query_history:
        st.subheader("📋 Query History")
        
        # Show recent queries
        for i, query_record in enumerate(reversed(st.session_state.query_history[-5:])):
            with st.expander(f"Query {len(st.session_state.query_history) - i}: {query_record['question'][:50]}..."):
                st.write(f"**Question:** {query_record['question']}")
                st.write(f"**Answer:** {query_record['answer'][:300]}...")
                
                if query_record.get('context_filter'):
                    st.write(f"**Filters:** {query_record['context_filter']}")
                
                st.write(f"**Asked:** {query_record['timestamp']}")
                
                # Re-ask button
                if st.button(f"Re-ask Question", key=f"reask_{i}"):
                    st.session_state.temp_question = query_record['question']
                    st.rerun()

def show_example_questions():
    """
    Show example questions users can ask
    """
    st.subheader("💡 Example Questions")
    
    example_categories = {
        "📊 Financial Performance": [
            "What was the company's total revenue last year?",
            "How did profit margins change compared to previous year?",
            "What are the main sources of revenue?",
            "What were the total operating expenses?"
        ],
        "📈 Business Analysis": [
            "What are the key business risks mentioned?",
            "What growth strategies does the company discuss?",
            "What market trends are affecting the business?",
            "What are the main competitive advantages?"
        ],
        "💰 Financial Position": [
            "What is the company's total debt?",
            "How much cash does the company have?",
            "What are the major assets?",
            "What is the debt-to-equity ratio?"
        ],
        "🔮 Future Outlook": [
            "What are the company's future plans?",
            "What investments is the company making?",
            "What are the expected challenges ahead?",
            "What guidance did management provide?"
        ]
    }
    
    for category, questions in example_categories.items():
        with st.expander(category):
            for question in questions:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {question}")
                with col2:
                    if st.button("Ask", key=f"example_{hash(question)}"):
                        st.session_state.temp_question = question
                        st.rerun()
    
    # Handle example question selection
    if hasattr(st.session_state, 'temp_question'):
        st.info(f"Selected question: {st.session_state.temp_question}")
        # You could auto-fill the question input here
        del st.session_state.temp_question

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
