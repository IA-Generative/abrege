<script lang="ts" setup>
import type { EntityDefinition, EntityDefinitionType } from '@/stores/abrege'
import { computed, nextTick, ref } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const { paramsValue } = useAbregeStore()

const typeOptions: { value: EntityDefinitionType, text: string }[] = [
  { value: 'string', text: 'Texte' },
  { value: 'number', text: 'Nombre' },
  { value: 'date', text: 'Date' },
  { value: 'boolean', text: 'Booléen (oui/non)' },
  { value: 'enum', text: 'Liste de valeurs' },
]
const typeLabels: Record<string, string> = Object.fromEntries(typeOptions.map(option => [option.value, option.text]))

const editingId = ref<number | null>(null)
const isEditing = computed(() => editingId.value !== null)

function isDuplicate (entity: EntityDefinition) {
  const name = entity.name.trim().toLowerCase()
  return !!name && paramsValue.entityDefinitions.some(
    other => other.id !== entity.id && other.name.trim().toLowerCase() === name,
  )
}

function canFinish (entity: EntityDefinition) {
  return !!entity.name.trim() && !isDuplicate(entity)
}

function addDefinition () {
  const id = Math.max(-1, ...paramsValue.entityDefinitions.map(entity => entity.id)) + 1
  paramsValue.entityDefinitions.push({
    id,
    name: '',
    type: 'string',
    definition: '',
    examples: [],
    enumValues: '',
  })
  editingId.value = id
}

function exampleId (entity: EntityDefinition, index: number) {
  return `example-${entity.id}-${index}`
}

async function addExample (entity: EntityDefinition) {
  entity.examples.push('')
  await nextTick()
  document.getElementById(exampleId(entity, entity.examples.length - 1))?.focus()
}

function removeExample (entity: EntityDefinition, index: number) {
  entity.examples.splice(index, 1)
}

function removeDefinition (id: number) {
  paramsValue.entityDefinitions = paramsValue.entityDefinitions.filter(entity => entity.id !== id)
  if (editingId.value === id) {
    editingId.value = null
  }
}
</script>

<template>
  <section class="definitions">
    <header class="definitions__intro">
      <h4 class="fr-text--bold definitions__title">
        Définition des entités à extraire
      </h4>
      <p class="fr-hint-text">
        Optionnel. Décrivez les entités attendues pour guider l'extraction.
      </p>
    </header>

    <p
      v-if="!paramsValue.entityDefinitions.length"
      class="definitions__empty"
    >
      Aucune entité définie : le modèle les détermine seul.
    </p>

    <ul
      v-else
      class="definition-list"
    >
      <li
        v-for="(entity, index) in paramsValue.entityDefinitions"
        :key="entity.id"
        class="definition-card"
        :class="{ 'definition-card--editing': editingId === entity.id }"
      >
        <template v-if="editingId === entity.id">
          <div class="definition-card__row">
            <span class="fr-text--bold">Entité {{ index + 1 }}</span>
            <DsfrButton
              label="Supprimer"
              tertiary
              no-outline
              icon="ri-delete-bin-line"
              size="sm"
              @click="removeDefinition(entity.id)"
            />
          </div>

          <div class="definition-form">
            <DsfrInput
              v-model="entity.name"
              label="Nom"
              label-visible
              hint="Ex : date_signature"
            />
            <DsfrSelect
              v-model="entity.type"
              label="Type"
              :options="typeOptions"
            />
            <div class="definition-form__wide">
              <DsfrInput
                v-model="entity.definition"
                label="Définition"
                label-visible
                is-textarea
                hint="Ce que le modèle doit repérer, ex : « date à laquelle le contrat est signé »"
              />
            </div>
            <div
              v-if="entity.type === 'enum'"
              class="definition-form__wide"
            >
              <DsfrInput
                v-model="entity.enumValues"
                label="Valeurs autorisées"
                label-visible
                is-textarea
                hint="Une valeur par ligne"
              />
            </div>
            <div class="definition-form__wide examples">
              <p class="fr-label examples__title">
                Exemples
                <span class="fr-hint-text">Optionnel, des valeurs concrètes que le modèle doit reconnaître</span>
              </p>
              <ul
                v-if="entity.examples.length"
                class="examples__list"
              >
                <li
                  v-for="(_, exampleIndex) in entity.examples"
                  :key="exampleIndex"
                  class="examples__item"
                >
                  <DsfrInput
                    :id="exampleId(entity, exampleIndex)"
                    v-model="entity.examples[exampleIndex]"
                    :label="`Exemple ${exampleIndex + 1}`"
                    class="examples__input"
                    @keydown.enter.prevent="addExample(entity)"
                  />
                  <DsfrButton
                    :title="`Supprimer l'exemple ${exampleIndex + 1}`"
                    label="Supprimer"
                    icon-only
                    icon="ri-close-line"
                    tertiary
                    no-outline
                    size="sm"
                    @click="removeExample(entity, exampleIndex)"
                  />
                </li>
              </ul>
              <DsfrButton
                label="Ajouter un exemple"
                tertiary
                icon="ri-add-line"
                size="sm"
                @click="addExample(entity)"
              />
            </div>
          </div>

          <div class="definition-card__row definition-card__footer">
            <p
              v-if="isDuplicate(entity)"
              class="fr-error-text"
            >
              Ce nom est déjà utilisé par une autre entité.
            </p>
            <DsfrButton
              label="Terminer"
              icon="ri-check-line"
              size="sm"
              :disabled="!canFinish(entity)"
              @click="editingId = null"
            />
          </div>
        </template>

        <div
          v-else
          class="definition-card__row"
        >
          <div class="definition-summary">
            <div class="definition-summary__head">
              <span class="fr-text--bold definition-summary__name">{{ entity.name || 'Sans nom' }}</span>
              <DsfrBadge
                :label="typeLabels[entity.type] ?? entity.type"
                type="info"
                small
                no-icon
              />
            </div>
            <p
              v-if="entity.definition"
              class="definition-summary__text"
            >
              {{ entity.definition }}
            </p>
          </div>
          <div class="definition-card__actions">
            <DsfrButton
              label="Modifier"
              secondary
              icon="ri-edit-line"
              size="sm"
              :disabled="isEditing"
              @click="editingId = entity.id"
            />
            <DsfrButton
              label="Supprimer"
              tertiary
              no-outline
              icon="ri-delete-bin-line"
              size="sm"
              :disabled="isEditing"
              @click="removeDefinition(entity.id)"
            />
          </div>
        </div>
      </li>
    </ul>

    <DsfrButton
      label="Ajouter une entité"
      secondary
      icon="ri-add-line"
      :disabled="isEditing"
      @click="addDefinition"
    />
  </section>
</template>

<style scoped>
  .definitions {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-default-grey);
  }
  .definitions__intro,
  .definition-list {
    width: 100%;
  }
  .definitions__title,
  .definitions__intro p {
    margin: 0;
  }
  .definitions__empty {
    margin: 0;
    color: var(--text-mention-grey);
  }
  .definition-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .definition-card {
    padding: 0.75rem 1rem;
    background: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    border-left: 3px solid var(--border-default-blue-france);
    border-radius: 0.25rem;
    box-shadow: 0 1px 3px rgb(0 0 0 / 8%);
    transition: box-shadow 0.15s ease;
  }
  .definition-card--editing {
    padding: 1rem 1.25rem 1.25rem;
    border-left-color: var(--border-plain-blue-france);
    box-shadow: 0 4px 12px rgb(0 0 18 / 12%);
  }
  .definition-card__row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
  .definition-card__actions {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 0.25rem;
  }
  .definition-card__footer {
    justify-content: flex-end;
    margin-top: 1.25rem;
  }
  .definition-form {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    margin-top: 0.75rem;
  }
  .definition-form__wide {
    grid-column: 1 / -1;
  }
  .definition-summary {
    min-width: 0;
  }
  .definition-summary__head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
  }
  .definition-summary__name {
    word-break: break-word;
  }
  .definition-summary__text {
    margin: 0.25rem 0 0;
    overflow: hidden;
    color: var(--text-mention-grey);
    font-size: 0.875rem;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .examples {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .examples__title {
    display: flex;
    flex-direction: column;
    margin: 0;
  }
  .examples__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .examples__item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .examples__input {
    flex: 1;
  }
  @media (min-width: 768px) {
    .definition-form {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
