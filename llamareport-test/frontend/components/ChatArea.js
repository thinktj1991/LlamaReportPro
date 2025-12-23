// 聊天区域组件 - 增强版
(function() {
    'use strict';
    
    if (typeof window === 'undefined') return;
    
    if (!window.Components) {
        window.Components = {};
    }
    
    window.Components.ChatArea = {
        name: 'ChatArea',
        props: { 
            messages: { type: Array, default: () => [] }, 
            loading: { type: Boolean, default: false },
            suggestions: { type: Array, default: () => [] }
        },
        emits: ['send-message', 'clear-chat', 'agent-query', 'get-suggestions'],
        data() { 
            return { 
                inputText: '', 
                queryMode: 'normal', // normal, agent
                showSuggestions: false
            }; 
        },
        methods: {
            sendMessage() {
                if (!this.inputText.trim() || this.loading) return;
                const question = this.inputText.trim();
                this.inputText = '';
                if (this.queryMode === 'agent') {
                    this.$emit('agent-query', question);
                } else {
                    this.$emit('send-message', question);
                }
            },
            clearChat() { this.$emit('clear-chat'); },
            async loadSuggestions() {
                if (this.showSuggestions) {
                    // 如果当前已显示，直接隐藏
                    this.showSuggestions = false;
                } else {
                    // 如果当前未显示，先切换状态，然后获取建议
                    this.showSuggestions = true;
                    // 如果没有数据，则获取
                    if (!this.suggestions || this.suggestions.length === 0) {
                        this.$emit('get-suggestions');
                    }
                }
            },
            useSuggestion(question) {
                this.inputText = question;
            },
            parseMarkdown(text) { return typeof marked !== 'undefined' ? marked.parse(text) : text; }
        },
        watch: {
            suggestions: {
                handler(newVal) {
                    // 当有建议数据且面板应该显示时，确保显示
                    if (newVal && newVal.length > 0 && this.showSuggestions) {
                        this.$nextTick(() => {
                            // 确保面板显示
                        });
                    }
                },
                immediate: true
            }
        },
        mounted() {
            this.$nextTick(() => {
                this.$refs.input?.addEventListener('keydown', (e) => {
                    if (e.ctrlKey && e.key === 'Enter') this.sendMessage();
                });
            });
        },
        template: `
            <Card title="智能问答" icon="💬" status="content" empty-text="开始对话，提出问题">
                <template #default>
                    <div class="chat-container">
                        <div class="chat-mode-selector">
                            <button :class="['mode-btn', { active: queryMode === 'normal' }]" @click="queryMode = 'normal'">普通查询</button>
                            <button :class="['mode-btn', { active: queryMode === 'agent' }]" @click="queryMode = 'agent'">Agent分析</button>
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
                        <div v-if="showSuggestions" class="suggestions-panel">
                            <div class="suggestions-header">
                                <span>💡 查询建议</span>
                                <button class="btn-close" @click="showSuggestions = false" title="收起">×</button>
                            </div>
                            <div v-if="suggestions.length === 0" class="suggestions-loading">
                                <div class="spinner-small"></div>
                                <span>正在加载建议...</span>
                            </div>
                            <div v-else class="suggestions-container">
                                <div v-for="(category, catIndex) in suggestions" :key="catIndex" class="suggestion-category">
                                    <div class="category-title">{{ category.category }}</div>
                                    <div class="suggestion-questions">
                                        <button 
                                            v-for="(question, qIndex) in category.questions" 
                                            :key="qIndex" 
                                            class="suggestion-btn"
                                            @click="useSuggestion(question); showSuggestions = false"
                                        >
                                            {{ question }}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="chat-actions">
                                <button :class="['btn-icon', { active: showSuggestions }]" @click="loadSuggestions" title="获取建议">💡</button>
                                <button class="btn-icon" @click="clearChat" title="清空对话">🗑️</button>
                            </div>
                            <div class="chat-input-wrapper">
                                <textarea ref="input" v-model="inputText" class="chat-input" placeholder="输入问题，按 Ctrl+Enter 发送" rows="1"></textarea>
                                <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || loading">发送</button>
                            </div>
                        </div>
                    </div>
                </template>
            </Card>
        `
    };
    
    console.log('✅ ChatArea组件已加载');
})();
