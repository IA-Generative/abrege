<script lang="ts" setup>
import { ref } from 'vue'
import AdvancedParams from './params/AdvancedParams.vue'
import SummaryParams from './params/SummaryParams.vue'

const expandedId = ref<string>()
const activeAccordion = ref<number>(1)
const accordionTitle = 'Plus de paramètres'
</script>

<template>
  <DsfrAccordionsGroup v-model="activeAccordion">
    <DsfrAccordion
      id="accordion-1"
      :title="accordionTitle"
      :expanded="activeAccordion === 0"
      :expanded-id="expandedId"
      @expand="expandedId = $event"
    >
      <div>
        <SummaryParams />
        <AdvancedParams />
      </div>
    </DsfrAccordion>
  </DsfrAccordionsGroup>
</template>

<style scoped>
  :deep(textarea){
    min-height: 114px;
  }
  @media (min-width: 768px) {
    textarea {
      min-height: 144px;
    }
  }
</style>
