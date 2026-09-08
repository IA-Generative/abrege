<script setup lang="ts">
import type { EntityRow, RelationshipRow } from '@/stores/abrege'
import Graph from 'graphology'
import Sigma from 'sigma'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import CustomTabs from './CustomTabs.vue'

const props = defineProps<{
  opened: boolean
  taskId: string
  entitiesStatus?: string | null
  relationshipsStatus?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const abrege = useAbregeStore()

const activeTab = ref(0)
const tabsData = [
  { label: 'Liste', slot: 'list' },
  { label: 'Graphe', slot: 'graph' },
]

// ----- Onglet liste -----
const entityHeaders = ['Type', 'Texte', 'Pages', 'Chunk', 'Modèle']
const entityRows = computed(() =>
  abrege.entities.map(e => [e.type, e.text, (e.pages ?? []).join(', ') || '—', String(e.chunk_index), e.model_name ?? '—']),
)

const entityLabelById = computed(() => {
  const map = new Map<string, string>()
  for (const e of abrege.entities) map.set(e.id, e.text)
  return map
})

const relationshipHeaders = ['Source', 'Relation', 'Cible', 'Description', 'Portée', 'Modèle']
const relationshipRows = computed(() =>
  abrege.relationships.map(r => [
    entityLabelById.value.get(r.source_entity_id) ?? r.source_entity_id,
    r.relationship_type,
    entityLabelById.value.get(r.target_entity_id) ?? r.target_entity_id,
    r.description ?? '—',
    r.chunk_index === null ? 'Globale' : `Chunk ${r.chunk_index}`,
    r.model_name ?? '—',
  ]),
)

// ----- Onglet graphe -----
const graphContainer = ref<HTMLDivElement | null>(null)
let renderer: Sigma | null = null

const ENTITY_TYPE_COLORS: Record<string, string> = {
  PERSON: '#000091', // bleu France
  ORGANIZATION: '#c9191e', // rouge marianne
  LOCATION: '#00a95f', // vert
  DATE: '#b34000', // orange
  AMOUNT: '#6e445a', // violet
  EVENT: '#0078f3',
}
const DEFAULT_ENTITY_COLOR = '#3a3a3a'
const RELATIONSHIP_COLOR = '#929292'

function colorForType (type: string): string {
  return ENTITY_TYPE_COLORS[type.toUpperCase()] ?? DEFAULT_ENTITY_COLOR
}

const legendTypes = computed(() => {
  const types = new Set(abrege.entities.map(e => e.type.toUpperCase()))
  return [...types]
})

function destroyGraph () {
  if (renderer) {
    renderer.kill()
    renderer = null
  }
}

function buildGraph (entityList: EntityRow[], relationshipList: RelationshipRow[]) {
  const graph = new Graph({ multi: true })
  const n = entityList.length || 1

  entityList.forEach((entity, index) => {
    const angle = (2 * Math.PI * index) / n
    graph.addNode(entity.id, {
      x: Math.cos(angle) * 10,
      y: Math.sin(angle) * 10,
      size: 8,
      label: entity.text,
      color: colorForType(entity.type),
    })
  })

  relationshipList.forEach((rel) => {
    if (!graph.hasNode(rel.source_entity_id) || !graph.hasNode(rel.target_entity_id)) return
    try {
      graph.addEdge(rel.source_entity_id, rel.target_entity_id, {
        size: 2,
        label: rel.relationship_type,
        color: RELATIONSHIP_COLOR,
        type: 'arrow',
      })
    }
    catch {
      // duplicate edge between the same pair, ignore
    }
  })

  return graph
}

async function renderGraph () {
  await nextTick()
  if (!graphContainer.value) return
  destroyGraph()
  const graph = buildGraph(abrege.entities, abrege.relationships)
  renderer = new Sigma(graph, graphContainer.value, {
    renderEdgeLabels: true,
    defaultEdgeType: 'arrow',
  })
}

watch(activeTab, (tab) => {
  if (tab === 1) renderGraph()
})

watch(
  () => props.opened,
  async (opened) => {
    if (!opened) {
      destroyGraph()
      activeTab.value = 0
      return
    }
    await abrege.fetchEntitiesAndRelationships(props.taskId)
    if (activeTab.value === 1) renderGraph()
  },
)

onBeforeUnmount(() => {
  destroyGraph()
})

function close () {
  emit('close')
}
</script>

<template>
  <DsfrModal
    v-if="opened"
    :opened="opened"
    title="Entités & relations"
    size="xl"
    @close="close"
  >
    <div class="entities-modal-subtitle-row">
      <p class="fr-text--sm fr-text-mention--grey entities-modal-subtitle">
        Tâche {{ taskId }} — {{ abrege.entities.length }} entité(s), {{ abrege.relationships.length }} relation(s)
      </p>
      <ExtractionStatusBadge :status="entitiesStatus" label="Entités" />
      <ExtractionStatusBadge :status="relationshipsStatus" label="Relations globales" />
    </div>

    <div v-if="abrege.entitiesLoading" class="fr-mt-4w">
      <p class="fr-text--sm">
        Chargement…
      </p>
    </div>

    <CustomTabs v-else v-model="activeTab" :tabs-data="tabsData">
      <template #list>
        <div v-if="abrege.entities.length === 0" class="fr-alert fr-alert--info">
          <p>Aucune entité disponible pour cette tâche.</p>
        </div>
        <div v-else class="entities-list-columns">
          <div class="entities-list-column">
            <h4 class="fr-h6">
              Entités
            </h4>
            <DsfrTable
              title="Entités extraites"
              :headers="entityHeaders"
              :rows="entityRows"
            />
          </div>

          <div class="entities-list-column">
            <h4 class="fr-h6">
              Relations
            </h4>
            <DsfrTable
              v-if="relationshipRows.length > 0"
              title="Relations extraites"
              :headers="relationshipHeaders"
              :rows="relationshipRows"
            />
            <p v-else class="fr-text--sm fr-text-mention--grey">
              Aucune relation détectée.
            </p>
          </div>
        </div>
      </template>

      <template #graph>
        <div v-if="legendTypes.length > 0" class="entities-graph-legend">
          <span
            v-for="type in legendTypes"
            :key="type"
            class="entities-graph-legend__item"
          >
            <span
              class="entities-graph-legend__dot"
              :style="{ backgroundColor: colorForType(type) }"
            />
            {{ type }}
          </span>
          <span class="entities-graph-legend__item">
            <span class="entities-graph-legend__line" />
            Relation
          </span>
        </div>
        <div ref="graphContainer" class="entities-graph-container" />
      </template>
    </CustomTabs>
  </DsfrModal>
</template>

<style scoped>
.entities-modal-subtitle-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}
.entities-modal-subtitle {
  margin-top: 0;
  margin-bottom: 0;
}
.entities-list-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 1.5rem;
  align-items: start;
}
.entities-list-column :deep(table) {
  width: 100%;
}
@media (max-width: 991px) {
  .entities-list-columns {
    grid-template-columns: 1fr;
    gap: 1.5rem 0;
  }
}
.entities-graph-container {
  width: 100%;
  height: 480px;
  border: 1px solid var(--border-default-grey);
  background: #fff;
}
.entities-graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}
.entities-graph-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}
.entities-graph-legend__dot {
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
}
.entities-graph-legend__line {
  display: inline-block;
  width: 1rem;
  height: 2px;
  background: v-bind(RELATIONSHIP_COLOR);
}
</style>
