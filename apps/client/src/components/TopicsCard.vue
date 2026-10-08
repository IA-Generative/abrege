<script setup lang="ts">
import type { TopicRow } from '@/stores/abrege'
import { computed, ref } from 'vue'

const props = withDefaults(defineProps<{
  topics: TopicRow[]
  status?: string | null
  errorCode?: number | null
  visibleCount?: number
  embedded?: boolean
}>(), {
  status: null,
  errorCode: null,
  visibleCount: 5,
  embedded: false,
})

type Level = 'high' | 'medium' | 'low'

function level (confidence: number): Level {
  if (confidence >= 0.7) { return 'high' }
  if (confidence >= 0.4) { return 'medium' }
  return 'low'
}

const sortedTopics = computed(() => [...props.topics].sort((a, b) => b.confidence - a.confidence))

const expanded = ref(false)
const hiddenCount = computed(() => Math.max(0, sortedTopics.value.length - props.visibleCount))
const displayedTopics = computed(() =>
  expanded.value ? sortedTopics.value : sortedTopics.value.slice(0, props.visibleCount),
)

const isPending = computed(() => props.status === 'in_progress' || props.status === 'pending')
const isFailed = computed(() => props.status === 'failed')

const openedReasons = ref<Set<string>>(new Set())

function toggleReason (id: string) {
  const next = new Set(openedReasons.value)
  if (!next.delete(id)) { next.add(id) }
  openedReasons.value = next
}

function percent (topic: TopicRow): number {
  return Math.round(topic.confidence * 100)
}
</script>

<template>
  <section
    class="topics-card"
    :class="{ 'topics-card--embedded': embedded }"
    :aria-labelledby="embedded ? undefined : 'topics-card-title'"
  >
    <header class="topics-card__header">
      <h2
        v-if="!embedded"
        id="topics-card-title"
        class="topics-card__title"
      >
        Sujets détectés
        <span
          v-if="sortedTopics.length > 0"
          class="topics-card__count"
        >{{ sortedTopics.length }}</span>
      </h2>
      <ExtractionStatusBadge
        :status="status"
        :error-code="errorCode"
        label="Classification"
        class="topics-card__status"
      />
    </header>

    <ul
      v-if="sortedTopics.length > 0"
      class="topics-card__list"
    >
      <li
        v-for="topic in displayedTopics"
        :key="topic.id"
        class="topic"
      >
        <div class="topic__head">
          <span class="topic__name">{{ topic.topic }}</span>
          <span class="topic__percent">{{ percent(topic) }}%</span>
        </div>
        <div
          class="topic__meter"
          role="meter"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-valuenow="percent(topic)"
          :aria-label="`Confiance pour ${topic.topic}`"
        >
          <div
            class="topic__meter-fill"
            :class="`topic__meter-fill--${level(topic.confidence)}`"
            :style="{ width: `${percent(topic)}%` }"
          />
        </div>
        <template v-if="topic.explanation">
          <button
            type="button"
            class="topic__reason-toggle"
            :aria-expanded="openedReasons.has(topic.id)"
            :aria-controls="`topic-reason-${topic.id}`"
            @click="toggleReason(topic.id)"
          >
            {{ openedReasons.has(topic.id) ? 'Masquer la raison' : 'Voir la raison' }}
          </button>
          <p
            v-if="openedReasons.has(topic.id)"
            :id="`topic-reason-${topic.id}`"
            class="topic__explanation"
          >
            {{ topic.explanation }}
          </p>
        </template>
      </li>
    </ul>

    <p
      v-else-if="isPending"
      class="topics-card__message"
    >
      Analyse du document en cours…
    </p>
    <p
      v-else-if="isFailed"
      class="topics-card__message topics-card__message--error"
    >
      La classification a échoué. Les autres résultats ne sont pas affectés.
    </p>
    <p
      v-else
      class="topics-card__message"
    >
      Aucun sujet détecté pour ce document.
    </p>

    <button
      v-if="hiddenCount > 0"
      type="button"
      class="topics-card__toggle"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'Voir moins' : `Voir les ${hiddenCount} autre${hiddenCount > 1 ? 's' : ''} sujet${hiddenCount > 1 ? 's' : ''}` }}
    </button>
  </section>
</template>

<style scoped>
.topics-card {
  padding: 1.25rem 1.5rem;
  background: var(--background-default-grey);
  border: 1px solid var(--border-default-grey);
  border-left: 3px solid var(--border-plain-blue-france);
  border-radius: 0.25rem;
  box-shadow: 0 1px 3px rgb(0 0 0 / 8%);
}
.topics-card--embedded {
  padding: 0;
  background: none;
  border: none;
  border-radius: 0;
  box-shadow: none;
}
.topics-card--embedded .topics-card__header {
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}
.topics-card__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  margin-bottom: 1rem;
}
.topics-card__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.125rem;
  line-height: 1.5rem;
}
.topics-card__count {
  min-width: 1.5rem;
  padding: 0 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.5rem;
  text-align: center;
  color: var(--text-action-high-blue-france);
  background: var(--background-contrast-blue-france);
  border-radius: 0.75rem;
}
.topics-card__status {
  margin-left: auto;
}
.topics-card__list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}
.topic {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}
.topic__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
}
.topic__name {
  font-weight: 700;
  word-break: break-word;
}
.topic__percent {
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.topic__meter {
  height: 0.5rem;
  overflow: hidden;
  background: var(--background-contrast-grey);
  border-radius: 0.25rem;
}
.topic__meter-fill {
  height: 100%;
  border-radius: 0.25rem;
  transition: width 0.4s ease;
}
.topic__meter-fill--high {
  background: var(--border-plain-success);
}
.topic__meter-fill--medium {
  background: var(--border-plain-blue-france);
}
.topic__meter-fill--low {
  background: var(--border-plain-warning);
}
.topic__reason-toggle {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-action-high-blue-france);
  cursor: pointer;
  background: none;
  border: none;
}
.topic__reason-toggle::after {
  width: 0.4rem;
  height: 0.4rem;
  border-right: 2px solid currentcolor;
  border-bottom: 2px solid currentcolor;
  content: '';
  transform: rotate(45deg);
  transition: transform 0.2s ease;
}
.topic__reason-toggle[aria-expanded='true']::after {
  transform: rotate(-135deg);
}
.topic__reason-toggle:hover {
  color: var(--text-active-blue-france);
}
.topic__explanation {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-mention-grey);
}
.topics-card__message {
  margin: 0;
  color: var(--text-mention-grey);
}
.topics-card__message--error {
  color: var(--text-default-error);
}
.topics-card__toggle {
  margin-top: 1rem;
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
.topics-card__toggle:hover {
  color: var(--text-active-blue-france);
}
@media (prefers-reduced-motion: reduce) {
  .topic__meter-fill,
  .topic__reason-toggle::after {
    transition: none;
  }
}
</style>
