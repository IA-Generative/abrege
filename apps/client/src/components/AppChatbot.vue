<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { ChatMessage } from '@/composables/use-chatbot'

defineProps<{
  messages: ChatMessage[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
}>()

const isOpen = ref(false)
const input = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const feedback = ref<Map<number, 'up' | 'down'>>(new Map())
const copiedId = ref<number | null>(null)

function setFeedback (msgId: number, vote: 'up' | 'down') {
  const current = feedback.value.get(msgId)
  const next = new Map(feedback.value)
  if (current === vote) {
    next.delete(msgId)
  } else {
    next.set(msgId, vote)
  }
  feedback.value = next
}

function copyMessage (msgId: number, text: string) {
  navigator.clipboard.writeText(text)
  copiedId.value = msgId
  setTimeout(() => { if (copiedId.value === msgId) copiedId.value = null }, 2000)
}

async function submit () {
  const value = input.value.trim()
  if (!value) return
  input.value = ''
  emit('send', value)
  await nextTick()
  messagesEl.value?.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })
}

function onKeydown (e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-40 flex flex-col items-end gap-3">
      <!-- Chat panel -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-4 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-4 scale-95"
      >
        <div
          v-if="isOpen"
          class="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden w-[360px] h-[480px] origin-bottom-right"
        >
          <!-- Header -->
          <div class="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50 shrink-0">
            <span class="fr-icon-chat-3-line text-blue-600" style="font-size:20px;" aria-hidden="true" />
            <span class="text-sm font-semibold text-slate-700 flex-1">Assistant Abrégé</span>
            <button
              class="shrink-0 flex items-center justify-center w-6 h-6 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
              aria-label="Fermer"
              @click="isOpen = false"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3.5 h-3.5"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          <!-- Messages -->
          <div
            ref="messagesEl"
            class="flex-1 overflow-y-auto px-4 py-3 space-y-4"
          >
            <!-- Empty state -->
            <div
              v-if="!messages.length"
              class="h-full flex flex-col items-center justify-center text-center text-slate-400 text-sm gap-2"
            >
              <span class="fr-icon-question-line text-3xl opacity-30" aria-hidden="true" />
              <p>Posez une question.<br>L'assistant est là pour vous aider.</p>
            </div>

            <!-- Message list -->
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="flex gap-2"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                v-if="msg.role === 'bot'"
                class="shrink-0 w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center mt-0.5"
              >
                <span class="fr-icon-chat-3-line text-blue-600" style="font-size:14px;" aria-hidden="true" />
              </div>

              <div
                class="max-w-[80%] rounded-2xl px-3 py-2 text-sm"
                :class="msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-slate-100 text-slate-800 rounded-tl-sm'"
              >
                <div v-if="msg.isLoading" class="py-1">
                  <span class="typing-dots"><span /><span /><span /></span>
                </div>
                <p v-else>
                  {{ msg.content }}
                </p>

                <!-- Action buttons (bot only) -->
                <div
                  v-if="msg.role === 'bot' && !msg.isLoading"
                  class="flex items-center gap-0 mt-1"
                >
                  <button
                    class="w-5 h-5 flex items-center justify-center rounded transition-colors"
                    :class="feedback.get(msg.id) === 'up' ? 'text-emerald-500' : 'text-slate-300 hover:text-slate-500'"
                    title="Bonne réponse"
                    @click="setFeedback(msg.id, 'up')"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>
                  </button>
                  <button
                    class="w-5 h-5 flex items-center justify-center rounded transition-colors"
                    :class="feedback.get(msg.id) === 'down' ? 'text-red-400' : 'text-slate-300 hover:text-slate-500'"
                    title="Mauvaise réponse"
                    @click="setFeedback(msg.id, 'down')"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></svg>
                  </button>
                  <button
                    class="w-5 h-5 flex items-center justify-center rounded transition-colors"
                    :class="copiedId === msg.id ? 'text-emerald-500' : 'text-slate-300 hover:text-slate-500'"
                    :title="copiedId === msg.id ? 'Copié !' : 'Copier'"
                    @click="copyMessage(msg.id, msg.content)"
                  >
                    <svg v-if="copiedId === msg.id" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><path d="M20 6 9 17l-5-5"/></svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Typing indicator -->
            <div
              v-if="isLoading"
              class="flex gap-2 justify-start"
            >
              <div class="shrink-0 w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center mt-0.5">
                <span class="fr-icon-chat-3-line text-blue-600" style="font-size:14px;" aria-hidden="true" />
              </div>
              <div class="bg-slate-100 rounded-2xl rounded-tl-sm px-3 py-2.5">
                <span class="typing-dots"><span /><span /><span /></span>
              </div>
            </div>
          </div>

          <!-- Input -->
          <div class="shrink-0 px-3 py-2.5 border-t border-slate-100 flex gap-2 items-end">
            <textarea
              v-model="input"
              rows="1"
              placeholder="Posez une question…"
              class="flex-1 resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 text-slate-800 placeholder-slate-400 transition-colors"
              :disabled="isLoading"
              @keydown="onKeydown"
            />
            <button
              class="shrink-0 flex items-center justify-center w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
              :disabled="isLoading || !input.trim()"
              aria-label="Envoyer"
              @click="submit"
            >
              <span class="fr-icon-send-plane-fill" style="font-size: 14px;" aria-hidden="true" />
            </button>
          </div>
        </div>
      </Transition>

      <!-- FAB button -->
      <button
        class="relative flex items-center justify-center w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 active:scale-95 text-white shadow-lg transition-all"
        :aria-label="isOpen ? 'Fermer l\'assistant' : 'Ouvrir l\'assistant'"
        @click="isOpen = !isOpen"
      >
        <Transition
          mode="out-in"
          enter-active-class="transition duration-150"
          enter-from-class="opacity-0 rotate-90 scale-50"
          enter-to-class="opacity-100 rotate-0 scale-100"
          leave-active-class="transition duration-150"
          leave-from-class="opacity-100 rotate-0 scale-100"
          leave-to-class="opacity-0 -rotate-90 scale-50"
        >
          <template v-if="isOpen">
            <span class="fr-icon-close-line" style="font-size: 22px;" aria-hidden="true" />
          </template>
          <template v-else>
            <span class="fr-icon-chat-3-line" style="font-size:22px;" aria-hidden="true" />
          </template>
        </Transition>
        <!-- Unread badge -->
        <span
          v-if="!isOpen && messages.length"
          class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center"
        >
          {{ messages.filter(m => m.role === 'bot').length > 9 ? '9+' : messages.filter(m => m.role === 'bot').length }}
        </span>
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #94a3b8;
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
