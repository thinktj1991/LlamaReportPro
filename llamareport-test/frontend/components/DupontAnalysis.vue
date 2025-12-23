<template>
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
</template>

<script>
import Card from './Card.vue'

export default {
  name: 'DupontAnalysis',
  components: {
    Card
  },
  props: { 
    data: { type: Object, default: null }, 
    loading: { type: Boolean, default: false } 
  },
  computed: {
    status() {
      if (this.loading) return 'loading';
      if (!this.data) return 'empty';
      return 'content';
    }
  }
}
</script>

