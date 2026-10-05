<script lang="ts" setup>
import { DsfrToggleSwitch } from '@gouvminint/vue-dsfr'
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const toggleLabel = 'Extraire les entités et relations'
const toggleHint = 'Identifie les personnes, organisations, lieux… et les relations entre elles'
const enabled = computed({
  get: () => paramsValue.extractEntities,
  set: (value) => {
    paramsValue.extractEntities = value
  },
})

const instructionsLabel = 'Instruction supplémentaire — Entités et relations'
const instructionsHint = 'Ex : "concentre-toi sur les personnes et organisations, ignore les lieux"'
const instructions = computed({
  get: () => paramsValue.entitiesInstructions,
  set: (value) => {
    paramsValue.entitiesInstructions = value
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
