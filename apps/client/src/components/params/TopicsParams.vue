<script lang="ts" setup>
import { DsfrToggleSwitch } from '@gouvminint/vue-dsfr'
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const toggleLabel = 'Classifier les sujets abordés'
const toggleHint = 'Détecte les grands thèmes du résumé, avec un score de confiance'
const enabled = computed({
  get: () => paramsValue.classifyTopics,
  set: (value) => {
    paramsValue.classifyTopics = value
  },
})

const instructionsLabel = 'Instruction supplémentaire — Classification'
const instructionsHint = 'Ex : "utilise des catégories métier RH (recrutement, paie, formation…)"'
const instructions = computed({
  get: () => paramsValue.topicsInstructions,
  set: (value) => {
    paramsValue.topicsInstructions = value
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
