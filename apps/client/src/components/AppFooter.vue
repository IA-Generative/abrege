<script setup lang="ts">
import { onMounted } from 'vue'
import useAppVersion from '@/composables/use-app-version'
import { ABREGE_API_URL } from '@/utils/constants'

const { frontendVersion, backendVersion, fetchBackendVersion } = useAppVersion()

onMounted(fetchBackendVersion)

const ecosystemLinks = [
  {
    label: 'Swagger API',
    href: `${ABREGE_API_URL}/docs`,
    title: 'Documentation interactive de l\'API (Swagger)',
  },
  {
    label: 'Dépôt du projet',
    href: 'https://github.com/IA-Generative/abrege',
    title: 'Code source sur GitHub',
  },
]
</script>

<template>
  <DsfrFooter
    :ecosystem-links="ecosystemLinks"
    :licence-text="`Frontend v${frontendVersion} - Backend v${backendVersion ?? '…'}`"
  />
</template>
