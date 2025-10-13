"""
可视化生成 Agent
智能分析数据并生成合适的图表配置
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Annotated
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from models.visualization_models import (
    ChartType,
    ChartRecommendation,
    VisualizationResponse,
    PlotlyChartConfig,
    ChartTrace,
    ChartLayout,
    SimpleBarChart,
    SimpleLineChart,
    SimplePieChart,
    MultiLineChart,
    GroupedBarChart,
    TableChart,
    VisualizationInsight
)

logger = logging.getLogger(__name__)


class VisualizationAgent:
    """可视化生成Agent"""
    
    def __init__(self, llm=None):
        """
        初始化可视化Agent
        
        Args:
            llm: LLM实例，如果为None则使用Settings.llm
        """
        self.llm = llm or Settings.llm
    
    async def generate_visualization(
        self,
        query: str,
        answer: str,
        data: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict]] = None
    ) -> VisualizationResponse:
        """
        生成可视化配置
        
        Args:
            query: 用户查询
            answer: 文本回答
            data: 原始数据（可选）
            sources: 数据来源（可选）
        
        Returns:
            VisualizationResponse: 包含图表配置的响应
        """
        try:
            logger.info(f"开始生成可视化: {query[:50]}...")
            
            # 1. 分析查询和回答，判断是否需要可视化
            needs_viz = await self._analyze_visualization_need(query, answer)
            
            if not needs_viz:
                return VisualizationResponse(
                    query=query,
                    answer=answer,
                    has_visualization=False
                )
            
            # 2. 提取数据
            extracted_data = await self._extract_data_from_answer(query, answer, sources)
            
            if not extracted_data or not extracted_data.get('has_data'):
                logger.info("未能从回答中提取到可视化数据")
                return VisualizationResponse(
                    query=query,
                    answer=answer,
                    has_visualization=False
                )
            
            # 3. 推荐图表类型
            recommendation = await self._recommend_chart_type(
                query, 
                extracted_data
            )
            
            # 4. 生成图表配置
            chart_config = await self._generate_chart_config(
                recommendation.recommended_chart_type,
                extracted_data,
                query
            )
            
            # 5. 生成洞察
            insights = await self._generate_insights(
                extracted_data,
                recommendation.recommended_chart_type
            )
            
            logger.info(f"✅ 可视化生成成功: {recommendation.recommended_chart_type}")
            
            return VisualizationResponse(
                query=query,
                answer=answer,
                has_visualization=True,
                chart_config=chart_config,
                recommendation=recommendation,
                insights=insights,
                confidence_score=0.85
            )
            
        except Exception as e:
            logger.error(f"❌ 生成可视化失败: {str(e)}")
            return VisualizationResponse(
                query=query,
                answer=answer,
                has_visualization=False
            )
    
    async def _analyze_visualization_need(
        self,
        query: str,
        answer: str
    ) -> bool:
        """
        分析是否需要可视化
        
        Args:
            query: 用户查询
            answer: 文本回答
        
        Returns:
            bool: 是否需要可视化
        """
        try:
            # 关键词检测
            viz_keywords = [
                '趋势', '对比', '比较', '增长', '下降', '变化',
                '分布', '占比', '份额', '排名', '图表', '可视化',
                '多少', '如何', '怎样', '数据', '指标', '财务',
                '收入', '利润', '资产', '负债', '现金流'
            ]
            
            # 检查查询中是否包含可视化关键词
            query_lower = query.lower()
            has_viz_keyword = any(keyword in query for keyword in viz_keywords)
            
            # 检查回答中是否包含数字
            has_numbers = bool(re.search(r'\d+\.?\d*', answer))
            
            # 检查回答长度（如果回答很短，可能不需要可视化）
            answer_length = len(answer)
            
            # 综合判断
            needs_viz = (has_viz_keyword or has_numbers) and answer_length > 50
            
            logger.info(f"可视化需求分析: {needs_viz} (关键词:{has_viz_keyword}, 数字:{has_numbers}, 长度:{answer_length})")
            
            return needs_viz
            
        except Exception as e:
            logger.error(f"分析可视化需求失败: {str(e)}")
            return False
    
    async def _extract_data_from_answer(
        self,
        query: str,
        answer: str,
        sources: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        从回答中提取数据
        
        Args:
            query: 用户查询
            answer: 文本回答
            sources: 数据来源
        
        Returns:
            Dict: 提取的数据
        """
        try:
            prompt = f"""
分析以下查询和回答，提取可用于可视化的数据。

查询: {query}

回答: {answer}

请提取以下信息（以JSON格式返回）：
1. has_data: 是否包含可视化数据（true/false）
2. data_type: 数据类型（time_series/comparison/distribution/single_value/table）
3. labels: 标签列表（如果适用）
4. values: 数值列表（如果适用）
5. series: 多系列数据（如果适用）
6. unit: 数值单位（如元、%、万等）
7. time_period: 时间周期（如果是时间序列）

示例输出：
{{
    "has_data": true,
    "data_type": "comparison",
    "labels": ["2021年", "2022年", "2023年"],
    "values": [100, 120, 150],
    "unit": "亿元",
    "time_period": "年度"
}}

如果无法提取数据，返回：
{{
    "has_data": false
}}
"""
            
            response = await self.llm.acomplete(prompt)
            response_text = str(response).strip()
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    logger.info(f"成功提取数据: {data.get('data_type', 'unknown')}")
                    return data
                else:
                    return {"has_data": False}
            except json.JSONDecodeError:
                logger.warning("无法解析LLM返回的JSON")
                return {"has_data": False}
                
        except Exception as e:
            logger.error(f"提取数据失败: {str(e)}")
            return {"has_data": False}
    
    async def _recommend_chart_type(
        self,
        query: str,
        data: Dict[str, Any]
    ) -> ChartRecommendation:
        """
        推荐图表类型
        
        Args:
            query: 用户查询
            data: 提取的数据
        
        Returns:
            ChartRecommendation: 图表推荐
        """
        try:
            data_type = data.get('data_type', 'unknown')
            
            # 基于数据类型的简单规则
            type_mapping = {
                'time_series': ChartType.LINE,
                'comparison': ChartType.BAR,
                'distribution': ChartType.PIE,
                'single_value': ChartType.GAUGE,
                'table': ChartType.TABLE
            }
            
            recommended_type = type_mapping.get(data_type, ChartType.BAR)
            
            # 备选图表
            alternatives = {
                'time_series': [ChartType.AREA, ChartType.MULTI_LINE],
                'comparison': [ChartType.GROUPED_BAR, ChartType.LINE],
                'distribution': [ChartType.BAR, ChartType.FUNNEL],
                'table': [ChartType.HEATMAP]
            }
            
            return ChartRecommendation(
                recommended_chart_type=recommended_type,
                reason=f"基于数据类型'{data_type}'，{recommended_type.value}图最适合展示这类数据",
                data_characteristics=f"数据类型: {data_type}, 数据点数: {len(data.get('values', []))}",
                alternative_charts=alternatives.get(data_type, [])
            )
            
        except Exception as e:
            logger.error(f"推荐图表类型失败: {str(e)}")
            return ChartRecommendation(
                recommended_chart_type=ChartType.BAR,
                reason="默认推荐",
                data_characteristics="未知"
            )

    async def _generate_chart_config(
        self,
        chart_type: ChartType,
        data: Dict[str, Any],
        query: str
    ) -> PlotlyChartConfig:
        """
        生成图表配置

        Args:
            chart_type: 图表类型
            data: 数据
            query: 查询

        Returns:
            PlotlyChartConfig: Plotly图表配置
        """
        try:
            labels = data.get('labels', [])
            values = data.get('values', [])
            unit = data.get('unit', '')

            # 生成标题
            title = self._generate_chart_title(query, chart_type)

            # 根据图表类型生成配置
            if chart_type == ChartType.BAR:
                trace = ChartTrace(
                    name="数据",
                    x=labels,
                    y=values,
                    type="bar",
                    marker={"color": "rgb(55, 83, 109)"},
                    text=[f"{v}{unit}" for v in values],
                    textposition="auto"
                )

            elif chart_type == ChartType.LINE:
                trace = ChartTrace(
                    name="趋势",
                    x=labels,
                    y=values,
                    type="scatter",
                    mode="lines+markers",
                    line={"color": "rgb(55, 128, 191)", "width": 3},
                    marker={"size": 8},
                    text=[f"{v}{unit}" for v in values],
                    hovertemplate="%{x}: %{y}" + unit + "<extra></extra>"
                )

            elif chart_type == ChartType.PIE:
                trace = ChartTrace(
                    name="分布",
                    x=[],  # PIE图不需要x
                    y=values,
                    type="pie",
                    text=labels,
                    hovertemplate="%{label}: %{value}" + unit + " (%{percent})<extra></extra>"
                )

            else:
                # 默认使用柱状图
                trace = ChartTrace(
                    name="数据",
                    x=labels,
                    y=values,
                    type="bar"
                )

            # 创建布局
            layout = ChartLayout(
                title=title,
                xaxis_title=data.get('x_title', ''),
                yaxis_title=data.get('y_title', unit),
                height=500,
                showlegend=True,
                template="plotly_white",
                hovermode="closest"
            )

            return PlotlyChartConfig(
                chart_type=chart_type,
                traces=[trace],
                layout=layout
            )

        except Exception as e:
            logger.error(f"生成图表配置失败: {str(e)}")
            # 返回一个基本的配置
            return PlotlyChartConfig(
                chart_type=ChartType.BAR,
                traces=[ChartTrace(name="数据", x=[], y=[])],
                layout=ChartLayout(title="图表生成失败")
            )

    def _generate_chart_title(self, query: str, chart_type: ChartType) -> str:
        """
        生成图表标题

        Args:
            query: 查询
            chart_type: 图表类型

        Returns:
            str: 图表标题
        """
        # 简化查询作为标题
        title = query[:50] + "..." if len(query) > 50 else query

        # 添加图表类型后缀
        type_suffix = {
            ChartType.BAR: "对比图",
            ChartType.LINE: "趋势图",
            ChartType.PIE: "分布图",
            ChartType.AREA: "面积图",
            ChartType.SCATTER: "散点图"
        }

        suffix = type_suffix.get(chart_type, "")
        if suffix and suffix not in title:
            title = f"{title} - {suffix}"

        return title

    async def _generate_insights(
        self,
        data: Dict[str, Any],
        chart_type: ChartType
    ) -> List[VisualizationInsight]:
        """
        生成可视化洞察

        Args:
            data: 数据
            chart_type: 图表类型

        Returns:
            List[VisualizationInsight]: 洞察列表
        """
        try:
            insights = []
            values = data.get('values', [])
            labels = data.get('labels', [])

            if not values:
                return insights

            # 趋势洞察
            if len(values) >= 2:
                if values[-1] > values[0]:
                    trend = "上升"
                    change = ((values[-1] - values[0]) / values[0]) * 100
                elif values[-1] < values[0]:
                    trend = "下降"
                    change = ((values[0] - values[-1]) / values[0]) * 100
                else:
                    trend = "持平"
                    change = 0

                insights.append(VisualizationInsight(
                    insight_type="trend",
                    description=f"整体呈现{trend}趋势",
                    key_findings=[
                        f"从{labels[0] if labels else '起始'}到{labels[-1] if labels else '结束'}，变化幅度为{change:.1f}%"
                    ]
                ))

            # 极值洞察
            if len(values) > 0:
                max_val = max(values)
                min_val = min(values)
                max_idx = values.index(max_val)
                min_idx = values.index(min_val)

                insights.append(VisualizationInsight(
                    insight_type="comparison",
                    description="极值分析",
                    key_findings=[
                        f"最大值: {max_val} ({labels[max_idx] if labels and max_idx < len(labels) else ''})",
                        f"最小值: {min_val} ({labels[min_idx] if labels and min_idx < len(labels) else ''})",
                        f"差值: {max_val - min_val}"
                    ]
                ))

            return insights

        except Exception as e:
            logger.error(f"生成洞察失败: {str(e)}")
            return []


# ==================== 工具函数 ====================

async def generate_visualization_for_query(
    query: Annotated[str, "用户查询"],
    answer: Annotated[str, "文本回答"],
    data: Annotated[Optional[Dict[str, Any]], "原始数据"] = None,
    sources: Annotated[Optional[List[Dict]], "数据来源"] = None
) -> Dict[str, Any]:
    """
    为查询生成可视化

    这是一个可以被Agent调用的工具函数

    Args:
        query: 用户查询
        answer: 文本回答
        data: 原始数据（可选）
        sources: 数据来源（可选）

    Returns:
        Dict: 可视化响应
    """
    try:
        logger.info(f"工具调用: 生成可视化 - {query[:50]}...")

        viz_agent = VisualizationAgent()
        result = await viz_agent.generate_visualization(
            query=query,
            answer=answer,
            data=data,
            sources=sources
        )

        # 使用 model_dump() 而不是 dict() (Pydantic v2)
        return result.model_dump()

    except Exception as e:
        logger.error(f"❌ 可视化工具调用失败: {str(e)}")
        return {
            "query": query,
            "answer": answer,
            "has_visualization": False,
            "error": str(e)
        }

