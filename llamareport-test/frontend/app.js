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

    // 通用卡片组件
    const Card = {
    name: 'Card',
    props: {
        title: { type: String, required: true },
        icon: { type: String, default: '📄' },
        status: { 
            type: String, 
            default: 'empty',
            validator: (value) => ['loading', 'empty', 'error', 'content'].includes(value)
        },
        emptyText: { type: String, default: '暂无数据' },
        errorText: { type: String, default: '加载失败' }
    },
    template: `
        <div class="card">
            <div class="card-header">
                <span class="card-icon">{{ icon }}</span>
                <h3 class="card-title">{{ title }}</h3>
            </div>
            <div class="card-content">
                <div v-if="status === 'loading'" class="card-state loading-state">
                    <div class="spinner"></div>
                    <p>加载中...</p>
                </div>
                <div v-else-if="status === 'empty'" class="card-state empty-state">
                    <p>{{ emptyText }}</p>
                </div>
                <div v-else-if="status === 'error'" class="card-state error-state">
                    <p>{{ errorText }}</p>
                </div>
                <div v-else class="card-body">
                    <slot></slot>
                </div>
            </div>
        </div>
    `
    };

    // 文件预览卡片组件 - 增强版
    const FilePreviewCard = {
    name: 'FilePreviewCard',
    props: { files: { type: Array, default: () => [] } },
    emits: ['file-selected', 'file-uploaded', 'file-deleted', 'show-message', 'file-process'],
    data() {
        return { isDragging: false, selectedFile: null, processingFile: null };
    },
    methods: {
        handleDragOver(e) { e.preventDefault(); this.isDragging = true; },
        handleDragLeave() { this.isDragging = false; },
        async handleDrop(e) {
            e.preventDefault();
            this.isDragging = false;
            await this.uploadFiles(Array.from(e.dataTransfer.files));
        },
        handleFileSelect(e) { this.uploadFiles(Array.from(e.target.files)); },
        async uploadFiles(files) {
            // 支持批量上传
            if (files.length > 1) {
                await this.batchUploadFiles(files);
            } else {
                for (const file of files) {
                    await this.uploadSingleFile(file);
                }
            }
        },
        async uploadSingleFile(file) {
            if (file.type !== 'application/pdf') {
                this.$emit('show-message', 'error', `文件 ${file.name} 不是PDF格式`);
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            try {
                const response = await fetch('/upload/file', { method: 'POST', body: formData });
                const result = await response.json();
                if (response.ok) {
                    this.$emit('file-uploaded');
                    this.$emit('show-message', 'success', `文件 ${result.filename} 上传成功`);
                } else {
                    this.$emit('show-message', 'error', `上传失败: ${result.detail}`);
                }
            } catch (error) {
                this.$emit('show-message', 'error', `上传失败: ${error.message}`);
            }
        },
        async batchUploadFiles(files) {
            const formData = new FormData();
            files.forEach(file => {
                if (file.type === 'application/pdf') {
                    formData.append('files', file);
                }
            });
            try {
                const response = await fetch('/upload/files', { method: 'POST', body: formData });
                const result = await response.json();
                if (response.ok) {
                    this.$emit('file-uploaded');
                    this.$emit('show-message', 'success', result.message);
                } else {
                    this.$emit('show-message', 'error', result.detail);
                }
            } catch (error) {
                this.$emit('show-message', 'error', `批量上传失败: ${error.message}`);
            }
        },
        selectFile(file) { this.selectedFile = file; this.$emit('file-selected', file); },
        async deleteFile(filename, e) {
            e.stopPropagation();
            if (!confirm(`确定要删除文件 "${filename}" 吗？`)) return;
            try {
                const response = await fetch(`/upload/file/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                const result = await response.json();
                if (response.ok) {
                    this.$emit('file-deleted');
                    this.$emit('show-message', 'success', `文件 ${filename} 删除成功`);
                    if (this.selectedFile?.filename === filename) this.selectedFile = null;
                } else {
                    this.$emit('show-message', 'error', `删除失败: ${result.detail}`);
                }
            } catch (error) {
                this.$emit('show-message', 'error', `删除失败: ${error.message}`);
            }
        },
        async clearAllFiles() {
            if (!confirm('确定要清空所有上传的文件吗？此操作不可恢复！')) return;
            try {
                const response = await fetch('/upload/clear', { method: 'DELETE' });
                const result = await response.json();
                if (response.ok) {
                    this.$emit('file-deleted');
                    this.$emit('show-message', 'success', result.message);
                    this.selectedFile = null;
                } else {
                    this.$emit('show-message', 'error', result.detail);
                }
            } catch (error) {
                this.$emit('show-message', 'error', `清空失败: ${error.message}`);
            }
        },
        async processFile(filename) {
            if (!filename) {
                this.$emit('show-message', 'error', '请先选择文件');
                return;
            }
            if (!confirm(`确定要处理文件 "${filename}" 吗？\n\n处理过程包括：\n1. 解析PDF文档\n2. 提取表格数据\n3. 构建RAG索引\n\n这可能需要几分钟时间。`)) {
                return;
            }
            this.processingFile = filename;
            this.$emit('file-process', filename);
            // 处理完成后重置状态
            setTimeout(() => {
                this.processingFile = null;
            }, 1000);
        },
        formatFileSize(bytes) { return (bytes / 1024 / 1024).toFixed(2) + ' MB'; }
    },
    template: `
        <Card title="文件预览" icon="📁" :status="files.length > 0 ? 'content' : 'empty'" empty-text="请上传PDF文件">
            <template #default>
                <div :class="['upload-zone', { dragover: isDragging }]" @dragover.prevent="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop" @click="$refs.fileInput.click()">
                    <input ref="fileInput" type="file" class="file-input" accept=".pdf" multiple @change="handleFileSelect">
                    <p>点击或拖拽上传PDF文件（支持批量）</p>
                </div>
                <div v-if="files.length > 0" class="file-actions">
                    <button class="btn-small" @click="processFile(selectedFile?.filename)" :disabled="!selectedFile || processingFile">
                        {{ processingFile ? '处理中...' : '🔄 处理选中文件' }}
                    </button>
                    <button class="btn-small btn-danger" @click="clearAllFiles">🗑️ 清空所有</button>
                </div>
                <div v-if="files.length > 0" class="file-list">
                    <div v-for="file in files" :key="file.filename" :class="['file-item', { active: selectedFile?.filename === file.filename }]" @click="selectFile(file)">
                        <div class="file-info">
                            <span class="file-icon">📄</span>
                            <div class="file-details">
                                <div class="file-name">{{ file.filename }}</div>
                                <div class="file-size">{{ formatFileSize(file.file_size) }}</div>
                            </div>
                        </div>
                        <button class="file-delete-btn" @click="deleteFile(file.filename, $event)">×</button>
                    </div>
                </div>
            </template>
        </Card>
    `
    };

    // 聊天区域组件 - 增强版
    const ChatArea = {
    name: 'ChatArea',
    props: { messages: { type: Array, default: () => [] }, loading: { type: Boolean, default: false } },
    emits: ['send-message', 'clear-chat', 'agent-query', 'get-suggestions', 'batch-query'],
    data() { 
        return { 
            inputText: '', 
            queryMode: 'normal', // normal, agent, batch
            suggestions: []
        }; 
    },
    methods: {
        sendMessage() {
            if (!this.inputText.trim() || this.loading) return;
            const question = this.inputText.trim();
            this.inputText = '';
            if (this.queryMode === 'agent') {
                this.$emit('agent-query', question);
            } else if (this.queryMode === 'batch') {
                const questions = question.split('\n').filter(q => q.trim());
                this.$emit('batch-query', questions);
            } else {
                this.$emit('send-message', question);
            }
        },
        clearChat() { this.$emit('clear-chat'); },
        async loadSuggestions() {
            this.$emit('get-suggestions');
        },
        useSuggestion(question) {
            this.inputText = question;
        },
        parseMarkdown(text) { return typeof marked !== 'undefined' ? marked.parse(text) : text; }
    },
    mounted() {
        this.$refs.input?.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') this.sendMessage();
        });
    },
    template: `
        <Card title="智能问答" icon="💬" :status="messages.length > 0 || loading ? 'content' : 'empty'" empty-text="开始对话，提出问题">
            <template #default>
                <div class="chat-mode-selector">
                    <button :class="['mode-btn', { active: queryMode === 'normal' }]" @click="queryMode = 'normal'">普通查询</button>
                    <button :class="['mode-btn', { active: queryMode === 'agent' }]" @click="queryMode = 'agent'">Agent分析</button>
                    <button :class="['mode-btn', { active: queryMode === 'batch' }]" @click="queryMode = 'batch'">批量查询</button>
                </div>
                <div class="chat-messages" ref="messagesContainer">
                    <div v-for="(msg, index) in messages" :key="index" :class="['chat-message', msg.type]">
                        <div v-if="msg.type === 'user'" class="message-content">{{ msg.content }}</div>
                        <div v-else class="message-content" v-html="parseMarkdown(msg.content)"></div>
                        <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
                            <div v-for="(source, idx) in msg.sources" :key="idx" class="source-item">{{ source.text.substring(0, 100) }}...</div>
                        </div>
                    </div>
                    <div v-if="loading" class="chat-message assistant loading">
                        <div class="spinner"></div>
                        <span>正在思考...</span>
                    </div>
                </div>
                <div class="chat-input-area">
                    <div class="chat-actions">
                        <button class="btn-icon" @click="loadSuggestions" title="获取建议">💡</button>
                        <button class="btn-icon" @click="clearChat" title="清空对话">🗑️</button>
                    </div>
                    <div v-if="queryMode === 'batch'" class="batch-hint">
                        <small>批量查询模式：每行一个问题</small>
                    </div>
                    <div class="chat-input-wrapper">
                        <textarea ref="input" v-model="inputText" class="chat-input" :placeholder="queryMode === 'batch' ? '输入多个问题，每行一个，按 Ctrl+Enter 发送' : '输入问题，按 Ctrl+Enter 发送'" rows="2"></textarea>
                        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || loading">发送</button>
                    </div>
                </div>
            </template>
        </Card>
    `
    };

    // 企业概况组件 - 增强版
    const CompanyOverview = {
    name: 'CompanyOverview',
    props: { data: { type: Object, default: null }, loading: { type: Boolean, default: false } },
    emits: ['generate-report'],
    data() { return { activeTab: 'basic' }; },
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.data) return 'empty';
            return 'content';
        }
    },
    methods: {
        async generateReport() {
            this.$emit('generate-report');
        },
        parseMarkdown(text) {
            if (!text) return '';
            if (typeof marked !== 'undefined' && marked && marked.parse) {
                return marked.parse(text);
            }
            return text;
        }
    },
    template: `
        <Card title="企业概况" icon="🏢" :status="status" empty-text="暂无企业概况数据">
            <template #default>
                <div class="tabs-container">
                    <div class="tabs-header">
                        <button :class="['tab-btn', { active: activeTab === 'basic' }]" @click="activeTab = 'basic'">基本信息</button>
                        <button :class="['tab-btn', { active: activeTab === 'business' }]" @click="activeTab = 'business'">业务板块</button>
                        <button :class="['tab-btn', { active: activeTab === 'finance' }]" @click="activeTab = 'finance'">财务状况</button>
                    </div>
                    <div class="tabs-content">
                        <div v-if="activeTab === 'basic'" class="tab-panel">
                            <div class="info-item"><span class="info-label">公司名称：</span><span class="info-value">{{ data?.company_name || '—' }}</span></div>
                            <div class="info-item"><span class="info-label">报告年度：</span><span class="info-value">{{ data?.year || '—' }}</span></div>
                            <div class="info-item"><span class="info-label">行业分类：</span><span class="info-value">{{ data?.industry || '—' }}</span></div>
                            <div v-if="!data" class="action-buttons">
                                <button class="btn-primary" @click="generateReport">📊 生成企业概况</button>
                            </div>
                        </div>
                        <div v-if="activeTab === 'business'" class="tab-panel">
                            <div v-if="data?.business" v-html="parseMarkdown(data.business)"></div>
                            <p v-else class="placeholder-text">业务板块信息将在此显示</p>
                        </div>
                        <div v-if="activeTab === 'finance'" class="tab-panel">
                            <div v-if="data?.finance" v-html="parseMarkdown(data.finance)"></div>
                            <p v-else class="placeholder-text">财务状况信息将在此显示</p>
                        </div>
                    </div>
                </div>
            </template>
        </Card>
    `
    };

    // 附注与风险组件 - 增强版
    const NotesAndRisks = {
    name: 'NotesAndRisks',
    props: { data: { type: Object, default: null }, loading: { type: Boolean, default: false } },
    emits: ['generate-section'],
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.data) return 'empty';
            return 'content';
        }
    },
    methods: {
        async generateSection() {
            this.$emit('generate-section', 'financial_review');
        },
        parseMarkdown(text) {
            if (!text) return '';
            if (typeof marked !== 'undefined' && marked && marked.parse) {
                return marked.parse(text);
            }
            return text;
        }
    },
    template: `
        <Card title="附注与风险" icon="⚠️" :status="status" empty-text="暂无附注与风险信息">
            <template #default>
                <div class="notes-risks-content">
                    <div v-if="data?.notes" class="section">
                        <h4>重要附注</h4>
                        <div v-html="parseMarkdown(data.notes)"></div>
                    </div>
                    <div v-if="data?.risks" class="section">
                        <h4>风险提示</h4>
                        <div v-html="parseMarkdown(data.risks)"></div>
                    </div>
                    <div v-if="!data" class="action-buttons">
                        <button class="btn-primary" @click="generateSection">📝 生成附注与风险</button>
                    </div>
                    <div v-if="!data" class="placeholder-text">附注与风险信息将在此显示</div>
                </div>
            </template>
        </Card>
    `
    };

    // 杜邦分析组件
    const DupontAnalysis = {
    name: 'DupontAnalysis',
    props: { data: { type: Object, default: null }, loading: { type: Boolean, default: false } },
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.data) return 'empty';
            return 'content';
        }
    },
    template: `
        <Card title="杜邦分析" icon="📊" :status="status" empty-text="暂无杜邦分析数据">
            <template #default>
                <div class="dupont-content">
                    <div v-if="data" class="dupont-tree">
                        <div class="dupont-item main">
                            <div class="dupont-label">ROE</div>
                            <div class="dupont-value">{{ data.roe || '—' }}</div>
                        </div>
                        <div class="dupont-branches">
                            <div class="dupont-item">
                                <div class="dupont-label">ROA</div>
                                <div class="dupont-value">{{ data.roa || '—' }}</div>
                            </div>
                            <div class="dupont-item">
                                <div class="dupont-label">权益乘数</div>
                                <div class="dupont-value">{{ data.equity_multiplier || '—' }}</div>
                            </div>
                        </div>
                    </div>
                    <div v-else class="placeholder-text">杜邦分析数据将在此显示</div>
                </div>
            </template>
        </Card>
    `
    };

    // 可视化面板组件 - 增强版（包含洞察和推荐）
    const VisualizationPanel = {
    name: 'VisualizationPanel',
    props: { 
        chartData: { type: Object, default: null }, 
        loading: { type: Boolean, default: false } 
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
                        chartDiv.innerHTML = `<div class="error-message"><p>图表渲染失败: ${error.message}</p></div>`;
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
        <Card title="数据可视化" icon="📈" :status="status" empty-text="图表将在此显示">
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

    // 消息提示组件
    const MessageToast = {
    props: ['message'],
    template: `
        <transition name="fade">
            <div v-if="message.text" :class="['message-toast', message.type]">{{ message.text }}</div>
        </transition>
    `
    };

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
        
        const handleBatchQuery = async (questions) => {
            if (questions.length === 0) return;
            queryLoading.value = true;
            try {
                const response = await fetch('/query/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ questions, enable_visualization: true })
                });
                const result = await response.json();
                if (response.ok) {
                    questions.forEach((q, i) => {
                        chatMessages.value.push({ type: 'user', content: q, timestamp: new Date() });
                        const res = result.results[i];
                        if (res.status === 'success') {
                            chatMessages.value.push({ type: 'assistant', content: res.answer, sources: res.sources, timestamp: new Date() });
                        } else {
                            chatMessages.value.push({ type: 'assistant', content: `错误: ${res.error}`, timestamp: new Date() });
                        }
                    });
                } else {
                    showMessage('error', result.detail);
                }
            } catch (error) {
                showMessage('error', `批量查询失败: ${error.message}`);
            } finally {
                queryLoading.value = false;
            }
        };
        
        const handleGetSuggestions = async () => {
            try {
                const response = await fetch('/query/suggestions');
                const data = await response.json();
                suggestions.value = data.suggestions || [];
                if (suggestions.value.length > 0) {
                    const suggestionText = suggestions.value.map(cat => 
                        `${cat.category}:\n${cat.questions.map(q => `- ${q}`).join('\n')}`
                    ).join('\n\n');
                    chatMessages.value.push({ 
                        type: 'assistant', 
                        content: `💡 查询建议：\n\n${suggestionText}`, 
                        timestamp: new Date() 
                    });
                }
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
            handleSendMessage, handleAgentQuery, handleBatchQuery, handleGetSuggestions,
            handleGenerateReport, handleGenerateSection, handleClearChat, checkIndexStatus
        };
    },
    template: `
        <div class="app-container">
            <header class="app-header">
                <div class="header-content">
                    <h1 class="app-title">🚀 LlamaReport Backend</h1>
                    <p class="app-subtitle">智能文档分析与问答系统</p>
                </div>
                <div class="header-status">
                    <span class="status-text">{{ systemStatus }}</span>
                </div>
            </header>
            <main class="app-main">
                <aside class="left-panel">
                    <FilePreviewCard :files="files" @file-selected="handleFileSelected" @file-uploaded="handleFileUploaded" @file-deleted="handleFileDeleted" @file-process="handleFileProcess" @show-message="showMessage" />
                    <ChatArea :messages="chatMessages" :loading="queryLoading" @send-message="handleSendMessage" @agent-query="handleAgentQuery" @batch-query="handleBatchQuery" @get-suggestions="handleGetSuggestions" @clear-chat="handleClearChat" />
                </aside>
                <section class="middle-panel">
                    <div class="middle-top">
                        <CompanyOverview :data="companyOverviewData" :loading="companyOverviewLoading" @generate-report="handleGenerateReport" />
                        <NotesAndRisks :data="notesAndRisksData" :loading="notesAndRisksLoading" @generate-section="handleGenerateSection" />
                    </div>
                    <div class="middle-bottom">
                        <DupontAnalysis :data="dupontData" :loading="dupontLoading" />
                    </div>
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
        
        const app = createApp(App);
        app.component('Card', Card);
        app.component('FilePreviewCard', FilePreviewCard);
        app.component('ChatArea', ChatArea);
        app.component('CompanyOverview', CompanyOverview);
        app.component('NotesAndRisks', NotesAndRisks);
        app.component('DupontAnalysis', DupontAnalysis);
        app.component('VisualizationPanel', VisualizationPanel);
        app.component('MessageToast', MessageToast);
        
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