<script setup lang="ts">
import useToaster from './composables/use-toaster'

const toaster = useToaster()

const serviceTitle = 'Résumer un texte'
const serviceDescription = 'Produire une synthèse de documents volumineux'
const logoText = ['Ministère', 'de l’intérieur']
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

  <AppToaster
    :messages="toaster.messages"
    @close-message="toaster.removeMessage($event)"
  />
</template>
