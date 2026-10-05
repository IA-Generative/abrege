<script lang="ts" setup>
import { computed, ref } from 'vue'
import ChunksParams from './ChunksParams.vue'
import EntitiesParams from './EntitiesParams.vue'
import QaParams from './QaParams.vue'
import TopicsParams from './TopicsParams.vue'

const sections = [
  { title: 'Questions/réponses', component: QaParams },
  { title: 'Entités et relations', component: EntitiesParams },
  { title: 'Chunks sémantiques', component: ChunksParams },
  { title: 'Classification des sujets', component: TopicsParams },
]

const current = ref(0)
const currentSection = computed(() => sections[current.value] as (typeof sections)[number])
const isFirst = computed(() => current.value === 0)
const isLast = computed(() => current.value === sections.length - 1)
const previousLabel = computed(() => isFirst.value ? 'Précédent' : `Précédent : ${sections[current.value - 1]?.title}`)
const nextLabel = computed(() => isLast.value ? 'Suivant' : `Suivant : ${sections[current.value + 1]?.title}`)
</script>

<template>
  <div class="advanced-params">
    <h3 class="fr-h6">
      Paramètres avancés
    </h3>
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
</template>

<style scoped>
  .advanced-params {
    margin-top: 2rem;
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
