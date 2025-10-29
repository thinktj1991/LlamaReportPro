"""
智能可视化问答页面
集成了自动图表生成功能的问答界面
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="智能可视化问答 - LlamaReport",
    page_icon="📊",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .insight-type {
        display: inline-block;
        background-color: #1f77b4;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    .recommendation-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-header">📊 智能可视化问答系统</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">基于 LlamaIndex + DeepSeek 的智能数据分析与可视化</div>', unsafe_allow_html=True)

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置选项")
    
    # API配置
    api_url = st.text_input(
        "API地址",
        value="http://localhost:8000",
        help="后端API服务地址"
    )
    
    # 可视化选项
    enable_viz = st.checkbox(
        "启用智能可视化",
        value=True,
        help="自动为包含数据的回答生成图表"
    )
    
    show_insights = st.checkbox(
        "显示数据洞察",
        value=True,
        help="显示AI生成的数据洞察"
    )
    
    show_recommendation = st.checkbox(
        "显示图表推荐",
        value=True,
        help="显示图表类型推荐理由"
    )
    
    st.divider()
    
    # 示例问题
    st.header("💡 示例问题")
    
    example_questions = [
        "公司2021-2023年的营业收入趋势如何？",
        "各业务板块的收入占比是多少？",
        "公司净利润增长情况如何？",
        "资产负债率的变化趋势",
        "研发费用占营业收入的比例",
        "现金流量的变化情况"
    ]
    
    for i, question in enumerate(example_questions):
        if st.button(f"📌 {question}", key=f"example_{i}"):
            st.session_state.selected_question = question

# 主界面
col1, col2 = st.columns([3, 1])

with col1:
    # 查询输入
    default_question = st.session_state.get('selected_question', '')
    question = st.text_area(
        "请输入您的问题",
        value=default_question,
        height=100,
        placeholder="例如：公司2021-2023年的营业收入趋势如何？"
    )

with col2:
    st.write("")  # 占位
    st.write("")  # 占位
    query_button = st.button("🔍 查询分析", type="primary", use_container_width=True)
    clear_button = st.button("🗑️ 清空", use_container_width=True)

if clear_button:
    st.session_state.selected_question = ''
    st.rerun()

# 查询处理
if query_button and question.strip():
    with st.spinner("🤔 正在分析数据并生成可视化..."):
        try:
            # 调用API
            response = requests.post(
                f"{api_url}/query/ask",
                json={
                    "question": question,
                    "enable_visualization": enable_viz
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 显示文本回答
                st.markdown("### 📝 分析结果")
                st.info(data['answer'])
                
                # 显示可视化
                if enable_viz and data.get('visualization'):
                    viz_data = data['visualization']
                    
                    if viz_data.get('has_visualization'):
                        st.markdown("---")
                        st.markdown("### 📊 数据可视化")
                        
                        # 显示图表推荐
                        if show_recommendation and viz_data.get('recommendation'):
                            rec = viz_data['recommendation']
                            st.markdown(f"""
                            <div class="recommendation-box">
                                <strong>🎯 推荐图表类型:</strong> {rec['recommended_chart_type']}<br>
                                <strong>💡 推荐理由:</strong> {rec['reason']}<br>
                                <strong>📈 数据特征:</strong> {rec['data_characteristics']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 渲染图表
                        chart_config = viz_data.get('chart_config')
                        if chart_config:
                            fig = create_plotly_chart(chart_config)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # 显示洞察
                        if show_insights and viz_data.get('insights'):
                            st.markdown("---")
                            st.markdown("### 💡 数据洞察")
                            
                            for insight in viz_data['insights']:
                                st.markdown(f"""
                                <div class="insight-box">
                                    <span class="insight-type">{insight['insight_type']}</span>
                                    <p><strong>{insight['description']}</strong></p>
                                    <ul>
                                        {''.join([f"<li>{finding}</li>" for finding in insight['key_findings']])}
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("💬 此查询不包含可视化数据")
                
                # 显示来源（如果有）
                if data.get('sources'):
                    with st.expander("📚 数据来源"):
                        for i, source in enumerate(data['sources'], 1):
                            st.markdown(f"**来源 {i}:**")
                            st.text(source.get('text', '')[:200] + "...")
                
            else:
                st.error(f"❌ 查询失败: {response.json().get('detail', '未知错误')}")
                
        except requests.exceptions.Timeout:
            st.error("❌ 请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            st.error(f"❌ 无法连接到API服务器: {api_url}")
        except Exception as e:
            st.error(f"❌ 发生错误: {str(e)}")
            logger.error(f"查询错误: {str(e)}")

elif query_button:
    st.warning("⚠️ 请输入问题")


def create_plotly_chart(chart_config: Dict[str, Any]) -> go.Figure:
    """
    根据配置创建Plotly图表
    
    Args:
        chart_config: 图表配置
    
    Returns:
        go.Figure: Plotly图表对象
    """
    fig = go.Figure()
    
    # 添加轨迹
    for trace_data in chart_config.get('traces', []):
        trace_type = trace_data.get('type', 'scatter')
        
        if trace_type == 'bar':
            trace = go.Bar(
                x=trace_data.get('x', []),
                y=trace_data.get('y', []),
                name=trace_data.get('name', ''),
                marker=trace_data.get('marker'),
                text=trace_data.get('text'),
                textposition=trace_data.get('textposition', 'auto')
            )
        elif trace_type == 'scatter':
            trace = go.Scatter(
                x=trace_data.get('x', []),
                y=trace_data.get('y', []),
                name=trace_data.get('name', ''),
                mode=trace_data.get('mode', 'lines+markers'),
                line=trace_data.get('line'),
                marker=trace_data.get('marker'),
                text=trace_data.get('text'),
                hovertemplate=trace_data.get('hovertemplate')
            )
        elif trace_type == 'pie':
            # 饼图：labels从text字段获取，values从y字段获取
            labels = trace_data.get('text', []) or trace_data.get('labels', [])
            values = trace_data.get('y', []) or trace_data.get('values', [])

            trace = go.Pie(
                labels=labels,
                values=values,
                name=trace_data.get('name', ''),
                hovertemplate=trace_data.get('hovertemplate'),
                marker=trace_data.get('marker')
            )
        else:
            # 默认使用散点图
            trace = go.Scatter(
                x=trace_data.get('x', []),
                y=trace_data.get('y', []),
                name=trace_data.get('name', '')
            )
        
        fig.add_trace(trace)
    
    # 更新布局
    layout = chart_config.get('layout', {})
    fig.update_layout(
        title=layout.get('title', ''),
        xaxis_title=layout.get('xaxis_title', ''),
        yaxis_title=layout.get('yaxis_title', ''),
        height=layout.get('height', 500),
        template=layout.get('template', 'plotly_white'),
        hovermode=layout.get('hovermode', 'closest'),
        showlegend=layout.get('showlegend', True)
    )
    
    return fig


# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>💡 提示：尝试询问包含数值、趋势、对比等关键词的问题，系统会自动生成相应的可视化图表</p>
    <p>🚀 Powered by LlamaIndex + DeepSeek + Plotly</p>
</div>
""", unsafe_allow_html=True)

