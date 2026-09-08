<script setup lang="ts">
import type { TopicRow } from '@/stores/abrege'
import { computed, ref } from 'vue'

const props = withDefaults(defineProps<{
  topics: TopicRow[]
  visibleCount?: number
}>(), {
  visibleCount: 5,
})

type BadgeType = 'success' | 'new' | 'warning'

function badgeType (confidence: number): BadgeType {
  if (confidence >= 0.7) return 'success'
  if (confidence >= 0.4) return 'new'
  return 'warning'
}

function tooltipContent (topic: TopicRow): string {
  const confidencePct = Math.round(topic.confidence * 100)
  const explanation = topic.explanation ?? 'Aucune explication disponible.'
  const model = topic.model_name ? ` (modèle : ${topic.model_name})` : ''
  return `Confiance : ${confidencePct}%${model} — ${explanation}`
}

const sortedTopics = computed(() => [...props.topics].sort((a, b) => b.confidence - a.confidence))

const expanded = ref(false)

const hiddenCount = computed(() => Math.max(0, sortedTopics.value.length - props.visibleCount))

const displayedTopics = computed(() =>
  expanded.value ? sortedTopics.value : sortedTopics.value.slice(0, props.visibleCount),
)

function toggleExpanded () {
  expanded.value = !expanded.value
}
</script>

<template>
  <div v-if="sortedTopics.length > 0" class="topic-badges">
    <DsfrTooltip
      v-for="topic in displayedTopics"
      :key="topic.id"
      :content="tooltipContent(topic)"
      on-hover
    >
      <DsfrBadge
        :label="`${topic.topic} · ${Math.round(topic.confidence * 100)}%`"
        :type="badgeType(topic.confidence)"
        small
      />
    </DsfrTooltip>

    <button
      v-if="hiddenCount > 0"
      type="button"
      class="topic-badges-toggle"
      @click="toggleExpanded"
    >
      {{ expanded ? 'Voir moins' : `+${hiddenCount} autre${hiddenCount > 1 ? 's' : ''}` }}
    </button>
  </div>
</template>

<style scoped>
.topic-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}
.topic-badges-toggle {
  border: none;
  background: none;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-action-high-blue-france);
  cursor: pointer;
  text-decoration: underline;
}
.topic-badges-toggle:hover {
  color: var(--text-active-blue-france);
}
</style>
