<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAbregeStore } from '@/stores/abrege'

const router = useRouter()

const abrege = useAbregeStore()

// ----- TRI -----
const sortKey = ref('created_at')
const sortAsc = ref(false)

const sortOptions = [
  { key: 'type', label: 'Type' },
  { key: 'percentage', label: 'Pourcentage' },
  { key: 'created_at', label: 'Créé le' },
  { key: 'updated_at', label: 'Mis à jour le' },
]

function MapStatusToLabel (status) {
  const map = {
    queued: 'En attente',
    in_progress: 'En cours',
    completed: 'Terminé',
    failed: 'Échoué',
  }
  return map[status] || status
}

function sortBy (key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

const sortedTasks = computed(() => {
  const items = abrege.userTasksPaginated?.items ?? []
  if (!sortKey.value) {
    return items
  }
  return [...items].sort((a, b) => {
    const valA = a[sortKey.value]
    const valB = b[sortKey.value]
    if (valA === valB) {
      return 0
    }
    if (sortAsc.value) {
      return valA > valB ? 1 : -1
    }
    return valA < valB ? 1 : -1
  })
})

async function loadAll () {
  await abrege.fetchUserTasks(1, 1000)
}

async function removeTask (taskId) {
  await abrege.deleteTask(taskId)
}

async function cancelTask (taskId) {
  await abrege.cancelTask(taskId)
}

// ----- TÉLÉCHARGEMENT -----
function downloadTaskResult (task) {
  if (!task || task.status !== 'completed') {
    return
  }
  const text = task.output?.summary ?? ''
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  let baseName
  if (task.input?.raw_filename) {
    baseName = task.input.raw_filename.replace(/\.[^/.]+$/, '')
  } else if (task.input?.url) {
    baseName = 'resume-url'
  } else {
    baseName = `resume-${task.id}`
  }
  a.download = `${baseName}.txt`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function formatDate (ts) {
  if (ts === null || ts === undefined || ts === '') {
    return ''
  }
  let n = Number(ts)
  if (Number.isNaN(n)) {
    return String(ts)
  }
  if (n < 1e12) {
    n = n * 1000
  }
  return new Date(n).toLocaleString()
}

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="task-container fr-container">
    <h2 class="fr-h2">
      Mes tâches
    </h2>

    <div class="task-sort-bar">
      <span class="fr-text--sm task-sort-label">Trier par :</span>
      <DsfrButton
        v-for="option in sortOptions"
        :key="option.key"
        size="sm"
        :priority="sortKey === option.key ? 'primary' : 'tertiary'"
        @click="sortBy(option.key)"
      >
        {{ option.label }}<span v-if="sortKey === option.key">{{ sortAsc ? ' ↑' : ' ↓' }}</span>
      </DsfrButton>
    </div>

    <div class="task-tile-grid">
      <div
        v-for="task in sortedTasks"
        :key="task.id"
        class="task-tile"
      >
        <div class="task-tile-title">
          <a
            v-if="task.input?.url"
            :href="task.input.url"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ task.input.url }}
          </a>
          <span v-else-if="task.input?.text">
            {{ task.input.text.length > 30 ? `${task.input.text.slice(0, 30)}...` : task.input.text }}
          </span>
          <span v-else-if="task.input?.raw_filename">{{ task.input.raw_filename }}</span>
          <span v-else>Inconnu</span>
        </div>

        <ProgressBar
          :visible="true"
          :progress="(task.percentage ?? 0) * 100"
          :text="MapStatusToLabel(task.status)"
        />

        <dl class="task-tile-dates">
          <div>
            <dt>Créé le</dt>
            <dd>{{ formatDate(task.created_at) }}</dd>
          </div>
          <div>
            <dt>Mis à jour le</dt>
            <dd>{{ formatDate(task.updated_at) }}</dd>
          </div>
        </dl>

        <div class="task-tile-actions">
          <DsfrButton
            size="sm"
            priority="tertiary"
            :disabled="task.status !== 'completed'"
            @click="router.push({ name: 'task-detail', params: { task_id: task.id } })"
          >
            Voir le détail
          </DsfrButton>

          <DsfrButton
            size="sm"
            priority="secondary"
            :disabled="task.status !== 'completed'"
            @click="downloadTaskResult(task)"
          >
            Voir résultat
          </DsfrButton>

          <DsfrButton
            v-if="['queued', 'started', 'in_progress', 'created'].includes(task.status)"
            size="sm"
            priority="secondary"
            icon="ri-stop-circle-line"
            @click="cancelTask(task.id)"
          >
            Annuler
          </DsfrButton>
          <DsfrButton
            v-else
            size="sm"
            priority="tertiary"
            icon="ri-delete-bin-line"
            :disabled="!['completed', 'failed', 'canceled', 'timeout'].includes(task.status)"
            @click="removeTask(task.id)"
          >
            Supprimer
          </DsfrButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-container {
  padding: 20px;
}

.task-sort-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.task-sort-label {
  margin-right: 0.25rem;
}

.task-tile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.task-tile {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  background: #fff;
}

.task-tile-title {
  font-weight: bold;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.task-tile-dates {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.5rem;
  margin: 0;
  font-size: 0.875rem;
}

.task-tile-dates dt {
  color: #666;
}

.task-tile-dates dd {
  margin: 0;
}

.task-tile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: auto;
}
</style>
