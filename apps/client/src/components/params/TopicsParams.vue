<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import DefinitionsEditor from './DefinitionsEditor.vue'

const { paramsValue } = useAbregeStore()

const instructionsLabel = 'Instruction supplémentaire'
const instructionsHint = 'Ex : "utilise des catégories métier RH (recrutement, paie, formation…)"'
const instructions = computed({
  get: () => paramsValue.topicsInstructions,
  set: (value) => {
    paramsValue.topicsInstructions = value
  },
})
</script>

<template>
  <div>
    <DsfrInput
      v-model="instructions"
      :label-visible="true"
      :is-textarea="true"
      :label="instructionsLabel"
      :hint="instructionsHint"
    />
    <DefinitionsEditor
      v-model="paramsValue.topicDefinitions"
      title="Sujets attendus"
      hint="Optionnel. Listez vos propres sujets : la classification s'en sert de repères."
      empty-text="Aucun sujet défini : le modèle les détermine seul."
      item-label="Sujet"
      add-label="Ajouter un sujet"
      name-hint="Ex : recrutement"
      definition-hint="Quand rattacher un document à ce sujet, ex : « offres d'emploi, entretiens, contrats d'embauche »"
      id-prefix="topic"
    />
  </div>
</template>
