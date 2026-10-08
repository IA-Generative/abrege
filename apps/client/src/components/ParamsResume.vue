<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import ExtractionPicker from './params/ExtractionPicker.vue'
import SummaryParams from './params/SummaryParams.vue'

const { paramsValue } = useAbregeStore()

const DEFAULT_SIZE = 4000

// Shown in the collapsed header so the current choices are visible without opening it.
const accordionTitle = computed(() => {
  const language = paramsValue.selectOptionSelected === 'English' ? 'Anglais' : 'Français'
  const size = Number(paramsValue.inputValue) || DEFAULT_SIZE
  return `Options du résumé — ${language}, ${size} mots`
})
</script>

<template>
  <div>
    <DsfrAccordion
      id="accordion-summary-options"
      class="summary-options"
      :title="accordionTitle"
    >
      <SummaryParams />
    </DsfrAccordion>
    <ExtractionPicker />
  </div>
</template>

<style scoped>
  .summary-options {
    margin-top: 1.5rem;
  }
  :deep(textarea){
    min-height: 114px;
  }
  @media (min-width: 768px) {
    textarea {
      min-height: 144px;
    }
  }
</style>
