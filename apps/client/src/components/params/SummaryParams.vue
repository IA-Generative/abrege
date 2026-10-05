<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const selectLabel = 'Choisissez en quelle langue sera généré votre résumé'
const selectOptions = [{ value: 'French', text: 'Français (par défaut)' }, { value: 'English', text: 'Anglais' }]
const selectOptionSelected = computed({
  get: () => paramsValue.selectOptionSelected,
  set: (value) => {
    paramsValue.selectOptionSelected = value
    paramsValue.selectOptionText = selectOptions.find(option => option.value === value)?.text || ''
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

const customPromptLabel = 'Rajoutez une instruction supplémentaire'
const customPromptHint = 'Ex : “utilise un ton très formel” ou “liste les points importants”'
const customPromptValue = computed({
  get: () => paramsValue.customPrompt,
  set: (value) => {
    paramsValue.customPrompt = value
  },
})
</script>

<template>
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
</template>

<style scoped>
  .input-bloc {
    margin-top: 2rem;
  }
</style>
