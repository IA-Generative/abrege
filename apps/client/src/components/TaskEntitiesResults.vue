<script setup lang="ts">
import type { EntityRow, RelationshipRow } from '@/stores/abrege'
import Graph from 'graphology'
import Sigma from 'sigma'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAbregeStore } from '@/stores/abrege'
import CustomTabs from './CustomTabs.vue'

const props = defineProps<{
  taskId: string
  entitiesStatus?: string | null
  relationshipsStatus?: string | null
  expanded?: boolean
  initialTab?: number
}>()

const emit = defineEmits<{ (e: 'tabChange', tab: number): void }>()

const abrege = useAbregeStore()

const activeTab = ref(props.initialTab ?? 0)
const tabsData = [
  { label: 'Liste', slot: 'list' },
  { label: 'Graphe', slot: 'graph' },
]

const searchQuery = ref('')

// ----- Onglet liste -----
const entityHeaders = ['Type', 'Texte', 'Pages', 'Chunk', 'Modèle']

const entityLabelById = computed(() => {
  const map = new Map<string, string>()
  for (const e of abrege.entities) { map.set(e.id, e.text) }
  return map
})

const filteredEntities = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) { return abrege.entities }
  return abrege.entities.filter(e =>
    e.type.toLowerCase().includes(q)
    || e.text.toLowerCase().includes(q)
    || (e.contexts ?? []).some(c => c.toLowerCase().includes(q)),
  )
})

const filteredRelationships = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) { return abrege.relationships }
  return abrege.relationships.filter(r =>
    r.relationship_type.toLowerCase().includes(q)
    || (r.description ?? '').toLowerCase().includes(q)
    || (entityLabelById.value.get(r.source_entity_id) ?? '').toLowerCase().includes(q)
    || (entityLabelById.value.get(r.target_entity_id) ?? '').toLowerCase().includes(q),
  )
})

const entityRows = computed(() =>
  filteredEntities.value.map(e => [e.type, e.text, (e.pages ?? []).join(', ') || '—', String(e.chunk_index), e.model_name ?? '—']),
)

const relationshipHeaders = ['Source', 'Relation', 'Cible', 'Description', 'Portée', 'Modèle']
const relationshipRows = computed(() =>
  filteredRelationships.value.map(r => [
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
  const types = new Set(filteredEntities.value.map(e => e.type.toUpperCase()))
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
    if (!graph.hasNode(rel.source_entity_id) || !graph.hasNode(rel.target_entity_id)) { return }
    try {
      graph.addEdge(rel.source_entity_id, rel.target_entity_id, {
        size: 2,
        label: rel.relationship_type,
        color: RELATIONSHIP_COLOR,
        type: 'arrow',
      })
    } catch {
      // duplicate edge between the same pair, ignore
    }
  })

  return graph
}

async function renderGraph () {
  await nextTick()
  if (!graphContainer.value) { return }
  destroyGraph()
  const graph = buildGraph(filteredEntities.value, filteredRelationships.value)
  // Relation labels overlap as soon as there are a few edges: only show those of the hovered
  // edge, or of the edges touching the hovered node.
  let hoveredEdge: string | null = null
  let hoveredNode: string | null = null
  renderer = new Sigma(graph, graphContainer.value, {
    renderEdgeLabels: true,
    enableEdgeEvents: true,
    defaultEdgeType: 'arrow',
    edgeReducer: (edge, data) => {
      const highlighted = hoveredEdge === edge || (hoveredNode !== null && graph.hasExtremity(edge, hoveredNode))
      return highlighted
        ? { ...data, forceLabel: true, color: '#000091', size: 3 }
        : { ...data, label: '' }
    },
  })
  const hover = (edge: string | null, node: string | null) => {
    hoveredEdge = edge
    hoveredNode = node
    renderer?.refresh()
  }
  renderer.on('enterEdge', ({ edge }) => hover(edge, null))
  renderer.on('leaveEdge', () => hover(null, null))
  renderer.on('enterNode', ({ node }) => hover(null, node))
  renderer.on('leaveNode', () => hover(null, null))
}

watch(activeTab, (tab) => {
  emit('tabChange', tab)
  if (tab === 1) { renderGraph() }
})

watch(searchQuery, () => {
  if (activeTab.value === 1) { renderGraph() }
})

async function loadEntities () {
  await abrege.fetchEntitiesAndRelationships(props.taskId)
  if (activeTab.value === 1) { renderGraph() }
}

onMounted(loadEntities)

// Entities and the global relationships complete one after the other while the task is polled.
watch(() => [props.entitiesStatus, props.relationshipsStatus], ([entitiesStatus, relationshipsStatus], [previousEntities, previousRelationships]) => {
  const justCompleted = (entitiesStatus === 'completed' && previousEntities !== 'completed')
    || (relationshipsStatus === 'completed' && previousRelationships !== 'completed')
  if (justCompleted) { loadEntities() }
})

onBeforeUnmount(() => {
  destroyGraph()
})
</script>

<template>
  <div class="entities-results">
    <div class="entities-modal-subtitle-row">
      <p class="fr-text--sm fr-text-mention--grey entities-modal-subtitle">
        {{ abrege.entities.length }} entité(s), {{ abrege.relationships.length }} relation(s)
      </p>
      <ExtractionStatusBadge
        :status="entitiesStatus"
        label="Entités"
      />
      <ExtractionStatusBadge
        :status="relationshipsStatus"
        label="Relations globales"
      />
    </div>

    <div
      v-if="abrege.entitiesLoading"
      class="fr-mt-4w"
    >
      <p class="fr-text--sm">
        Chargement…
      </p>
    </div>

    <template v-else>
      <DsfrSearchBar
        v-if="abrege.entities.length > 0"
        v-model="searchQuery"
        label="Rechercher dans les entités et relations"
        placeholder="Rechercher un type, un texte, une relation…"
        class="fr-mt-2w"
      />

      <CustomTabs
        v-model="activeTab"
        :tabs-data="tabsData"
      >
        <template #list>
          <div
            v-if="abrege.entities.length === 0"
            class="fr-alert fr-alert--info"
          >
            <p>Aucune entité disponible pour cette tâche.</p>
          </div>
          <p
            v-else-if="entityRows.length === 0"
            class="fr-text--sm fr-text-mention--grey"
          >
            Aucun résultat pour « {{ searchQuery }} ».
          </p>
          <div
            v-else
            class="entities-list-columns"
          >
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
              <p
                v-else
                class="fr-text--sm fr-text-mention--grey"
              >
                Aucune relation détectée.
              </p>
            </div>
          </div>
        </template>

        <template #graph>
          <p
            v-if="legendTypes.length > 0"
            class="fr-hint-text entities-graph-hint"
          >
            Survolez un nœud ou une relation pour voir le détail des liens.
          </p>
          <div
            v-if="legendTypes.length > 0"
            class="entities-graph-legend"
          >
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
          <div
            v-else-if="abrege.entities.length === 0"
            class="fr-alert fr-alert--info"
          >
            <p>Aucune entité à afficher : l'extraction n'a rien trouvé ou n'a pas pu être enregistrée. Consultez le statut ci-dessus.</p>
          </div>
          <p
            v-else-if="searchQuery"
            class="fr-text--sm fr-text-mention--grey"
          >
            Aucun résultat pour « {{ searchQuery }} ».
          </p>
          <div
            v-show="abrege.entities.length > 0"
            ref="graphContainer"
            class="entities-graph-container"
            :class="{ 'entities-graph-container--expanded': expanded }"
          />
        </template>
      </CustomTabs>
    </template>
  </div>
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
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
.entities-list-column {
  min-width: 0;
}
.entities-list-column :deep(.fr-table),
.entities-list-column :deep(.fr-table__wrapper),
.entities-list-column :deep(.fr-table__container),
.entities-list-column :deep(.fr-table__content) {
  max-width: 100%;
}
.entities-list-column :deep(.fr-table__wrapper) {
  overflow-x: auto;
}
.entities-list-column :deep(table) {
  width: 100%;
}
.entities-list-column :deep(td) {
  overflow-wrap: anywhere;
}
.entities-graph-container {
  width: 100%;
  height: 480px;
  border: 1px solid var(--border-default-grey);
  background: #fff;
}
.entities-graph-container--expanded {
  height: max(480px, calc(100vh - 420px));
}
.entities-graph-hint {
  margin: 0 0 0.5rem;
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
