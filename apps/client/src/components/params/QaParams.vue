<script lang="ts" setup>
import { DsfrToggleSwitch } from '@gouvminint/vue-dsfr'
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const toggleLabel = 'Générer aussi des questions/réponses'
const enabled = computed({
  get: () => paramsValue.extractQa,
  set: (value) => {
    paramsValue.extractQa = value
  },
})

const instructionsLabel = 'Instruction supplémentaire — Questions/réponses'
const instructionsHint = 'Ex : "privilégie des questions chiffrées" ou "formule les réponses en une phrase"'
const instructions = computed({
  get: () => paramsValue.qaInstructions,
  set: (value) => {
    paramsValue.qaInstructions = value
  },
})
</script>

<template>
  <div class="input-bloc">
    <DsfrToggleSwitch
      v-model="enabled"
      :label="toggleLabel"
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
