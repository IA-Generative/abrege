<script setup lang="ts">
import type { components } from '@/api/types/api.schema'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ResumeResult from '@/components/ResumeResult.vue'
import { useAbregeStore } from '@/stores/abrege'

// The generated schema doesn't yet know about these — the API already returns them.
type TaskModel = components['schemas']['TaskModel'] & {
  qa_entities_status?: string | null
  relationships_status?: string | null
  topics_status?: string | null
  qa_entities_error?: number | null
  relationships_error?: number | null
  topics_error?: number | null
}

const route = useRoute()
const router = useRouter()
const abrege = useAbregeStore()

const task = ref<TaskModel | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const taskId = computed(() => route.params.task_id as string)

const PENDING_STATUSES = new Set(['in_progress', 'pending'])
let statusPollTimer: ReturnType<typeof setInterval> | null = null

function isStillPending (): boolean {
  if (!task.value) { return false }
  return (
    PENDING_STATUSES.has(task.value.qa_entities_status ?? '')
    || PENDING_STATUSES.has(task.value.relationships_status ?? '')
    || PENDING_STATUSES.has(task.value.topics_status ?? '')
  )
}

// After a retry the status can stay "failed" for a moment, until the worker picks the job up:
// keep polling a few more ticks even when nothing looks pending.
let graceTicks = 0

function startStatusPolling () {
  if (statusPollTimer) { return }
  statusPollTimer = setInterval(async () => {
    if (!isStillPending() && graceTicks <= 0) {
      if (statusPollTimer) { clearInterval(statusPollTimer) }
      statusPollTimer = null
      return
    }
    graceTicks -= 1
    const refreshed = await abrege.getTask(taskId.value) as TaskModel
    task.value = refreshed
  }, 3000)
}

async function onRetry () {
  graceTicks = 5
  task.value = await abrege.getTask(taskId.value) as TaskModel
  startStatusPolling()
}

onBeforeUnmount(() => {
  if (statusPollTimer) { clearInterval(statusPollTimer) }
})

const inputLabel = computed(() => {
  if (!task.value?.input) { return null }
  if (task.value.input.url) { return task.value.input.url }
  if (task.value.input.raw_filename) { return task.value.input.raw_filename }
  if (task.value.input.text) {
    const t = task.value.input.text
    return t.length > 80 ? `${t.slice(0, 80)}…` : t
  }
  return null
})

const inputType = computed(() => {
  if (!task.value?.input) { return null }
  if (task.value.input.url) { return 'URL' }
  if (task.value.input.raw_filename) { return 'Document' }
  if (task.value.input.text) { return 'Texte' }
  return null
})

onMounted(async () => {
  try {
    task.value = await abrege.getTask(taskId.value) as TaskModel
    if (task.value?.status === 'completed') {
      if (isStillPending()) { startStatusPolling() }
    }
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

    <div
      v-if="loading"
      class="fr-mt-4w"
    >
      <p class="fr-text--sm">
        Chargement…
      </p>
    </div>

    <div
      v-else-if="error"
      class="fr-alert fr-alert--error fr-mt-4w"
    >
      <p>{{ error }}</p>
    </div>

    <template v-else-if="task">
      <div class="task-detail-header fr-mb-4w">
        <div class="task-detail-meta">
          <span
            v-if="inputType"
            class="fr-badge fr-badge--info fr-mr-2w"
          >{{ inputType }}</span>
          <span class="fr-text--sm fr-text-mention--grey">Tâche {{ task.id }}</span>
        </div>
        <a
          v-if="task.input?.url"
          :href="task.input.url"
          class="task-detail-source"
          target="_blank"
          rel="noopener noreferrer"
        >{{ task.input.url }}</a>
        <p
          v-else-if="inputLabel"
          class="task-detail-source"
        >
          {{ inputLabel }}
        </p>
      </div>

      <div v-if="task.status === 'completed' && task.output">
        <ResumeResult
          :resume-result="task"
          @re-generate="router.push({ name: 'resume-tab', params: { tab: 'tasks' } })"
          @retry="onRetry"
        />
      </div>

      <div
        v-else
        class="fr-alert fr-alert--warning fr-mt-4w"
      >
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
