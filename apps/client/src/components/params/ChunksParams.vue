<script lang="ts" setup>
import { DsfrToggleSwitch } from '@gouvminint/vue-dsfr'
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const toggleLabel = 'Conserver les chunks sémantiques'
const toggleHint = 'Persiste les sous-découpages sémantiques utilisés pendant le résumé'
const enabled = computed({
  get: () => paramsValue.extractChunks,
  set: (value) => {
    paramsValue.extractChunks = value
  },
})

const instructionsLabel = 'Instruction supplémentaire — Découpage'
const instructionsHint = 'Ex : "découpe par section plutôt que par paragraphe"'
const instructions = computed({
  get: () => paramsValue.chunksInstructions,
  set: (value) => {
    paramsValue.chunksInstructions = value
  },
})
</script>

<template>
  <div class="input-bloc">
    <DsfrToggleSwitch
      v-model="enabled"
      :label="toggleLabel"
      :hint="toggleHint"
    />
    <div
      v-if="enabled"
      class="instruction-bloc"
    >
      <DsfrInput
        v-model="instructions"
        :label-visible="true"
        :is-textarea="true"
        :label="instructionsLabel"
        :hint="instructionsHint"
      />
    </div>
  </div>
</template>

<style scoped>
  .input-bloc {
    margin-top: 2rem;
  }
  .instruction-bloc {
    margin-top: 1rem;
    padding: 0.75rem 1rem 1rem;
    background: var(--background-alt-blue-france);
    border-left: 3px solid var(--border-plain-blue-france);
  }
</style>
