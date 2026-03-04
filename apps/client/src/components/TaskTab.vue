<template>
  <div class="task-container fr-container">
    <h2 class="fr-h2">Liste des tâches</h2>
    <DsfrButton size="sm" priority="secondary" class="fr-ml-1" @click="statsVisible = true">Voir les statistiques</DsfrButton>

    <table class="fr-table task-table">
      <thead>
        <tr>
          <th @click="sortBy('type')">Type ⬍</th>
          <th @click="sortBy('percentage')">Pourcentage ⬍</th>
          <th @click="sortBy('created_at')">Créé le ⬍</th>
          <th @click="sortBy('updated_at')">Mis à jour le ⬍</th>
          <th>Voir résumé</th>
          <th>Supprimer</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="task in paginatedTasks" :key="task.id">
          <td>
            <a
              v-if="task.input?.url"
              :href="task.input.url"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ task.input.url }}
            </a>
            <span v-else-if="task.output?.summary">
              {{ task.output.summary.length > 30 ? task.output.summary.slice(0, 30) + '...' : task.output.summary }}
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
            <DsfrButton size="sm" priority="secondary" :disabled="task.status !== 'completed'" @click="openModal(task)">
              Voir résumé
            </DsfrButton>
          </td>

          <td>
            <DsfrButton
              size="sm"
              priority="tertiary"
              :disabled="task.status !== 'completed' && (task.percentage ?? 0) < 100"
              @click="removeTask(task.id)"
            >
              Supprimer
            </DsfrButton>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div class="pagination fr-mt-2">
      <DsfrButton size="sm" priority="tertiary" :disabled="paginatedData.page === 1" @click="loadPage(paginatedData.page - 1)">
        Précédent
      </DsfrButton>

      <span class="fr-ml-2 fr-mr-2">Page {{ paginatedData.page }} / {{ totalPages }}</span>

      <DsfrButton size="sm" priority="tertiary" :disabled="paginatedData.page === totalPages" @click="loadPage(paginatedData.page + 1)">
        Suivant
      </DsfrButton>
    </div>

    <!-- Modal -->
    <div v-if="selectedTask" class="modal-overlay" @click.self="selectedTask = null">
      <div class="modal fr-card" @click.stop>
        <header class="modal-header fr-card">
          <h3 class="fr-h3">Résumer</h3>  
        </header>


        <section class="modal-section fr-card">
          <div class="section-title">Source</div>
          <div class="section-content">
            <div v-if="selectedTask.input?.url">
              <a :href="selectedTask.input.url" target="_blank" rel="noopener noreferrer">{{ selectedTask.input.url }}</a>
            </div>
            <div v-else-if="selectedTask.input?.raw_filename">{{ selectedTask.input.raw_filename }}</div>
            <div v-else>—</div>
          </div>
        </section>

        <section class="modal-section fr-card">
          <div class="section-title">Contenu</div>
          <div class="section-content">
            <div v-if="selectedTask.output?.summary">
              <textarea readonly class="summary-text" :value="selectedTask.output.summary"></textarea>
            </div>
            <div v-else-if="selectedTask.input?.url">
              <div>URL fournie. Cliquez sur le lien ci‑dessous pour ouvrir.</div>
              <a :href="selectedTask.input.url" target="_blank" rel="noopener noreferrer">{{ selectedTask.input.url }}</a>
            </div>
            <div v-else>
              <div>Contenu indisponible</div>
            </div>
          </div>
        </section>

        <section class="modal-section modal-actions">
          <div class="section-content">
            <DsfrButton v-if="selectedTask.input?.url" size="sm" priority="tertiary" @click="copyToClipboard(selectedTask.input.url)">Copier l'URL</DsfrButton>
            <DsfrButton v-else-if="selectedTask.output?.summary" size="sm" priority="tertiary" @click="copyToClipboard(selectedTask.output.summary)">Copier le résumé</DsfrButton>
            <DsfrButton v-else-if="selectedTask.input?.raw_filename" size="sm" priority="tertiary" @click="copyToClipboard(selectedTask.input.raw_filename)">Copier le nom</DsfrButton>
            <span v-if="copySuccess" class="copy-success">Copié&nbsp;!</span>
          </div>
        </section>



        
      </div>
    </div>
    
    <!-- Stats Modal -->
    <StatModel v-if="statsVisible" @close="statsVisible = false" />

      <!-- Connected users badge -->
      <div class="connected-badge" title="Utilisateurs connectés aujourd'hui">
        <span class="badge-emoji">👥</span>
        <span class="badge-number">{{ connectedUsers ?? '—' }}</span>
      </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onMounted, onBeforeUnmount } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'
import { useAbregeStore } from '@/stores/abrege'
import StatModel from './StatModel.vue'

const abrege = useAbregeStore()
const paginatedData = abrege.userTasksPaginated

// connected users today badge
const connectedUsers = ref<number | null>(null)
const http = createHttpClient(ABREGE_API_URL)

const fetchConnectedUsers = async () => {
  try {
    const { data } = await http.get('/task/unique_users')
    // API returns { users_today: <number> }
    connectedUsers.value = data?.users_today ?? null
  }
  catch (e) {
    // keep null on error
    connectedUsers.value = null
  }
}

// Example full dataset (would come from API). We'll expose paginatedData matching the API schema:


// Initialize first page
// Initialize first page (defined after sortedTasks to avoid TDZ)

// ----- TRI -----
const sortKey = ref('')
const sortAsc = ref(true)

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

// sort and expose paginated tasks (client-side sorting of current page)
// `paginatedData` can be a ref (has `.value`) or a reactive proxy; resolve both cases.
const paginatedTasks = computed(() => {
  const resolved = paginatedData && Object.prototype.hasOwnProperty.call(paginatedData, 'value')
    ? paginatedData.value
    : paginatedData

  const items = resolved?.items ?? []
  if (!sortKey.value) return items
  return [...items].sort((a, b) => {
    const key = sortKey.value
    const valA = a[key]
    const valB = b[key]
    if (valA === valB) return 0
    return sortAsc.value ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1)
  })
})

// define loadPage to start polling via store
const loadPage = async (page = 1) => {
  const pageSize = paginatedData?.page_size ?? 10
  // start polling via store (store updates paginatedData automatically)
  abrege.startPollingUserTasks(page, pageSize)
  
}

onMounted(() => {
  loadPage(1)
  fetchConnectedUsers()
})

onBeforeUnmount(() => {
  if (typeof abrege.stopPollingUserTasks === 'function') {
    abrege.stopPollingUserTasks()
  }
})

// ----- PAGINATION -----
const totalPages = computed(() => {
  const total = paginatedData.value?.total ?? 0
  const pageSize = paginatedData.value?.page_size ?? 1
  return Math.max(1, Math.ceil(total / pageSize))
})


// ----- MODAL -----
// `selectedTask` starts as `null` so the modal is hidden by default.
const selectedTask = ref(null)

// stats modal visibility
const statsVisible = ref(false)

/* Example structure for reference: */
// const selectedTask = {
//   id: 'task123',
//   type: 'summarization',
//   status: 'completed',
//   percentage: 1,
//   created_at: '2024-01-01T12:00:00Z',
//   updated_at: '2024-01-01T12:05:00Z',
//   input: {
//     text: 'Some input text...',
//     raw_filename: 'document.pdf'
//   },
//   output: {
//     summary: 'This is a summary of the article...'
//   }
// }


const openModal = (task) => {
  if (!task || task.status !== 'completed') {
    return
  }
  selectedTask.value = task
}

// remove a task via the store API and refresh the current page
const removeTask = async (taskId) => {
  if (!taskId) return
  try {
    // call store action to delete
    await abrege.deleteTask(taskId)
    // reload current page
    const currentPage = paginatedData && paginatedData.value ? paginatedData.value.page ?? 1 : (paginatedData.page ?? 1)
    const pageSize = paginatedData && paginatedData.value ? paginatedData.value.page_size ?? 10 : (paginatedData.page_size ?? 10)
    await loadPage(currentPage, pageSize)
  }
  catch (e) {
    console.error('Failed to remove task', e)
  }
}

const formatDate = (ts) => {
  if (ts === null || ts === undefined || ts === '') return ''
  try {
    let n = Number(ts)
    if (Number.isNaN(n)) return String(ts)
    // If timestamp looks like seconds (<= 1e12), convert to milliseconds
    if (n < 1e12) n = n * 1000
    return new Date(n).toLocaleString()
  } catch (e) {
    return String(ts)
  }
}

// // copy helper for modal with visual feedback
// import { watch } from 'vue'
const copySuccess = ref(false)
let _copyTimeout = null

const copyToClipboard = async (text) => {
  try {
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      // fallback: create textarea and execCopy
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.focus()
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }

    // show feedback
    copySuccess.value = true
    if (_copyTimeout) clearTimeout(_copyTimeout)
    _copyTimeout = setTimeout(() => (copySuccess.value = false), 2000)
  } catch (e) {
    console.error('Copy failed', e)
  }
}

// close modal on Escape
const _escHandler = (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    selectedTask.value = null
  }
}

onMounted(() => {
  window.addEventListener('keydown', _escHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', _escHandler)
  if (_copyTimeout) clearTimeout(_copyTimeout)
})

// Summary rendering handled by `ResumeResult` component



</script>

<style scoped>
.task-container {
  padding: 20px;
  position: relative;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
}

.task-table th,
.task-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
  cursor: pointer;
}


.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: center;
  gap: 15px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);

  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 1.25rem;
  border-radius: 12px;
  width: min(900px, 95%);
  max-width: 900px;
  max-height: 80vh;
  overflow: auto;
  box-sizing: border-box;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  z-index: 10000;
}

/* Ensure modal inner content has comfortable horizontal padding */
.modal .modal-header,
.modal .modal-section,
.modal .modal-footer {
  padding-left: 1rem;
  padding-right: 1rem;
}

/* Make textarea respect modal padding */
.summary-text {
  width: 100%;
  min-height: 6rem;
  resize: vertical;
  box-sizing: border-box;
  padding: 0.5rem;
}

.summary-block {
  margin-top: 1rem;
}

.summary-block > div {
  max-height: 50vh;
  overflow: auto;
  padding-right: 0.5rem;
}

/* Modal sections */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
.modal-close {
  background: transparent;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
}
.modal-section {
  border-top: 1px solid #eee;
  padding: 0.75rem 0;
}
.section-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.section-content {
  display: block;
}
.summary-text {
  width: 100%;
  min-height: 6rem;
  resize: vertical;
}
.modal-actions .section-content > * {
  margin-right: 0.5rem;
}
.modal-meta .meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem 1rem;
}
.modal-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

.copy-success {
  color: #0b6623;
  margin-left: 0.75rem;
  font-weight: 600;
}

/* connected badge */
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
  box-shadow: 0 6px 18px rgba(11,107,255,0.15);
  font-weight: 600;
}
.connected-badge .badge-emoji { font-size: 14px }
.connected-badge .badge-number { min-width: 32px; text-align: center }
</style>