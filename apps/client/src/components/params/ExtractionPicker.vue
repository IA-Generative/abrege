<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import ChunksParams from './ChunksParams.vue'
import EntitiesParams from './EntitiesParams.vue'
import QaParams from './QaParams.vue'
import TopicsParams from './TopicsParams.vue'

type FlagName = 'extractQa' | 'extractEntities' | 'extractChunks' | 'classifyTopics'

interface ExtractionOption {
  key: string
  flag: FlagName
  title: string
  description: string
  component: object
  customizations: () => number
}

const { paramsValue } = useAbregeStore()

const filled = (value: unknown) => (typeof value === 'string' && value.trim() ? 1 : 0)

const options: ExtractionOption[] = [
  {
    key: 'qa',
    flag: 'extractQa',
    title: 'Questions/réponses',
    description: 'Des questions qu\'un lecteur pourrait se poser, avec leur réponse tirée du texte.',
    component: QaParams,
    customizations: () => filled(paramsValue.qaInstructions),
  },
  {
    key: 'entities',
    flag: 'extractEntities',
    title: 'Entités et relations',
    description: 'Les personnes, dates, montants… cités dans le document, et les liens entre eux.',
    component: EntitiesParams,
    customizations: () => filled(paramsValue.entitiesInstructions) + paramsValue.entityDefinitions.length,
  },
  {
    key: 'chunks',
    flag: 'extractChunks',
    title: 'Chunks sémantiques',
    description: 'Le document découpé en passages cohérents, pour retrouver d\'où vient une information.',
    component: ChunksParams,
    customizations: () => filled(paramsValue.chunksInstructions),
  },
  {
    key: 'topics',
    flag: 'classifyTopics',
    title: 'Classification des sujets',
    description: 'Les grands thèmes du document, avec un score de confiance.',
    component: TopicsParams,
    customizations: () => filled(paramsValue.topicsInstructions) + paramsValue.topicDefinitions.length,
  },
]

const customizing = ref<string | null>(null)
const openOption = computed(() => options.find(option => option.key === customizing.value))

const isEnabled = (option: ExtractionOption) => !!paramsValue[option.flag]
const allSelected = computed(() => options.every(isEnabled))

function setEnabled (option: ExtractionOption, value: boolean) {
  paramsValue[option.flag] = value
  if (!value && customizing.value === option.key) {
    customizing.value = null
  }
}

function toggleAll () {
  const target = !allSelected.value
  for (const option of options) {
    setEnabled(option, target)
  }
}

function toggleCustomize (option: ExtractionOption) {
  customizing.value = customizing.value === option.key ? null : option.key
}
</script>

<template>
  <section
    class="picker"
    aria-labelledby="picker-title"
  >
    <header class="picker__header">
      <div>
        <h3
          id="picker-title"
          class="fr-h6 picker__title"
        >
          Que voulez-vous obtenir en plus du résumé ?
        </h3>
        <p class="fr-hint-text picker__hint">
          Facultatif. Cochez ce qui vous intéresse, vous pourrez ensuite le personnaliser.
        </p>
      </div>
      <DsfrButton
        size="sm"
        tertiary
        :icon="allSelected ? 'ri-checkbox-multiple-blank-line' : 'ri-checkbox-multiple-line'"
        :label="allSelected ? 'Tout désélectionner' : 'Tout sélectionner'"
        @click="toggleAll"
      />
    </header>

    <div class="picker__grid">
      <div
        v-for="option in options"
        :key="option.key"
        class="card"
        :class="{ 'card--active': isEnabled(option), 'card--open': customizing === option.key }"
      >
        <div class="fr-checkbox-group card__check">
          <input
            :id="`extract-${option.key}`"
            type="checkbox"
            :checked="isEnabled(option)"
            @change="setEnabled(option, ($event.target as HTMLInputElement).checked)"
          >
          <label
            class="fr-label"
            :for="`extract-${option.key}`"
          >
            {{ option.title }}
            <span class="fr-hint-text">{{ option.description }}</span>
          </label>
        </div>
        <div
          v-if="isEnabled(option)"
          class="card__actions"
        >
          <button
            type="button"
            class="card__customize"
            :aria-expanded="customizing === option.key"
            :aria-controls="`picker-panel-${option.key}`"
            @click="toggleCustomize(option)"
          >
            {{ customizing === option.key ? 'Fermer' : 'Personnaliser' }}
          </button>
          <span
            v-if="option.customizations() > 0"
            class="fr-badge fr-badge--sm fr-badge--info fr-badge--no-icon"
          >
            Personnalisé
          </span>
        </div>
      </div>
    </div>

    <div
      v-if="openOption"
      :id="`picker-panel-${openOption.key}`"
      class="panel"
    >
      <p class="panel__title fr-text--bold">
        Personnaliser : {{ openOption.title }}
      </p>
      <component :is="openOption.component" />
    </div>
  </section>
</template>

<style scoped>
  .picker {
    margin-top: 1.5rem;
  }
  .picker__header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem 1rem;
    margin-bottom: 1rem;
  }
  .picker__title,
  .picker__hint {
    margin: 0;
  }
  .picker__grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  .card {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    border-radius: 0.25rem;
    transition: border-color 0.15s ease, background-color 0.15s ease;
  }
  .card--active {
    background: var(--background-alt-blue-france);
    border-color: var(--border-plain-blue-france);
  }
  .card__check {
    margin: 0;
  }
  .card__actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding-left: 2rem;
  }
  .card__customize {
    padding: 0;
    font: inherit;
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--text-action-high-blue-france);
    text-decoration: underline;
    cursor: pointer;
    background: none;
    border: none;
  }
  .card__customize:hover {
    color: var(--text-active-blue-france);
  }
  .panel {
    margin-top: 1rem;
    padding: 1rem 1.25rem 1.25rem;
    background: var(--background-default-grey);
    border: 1px solid var(--border-plain-blue-france);
    border-left-width: 3px;
    border-radius: 0.25rem;
  }
  .panel__title {
    margin: 0 0 0.75rem;
  }
  @media (min-width: 768px) {
    .picker__grid {
      grid-template-columns: 1fr 1fr;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .card {
      transition: none;
    }
  }
</style>
