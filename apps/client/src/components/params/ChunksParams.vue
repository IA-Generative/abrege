<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const instructionsLabel = 'Instruction supplémentaire'
const instructionsHint = 'Ex : "découpe par section plutôt que par paragraphe"'
const instructions = computed({
  get: () => paramsValue.chunksInstructions,
  set: (value) => {
    paramsValue.chunksInstructions = value
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
