// 企业概况组件
export default {
    name: 'CompanyOverview',
    props: {
        data: {
            type: Object,
            default: null
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            activeTab: 'basic'
        };
    },
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.data) return 'empty';
            return 'content';
        }
    },
    template: `
        <Card 
            title="企业概况" 
            icon="🏢"
            :status="status"
            empty-text="暂无企业概况数据"
        >
            <template #default>
                <div class="tabs-container">
                    <div class="tabs-header">
                        <button 
                            :class="['tab-btn', { active: activeTab === 'basic' }]"
                            @click="activeTab = 'basic'"
                        >
                            基本信息
                        </button>
                        <button 
                            :class="['tab-btn', { active: activeTab === 'business' }]"
                            @click="activeTab = 'business'"
                        >
                            业务板块
                        </button>
                        <button 
                            :class="['tab-btn', { active: activeTab === 'finance' }]"
                            @click="activeTab = 'finance'"
                        >
                            财务状况
                        </button>
                    </div>
                    <div class="tabs-content">
                        <div v-if="activeTab === 'basic'" class="tab-panel">
                            <div class="info-item">
                                <span class="info-label">公司名称：</span>
                                <span class="info-value">{{ data?.company_name || '—' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">报告年度：</span>
                                <span class="info-value">{{ data?.year || '—' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">行业分类：</span>
                                <span class="info-value">{{ data?.industry || '—' }}</span>
                            </div>
                        </div>
                        <div v-if="activeTab === 'business'" class="tab-panel">
                            <p class="placeholder-text">业务板块信息将在此显示</p>
                        </div>
                        <div v-if="activeTab === 'finance'" class="tab-panel">
                            <p class="placeholder-text">财务状况信息将在此显示</p>
                        </div>
                    </div>
                </div>
            </template>
        </Card>
    `
};
