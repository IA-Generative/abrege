<template>
  <div class="tasks-page">

    <!-- Header -->
    <div class="tasks-header">
      <div>
        <h2 class="tasks-title">Tâches</h2>
        <p class="tasks-subtitle">{{ paginatedDataSafe.total ?? 0 }} tâche{{ (paginatedDataSafe.total ?? 0) !== 1 ? 's' : '' }} au total</p>
      </div>
      <div class="tasks-header-actions">
        <button class="action-btn" @click="statsVisible = true">
          <span class="fr-icon-bar-chart-box-line" aria-hidden="true" />
          Statistiques
        </button>
        <button class="action-btn" @click="leaderboardVisible = true">
          <span class="fr-icon-trophy-line" aria-hidden="true" />
          Leaderboard
        </button>
        <div class="users-pill" title="Utilisateurs actifs aujourd'hui">
          <span class="fr-icon-user-line" style="font-size:13px" aria-hidden="true" />
          <span>{{ connectedUsers ?? '—' }}</span>
        </div>
      </div>
    </div>

    <!-- Sort bar -->
    <div class="sort-bar">
      <span class="sort-label">Trier par</span>
      <button :class="['sort-btn', sortKey === 'created_at' ? 'sort-active' : '']" @click="sortBy('created_at')">
        Date <span>{{ sortKey === 'created_at' ? (sortAsc ? '↑' : '↓') : '' }}</span>
      </button>
      <button :class="['sort-btn', sortKey === 'type' ? 'sort-active' : '']" @click="sortBy('type')">
        Type <span>{{ sortKey === 'type' ? (sortAsc ? '↑' : '↓') : '' }}</span>
      </button>
      <button :class="['sort-btn', sortKey === 'percentage' ? 'sort-active' : '']" @click="sortBy('percentage')">
        Avancement <span>{{ sortKey === 'percentage' ? (sortAsc ? '↑' : '↓') : '' }}</span>
      </button>
    </div>

    <!-- Task list -->
    <div class="task-list">
      <template v-for="row in flatRows" :key="row._rowKey">

        <!-- Empty state placeholder -->
        <div
          v-if="row._isEmpty"
          class="task-empty-row"
          :style="{ marginLeft: `${row._depth * 32 + 16}px` }"
        >
          <span class="fr-icon-list-unordered" style="font-size:13px" aria-hidden="true" />
          Aucune sous-tâche
        </div>

        <!-- Task card -->
        <div
          v-else
          class="task-card"
          :class="[`depth-${Math.min(row._depth, 3)}`, `status-${row.status}`]"
          :style="{ marginLeft: `${row._depth * 32}px` }"
        >
          <!-- Connector line for children -->
          <div v-if="row._depth > 0" class="connector-line" />

          <div class="task-card-inner">
            <!-- Left: expand + status dot -->
            <div class="task-card-left">
              <button
                v-if="row.type === 'merge'"
                class="expand-toggle"
                :class="{ 'is-expanded': expandedIds.includes(row.id) }"
                :aria-label="expandedIds.includes(row.id) ? 'Réduire' : 'Développer'"
                @click="toggleExpand(row)"
              >
                <span v-if="loadingChildren.includes(row.id)" class="spinner" />
                <span v-else class="fr-icon-arrow-right-s-line expand-icon" aria-hidden="true" />
              </button>
              <div v-else class="expand-spacer" />
              <div class="status-dot" :class="`dot-${row.status}`" :title="MapStatusToLabel(row.status)" />
            </div>

            <!-- Center: main info -->
            <div class="task-card-body">
              <div class="task-card-top">
                <span class="task-type-badge" :class="`badge-${row.type?.replace(/[^a-z]/g, '-')}`">
                  {{ MapTaskTypeToLabel(row.type) }}
                </span>
                <code class="task-id" :title="row.id">{{ row.id.slice(0, 8) }}…</code>
                <span v-if="row.input?.raw_filename" class="task-filename">
                  <span class="fr-icon-file-line" style="font-size:11px" aria-hidden="true" />
                  {{ row.input.raw_filename }}
                </span>
                <a
                  v-else-if="row.input?.url"
                  :href="row.input.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="task-filename"
                >
                  {{ row.input.url }}
                </a>
              </div>

              <!-- Progress bar -->
              <div class="task-progress-row">
                <div class="task-progress-track">
                  <div
                    class="task-progress-fill"
                    :class="`fill-${row.status}`"
                    :style="{ width: `${(row.percentage ?? 0) * 100}%` }"
                  />
                </div>
                <span class="task-progress-pct">{{ Math.round((row.percentage ?? 0) * 100) }}%</span>
                <span class="task-status-label" :class="`label-${row.status}`">{{ MapStatusToLabel(row.status) }}</span>
                <span v-if="row.position != null" class="task-position-badge" :title="`Position en file d'attente : ${row.position + 1}`">
                  <span class="fr-icon-timer-line" style="font-size:11px" aria-hidden="true" />
                  #{{ row.position + 1 }}
                </span>
              </div>

              <!-- Dates -->
              <div class="task-dates">
                <span>
                  <span class="fr-icon-calendar-line" style="font-size:11px" aria-hidden="true" />
                  {{ formatDate(row.created_at) }}
                </span>
                <span v-if="row.updated_at !== row.created_at" class="task-date-sep">·</span>
                <span v-if="row.updated_at !== row.created_at">
                  <span class="fr-icon-refresh-line" style="font-size:11px" aria-hidden="true" />
                  {{ formatDate(row.updated_at) }}
                </span>
              </div>
            </div>

            <!-- Right: actions -->
            <div class="task-card-actions">
              <button
                class="task-action-btn primary"
                :disabled="row.status !== 'completed'"
                :title="row.status !== 'completed' ? 'Disponible une fois terminé' : 'Voir le résumé'"
                @click="openModal(row)"
              >
                <span class="fr-icon-eye-line" aria-hidden="true" />
              </button>
              <button
                v-if="['queued', 'started', 'in_progress'].includes(row.status)"
                class="task-action-btn warning"
                title="Révoquer"
                @click="revokeTask(row.id)"
              >
                <span class="fr-icon-stop-circle-line" aria-hidden="true" />
              </button>
              <button
                class="task-action-btn danger"
                title="Supprimer"
                @click="removeTask(row.id)"
              >
                <span class="fr-icon-delete-line" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>

      </template>

      <!-- Empty list -->
      <div v-if="flatRows.length === 0" class="tasks-empty">
        <span class="fr-icon-time-line" style="font-size:32px; color:#cbd5e1" aria-hidden="true" />
        <p>Aucune tâche pour le moment</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="tasks-pagination">
      <button class="page-btn" :disabled="paginatedDataSafe.page === 1" @click="loadPage(paginatedDataSafe.page - 1)">
        <span class="fr-icon-arrow-left-s-line" aria-hidden="true" />
      </button>
      <span class="page-info">Page <strong>{{ paginatedDataSafe.page }}</strong> / {{ totalPages }}</span>
      <button class="page-btn" :disabled="paginatedDataSafe.page === totalPages" @click="loadPage(paginatedDataSafe.page + 1)">
        <span class="fr-icon-arrow-right-s-line" aria-hidden="true" />
      </button>
    </div>

    <!-- Modal résumé -->
    <ResumeResultModal
      v-if="selectedTask"
      :results="[{ filename: (selectedTask as any).input?.raw_filename || (selectedTask as any).input?.url || 'Tâche', task: selectedTask }]"
      @close="selectedTask = null"
      @re-generate="selectedTask = null"
    />

    <!-- Stats Modal -->
    <StatModel v-if="statsVisible" @close="statsVisible = false" />
    <LeaderboardModal v-if="leaderboardVisible" @close="leaderboardVisible = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'
import { useAbregeStore } from '@/stores/abrege'
import StatModel from './StatModel.vue'
import ResumeResultModal from './ResumeResultModal.vue'
import LeaderboardModal from './LeaderboardModal.vue'

type TaskModel = {
  id: string
  type: string
  status: string
  percentage?: number | null
  input?: any
  output?: any
  created_at: number
  updated_at: number
  position?: number | null
  [k: string]: any
}

type FlatRow = TaskModel & { _rowKey: string; _isParent: boolean; _isEmpty?: boolean; _depth: number }

const abrege = useAbregeStore()
const { userTasksPaginated: paginatedData } = storeToRefs(abrege)

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

const data_task_mock = { total: 0, page: 1, page_size: 10, items: [] as TaskModel[] }

// ----- TRI -----
const sortKey = ref('')
const sortAsc = ref(true)

function MapTaskTypeToLabel(type: string) {
  const map: Record<string, string> = {
    abrege: 'Résumé',
    merge: 'Fusion',
    classification: 'Classification',
    default: 'Défaut',
  }
  return map[type] ?? type
}

function MapStatusToLabel(status: string) {
  const map: Record<string, string> = {
    queued: 'En attente',
    in_progress: 'En cours',
    started: 'Démarré',
    completed: 'Terminé',
    failed: 'Échoué',
    revoked: 'Révoqué',
    canceled: 'Annulé',
    timeout: 'Timeout',
    created: 'Créé',
  }
  return map[status] || status
}

function sortBy(key: string) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

// ----- TREE (merge expand) -----
const expandedIds = ref<string[]>([])
const loadingChildren = ref<string[]>([])
const childrenCache = ref<Record<string, TaskModel[]>>({})

async function toggleExpand(task: TaskModel) {
  const id = task.id
  if (expandedIds.value.includes(id)) {
    expandedIds.value = expandedIds.value.filter(x => x !== id)
    return
  }
  if (!(id in childrenCache.value)) {
    loadingChildren.value = [...loadingChildren.value, id]
    try {
      const taskIds: string[] = (task.input as any)?.task_ids ?? []
      const children = await Promise.all(
        taskIds.map(async (tid: string) => {
          try {
            const { data } = await http.get(`/task/${tid}`)
            return data as TaskModel
          } catch {
            return null
          }
        }),
      )
      childrenCache.value = { ...childrenCache.value, [id]: children.filter(Boolean) as TaskModel[] }
    } finally {
      loadingChildren.value = loadingChildren.value.filter(x => x !== id)
    }
  }
  expandedIds.value = [...expandedIds.value, id]
}

const paginatedTasks = computed(() => {
  const items = paginatedData.value?.items ?? []
  if (!sortKey.value) return items
  return [...items].sort((a: any, b: any) => {
    const valA = a[sortKey.value]
    const valB = b[sortKey.value]
    if (valA === valB) return 0
    return sortAsc.value ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1)
  })
})

const rootTasks = computed((): TaskModel[] => {
  return (paginatedTasks.value || []) as TaskModel[]
})

function buildRows(tasks: TaskModel[], depth: number, rows: FlatRow[]) {
  for (const task of tasks) {
    const isExpanded = expandedIds.value.includes(task.id)
    rows.push({
      ...task,
      _rowKey: `${task.id}__d${depth}`,
      _isParent: true,
      _depth: depth,
    })
    if (isExpanded) {
      const children = childrenCache.value[task.id] ?? []
      if (children.length === 0) {
        rows.push({ ...task, _rowKey: `${task.id}__empty`, _isParent: false, _isEmpty: true, _depth: depth + 1 })
      } else {
        buildRows(children, depth + 1, rows)
      }
    }
  }
}

const flatRows = computed((): FlatRow[] => {
  const rows: FlatRow[] = []
  buildRows(rootTasks.value, 0, rows)
  return rows
})

const paginatedDataSafe = computed(() => {
  if ((paginatedData.value?.items ?? []).length > 0) return paginatedData.value
  return data_task_mock
})

const loadPage = async (page = 1, overridePageSize?: number) => {
  const pageSize = overridePageSize ?? paginatedData.value?.page_size ?? 10
  await abrege.fetchUserTasks(page, pageSize)
  expandedIds.value = []
  childrenCache.value = {}
  try { await fetchConnectedUsers() } catch { }
}

onMounted(() => {
  void loadPage(1)
  void fetchConnectedUsers()
})

onBeforeUnmount(() => {
  if (typeof abrege.stopPollingUserTasks === 'function') {
    abrege.stopPollingUserTasks()
  }
})

const totalPages = computed(() => {
  const resolved = paginatedDataSafe.value || {}
  const total = resolved.total ?? 0
  const pageSize = resolved.page_size ?? 1
  return Math.max(1, Math.ceil(total / pageSize))
})

// ----- MODAL -----
const selectedTask = ref<TaskModel | null>(null)
const statsVisible = ref(false)
const leaderboardVisible = ref(false)

const openModal = (task: any) => {
  if (!task || task.status !== 'completed') return
  selectedTask.value = task
}

const revokeTask = async (taskId: string) => {
  if (!taskId) return
  try {
    await abrege.revokeTask(taskId)
  }
  catch (e) {
    console.error('Failed to revoke task', e)
  }
  finally {
    const currentPage = paginatedData.value?.page ?? 1
    const pageSize = paginatedData.value?.page_size ?? 10
    await loadPage(currentPage, pageSize)
  }
}

const removeTask = async (taskId: string) => {
  if (!taskId) return
  try {
    await abrege.deleteTask(taskId)
  }
  catch (e) {
    console.error('Failed to remove task', e)
  }
  finally {
    delete childrenCache.value[taskId]
    expandedIds.value = expandedIds.value.filter(x => x !== taskId)
    const currentPage = paginatedData.value?.page ?? 1
    const pageSize = paginatedData.value?.page_size ?? 10
    await loadPage(currentPage, pageSize)
  }
}

const formatDate = (ts: any) => {
  if (ts === null || ts === undefined || ts === '') return ''
  try {
    let n = Number(ts)
    if (Number.isNaN(n)) return String(ts)
    if (n < 1e12) n = n * 1000
    return new Date(n).toLocaleString()
  } catch { return String(ts) }
}
</script>

<style scoped>
/* ── Layout ── */
.tasks-page {
  padding: 24px 32px;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Header ── */
.tasks-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.tasks-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}
.tasks-subtitle {
  font-size: 0.8125rem;
  color: #94a3b8;
  margin: 2px 0 0;
}
.tasks-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.action-btn:hover { background: #f8fafc; border-color: #cbd5e1; }
.users-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 600;
}

/* ── Sort bar ── */
.sort-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sort-label {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
  margin-right: 4px;
}
.sort-btn {
  padding: 4px 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}
.sort-btn:hover { background: #f8fafc; }
.sort-active {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
  font-weight: 600;
}

/* ── Task List ── */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ── Task Card ── */
.task-card {
  position: relative;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.task-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  border-color: #cbd5e1;
}

/* depth tinting */
.depth-1 { background: #fafbff; border-color: #dde5ff; }
.depth-2 { background: #f8f8ff; border-color: #c5ceff; }
.depth-3 { background: #f5f5ff; border-color: #b0b8ff; }

/* status left accent */
.status-completed { border-left: 3px solid #10b981; }
.status-failed    { border-left: 3px solid #ef4444; }
.status-in_progress, .status-started { border-left: 3px solid #3b82f6; }
.status-queued, .status-created { border-left: 3px solid #94a3b8; }

/* connector line */
.connector-line {
  position: absolute;
  left: -20px;
  top: 50%;
  width: 16px;
  height: 1px;
  background: #cbd5e1;
}

.task-card-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
}

/* ── Left ── */
.task-card-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.expand-toggle {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
  flex-shrink: 0;
}
.expand-toggle:hover { background: #f1f5f9; border-color: #cbd5e1; }
.expand-toggle.is-expanded .expand-icon { transform: rotate(90deg); }
.expand-icon { transition: transform 0.2s; font-size: 14px; }
.expand-spacer { width: 26px; height: 26px; flex-shrink: 0; }

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-completed  { background: #10b981; }
.dot-failed     { background: #ef4444; }
.dot-in_progress, .dot-started { background: #3b82f6; animation: pulse 1.5s infinite; }
.dot-queued, .dot-created { background: #94a3b8; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Body ── */
.task-card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.task-card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-type-badge {
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: #eff6ff;
  color: #1d4ed8;
  white-space: nowrap;
}

.task-id {
  font-size: 0.6875rem;
  color: #94a3b8;
  font-family: monospace;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  padding: 1px 6px;
  border-radius: 4px;
}

.task-filename {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.75rem;
  color: #64748b;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.task-progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.task-progress-track {
  flex: 1;
  height: 4px;
  background: #f1f5f9;
  border-radius: 99px;
  overflow: hidden;
}
.task-progress-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;
  background: #94a3b8;
}
.fill-completed  { background: #10b981; }
.fill-failed     { background: #ef4444; }
.fill-in_progress, .fill-started { background: #3b82f6; }
.task-progress-pct {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #64748b;
  width: 30px;
  text-align: right;
  white-space: nowrap;
}
.task-status-label {
  font-size: 0.6875rem;
  font-weight: 500;
  white-space: nowrap;
  color: #64748b;
}
.label-completed  { color: #059669; }
.label-failed     { color: #dc2626; }
.label-in_progress, .label-started { color: #2563eb; }

.task-position-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 0.625rem;
  font-weight: 600;
  color: #d97706;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 9999px;
  padding: 1px 7px;
  white-space: nowrap;
}

.task-dates {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.6875rem;
  color: #94a3b8;
}
.task-date-sep { color: #cbd5e1; }

/* ── Actions ── */
.task-card-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.task-action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  color: #64748b;
  transition: all 0.15s;
}
.task-action-btn:hover:not(:disabled) { background: #f8fafc; border-color: #cbd5e1; }
.task-action-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.task-action-btn.primary:not(:disabled):hover  { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.task-action-btn.warning:not(:disabled):hover  { background: #fffbeb; border-color: #fde68a; color: #d97706; }
.task-action-btn.danger:hover:not(:disabled)   { background: #fff1f2; border-color: #fecada; color: #dc2626; }

/* ── Empty & placeholder ── */
.task-empty-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  color: #94a3b8;
  font-size: 0.75rem;
  font-style: italic;
}
.tasks-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 0;
  color: #94a3b8;
  font-size: 0.875rem;
}

/* ── Pagination ── */
.tasks-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: #f8fafc; border-color: #cbd5e1; }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info {
  font-size: 0.8125rem;
  color: #64748b;
}
</style>
