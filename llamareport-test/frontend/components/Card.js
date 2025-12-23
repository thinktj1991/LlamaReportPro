// 通用卡片组件 - 支持 loading/empty/error 状态
export default {
    name: 'Card',
    props: {
        title: {
            type: String,
            required: true
        },
        icon: {
            type: String,
            default: '📄'
        },
        status: {
            type: String,
            default: 'empty', // 'loading' | 'empty' | 'error' | 'content'
            validator: (value) => ['loading', 'empty', 'error', 'content'].includes(value)
        },
        emptyText: {
            type: String,
            default: '暂无数据'
        },
        errorText: {
            type: String,
            default: '加载失败'
        }
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
