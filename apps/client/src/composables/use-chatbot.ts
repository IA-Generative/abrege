import { ref } from 'vue'

export interface ChatMessage {
  id: number
  role: 'user' | 'bot'
  content: string
  isLoading?: boolean
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
  let nextId = persisted.length ? Math.max(...persisted.map(m => m.id)) + 1 : 1

  async function sendMessage (content: string) {
    if (!content.trim() || isLoading.value) return

    const userMsg: ChatMessage = { id: nextId++, role: 'user', content }
    messages.value = [...messages.value, userMsg]
    isLoading.value = true

    try {
      // TODO: appeler le backend quand il sera prêt
      // Pour l'instant, réponse placeholder
      const botMsg: ChatMessage = {
        id: nextId++,
        role: 'bot',
        content: 'Le backend du chatbot n\'est pas encore connecté. Cette fonctionnalité sera disponible prochainement.',
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

  return { messages, isLoading, sendMessage, clearMessages }
}
