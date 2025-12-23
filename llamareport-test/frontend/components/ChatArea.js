// 聊天区域组件
export default {
    name: 'ChatArea',
    props: {
        messages: {
            type: Array,
            default: () => []
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    emits: ['send-message', 'clear-chat'],
    data() {
        return {
            inputText: ''
        };
    },
    methods: {
        sendMessage() {
            if (!this.inputText.trim() || this.loading) return;
            
            const question = this.inputText.trim();
            this.inputText = '';
            this.$emit('send-message', question);
        },
        clearChat() {
            this.$emit('clear-chat');
        },
        parseMarkdown(text) {
            if (typeof marked !== 'undefined') {
                return marked.parse(text);
            }
            return text;
        }
    },
    mounted() {
        // 支持 Ctrl+Enter 发送
        this.$refs.input?.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.sendMessage();
            }
        });
    },
    template: `
        <Card 
            title="智能问答" 
            icon="💬"
            :status="messages.length > 0 || loading ? 'content' : 'empty'"
            empty-text="开始对话，提出问题"
        >
            <template #default>
                <div class="chat-messages" ref="messagesContainer">
                    <div 
                        v-for="(msg, index) in messages" 
                        :key="index"
                        :class="['chat-message', msg.type]"
                    >
                        <div v-if="msg.type === 'user'" class="message-content">
                            {{ msg.content }}
                        </div>
                        <div v-else class="message-content" v-html="parseMarkdown(msg.content)"></div>
                        <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
                            <div 
                                v-for="(source, idx) in msg.sources" 
                                :key="idx"
                                class="source-item"
                            >
                                {{ source.text.substring(0, 100) }}...
                            </div>
                        </div>
                    </div>
                    <div v-if="loading" class="chat-message assistant loading">
                        <div class="spinner"></div>
                        <span>正在思考...</span>
                    </div>
                </div>
                <div class="chat-input-area">
                    <div class="chat-actions">
                        <button class="btn-icon" @click="clearChat" title="清空对话">🗑️</button>
                    </div>
                    <div class="chat-input-wrapper">
                        <textarea
                            ref="input"
                            v-model="inputText"
                            class="chat-input"
                            placeholder="输入问题，按 Ctrl+Enter 发送"
                            rows="2"
                        ></textarea>
                        <button 
                            class="send-btn"
                            @click="sendMessage"
                            :disabled="!inputText.trim() || loading"
                        >
                            发送
                        </button>
                    </div>
                </div>
            </template>
        </Card>
    `
};
