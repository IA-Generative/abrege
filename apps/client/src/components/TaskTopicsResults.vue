<script setup lang="ts">
import { onMounted } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import TopicsCard from './TopicsCard.vue'

const props = defineProps<{
  taskId: string
  status?: string | null
}>()

const abrege = useAbregeStore()

onMounted(() => abrege.fetchTopics(props.taskId))
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
