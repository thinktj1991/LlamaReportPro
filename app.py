import streamlit as st
import os
from pathlib import Path
from utils.state import init_state, get_processing_stats

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env文件加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，请运行: pip install python-dotenv")
except Exception as e:
    print(f"⚠️ 加载.env文件时出错: {e}")

# Apply nest_asyncio early to prevent event loop issues
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# Set page configuration
st.set_page_config(
    page_title="年报分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced UI styling
st.markdown("""
<style>
    /* Hide default navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Enhance sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
    }
    
    /* Custom navigation buttons */
    .nav-button {
        display: block;
        width: 100%;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: white;
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .nav-button.active {
        background: rgba(255, 255, 255, 0.3);
        font-weight: bold;
    }
    
    /* Status cards */
    .status-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .status-card h3 {
        margin: 0;
        font-size: 1.2rem;
    }
    
    .status-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Progress indicators */
    .progress-step {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-left: 4px solid #28a745;
        border-radius: 4px;
    }
    
    .progress-step.pending {
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .progress-step.completed {
        border-left-color: #28a745;
        background: #d4edda;
    }
    
    /* Enhanced metrics */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_state()

def main():
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>📊 年报分析系统</h1>
        <p>使用LlamaIndex和AI技术进行年报综合分析</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar navigation
    st.sidebar.title("🧭 导航菜单")
    
    # Navigation with status indicators
    stats = get_processing_stats()
    
    navigation_options = [
        {"name": "首页", "icon": "🏠", "desc": "系统概览和状态"},
        {"name": "上传与处理", "icon": "📁", "desc": "上传PDF文档", "badge": f"{stats['documents_count']}个文档" if stats['documents_count'] > 0 else None},
        {"name": "数据分析", "icon": "📊", "desc": "数据分析和可视化", "badge": f"{stats['tables_count']}个表格" if stats['tables_count'] > 0 else None},
        {"name": "问答系统", "icon": "🤖", "desc": "AI智能问答", "badge": "就绪" if stats['rag_ready'] else "未就绪"},
        {"name": "公司对比", "icon": "🏢", "desc": "多公司对比分析", "badge": f"{stats['companies_count']}家公司" if stats['companies_count'] > 0 else None},
        {"name": "比率分析", "icon": "📈", "desc": "财务比率计算"},
        {"name": "AI洞察", "icon": "🔍", "desc": "智能分析洞察"},
        {"name": "数据导出", "icon": "📤", "desc": "导出分析结果"}
    ]
    
    # Initialize navigation state
    if 'nav_page' not in st.session_state:
        st.session_state.nav_page = "首页"
    
    # Enhanced navigation with state management
    current_index = next((i for i, opt in enumerate(navigation_options) if opt["name"] == st.session_state.nav_page), 0)
    
    selected_page = st.sidebar.radio(
        "选择页面",
        [opt["name"] for opt in navigation_options],
        index=current_index,
        format_func=lambda x: next(opt["icon"] + " " + opt["name"] for opt in navigation_options if opt["name"] == x)
    )
    
    # Update session state
    st.session_state.nav_page = selected_page
    
    # Show navigation status
    for opt in navigation_options:
        if opt["name"] == selected_page:
            st.sidebar.info(f"📍 当前页面: {opt['desc']}")
            if opt.get("badge"):
                st.sidebar.success(f"📊 状态: {opt['badge']}")
            break
    
    page = selected_page
    
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
    # Welcome section with better visual hierarchy
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h2>🎉 欢迎使用年报分析系统</h2>
            <p style="font-size: 1.1rem; color: #6c757d;">一站式智能年报分析解决方案</p>
        </div>
        """, unsafe_allow_html=True)
    
    # System status overview with enhanced cards
    st.subheader("📊 系统状态总览")
    
    stats = get_processing_stats()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">📁</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">已处理文档</div>
        </div>
        """.format(stats['documents_count']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">📊</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">已提取表格</div>
        </div>
        """.format(stats['tables_count']), unsafe_allow_html=True)
    
    with col3:
        rag_status_icon = "🟢" if stats['rag_ready'] else "🔴"
        rag_status_text = "就绪" if stats['rag_ready'] else "未就绪"
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">RAG系统</div>
        </div>
        """.format(rag_status_icon, rag_status_text), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">🏢</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">识别公司</div>
        </div>
        """.format(stats['companies_count']), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Enhanced layout with better visual hierarchy
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.subheader("✨ 核心功能")
        
        features = [
            {"icon": "📄", "title": "PDF智能处理", "desc": "上传和处理多个年度报告"},
            {"icon": "📊", "title": "财务表格提取", "desc": "高级财务表格提取技术"},
            {"icon": "🤖", "title": "智能问答系统", "desc": "基于RAG技术的问答系统"},
            {"icon": "📈", "title": "财务比率分析", "desc": "高级财务比率计算"},
            {"icon": "🔍", "title": "AI智能洞察", "desc": "模式识别和异常检测"},
            {"icon": "🏢", "title": "公司对比分析", "desc": "多公司并排分析和基准测试"},
            {"icon": "📤", "title": "专业报告导出", "desc": "生成多种格式的专业报告"},
            {"icon": "📉", "title": "数据可视化", "desc": "交互式图表和图形"}
        ]
        
        for feature in features:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;">
                <span style="font-size: 1.2rem; margin-right: 0.75rem;">{feature['icon']}</span>
                <div>
                    <strong style="color: #2c3e50;">{feature['title']}</strong><br>
                    <small style="color: #6c757d;">{feature['desc']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🚀 使用引导")
        
        # Dynamic workflow based on current state
        workflow_steps = [
            {
                "step": 1,
                "title": "上传PDF文档",
                "desc": "选择年报或财务文档进行上传",
                "status": "completed" if stats['documents_count'] > 0 else "pending",
                "page": "上传与处理"
            },
            {
                "step": 2,
                "title": "数据分析",
                "desc": "探索提取的财务数据和表格",
                "status": "completed" if stats['tables_count'] > 0 else "pending",
                "page": "数据分析"
            },
            {
                "step": 3,
                "title": "智能问答",
                "desc": "使用AI对文档内容进行提问",
                "status": "completed" if stats['rag_ready'] else "pending",
                "page": "问答系统"
            },
            {
                "step": 4,
                "title": "深度分析",
                "desc": "财务比率分析和AI洞察",
                "status": "pending",
                "page": "比率分析"
            },
            {
                "step": 5,
                "title": "导出报告",
                "desc": "生成专业的分析报告",
                "status": "pending",
                "page": "数据导出"
            }
        ]
        
        for step in workflow_steps:
            status_class = step['status']
            status_icon = "✅" if status_class == "completed" else "⏳"
            
            st.markdown(f"""
            <div class="progress-step {status_class}">
                <span style="font-size: 1.2rem; margin-right: 0.75rem;">{status_icon}</span>
                <div style="flex-grow: 1;">
                    <strong>步骤 {step['step']}: {step['title']}</strong><br>
                    <small>{step['desc']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced configuration status
    st.subheader("⚙️ 系统配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            st.markdown("""
            <div class="status-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <h3>🔑 API配置</h3>
                <p>✅ OpenAI API密钥已配置</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card" style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);">
                <h3>🔑 API配置</h3>
                <p>⚠️ 需要配置OpenAI API密钥</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if stats['documents_count'] > 0:
            st.markdown("""
            <div class="status-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <h3>📊 数据状态</h3>
                <p>✅ 系统已处理数据，可以开始分析</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card" style="background: linear-gradient(135deg, #fad0c4 0%, #fad0c4 100%);">
                <h3>📊 数据状态</h3>
                <p>📁 请上传PDF文档开始分析</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick action buttons
    st.subheader("⚡ 快速开始")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 上传文档", use_container_width=True):
            st.session_state.nav_page = "上传与处理"
            st.rerun()
    
    with col2:
        disabled = stats['documents_count'] == 0
        if st.button("📊 查看分析", use_container_width=True, disabled=disabled):
            st.session_state.nav_page = "数据分析"
            st.rerun()
    
    with col3:
        disabled = not stats['rag_ready']
        if st.button("🤖 智能问答", use_container_width=True, disabled=disabled):
            st.session_state.nav_page = "问答系统"
            st.rerun()
    
    with col4:
        disabled = stats['companies_count'] < 2
        if st.button("🏢 公司对比", use_container_width=True, disabled=disabled):
            st.session_state.nav_page = "公司对比"
            st.rerun()

if __name__ == "__main__":
    main()
