<script lang="ts" setup>
import { TCHAP_CANAL_URL } from '@/utils/constants'
</script>

<template>
  <div class="fr-alert fr-alert--info fr-mb-4w">
    <p>
      L'IA peut halluciner. <span style="font-weight:bold">Veuillez toujours confirmer les informations traitées et consulter impérativement
        les conditions d'utilisation ainsi que les responsabilités de l'agent et du service utilisateur.</span>
      <br>
      <br>
      Nous travaillons pour améliorer la performance et le type de documents acceptes, veuillez nous notifier
      via le <a
        :href="TCHAP_CANAL_URL"
        target="_blank"
      >canal Tchap</a> de tout dysfonctionnement.
    </p>
  </div>
</template>
