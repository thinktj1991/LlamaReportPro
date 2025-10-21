"""
杜邦分析可视化组件
使用Plotly创建Sankey图和树状图
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def create_dupont_sankey(dupont_analysis: Any) -> go.Figure:
    """
    创建杜邦分析Sankey图
    
    Args:
        dupont_analysis: DupontAnalysis Pydantic模型实例
        
    Returns:
        Plotly Figure对象
    """
    try:
        # 定义节点标签
        labels = [
            # Level 1 (索引 0-2)
            f"净资产收益率<br>{dupont_analysis.level1.roe.formatted_value}",
            f"资产净利率<br>{dupont_analysis.level1.roa.formatted_value}",
            f"权益乘数<br>{dupont_analysis.level1.equity_multiplier.formatted_value}",
            
            # Level 2 (索引 3-6)
            f"营业净利润率<br>{dupont_analysis.level2.net_profit_margin.formatted_value}",
            f"资产周转率<br>{dupont_analysis.level2.asset_turnover.formatted_value}",
            f"总资产<br>{dupont_analysis.level2.total_assets.formatted_value}",
            f"股东权益<br>{dupont_analysis.level2.shareholders_equity.formatted_value}",
            
            # Level 3 (索引 7-10)
            f"净利润<br>{dupont_analysis.level3.net_income.formatted_value}",
            f"营业收入<br>{dupont_analysis.level3.revenue.formatted_value}",
            f"流动资产<br>{dupont_analysis.level3.current_assets.formatted_value}",
            f"非流动资产<br>{dupont_analysis.level3.non_current_assets.formatted_value}",
        ]
        
        # 定义连接关系 (source -> target)
        # ROE <- ROA, 权益乘数
        # ROA <- 营业净利润率, 资产周转率
        # 权益乘数 <- 总资产, 股东权益
        # 营业净利润率 <- 净利润, 营业收入
        # 资产周转率 <- 营业收入, 总资产
        # 总资产 <- 流动资产, 非流动资产
        
        source = [
            1, 2,      # ROA, 权益乘数 -> ROE
            3, 4,      # 营业净利润率, 资产周转率 -> ROA
            5, 6,      # 总资产, 股东权益 -> 权益乘数
            7, 8,      # 净利润, 营业收入 -> 营业净利润率
            8, 5,      # 营业收入, 总资产 -> 资产周转率
            9, 10      # 流动资产, 非流动资产 -> 总资产
        ]
        
        target = [
            0, 0,      # -> ROE
            1, 1,      # -> ROA
            2, 2,      # -> 权益乘数
            3, 3,      # -> 营业净利润率
            4, 4,      # -> 资产周转率
            5, 5       # -> 总资产
        ]
        
        # 定义流量值（用于控制线条粗细）
        # 使用归一化的值
        roe_value = float(dupont_analysis.level1.roe.value)
        roa_value = float(dupont_analysis.level1.roa.value)
        equity_multiplier_value = float(dupont_analysis.level1.equity_multiplier.value)
        
        values = [
            roa_value * 10,                    # ROA -> ROE
            equity_multiplier_value * 5,       # 权益乘数 -> ROE
            roa_value * 5,                     # 营业净利润率 -> ROA
            roa_value * 5,                     # 资产周转率 -> ROA
            equity_multiplier_value * 3,       # 总资产 -> 权益乘数
            equity_multiplier_value * 2,       # 股东权益 -> 权益乘数
            10, 10,                            # 净利润, 营业收入 -> 营业净利润率
            10, 10,                            # 营业收入, 总资产 -> 资产周转率
            10, 10                             # 流动资产, 非流动资产 -> 总资产
        ]
        
        # 定义节点颜色
        node_colors = [
            "#FF6B6B",  # ROE - 红色（最重要）
            "#4ECDC4",  # ROA - 青色
            "#45B7D1",  # 权益乘数 - 蓝色
            "#96CEB4",  # 营业净利润率 - 绿色
            "#FFEAA7",  # 资产周转率 - 黄色
            "#DFE6E9",  # 总资产 - 灰色
            "#74B9FF",  # 股东权益 - 浅蓝
            "#A29BFE",  # 净利润 - 紫色
            "#FD79A8",  # 营业收入 - 粉色
            "#FDCB6E",  # 流动资产 - 橙色
            "#6C5CE7"   # 非流动资产 - 深紫
        ]
        
        # 创建Sankey图
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color="black", width=0.5),
                label=labels,
                color=node_colors,
                customdata=[f"层级 {i//4 + 1}" for i in range(len(labels))],
                hovertemplate='%{label}<br>%{customdata}<extra></extra>'
            ),
            link=dict(
                source=source,
                target=target,
                value=values,
                color="rgba(0,0,0,0.15)",
                hovertemplate='%{source.label} → %{target.label}<br>影响权重: %{value:.2f}<extra></extra>'
            )
        )])
        
        # 更新布局
        fig.update_layout(
            title={
                'text': f"{dupont_analysis.company_name} - {dupont_analysis.report_year}年度杜邦分析",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Microsoft YaHei, Arial', 'color': '#2C3E50'}
            },
            font=dict(size=12, family="Microsoft YaHei, Arial"),
            height=700,
            margin=dict(l=20, r=20, t=80, b=20),
            paper_bgcolor='#F8F9FA',
            plot_bgcolor='#F8F9FA'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"创建Sankey图失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 返回错误提示图
        fig = go.Figure()
        fig.add_annotation(
            text=f"可视化生成失败: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="Sankey图生成错误",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig


def create_dupont_tree_chart(dupont_analysis: Any) -> go.Figure:
    """
    创建杜邦分析树状图（备选方案）
    
    Args:
        dupont_analysis: DupontAnalysis Pydantic模型实例
        
    Returns:
        Plotly Figure对象
    """
    try:
        import plotly.graph_objects as go
        
        # 使用tree_structure构建树状图
        tree = dupont_analysis.tree_structure
        
        # 递归构建节点和边
        nodes_x = []
        nodes_y = []
        nodes_text = []
        nodes_color = []
        edges_x = []
        edges_y = []
        
        def add_node_recursive(node, x, y, level, parent_x=None, parent_y=None):
            """递归添加节点"""
            nodes_x.append(x)
            nodes_y.append(y)
            nodes_text.append(f"{node.name}<br>{node.formatted_value}")
            
            # 根据层级设置颜色
            colors = ['#FF6B6B', '#4ECDC4', '#96CEB4', '#A29BFE']
            nodes_color.append(colors[level - 1] if level <= 4 else '#DFE6E9')
            
            # 添加边
            if parent_x is not None and parent_y is not None:
                edges_x.extend([parent_x, x, None])
                edges_y.extend([parent_y, y, None])
            
            # 递归处理子节点
            if node.children:
                child_count = len(node.children)
                child_spacing = 2.0 / (child_count + 1)
                for i, child in enumerate(node.children):
                    child_x = x - 1.0 + (i + 1) * child_spacing
                    child_y = y - 1
                    add_node_recursive(child, child_x, child_y, level + 1, x, y)
        
        # 从根节点开始
        add_node_recursive(tree, 0, 0, 1)
        
        # 创建边的trace
        edge_trace = go.Scatter(
            x=edges_x, y=edges_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # 创建节点的trace
        node_trace = go.Scatter(
            x=nodes_x, y=nodes_y,
            mode='markers+text',
            hoverinfo='text',
            text=nodes_text,
            textposition="top center",
            marker=dict(
                size=30,
                color=nodes_color,
                line=dict(width=2, color='white')
            )
        )
        
        # 创建图形
        fig = go.Figure(data=[edge_trace, node_trace])
        
        fig.update_layout(
            title=f"{dupont_analysis.company_name} - {dupont_analysis.report_year}年度杜邦分析树状图",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=80),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600,
            font=dict(family="Microsoft YaHei, Arial")
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"创建树状图失败: {str(e)}")
        return create_error_figure(str(e))


def create_dupont_bar_chart(dupont_analysis: Any) -> go.Figure:
    """
    创建杜邦分析指标对比柱状图
    
    Args:
        dupont_analysis: DupontAnalysis Pydantic模型实例
        
    Returns:
        Plotly Figure对象
    """
    try:
        # 提取关键指标
        metrics = {
            '净资产收益率': float(dupont_analysis.level1.roe.value),
            '资产净利率': float(dupont_analysis.level1.roa.value),
            '权益乘数': float(dupont_analysis.level1.equity_multiplier.value),
            '营业净利润率': float(dupont_analysis.level2.net_profit_margin.value),
            '资产周转率': float(dupont_analysis.level2.asset_turnover.value)
        }
        
        # 创建柱状图
        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker=dict(
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
                    line=dict(color='white', width=2)
                ),
                text=[f"{v:.2f}" for v in metrics.values()],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title=f"{dupont_analysis.company_name} - {dupont_analysis.report_year}年度关键指标",
            xaxis_title="指标名称",
            yaxis_title="指标值",
            font=dict(family="Microsoft YaHei, Arial"),
            height=500,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"创建柱状图失败: {str(e)}")
        return create_error_figure(str(e))


def create_error_figure(error_message: str) -> go.Figure:
    """
    创建错误提示图
    
    Args:
        error_message: 错误信息
        
    Returns:
        Plotly Figure对象
    """
    fig = go.Figure()
    fig.add_annotation(
        text=f"可视化生成失败: {error_message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(
        title="可视化错误",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400
    )
    return fig

