<template>
  <div class="task-container fr-container">
    <h2 class="fr-h2">Liste des tâches</h2>

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
          <td>{{ task.type }}</td>

          <td>
            <ProgressBar :visible="true" :progress="task.percentage ?? 0" :text="MapStatusToLabel(task.status)" />
            <div class="fr-ml-1">{{ task.percentage ?? 0 }}%</div>
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
    <div v-if="selectedTask" class="modal-overlay">
      <div class="modal fr-card">

        <div class="summary-block">
          <ResumeResult :resumeResult="selectedTask" />
        </div>

        <div class="fr-pt-2">
          <DsfrButton size="sm" priority="secondary" @click="selectedTask = null">Fermer</DsfrButton>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ResumeResult from '@/components/ResumeResult.vue'
import { onMounted, onBeforeUnmount } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const abrege = useAbregeStore()
const paginatedData = abrege.userTasksPaginated

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
const selectedTask = ref(null)

const openModal = (task) => {
  if (!task || task.status !== 'completed') {
    return
  }
  selectedTask.value = task
}

const formatDate = (ts) => {
  if (!ts) return ''
  try {
    return new Date(Number(ts)).toLocaleString()
  }
  catch (e) {
    return String(ts)
  }
}

// Summary rendering handled by `ResumeResult` component



</script>

<style scoped>
.task-container {
  padding: 20px;
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

.summary-block {
  margin-top: 1rem;
}

.summary-block > div {
  max-height: 50vh;
  overflow: auto;
  padding-right: 0.5rem;
}
</style>