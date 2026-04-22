<script setup lang="ts">
import { computed } from 'vue'
import type { ChatTask } from '@/composables/use-chatbot'

const props = defineProps<{
  visible: boolean
  selectedTaskIds: string[]
  availableTasks: ChatTask[]
  tasksLoading: boolean
  tasksTotal: number
  tasksPage: number
  tasksPageSize: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:selectedTaskIds': [ids: string[]]
  fetchTasks: [page: number]
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.tasksTotal / props.tasksPageSize)))

function close () {
  emit('update:visible', false)
}

function goToPage (page: number) {
  if (page < 1 || page > totalPages.value) return
  emit('fetchTasks', page)
}

function toggleTask (taskId: string) {
  const current = props.selectedTaskIds
  const next = current.includes(taskId)
    ? current.filter(id => id !== taskId)
    : [...current, taskId]
  emit('update:selectedTaskIds', next)
}

function clearFilter () {
  emit('update:selectedTaskIds', [])
}

function formatDate (iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="close"
      >
        <div class="modal-card rounded-2xl shadow-2xl w-[440px] max-h-[520px] flex flex-col overflow-hidden border border-white/20">
          <!-- Header -->
          <div class="flex items-center gap-3 px-5 py-4 border-b border-white/10">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5 text-blue-400 shrink-0"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-slate-100">Filtrer par document</h3>
              <p class="text-[11px] text-slate-400">Sélectionnez les documents pour cibler les réponses</p>
            </div>
            <button
              class="shrink-0 w-7 h-7 rounded-full hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors"
              @click="close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          <!-- Selection summary -->
          <div
            v-if="selectedTaskIds.length"
            class="flex items-center justify-between px-5 py-2 bg-blue-500/10 border-b border-blue-400/20"
          >
            <span class="text-xs text-blue-300 font-medium">{{ selectedTaskIds.length }} document(s) sélectionné(s)</span>
            <button class="text-[11px] text-blue-400 hover:text-blue-300 font-medium" @click="clearFilter">Tout désélectionner</button>
          </div>

          <!-- Task list -->
          <div class="flex-1 overflow-y-auto px-3 py-2 min-h-[200px]">
            <div v-if="tasksLoading" class="flex items-center justify-center py-10">
              <span class="typing-dots"><span /><span /><span /></span>
            </div>
            <div v-else-if="!availableTasks.length" class="flex flex-col items-center justify-center py-10 text-slate-500 text-sm gap-2">
              <span class="fr-icon-file-line text-2xl opacity-30" aria-hidden="true" />
              <p>Aucun document terminé disponible.</p>
            </div>
            <div v-else class="space-y-1">
              <label
                v-for="task in availableTasks"
                :key="task.id"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-colors group"
                :class="selectedTaskIds.includes(task.id)
                  ? 'bg-blue-500/15 ring-1 ring-blue-400/30'
                  : 'hover:bg-white/5'"
              >
                <input
                  type="checkbox"
                  :checked="selectedTaskIds.includes(task.id)"
                  class="rounded border-slate-500 text-blue-500 focus:ring-blue-500 w-4 h-4 shrink-0 bg-transparent"
                  @change="toggleTask(task.id)"
                >
                <div class="flex-1 min-w-0">
                  <p
                    class="text-sm font-medium truncate"
                    :class="selectedTaskIds.includes(task.id) ? 'text-blue-300' : 'text-slate-200'"
                  >{{ task.title }}</p>
                  <p class="text-[11px] text-slate-500 mt-0.5">{{ formatDate(task.created_at) }}</p>
                </div>
                <span class="fr-icon-file-text-line text-slate-600 group-hover:text-slate-400 shrink-0" style="font-size:16px;" aria-hidden="true" />
              </label>
            </div>
          </div>

          <!-- Pagination -->
          <div
            v-if="totalPages > 1"
            class="flex items-center justify-center gap-2 px-5 py-3 border-t border-white/10"
          >
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-colors"
              :class="tasksPage <= 1 ? 'text-slate-600 cursor-not-allowed' : 'text-slate-400 hover:bg-white/10'"
              :disabled="tasksPage <= 1"
              @click="goToPage(tasksPage - 1)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <template v-for="p in totalPages" :key="p">
              <button
                v-if="p === 1 || p === totalPages || (p >= tasksPage - 1 && p <= tasksPage + 1)"
                class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
                :class="p === tasksPage
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:bg-white/10'"
                @click="goToPage(p)"
              >{{ p }}</button>
              <span
                v-else-if="p === 2 || p === totalPages - 1"
                class="text-slate-600 text-xs"
              >…</span>
            </template>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-colors"
              :class="tasksPage >= totalPages ? 'text-slate-600 cursor-not-allowed' : 'text-slate-400 hover:bg-white/10'"
              :disabled="tasksPage >= totalPages"
              @click="goToPage(tasksPage + 1)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>

          <!-- Footer -->
          <div class="flex justify-end px-5 py-3 border-t border-white/10">
            <button
              class="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              @click="close"
            >Appliquer</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-card {
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
}

.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #64748b;
  animation: typing-bounce 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: 0s; }
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
