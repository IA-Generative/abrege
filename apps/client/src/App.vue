<script setup lang="ts">
import { ref } from 'vue'
import useToaster from './composables/use-toaster'
import { useChatbot } from './composables/use-chatbot'
import AppChatbot from './components/AppChatbot.vue'
import ResumeResultModal from './components/ResumeResultModal.vue'
import createHttpClient from './api/http-client'
import { ABREGE_API_URL } from './utils/constants'

const http = createHttpClient(ABREGE_API_URL)
const toaster = useToaster()
const { messages: chatMessages, isLoading: chatLoading, sendMessage, selectedTaskIds, availableTasks, tasksLoading, tasksTotal, tasksPage, tasksPageSize, fetchAvailableTasks } = useChatbot()

const sourceTask = ref<any>(null)

async function openSourceTask (taskId: string) {
  try {
    const { data } = await http.get(`/task/${taskId}`)
    if (data && data.status === 'completed') {
      sourceTask.value = data
    }
  }
  catch { /* swallow */ }
}
</script>

<template>
  <AppHeader />
  <div class="fr-container  fr-mt-3w  fr-mt-md-5w  fr-mb-5w">
    <router-view />
  </div>

  <AppToaster
    :messages="toaster.messages"
    @close-message="toaster.removeMessage($event)"
  />
  <AppChatbot
    :messages="chatMessages"
    :is-loading="chatLoading"
    :selected-task-ids="selectedTaskIds"
    :available-tasks="availableTasks"
    :tasks-loading="tasksLoading"
    :tasks-total="tasksTotal"
    :tasks-page="tasksPage"
    :tasks-page-size="tasksPageSize"
    @send="sendMessage"
    @update:selected-task-ids="selectedTaskIds = $event"
    @fetch-tasks="fetchAvailableTasks"
    @open-source="openSourceTask"
  />
  <ResumeResultModal
    v-if="sourceTask"
    :results="[{ filename: sourceTask.input?.raw_filename || sourceTask.input?.url || 'Document', task: sourceTask }]"
    @close="sourceTask = null"
    @re-generate="sourceTask = null"
  />
  <AppFooter />
</template>
