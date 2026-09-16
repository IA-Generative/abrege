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
const qaInstructionsLabel = 'Instruction supplémentaire — Questions/réponses'
const qaInstructionsHint = 'Ex : "privilégie des questions chiffrées" ou "formule les réponses en une phrase"'
const qaInstructionsValue = computed({
  get: () => paramsValue.qaInstructions,
  set: (value) => {
    paramsValue.qaInstructions = value
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
const entitiesInstructionsLabel = 'Instruction supplémentaire — Entités et relations'
const entitiesInstructionsHint = 'Ex : "concentre-toi sur les personnes et organisations, ignore les lieux"'
const entitiesInstructionsValue = computed({
  get: () => paramsValue.entitiesInstructions,
  set: (value) => {
    paramsValue.entitiesInstructions = value
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
const chunksInstructionsLabel = 'Instruction supplémentaire — Découpage'
const chunksInstructionsHint = 'Ex : "découpe par section plutôt que par paragraphe"'
const chunksInstructionsValue = computed({
  get: () => paramsValue.chunksInstructions,
  set: (value) => {
    paramsValue.chunksInstructions = value
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
const topicsInstructionsLabel = 'Instruction supplémentaire — Classification'
const topicsInstructionsHint = 'Ex : "utilise des catégories métier RH (recrutement, paie, formation…)"'
const topicsInstructionsValue = computed({
  get: () => paramsValue.topicsInstructions,
  set: (value) => {
    paramsValue.topicsInstructions = value
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
          <div
            v-if="extractQaValue"
            class="instruction-bloc"
          >
            <DsfrInput
              v-model="qaInstructionsValue"
              :label-visible="true"
              :is-textarea="true"
              :label="qaInstructionsLabel"
              :hint="qaInstructionsHint"
            />
          </div>
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="extractEntitiesValue"
            :label="extractEntitiesLabel"
            :hint="extractEntitiesHint"
          />
          <div
            v-if="extractEntitiesValue"
            class="instruction-bloc"
          >
            <DsfrInput
              v-model="entitiesInstructionsValue"
              :label-visible="true"
              :is-textarea="true"
              :label="entitiesInstructionsLabel"
              :hint="entitiesInstructionsHint"
            />
          </div>
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="extractChunksValue"
            :label="extractChunksLabel"
            :hint="extractChunksHint"
          />
          <div
            v-if="extractChunksValue"
            class="instruction-bloc"
          >
            <DsfrInput
              v-model="chunksInstructionsValue"
              :label-visible="true"
              :is-textarea="true"
              :label="chunksInstructionsLabel"
              :hint="chunksInstructionsHint"
            />
          </div>
        </div>
        <div class="input-bloc">
          <DsfrToggleSwitch
            v-model="classifyTopicsValue"
            :label="classifyTopicsLabel"
            :hint="classifyTopicsHint"
          />
          <div
            v-if="classifyTopicsValue"
            class="instruction-bloc"
          >
            <DsfrInput
              v-model="topicsInstructionsValue"
              :label-visible="true"
              :is-textarea="true"
              :label="topicsInstructionsLabel"
              :hint="topicsInstructionsHint"
            />
          </div>
        </div>
      </div>
    </DsfrAccordion>
  </DsfrAccordionsGroup>
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
  :deep(textarea){
    min-height: 114px;
  }
  @media (min-width: 768px) {
    textarea {
      min-height: 144px;
    }
  }
</style>
