// 附注与风险组件
export default {
    name: 'NotesAndRisks',
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
    computed: {
        status() {
            if (this.loading) return 'loading';
            if (!this.data) return 'empty';
            return 'content';
        }
    },
    template: `
        <Card 
            title="附注与风险" 
            icon="⚠️"
            :status="status"
            empty-text="暂无附注与风险信息"
        >
            <template #default>
                <div class="notes-risks-content">
                    <div v-if="data?.notes" class="section">
                        <h4>重要附注</h4>
                        <ul class="notes-list">
                            <li v-for="(note, index) in data.notes" :key="index">{{ note }}</li>
                        </ul>
                    </div>
                    <div v-if="data?.risks" class="section">
                        <h4>风险提示</h4>
                        <ul class="risks-list">
                            <li v-for="(risk, index) in data.risks" :key="index">{{ risk }}</li>
                        </ul>
                    </div>
                    <div v-if="!data" class="placeholder-text">
                        附注与风险信息将在此显示
                    </div>
                </div>
            </template>
        </Card>
    `
};
