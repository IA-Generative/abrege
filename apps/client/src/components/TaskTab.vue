<template>
  <div class="task-container fr-container">
    <h2 class="fr-h2">Mes tâches</h2>

    <div class="table-responsive">
      <table class="fr-table task-table">
        <thead>
          <tr>
            <th @click="sortBy('type')">Type ⬍</th>
            <th @click="sortBy('percentage')">Pourcentage ⬍</th>
            <th @click="sortBy('created_at')">Créé le ⬍</th>
            <th @click="sortBy('updated_at')">Mis à jour le ⬍</th>
            <th>Voir résultat</th>
            <th>Détail</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="task in sortedTasks" :key="task.id">
            <td>
              <a
                v-if="task.input?.url"
                :href="task.input.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ task.input.url }}
              </a>
              <span v-else-if="task.input?.text">
                {{ task.input.text.length > 30 ? task.input.text.slice(0, 30) + '...' : task.input.text }}
              </span>
              <span v-else-if="task.input?.raw_filename">{{ task.input.raw_filename }}</span>
              <span v-else>Inconnu</span>
            </td>

            <td>
              <ProgressBar :visible="true" :progress="task.percentage * 100 ?? 0" :text="MapStatusToLabel(task.status)" />
              <div class="fr-ml-1">{{ task.percentage * 100 ?? 0 }}%</div>
            </td>

            <td>{{ formatDate(task.created_at) }}</td>
            <td>{{ formatDate(task.updated_at) }}</td>

            <td>
              <DsfrButton size="sm" priority="secondary" :disabled="task.status !== 'completed'" @click="downloadTaskResult(task)">
                Voir résultat
              </DsfrButton>
            </td>

            <td>
              <DsfrButton
                size="sm"
                priority="secondary"
                icon="ri-eye-line"
                icon-only
                label="Voir le détail"
                :disabled="task.status !== 'completed'"
                @click="router.push({ name: 'task-detail', params: { task_id: task.id } })"
              />
            </td>

            <td>
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
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAbregeStore } from '@/stores/abrege'

const router = useRouter()

const abrege = useAbregeStore()

// ----- TRI -----
const sortKey = ref('created_at')
const sortAsc = ref(false)

function MapStatusToLabel(status) {
  const map = {
    queued: 'En attente',
    in_progress: 'En cours',
    completed: 'Terminé',
    failed: 'Échoué',
  }
  return map[status] || status
}

function sortBy(key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

const sortedTasks = computed(() => {
  const items = abrege.userTasksPaginated?.items ?? []
  if (!sortKey.value) return items
  return [...items].sort((a, b) => {
    const valA = a[sortKey.value]
    const valB = b[sortKey.value]
    if (valA === valB) return 0
    if (sortAsc.value) return valA > valB ? 1 : -1
    return valA < valB ? 1 : -1
  })
})

const loadAll = async () => {
  await abrege.fetchUserTasks(1, 1000)
}

const removeTask = async (taskId) => {
  await abrege.deleteTask(taskId)
}

const cancelTask = async (taskId) => {
  await abrege.cancelTask(taskId)
}

// ----- TÉLÉCHARGEMENT -----
const downloadTaskResult = (task) => {
  if (!task || task.status !== 'completed') return
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

const formatDate = (ts) => {
  if (ts === null || ts === undefined || ts === '') return ''
  let n = Number(ts)
  if (Number.isNaN(n)) return String(ts)
  if (n < 1e12) n = n * 1000
  return new Date(n).toLocaleString()
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.task-container {
  padding: 20px;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.task-table {
  width: 100%;
  min-width: 600px;
  border-collapse: collapse;
}

.task-table th,
.task-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.task-table th {
  cursor: pointer;
}
</style>
