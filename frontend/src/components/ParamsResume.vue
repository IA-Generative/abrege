<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const expandedId = ref<string>()
const activeAccordion = ref<number>(1)
const accordionTitle = 'Plus de paramètres'

const abregeStore = useAbregeStore()
const { paramsValue } = abregeStore

const customPromptLabel = 'Rajoutez une instruction supplémentaire'
const customPromptHint = 'Ex : “utilise un ton très formel” ou “liste les points importants”'
const customPromptValue = computed({
  get: () => paramsValue.customPrompt,
  set: (value) => {
    paramsValue.customPrompt = value
  },
})

const inputLabel = 'Choississez un nombre de mots pour votre résumé'
const inputHint = 'Le résumé contiendra un nombre de mots approximatif en fonction de la valeur indiquée'
const inputPlaceholder = '4000 (par défaut)'
const inputValue = computed({
  get: () => paramsValue.inputValue,
  set: (value) => {
    paramsValue.inputValue = value
  },
})

const selectLabel = 'Choisissez en quelle langue sera généré votre résumé'
const selectOptions = [{ value: 'French', text: 'Français (par défaut)' }, { value: 'English', text: 'Anglais' }]
const selectOptionSelected = computed({
  get: () => paramsValue.selectOptionSelected,
  set: (value) => {
    paramsValue.selectOptionSelected = value
    paramsValue.selectOptionText = selectOptions.find(option => option.value === value)?.text || ''
  },
})
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
        <div class="input-bloc">
          <DsfrSelect
            v-model="selectOptionSelected"
            :label="selectLabel"
            :options="selectOptions"
          />
        </div>
        <div class="input-bloc">
          <DsfrInput
            v-model="inputValue"
            :label="inputLabel"
            label-visible
            :placeholder="inputPlaceholder"
            :hint="inputHint"
            type="number"
          />
        </div>
        <div class="input-bloc">
          <DsfrInput
            v-model="customPromptValue"
            :label-visible="true"
            :is-textarea="true"
            :label="customPromptLabel"
            :hint="customPromptHint"
          />
        </div>
      </div>
    </DsfrAccordion>
  </DsfrAccordionsGroup>
</template>

<style scoped>
  .input-bloc {
    margin-top: 2rem;
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
