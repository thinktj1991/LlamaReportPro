import streamlit as st
import os
from pathlib import Path
from utils.state import init_state, get_processing_stats

# Set page configuration
st.set_page_config(
    page_title="Annual Report Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_state()

def main():
    st.title("📊 Annual Report Analysis System")
    st.markdown("Comprehensive analysis of annual reports using LlamaIndex and AI")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select a page:",
        ["Home", "Upload & Process", "Data Analysis", "Q&A System", "Company Comparison", "Ratio Analysis", "AI Insights", "Data Export"]
    )
    
    # Display selected page
    if page == "Home":
        show_home_page()
    elif page == "Upload & Process":
        from pages.upload import show_upload_page
        show_upload_page()
    elif page == "Data Analysis":
        from pages.analysis import show_analysis_page
        show_analysis_page()
    elif page == "Q&A System":
        from pages.qa_system import show_qa_page
        show_qa_page()
    elif page == "Company Comparison":
        from pages.comparison import show_comparison_page
        show_comparison_page()
    elif page == "Ratio Analysis":
        # Note: This routing is handled by Streamlit's multipage system
        # The pages/ratio_analysis.py file is executed directly
        st.info("Navigating to Ratio Analysis... (handled by Streamlit multipage system)")
    elif page == "AI Insights":
        from pages.insights import show_insights_page
        show_insights_page()
    elif page == "Data Export":
        from pages.export import show_export_page
        show_export_page()

def show_home_page():
    st.header("Welcome to the Annual Report Analysis System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Key Features")
        st.markdown("""
        - **PDF Processing**: Upload and process multiple annual reports
        - **Table Extraction**: Advanced extraction of financial tables
        - **Text Analysis**: Comprehensive content analysis
        - **Q&A System**: RAG-based question answering
        - **Ratio Analysis**: Advanced financial ratio calculations
        - **AI Insights**: Pattern recognition and anomaly detection
        - **Company Comparison**: Side-by-side analysis with benchmarking
        - **Data Export**: Professional reports in CSV, Excel, and PDF formats
        - **Visualization**: Interactive charts and graphs
        """)
    
    with col2:
        st.subheader("🚀 Getting Started")
        st.markdown("""
        1. Navigate to **Upload & Process** to upload PDF files
        2. Use **Data Analysis** to explore extracted content
        3. Try the **Q&A System** for intelligent queries
        4. Analyze ratios in **Ratio Analysis** for detailed financial insights
        5. Compare companies in **Company Comparison** with industry benchmarks
        6. Explore **AI Insights** for automated pattern recognition and risk analysis
        7. Export your analysis in **Data Export** as professional reports
        """)
    
    # System status
    st.subheader("📋 System Status")
    col1, col2, col3, col4 = st.columns(4)
    
    # Get processing stats safely
    stats = get_processing_stats()
    
    with col1:
        st.metric("Processed Documents", stats['documents_count'])
    
    with col2:
        st.metric("Extracted Tables", stats['tables_count'])
    
    with col3:
        rag_status = "Active" if stats['rag_ready'] else "Inactive"
        st.metric("RAG System", rag_status)
    
    with col4:
        st.metric("Companies", stats['companies_count'])
    
    # API Key status
    st.subheader("🔑 Configuration Status")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        st.success("✅ OpenAI API Key configured")
    else:
        st.warning("⚠️ OpenAI API Key not found. Please set OPENAI_API_KEY environment variable.")

if __name__ == "__main__":
    main()
