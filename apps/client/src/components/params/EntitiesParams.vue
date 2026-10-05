<script lang="ts" setup>
import { computed } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import DefinitionsEditor from './DefinitionsEditor.vue'

const { paramsValue } = useAbregeStore()

const typeOptions = [
  { value: 'string', text: 'Texte' },
  { value: 'number', text: 'Nombre' },
  { value: 'date', text: 'Date' },
  { value: 'boolean', text: 'Booléen (oui/non)' },
  { value: 'enum', text: 'Liste de valeurs' },
]

const instructionsLabel = 'Instruction supplémentaire'
const instructionsHint = 'Ex : "concentre-toi sur les personnes et organisations, ignore les lieux"'
const instructions = computed({
  get: () => paramsValue.entitiesInstructions,
  set: (value) => {
    paramsValue.entitiesInstructions = value
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
      v-model="paramsValue.entityDefinitions"
      title="Entités à extraire"
      hint="Optionnel. Listez les entités attendues : l'extraction se limite alors à celles-ci."
      empty-text="Aucune entité définie : le modèle les détermine seul."
      item-label="Entité"
      add-label="Ajouter une entité"
      name-hint="Ex : date_signature"
      definition-hint="Ce que le modèle doit repérer, ex : « date à laquelle le contrat est signé »"
      id-prefix="entity"
      :type-options="typeOptions"
    />
  </div>
</template>
