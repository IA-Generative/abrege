<script setup lang="ts">
import { useRegisterSW } from 'virtual:pwa-register/vue'

import useToaster from './composables/use-toaster'

const toaster = useToaster()

const serviceTitle = 'Résumer un texte'
const serviceDescription = 'Produire une synthèse de documents volumineux'
const logoText = ['Ministère', 'de l’intérieur']

const {
  offlineReady,
  needRefresh,
  updateServiceWorker,
} = useRegisterSW()

function close () {
  offlineReady.value = false
  needRefresh.value = false
}
</script>

<template>
  <DsfrHeader
    :service-title="serviceTitle"
    :service-description="serviceDescription"
    :logo-text="logoText"
  />

  <div class="fr-container  fr-mt-3w  fr-mt-md-5w  fr-mb-5w">
    <router-view />
  </div>

  <ReloadPrompt
    :offline-ready="offlineReady"
    :need-refresh="needRefresh"
    @close="close()"
    @update-service-worker="updateServiceWorker()"
  />

  <AppToaster
    :messages="toaster.messages"
    @close-message="toaster.removeMessage($event)"
  />
</template>
