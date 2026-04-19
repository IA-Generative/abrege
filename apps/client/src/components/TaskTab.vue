<template>
  <div class="task-container fr-container">
    <h2 class="fr-h2">
      Liste des tâches
    </h2>
    <DsfrButton
      size="sm"
      priority="secondary"
      class="fr-ml-1"
      @click="statsVisible = true"
    >
      Voir les statistiques
    </DsfrButton>

    <table class="fr-table task-table">
      <thead>
        <tr>
          <th>ID</th>
          <th @click="sortBy('type')">
            Type ⬍
          </th>
          <th>Source</th>
          <th @click="sortBy('percentage')">
            Pourcentage ⬍
          </th>
          <th @click="sortBy('created_at')">
            Créé le ⬍
          </th>
          <th @click="sortBy('updated_at')">
            Mis à jour le ⬍
          </th>
          <th>Voir résumé</th>
          <th>Supprimer</th>
        </tr>
      </thead>

      <tbody>
        <template
          v-for="task in paginatedTasks"
          :key="task.id"
        >
          <tr :class="{ 'merge-row': task.type === 'merge' }">
            <td>
              <code
                :title="task.id"
                style="font-size: 0.75rem; cursor: default"
              >{{ task.id?.slice(0, 8) }}…</code>
            </td>
            <td>{{ task.type ?? '—' }}</td>
            <td>
              <button
                v-if="task.type === 'merge'"
                class="merge-expand-btn"
                :title="expandedMergeRows.has(task.id) ? 'Masquer les sources' : 'Voir les sources'"
                @click="toggleMergeExpand(task)"
              >
                {{ (task.input as any)?.task_ids?.length ?? 0 }} source(s)
                {{ expandedMergeRows.has(task.id) ? '▲' : '▼' }}
              </button>
              <span v-else-if="task.input?.raw_filename">{{ task.input.raw_filename }}</span>
              <a
                v-else-if="task.input?.url"
                :href="task.input.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ task.input.url }}
              </a>
              <span v-else>—</span>
            </td>
            <td>
              <ProgressBar
                :visible="true"
                :progress="(task.percentage ?? 0) * 100"
                :text="MapStatusToLabel(task.status)"
              />
            </td>
            <td>{{ formatDate(task.created_at) }}</td>
            <td>{{ formatDate(task.updated_at) }}</td>
            <td>
              <DsfrButton
                size="sm"
                priority="secondary"
                :disabled="task.status !== 'completed'"
                @click="openModal(task)"
              >
                Voir résumé
              </DsfrButton>
            </td>
            <td>
              <DsfrButton
                size="sm"
                priority="tertiary"
                @click="removeTask(task.id)"
              >
                Supprimer
              </DsfrButton>
            </td>
          </tr>

          <!-- Sous-ligne expansible pour les tâches merge -->
          <tr
            v-if="task.type === 'merge' && expandedMergeRows.has(task.id)"
            class="merge-expand-row"
          >
            <td colspan="8">
              <div class="merge-children">
                <div
                  v-if="!mergeChildTasks[task.id]"
                  class="merge-loading"
                >
                  Chargement des sources…
                </div>
                <table
                  v-else
                  class="merge-children-table"
                >
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Source</th>
                      <th>Statut</th>
                      <th>Voir résumé</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="child in mergeChildTasks[task.id]"
                      :key="child.id"
                    >
                      <td>
                        <code
                          :title="child.id"
                          style="font-size: 0.75rem; cursor: default"
                        >{{ child.id?.slice(0, 8) }}…</code>
                      </td>
                      <td>
                        <span v-if="child.input?.raw_filename">{{ child.input.raw_filename }}</span>
                        <a
                          v-else-if="child.input?.url"
                          :href="child.input.url"
                          target="_blank"
                          rel="noopener noreferrer"
                        >{{ child.input.url }}</a>
                        <span v-else>—</span>
                      </td>
                      <td>{{ MapStatusToLabel(child.status) }}</td>
                      <td>
                        <DsfrButton
                          size="sm"
                          priority="secondary"
                          :disabled="child.status !== 'completed'"
                          @click="openModal(child)"
                        >
                          Voir résumé
                        </DsfrButton>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <!-- Pagination -->
    <div class="pagination fr-mt-2">
      <DsfrButton
        size="sm"
        priority="tertiary"
        :disabled="paginatedData.page === 1"
        @click="loadPage(paginatedData.page - 1)"
      >
        Précédent
      </DsfrButton>
      <span class="fr-ml-2 fr-mr-2">Page {{ paginatedData.page }} / {{ totalPages }}</span>
      <DsfrButton
        size="sm"
        priority="tertiary"
        :disabled="paginatedData.page === totalPages"
        @click="loadPage(paginatedData.page + 1)"
      >
        Suivant
      </DsfrButton>
    </div>

    <!-- Modal résumé -->
    <ResumeResultModal
      v-if="selectedTask"
      :results="[{ filename: selectedTask.input?.raw_filename || selectedTask.input?.url || 'Tâche', task: selectedTask }]"
      @close="selectedTask = null"
      @re-generate="selectedTask = null"
    />

    <!-- Stats Modal -->
    <StatModel
      v-if="statsVisible"
      @close="statsVisible = false"
    />

    <!-- Connected users badge -->
    <div
      class="connected-badge"
      title="Utilisateurs qu'ont utilisé le service aujourd'hui"
    >
      <span class="badge-emoji">👥</span>
      <span class="badge-number">{{ connectedUsers ?? '—' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'
import { useAbregeStore } from '@/stores/abrege'
import StatModel from './StatModel.vue'

const abrege = useAbregeStore()
const paginatedData = abrege.userTasksPaginated

// ----- UTILISATEURS CONNECTÉS -----
const connectedUsers = ref<number | null>(null)
const http = createHttpClient(ABREGE_API_URL)

const fetchConnectedUsers = async () => {
  try {
    const { data } = await http.get('/tasks/count-users-today')
    connectedUsers.value = data?.users_today ?? null
  }
  catch {
    connectedUsers.value = null
  }
}

// ----- TRI -----
const sortKey = ref('')
const sortAsc = ref(true)

function MapStatusToLabel (status: string) {
  const map: Record<string, string> = {
    queued: 'En attente',
    in_progress: 'En cours',
    completed: 'Terminé',
    failed: 'Échoué',
  }
  return map[status] || status
}

function sortBy (key: string) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  }
  else {
    sortKey.value = key
    sortAsc.value = true
  }
}

const paginatedTasks = computed(() => {
  const resolved = paginatedData && Object.prototype.hasOwnProperty.call(paginatedData, 'value')
    ? (paginatedData as any).value
    : paginatedData
  const items = resolved?.items ?? []
  if (!sortKey.value) return items
  return [...items].sort((a, b) => {
    const valA = a[sortKey.value]
    const valB = b[sortKey.value]
    if (valA === valB) return 0
    return sortAsc.value ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1)
  })
})

// ----- PAGINATION -----
const totalPages = computed(() => {
  const total = (paginatedData as any).value?.total ?? 0
  const pageSize = (paginatedData as any).value?.page_size ?? 1
  return Math.max(1, Math.ceil(total / pageSize))
})

const loadPage = async (page = 1, overridePageSize?: number) => {
  const pageSize = overridePageSize ?? (paginatedData as any)?.page_size ?? 10
  await abrege.fetchUserTasks(page, pageSize)
  await fetchConnectedUsers()
}

// ----- FORMATAGE -----
const formatDate = (ts: unknown) => {
  if (ts === null || ts === undefined || ts === '') return ''
  try {
    let n = Number(ts)
    if (Number.isNaN(n)) return String(ts)
    if (n < 1e12) n = n * 1000
    return new Date(n).toLocaleString()
  }
  catch {
    return String(ts)
  }
}

// ----- MERGE EXPAND -----
const expandedMergeRows = ref(new Set<string>())
const mergeChildTasks = ref<Record<string, any[]>>({})

async function toggleMergeExpand (task: any) {
  const id = task.id
  if (expandedMergeRows.value.has(id)) {
    expandedMergeRows.value = new Set([...expandedMergeRows.value].filter(x => x !== id))
    return
  }
  expandedMergeRows.value = new Set([...expandedMergeRows.value, id])
  if (!mergeChildTasks.value[id]) {
    const taskIds: string[] = (task.input as any)?.task_ids ?? []
    const children = await Promise.all(
      taskIds.map(async (tid: string) => {
        try {
          const { data } = await http.get(`/task/${tid}`)
          return data
        }
        catch {
          return null
        }
      }),
    )
    mergeChildTasks.value = { ...mergeChildTasks.value, [id]: children.filter(Boolean) }
  }
}

// ----- MODAL -----
const selectedTask = ref(null)
const statsVisible = ref(false)

const openModal = (task: any) => {
  if (!task || task.status !== 'completed') return
  selectedTask.value = task
}

// ----- SUPPRESSION -----
const removeTask = async (taskId: string) => {
  if (!taskId) return
  try {
    await abrege.deleteTask(taskId)
    const page = (paginatedData as any).value?.page ?? (paginatedData as any).page ?? 1
    const pageSize = (paginatedData as any).value?.page_size ?? (paginatedData as any).page_size ?? 10
    await loadPage(page, pageSize)
  }
  catch (e) {
    console.error('Failed to remove task', e)
  }
}

// ----- LIFECYCLE -----
const onEsc = (e: KeyboardEvent) => {
  if (e.key === 'Escape') selectedTask.value = null
}

onMounted(() => {
  loadPage(1)
  window.addEventListener('keydown', onEsc)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onEsc)
  if (typeof abrege.stopPollingUserTasks === 'function') {
    abrege.stopPollingUserTasks()
  }
})
</script>

<style scoped>
.task-container {
  padding: 20px;
  position: relative;
}

.task-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.task-table th,
.task-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
  cursor: pointer;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: center;
  gap: 15px;
}

.connected-badge {
  position: absolute;
  right: 12px;
  bottom: 12px;
  background: #0b6bff;
  color: white;
  padding: 6px 10px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 6px 18px rgba(11, 107, 255, 0.15);
  font-weight: 600;
}

.connected-badge .badge-emoji {
  font-size: 14px;
}

.connected-badge .badge-number {
  min-width: 32px;
  text-align: center;
}

.merge-row td {
  background: var(--blue-france-975-75, #f5f5fe);
}

.merge-expand-btn {
  background: none;
  border: 1px solid var(--blue-france-sun-113-625, #000091);
  color: var(--blue-france-sun-113-625, #000091);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
}

.merge-expand-btn:hover {
  background: var(--blue-france-950-100, #ececfe);
}

.merge-expand-row td {
  background: var(--grey-950-100, #f0f0f0);
  padding: 0.75rem 1rem;
}

.merge-children {
  padding: 0.25rem 0;
}

.merge-loading {
  font-style: italic;
  color: #666;
  padding: 0.5rem;
}

.merge-children-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.merge-children-table th,
.merge-children-table td {
  border: 1px solid #ddd;
  padding: 6px 8px;
  text-align: center;
}

.merge-children-table thead th {
  background: var(--blue-france-925-125, #e3e3fd);
  font-weight: 600;
}
</style>
