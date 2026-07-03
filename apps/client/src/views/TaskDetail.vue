<script setup lang="ts">
import type { components } from '@/api/types/api.schema'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ResumeResult from '@/components/ResumeResult.vue'
import { useAbregeStore } from '@/stores/abrege'

type TaskModel = components['schemas']['TaskModel']

const route = useRoute()
const router = useRouter()
const abrege = useAbregeStore()

const task = ref<TaskModel | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const taskId = computed(() => route.params.task_id as string)

const inputLabel = computed(() => {
  if (!task.value?.input) return null
  if (task.value.input.url) return task.value.input.url
  if (task.value.input.raw_filename) return task.value.input.raw_filename
  if (task.value.input.text) {
    const t = task.value.input.text
    return t.length > 80 ? t.slice(0, 80) + '…' : t
  }
  return null
})

const inputType = computed(() => {
  if (!task.value?.input) return null
  if (task.value.input.url) return 'URL'
  if (task.value.input.raw_filename) return 'Document'
  if (task.value.input.text) return 'Texte'
  return null
})

onMounted(async () => {
  try {
    task.value = await abrege.getTask(taskId.value)
  } catch (e: any) {
    error.value = e.message ?? 'Impossible de charger la tâche.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="task-detail-page fr-container fr-py-4w">
    <DsfrButton
      label="Retour aux tâches"
      icon="ri-arrow-left-line"
      tertiary
      no-outline
      size="sm"
      class="fr-mb-3w"
      @click="router.back()"
    />

    <div v-if="loading" class="fr-mt-4w">
      <p class="fr-text--sm">Chargement…</p>
    </div>

    <div v-else-if="error" class="fr-alert fr-alert--error fr-mt-4w">
      <p>{{ error }}</p>
    </div>

    <template v-else-if="task">
      <div class="task-detail-header fr-mb-4w">
        <div class="task-detail-meta">
          <span v-if="inputType" class="fr-badge fr-badge--info fr-mr-2w">{{ inputType }}</span>
          <span class="fr-text--sm fr-text-mention--grey">Tâche {{ task.id }}</span>
        </div>
        <a
          v-if="task.input?.url"
          :href="task.input.url"
          class="task-detail-source"
          target="_blank"
          rel="noopener noreferrer"
        >{{ task.input.url }}</a>
        <p v-else-if="inputLabel" class="task-detail-source">{{ inputLabel }}</p>
      </div>

      <div v-if="task.status === 'completed' && task.output">
        <ResumeResult
          :resume-result="task"
          @reGenerate="router.push({ name: 'resume-tab', params: { tab: 'tasks' } })"
        />
      </div>

      <div v-else class="fr-alert fr-alert--warning fr-mt-4w">
        <p>Ce résumé n'est pas encore disponible (statut : {{ task.status }}).</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.task-detail-page {
  max-width: 860px;
}
.task-detail-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.task-detail-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}
.task-detail-source {
  font-size: 0.875rem;
  color: var(--text-mention-grey);
  word-break: break-all;
  margin: 0;
}
</style>
