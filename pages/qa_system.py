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
    st.header("🤖 问答系统")
    st.markdown("使用AI智能搜索对您的年报提问")
    
    # Initialize session state safely
    init_state()
    
    # Check if system is ready
    if not st.session_state.processed_documents:
        st.warning("尚未处理任何文档。请先在“上传与处理”页面上传文档。")
        return
    
    if not st.session_state.rag_index:
        st.warning("搜索索引尚未构建。请重新处理您的文档。")
        return
    
    # Initialize processors including RAG system and visualizer
    if not init_processors():
        st.error("初始化问答系统组件失败")
        return
    
    # Check API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "default_key":
        st.error("🔑 OpenAI API密钥未配置。请设置OPENAI_API_KEY环境变量。")
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
    Display RAG system status
    """
    st.subheader("🔍 系统状态")
    
    try:
        # Get index statistics
        index_stats = st.session_state.rag_system.get_index_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("索引状态", index_stats.get('status', '未知'))
        
        with col2:
            st.metric("文档总数", index_stats.get('total_documents', 0))
        
        with col3:
            query_engine_status = "✅ 就绪" if index_stats.get('has_query_engine', False) else "❌ 未就绪"
            st.metric("查询引擎", query_engine_status)
        
        with col4:
            doc_types = index_stats.get('document_types', {})
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
