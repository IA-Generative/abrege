<script lang="ts" setup>
import { DsfrToggleSwitch } from '@gouvminint/vue-dsfr'
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

const extractQaLabel = 'Générer aussi des questions/réponses'
const extractQaHint = 'En plus du résumé, extrait des questions/réponses à partir du document'
const extractQaValue = computed({
  get: () => paramsValue.extractQa,
  set: (value) => {
    paramsValue.extractQa = value
  },
})

const extractEntitiesLabel = 'Extraire les entités et relations'
const extractEntitiesHint = 'Identifie les personnes, organisations, lieux… et les relations entre elles'
const extractEntitiesValue = computed({
  get: () => paramsValue.extractEntities,
  set: (value) => {
    paramsValue.extractEntities = value
  },
})

const extractChunksLabel = 'Conserver les chunks sémantiques'
const extractChunksHint = 'Persiste les sous-découpages sémantiques utilisés pendant le résumé'
const extractChunksValue = computed({
  get: () => paramsValue.extractChunks,
  set: (value) => {
    paramsValue.extractChunks = value
  },
})

const classifyTopicsLabel = 'Classifier les sujets abordés'
const classifyTopicsHint = 'Détecte les grands thèmes du résumé, avec un score de confiance'
const classifyTopicsValue = computed({
  get: () => paramsValue.classifyTopics,
  set: (value) => {
    paramsValue.classifyTopics = value
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
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="extractQaValue"
            :label="extractQaLabel"
            :hint="extractQaHint"
          />
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="extractEntitiesValue"
            :label="extractEntitiesLabel"
            :hint="extractEntitiesHint"
          />
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="extractChunksValue"
            :label="extractChunksLabel"
            :hint="extractChunksHint"
          />
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="classifyTopicsValue"
            :label="classifyTopicsLabel"
            :hint="classifyTopicsHint"
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
