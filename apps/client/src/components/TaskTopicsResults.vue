<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import TopicsCard from './TopicsCard.vue'

const props = defineProps<{
  taskId: string
  status?: string | null
}>()

const abrege = useAbregeStore()

onMounted(() => abrege.fetchTopics(props.taskId))

// The task is polled while classification is pending: load the topics as soon as it completes.
watch(() => props.status, (status, previous) => {
  if (status === 'completed' && previous !== 'completed') {
    abrege.fetchTopics(props.taskId)
  }
})
</script>

<template>
  <p
    v-if="abrege.topicsLoading"
    class="fr-text--sm"
  >
    Chargement…
  </p>
  <TopicsCard
    v-else
    :topics="abrege.topics"
    :status="status"
    embedded
  />
</template>
