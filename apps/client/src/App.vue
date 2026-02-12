<script setup lang="ts">
import useToaster from './composables/use-toaster'

const toaster = useToaster()
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
</template>
