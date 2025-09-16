<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ visible: boolean, progress: number }>()

const progressColor = computed(() => {
  if (props.progress < 25) {
    return '#e8edff'
  }

  if (props.progress < 50) {
    return '#dde5ff'
  }

  if (props.progress < 75) {
    return '#bccdff'
  }

  if (props.progress < 100) {
    return 'var(--background-flat-info)'
  }

  return 'var(--artwork-major-blue-france)'
})
</script>

<template>
  <div
    v-if="visible"
    class="mt-4"
  >
    <div>En cours de chargement... ({{ progress }}%)</div>
    <div class="progress-bar-container">
      <div
        class="progress-bar"
        :style="{ width: `${progress}%`, backgroundColor: progressColor }"
      />
    </div>
  </div>
</template>

<style scoped>
.mt-4 {
    margin-top: 1rem;
}

.progress-bar-container {
    width: 100%;
    background-color: var(--info-950-100);
    height: 15px;
    border-radius: 4px;
    margin-top: 8px;
    overflow: hidden;
    position: relative;
}

.progress-bar {
    height: 100%;
    transition: width 0.3s, background-color 0.3s;
}
</style>
