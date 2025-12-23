// Vue 3 应用主文件 - Composition API 风格，完整功能版
(function() {
    'use strict';
    
    // 等待 Vue 加载 - 如果立即检查失败，等待一段时间再检查
    function waitForVue(maxAttempts = 10, attempt = 0) {
        if (typeof Vue !== 'undefined') {
            console.log('✅ Vue已加载');
            initializeApp();
            return;
        }
        
        if (attempt >= maxAttempts) {
            console.error('❌ Vue加载超时，请检查CDN链接');
            document.body.innerHTML = '<div style="padding: 20px; color: red; font-family: Arial, sans-serif; background: #fff; border: 2px solid red; margin: 20px;"><h2>❌ Vue未加载</h2><p>无法加载Vue.js，可能的原因：</p><ul><li>网络连接问题</li><li>CDN服务不可用</li><li>防火墙阻止了CDN访问</li><li>浏览器阻止了外部脚本加载</li></ul><p><strong>解决方案：</strong></p><ol><li>检查浏览器控制台的网络请求</li><li>尝试刷新页面</li><li>检查网络代理设置</li><li>考虑使用本地Vue文件</li></ol></div>';
            return;
        }
        
        setTimeout(() => waitForVue(maxAttempts, attempt + 1), 100);
    }
    
    function initializeApp() {
        if (typeof Vue === 'undefined') {
            console.error('❌ Vue仍未加载');
            return;
        }
        
        const { createApp, ref, reactive, computed, onMounted, watch } = Vue;

    // ==================== 组件定义 ====================
    // 组件已从独立文件加载到 window.Components 中
    // 检查组件是否已加载
    function checkComponents() {
        if (!window.Components) {
            console.error('❌ 组件未加载，请确保所有组件文件已正确加载');
            return false;
        }
        const requiredComponents = ['Card', 'FilePreviewCard', 'ChatArea', 'CompanyOverview', 'NotesAndRisks', 'DupontAnalysis', 'VisualizationPanel', 'MessageToast'];
        const missing = requiredComponents.filter(name => !window.Components[name]);
        if (missing.length > 0) {
            console.error('❌ 缺少组件:', missing.join(', '));
            return false;
        }
        return true;
    }


    // ==================== 主应用 ====================

    const App = {
    setup() {
        const systemStatus = ref('检查中...');
        const files = ref([]);
        const selectedFile = ref(null);
        const chatMessages = ref([]);
        const queryLoading = ref(false);
        const message = reactive({ type: '', text: '' });
        const companyOverviewData = ref(null);
        const companyOverviewLoading = ref(false);
        const notesAndRisksData = ref(null);
        const notesAndRisksLoading = ref(false);
        const dupontData = ref(null);
        const dupontLoading = ref(false);
        const visualizationData = ref(null);
        const visualizationLoading = ref(false);
        const processStatus = ref(null);
        const suggestions = ref([]);
        
        const checkSystemStatus = async () => {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                systemStatus.value = data.status === 'healthy' ? '✅ 系统正常运行' : '⚠️ 系统状态异常';
            } catch (error) {
                systemStatus.value = '❌ 无法连接到服务器';
            }
        };
        
        const loadFileList = async () => {
            try {
                const response = await fetch('/upload/list');
                const data = await response.json();
                files.value = data.files || [];
            } catch (error) {
                console.error('加载文件列表失败:', error);
            }
        };
        
        const showMessage = (type, text) => {
            message.type = type;
            message.text = text;
            setTimeout(() => { message.type = ''; message.text = ''; }, 3000);
        };
        
        const handleFileSelected = (file) => { selectedFile.value = file; };
        const handleFileUploaded = () => { 
            loadFileList();
            // 延迟检查状态，等待文件上传完成
            setTimeout(() => checkIndexStatus(), 500);
        };
        const handleFileDeleted = () => {
            loadFileList();
            if (selectedFile.value && !files.value.find(f => f.filename === selectedFile.value.filename)) {
                selectedFile.value = null;
            }
        };
        
        const handleFileProcess = async (filename) => {
            if (!filename) {
                showMessage('error', '请先选择文件');
                return;
            }
            try {
                showMessage('loading', '正在处理文件，这可能需要几分钟...');
                const response = await fetch('/process/file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename, build_index: true })
                });
                const result = await response.json();
                if (response.ok) {
                    const indexBuilt = result.processing_summary?.index_info?.index_built;
                    if (indexBuilt) {
                        showMessage('success', '✅ 文件处理完成！索引已构建，可以开始问答了。');
                    } else {
                        showMessage('success', '⚠️ 文件处理完成，但索引构建失败，请检查日志。');
                    }
                    processStatus.value = result;
                    
                    // 添加提示消息到聊天区域
                    chatMessages.value.push({
                        type: 'assistant',
                        content: `✅ 文件 "${filename}" 处理完成！\n\n- 页数: ${result.processing_summary?.document_info?.page_count || 'N/A'}\n- 表格数: ${result.processing_summary?.table_info?.total_tables || 'N/A'}\n- 索引状态: ${indexBuilt ? '✅ 已构建' : '❌ 未构建'}\n\n现在可以开始提问了！`,
                        timestamp: new Date()
                    });
                } else {
                    showMessage('error', result.detail || '处理失败');
                }
            } catch (error) {
                console.error('处理文件错误:', error);
                showMessage('error', `处理失败: ${error.message}`);
            }
        };
        
        const handleSendMessage = async (question) => {
            chatMessages.value.push({ type: 'user', content: question, timestamp: new Date() });
            queryLoading.value = true;
            try {
                const response = await fetch('/query/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question, enable_visualization: true })
                });
                
                // 检查HTTP状态码
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '请求失败' }));
                    const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`;
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ 查询失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                    return;
                }
                
                const result = await response.json();
                
                // 检查结果中是否有错误
                if (result.error) {
                    const errorMsg = result.answer || result.error || '查询失败';
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                    return;
                }
                
                // 成功处理
                if (result.answer) {
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: result.answer, 
                        sources: result.sources || [], 
                        timestamp: new Date() 
                    });
                    
                    // 处理可视化
                    if (result.visualization && result.visualization.has_visualization) {
                        visualizationData.value = result.visualization;
                        visualizationLoading.value = false;
                    }
                } else {
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: '⚠️ 未收到有效回答，请重试。', 
                        timestamp: new Date() 
                    });
                }
            } catch (error) {
                console.error('查询错误:', error);
                const errorMsg = error.message || '网络错误或服务器无响应';
                chatMessages.value.push({ 
                    type: 'assistant', 
                    content: `❌ 查询失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. 服务器未响应\n3. 索引未构建完成\n\n请检查网络连接，确保已处理文档。`, 
                    timestamp: new Date() 
                });
                showMessage('error', errorMsg);
            } finally {
                queryLoading.value = false;
            }
        };
        
        const handleAgentQuery = async (question) => {
            chatMessages.value.push({ type: 'user', content: question, timestamp: new Date() });
            queryLoading.value = true;
            
            // 添加进度提示
            const progressIndex = chatMessages.value.length;
            chatMessages.value.push({ 
                type: 'assistant', 
                content: '🤖 Agent正在分析中，这可能需要1-3分钟，请耐心等待...\n\n正在执行：\n- 检索相关数据\n- 调用工具分析\n- 生成结构化回答', 
                timestamp: new Date(),
                isProgress: true
            });
            
            try {
                // 设置超时（10分钟，因为Agent查询可能需要较长时间）
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);
                
                const response = await fetch('/agent/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '请求失败' }));
                    const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}`;
                    // 移除进度提示，添加错误消息
                    const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress);
                    if (progressMsgIndex >= 0) {
                        chatMessages.value.splice(progressMsgIndex, 1);
                    }
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ Agent查询失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，Agent系统已初始化。`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                    return;
                }
                
                const result = await response.json();
                
                // 移除进度提示
                const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress);
                if (progressMsgIndex >= 0) {
                    chatMessages.value.splice(progressMsgIndex, 1);
                }
                
                if (result.status === 'success') {
                    // 显示文本回答在聊天区域
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: result.answer, 
                        timestamp: new Date() 
                    });
                    
                    // 处理工具调用结果，填充到对应的卡片中
                    if (result.tool_calls && Array.isArray(result.tool_calls)) {
                        result.tool_calls.forEach(toolCall => {
                            const toolName = toolCall.tool_name;
                            const toolOutput = toolCall.tool_output;
                            
                            // 根据工具名称将结果映射到对应的卡片
                            if (toolName === 'generate_dupont_analysis' && toolOutput) {
                                // 杜邦分析结果
                                dupontData.value = toolOutput;
                                dupontLoading.value = false;
                            } else if (toolName === 'generate_financial_review' && toolOutput) {
                                // 财务点评 - 填充到企业概况
                                if (!companyOverviewData.value) {
                                    companyOverviewData.value = {};
                                }
                                companyOverviewData.value.financialReview = toolOutput;
                                companyOverviewLoading.value = false;
                            } else if (toolName === 'generate_business_highlights' && toolOutput) {
                                // 业务亮点 - 填充到企业概况
                                if (!companyOverviewData.value) {
                                    companyOverviewData.value = {};
                                }
                                companyOverviewData.value.businessHighlights = toolOutput;
                                companyOverviewLoading.value = false;
                            } else if (toolName === 'generate_business_guidance' && toolOutput) {
                                // 业绩指引 - 填充到附注与风险
                                if (!notesAndRisksData.value) {
                                    notesAndRisksData.value = {};
                                }
                                notesAndRisksData.value.businessGuidance = toolOutput;
                                notesAndRisksLoading.value = false;
                            } else if (toolName === 'retrieve_financial_data' && toolOutput) {
                                // 财务数据 - 可以用于企业概况或可视化
                                if (!companyOverviewData.value) {
                                    companyOverviewData.value = {};
                                }
                                if (!companyOverviewData.value.financialData) {
                                    companyOverviewData.value.financialData = [];
                                }
                                companyOverviewData.value.financialData.push(toolOutput);
                                companyOverviewLoading.value = false;
                            }
                        });
                    }
                    
                    // 如果有结构化响应，也尝试填充
                    if (result.structured_response) {
                        const structured = result.structured_response;
                        if (structured.dupont_analysis) {
                            dupontData.value = structured.dupont_analysis;
                            dupontLoading.value = false;
                        }
                        if (structured.financial_review) {
                            if (!companyOverviewData.value) {
                                companyOverviewData.value = {};
                            }
                            companyOverviewData.value.financialReview = structured.financial_review;
                            companyOverviewLoading.value = false;
                        }
                    }
                    
                    // 如果有可视化数据，显示在右栏
                    if (result.visualization) {
                        visualizationData.value = result.visualization;
                        visualizationLoading.value = false;
                    }
                    
                    showMessage('success', 'Agent分析完成！结果已更新到各个卡片中。');
                } else {
                    const errorMsg = result.error || result.detail || '查询失败';
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ Agent查询失败: ${errorMsg}`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                }
            } catch (error) {
                console.error('Agent查询错误:', error);
                
                // 移除进度提示
                const progressMsgIndex = chatMessages.value.findIndex(msg => msg.isProgress);
                if (progressMsgIndex >= 0) {
                    chatMessages.value.splice(progressMsgIndex, 1);
                }
                
                let errorMsg = '网络错误或请求超时';
                if (error.name === 'AbortError') {
                    errorMsg = '请求超时（超过10分钟），Agent查询可能需要更长时间，请稍后重试或使用普通查询模式';
                } else if (error.message) {
                    errorMsg = error.message;
                }
                
                chatMessages.value.push({ 
                    type: 'assistant', 
                    content: `❌ Agent查询失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. Agent系统未初始化\n3. 索引未构建完成\n4. 查询时间过长（Agent查询通常需要1-3分钟）\n\n建议：\n- 检查网络连接\n- 尝试使用普通查询模式\n- 确保已处理文档并构建索引`, 
                    timestamp: new Date() 
                });
                showMessage('error', errorMsg);
            } finally {
                queryLoading.value = false;
            }
        };
        
        const handleGetSuggestions = async () => {
            try {
                const response = await fetch('/query/suggestions');
                const data = await response.json();
                suggestions.value = data.suggestions || [];
            } catch (error) {
                showMessage('error', `获取建议失败: ${error.message}`);
            }
        };
        
        const handleGenerateReport = async () => {
            companyOverviewLoading.value = true;
            try {
                const response = await fetch('/agent/generate-report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        company_name: '公司名称',
                        year: '2023',
                        save_to_file: false
                    })
                });
                const result = await response.json();
                if (response.ok && result.status === 'success') {
                    companyOverviewData.value = { company_name: result.company_name, year: result.year };
                    showMessage('success', '企业概况生成成功');
                } else {
                    showMessage('error', result.error || '生成失败');
                }
            } catch (error) {
                showMessage('error', `生成失败: ${error.message}`);
            } finally {
                companyOverviewLoading.value = false;
            }
        };
        
        const handleGenerateSection = async (sectionName) => {
            notesAndRisksLoading.value = true;
            try {
                const response = await fetch('/agent/generate-section', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        section_name: sectionName,
                        company_name: '公司名称',
                        year: '2023'
                    })
                });
                const result = await response.json();
                if (response.ok && result.status === 'success') {
                    notesAndRisksData.value = { notes: result.content, risks: '' };
                    showMessage('success', '附注与风险生成成功');
                } else {
                    showMessage('error', result.error || '生成失败');
                }
            } catch (error) {
                showMessage('error', `生成失败: ${error.message}`);
            } finally {
                notesAndRisksLoading.value = false;
            }
        };
        
        const handleClearChat = () => {
            chatMessages.value = [];
            visualizationData.value = null;
        };
        
        const handleAnalysisQuery = async (question) => {
            // 文件分析查询处理（可以复用普通查询逻辑，或者使用专门的接口）
            queryLoading.value = true;
            chatMessages.value.push({ 
                type: 'user', 
                content: `📊 文件分析：${question}`, 
                timestamp: new Date() 
            });
            
            try {
                const response = await fetch('/query/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, enable_visualization: true })
                });
                
                // 检查HTTP状态码
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '请求失败' }));
                    const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`;
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ 分析失败: ${errorMsg}\n\n提示：请确保已上传并处理文档，索引已构建完成。`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                    return;
                }
                
                const result = await response.json();
                
                // 检查结果中是否有错误
                if (result.error) {
                    const errorMsg = result.answer || result.error || '分析失败';
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `❌ ${errorMsg}`, 
                        timestamp: new Date() 
                    });
                    showMessage('error', errorMsg);
                    return;
                }
                
                // 成功处理
                if (result.answer) {
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: result.answer, 
                        sources: result.sources || [],
                        timestamp: new Date() 
                    });
                    
                    // 处理可视化
                    if (result.visualization && result.visualization.has_visualization) {
                        visualizationData.value = result.visualization;
                        visualizationLoading.value = false;
                    }
                } else {
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: '⚠️ 未收到有效回答，请重试。', 
                        timestamp: new Date() 
                    });
                }
            } catch (error) {
                console.error('分析错误:', error);
                const errorMsg = error.message || '网络错误或服务器无响应';
                chatMessages.value.push({ 
                    type: 'assistant', 
                    content: `❌ 分析失败: ${errorMsg}\n\n可能的原因：\n1. 网络连接问题\n2. 服务器未响应\n3. 索引未构建完成\n\n请检查网络连接，确保已处理文档。`, 
                    timestamp: new Date() 
                });
                showMessage('error', errorMsg);
            } finally {
                queryLoading.value = false;
            }
        };
        
        // 检查索引状态
        const checkIndexStatus = async () => {
            try {
                const response = await fetch('/process/status');
                if (!response.ok) {
                    console.warn('获取处理状态失败，可能索引未初始化');
                    return;
                }
                const data = await response.json();
                processStatus.value = data;
                
                // 如果索引未构建，提示用户
                if (data.index_status) {
                    const indexBuilt = data.index_status.index_built === true || data.index_status.status === 'ready';
                    if (!indexBuilt && files.value.length > 0) {
                        // 不显示提示，只在控制台记录
                        console.log('提示：请先处理文档以构建索引');
                    }
                }
            } catch (error) {
                console.warn('检查索引状态失败（这是正常的，如果索引未初始化）:', error.message);
            }
        };
        
        onMounted(() => {
            checkSystemStatus();
            loadFileList();
            checkIndexStatus();
        });
        
        return {
            systemStatus, files, selectedFile, chatMessages, queryLoading, message,
            companyOverviewData, companyOverviewLoading, notesAndRisksData, notesAndRisksLoading,
            dupontData, dupontLoading, visualizationData, visualizationLoading, processStatus, suggestions,
            showMessage, handleFileSelected, handleFileUploaded, handleFileDeleted, handleFileProcess,
            handleSendMessage, handleAgentQuery, handleGetSuggestions,
            handleGenerateReport, handleGenerateSection, handleClearChat, handleAnalysisQuery, checkIndexStatus
        };
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
    };

    // 创建并挂载应用
    function mountApp() {
        try {
        if (typeof createApp === 'undefined') {
            throw new Error('Vue createApp未定义，请检查Vue是否正确加载');
        }
        
        // 检查组件是否已加载
        if (!checkComponents()) {
            throw new Error('组件未完全加载，请刷新页面重试');
        }
        
        const app = createApp(App);
        // 从全局组件对象注册组件
        app.component('Card', window.Components.Card);
        app.component('FilePreviewCard', window.Components.FilePreviewCard);
        app.component('ChatArea', window.Components.ChatArea);
        app.component('CompanyOverview', window.Components.CompanyOverview);
        app.component('NotesAndRisks', window.Components.NotesAndRisks);
        app.component('DupontAnalysis', window.Components.DupontAnalysis);
        app.component('VisualizationPanel', window.Components.VisualizationPanel);
        app.component('MessageToast', window.Components.MessageToast);
        
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                app.mount('#app');
                console.log('✅ Vue应用挂载成功');
            });
        } else {
            app.mount('#app');
            console.log('✅ Vue应用挂载成功');
        }
    } catch (error) {
        console.error('❌ Vue应用挂载失败:', error);
        console.error('错误堆栈:', error.stack);
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'padding: 20px; color: red; font-family: Arial, sans-serif; background: #fff; border: 2px solid red; margin: 20px;';
        errorDiv.innerHTML = '<h2>❌ 应用加载失败</h2><p><strong>错误信息:</strong> ' + error.message + '</p><p><strong>错误堆栈:</strong></p><pre style="background: #f5f5f5; padding: 10px; overflow: auto;">' + (error.stack || '无堆栈信息') + '</pre><p>请检查浏览器控制台获取更多信息。</p>';
        document.body.appendChild(errorDiv);
        }
    }
    
    // 在initializeApp末尾调用mountApp来挂载应用
    mountApp();
    } // initializeApp函数结束
    
    // 开始等待Vue加载
    waitForVue();
})();