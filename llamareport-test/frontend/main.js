import { createApp } from 'vue'
import { ref, reactive, onMounted } from 'vue'

// 导入组件
import Card from './components/Card.vue'
import FilePreviewCard from './components/FilePreviewCard.vue'
import ChatArea from './components/ChatArea.vue'
import CompanyOverview from './components/CompanyOverview.vue'
import NotesAndRisks from './components/NotesAndRisks.vue'
import VisualizationPanel from './components/VisualizationPanel.vue'
import MessageToast from './components/MessageToast.vue'
import AgentAnalysisPage from './components/AgentAnalysisPage.vue'

// 导入样式
import './style.css'

// 主应用组件
const App = {
  setup() {
    const systemStatus = ref('检查中...')
    const currentPage = ref('main')  // 'main' 或 'agent-analysis'
    const files = ref([])
    const selectedFile = ref(null)
    const chatMessages = ref([])
    const queryLoading = ref(false)
    const message = reactive({ type: '', text: '' })
    const companyOverviewData = ref(null)
    const companyOverviewLoading = ref(false)
    const quickOverviewData = ref(null)
    const notesAndRisksData = ref(null)
    const notesAndRisksLoading = ref(false)
    const dupontData = ref(null)
    const dupontLoading = ref(false)
    const visualizationData = ref(null)
    const visualizationLoading = ref(false)
    const visualizationCards = ref([])  // 存储所有可视化卡片
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
            // 自动获取快速概况
            setTimeout(() => {
              if (typeof loadQuickOverview === 'function') {
                loadQuickOverview()
              }
            }, 500)
          } else {
            showMessage('success', '⚠️ 文件处理完成，但索引构建失败，请检查日志。')
          }
          processStatus.value = result
          
          // 通知FilePreviewCard组件更新文件状态
          window.dispatchEvent(new CustomEvent('file-processing-complete', {
            detail: { filename: filename }
          }))
          
          chatMessages.value.push({
            type: 'assistant',
            content: `✅ 文件 "${filename}" 处理完成！\n\n- 页数: ${result.processing_summary?.document_info?.page_count || 'N/A'}\n- 表格数: ${result.processing_summary?.table_info?.total_tables || 'N/A'}\n- 索引状态: ${indexBuilt ? '✅ 已构建' : '❌ 未构建'}\n\n现在可以开始提问了！`,
            timestamp: new Date()
          })
        } else {
          showMessage('error', result.detail || '处理失败')
          // 处理失败时，清除处理中状态
          window.dispatchEvent(new CustomEvent('file-processing-failed', {
            detail: { filename: filename }
          }))
        }
      } catch (error) {
        console.error('处理文件错误:', error)
        showMessage('error', `处理失败: ${error.message}`)
        // 处理失败时，清除处理中状态
        window.dispatchEvent(new CustomEvent('file-processing-failed', {
          detail: { filename: filename }
        }))
      }
    }
    
    const handleFileProcessMultiple = async (filenames) => {
      if (!filenames || filenames.length === 0) {
        showMessage('error', '请先选择要处理的文件')
        return
      }
      try {
        showMessage('loading', `正在处理 ${filenames.length} 个文件，这可能需要几分钟...`)
        const response = await fetch('/process/files', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filenames, build_index: true })
        })
        const result = await response.json()
        if (response.ok) {
          const indexBuilt = result.processing_summary?.index_info?.index_built
          const successCount = result.success_count || 0
          const totalCount = result.total_files || filenames.length
          const errorCount = result.error_count || 0
          
          if (indexBuilt) {
            showMessage('success', `✅ ${successCount}/${totalCount} 个文件处理完成！索引已构建，可以开始问答了。`)
            // 自动获取快速概况
            setTimeout(() => {
              if (typeof loadQuickOverview === 'function') {
                loadQuickOverview()
              }
            }, 500)
          } else {
            showMessage('warning', `⚠️ ${successCount}/${totalCount} 个文件处理完成，但索引构建失败，请检查日志。`)
          }
          
          processStatus.value = result
          
          // 显示处理结果摘要
          let summary = `✅ 批量处理完成！\n\n`
          summary += `- 成功: ${successCount}/${totalCount} 个文件`
          if (errorCount > 0) {
            summary += `，失败: ${errorCount} 个文件`
          }
          summary += `\n`
          
          if (result.processing_summary?.document_info) {
            const pageCount = result.processing_summary.document_info.page_count || 0
            if (pageCount > 0) {
              summary += `- 总页数/工作表数: ${pageCount}\n`
            }
            const tableCount = result.processing_summary.table_info?.total_tables || 0
            if (tableCount > 0) {
              summary += `- 总表格数: ${tableCount}\n`
            }
          }
          summary += `- 索引状态: ${indexBuilt ? '✅ 已构建' : '❌ 未构建'}\n\n`
          summary += `现在可以开始提问了！`
          
          chatMessages.value.push({
            type: 'assistant',
            content: summary,
            timestamp: new Date()
          })
          
          // 显示失败的文件（如果有）
          if (result.failed_files && result.failed_files.length > 0) {
            chatMessages.value.push({
              type: 'assistant',
              content: `❌ 以下文件处理失败：\n${result.failed_files.map(f => `- ${f.filename}: ${f.error || f.message || '未知错误'}`).join('\n')}`,
              timestamp: new Date()
            })
            // 通知FilePreviewCard组件清除失败文件的处理中状态
            result.failed_files.forEach(failedFile => {
              window.dispatchEvent(new CustomEvent('file-processing-failed', {
                detail: { filename: failedFile.filename }
              }))
            })
          }
          
          // 显示成功的文件详情（如果有）
          if (result.file_results && result.file_results.length > 0) {
            const successFiles = result.file_results.filter(r => r.status === 'success')
            if (successFiles.length > 0 && successFiles.length <= 5) {
              // 只显示前5个成功文件的详情
              const filesDetail = successFiles.map(f => {
                const summary = f.summary || {}
                return `- ${f.filename}: ${summary.page_count || 0}页, ${summary.table_count || 0}个表格`
              }).join('\n')
              chatMessages.value.push({
                type: 'assistant',
                content: `📋 处理成功的文件：\n${filesDetail}`,
                timestamp: new Date()
              })
            }
            
            // 通知FilePreviewCard组件更新文件状态
            const successFilenames = successFiles.map(f => f.filename)
            // 通过emit事件通知子组件
            if (successFilenames.length > 0) {
              // 触发自定义事件，让FilePreviewCard监听
              window.dispatchEvent(new CustomEvent('files-processing-complete', {
                detail: { filenames: successFilenames }
              }))
            }
          }
        } else {
          showMessage('error', result.detail || '批量处理失败')
          // 批量处理失败时，清除所有文件的处理中状态
          filenames.forEach(filename => {
            window.dispatchEvent(new CustomEvent('file-processing-failed', {
              detail: { filename: filename }
            }))
          })
        }
      } catch (error) {
        console.error('批量处理文件错误:', error)
        showMessage('error', `批量处理失败: ${error.message}`)
        // 批量处理失败时，清除所有文件的处理中状态
        filenames.forEach(filename => {
          window.dispatchEvent(new CustomEvent('file-processing-failed', {
            detail: { filename: filename }
          }))
        })
      }
    }
    
    const handleSendMessage = async (question) => {
      chatMessages.value.push({ type: 'user', content: question, timestamp: new Date() })
      queryLoading.value = true
      try {
        // 构建context_filter：如果有选中的文件，使用文件名过滤
        const context_filter = selectedFile.value ? {
          filename: selectedFile.value.filename
        } : null
        
        const response = await fetch('/query/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            question: question, 
            enable_visualization: true,
            context_filter: context_filter
          })
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
            // 添加新的可视化卡片
            const cardId = Date.now().toString()
            visualizationCards.value.push({
              id: cardId,
              question: question,
              timestamp: new Date(),
              data: result.visualization,
              type: 'chart'
            })
            // 注意：不再设置visualizationData，避免重复显示
            // 因为isCardInList会检查卡片是否已在列表中
            // visualizationData.value = result.visualization  // 注释掉，避免重复显示
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
      // 切换到Agent分析页面
      currentPage.value = 'agent-analysis'
      
      // 等待页面切换完成后再执行查询
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 触发Agent分析页面的查询
      // 这个函数会被AgentAnalysisPage组件调用
      return await executeAgentQuery(question)
    }
    
    const executeAgentQuery = async (question) => {
      queryLoading.value = true
      
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
          showMessage('error', errorMsg)
          return {
            status: 'error',
            error: errorMsg
          }
        }
        
        const result = await response.json()
        
        // 添加调试日志
        console.log('🔍 [main.js] Agent查询响应:', {
          status: result.status,
          hasAnswer: !!result.answer,
          answerLength: result.answer?.length || 0,
          toolCallsCount: result.tool_calls?.length || 0,
          hasVisualization: !!result.visualization,
          hasStructuredResponse: !!result.structured_response,
          performance: result.performance
        })
        
        if (result.status === 'success') {
          const toolCallsCount = result.tool_calls?.length || 0
          const totalTime = result.performance?.total_seconds || 0
          showMessage('success', `Agent分析完成！执行了 ${toolCallsCount} 个工具调用，耗时 ${totalTime.toFixed(1)} 秒`)
        } else {
          const errorMsg = result.error || result.detail || '查询失败'
          showMessage('error', errorMsg)
        }
        
        return result
      } catch (error) {
        console.error('Agent查询错误:', error)
        
        let errorMsg = '网络错误或请求超时'
        if (error.name === 'AbortError') {
          errorMsg = '请求超时（超过10分钟），Agent查询可能需要更长时间，请稍后重试或使用普通查询模式'
        } else if (error.message) {
          errorMsg = error.message
        }
        
        showMessage('error', errorMsg)
        return {
          status: 'error',
          error: errorMsg
        }
      } finally {
        queryLoading.value = false
      }
    }
    
    const goToAgentAnalysis = () => {
      currentPage.value = 'agent-analysis'
    }
    
    const goBackToMain = () => {
      currentPage.value = 'main'
    }
    
    const handleDupontAnalysis = async () => {
      chatMessages.value.push({ 
        type: 'user', 
        content: '📊 请求杜邦分析', 
        timestamp: new Date() 
      })
      queryLoading.value = true
      dupontLoading.value = true
      
      const progressIndex = chatMessages.value.length
      chatMessages.value.push({ 
        type: 'assistant', 
        content: '📊 正在生成杜邦分析，这可能需要30秒-2分钟，请耐心等待...\n\n正在执行：\n- 提取财务数据\n- 计算杜邦指标\n- 生成分析报告', 
        timestamp: new Date(),
        isProgress: true
      })
      
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000) // 5分钟超时
        
        const response = await fetch('/query/dupont-analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_name: null,  // 自动提取
            year: null,  // 自动提取
            filename: selectedFile.value?.filename || null  // 传递选中的文件名
          }),
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)
        
        const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress)
        if (progressMsgIndex >= 0) {
          chatMessages.value.splice(progressMsgIndex, 1)
        }
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
          const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}`
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ 杜邦分析失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
          dupontLoading.value = false
          return
        }
        
        const result = await response.json()
        
        if (result.status === 'success' && result.analysis) {
          // 保存杜邦分析数据，转换为组件需要的格式
          // 注意：杜邦分析按钮生成的视图只设置dupontData，不添加到visualizationCards
          const analysis = result.analysis
          const level1 = analysis.level1 || {}
          dupontData.value = {
            roe: level1.roe?.formatted_value || level1.roe?.value || '—',
            roa: level1.roa?.formatted_value || level1.roa?.value || '—',
            equity_multiplier: level1.equity_multiplier?.formatted_value || level1.equity_multiplier?.value || '—',
            // 保存完整数据以便后续使用
            full_data: analysis
          }
          // 不添加到visualizationCards，因为杜邦分析按钮生成的视图应该通过dupontData显示
          dupontLoading.value = false
          
          // 生成友好的显示文本
          const roe = level1.roe?.formatted_value || 'N/A'
          const roa = level1.roa?.formatted_value || 'N/A'
          const equityMultiplier = level1.equity_multiplier?.formatted_value || 'N/A'
          
          let content = `✅ 杜邦分析生成成功！\n\n`
          content += `**公司**: ${result.company_name || '未知'}\n`
          content += `**年份**: ${result.year || '未知'}\n\n`
          content += `**核心指标**:\n`
          content += `- 净资产收益率(ROE): ${roe}\n`
          content += `- 资产净利率(ROA): ${roa}\n`
          content += `- 权益乘数: ${equityMultiplier}\n\n`
          
          if (analysis.insights && analysis.insights.length > 0) {
            content += `**分析洞察**:\n`
            analysis.insights.forEach(insight => {
              content += `- ${insight}\n`
            })
            content += `\n`
          }
          
          if (analysis.strengths && analysis.strengths.length > 0) {
            content += `**优势**:\n`
            analysis.strengths.forEach(strength => {
              content += `- ✅ ${strength}\n`
            })
            content += `\n`
          }
          
          if (analysis.weaknesses && analysis.weaknesses.length > 0) {
            content += `**劣势**:\n`
            analysis.weaknesses.forEach(weakness => {
              content += `- ⚠️ ${weakness}\n`
            })
            content += `\n`
          }
          
          if (analysis.recommendations && analysis.recommendations.length > 0) {
            content += `**改进建议**:\n`
            analysis.recommendations.forEach(rec => {
              content += `- 💡 ${rec}\n`
            })
          }
          
          chatMessages.value.push({ 
            type: 'assistant', 
            content: content, 
            timestamp: new Date() 
          })
          
          showMessage('success', '杜邦分析生成成功！结果已显示在右侧面板。')
        } else {
          const errorMsg = result.error || result.detail || '分析失败'
          chatMessages.value.push({ 
            type: 'assistant', 
            content: `❌ 杜邦分析失败: ${errorMsg}`, 
            timestamp: new Date() 
          })
          showMessage('error', errorMsg)
          dupontLoading.value = false
        }
      } catch (error) {
        console.error('杜邦分析错误:', error)
        
        const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress)
        if (progressMsgIndex >= 0) {
          chatMessages.value.splice(progressMsgIndex, 1)
        }
        
        let errorMsg = '网络错误或请求超时'
        if (error.name === 'AbortError') {
          errorMsg = '请求超时（超过5分钟），请稍后重试'
        } else if (error.message) {
          errorMsg = error.message
        }
        
        chatMessages.value.push({ 
          type: 'assistant', 
          content: `❌ 杜邦分析失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. 索引未构建完成\n3. 文档中缺少必要的财务数据\n\n建议：\n- 检查网络连接\n- 确保已处理文档并构建索引\n- 确保文档包含完整的财务报表数据`, 
          timestamp: new Date() 
        })
        showMessage('error', errorMsg)
        dupontLoading.value = false
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
          showMessage('success', '财务概况生成成功')
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
      visualizationCards.value = []  // 清空所有可视化卡片
    }
    
    const handleDeleteMessage = (index) => {
      if (index >= 0 && index < chatMessages.value.length) {
        chatMessages.value.splice(index, 1)
      }
    }
    
    const loadQuickOverview = async () => {
      companyOverviewLoading.value = true
      try {
        const response = await fetch('/query/quick-overview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
        const result = await response.json()
        if (response.ok && result.status === 'success') {
          quickOverviewData.value = result.overview
          showMessage('success', '✅ 财务概况已生成')
        } else {
          console.warn('快速概况生成失败:', result)
        }
      } catch (error) {
        console.error('加载快速概况失败:', error)
        // 不显示错误，静默失败
      } finally {
        companyOverviewLoading.value = false
      }
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
      currentPage, systemStatus, files, selectedFile, chatMessages, queryLoading, message,
      companyOverviewData, companyOverviewLoading, notesAndRisksData, notesAndRisksLoading,
      dupontData, dupontLoading, visualizationData, visualizationLoading, visualizationCards, processStatus, suggestions,
      quickOverviewData,
      showMessage, handleFileSelected, handleFileUploaded, handleFileDeleted, handleFileProcess, handleFileProcessMultiple,
      handleSendMessage, handleAgentQuery, executeAgentQuery, handleDupontAnalysis, handleGetSuggestions,
      handleGenerateReport, handleGenerateSection, handleClearChat, checkIndexStatus, loadQuickOverview,
      handleDeleteMessage, goToAgentAnalysis, goBackToMain,
      handleRemoveVizCard: (cardId) => {
        // 删除整个卡片（包括图表、推荐说明、数据洞察等所有内容）
        console.log('🗑️ 处理删除卡片请求:', cardId);
        console.log('  删除前卡片数量:', visualizationCards.value.length);
        
        const index = visualizationCards.value.findIndex(card => card.id === cardId)
        if (index > -1) {
          const removedCard = visualizationCards.value[index];
          console.log('  找到卡片:', removedCard.question || removedCard.id);
          visualizationCards.value.splice(index, 1);
          console.log('  删除后卡片数量:', visualizationCards.value.length);
          showMessage('success', `✅ 已删除视图卡片: ${removedCard.question || '可视化卡片'}`)
        } else {
          console.warn('  未找到要删除的卡片:', cardId);
        }
        
        // 如果删除的是当前显示的图表，也清空visualizationData
        if (visualizationData.value && visualizationCards.value.length === 0) {
          visualizationData.value = null
          console.log('  所有卡片已删除，清空visualizationData');
        }
      },
      handleRemoveDupontCard: () => {
        // 删除杜邦分析卡片：从cards中删除所有杜邦分析类型的卡片，并清空dupontData
        visualizationCards.value = visualizationCards.value.filter(card => card.type !== 'dupont')
        dupontData.value = null
      },
      handleGenerateComprehensiveAnalysis: async (selectedCards) => {
        // 处理生成总分析请求
        showMessage('loading', '正在生成总分析雷达图...')
        visualizationLoading.value = true
        
        try {
          const response = await fetch('/query/comprehensive-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              selected_cards: selectedCards.map(card => ({
                id: card.id,
                question: card.question,
                data: card.data
              })),
              overview_data: quickOverviewData.value,  // 传递财务概况数据
              context_filter: selectedFile.value ? {
                filename: selectedFile.value.filename
              } : null
            })
          })
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
            const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}`
            showMessage('error', `生成总分析失败: ${errorMsg}`)
            visualizationLoading.value = false
            // 重置选择状态
            window.dispatchEvent(new CustomEvent('reset-viz-selection'))
            return
          }
          
          const result = await response.json()
          
          if (result.status === 'success' && result.visualization) {
            // 添加总分析雷达图卡片
            const cardId = Date.now().toString()
            visualizationCards.value.push({
              id: cardId,
              question: '综合能力分析雷达图',
              timestamp: new Date(),
              data: result.visualization,
              type: 'chart'
            })
            showMessage('success', '✅ 总分析雷达图已生成')
            visualizationLoading.value = false
            
            // 重置选择状态，允许再次选择
            window.dispatchEvent(new CustomEvent('reset-viz-selection'))
          } else {
            const errorMsg = result.error || result.detail || '生成失败'
            showMessage('error', `生成总分析失败: ${errorMsg}`)
            visualizationLoading.value = false
            // 重置选择状态
            window.dispatchEvent(new CustomEvent('reset-viz-selection'))
          }
        } catch (error) {
          console.error('生成总分析错误:', error)
          const errorMsg = error.message || '网络错误或服务器无响应'
          showMessage('error', `生成总分析失败: ${errorMsg}`)
          visualizationLoading.value = false
          // 重置选择状态
          window.dispatchEvent(new CustomEvent('reset-viz-selection'))
        }
      },
      handleMetricClick: async (metricInfo) => {
        // 处理指标点击事件，生成可视化
        const { metricName, metricData } = metricInfo
        const metricValue = typeof metricData === 'object' ? metricData.value : metricData
        
        // 构建查询问题（针对不同指标优化查询）
        let question = ''
        if (metricName === 'ROE') {
          question = `请展示${metricName}（加权平均净资产收益率）的可视化图表，当前值为${metricValue}。请提供最近3-5年的ROE数据用于绘制趋势图。`
        } else if (metricName === '营业收入') {
          question = `请展示${metricName}的可视化图表，当前值为${metricValue}。请提供最近3-5年的营业收入数据，包括各年度的具体数值，用于绘制趋势图或柱状图。`
        } else if (metricName === '净利润') {
          question = `请展示${metricName}的可视化图表，当前值为${metricValue}。请提供最近3-5年的净利润数据，包括各年度的具体数值，用于绘制趋势图。`
        } else if (metricName === '资产总额') {
          question = `请展示${metricName}的可视化图表，当前值为${metricValue}。请提供最近3-5年的资产总额数据，包括各年度的具体数值，用于绘制趋势图。`
        } else {
          question = `请展示${metricName}的可视化图表，当前值为${metricValue}。请提供最近3-5年的历史数据，包括各年度的具体数值，用于绘制图表。`
        }
        
        // 显示加载提示
        showMessage('loading', `正在生成${metricName}的可视化图表...`)
        visualizationLoading.value = true
        
        try {
          // 构建context_filter：如果有选中的文件，使用文件名过滤
          const context_filter = selectedFile.value ? {
            filename: selectedFile.value.filename
          } : null
          
          const response = await fetch('/query/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              question: question, 
              enable_visualization: true,
              context_filter: context_filter
            })
          })
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
            const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
            showMessage('error', `生成${metricName}可视化失败: ${errorMsg}`)
            visualizationLoading.value = false
            return
          }
          
          const result = await response.json()
          
          if (result.error) {
            const errorMsg = result.answer || result.error || '查询失败'
            showMessage('error', `生成${metricName}可视化失败: ${errorMsg}`)
            visualizationLoading.value = false
            return
          }
          
          // 如果成功生成可视化，添加到可视化卡片列表
          if (result.visualization && result.visualization.has_visualization) {
            const cardId = Date.now().toString()
            visualizationCards.value.push({
              id: cardId,
              question: `${metricName}可视化`,
              timestamp: new Date(),
              data: result.visualization,
              type: 'chart'
            })
            showMessage('success', `✅ ${metricName}可视化图表已生成`)
            visualizationLoading.value = false
          } else {
            showMessage('warning', `⚠️ 未能为${metricName}生成可视化图表`)
            visualizationLoading.value = false
          }
        } catch (error) {
          console.error('生成指标可视化错误:', error)
          const errorMsg = error.message || '网络错误或服务器无响应'
          showMessage('error', `生成${metricName}可视化失败: ${errorMsg}`)
          visualizationLoading.value = false
        }
      }
    }
  },
  template: `
    <div class="app-container">
      <!-- Agent分析页面 -->
      <AgentAnalysisPage 
        v-if="currentPage === 'agent-analysis'"
        :on-back="goBackToMain"
        :on-query="executeAgentQuery"
      />
      
      <!-- 主页面 -->
      <template v-else>
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
            <FilePreviewCard ref="filePreviewCard" :files="files" @file-selected="handleFileSelected" @file-uploaded="handleFileUploaded" @file-deleted="handleFileDeleted" @file-process="handleFileProcess" @file-process-multiple="handleFileProcessMultiple" @show-message="showMessage" @files-processed="handleFilesProcessed" />
            <CompanyOverview :data="companyOverviewData" :loading="companyOverviewLoading" :overview-data="quickOverviewData" @generate-report="handleGenerateReport" @metric-click="handleMetricClick" />
          </aside>
          <section class="middle-panel">
            <ChatArea :messages="chatMessages" :loading="queryLoading" :suggestions="suggestions" @send-message="handleSendMessage" @agent-query="handleAgentQuery" @agent-analysis="goToAgentAnalysis" @dupont-analysis="handleDupontAnalysis" @get-suggestions="handleGetSuggestions" @clear-chat="handleClearChat" @delete-message="handleDeleteMessage" />
          </section>
          <aside class="right-panel">
            <VisualizationPanel :chart-data="visualizationData" :dupont-data="dupontData" :visualization-cards="visualizationCards" :loading="visualizationLoading || dupontLoading" @remove-card="handleRemoveVizCard" @remove-dupont-card="handleRemoveDupontCard" @generate-comprehensive-analysis="handleGenerateComprehensiveAnalysis" />
          </aside>
        </main>
        <MessageToast :message="message" />
      </template>
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
app.component('VisualizationPanel', VisualizationPanel)
app.component('MessageToast', MessageToast)
app.component('AgentAnalysisPage', AgentAnalysisPage)

// 挂载应用
app.mount('#app')

console.log('✅ Vue应用已加载')

