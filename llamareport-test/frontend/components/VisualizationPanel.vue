<template>
  <Card title="可视化视图" icon="📊" :status="status" empty-text="暂无可视化数据">
    <template #default>
      <div class="visualization-panel-container">
        <!-- 卡片列表容器 -->
        <div class="visualization-cards-list" v-if="hasAnyVisualization">
          <!-- 杜邦分析卡片 -->
          <div v-if="dupontData && (dupontData.full_data || dupontData.roe)" class="viz-card dupont-card">
            <div class="viz-card-header">
              <div class="viz-card-title">
                <span class="viz-card-icon">📊</span>
                <h3>杜邦分析树状视图</h3>
              </div>
              <div class="viz-card-header-right">
                <div v-if="dupontData.full_data" class="viz-card-meta">
                  <span>{{ dupontData.full_data.company_name || '未知公司' }} - {{ dupontData.full_data.report_year || '未知年份' }}</span>
                </div>
                <div class="viz-card-actions">
                  <button class="viz-card-close" @click="removeDupontCard" title="删除">×</button>
                </div>
              </div>
            </div>
            <div class="viz-card-content">
              <!-- 树状结构视图 -->
              <div v-if="dupontData.full_data && dupontData.full_data.tree_structure" class="dupont-tree-view-enhanced">
                <div class="dupont-diagram-container">
                  <svg class="dupont-connectors" v-if="dupontData.full_data.tree_structure"></svg>
                  <DupontTreeNodeEnhanced :node="dupontData.full_data.tree_structure" :level="1" />
                </div>
              </div>
              <!-- 层级视图 -->
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
              <!-- 简单视图 -->
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
          </div>
          
          <!-- 普通查询可视化卡片列表（排除杜邦分析类型，因为杜邦分析通过dupontData显示） -->
          <div 
            v-for="card in visualizationCards.filter(c => c.type !== 'dupont')" 
            :key="card.id" 
            class="viz-card chart-card"
          >
            <div class="viz-card-header">
              <div class="viz-card-title">
                <span class="viz-card-icon">📊</span>
                <h3>{{ card.question || '数据可视化' }}</h3>
              </div>
              <div class="viz-card-actions">
                <button class="viz-card-close" @click="removeCard(card.id)" title="删除">×</button>
              </div>
            </div>
            <div class="viz-card-content">
              <div v-if="card.data && card.data.has_visualization" class="chart-card-content">
                <div :id="'chart-' + card.id" class="chart-container-inline"></div>
                
                <!-- 推荐说明 -->
                <div v-if="card.data.recommendation" class="recommendation-box">
                  <h4>📈 图表推荐</h4>
                  <p><strong>推荐图表类型:</strong> {{ getChartTypeName(card.data.recommendation.recommended_chart_type) }}</p>
                  <p><strong>推荐理由:</strong> {{ card.data.recommendation.reason }}</p>
                </div>
                
                <!-- 数据洞察 -->
                <div v-if="card.data.insights && card.data.insights.length > 0" class="insights-box">
                  <h3>💡 数据洞察</h3>
                  <div 
                    v-for="(insight, index) in card.data.insights" 
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
              <div v-else-if="card.data && card.data.error" class="error-message">
                <p>⚠️ 可视化生成失败: {{ card.data.error }}</p>
              </div>
            </div>
          </div>
          
          <!-- 当前查询的图表（向后兼容） -->
          <div v-if="chartData && chartData.has_visualization && !isCardInList(chartData)" class="viz-card chart-card">
            <div class="viz-card-header">
              <div class="viz-card-title">
                <span class="viz-card-icon">📊</span>
                <h3>数据可视化</h3>
              </div>
            </div>
            <div class="viz-card-content">
              <div id="visualizationChart" class="chart-container-inline"></div>
              
              <div v-if="hasRecommendation" class="recommendation-box">
                <h4>📈 图表推荐</h4>
                <p><strong>推荐图表类型:</strong> {{ getChartTypeName(chartData.recommendation.recommended_chart_type) }}</p>
                <p><strong>推荐理由:</strong> {{ chartData.recommendation.reason }}</p>
              </div>
              
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
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-else class="no-viz-message">
          <p>ℹ️ 暂无可视化数据。生成杜邦分析或进行包含数据的查询后，图表将在此显示。</p>
        </div>
      </div>
    </template>
  </Card>
</template>

<script>
import Card from './Card.vue'

// 递归树节点组件
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

DupontTreeNode.components = { DupontTreeNode }

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
    visualizationCards: { type: Array, default: () => [] },
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
             (this.dupontData && (this.dupontData.full_data || this.dupontData.roe)) ||
             (this.visualizationCards && this.visualizationCards.length > 0);
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
    removeCard(cardId) {
      // 清理Plotly图表实例（如果存在）
      if (window.Plotly) {
        try {
          const chartElement = document.getElementById(`chart-${cardId}`);
          if (chartElement) {
            window.Plotly.purge(chartElement);
          }
        } catch (error) {
          console.warn('清理图表失败:', error);
        }
      }
      // 触发删除事件
      this.$emit('remove-card', cardId);
    },
    removeDupontCard() {
      // 删除杜邦分析卡片：从cards中删除，并清空dupontData
      this.$emit('remove-dupont-card');
    },
    isCardInList(chartData) {
      // 检查当前chartData是否已经在cards列表中
      return this.visualizationCards.some(card => 
        card.data && card.data.chart_config && 
        chartData.chart_config &&
        JSON.stringify(card.data.chart_config) === JSON.stringify(chartData.chart_config)
      );
    },
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
    renderChart(cardId, chartData) {
      if (!chartData?.chart_config || !window.Plotly) {
        if (!window.Plotly) {
          console.warn('Plotly未加载，无法渲染图表');
        }
        return;
      }
      this.$nextTick(() => {
        try {
          const chartConfig = chartData.chart_config;
          const chartElementId = cardId ? `chart-${cardId}` : 'visualizationChart';
          
          // 检查DOM元素是否存在
          const chartElement = document.getElementById(chartElementId);
          if (!chartElement) {
            console.warn(`图表容器不存在: ${chartElementId}，延迟重试...`);
            // 如果元素不存在，延迟重试
            setTimeout(() => {
              this.renderChart(cardId, chartData);
            }, 200);
            return;
          }
          const traces = chartConfig.traces.map(trace => {
            const plotlyTrace = { 
              type: trace.type || 'scatter', 
              name: trace.name || '数据' 
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
            if (trace.type !== 'pie' && trace.text) plotlyTrace.text = trace.text;
            if (trace.textposition) plotlyTrace.textposition = trace.textposition;
            if (trace.hovertemplate) plotlyTrace.hovertemplate = trace.hovertemplate;
            return plotlyTrace;
          });
          const layout = {
            title: { 
              text: chartConfig.layout.title || '', 
              font: { size: 14, color: '#333' } 
            },
            xaxis: { 
              title: chartConfig.layout.xaxis_title || '', 
              gridcolor: '#e0e0e0' 
            },
            yaxis: { 
              title: chartConfig.layout.yaxis_title || '', 
              gridcolor: '#e0e0e0' 
            },
            height: 280,  // 固定高度，适配卡片
            template: chartConfig.layout.template || 'plotly_white',
            hovermode: chartConfig.layout.hovermode || 'closest',
            showlegend: chartConfig.layout.showlegend !== false,
            margin: { t: 40, r: 20, b: 50, l: 50 },  // 缩小边距，左右贴合
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            autosize: true  // 自动调整大小
          };
          const config = { 
            responsive: true, 
            displayModeBar: true, 
            displaylogo: false, 
            modeBarButtonsToRemove: ['lasso2d', 'select2d'] 
          };
          if (window.Plotly && window.Plotly.newPlot) {
            // 如果图表已存在，先清理
            try {
              const existingChart = document.getElementById(chartElementId);
              if (existingChart && existingChart.data) {
                window.Plotly.purge(chartElementId);
              }
            } catch (e) {
              // 忽略清理错误
            }
            
            window.Plotly.newPlot(chartElementId, traces, layout, config);
            console.log(`✅ 图表渲染成功: ${chartElementId}`);
          } else {
            console.warn('Plotly未加载，无法渲染图表');
          }
        } catch (error) {
          console.error('渲染图表失败:', error);
          const chartDiv = document.getElementById(cardId ? `chart-${cardId}` : 'visualizationChart');
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
          // 使用$nextTick确保DOM已更新
          this.$nextTick(() => {
            setTimeout(() => {
              this.renderChart(null, this.chartData);
            }, 100);
          });
        }
      }, 
      deep: true 
    },
    visualizationCards: {
      handler(newCards, oldCards) {
        // 为每个卡片渲染图表
        console.log('📊 visualizationCards变化:', {
          oldCount: oldCards?.length || 0,
          newCount: newCards?.length || 0,
          cards: newCards.map(c => ({ id: c.id, type: c.type, question: c.question, hasViz: c.data?.has_visualization }))
        });
        
        // 使用$nextTick确保DOM已更新
        this.$nextTick(() => {
          // 为所有图表类型的卡片渲染图表
          newCards.forEach(card => {
            if (card.data && card.data.has_visualization && card.type === 'chart') {
              // 延迟渲染，确保DOM元素已创建
              setTimeout(() => {
                console.log(`🎨 渲染图表卡片: ${card.id} - ${card.question}`);
                this.renderChart(card.id, card.data);
              }, 200);
            }
          });
        });
      },
      deep: true,
      immediate: true  // 立即执行一次
    },
    dupontData: {
      handler() {
        // 杜邦分析使用树状视图组件，不需要渲染 Plotly 图表
      },
      deep: true
    }
  }
}
</script>
