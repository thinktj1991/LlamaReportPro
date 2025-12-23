import { createApp } from 'vue'
import { ref, reactive, onMounted } from 'vue'

// 导入组件
import Card from './components/Card.vue'
import FilePreviewCard from './components/FilePreviewCard.vue'
import ChatArea from './components/ChatArea.vue'
import CompanyOverview from './components/CompanyOverview.vue'
import NotesAndRisks from './components/NotesAndRisks.vue'
import DupontAnalysis from './components/DupontAnalysis.vue'
import VisualizationPanel from './components/VisualizationPanel.vue'
import MessageToast from './components/MessageToast.vue'

// 导入样式
import './style.css'

// 主应用组件
const App = {
  setup() {
    const systemStatus = ref('检查中...')
    const files = ref([])
    const selectedFile = ref(null)
    const chatMessages = ref([])
    const queryLoading = ref(false)
    const message = reactive({ type: '', text: '' })
    const companyOverviewData = ref(null)
    const companyOverviewLoading = ref(false)
    const notesAndRisksData = ref(null)
    const notesAndRisksLoading = ref(false)
    const dupontData = ref(null)
    const dupontLoading = ref(false)
    const visualizationData = ref(null)
    const visualizationLoading = ref(false)
    const processStatus = ref(null)
    const suggestions = ref([])
    
    const checkSystemStatus = async () => {
      try {
        const response = await fetch('/health')
        const data = await response.json()
        systemStatus.value = data.status === 'healthy' ? '✅ 系统正常运行' : '⚠️ 系统状态异常'
      } catch (error) {
        systemStatus.value = '❌ 无法连接到服务器'
      }
    }
    
    const loadFileList = async () => {
      try {
        const response = await fetch('/upload/list')
        const data = await response.json()
        files.value = data.files || []
      } catch (error) {
        console.error('加载文件列表失败:', error)
      }
    }
    
    const showMessage = (type, text) => {
      message.type = type
      message.text = text
      setTimeout(() => { message.type = ''; message.text = '' }, 3000)
    }
    
    const handleFileSelected = (file) => { selectedFile.value = file }
    const handleFileUploaded = () => { 
      loadFileList()
      setTimeout(() => checkIndexStatus(), 500)
    }
    const handleFileDeleted = () => {
      loadFileList()
      if (selectedFile.value && !files.value.find(f => f.filename === selectedFile.value.filename)) {
        selectedFile.value = null
      }
    }
    
    const handleFileProcess = async (filename) => {
      if (!filename) {
        showMessage('error', '请先选择文件')
        return
      }
      try {
        showMessage('loading', '正在处理文件，这可能需要几分钟...')
        const response = await fetch('/process/file', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename, build_index: true })
        })
        const result = await response.json()
        if (response.ok) {
          const indexBuilt = result.processing_summary?.index_info?.index_built
          if (indexBuilt) {
            showMessage('success', '✅ 文件处理完成！索引已构建，可以开始问答了。')
          } else {
            showMessage('success', '⚠️ 文件处理完成，但索引构建失败，请检查日志。')
          }
          processStatus.value = result
          
          chatMessages.value.push({
            type: 'assistant',
            content: `✅ 文件 "${filename}" 处理完成！\n\n- 页数: ${result.processing_summary?.document_info?.page_count || 'N/A'}\n- 表格数: ${result.processing_summary?.table_info?.total_tables || 'N/A'}\n- 索引状态: ${indexBuilt ? '✅ 已构建' : '❌ 未构建'}\n\n现在可以开始提问了！`,
            timestamp: new Date()
          })
        } else {
          showMessage('error', result.detail || '处理失败')
        }
      } catch (error) {
        console.error('处理文件错误:', error)
        showMessage('error', `处理失败: ${error.message}`)
      }
    }
    
    const handleSendMessage = async (question) => {
      chatMessages.value.push({ type: 'user', content: question, timestamp: new Date() })
      queryLoading.value = true
      try {
        const response = await fetch('/query/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question, enable_visualization: true })
        })
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
          const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ 查询失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
          return
        }
        
        const result = await response.json()
        
        if (result.error) {
          const errorMsg = result.answer || result.error || '查询失败'
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
          return
        }
        
        if (result.answer) {
          chatMessages.value.push({ 
            type: 'assistant', 
            content: result.answer, 
            sources: result.sources || [], 
            timestamp: new Date() 
          })
          
          if (result.visualization && result.visualization.has_visualization) {
            visualizationData.value = result.visualization
            visualizationLoading.value = false
          }
        } else {
          chatMessages.value.push({ 
            type: 'assistant', 
            content: '⚠️ 未收到有效回答，请重试。', 
            timestamp: new Date() 
          })
        }
      } catch (error) {
        console.error('查询错误:', error)
        const errorMsg = error.message || '网络错误或服务器无响应'
        chatMessages.value.push({ 
          type: 'assistant', 
          content: `❌ 查询失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. 服务器未响应\n3. 索引未构建完成\n\n请检查网络连接，确保已处理文档。`, 
          timestamp: new Date() 
        })
        showMessage('error', errorMsg)
      } finally {
        queryLoading.value = false
      }
    }
    
    const handleAgentQuery = async (question) => {
      chatMessages.value.push({ type: 'user', content: question, timestamp: new Date() })
      queryLoading.value = true
      
      const progressIndex = chatMessages.value.length
      chatMessages.value.push({ 
        type: 'assistant', 
        content: '🤖 Agent正在分析中，这可能需要1-3分钟，请耐心等待...\n\n正在执行：\n- 检索相关数据\n- 调用工具分析\n- 生成结构化回答', 
        timestamp: new Date(),
        isProgress: true
      })
      
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000)
        
        const response = await fetch('/agent/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
          const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}`
          const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress)
          if (progressMsgIndex >= 0) {
            chatMessages.value.splice(progressMsgIndex, 1)
          }
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ Agent查询失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，Agent系统已初始化。`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
          return
        }
        
        const result = await response.json()
        
        const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress)
        if (progressMsgIndex >= 0) {
          chatMessages.value.splice(progressMsgIndex, 1)
        }
        
        if (result.status === 'success') {
          chatMessages.value.push({ 
            type: 'assistant', 
            content: result.answer, 
            timestamp: new Date() 
          })
          
          if (result.tool_calls && Array.isArray(result.tool_calls)) {
            result.tool_calls.forEach(toolCall => {
              const toolName = toolCall.tool_name
              const toolOutput = toolCall.tool_output
              
              if (toolName === 'generate_dupont_analysis' && toolOutput) {
                dupontData.value = toolOutput
                dupontLoading.value = false
              } else if (toolName === 'generate_financial_review' && toolOutput) {
                if (!companyOverviewData.value) {
                  companyOverviewData.value = {}
                }
                companyOverviewData.value.financialReview = toolOutput
                companyOverviewLoading.value = false
              } else if (toolName === 'generate_business_highlights' && toolOutput) {
                if (!companyOverviewData.value) {
                  companyOverviewData.value = {}
                }
                companyOverviewData.value.businessHighlights = toolOutput
                companyOverviewLoading.value = false
              } else if (toolName === 'generate_business_guidance' && toolOutput) {
                if (!notesAndRisksData.value) {
                  notesAndRisksData.value = {}
                }
                notesAndRisksData.value.businessGuidance = toolOutput
                notesAndRisksLoading.value = false
              } else if (toolName === 'retrieve_financial_data' && toolOutput) {
                if (!companyOverviewData.value) {
                  companyOverviewData.value = {}
                }
                if (!companyOverviewData.value.financialData) {
                  companyOverviewData.value.financialData = []
                }
                companyOverviewData.value.financialData.push(toolOutput)
                companyOverviewLoading.value = false
              }
            })
          }
          
          if (result.structured_response) {
            const structured = result.structured_response
            if (structured.dupont_analysis) {
              dupontData.value = structured.dupont_analysis
              dupontLoading.value = false
            }
            if (structured.financial_review) {
              if (!companyOverviewData.value) {
                companyOverviewData.value = {}
              }
              companyOverviewData.value.financialReview = structured.financial_review
              companyOverviewLoading.value = false
            }
          }
          
          if (result.visualization) {
            visualizationData.value = result.visualization
            visualizationLoading.value = false
          }
          
          showMessage('success', 'Agent分析完成！结果已更新到各个卡片中。')
        } else {
          const errorMsg = result.error || result.detail || '查询失败'
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ Agent查询失败: ${errorMsg}`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
        }
      } catch (error) {
        console.error('Agent查询错误:', error)
        
        const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress)
        if (progressMsgIndex >= 0) {
          chatMessages.value.splice(progressMsgIndex, 1)
        }
        
        let errorMsg = '网络错误或请求超时'
        if (error.name === 'AbortError') {
          errorMsg = '请求超时（超过10分钟），Agent查询可能需要更长时间，请稍后重试或使用普通查询模式'
        } else if (error.message) {
          errorMsg = error.message
        }
        
        chatMessages.value.push({ 
          type: 'assistant', 
          content: `❌ Agent查询失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. Agent系统未初始化\n3. 索引未构建完成\n4. 查询时间过长（Agent查询通常需要1-3分钟）\n\n建议：\n- 检查网络连接\n- 尝试使用普通查询模式\n- 确保已处理文档并构建索引`, 
          timestamp: new Date() 
        })
        showMessage('error', errorMsg)
      } finally {
        queryLoading.value = false
      }
    }
    
    const handleGetSuggestions = async () => {
      try {
        const response = await fetch('/query/suggestions')
        const data = await response.json()
        suggestions.value = data.suggestions || []
      } catch (error) {
        showMessage('error', `获取建议失败: ${error.message}`)
      }
    }
    
    const handleGenerateReport = async () => {
      companyOverviewLoading.value = true
      try {
        const response = await fetch('/agent/generate-report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_name: '公司名称',
            year: '2023',
            save_to_file: false
          })
        })
        const result = await response.json()
        if (response.ok && result.status === 'success') {
          companyOverviewData.value = { company_name: result.company_name, year: result.year }
          showMessage('success', '企业概况生成成功')
        } else {
          showMessage('error', result.error || '生成失败')
        }
      } catch (error) {
        showMessage('error', `生成失败: ${error.message}`)
      } finally {
        companyOverviewLoading.value = false
      }
    }
    
    const handleGenerateSection = async (sectionName) => {
      notesAndRisksLoading.value = true
      try {
        const response = await fetch('/agent/generate-section', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            section_name: sectionName,
            company_name: '公司名称',
            year: '2023'
          })
        })
        const result = await response.json()
        if (response.ok && result.status === 'success') {
          notesAndRisksData.value = { notes: result.content, risks: '' }
          showMessage('success', '附注与风险生成成功')
        } else {
          showMessage('error', result.error || '生成失败')
        }
      } catch (error) {
        showMessage('error', `生成失败: ${error.message}`)
      } finally {
        notesAndRisksLoading.value = false
      }
    }
    
    const handleClearChat = () => {
      chatMessages.value = []
      visualizationData.value = null
    }
    
    const checkIndexStatus = async () => {
      try {
        const response = await fetch('/process/status')
        if (!response.ok) {
          console.warn('获取处理状态失败，可能索引未初始化')
          return
        }
        const data = await response.json()
        processStatus.value = data
        
        if (data.index_status) {
          const indexBuilt = data.index_status.index_built === true || data.index_status.status === 'ready'
          if (!indexBuilt && files.value.length > 0) {
            console.log('提示：请先处理文档以构建索引')
          }
        }
      } catch (error) {
        console.warn('检查索引状态失败（这是正常的，如果索引未初始化）:', error.message)
      }
    }
    
    onMounted(() => {
      checkSystemStatus()
      loadFileList()
      checkIndexStatus()
    })
    
    return {
      systemStatus, files, selectedFile, chatMessages, queryLoading, message,
      companyOverviewData, companyOverviewLoading, notesAndRisksData, notesAndRisksLoading,
      dupontData, dupontLoading, visualizationData, visualizationLoading, processStatus, suggestions,
      showMessage, handleFileSelected, handleFileUploaded, handleFileDeleted, handleFileProcess,
      handleSendMessage, handleAgentQuery, handleGetSuggestions,
      handleGenerateReport, handleGenerateSection, handleClearChat, checkIndexStatus
    }
  },
  template: `
    <div class="app-container">
      <header class="app-header">
        <div class="header-content">
          <h1 class="app-title">🚀 FinDecipher</h1>
        </div>
        <div class="header-status">
          <span class="status-text">{{ systemStatus }}</span>
        </div>
      </header>
      <main class="app-main">
        <aside class="left-panel">
          <FilePreviewCard :files="files" @file-selected="handleFileSelected" @file-uploaded="handleFileUploaded" @file-deleted="handleFileDeleted" @file-process="handleFileProcess" @show-message="showMessage" />
          <CompanyOverview :data="companyOverviewData" :loading="companyOverviewLoading" @generate-report="handleGenerateReport" />
        </aside>
        <section class="middle-panel">
          <ChatArea :messages="chatMessages" :loading="queryLoading" :suggestions="suggestions" @send-message="handleSendMessage" @agent-query="handleAgentQuery" @get-suggestions="handleGetSuggestions" @clear-chat="handleClearChat" />
        </section>
        <aside class="right-panel">
          <VisualizationPanel :chart-data="visualizationData" :loading="visualizationLoading" />
        </aside>
      </main>
      <MessageToast :message="message" />
    </div>
  `
}

// 创建并挂载应用
const app = createApp(App)

// 注册组件
app.component('Card', Card)
app.component('FilePreviewCard', FilePreviewCard)
app.component('ChatArea', ChatArea)
app.component('CompanyOverview', CompanyOverview)
app.component('NotesAndRisks', NotesAndRisks)
app.component('DupontAnalysis', DupontAnalysis)
app.component('VisualizationPanel', VisualizationPanel)
app.component('MessageToast', MessageToast)

// 挂载应用
app.mount('#app')

console.log('✅ Vue应用已加载')

