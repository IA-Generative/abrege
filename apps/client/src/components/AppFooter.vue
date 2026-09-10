<script setup lang="ts">
import { onMounted } from 'vue'
import useAppVersion from '@/composables/use-app-version'

const { frontendVersion, backendVersion, fetchBackendVersion } = useAppVersion()

onMounted(fetchBackendVersion)
</script>

<template>
  <DsfrFooter
    :licence-text="`Frontend v${frontendVersion} - Backend v${backendVersion ?? '…'}`"
  />
</template>
