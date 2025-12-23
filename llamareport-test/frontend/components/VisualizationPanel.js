// 可视化面板组件 - 增强版（包含洞察和推荐）
export default {
    name: 'VisualizationPanel',
    props: {
        chartData: {
            type: Object,
            default: null
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.chartData || !this.chartData.has_visualization) return 'empty';
            return 'content';
        },
        hasInsights() {
            return this.chartData?.insights && this.chartData.insights.length > 0;
        },
        hasRecommendation() {
            return this.chartData?.recommendation != null;
        },
        confidenceScore() {
            return this.chartData?.confidence_score || 0;
        }
    },
    methods: {
        renderChart() {
            if (!this.chartData?.chart_config || !window.Plotly) {
                if (!window.Plotly) {
                    console.warn('Plotly未加载，无法渲染图表');
                }
                return;
            }
            
            this.$nextTick(() => {
                try {
                    const chartConfig = this.chartData.chart_config;
                    const traces = chartConfig.traces.map(trace => {
                        const plotlyTrace = {
                            type: trace.type || 'scatter',
                            name: trace.name || '数据',
                        };
                        
                        // 特殊处理饼图
                        if (trace.type === 'pie') {
                            plotlyTrace.labels = trace.text || [];
                            plotlyTrace.values = trace.y || [];
                        } else {
                            plotlyTrace.x = trace.x || [];
                            plotlyTrace.y = trace.y || [];
                        }
                        
                        // 添加可选属性
                        if (trace.mode) plotlyTrace.mode = trace.mode;
                        if (trace.marker) plotlyTrace.marker = trace.marker;
                        if (trace.line) plotlyTrace.line = trace.line;
                        if (trace.type !== 'pie' && trace.text) {
                            plotlyTrace.text = trace.text;
                        }
                        if (trace.textposition) plotlyTrace.textposition = trace.textposition;
                        if (trace.hovertemplate) plotlyTrace.hovertemplate = trace.hovertemplate;
                        
                        return plotlyTrace;
                    });
                    
                    const layout = {
                        title: {
                            text: chartConfig.layout.title || '',
                            font: { size: 18, color: '#333' }
                        },
                        xaxis: {
                            title: chartConfig.layout.xaxis_title || '',
                            gridcolor: '#e0e0e0'
                        },
                        yaxis: {
                            title: chartConfig.layout.yaxis_title || '',
                            gridcolor: '#e0e0e0'
                        },
                        height: chartConfig.layout.height || 500,
                        template: chartConfig.layout.template || 'plotly_white',
                        hovermode: chartConfig.layout.hovermode || 'closest',
                        showlegend: chartConfig.layout.showlegend !== false,
                        margin: { t: 60, r: 40, b: 60, l: 60 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)'
                    };
                    
                    const config = {
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d']
                    };
                    
                    if (window.Plotly && window.Plotly.newPlot) {
                        window.Plotly.newPlot('visualizationChart', traces, layout, config);
                    } else {
                        console.warn('Plotly未加载，无法渲染图表');
                    }
                } catch (error) {
                    console.error('渲染图表失败:', error);
                    const chartDiv = document.getElementById('visualizationChart');
                    if (chartDiv) {
                        chartDiv.innerHTML = `<div class="error">图表渲染失败: ${error.message}</div>`;
                    }
                }
            });
        },
        getInsightIcon(type) {
            const icons = {
                'trend': '📈',
                'comparison': '⚖️',
                'distribution': '📊',
                'correlation': '🔗',
                'anomaly': '⚠️'
            };
            return icons[type] || '💡';
        },
        getChartTypeName(type) {
            const names = {
                'bar': '柱状图',
                'line': '折线图',
                'pie': '饼图',
                'scatter': '散点图',
                'area': '面积图',
                'multi_line': '多折线图',
                'grouped_bar': '分组柱状图',
                'stacked_bar': '堆叠柱状图',
                'heatmap': '热力图',
                'box': '箱线图',
                'waterfall': '瀑布图',
                'funnel': '漏斗图',
                'gauge': '仪表盘',
                'table': '表格'
            };
            return names[type] || type;
        }
    },
    watch: {
        chartData: {
            handler() {
                if (this.chartData && this.chartData.has_visualization) {
                    this.renderChart();
                }
            },
            deep: true
        }
    },
    template: `
        <Card 
            title="数据可视化" 
            icon="📈"
            :status="status"
            empty-text="图表将在此显示"
        >
            <template #default>
                <!-- 图表区域 -->
                <div v-if="chartData && chartData.has_visualization" class="visualization-content">
                    <div class="chart-header">
                        <h3>📊 数据可视化 <span class="viz-badge">智能生成</span></h3>
                        <div v-if="confidenceScore > 0" class="confidence-badge">
                            置信度: {{ (confidenceScore * 100).toFixed(0) }}%
                        </div>
                    </div>
                    
                    <div id="visualizationChart" class="chart-container"></div>
                    
                    <!-- 推荐说明 -->
                    <div v-if="hasRecommendation" class="recommendation-box">
                        <h4>📈 图表推荐</h4>
                        <p><strong>推荐图表类型:</strong> {{ getChartTypeName(chartData.recommendation.recommended_chart_type) }}</p>
                        <p><strong>推荐理由:</strong> {{ chartData.recommendation.reason }}</p>
                    </div>
                    
                    <!-- 数据洞察 -->
                    <div v-if="hasInsights" class="insights-box">
                        <h3>💡 数据洞察</h3>
                        <div 
                            v-for="(insight, index) in chartData.insights" 
                            :key="index" 
                            class="insight-item"
                        >
                            <h4>
                                {{ getInsightIcon(insight.insight_type) }} 
                                {{ insight.description }}
                            </h4>
                            <ul v-if="insight.key_findings && insight.key_findings.length > 0">
                                <li v-for="(finding, idx) in insight.key_findings" :key="idx">
                                    {{ finding }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <!-- 错误提示 -->
                <div v-else-if="chartData && chartData.error" class="error-message">
                    <p>⚠️ 可视化生成失败: {{ chartData.error }}</p>
                </div>
                
                <!-- 无可视化提示 -->
                <div v-else-if="chartData && !chartData.has_visualization" class="no-viz-message">
                    <p>ℹ️ 此问题不包含可视化数据。尝试询问包含数值、趋势、对比等关键词的问题以获得图表展示。</p>
                </div>
            </template>
        </Card>
    `
};
