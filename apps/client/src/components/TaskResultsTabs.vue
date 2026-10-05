<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import TaskChunksResults from './TaskChunksResults.vue'
import TaskEntitiesResults from './TaskEntitiesResults.vue'
import TaskQAResults from './TaskQAResults.vue'
import TaskTopicsResults from './TaskTopicsResults.vue'

const props = defineProps<{
  taskId: string
  parameters?: {
    extract_qa?: boolean
    extract_entities?: boolean
    extract_chunks?: boolean
    classify_topics?: boolean
  } | null
  qaEntitiesStatus?: string | null
  relationshipsStatus?: string | null
  topicsStatus?: string | null
}>()

const emit = defineEmits<{ (e: 'retry'): void }>()

const abrege = useAbregeStore()
const overview = computed(() => abrege.resultsOverview)

type Phase = 'pending' | 'done' | 'failed' | null

function phase (...statuses: (string | null | undefined)[]): Phase {
  const known = statuses.filter(Boolean)
  if (known.includes('failed')) { return 'failed' }
  if (known.some(status => status === 'pending' || status === 'in_progress')) { return 'pending' }
  if (known.length > 0 && known.every(status => status === 'completed')) { return 'done' }
  return null
}

const phaseText: Record<string, string> = { pending: 'en cours…', done: 'terminé', failed: 'échec' }

interface ResultTab {
  key: string
  label: string
  title: string
  description: string
  count: number
  detail?: string
  phase: Phase
  retryable: boolean
  component: object
  props: Record<string, unknown>
}

// Each extraction is opt-in per task (see ExtractionPicker.vue): only requested ones get a tab.
const tabs = computed<ResultTab[]>(() => {
  const result: ResultTab[] = []
  if (props.parameters?.classify_topics) {
    result.push({
      key: 'topics',
      label: 'Sujets',
      title: 'Classification des sujets',
      description: 'Les grands thèmes du document, avec un score de confiance et la raison de chaque choix.',
      count: overview.value.topics,
      phase: phase(props.topicsStatus),
      retryable: false,
      component: TaskTopicsResults,
      props: { taskId: props.taskId, status: props.topicsStatus },
    })
  }
  if (props.parameters?.extract_qa) {
    result.push({
      key: 'qa',
      label: 'Q&R',
      title: 'Questions / réponses',
      description: 'Les questions qu\'un lecteur pourrait se poser, avec la réponse tirée du texte.',
      count: overview.value.qa,
      phase: phase(props.qaEntitiesStatus),
      retryable: true,
      component: TaskQAResults,
      props: { taskId: props.taskId, status: props.qaEntitiesStatus },
    })
  }
  if (props.parameters?.extract_entities) {
    result.push({
      key: 'entities',
      label: 'Entités',
      title: 'Entités et relations',
      description: 'Les personnes, dates, montants… cités dans le document, et les liens entre eux, en liste ou en graphe.',
      count: overview.value.entities,
      detail: `${overview.value.relationships} relation${overview.value.relationships > 1 ? 's' : ''}`,
      phase: phase(props.qaEntitiesStatus, props.relationshipsStatus),
      retryable: true,
      component: TaskEntitiesResults,
      props: { taskId: props.taskId, entitiesStatus: props.qaEntitiesStatus, relationshipsStatus: props.relationshipsStatus },
    })
  }
  if (props.parameters?.extract_chunks) {
    result.push({
      key: 'chunks',
      label: 'Chunks',
      title: 'Chunks sémantiques',
      description: 'Le document découpé en passages cohérents, pour retrouver d\'où vient une information.',
      count: overview.value.chunks,
      phase: phase(props.qaEntitiesStatus),
      retryable: true,
      component: TaskChunksResults,
      props: { taskId: props.taskId, status: props.qaEntitiesStatus },
    })
  }
  return result
})

const activeKey = ref<string>()
const active = computed(() => tabs.value.find(tab => tab.key === activeKey.value) ?? tabs.value[0])
const expanded = ref(false)
const entitiesSubTab = ref(0)
const retrying = ref(false)

const panelProps = computed(() => (active.value?.key === 'entities'
  ? { ...active.value.props, initialTab: entitiesSubTab.value, expanded: expanded.value }
  : active.value?.props))

function focusTab (index: number) {
  const tab = tabs.value[(index + tabs.value.length) % tabs.value.length]
  if (tab) {
    activeKey.value = tab.key
    document.getElementById(`results-tab-${tab.key}`)?.focus()
  }
}

async function retry () {
  retrying.value = true
  try {
    await abrege.retryExtraction(props.taskId)
    emit('retry')
  } catch {
    // the store already reported the error
  } finally {
    retrying.value = false
  }
}

onMounted(() => abrege.fetchResultsOverview(props.taskId))
// Counts follow the extraction while the task is polled.
watch(
  () => [props.qaEntitiesStatus, props.relationshipsStatus, props.topicsStatus],
  () => abrege.fetchResultsOverview(props.taskId),
)
</script>

<template>
  <section
    v-if="tabs.length > 0 && active"
    class="results"
    aria-labelledby="results-title"
  >
    <h3
      id="results-title"
      class="fr-h6 results__title"
    >
      Analyse du document
    </h3>

    <p
      v-if="overview.topTopics.length > 0"
      class="results__topics"
    >
      <span class="results__topics-label">Sujets principaux</span>
      <span
        v-for="topic in overview.topTopics"
        :key="topic.id"
        class="chip"
      >
        {{ topic.topic }} <strong>{{ Math.round(topic.confidence * 100) }}%</strong>
      </span>
    </p>

    <div
      class="tabs"
      role="tablist"
      aria-label="Résultats de l'analyse"
    >
      <button
        v-for="(tab, index) in tabs"
        :id="`results-tab-${tab.key}`"
        :key="tab.key"
        type="button"
        role="tab"
        class="tab"
        :class="{ 'tab--active': tab.key === active.key }"
        :aria-selected="tab.key === active.key"
        :aria-controls="`results-panel-${tab.key}`"
        :tabindex="tab.key === active.key ? 0 : -1"
        :title="tab.description"
        @click="activeKey = tab.key"
        @keydown.right.prevent="focusTab(index + 1)"
        @keydown.left.prevent="focusTab(index - 1)"
      >
        <span class="tab__label">{{ tab.label }}</span>
        <span class="tab__meta">
          <strong class="tab__count">{{ tab.count }}</strong>
          <span
            v-if="tab.phase"
            class="tab__status"
            :class="`tab__status--${tab.phase}`"
          >{{ phaseText[tab.phase] }}</span>
        </span>
      </button>
    </div>

    <div
      :id="`results-panel-${active.key}`"
      class="panel"
      role="tabpanel"
      :aria-labelledby="`results-tab-${active.key}`"
    >
      <header class="panel__header">
        <div>
          <p class="panel__title fr-text--bold">
            {{ active.title }}
            <span
              v-if="active.detail"
              class="panel__detail"
            >· {{ active.detail }}</span>
          </p>
          <p class="panel__description">
            {{ active.description }}
          </p>
        </div>
        <div class="panel__actions">
          <DsfrButton
            v-if="active.phase === 'failed' && active.retryable"
            size="sm"
            secondary
            icon="ri-refresh-line"
            :label="retrying ? 'Relance…' : 'Réessayer'"
            :disabled="retrying"
            @click="retry"
          />
          <DsfrButton
            size="sm"
            tertiary
            icon="ri-fullscreen-line"
            label="Agrandir"
            @click="expanded = true"
          />
        </div>
      </header>

      <component
        :is="active.component"
        :key="active.key"
        v-bind="panelProps"
        @tab-change="entitiesSubTab = $event"
      />
    </div>

    <DsfrModal
      v-if="expanded"
      :opened="expanded"
      :title="active.title"
      size="xl"
      @close="expanded = false"
    >
      <component
        :is="active.component"
        :key="`expanded-${active.key}`"
        v-bind="panelProps"
        @tab-change="entitiesSubTab = $event"
      />
    </DsfrModal>
  </section>
</template>

<style scoped>
  .results {
    margin-top: 2rem;
  }
  .results__title {
    margin: 0 0 0.75rem;
  }
  .results__topics {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin: 0 0 1rem;
  }
  .results__topics-label {
    font-size: 0.875rem;
    color: var(--text-mention-grey);
  }
  .chip {
    padding: 0.125rem 0.625rem;
    font-size: 0.875rem;
    background: var(--background-contrast-blue-france);
    color: var(--text-action-high-blue-france);
    border-radius: 1rem;
  }
  .tabs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.5rem;
  }
  .tab {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    padding: 0.625rem 0.875rem;
    font: inherit;
    text-align: left;
    cursor: pointer;
    background: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    border-bottom: 3px solid transparent;
    border-radius: 0.25rem 0.25rem 0 0;
  }
  .tab:hover {
    background: var(--background-alt-blue-france);
  }
  .tab--active {
    background: var(--background-alt-blue-france);
    border-color: var(--border-plain-blue-france);
    border-bottom-color: var(--border-plain-blue-france);
  }
  .tab__label {
    font-weight: 700;
    color: var(--text-action-high-blue-france);
  }
  .tab__meta {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }
  .tab__count {
    font-size: 1.25rem;
    line-height: 1.5rem;
  }
  .tab__status {
    font-size: 0.75rem;
  }
  .tab__status--done {
    color: var(--text-default-success);
  }
  .tab__status--failed {
    color: var(--text-default-error);
    font-weight: 700;
  }
  .tab__status--pending {
    color: var(--text-default-info);
    animation: results-pulse 1.6s ease-in-out infinite;
  }
  .panel {
    padding: 1rem 1.25rem 1.25rem;
    border: 1px solid var(--border-plain-blue-france);
    border-top-width: 1px;
  }
  .panel__header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem 1rem;
    margin-bottom: 1rem;
  }
  .panel__title,
  .panel__description {
    margin: 0;
  }
  .panel__detail {
    font-weight: normal;
    color: var(--text-mention-grey);
  }
  .panel__description {
    font-size: 0.875rem;
    color: var(--text-mention-grey);
  }
  .panel__header > div:first-child {
    flex: 1 1 18rem;
  }
  .panel__actions {
    display: flex;
    flex-shrink: 0;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-left: auto;
  }
  @keyframes results-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  @media (prefers-reduced-motion: reduce) {
    .tab__status--pending {
      animation: none;
    }
  }
</style>
