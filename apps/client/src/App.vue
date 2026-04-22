<script setup lang="ts">
import useToaster from './composables/use-toaster'
import { useChatbot } from './composables/use-chatbot'
import AppChatbot from './components/AppChatbot.vue'

const toaster = useToaster()
const { messages: chatMessages, isLoading: chatLoading, sendMessage } = useChatbot()
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
    @send="sendMessage"
  />
  <AppFooter />
</template>
