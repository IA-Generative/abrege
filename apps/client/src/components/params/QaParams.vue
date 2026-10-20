<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const instructionsLabel = 'Instruction supplémentaire'
const instructionsHint = 'Ex : "privilégie des questions chiffrées" ou "formule les réponses en une phrase"'
const instructions = computed({
  get: () => paramsValue.qaInstructions,
  set: (value) => {
    paramsValue.qaInstructions = value
  },
})
</script>

<template>
  <DsfrInput
    v-model="instructions"
    :label-visible="true"
    :is-textarea="true"
    :label="instructionsLabel"
    :hint="instructionsHint"
  />
</template>
