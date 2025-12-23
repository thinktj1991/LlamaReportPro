<template>
  <Card title="可视化视图" icon="📊" :status="status" empty-text="暂无可视化数据">
    <template #default>
      <!-- 杜邦分析可视化 -->
      <div v-if="dupontData && (dupontData.full_data || dupontData.roe)" class="dupont-visualization">
        <div class="chart-header">
          <h3>杜邦分析树状视图</h3>
          <div v-if="dupontData.full_data" class="dupont-info">
            <span>{{ dupontData.full_data.company_name || '未知公司' }} - {{ dupontData.full_data.report_year || '未知年份' }}</span>
          </div>
        </div>
        
        <!-- 树状结构视图 - 改进版杜邦分析图 -->
        <div v-if="dupontData.full_data && dupontData.full_data.tree_structure" class="dupont-tree-view-enhanced">
          <div class="dupont-diagram-container">
            <svg class="dupont-connectors" v-if="dupontData.full_data.tree_structure">
              <!-- SVG连接线将在JavaScript中动态生成 -->
            </svg>
            <DupontTreeNodeEnhanced :node="dupontData.full_data.tree_structure" :level="1" />
          </div>
        </div>
        
        <!-- 如果没有树状结构，使用层级视图 -->
        <div v-else-if="dupontData.full_data" class="dupont-level-view">
          <div class="level-section">
            <h4>第一层：ROE分解</h4>
            <div class="metrics-grid">
              <div class="metric-card main">
                <div class="metric-name">ROE (净资产收益率)</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level1', 'roe') }}</div>
                <div class="metric-formula">{{ getMetricFormula(dupontData.full_data, 'level1', 'roe') }}</div>
              </div>
            </div>
          </div>
          
          <div class="level-section">
            <h4>第二层：ROA和权益乘数</h4>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-name">ROA (资产净利率)</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level1', 'roa') }}</div>
                <div class="metric-formula">{{ getMetricFormula(dupontData.full_data, 'level1', 'roa') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">权益乘数</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level1', 'equity_multiplier') }}</div>
                <div class="metric-formula">{{ getMetricFormula(dupontData.full_data, 'level1', 'equity_multiplier') }}</div>
              </div>
            </div>
          </div>
          
          <div class="level-section">
            <h4>第三层：底层指标</h4>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-name">营业净利润率</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level2', 'net_profit_margin') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">资产周转率</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level2', 'asset_turnover') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">净利润</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level3', 'net_income') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">营业收入</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level3', 'revenue') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">总资产</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level2', 'total_assets') }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-name">股东权益</div>
                <div class="metric-value">{{ getMetricValue(dupontData.full_data, 'level2', 'shareholders_equity') }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 简单视图（如果没有完整数据） -->
        <div v-else class="dupont-tree">
          <div class="dupont-item main">
            <div class="dupont-label">ROE</div>
            <div class="dupont-value">{{ dupontData.roe || '—' }}</div>
          </div>
          <div class="dupont-branches">
            <div class="dupont-item">
              <div class="dupont-label">ROA</div>
              <div class="dupont-value">{{ dupontData.roa || '—' }}</div>
            </div>
            <div class="dupont-item">
              <div class="dupont-label">权益乘数</div>
              <div class="dupont-value">{{ dupontData.equity_multiplier || '—' }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 普通数据可视化图表区域 -->
      <div v-else-if="chartData && chartData.has_visualization" class="visualization-content">
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
      
      <!-- 完全空状态 -->
      <div v-else class="no-viz-message">
        <p>ℹ️ 暂无可视化数据。生成杜邦分析或进行包含数据的查询后，图表将在此显示。</p>
      </div>
    </template>
  </Card>
</template>

<script>
import Card from './Card.vue'

// 递归树节点组件 - 原始版本（保留作为备用）
const DupontTreeNode = {
  name: 'DupontTreeNode',
  props: {
    node: { type: Object, required: true },
    level: { type: Number, default: 1 }
  },
  template: `
    <div class="tree-node" :class="'level-' + level">
      <div class="node-content" :class="'level-' + level">
        <div class="node-name">{{ node.name }}</div>
        <div class="node-value">{{ node.formatted_value || node.value || '—' }}</div>
        <div v-if="node.formula" class="node-formula">{{ node.formula }}</div>
      </div>
      <div v-if="node.children && node.children.length > 0" class="node-children">
        <component 
          v-for="(child, index) in node.children" 
          :key="child.id || index"
          :is="'DupontTreeNode'"
          :node="child" 
          :level="level + 1"
        />
      </div>
    </div>
  `
}

// 注册递归组件
DupontTreeNode.components = { DupontTreeNode }

// 改进版杜邦分析树节点组件 - 参考GitHub项目实现
const DupontTreeNodeEnhanced = {
  name: 'DupontTreeNodeEnhanced',
  props: {
    node: { type: Object, required: true },
    level: { type: Number, default: 1 },
    index: { type: Number, default: 0 },
    total: { type: Number, default: 1 }
  },
  template: `
    <div class="dupont-node-wrapper" :class="'level-' + level" :data-level="level" :data-index="index">
      <div class="dupont-node" :class="'level-' + level">
        <div class="dupont-node-header">
          <div class="dupont-node-name">{{ node.name }}</div>
        </div>
        <div class="dupont-node-value">{{ node.formatted_value || node.value || '—' }}</div>
        <div v-if="node.formula" class="dupont-node-formula">{{ node.formula }}</div>
      </div>
      <div v-if="node.children && node.children.length > 0" class="dupont-children-container">
        <div class="dupont-children-row">
          <component
            v-for="(child, idx) in node.children"
            :key="child.id || idx"
            :is="'DupontTreeNodeEnhanced'"
            :node="child"
            :level="level + 1"
            :index="idx"
            :total="node.children.length"
          />
        </div>
      </div>
    </div>
  `,
  components: {}
}

// 注册递归组件
DupontTreeNodeEnhanced.components = { DupontTreeNodeEnhanced }

export default {
  name: 'VisualizationPanel',
  components: {
    Card,
    DupontTreeNode,
    DupontTreeNodeEnhanced
  },
  props: { 
    chartData: { type: Object, default: null }, 
    dupontData: { type: Object, default: null },
    loading: { type: Boolean, default: false } 
  },
  computed: {
    status() {
      if (this.loading) return 'loading';
      if (this.hasAnyVisualization) return 'content';
      return 'empty';
    },
    hasAnyVisualization() {
      return (this.chartData && this.chartData.has_visualization) || 
             (this.dupontData && (this.dupontData.full_data || this.dupontData.roe));
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
    getMetricValue(data, level, metric) {
      if (!data || !data[level] || !data[level][metric]) return '—'
      const metricObj = data[level][metric]
      return metricObj.formatted_value || metricObj.value || '—'
    },
    getMetricFormula(data, level, metric) {
      if (!data || !data[level] || !data[level][metric]) return ''
      const metricObj = data[level][metric]
      return metricObj.formula || ''
    },
    renderDupontChart() {
      if (!this.dupontData?.full_data || !window.Plotly) {
        return;
      }
      
      this.$nextTick(() => {
        try {
          const dupontData = this.dupontData.full_data;
          const level1 = dupontData.level1 || {};
          
          // 创建简单的柱状图显示关键指标
          const metrics = {
            'ROE': parseFloat(level1.roe?.value || 0) * 100,
            'ROA': parseFloat(level1.roa?.value || 0) * 100,
            '权益乘数': parseFloat(level1.equity_multiplier?.value || 0)
          };
          
          const trace = {
            type: 'bar',
            x: Object.keys(metrics),
            y: Object.values(metrics),
            marker: {
              color: ['#4facfe', '#00f2fe', '#43e97b'],
              line: { color: 'white', width: 1 }
            },
            text: Object.values(metrics).map((v, i) => {
              const key = Object.keys(metrics)[i];
              return v.toFixed(2) + (key === '权益乘数' ? '' : '%');
            }),
            textposition: 'outside'
          };
          
          const layout = {
            title: {
              text: '杜邦分析关键指标',
              font: { size: 16, color: '#333' }
            },
            xaxis: { title: '指标', gridcolor: '#e0e0e0' },
            yaxis: { title: '数值', gridcolor: '#e0e0e0' },
            height: 400,
            margin: { t: 60, r: 40, b: 60, l: 60 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            showlegend: false
          };
          
          const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
          };
          
          if (window.Plotly && window.Plotly.newPlot) {
            window.Plotly.newPlot('dupontChart', [trace], layout, config);
          }
        } catch (error) {
          console.error('渲染杜邦分析图表失败:', error);
        }
      });
    },
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
              name: trace.name || '数据' 
            };
            // 特殊处理饼图
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
            if (trace.type !== 'pie' && trace.text) plotlyTrace.text = trace.text;
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
            const errorMsg = error.message || '未知错误';
            chartDiv.innerHTML = '<div class="error-message"><p>图表渲染失败: ' + errorMsg + '</p></div>';
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
    },
    dupontData: {
      handler() {
        if (this.dupontData && this.dupontData.full_data) {
          this.renderDupontChart();
        }
      },
      deep: true
    }
  }
}
</script>


