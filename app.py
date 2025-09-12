import streamlit as st
import os
from pathlib import Path
from utils.state import init_state, get_processing_stats

# Set page configuration
st.set_page_config(
    page_title="年报分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the default Streamlit pages navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_state()

def main():
    st.title("📊 年报分析系统")
    st.markdown("使用LlamaIndex和AI技术进行年报综合分析")
    
    # Sidebar navigation
    st.sidebar.title("导航菜单")
    page = st.sidebar.selectbox(
        "选择页面：",
        ["首页", "上传与处理", "数据分析", "问答系统", "公司对比", "比率分析", "AI洞察", "数据导出"]
    )
    
    # Display selected page
    if page == "首页":
        show_home_page()
    elif page == "上传与处理":
        from pages.upload import show_upload_page
        show_upload_page()
    elif page == "数据分析":
        from pages.analysis import show_analysis_page
        show_analysis_page()
    elif page == "问答系统":
        from pages.qa_system import show_qa_page
        show_qa_page()
    elif page == "公司对比":
        from pages.comparison import show_comparison_page
        show_comparison_page()
    elif page == "比率分析":
        from pages.ratio_analysis import show_ratio_analysis_page
        show_ratio_analysis_page()
    elif page == "AI洞察":
        from pages.insights import show_insights_page
        show_insights_page()
    elif page == "数据导出":
        from pages.export import show_export_page
        show_export_page()

def show_home_page():
    st.header("欢迎使用年报分析系统")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 核心功能")
        st.markdown("""
        - **PDF处理**: 上传和处理多个年度报告
        - **表格提取**: 高级财务表格提取技术
        - **文本分析**: 全面的内容分析
        - **问答系统**: 基于RAG技术的问答系统
        - **比率分析**: 高级财务比率计算
        - **AI洞察**: 模式识别和异常检测
        - **公司对比**: 多公司并排分析和基准测试
        - **数据导出**: 生成CSV、Excel和PDF格式的专业报告
        - **数据可视化**: 交互式图表和图形
        """)
    
    with col2:
        st.subheader("🚀 快速入门")
        st.markdown("""
        1. 访问 **上传与处理** 页面上传PDF文件
        2. 使用 **数据分析** 探索提取的内容
        3. 尝试 **问答系统** 进行智能查询
        4. 在 **比率分析** 中获取详细的财务洞察
        5. 在 **公司对比** 中进行多公司对比和行业基准分析
        6. 探索 **AI洞察** 获取自动化模式识别和风险分析
        7. 在 **数据导出** 中将您的分析结果导出为专业报告
        """)
    
    # System status
    st.subheader("📋 系统状态")
    col1, col2, col3, col4 = st.columns(4)
    
    # Get processing stats safely
    stats = get_processing_stats()
    
    with col1:
        st.metric("已处理文档", stats['documents_count'])
    
    with col2:
        st.metric("已提取表格", stats['tables_count'])
    
    with col3:
        rag_status = "活跃" if stats['rag_ready'] else "非活跃"
        st.metric("RAG系统", rag_status)
    
    with col4:
        st.metric("公司数量", stats['companies_count'])
    
    # API Key status
    st.subheader("🔑 配置状态")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        st.success("✅ OpenAI API密钥已配置")
    else:
        st.warning("⚠️ 未找到OpenAI API密钥。请设置OPENAI_API_KEY环境变量。")

if __name__ == "__main__":
    main()
