<script setup lang="ts">
import { computed } from 'vue'
import { describeError } from '@/utils/error-codes'

const props = defineProps<{
  status?: string | null
  label: string
  errorCode?: number | null
}>()

type BadgeType = 'info' | 'success' | 'error' | 'warning'

const config = computed((): { type: BadgeType, text: string } | null => {
  switch (props.status) {
    case 'in_progress':
    case 'pending':
      return { type: 'info', text: 'En cours…' }
    case 'completed':
      return { type: 'success', text: 'Terminé' }
    case 'failed':
      return { type: 'error', text: props.errorCode ? `Échec ${props.errorCode}` : 'Échec' }
    default:
      return null
  }
})
</script>

<template>
  <DsfrBadge
    v-if="config"
    :label="`${label} : ${config.text}`"
    :type="config.type"
    small
    :title="status === 'failed' ? describeError(errorCode) : undefined"
    class="extraction-status-badge"
    :class="{ 'extraction-status-badge--pending': status === 'in_progress' || status === 'pending' }"
  />
</template>

<style scoped>
.extraction-status-badge--pending {
  animation: extraction-status-pulse 1.6s ease-in-out infinite;
}
@keyframes extraction-status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}
</style>
