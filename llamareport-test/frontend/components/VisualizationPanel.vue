<template>
  <Card title="可视化视图" icon="📊" :status="status" empty-text="暂无可视化数据">
    <template #default>
      <div class="visualization-panel-container">
        <!-- 选择模式和生成总分析按钮 -->
        <div v-if="hasAnyVisualization" class="viz-controls">
          <button 
            class="toggle-select-btn" 
            :class="{ active: selectionMode }"
            @click="toggleSelectionMode"
          >
            {{ selectionMode ? '取消选择' : '选择卡片' }}
          </button>
          <button 
            v-if="selectionMode && selectedCards.length > 0"
            class="generate-analysis-btn"
            @click="generateComprehensiveAnalysis"
            :disabled="generatingAnalysis"
          >
            {{ generatingAnalysis ? '生成中...' : `生成总分析 (已选${selectedCards.length}个)` }}
          </button>
        </div>
        
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
            :class="{ 'selected': isCardSelected(card.id), 'selectable': selectionMode }"
            @click="handleCardClick(card.id, $event)"
          >
            <div class="viz-card-header">
              <div class="viz-card-title">
                <span v-if="selectionMode" class="selection-checkbox" :class="{ checked: isCardSelected(card.id) }">
                  {{ isCardSelected(card.id) ? '✓' : '' }}
                </span>
                <span class="viz-card-icon">📊</span>
                <h3>{{ card.question || '数据可视化' }}</h3>
              </div>
              <div class="viz-card-actions">
                <button class="viz-card-close" @click.stop="removeCard(card.id, $event)" title="删除">×</button>
              </div>
            </div>
            <div class="viz-card-content">
              <div v-if="card.data && card.data.has_visualization" class="chart-card-content">
                <!-- 财务表格 -->
                <div v-if="card.type === 'financial_table' && card.data.table" class="table-container">
                  <table class="financial-table">
                    <thead>
                      <tr>
                        <th v-for="(header, hIdx) in card.data.table.headers" :key="hIdx">
                          {{ header }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rIdx) in card.data.table.rows" :key="rIdx">
                        <td v-for="(cell, cIdx) in row" :key="cIdx">
                          {{ cell }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <!-- Timeline时间轴（纵向布局，紧凑型） -->
                <div v-else-if="card.data.visualization_type === 'timeline' && card.data.timeline_data" 
                     class="timeline-container">
                  <div class="custom-timeline">
                    <div 
                      v-for="(item, index) in card.data.timeline_data" 
                      :key="index"
                      class="timeline-item"
                      :class="{'timeline-item-left': index % 2 === 0, 'timeline-item-right': index % 2 === 1}">
                      <div class="timeline-dot" :style="{backgroundColor: getTimelineColor(item.color)}"></div>
                      <div class="timeline-content">
                        <div class="timeline-time" v-if="item.time">{{ item.time }}</div>
                        <div class="timeline-text">{{ item.content }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Plotly图表 -->
                <div v-else :id="'chart-' + card.id" class="chart-container-inline"></div>
                
                <!-- 综合能力分析文本 -->
                <div v-if="card.data.analysis_text" class="analysis-text-box">
                  <div v-html="formatAnalysisText(card.data.analysis_text)"></div>
                </div>
                
                <!-- 推荐说明 -->
                <div v-if="card.data.recommendation && card.type !== 'financial_table'" class="recommendation-box">
                  <h4>📈 图表推荐</h4>
                  <p><strong>推荐图表类型:</strong> 
                    <span>{{ getChartTypeName(getActualChartType(card.data)) }}</span>
                  </p>
                  <p><strong>推荐理由:</strong> {{ card.data.recommendation.reason }}</p>
                </div>
                
                <!-- 数据洞察 -->
                <div v-if="card.data.insights && card.data.insights.length > 0 && card.type !== 'financial_table'" class="insights-box">
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
  emits: ['remove-card', 'remove-dupont-card', 'generate-comprehensive-analysis'],
  data() {
    return {
      selectionMode: false,
      selectedCards: [],
      generatingAnalysis: false
    }
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
    removeCard(cardId, event) {
      // 阻止事件冒泡，确保不会触发卡片选择
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      
      console.log('🗑️ 删除卡片:', cardId);
      
      // 如果卡片在选中列表中，先移除
      const index = this.selectedCards.indexOf(cardId);
      if (index > -1) {
        this.selectedCards.splice(index, 1);
        console.log('  从选中列表中移除');
      }
      
      // 清理Plotly图表实例（如果存在）
      if (window.Plotly) {
        try {
          const chartElement = document.getElementById(`chart-${cardId}`);
          if (chartElement) {
            window.Plotly.purge(chartElement);
            console.log('  清理图表实例成功');
          }
        } catch (error) {
          console.warn('清理图表失败:', error);
        }
      }
      
      // 触发删除事件，删除整个卡片
      console.log('  触发删除事件，删除整个视图卡片');
      this.$emit('remove-card', cardId);
    },
    removeDupontCard() {
      // 删除杜邦分析卡片：从cards中删除，并清空dupontData
      this.$emit('remove-dupont-card');
    },
    isCardInList(chartData) {
      // 检查当前chartData是否已经在cards列表中
      if (!chartData || !chartData.has_visualization) {
        return false;
      }
      
      return this.visualizationCards.some(card => {
        if (!card.data || !card.data.has_visualization) {
          return false;
        }
        
        // 对于Plotly类型，比较chart_config
        if (chartData.chart_config && card.data.chart_config) {
          try {
            return JSON.stringify(card.data.chart_config) === JSON.stringify(chartData.chart_config);
          } catch (e) {
            // 如果JSON比较失败，使用更简单的比较
            return card.data.chart_config.chart_type === chartData.chart_config.chart_type;
          }
        }
        
        // 如果都没有配置，比较其他唯一标识符（如query）
        // 这里可以根据实际需求调整
        return false;
      });
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
      if (chartData?.type === 'financial_table') {
        return;
      }
      // 如果是Timeline类型，不需要渲染（由Vue模板直接渲染）
      if (chartData?.visualization_type === 'timeline' && chartData?.timeline_data) {
        console.log(`🎨 Timeline类型，由Vue模板直接渲染: ${cardId}`);
        return;
      }
      
      // Plotly图表渲染
      if (!chartData?.chart_config || !window.Plotly) {
        if (!window.Plotly) {
          console.warn('Plotly未加载，无法渲染图表');
        }
        if (!chartData?.chart_config) {
          console.warn(`⚠️ 缺少chart_config，跳过Plotly渲染: ${cardId}`);
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
          
          // 处理雷达图
          if (chartConfig.chart_type === 'radar' || (chartConfig.traces && chartConfig.traces[0]?.type === 'scatterpolar')) {
            this.renderRadarChart(chartElementId, chartConfig);
            return;
          }
          
          // 处理桑基图（Sankey Diagram）
          if (chartConfig.config && chartConfig.config.sankey_data) {
            this.renderSankeyChart(chartElementId, chartConfig);
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
    renderSankeyChart(chartElementId, chartConfig) {
      try {
        const sankeyData = chartConfig.config.sankey_data;
        const nodes = sankeyData.nodes || {};
        const links = sankeyData.links || {};
        
        // 创建Plotly Sankey trace（优化节点大小以适配视图卡片）
        const trace = {
          type: 'sankey',
          node: {
            pad: 10,  // 进一步减小节点间距（原15改为10）
            thickness: 18,  // 进一步减小节点厚度（原20改为18）
            line: { color: 'black', width: 0.5 },
            label: nodes.label || [],
            color: nodes.color || [],
            labelpadding: 3,  // 进一步减小标签内边距
            labelsuffix: ''  // 移除标签后缀
          },
          link: {
            source: links.source || [],
            target: links.target || [],
            value: links.value || [],
            color: 'rgba(0,0,0,0.15)'
          }
        };
        
        const layout = {
          title: {
            text: chartConfig.layout.title || '桑基图',
            font: { size: 13, color: '#333' }
          },
          height: 280,  // 减小高度以适配视图卡片（与普通图表一致）
          font: { size: 10 },  // 进一步减小字体大小
          margin: { t: 45, r: 15, b: 15, l: 15 },  // 减小边距
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
          try {
            const existingChart = document.getElementById(chartElementId);
            if (existingChart && existingChart.data) {
              window.Plotly.purge(chartElementId);
            }
          } catch (e) {
            // 忽略清理错误
          }
          
          window.Plotly.newPlot(chartElementId, [trace], layout, config);
          console.log(`✅ 桑基图渲染成功: ${chartElementId}`);
        } else {
          console.warn('Plotly未加载，无法渲染桑基图');
        }
      } catch (error) {
        console.error('渲染桑基图失败:', error);
        const chartDiv = document.getElementById(chartElementId);
        if (chartDiv) {
          const errorMsg = error.message || '未知错误';
          chartDiv.innerHTML = '<div class="error-message"><p>桑基图渲染失败: ' + errorMsg + '</p></div>';
        }
      }
    },
    renderRadarChart(chartElementId, chartConfig) {
      try {
        const trace = chartConfig.traces[0];
        const layout = chartConfig.layout || {};
        
        // 构建Plotly雷达图数据
        const plotlyTrace = {
          type: 'scatterpolar',
          r: trace.r || [],
          theta: trace.theta || [],
          fill: trace.fill || 'toself',
          mode: trace.mode || 'lines+markers',
          name: trace.name || '综合能力',
          line: trace.line || { color: 'rgb(55, 128, 191)', width: 2 },
          marker: trace.marker || { size: 6, color: 'rgb(55, 128, 191)' }
        };
        
        // 构建布局（优化大小和位置，适配卡片）
        const plotlyLayout = {
          polar: layout.polar || {
            radialaxis: {
              visible: true,
              range: [0, 100],
              tickmode: 'linear',
              tick0: 0,
              dtick: 20,
              tickfont: { size: 10 },
              gridcolor: '#e0e0e0',
              linecolor: '#999'
            },
            angularaxis: {
              rotation: 90,
              direction: 'counterclockwise',
              tickfont: { size: 11 }
            }
          },
          title: {
            text: layout.title || '综合能力分析雷达图',
            font: { size: 14, color: '#333' },
            x: 0.5,
            xanchor: 'center'
          },
          height: 350,  // 减小高度，适配卡片
          margin: { t: 50, r: 50, b: 50, l: 50 },  // 减小边距
          showlegend: layout.showlegend !== false,
          template: layout.template || 'plotly_white',
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)'
        };
        
        const config = {
          responsive: true,
          displayModeBar: false,  // 隐藏工具栏，节省空间
          displaylogo: false
        };
        
        // 清理旧图表
        try {
          const existingChart = document.getElementById(chartElementId);
          if (existingChart && existingChart.data) {
            window.Plotly.purge(chartElementId);
          }
        } catch (e) {
          // 忽略清理错误
        }
        
        window.Plotly.newPlot(chartElementId, [plotlyTrace], plotlyLayout, config);
        console.log(`✅ 雷达图渲染成功: ${chartElementId}`);
      } catch (error) {
        console.error('渲染雷达图失败:', error);
        const chartDiv = document.getElementById(chartElementId);
        if (chartDiv) {
          chartDiv.innerHTML = '<div class="error-message"><p>雷达图渲染失败: ' + error.message + '</p></div>';
        }
      }
    },
    getTimelineColor(color) {
      const colorMap = {
        'blue': '#1890ff',
        'green': '#52c41a',
        'red': '#ff4d4f',
        'gray': '#8c8c8c',
        'orange': '#fa8c16',
        'purple': '#722ed1'
      };
      return colorMap[color] || colorMap['blue'];
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
        'table': '表格',
        'radar': '雷达图',
        'timeline': '时间轴',
        'sankey': '桑基图'
      };
      return names[type] || type;
    },
    // 获取实际图表类型（考虑特殊图表类型）
    getActualChartType(cardData) {
      // 检查是否是桑基图
      if (cardData?.chart_config?.config?.sankey_data) {
        return 'sankey';
      }
      // 检查是否是时间轴
      if (cardData?.visualization_type === 'timeline' || cardData?.timeline_data) {
        return 'timeline';
      }
      // 检查是否是雷达图
      if (cardData?.chart_config?.chart_type === 'radar' || 
          (cardData?.chart_config?.traces && cardData.chart_config.traces[0]?.type === 'scatterpolar')) {
        return 'radar';
      }
      // 返回推荐的图表类型
      return cardData?.recommendation?.recommended_chart_type || 'bar';
    },
    formatAnalysisText(text) {
      if (!text) return '';
      // 将Markdown格式转换为HTML
      if (typeof marked !== 'undefined' && marked && marked.parse) {
        return marked.parse(text);
      }
      // 简单的文本格式化
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    },
    toggleSelectionMode() {
      this.selectionMode = !this.selectionMode
      if (!this.selectionMode) {
        this.selectedCards = []
      }
    },
    handleCardClick(cardId, event) {
      // 如果点击的是删除按钮，不处理选择逻辑
      if (event && event.target && (event.target.classList.contains('viz-card-close') || event.target.closest('.viz-card-close'))) {
        return
      }
      
      if (!this.selectionMode) return
      
      const index = this.selectedCards.indexOf(cardId)
      if (index > -1) {
        this.selectedCards.splice(index, 1)
      } else {
        this.selectedCards.push(cardId)
      }
    },
    isCardSelected(cardId) {
      return this.selectedCards.includes(cardId)
    },
    async generateComprehensiveAnalysis() {
      if (this.selectedCards.length === 0) {
        return
      }
      
      this.generatingAnalysis = true
      try {
        // 获取选中的卡片数据
        const selectedCardsData = this.visualizationCards.filter(card => 
          this.selectedCards.includes(card.id)
        )
        
        // 触发事件，传递选中的卡片数据
        this.$emit('generate-comprehensive-analysis', selectedCardsData)
      } catch (error) {
        console.error('生成总分析失败:', error)
        this.generatingAnalysis = false
      }
      // 注意：成功时generatingAnalysis会在父组件处理完成后重置
    },
    resetSelection() {
      // 重置选择状态（由父组件调用）
      this.selectedCards = []
      this.generatingAnalysis = false
    }
  },
  mounted() {
    // 监听重置选择事件
    window.addEventListener('reset-viz-selection', this.resetSelection)
  },
  beforeUnmount() {
    // 清理事件监听
    window.removeEventListener('reset-viz-selection', this.resetSelection)
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
                const vizType = card.data.visualization_type || 'plotly';
                console.log(`🎨 渲染图表卡片: ${card.id} - ${card.question} (类型: ${vizType})`);
                // 根据可视化类型决定渲染方式
                if (vizType === 'timeline' && card.data.timeline_data) {
                  // Timeline类型，由Vue模板直接渲染，不需要手动渲染
                  console.log(`✅ Timeline类型，由Vue模板渲染: ${card.id}`);
                } else if (vizType === 'plotly' && card.data.chart_config) {
                  // Plotly类型，只渲染Plotly
                  this.renderChart(card.id, card.data);
                } else {
                  console.warn(`⚠️ 卡片 ${card.id} 的可视化类型或数据不完整，跳过渲染`);
                }
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

<style scoped>
.viz-controls {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  padding: 4px 6px;
  background: #f9fafb;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.toggle-select-btn {
  padding: 4px 10px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
  color: #374151;
  transition: all 0.2s;
  line-height: 1.2;
}

.toggle-select-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.toggle-select-btn.active {
  background: #0284c7;
  color: white;
  border-color: #0284c7;
}

.generate-analysis-btn {
  padding: 4px 10px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
  line-height: 1.2;
}

.generate-analysis-btn:hover:not(:disabled) {
  background: #059669;
}

.generate-analysis-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.viz-card.selectable {
  cursor: pointer;
  transition: all 0.2s;
}

.viz-card.selectable:hover {
  border-color: #0284c7;
  box-shadow: 0 2px 8px rgba(2, 132, 199, 0.15);
}

.viz-card.selected {
  border: 2px solid #0284c7;
  background: #f0f9ff;
  box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
}

.selection-checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  margin-right: 8px;
  background: white;
  transition: all 0.2s;
}

.selection-checkbox.checked {
  background: #0284c7;
  border-color: #0284c7;
  color: white;
  font-weight: bold;
}

.analysis-text-box {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-left: 4px solid #0284c7;
  border-radius: 6px;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #0c4a6e;
}

.timeline-container {
  width: 100%;
  padding: 12px 20px;
  background: #fff;
  border-radius: 8px;
  overflow-x: auto;
}

/* 纵向时间轴布局（紧凑型） */
.custom-timeline {
  position: relative;
  padding: 10px 0;
  min-height: 100px;
}

.custom-timeline::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e8e8e8;
  transform: translateX(-50%);
}

.timeline-item {
  position: relative;
  margin-bottom: 20px;
  display: flex;
  align-items: flex-start;
  width: 50%;
  min-height: 40px;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-item-left {
  left: 0;
  flex-direction: row;
  padding-right: 35px;
  text-align: right;
}

.timeline-item-right {
  left: 50%;
  flex-direction: row-reverse;
  padding-left: 35px;
  text-align: left;
}

.timeline-dot {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #1890ff;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #e8e8e8;
  z-index: 2;
  flex-shrink: 0;
}

.timeline-item-left .timeline-dot {
  right: -5px;
  top: 2px;
}

.timeline-item-right .timeline-dot {
  left: -5px;
  top: 2px;
}

.timeline-content {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  word-break: break-word;
}

.timeline-time {
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
  font-size: 12px;
  line-height: 1.3;
}

.timeline-item-left .timeline-time {
  text-align: right;
}

.timeline-item-right .timeline-time {
  text-align: left;
}

.timeline-text {
  color: #333;
  line-height: 1.4;
  font-size: 12px;
  word-wrap: break-word;
  word-break: break-word;
}

.timeline-item-left .timeline-text {
  text-align: right;
}

.timeline-item-right .timeline-text {
  text-align: left;
}

/* 响应式优化：在小屏幕上调整布局 */
@media (max-width: 768px) {
  .timeline-item {
    width: 100%;
    margin-bottom: 15px;
  }
  
  .timeline-item-left,
  .timeline-item-right {
    left: 0;
    flex-direction: row;
    padding-left: 35px;
    padding-right: 0;
    text-align: left;
  }
  
  .timeline-item-left .timeline-dot,
  .timeline-item-right .timeline-dot {
    left: 15px;
    right: auto;
  }
  
  .custom-timeline::before {
    left: 20px;
  }
  
  .timeline-item-left .timeline-time,
  .timeline-item-right .timeline-time,
  .timeline-item-left .timeline-text,
  .timeline-item-right .timeline-text {
    text-align: left;
  }
}


.analysis-text-box :deep(strong) {
  color: #0284c7;
  font-weight: 600;
}

.analysis-text-box :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.analysis-text-box :deep(li) {
  margin: 4px 0;
}
</style>
