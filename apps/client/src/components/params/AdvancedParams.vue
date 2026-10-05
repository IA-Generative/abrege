<script lang="ts" setup>
import { computed, ref } from 'vue'
import ChunksParams from './ChunksParams.vue'
import EntitiesParams from './EntitiesParams.vue'
import QaParams from './QaParams.vue'
import TopicsParams from './TopicsParams.vue'

const sections = [
  {
    title: 'Questions/réponses',
    component: QaParams,
  },
  {
    title: 'Entités et relations',
    component: EntitiesParams,
  },
  {
    title: 'Chunks sémantiques',
    component: ChunksParams,
  },
  {
    title: 'Classification des sujets',
    component: TopicsParams,
  },
]

const isOpen = ref(false)
const current = ref(0)
const currentSection = computed(() => sections[current.value] as (typeof sections)[number])
const isFirst = computed(() => current.value === 0)
const isLast = computed(() => current.value === sections.length - 1)
const previousLabel = computed(() => isFirst.value ? 'Précédent' : `Précédent : ${sections[current.value - 1]?.title}`)
const nextLabel = computed(() => isLast.value ? 'Suivant' : `Suivant : ${sections[current.value + 1]?.title}`)
</script>

<template>
  <div class="advanced-params">
    <h3 class="advanced-heading">
      <button
        type="button"
        class="advanced-toggle"
        :aria-expanded="isOpen"
        aria-controls="advanced-panel"
        @click="isOpen = !isOpen"
      >
        Paramètres avancés
      </button>
    </h3>
    <div
      v-show="isOpen"
      id="advanced-panel"
      class="advanced-panel"
    >
      <div
        class="advanced-card"
        aria-live="polite"
      >
        <p class="advanced-card__title fr-text--bold">
          {{ currentSection.title }}
          <span class="advanced-card__counter">({{ current + 1 }}/{{ sections.length }})</span>
        </p>
        <component :is="currentSection.component" />
      </div>
      <div class="advanced-nav">
        <DsfrButton
          :label="previousLabel"
          secondary
          icon="ri-arrow-left-line"
          :disabled="isFirst"
          @click="current--"
        />
        <DsfrButton
          :label="nextLabel"
          secondary
          icon="ri-arrow-right-line"
          icon-right
          :disabled="isLast"
          @click="current++"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
  .advanced-params {
    margin-top: 2rem;
  }
  .advanced-heading {
    margin: 0;
  }
  .advanced-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 1rem;
    font: inherit;
    font-weight: 700;
    color: var(--text-action-high-blue-france);
    text-align: left;
    background: transparent;
    border: 0;
    border-bottom: 1px solid var(--border-default-grey);
    cursor: pointer;
  }
  .advanced-toggle::after {
    flex-shrink: 0;
    width: 0.5rem;
    height: 0.5rem;
    margin-left: 1rem;
    border-right: 2px solid currentcolor;
    border-bottom: 2px solid currentcolor;
    content: '';
    transform: rotate(45deg);
    transition: transform 0.2s ease;
  }
  .advanced-toggle[aria-expanded='true']::after {
    transform: rotate(-135deg);
  }
  .advanced-panel {
    padding-top: 1rem;
  }
  .advanced-card {
    padding: 1rem 1.5rem 1.5rem;
    border: 1px solid var(--border-default-grey);
  }
  .advanced-card__title {
    margin: 0;
  }
  .advanced-card__counter {
    font-weight: normal;
    color: var(--text-mention-grey);
  }
  .advanced-nav {
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
  }
</style>
