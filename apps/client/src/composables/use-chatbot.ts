import { ref } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

const http = createHttpClient(ABREGE_API_URL)

export interface ChatSource {
  storage_path: string
  text: string
  task_id?: string
  filename?: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'bot'
  content: string
  isLoading?: boolean
  sources?: ChatSource[]
}

export interface ChatTask {
  id: string
  title: string
  status: string
  created_at: string
  chunked?: boolean | null // null = loading, true = ready, false = not chunked
  submitting?: boolean
}

function storageKey () {
  return 'abrege-chat'
}

function loadMessages (): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(storageKey())
    if (!raw) return []
    return JSON.parse(raw) as ChatMessage[]
  }
  catch {
    return []
  }
}

function saveMessages (msgs: ChatMessage[]) {
  try {
    const toStore = msgs.map(m => ({ ...m, isLoading: undefined }))
    sessionStorage.setItem(storageKey(), JSON.stringify(toStore))
  }
  catch { /* quota exceeded — silently ignore */ }
}

export function useChatbot () {
  const persisted = loadMessages()
  const messages = ref<ChatMessage[]>(persisted)
  const isLoading = ref(false)
  const selectedTaskIds = ref<string[]>([])
  const availableTasks = ref<ChatTask[]>([])
  const tasksLoading = ref(false)
  const tasksTotal = ref(0)
  const tasksPage = ref(1)
  const tasksPageSize = 10
  let nextId = persisted.length ? Math.max(...persisted.map(m => m.id)) + 1 : 1

  async function fetchAvailableTasks (page = 1) {
    tasksLoading.value = true
    try {
      const { data } = await http.get('/task/user/', { params: { offset: page, limit: tasksPageSize } })
      availableTasks.value = (data.items ?? [])
        .filter((t: any) => t.status === 'completed')
        .map((t: any) => ({
          id: t.id,
          title: t.input?.raw_filename ?? t.input?.url ?? t.id,
          status: t.status,
          created_at: t.created_at,
          chunked: null as boolean | null,
          submitting: false,
        }))
      tasksTotal.value = data.total ?? 0
      tasksPage.value = page
      // Check chunk status for each task in background
      for (const task of availableTasks.value) {
        checkChunkedStatus(task.id)
      }
    }
    catch { /* swallow */ }
    finally {
      tasksLoading.value = false
    }
  }

  async function checkChunkedStatus (taskId: string) {
    try {
      const { data } = await http.get(`/v1/chunks/is-chunked/${taskId}`)
      const task = availableTasks.value.find(t => t.id === taskId)
      if (task) task.chunked = !!data
    }
    catch {
      const task = availableTasks.value.find(t => t.id === taskId)
      if (task) task.chunked = false
    }
  }

  async function submitChunks (taskId: string) {
    const task = availableTasks.value.find(t => t.id === taskId)
    if (!task) return
    task.submitting = true
    try {
      await http.post(`/v1/chunks/task/${taskId}/submit-chunks`)
      task.chunked = null
      // Poll until chunked
      const poll = setInterval(async () => {
        try {
          const { data } = await http.get(`/v1/chunks/is-chunked/${taskId}`)
          if (data) {
            task.chunked = true
            task.submitting = false
            clearInterval(poll)
          }
        }
        catch { /* keep polling */ }
      }, 3000)
      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(poll)
        if (task.submitting) {
          task.submitting = false
          task.chunked = false
        }
      }, 120_000)
    }
    catch {
      task.submitting = false
      task.chunked = false
    }
  }

  async function sendMessage (content: string) {
    if (!content.trim() || isLoading.value) return

    const userMsg: ChatMessage = { id: nextId++, role: 'user', content }
    messages.value = [...messages.value, userMsg]
    isLoading.value = true

    try {
      // Build conversation history for the API (map 'bot' → 'assistant')
      const apiMessages = messages.value.map(m => ({
        role: m.role === 'bot' ? 'assistant' as const : 'user' as const,
        content: m.content,
      }))

      // Get embedding for the user's query
      const { data: embedData } = await http.post('/chat/embed', { text: content })
      const queryVector: number[] = embedData.vector

      // Call chat/ask
      const { data } = await http.post('/chat/ask', {
        messages: apiMessages,
        query_vector: queryVector,
        filter_by_task: selectedTaskIds.value,
        top_k: 5,
      })

      const sources: ChatSource[] = (data.sources ?? []).map((s: any) => ({
        storage_path: s.storage_path,
        text: s.text,
        task_id: s.task_id,
        filename: s.filename,
      }))

      const botMsg: ChatMessage = {
        id: nextId++,
        role: 'bot',
        content: data.message?.content ?? 'Pas de réponse.',
        sources,
      }
      messages.value = [...messages.value, botMsg]
    }
    catch (err: any) {
      const botMsg: ChatMessage = {
        id: nextId++,
        role: 'bot',
        content: `Erreur : ${err?.response?.data?.detail ?? err?.message ?? 'Impossible de contacter le serveur.'}`,
      }
      messages.value = [...messages.value, botMsg]
    }
    finally {
      isLoading.value = false
      saveMessages(messages.value)
    }
  }

  function clearMessages () {
    messages.value = []
    sessionStorage.removeItem(storageKey())
  }

  return { messages, isLoading, sendMessage, clearMessages, selectedTaskIds, availableTasks, tasksLoading, tasksTotal, tasksPage, tasksPageSize, fetchAvailableTasks, submitChunks }
}
