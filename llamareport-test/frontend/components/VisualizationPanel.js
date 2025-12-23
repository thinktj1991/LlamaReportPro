// 可视化面板组件
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
            if (!this.chartData) return 'empty';
            return 'content';
        }
    },
    methods: {
        renderChart() {
            if (!this.chartData?.chart_config || !window.Plotly) return;
            
            this.$nextTick(() => {
                try {
                    const chartConfig = this.chartData.chart_config;
                    const traces = chartConfig.traces.map(trace => {
                        const plotlyTrace = {
                            type: trace.type || 'scatter',
                            name: trace.name || '数据',
                        };
                        
                        if (trace.type === 'pie') {
                            plotlyTrace.labels = trace.text || [];
                            plotlyTrace.values = trace.y || [];
                        } else {
                            plotlyTrace.x = trace.x || [];
                            plotlyTrace.y = trace.y || [];
                        }
                        
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
                            font: { size: 16, color: '#333' }
                        },
                        xaxis: {
                            title: chartConfig.layout.xaxis_title || '',
                            gridcolor: '#e0e0e0'
                        },
                        yaxis: {
                            title: chartConfig.layout.yaxis_title || '',
                            gridcolor: '#e0e0e0'
                        },
                        height: 400,
                        template: chartConfig.layout.template || 'plotly_white',
                        hovermode: chartConfig.layout.hovermode || 'closest',
                        showlegend: chartConfig.layout.showlegend !== false,
                        margin: { t: 50, r: 30, b: 50, l: 50 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)'
                    };
                    
                    const config = {
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d']
                    };
                    
                    Plotly.newPlot('visualizationChart', traces, layout, config);
                } catch (error) {
                    console.error('渲染图表失败:', error);
                }
            });
        }
    },
    watch: {
        chartData: {
            handler() {
                if (this.chartData) {
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
                <div id="visualizationChart" class="chart-container"></div>
            </template>
        </Card>
    `
};
