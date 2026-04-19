<script setup lang="ts">
import { useApiVersion } from '@/composables/use-api-version'

const { version } = useApiVersion()
</script>

<template>
  <footer class="fr-footer" role="contentinfo">
    <div class="fr-container">
      <div class="fr-footer__body">
        <p class="fr-footer__bottom-copy">
          Version API :
          <span v-if="version">{{ version }}</span>
          <span v-else>—</span>
        </p>
      </div>
    </div>
  </footer>
</template>
