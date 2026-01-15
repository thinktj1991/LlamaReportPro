<template>
  <div class="agent-analysis-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <button class="back-btn" @click="goBack" title="返回主页">
        <span>←</span> 返回
      </button>
      <div class="page-title">
        <span class="page-icon">🤖</span>
        <h1>Agent 智能分析</h1>
      </div>
    </div>

    <!-- 问题输入区域 -->
    <div class="query-section">
      <div class="query-input-wrapper">
        <textarea 
          v-model="inputText" 
          class="query-input" 
          placeholder="输入您的问题，Agent将进行深度分析并生成完整报告..."
          rows="2"
          @keydown.ctrl.enter="handleSubmit"
        ></textarea>
        <button 
          class="submit-btn" 
          @click="handleSubmit" 
          :disabled="!inputText.trim() || loading"
        >
          <span v-if="!loading">🚀 开始分析</span>
          <span v-else class="loading-text">
            <span class="spinner-small"></span> 分析中...
          </span>
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-area" ref="contentArea">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
        <div class="loading-card">
          <div class="spinner-large"></div>
          <h3>Agent 正在分析中...</h3>
          <p>这可能需要1-3分钟，请耐心等待</p>
          <div class="progress-steps">
            <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
              <span class="step-icon">🔍</span>
              <span class="step-text">检索相关数据</span>
            </div>
            <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
              <span class="step-icon">⚙️</span>
              <span class="step-text">调用工具分析</span>
            </div>
            <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
              <span class="step-icon">📊</span>
              <span class="step-text">生成结构化回答</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && !hasContent" class="empty-container">
        <div class="empty-card">
          <div class="empty-icon">🤖</div>
          <h2>开始您的智能分析</h2>
          <p>输入问题，Agent将为您生成完整的分析报告</p>
          <div class="suggestions">
            <div class="suggestion-title">💡 推荐问题：</div>
            <button 
              v-for="(suggestion, idx) in defaultSuggestions" 
              :key="idx"
              class="suggestion-btn"
              @click="useSuggestion(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>
      </div>

            <!-- 内容展示区域 -->
            <div v-if="!loading && hasContent" class="results-container">
              <!-- 调试信息（开发环境） -->
              <div v-if="false" class="debug-info" style="background: #f0f0f0; padding: 10px; margin-bottom: 20px; font-size: 12px;">
                <strong>调试信息:</strong><br>
                hasContent: {{ hasContent }}<br>
                hasAnswer: {{ !!answer }}<br>
                answerLength: {{ answer?.length || 0 }}<br>
                visualizationsCount: {{ visualizations.length }}<br>
                hasFinancialReview: {{ !!structuredData.financialReview }}<br>
                hasBusinessHighlights: {{ !!structuredData.businessHighlights }}<br>
                hasBusinessGuidance: {{ !!structuredData.businessGuidance }}<br>
                hasDupontAnalysis: {{ !!structuredData.dupontAnalysis }}
              </div>
              
              <!-- 问题卡片 -->
              <div v-if="currentQuestion" class="question-card">
                <div class="question-header">
                  <span class="question-icon">❓</span>
                  <h3>分析问题</h3>
                </div>
                <div class="question-content">{{ currentQuestion }}</div>
              </div>

              <!-- 文本回答 -->
              <div v-if="answer" class="answer-card">
          <div class="answer-header">
            <div class="answer-header-left">
              <span class="answer-icon">📝</span>
              <h3>分析结果</h3>
            </div>
            <div class="answer-header-actions">
              <button class="action-btn" @click="copyAnswer" title="复制内容">
                <span>📋</span> 复制
              </button>
              <button class="action-btn" @click="exportReport" title="导出报告">
                <span>💾</span> 导出
              </button>
            </div>
          </div>
          <div class="answer-content" v-html="parseMarkdown(answer)"></div>
        </div>

        <!-- 可视化图表区域 -->
        <div v-if="visualizations.length > 0" class="visualizations-section">
          <div class="section-header">
            <span class="section-icon">📊</span>
            <h2>数据可视化</h2>
            <span class="section-count">{{ visualizations.length }}</span>
          </div>
          <div class="visualizations-grid">
            <div 
              v-for="(viz, idx) in visualizations" 
              :key="viz.id || idx"
              class="visualization-card"
            >
              <div class="viz-card-header">
                <h4>{{ viz.question || '数据图表' }}</h4>
                <button class="viz-close-btn" @click="removeVisualization(idx)" title="删除">×</button>
              </div>
              <div class="viz-card-content">
                <div v-if="viz.data?.type === 'financial_table' && viz.data?.table" class="table-container">
                  <table class="financial-table">
                    <thead>
                      <tr>
                        <th v-for="(header, hIdx) in viz.data.table.headers" :key="hIdx">
                          {{ header }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rIdx) in viz.data.table.rows" :key="rIdx">
                        <td v-for="(cell, cIdx) in row" :key="cIdx">
                          {{ cell }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else :id="'agent-viz-' + (viz.id || idx)" class="chart-container"></div>
                
                <!-- 推荐说明 -->
                <div v-if="viz.data?.recommendation && viz.data?.type !== 'financial_table'" class="recommendation-box">
                  <h5>📈 图表推荐</h5>
                  <p><strong>类型:</strong> {{ getChartTypeName(viz.data.recommendation.recommended_chart_type) }}</p>
                  <p><strong>理由:</strong> {{ viz.data.recommendation.reason }}</p>
                </div>
                
                <!-- 数据洞察 -->
                <div v-if="viz.data?.insights && viz.data.insights.length > 0 && viz.data?.type !== 'financial_table'" class="insights-box">
                  <h5>💡 数据洞察</h5>
                  <div 
                    v-for="(insight, i) in viz.data.insights" 
                    :key="i" 
                    class="insight-item"
                  >
                    <h6>
                      {{ getInsightIcon(insight.insight_type) }} 
                      {{ insight.description }}
                    </h6>
                    <ul v-if="insight.key_findings && insight.key_findings.length > 0">
                      <li v-for="(finding, j) in insight.key_findings" :key="j">
                        {{ finding }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 结构化数据区域 -->
        <div v-if="hasStructuredData" class="structured-data-section">
          <div class="section-header">
            <span class="section-icon">📋</span>
            <h2>结构化分析</h2>
          </div>
          <div class="structured-grid">
            <!-- 财务点评 -->
            <div v-if="structuredData.financialReview" class="data-card financial-review">
              <div class="data-card-header">
                <span class="data-icon">💰</span>
                <h3>财务点评</h3>
              </div>
              <div class="data-card-content" v-html="parseMarkdown(structuredData.financialReview)"></div>
            </div>

            <!-- 业务亮点 -->
            <div v-if="structuredData.businessHighlights" class="data-card business-highlights">
              <div class="data-card-header">
                <span class="data-icon">⭐</span>
                <h3>业务亮点</h3>
              </div>
              <div class="data-card-content" v-html="parseMarkdown(structuredData.businessHighlights)"></div>
            </div>

            <!-- 业绩指引 -->
            <div v-if="structuredData.businessGuidance" class="data-card business-guidance">
              <div class="data-card-header">
                <span class="data-icon">🎯</span>
                <h3>业绩指引</h3>
              </div>
              <div class="data-card-content" v-html="parseMarkdown(structuredData.businessGuidance)"></div>
            </div>

            <!-- 杜邦分析 -->
            <div v-if="structuredData.dupontAnalysis" class="data-card dupont-analysis">
              <div class="data-card-header">
                <span class="data-icon">📊</span>
                <h3>杜邦分析</h3>
              </div>
              <div class="data-card-content">
                <div v-if="structuredData.dupontAnalysis.full_data" class="dupont-content">
                  <div class="dupont-metrics">
                    <div class="metric-item">
                      <span class="metric-label">ROE</span>
                      <span class="metric-value">{{ getDupontValue(structuredData.dupontAnalysis, 'roe') }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">ROA</span>
                      <span class="metric-value">{{ getDupontValue(structuredData.dupontAnalysis, 'roa') }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">权益乘数</span>
                      <span class="metric-value">{{ getDupontValue(structuredData.dupontAnalysis, 'equity_multiplier') }}</span>
                    </div>
                  </div>
                  <div v-if="structuredData.dupontAnalysis.full_data?.insights" class="dupont-insights">
                    <h4>分析洞察</h4>
                    <ul>
                      <li v-for="(insight, i) in structuredData.dupontAnalysis.full_data.insights" :key="i">
                        {{ insight }}
                      </li>
                    </ul>
                  </div>
                </div>
                <div v-else class="dupont-simple">
                  <p>ROE: {{ structuredData.dupontAnalysis.roe || '—' }}</p>
                  <p>ROA: {{ structuredData.dupontAnalysis.roa || '—' }}</p>
                  <p>权益乘数: {{ structuredData.dupontAnalysis.equity_multiplier || '—' }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AgentAnalysisPage',
  props: {
    onBack: { type: Function, required: true },
    onQuery: { type: Function, required: true }
  },
  data() {
    return {
      inputText: '',
      loading: false,
      currentQuestion: '',
      answer: '',
      visualizations: [],
      structuredData: {
        financialReview: null,
        businessHighlights: null,
        businessGuidance: null,
        dupontAnalysis: null
      },
      currentStep: 0,
      defaultSuggestions: [
        '请生成完整的年报分析报告，包括财务点评、业绩指引、业务亮点和盈利预测',
        '分析这家公司的财务状况和盈利能力',
        '进行杜邦分析，深入分析ROE的驱动因素',
        '对比分析近三年的财务指标变化趋势',
        '分析公司的业务亮点和主要成就',
        '评估公司的盈利预测和估值水平'
      ],
      showExportMenu: false
    }
  },
  computed: {
    hasContent() {
      const hasAnswer = this.answer && this.answer.trim().length > 0
      const hasViz = this.visualizations && this.visualizations.length > 0
      const hasStructured = this.hasStructuredData
      
      const result = hasAnswer || hasViz || hasStructured
      
      // 调试日志（只在状态变化时输出，避免过多日志）
      if (result && !this._lastHasContent) {
        console.log('✅ [AgentAnalysisPage] hasContent 变为 true:', {
          hasAnswer,
          hasViz,
          hasStructured,
          answerLength: this.answer?.length || 0,
          visualizationsCount: this.visualizations?.length || 0,
          structuredDataKeys: Object.keys(this.structuredData).filter(k => this.structuredData[k])
        })
      }
      this._lastHasContent = result
      
      return result
    },
    hasStructuredData() {
      return this.structuredData.financialReview || 
             this.structuredData.businessHighlights || 
             this.structuredData.businessGuidance || 
             this.structuredData.dupontAnalysis
    }
  },
  methods: {
    goBack() {
      this.onBack()
    },
    async handleSubmit() {
      if (!this.inputText.trim() || this.loading) return
      
      const question = this.inputText.trim()
      this.inputText = ''
      this.currentQuestion = question
      this.loading = true
      this.currentStep = 0
      
      // 清空之前的结果
      this.answer = ''
      this.visualizations = []
      this.structuredData = {
        financialReview: null,
        businessHighlights: null,
        businessGuidance: null,
        dupontAnalysis: null
      }
      
      // 模拟进度步骤 - 更智能的进度更新
      const stepInterval = setInterval(() => {
        if (this.currentStep < 3) {
          this.currentStep++
        }
      }, 3000)  // 每3秒更新一次，更符合实际处理时间
      
      try {
        const result = await this.onQuery(question)
        
        clearInterval(stepInterval)
        this.currentStep = 3
        
        // 添加调试日志
        console.log('🔍 [AgentAnalysisPage] 收到响应:', {
          status: result.status,
          hasAnswer: !!result.answer,
          answerLength: result.answer?.length || 0,
          toolCallsCount: result.tool_calls?.length || 0,
          hasVisualization: !!result.visualization,
          hasStructuredResponse: !!result.structured_response
        })
        
        if (result.status === 'success') {
          // 设置文本回答 - 确保有内容
          if (result.answer && result.answer.trim()) {
            this.answer = result.answer
            console.log('✅ [AgentAnalysisPage] 设置文本回答，长度:', this.answer.length)
          } else {
            // 如果没有answer，尝试从工具调用中提取
            if (result.tool_calls && result.tool_calls.length > 0) {
              this.answer = `✅ Agent分析完成，共执行了 ${result.tool_calls.length} 个工具调用。\n\n请查看下方的结构化数据卡片。`
              console.log('⚠️ [AgentAnalysisPage] 没有answer，使用默认提示')
            } else {
              this.answer = '✅ Agent分析完成，但未返回详细内容。'
            }
          }
          
          // 处理可视化
          if (result.visualization && result.visualization.has_visualization) {
            console.log('📊 [AgentAnalysisPage] 添加可视化数据')
            if (result.visualization.type === 'financial_tables' && Array.isArray(result.visualization.tables)) {
              result.visualization.tables
                .filter(table => table)
                .forEach((table, idx) => {
                  this.visualizations.push({
                    id: `${Date.now().toString()}-${idx}`,
                    question: table.title || '财务表格',
                    data: {
                      has_visualization: true,
                      type: 'financial_table',
                      table
                    }
                  })
                })
            } else {
              this.visualizations.push({
                id: Date.now().toString(),
                question: question,
                data: result.visualization
              })
            }
          }
          
          // 处理工具调用结果 - 优先处理
          if (result.tool_calls && Array.isArray(result.tool_calls)) {
            console.log(`🔧 [AgentAnalysisPage] 处理 ${result.tool_calls.length} 个工具调用`)
            result.tool_calls.forEach((toolCall, index) => {
              const toolName = toolCall.tool_name
              // 从工具调用中提取实际输出（可能是 raw_output 字段）
              let toolOutput = toolCall.tool_output
              
              // 如果 tool_output 是包含 raw_output 的对象，提取它
              if (toolOutput && typeof toolOutput === 'object' && toolOutput.raw_output !== undefined) {
                toolOutput = toolOutput.raw_output
                console.log(`  [${index + 1}] 从 tool_output.raw_output 提取内容`)
              }
              
              console.log(`  [${index + 1}] 工具: ${toolName}`, {
                hasOutput: !!toolOutput,
                outputType: typeof toolOutput,
                hasError: !!(toolOutput && toolOutput.error)
              })
              
              // 跳过错误输出
              if (toolOutput && toolOutput.error) {
                console.warn(`⚠️ 工具 ${toolName} 执行失败:`, toolOutput.error)
                return
              }
              
              // 处理各种工具的输出
              // 辅助函数：从工具输出中提取文本内容
              const extractTextFromToolOutput = (output) => {
                if (!output) return null
                
                // 如果是字符串，直接返回
                if (typeof output === 'string') {
                  return output
                }
                
                // 如果是对象，尝试提取文本字段
                if (typeof output === 'object') {
                  // 优先查找常见的文本字段
                  if (output.raw_output && typeof output.raw_output === 'string') {
                    return output.raw_output
                  }
                  if (output.content && typeof output.content === 'string') {
                    return output.content
                  }
                  if (output.text && typeof output.text === 'string') {
                    return output.text
                  }
                  if (output.answer && typeof output.answer === 'string') {
                    return output.answer
                  }
                  // 如果有 summary 或 report 字段
                  if (output.summary && typeof output.summary === 'string') {
                    return output.summary
                  }
                  if (output.report && typeof output.report === 'string') {
                    return output.report
                  }
                  // 如果是包含 blocks 的对象（LlamaIndex 格式）
                  if (output.blocks && Array.isArray(output.blocks)) {
                    return output.blocks.map(block => {
                      if (typeof block === 'string') return block
                      if (block.text) return block.text
                      if (block.content) return block.content
                      return JSON.stringify(block)
                    }).join('\n\n')
                  }
                  // 最后尝试 JSON 序列化（用于调试）
                  console.warn('⚠️ [AgentAnalysisPage] 无法从工具输出中提取文本，使用 JSON 格式:', output)
                  return JSON.stringify(output, null, 2)
                }
                
                // 其他类型转换为字符串
                return String(output)
              }
              
              if (toolName === 'generate_dupont_analysis' && toolOutput) {
                // 杜邦分析保持为对象（需要特殊处理）
                this.structuredData.dupontAnalysis = toolOutput
                console.log('✅ [AgentAnalysisPage] 设置杜邦分析数据')
              } else if (toolName === 'generate_financial_review' && toolOutput) {
                // 提取文本内容
                const textContent = extractTextFromToolOutput(toolOutput)
                this.structuredData.financialReview = textContent || toolOutput
                console.log('✅ [AgentAnalysisPage] 设置财务点评数据', typeof textContent === 'string' ? `(文本，长度: ${textContent.length})` : '(对象)')
              } else if (toolName === 'generate_business_highlights' && toolOutput) {
                const textContent = extractTextFromToolOutput(toolOutput)
                this.structuredData.businessHighlights = textContent || toolOutput
                console.log('✅ [AgentAnalysisPage] 设置业务亮点数据', typeof textContent === 'string' ? `(文本，长度: ${textContent.length})` : '(对象)')
              } else if (toolName === 'generate_business_guidance' && toolOutput) {
                const textContent = extractTextFromToolOutput(toolOutput)
                this.structuredData.businessGuidance = textContent || toolOutput
                console.log('✅ [AgentAnalysisPage] 设置业绩指引数据', typeof textContent === 'string' ? `(文本，长度: ${textContent.length})` : '(对象)')
              } else if (toolName === 'generate_visualization' && toolOutput && toolOutput.has_visualization) {
                this.visualizations.push({
                  id: Date.now().toString() + '-' + this.visualizations.length,
                  question: question,
                  data: toolOutput
                })
                console.log('✅ [AgentAnalysisPage] 添加可视化数据（从工具调用）')
              } else if (toolName === 'generate_profit_forecast_and_valuation' && toolOutput) {
                // 盈利预测数据可以存储在其他地方或合并到结构化数据中
                console.log('✅ [AgentAnalysisPage] 收到盈利预测数据')
              }
            })
          }
          
          // 处理结构化响应（备用）
          if (result.structured_response) {
            console.log('📋 [AgentAnalysisPage] 处理结构化响应')
            const structured = result.structured_response
            if (structured.dupont_analysis) {
              this.structuredData.dupontAnalysis = structured.dupont_analysis
            }
            if (structured.financial_review) {
              this.structuredData.financialReview = structured.financial_review
            }
            if (structured.business_highlights) {
              this.structuredData.businessHighlights = structured.business_highlights
            }
            if (structured.business_guidance) {
              this.structuredData.businessGuidance = structured.business_guidance
            }
          }
          
          // 先设置loading为false，确保UI能切换到结果视图
          this.loading = false
          
          // 确保数据已设置完成
          console.log('📋 [AgentAnalysisPage] 数据设置完成，准备渲染:', {
            answer: this.answer?.substring(0, 100),
            visualizationsCount: this.visualizations.length,
            structuredData: Object.keys(this.structuredData).filter(k => this.structuredData[k])
          })
          
          // 强制触发响应式更新
          this.$forceUpdate()
          
          // 渲染图表
          this.$nextTick(() => {
            console.log('🎨 [AgentAnalysisPage] 开始渲染图表')
            this.renderAllCharts()
            
            // 检查最终状态
            console.log('📊 [AgentAnalysisPage] 最终状态:', {
              loading: this.loading,
              hasAnswer: !!this.answer,
              answerLength: this.answer?.length || 0,
              visualizationsCount: this.visualizations.length,
              hasFinancialReview: !!this.structuredData.financialReview,
              hasBusinessHighlights: !!this.structuredData.businessHighlights,
              hasBusinessGuidance: !!this.structuredData.businessGuidance,
              hasDupontAnalysis: !!this.structuredData.dupontAnalysis,
              hasStructuredData: this.hasStructuredData,
              hasContent: this.hasContent
            })
            
            // 如果还是没有内容，再次检查
            if (!this.hasContent) {
              console.warn('⚠️ [AgentAnalysisPage] 警告：数据已设置但hasContent仍为false')
              console.warn('数据详情:', {
                answer: this.answer,
                structuredData: this.structuredData,
                visualizations: this.visualizations
              })
            }
          })
        } else {
          const errorMsg = result.error || result.detail || '未知错误'
          this.answer = `❌ 分析失败: ${errorMsg}`
          this.loading = false
          console.error('❌ [AgentAnalysisPage] 分析失败:', errorMsg)
        }
      } catch (error) {
        clearInterval(stepInterval)
        const errorMsg = error.message || '网络错误'
        this.answer = `❌ 分析失败: ${errorMsg}`
        this.loading = false
        console.error('❌ [AgentAnalysisPage] 异常:', error)
      } finally {
        // 确保loading被设置为false
        if (this.loading) {
          this.loading = false
        }
        this.currentStep = 0
        console.log('🏁 [AgentAnalysisPage] 查询完成，loading设置为false')
        
        // 最终检查
        this.$nextTick(() => {
          console.log('🔍 [AgentAnalysisPage] finally后的状态检查:', {
            loading: this.loading,
            hasContent: this.hasContent,
            hasAnswer: !!this.answer,
            hasStructuredData: this.hasStructuredData
          })
        })
      }
    },
    useSuggestion(suggestion) {
      this.inputText = suggestion
      this.$nextTick(() => {
        const textarea = this.$el.querySelector('.query-input')
        if (textarea) {
          textarea.focus()
        }
      })
    },
    parseMarkdown(text) {
      // 确保输入是字符串类型
      if (!text) {
        return ''
      }
      
      // 如果是对象，尝试转换为字符串
      if (typeof text === 'object') {
        console.warn('⚠️ [AgentAnalysisPage] parseMarkdown 收到对象类型，尝试转换:', text)
        try {
          // 尝试提取可能的文本字段
          if (text.answer) {
            text = text.answer
          } else if (text.content) {
            text = text.content
          } else if (text.text) {
            text = text.text
          } else {
            // 如果都没有，尝试 JSON 序列化（仅用于调试）
            text = JSON.stringify(text, null, 2)
          }
        } catch (e) {
          console.error('❌ [AgentAnalysisPage] 对象转换失败:', e)
          text = String(text)
        }
      }
      
      // 确保是字符串
      if (typeof text !== 'string') {
        text = String(text)
      }
      
      // 使用 marked 解析
      if (typeof marked !== 'undefined' && marked && marked.parse) {
        try {
          return marked.parse(text)
        } catch (e) {
          console.error('❌ [AgentAnalysisPage] marked.parse 失败:', e, '输入类型:', typeof text, '输入长度:', text.length)
          // 如果 marked 解析失败，返回原始文本（转义 HTML）
          return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
        }
      } else {
        // 如果 marked 不可用，返回转义后的文本
        return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
      }
    },
    removeVisualization(index) {
      const viz = this.visualizations[index]
      if (viz && window.Plotly) {
        try {
          const chartElement = document.getElementById(`agent-viz-${viz.id || index}`)
          if (chartElement) {
            window.Plotly.purge(chartElement)
          }
        } catch (error) {
          console.warn('清理图表失败:', error)
        }
      }
      this.visualizations.splice(index, 1)
    },
    renderAllCharts() {
      this.visualizations.forEach((viz, idx) => {
        if (viz.data && viz.data.has_visualization && viz.data.type !== 'financial_table') {
          setTimeout(() => {
            this.renderChart(viz.id || idx, viz.data)
          }, 100 * (idx + 1))
        }
      })
    },
    renderChart(cardId, chartData) {
      if (!chartData?.chart_config || !window.Plotly) {
        return
      }
      
      this.$nextTick(() => {
        try {
          const chartConfig = chartData.chart_config
          const chartElementId = `agent-viz-${cardId}`
          const chartElement = document.getElementById(chartElementId)
          
          if (!chartElement) {
            setTimeout(() => {
              this.renderChart(cardId, chartData)
            }, 200)
            return
          }
          
          const traces = chartConfig.traces.map(trace => {
            const plotlyTrace = { 
              type: trace.type || 'scatter', 
              name: trace.name || '数据' 
            }
            if (trace.type === 'pie') {
              plotlyTrace.labels = trace.text || []
              plotlyTrace.values = trace.y || []
            } else {
              plotlyTrace.x = trace.x || []
              plotlyTrace.y = trace.y || []
            }
            if (trace.mode) plotlyTrace.mode = trace.mode
            if (trace.marker) plotlyTrace.marker = trace.marker
            if (trace.line) plotlyTrace.line = trace.line
            if (trace.type !== 'pie' && trace.text) plotlyTrace.text = trace.text
            if (trace.textposition) plotlyTrace.textposition = trace.textposition
            if (trace.hovertemplate) plotlyTrace.hovertemplate = trace.hovertemplate
            return plotlyTrace
          })
          
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
            margin: { t: 50, r: 30, b: 60, l: 60 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            autosize: true
          }
          
          const config = { 
            responsive: true, 
            displayModeBar: true, 
            displaylogo: false, 
            modeBarButtonsToRemove: ['lasso2d', 'select2d'] 
          }
          
          if (window.Plotly && window.Plotly.newPlot) {
            try {
              window.Plotly.purge(chartElementId)
            } catch (e) {}
            
            window.Plotly.newPlot(chartElementId, traces, layout, config)
          }
        } catch (error) {
          console.error('渲染图表失败:', error)
        }
      })
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
        'box': '箱线图'
      }
      return names[type] || type
    },
    getInsightIcon(type) {
      const icons = {
        'trend': '📈',
        'comparison': '⚖️',
        'distribution': '📊',
        'correlation': '🔗',
        'anomaly': '⚠️'
      }
      return icons[type] || '💡'
    },
    getDupontValue(data, metric) {
      if (!data) return '—'
      if (data.full_data && data.full_data.level1 && data.full_data.level1[metric]) {
        const metricObj = data.full_data.level1[metric]
        return metricObj.formatted_value || metricObj.value || '—'
      }
      return data[metric] || '—'
    },
    copyAnswer() {
      if (!this.answer) return
      
      // 创建临时文本区域
      const textarea = document.createElement('textarea')
      textarea.value = this.answer.replace(/<[^>]*>/g, '') // 移除HTML标签
      document.body.appendChild(textarea)
      textarea.select()
      
      try {
        document.execCommand('copy')
        this.showToast('已复制到剪贴板', 'success')
      } catch (err) {
        this.showToast('复制失败', 'error')
      }
      
      document.body.removeChild(textarea)
    },
    exportReport() {
      if (!this.hasContent) {
        this.showToast('没有可导出的内容', 'warning')
        return
      }
      
      // 构建报告内容
      let reportContent = `# ${this.currentQuestion || 'Agent分析报告'}\n\n`
      reportContent += `生成时间: ${new Date().toLocaleString('zh-CN')}\n\n`
      
      if (this.answer) {
        reportContent += `## 分析结果\n\n${this.answer.replace(/<[^>]*>/g, '')}\n\n`
      }
      
      if (this.structuredData.financialReview) {
        reportContent += `## 财务点评\n\n${JSON.stringify(this.structuredData.financialReview, null, 2)}\n\n`
      }
      
      if (this.structuredData.businessHighlights) {
        reportContent += `## 业务亮点\n\n${JSON.stringify(this.structuredData.businessHighlights, null, 2)}\n\n`
      }
      
      if (this.structuredData.businessGuidance) {
        reportContent += `## 业绩指引\n\n${JSON.stringify(this.structuredData.businessGuidance, null, 2)}\n\n`
      }
      
      if (this.structuredData.dupontAnalysis) {
        reportContent += `## 杜邦分析\n\n${JSON.stringify(this.structuredData.dupontAnalysis, null, 2)}\n\n`
      }
      
      // 创建Blob并下载
      const blob = new Blob([reportContent], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Agent分析报告_${new Date().getTime()}.md`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      this.showToast('报告导出成功', 'success')
    },
    showToast(message, type = 'info') {
      // 简单的toast提示
      const toast = document.createElement('div')
      toast.className = `agent-toast agent-toast-${type}`
      toast.textContent = message
      document.body.appendChild(toast)
      
      setTimeout(() => {
        toast.classList.add('show')
      }, 10)
      
      setTimeout(() => {
        toast.classList.remove('show')
        setTimeout(() => {
          document.body.removeChild(toast)
        }, 300)
      }, 2000)
    }
  }
}
</script>

<style scoped>
.agent-analysis-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 32px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.back-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.back-btn:hover {
  background: rgba(255,255,255,0.3);
  transform: translateX(-2px);
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-icon {
  font-size: 28px;
}

.page-title h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

/* 问题输入区域 */
.query-section {
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.query-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.query-input {
  flex: 1;
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  font-family: inherit;
  resize: none;
  transition: all 0.3s ease;
  line-height: 1.5;
}

.query-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-btn {
  padding: 14px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  min-height: 0;
}

/* 加载状态 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  max-width: 600px;
  width: 100%;
}

.spinner-large {
  width: 64px;
  height: 64px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 24px;
}

.loading-card h3 {
  font-size: 20px;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.loading-card p {
  color: #6b7280;
  margin: 0 0 32px 0;
}

.progress-steps {
  display: flex;
  justify-content: space-around;
  gap: 16px;
  margin-top: 32px;
}

.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.step.active {
  opacity: 1;
  transform: scale(1.05);
}

.step.completed .step-icon {
  background: #10b981;
  color: white;
}

.step.active .step-icon {
  background: #667eea;
  color: white;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.step-icon {
  font-size: 24px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3f4f6;
  transition: all 0.3s ease;
}

.step-text {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

/* 空状态 */
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  max-width: 600px;
  width: 100%;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.empty-card h2 {
  font-size: 24px;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.empty-card p {
  color: #6b7280;
  margin: 0 0 32px 0;
}

.suggestions {
  text-align: left;
}

.suggestion-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.suggestion-btn {
  display: block;
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #374151;
}

.suggestion-btn:hover {
  background: #f3f4f6;
  border-color: #667eea;
  transform: translateX(4px);
}

/* 结果容器 */
.results-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 问题卡片 */
.question-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-left: 4px solid #667eea;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.question-icon {
  font-size: 20px;
}

.question-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.question-content {
  font-size: 16px;
  color: #374151;
  line-height: 1.6;
}

/* 回答卡片 */
.answer-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.answer-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.answer-header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-btn:hover {
  background: #e5e7eb;
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
}

.answer-icon {
  font-size: 24px;
}

.answer-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.answer-content {
  font-size: 15px;
  color: #374151;
  line-height: 1.8;
}

.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3) {
  color: #1f2937;
  margin-top: 24px;
  margin-bottom: 12px;
}

.answer-content :deep(p) {
  margin-bottom: 12px;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin-left: 24px;
  margin-bottom: 12px;
}

.answer-content :deep(li) {
  margin-bottom: 6px;
}

/* 可视化区域 */
.visualizations-section {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.section-icon {
  font-size: 24px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  flex: 1;
}

.section-count {
  background: #667eea;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.visualizations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
}

.visualization-card {
  background: #f9fafb;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
}

.viz-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.viz-card-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.viz-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.viz-close-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin-bottom: 16px;
}

.recommendation-box,
.insights-box {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.recommendation-box h5,
.insights-box h5 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.recommendation-box p {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0;
}

.insight-item {
  margin-bottom: 16px;
}

.insight-item h6 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.insight-item ul {
  margin-left: 20px;
  margin-top: 8px;
}

.insight-item li {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

/* 结构化数据区域 */
.structured-data-section {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.structured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.data-card {
  background: #f9fafb;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.data-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.data-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.data-icon {
  font-size: 20px;
}

.data-card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.data-card-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}

.data-card-content :deep(p) {
  margin-bottom: 12px;
}

.data-card-content :deep(ul),
.data-card-content :deep(ol) {
  margin-left: 20px;
  margin-bottom: 12px;
}

/* 杜邦分析特殊样式 */
.dupont-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dupont-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e5e7eb;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.metric-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #667eea;
}

.dupont-insights {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.dupont-insights h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.dupont-insights ul {
  margin: 0;
  padding-left: 20px;
}

.dupont-insights li {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 6px;
}

.dupont-simple p {
  margin: 8px 0;
  font-size: 14px;
  color: #374151;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Toast 提示 */
.agent-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: #667eea;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 10000;
  opacity: 0;
  transform: translateX(100%);
  transition: all 0.3s ease;
}

.agent-toast.show {
  opacity: 1;
  transform: translateX(0);
}

.agent-toast-success {
  background: #10b981;
}

.agent-toast-error {
  background: #ef4444;
}

.agent-toast-warning {
  background: #f59e0b;
}

.agent-toast-info {
  background: #667eea;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .visualizations-grid {
    grid-template-columns: 1fr;
  }
  
  .structured-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .query-section {
    padding: 16px 20px;
  }
  
  .content-area {
    padding: 20px;
  }
  
  .query-input-wrapper {
    flex-direction: column;
  }
  
  .submit-btn {
    width: 100%;
  }
}
</style>

