<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed, onMounted, ref, watch } from 'vue'
import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'

type TaskModel = components['schemas']['TaskModel']
type SummaryModel = components['schemas']['SummaryModel']
type EntityModel = components['schemas']['EntityModel']
type RelationshipModel = components['schemas']['RelationshipModel']
type QAItem = components['schemas']['QAItem']

const ENTITY_TYPE_LABELS: Record<EntityModel['type'], string> = {
  PERSON: 'Personne',
  DATE: 'Date',
  ORGANIZATION: 'Organisation',
  LOCATION: 'Lieu',
  AMOUNT: 'Montant',
  EVENT: 'Événement',
  OTHER: 'Autre',
}

const ENTITY_TYPE_COLORS: Record<EntityModel['type'], string> = {
  PERSON: '#dbeafe',
  DATE: '#fef3c7',
  ORGANIZATION: '#dcfce7',
  LOCATION: '#fce7f3',
  AMOUNT: '#ede9fe',
  EVENT: '#ffedd5',
  OTHER: '#f3f4f6',
}

const props = defineProps({
  resumeResult: {
    name: 'resumeResult',
    type: Object as () => TaskModel,
    required: true,
  },
})

const emit = defineEmits(['inFocus', 'reGenerate'])
const { addErrorMessage } = useToaster()

function hasSummary(output: TaskModel['output']): output is SummaryModel {
  return !!(output as SummaryModel)?.summary?.length
}

const summaryOutput = computed<SummaryModel | null>(() =>
  hasSummary(props.resumeResult.output) ? (props.resumeResult.output as SummaryModel) : null,
)
const showDetails = ref(false)
const expandedContextId = ref<string | undefined>(undefined)
const expandedQaSourceId = ref<string | undefined>(undefined)
const activeTab = ref(0)
const searchQuery = ref('')
const entityTypeFilter = ref<EntityModel['type'] | null>(null)
const relationTypeFilter = ref<string | null>(null)

const PAGE_SIZE = 6
const entityPage = ref(1)
const relationPage = ref(1)
const qaPage = ref(1)

const entities = computed<EntityModel[]>(() => summaryOutput.value?.entities ?? [])
const relationships = computed<RelationshipModel[]>(() => summaryOutput.value?.relationships ?? [])
const qaItems = computed<QAItem[]>(() => summaryOutput.value?.qa_items ?? [])
const hasDetails = computed(() => entities.value.length > 0 || relationships.value.length > 0 || qaItems.value.length > 0)

const q = computed(() => searchQuery.value.toLowerCase().trim())

const filteredEntities = computed(() => {
  return entities.value.filter(e => {
    const matchType = !entityTypeFilter.value || e.type === entityTypeFilter.value
    const matchQuery = !q.value ||
      e.text.toLowerCase().includes(q.value) ||
      e.type.toLowerCase().includes(q.value) ||
      ENTITY_TYPE_LABELS[e.type]?.toLowerCase().includes(q.value) ||
      e.contexts.some(c => c.toLowerCase().includes(q.value))
    return matchType && matchQuery
  })
})

const filteredRelations = computed(() => {
  return relationships.value.filter(r => {
    const matchType = !relationTypeFilter.value || r.relationship_type === relationTypeFilter.value
    const matchQuery = !q.value ||
      r.relationship_type.toLowerCase().includes(q.value) ||
      r.description.toLowerCase().includes(q.value) ||
      entityName(r.source_index).toLowerCase().includes(q.value) ||
      entityName(r.target_index).toLowerCase().includes(q.value)
    return matchType && matchQuery
  })
})

const filteredQaItems = computed(() => {
  return qaItems.value.filter(qa => {
    return !q.value ||
      qa.question.toLowerCase().includes(q.value) ||
      qa.answer.toLowerCase().includes(q.value) ||
      qa.source_text.toLowerCase().includes(q.value)
  })
})

const availableEntityTypes = computed(() => {
  const types = [...new Set(entities.value.map(e => e.type))]
  return types.sort()
})

const availableRelationTypes = computed(() => {
  const types = [...new Set(relationships.value.map(r => r.relationship_type))]
  return types.sort()
})

watch([searchQuery, entityTypeFilter, relationTypeFilter], () => {
  entityPage.value = 1
  relationPage.value = 1
  qaPage.value = 1
})

const tabTitles = computed(() => [
  {
    tabId: 'tab-entities',
    panelId: 'panel-entities',
    title: 'Entités' + (filteredEntities.value.length !== entities.value.length
      ? ' (' + filteredEntities.value.length + '/' + entities.value.length + ')'
      : entities.value.length ? ' (' + entities.value.length + ')' : ''),
    icon: 'ri-user-line',
  },
  {
    tabId: 'tab-relations',
    panelId: 'panel-relations',
    title: 'Relations' + (filteredRelations.value.length !== relationships.value.length
      ? ' (' + filteredRelations.value.length + '/' + relationships.value.length + ')'
      : relationships.value.length ? ' (' + relationships.value.length + ')' : ''),
    icon: 'ri-link-m',
  },
  {
    tabId: 'tab-qa',
    panelId: 'panel-qa',
    title: 'Q&A' + (filteredQaItems.value.length !== qaItems.value.length
      ? ' (' + filteredQaItems.value.length + '/' + qaItems.value.length + ')'
      : qaItems.value.length ? ' (' + qaItems.value.length + ')' : ''),
    icon: 'ri-question-answer-line',
  },
])

const entityPageCount = computed(() => Math.ceil(filteredEntities.value.length / PAGE_SIZE))
const relationPageCount = computed(() => Math.ceil(filteredRelations.value.length / PAGE_SIZE))
const qaPageCount = computed(() => Math.ceil(filteredQaItems.value.length / PAGE_SIZE))

const pagedEntities = computed(() => {
  const start = (entityPage.value - 1) * PAGE_SIZE
  return filteredEntities.value.slice(start, start + PAGE_SIZE)
})

const pagedRelations = computed(() => {
  const start = (relationPage.value - 1) * PAGE_SIZE
  return filteredRelations.value.slice(start, start + PAGE_SIZE)
})

const pagedQaItems = computed(() => {
  const start = (qaPage.value - 1) * PAGE_SIZE
  return filteredQaItems.value.slice(start, start + PAGE_SIZE)
})

function entityPageOffset(i: number): number {
  return (entityPage.value - 1) * PAGE_SIZE + i
}

function qaPageOffset(i: number): number {
  return (qaPage.value - 1) * PAGE_SIZE + i
}

function highlight(text: string): string {
  if (!q.value) return text
  const escaped = q.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp('(' + escaped + ')', 'gi'), '<mark>$1</mark>')
}

const tags = ref<string[]>([
  'Synthèse',
  props.resumeResult.parameters?.language === 'French'
    ? 'Français'
    : props.resumeResult.parameters?.language === 'English'
      ? 'Anglais'
      : props.resumeResult.parameters?.language || '',
])

const speech = ref<SpeechSynthesisUtterance | null>(null)
const isSpeaking = ref<boolean>(false)
const textQueue = ref<string[]>([])
const currentIndex = ref<number>(0)

function entityLabel(type: EntityModel['type']) {
  return ENTITY_TYPE_LABELS[type] ?? type
}

function entityColor(type: EntityModel['type']) {
  return ENTITY_TYPE_COLORS[type] ?? '#f3f4f6'
}

function entityName(index: number): string {
  return entities.value[index]?.text ?? ('#' + index)
}

function countLabel(): string {
  const e = entities.value.length
  const r = relationships.value.length
  const qa = qaItems.value.length
  let s = e + ' entité' + (e > 1 ? 's' : '')
  if (r > 0) s += ' · ' + r + ' relation' + (r > 1 ? 's' : '')
  if (qa > 0) s += ' · ' + qa + ' Q&A'
  return s
}

function speakMultipleTexts(texts: string[]) {
  if (!texts.length) {
    addErrorMessage({ title: 'Erreur', description: 'Aucun texte à lire.' })
    return
  }
  stopSpeech()
  textQueue.value = texts
  currentIndex.value = 0
  speakNextText()
}

function speakNextText() {
  if (speech.value && currentIndex.value < textQueue.value.length) {
    speech.value.text = textQueue.value[currentIndex.value]
    window.speechSynthesis.speak(speech.value)
    isSpeaking.value = true
  }
}

function stopSpeech() {
  window.speechSynthesis.cancel()
  isSpeaking.value = false
}

function reGenerate() {
  stopSpeech()
  emit('reGenerate')
}

function copyOnClipboard() {
  stopSpeech()
  if (hasSummary(props.resumeResult.output)) {
    navigator.clipboard.writeText(props.resumeResult.output.summary)
  } else {
    addErrorMessage({ title: 'Erreur', description: 'Le résumé est vide, rien à copier.' })
  }
}

function renderMarkdown(markdownText: string) {
  const html = marked.parse(markdownText) as string
  return DOMPurify.sanitize(html)
}

onMounted(() => {
  const abregeStore = useAbregeStore()
  const { paramsValue } = abregeStore
  const speechLanguage = paramsValue.selectOptionSelected === 'French' ? 'fr-FR' : 'en-EN'
  speech.value = new SpeechSynthesisUtterance()
  speech.value.lang = speechLanguage
  speech.value.rate = 0.8
  speech.value.pitch = 1
  speech.value.onend = () => {
    currentIndex.value++
    if (currentIndex.value < textQueue.value.length) {
      speakNextText()
    } else {
      isSpeaking.value = false
    }
  }
})
</script>

<template>
  <div class="resume-container">
    <div class="resume-content">

      <div class="resume-content-header">
        <div class="resume-content-tag">
          <div v-for="(tag, index) in tags" :key="index" class="tag">{{ tag }}</div>
        </div>
        <span class="resume-content-words">
          {{ summaryOutput?.word_count || 0 }} mots générés
        </span>
      </div>

      <div class="resume-content-result" v-html="renderMarkdown(summaryOutput?.summary ?? '')"></div>

      <div v-if="hasDetails" class="details-wrapper">
        <button class="details-toggle" @click="showDetails = !showDetails">
          {{ showDetails ? '▲ Masquer les détails' : '▼ Analyse du document' }}
          <span v-if="!showDetails" class="details-count">{{ countLabel() }}</span>
        </button>

        <div v-if="showDetails" class="details-body">
          <div class="search-bar">
            <span class="fr-icon-search-line search-icon" aria-hidden="true"></span>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Rechercher dans les entités et relations…"
              aria-label="Rechercher dans les entités et relations"
            />
            <button
              v-if="searchQuery"
              class="search-clear"
              aria-label="Effacer la recherche"
              @click="searchQuery = ''"
            >✕</button>
          </div>
          <DsfrTabs v-model="activeTab" :tab-titles="tabTitles" tab-list-name="analyse">
          <DsfrTabContent panel-id="panel-entities" tab-id="tab-entities">
            <div v-if="entities.length > 0" class="tab-content">
              <div v-if="availableEntityTypes.length > 1" class="type-filters">
                <button
                  class="type-chip"
                  :class="{ active: entityTypeFilter === null }"
                  @click="entityTypeFilter = null"
                >Tous</button>
                <button
                  v-for="type in availableEntityTypes"
                  :key="type"
                  class="type-chip"
                  :class="{ active: entityTypeFilter === type }"
                  :style="entityTypeFilter === type ? { backgroundColor: entityColor(type), borderColor: entityColor(type) } : {}"
                  @click="entityTypeFilter = entityTypeFilter === type ? null : type"
                >{{ entityLabel(type) }}</button>
              </div>
              <div class="cards-list">
                <div
                  v-for="(entity, i) in pagedEntities"
                  :key="entityPageOffset(i)"
                  class="entity-card"
                  :style="{ borderLeftColor: entityColor(entity.type) }"
                >
                  <div class="entity-card-header">
                    <DsfrTag
                      :label="entityLabel(entity.type)"
                      small
                      :style="{ backgroundColor: entityColor(entity.type), color: '#333', border: 'none' }"
                    />
                    <span class="entity-text" v-html="highlight(entity.text)"></span>
                    <span v-if="entity.pages.length > 0" class="entity-pages">p. {{ entity.pages.join(', ') }}</span>
                  </div>
                  <DsfrAccordionsGroup v-if="entity.contexts.length > 0" v-model="expandedContextId">
                    <DsfrAccordion
                      :id="'ctx-' + entityPageOffset(i)"
                      :title="entity.contexts.length + ' contexte' + (entity.contexts.length > 1 ? 's' : '')"
                      :expanded-id="expandedContextId"
                      @expand="expandedContextId = $event"
                    >
                      <ul class="entity-contexts-list">
                        <li v-for="(ctx, ci) in entity.contexts" :key="ci" v-html="highlight(ctx)"></li>
                      </ul>
                    </DsfrAccordion>
                  </DsfrAccordionsGroup>
                </div>
              </div>
              <div v-if="entityPageCount > 1" class="pagination">
                <span class="pagination-info">{{ entityPage }} / {{ entityPageCount }}</span>
                <DsfrButton
                  label="Précédent"
                  :disabled="entityPage === 1"
                  size="sm"
                  secondary
                  icon="ri-arrow-left-line"
                  icon-only
                  @click="entityPage--"
                />
                <DsfrButton
                  label="Suivant"
                  :disabled="entityPage === entityPageCount"
                  size="sm"
                  secondary
                  icon="ri-arrow-right-line"
                  icon-only
                  @click="entityPage++"
                />
              </div>
            </div>
            <p v-else class="fr-text--sm empty-state">
              <template v-if="searchQuery">Aucune entité ne correspond à « {{ searchQuery }} ».</template>
              <template v-else>Aucune entité extraite.</template>
            </p>
          </DsfrTabContent>

          <DsfrTabContent panel-id="panel-relations" tab-id="tab-relations">
            <div v-if="relationships.length > 0" class="tab-content">
              <div v-if="availableRelationTypes.length > 1" class="type-filters">
                <button
                  class="type-chip"
                  :class="{ active: relationTypeFilter === null }"
                  @click="relationTypeFilter = null"
                >Tous</button>
                <button
                  v-for="type in availableRelationTypes"
                  :key="type"
                  class="type-chip"
                  :class="{ active: relationTypeFilter === type }"
                  @click="relationTypeFilter = relationTypeFilter === type ? null : type"
                >{{ type }}</button>
              </div>
              <div class="cards-list">
                <div v-for="(rel, i) in pagedRelations" :key="i" class="relation-card">
                  <div class="relation-header">
                    <DsfrTag :label="entityName(rel.source_index)" small class="relation-entity-tag" />
                    <span class="relation-arrow">→</span>
                    <DsfrTag :label="rel.relationship_type" small class="relation-type-tag" />
                    <span class="relation-arrow">→</span>
                    <DsfrTag :label="entityName(rel.target_index)" small class="relation-entity-tag" />
                  </div>
                  <p class="relation-desc" v-html="highlight(rel.description)"></p>
                </div>
              </div>
              <div v-if="relationPageCount > 1" class="pagination">
                <span class="pagination-info">{{ relationPage }} / {{ relationPageCount }}</span>
                <DsfrButton
                  label="Précédent"
                  :disabled="relationPage === 1"
                  size="sm"
                  secondary
                  icon="ri-arrow-left-line"
                  icon-only
                  @click="relationPage--"
                />
                <DsfrButton
                  label="Suivant"
                  :disabled="relationPage === relationPageCount"
                  size="sm"
                  secondary
                  icon="ri-arrow-right-line"
                  icon-only
                  @click="relationPage++"
                />
              </div>
            </div>
            <p v-else class="fr-text--sm empty-state">
              <template v-if="searchQuery">Aucune relation ne correspond à « {{ searchQuery }} ».</template>
              <template v-else>Aucune relation détectée.</template>
            </p>
          </DsfrTabContent>

          <DsfrTabContent panel-id="panel-qa" tab-id="tab-qa">
            <div v-if="qaItems.length > 0" class="tab-content">
              <div class="cards-list">
                <div v-for="(qa, i) in pagedQaItems" :key="qaPageOffset(i)" class="qa-card">
                  <div class="qa-card-header">
                    <span class="qa-question" v-html="highlight(qa.question)"></span>
                    <span v-if="qa.page" class="entity-pages">p. {{ qa.page }}</span>
                  </div>
                  <p class="qa-answer" v-html="highlight(qa.answer)"></p>
                  <DsfrAccordionsGroup v-model="expandedQaSourceId">
                    <DsfrAccordion
                      :id="'qa-src-' + qaPageOffset(i)"
                      title="Texte source"
                      :expanded-id="expandedQaSourceId"
                      @expand="expandedQaSourceId = $event"
                    >
                      <p class="qa-source-text" v-html="highlight(qa.source_text)"></p>
                    </DsfrAccordion>
                  </DsfrAccordionsGroup>
                </div>
              </div>
              <div v-if="qaPageCount > 1" class="pagination">
                <span class="pagination-info">{{ qaPage }} / {{ qaPageCount }}</span>
                <DsfrButton
                  label="Précédent"
                  :disabled="qaPage === 1"
                  size="sm"
                  secondary
                  icon="ri-arrow-left-line"
                  icon-only
                  @click="qaPage--"
                />
                <DsfrButton
                  label="Suivant"
                  :disabled="qaPage === qaPageCount"
                  size="sm"
                  secondary
                  icon="ri-arrow-right-line"
                  icon-only
                  @click="qaPage++"
                />
              </div>
            </div>
            <p v-else class="fr-text--sm empty-state">
              <template v-if="searchQuery">Aucune question/réponse ne correspond à « {{ searchQuery }} ».</template>
              <template v-else>Aucune question/réponse générée.</template>
            </p>
          </DsfrTabContent>
        </DsfrTabs>
        </div>
      </div>

    </div>

    <div class="resume-container-buttons">
      <DsfrButton
        :icon="{ name: 'ri:volume-up-fill', fill: 'var(--border-plain-blue-france))' }"
        icon-only tertiary no-outline
        @click="speakMultipleTexts([summaryOutput?.summary ?? ''])"
      />
      <DsfrButton
        :icon="{ name: 'ri-refresh-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only tertiary no-outline
        @click="reGenerate"
      />
      <DsfrButton
        :icon="{ name: 'ri-file-copy-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only tertiary no-outline
        @click="copyOnClipboard"
      />
    </div>
  </div>
</template>

<style scoped>
.resume-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.resume-content {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  border: 1px solid var(--border-default-grey);
  gap: 1rem;
}
.resume-content-result {
  display: flex;
  flex-direction: column;
}
.resume-content-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.resume-content-tag {
  display: flex;
  gap: 0.5rem;
}
.resume-content-words {
  font-size: 0.75rem;
  color: var(--text-mention-grey);
}
.resume-container-buttons {
  display: flex;
  gap: 0.5rem;
}
.tag {
  background-color: var(--background-default-grey);
  border: 1px solid var(--border-default-grey);
  border-radius: 12px;
  padding: 2px 8px;
}
.details-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.details-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
/* Barre de recherche */
.search-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--background-default-grey);
  border: 1px solid var(--border-default-grey);
  border-radius: 4px;
  padding: 0.375rem 0.75rem;
}
.search-icon {
  color: var(--text-mention-grey);
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.875rem;
  color: var(--text-default-grey);
  min-width: 0;
}
.search-input::placeholder {
  color: var(--text-mention-grey);
}
.search-clear {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-mention-grey);
  font-size: 0.75rem;
  padding: 0 0.25rem;
  line-height: 1;
}
.search-clear:hover {
  color: var(--text-default-grey);
}
/* Surbrillance des résultats */
:deep(mark) {
  background-color: #fef08a;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}
/* Chips de filtre par type */
.type-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}
.type-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.1875rem 0.625rem;
  border: 1px solid var(--border-default-grey);
  border-radius: 99px;
  background: transparent;
  font-size: 0.75rem;
  cursor: pointer;
  color: var(--text-default-grey);
  transition: background 0.1s, border-color 0.1s;
  line-height: 1.4;
}
.type-chip:hover {
  background: var(--background-alt-grey);
}
.type-chip.active {
  background: var(--background-action-high-blue-france, #000091);
  border-color: var(--background-action-high-blue-france, #000091);
  color: #fff;
}
.details-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-action-high-blue-france, #000091);
  padding: 0;
  text-align: left;
}
.details-count {
  font-size: 0.75rem;
  color: var(--text-mention-grey);
}
/* Tabs content padding */
:deep(.fr-tabs__panel) {
  padding: 1rem 0 0;
}
.empty-state {
  color: var(--text-mention-grey);
  font-style: italic;
}
/* Liste + pagination */
.tab-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.25rem;
}
.pagination-info {
  font-size: 0.75rem;
  color: var(--text-mention-grey);
  margin-right: 0.25rem;
}
/* Cards entités */
.entity-card {
  display: flex;
  flex-direction: column;
  background: var(--background-default-grey);
  border-left: 3px solid;
  padding: 0.625rem 0.875rem;
  gap: 0.25rem;
}
.entity-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.entity-text {
  font-size: 0.875rem;
  font-weight: 600;
  flex: 1;
}
.entity-pages {
  font-size: 0.6875rem;
  color: var(--text-mention-grey);
  margin-left: auto;
}
.entity-contexts-list {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
  font-size: 0.75rem;
  color: var(--text-mention-grey);
}
.entity-contexts-list li {
  margin-bottom: 0.25rem;
}
.entity-card :deep(.fr-accordion__btn) {
  font-size: 0.75rem;
  padding: 0.25rem 0;
  min-height: unset;
  background: none;
}
.entity-card :deep(.fr-accordion) {
  border-top: none;
}
/* Cards relations */
.relation-card {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 0.625rem 0.875rem;
  background: var(--background-alt-grey);
  border-left: 3px solid var(--border-plain-blue-france);
}
.relation-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.375rem;
}
.relation-arrow {
  color: var(--text-mention-grey);
  font-size: 0.875rem;
}
.relation-entity-tag {
  background-color: var(--background-alt-blue-france) !important;
}
.relation-type-tag {
  background-color: var(--background-contrast-blue-france) !important;
  font-weight: 700;
  text-transform: uppercase;
}
.relation-desc {
  margin: 0;
  color: var(--text-mention-grey);
  font-size: 0.75rem;
  font-style: italic;
}
/* Cards Q&A */
.qa-card {
  display: flex;
  flex-direction: column;
  background: var(--background-default-grey);
  border-left: 3px solid var(--border-plain-blue-france);
  padding: 0.625rem 0.875rem;
  gap: 0.25rem;
}
.qa-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.qa-question {
  font-size: 0.875rem;
  font-weight: 600;
  flex: 1;
}
.qa-answer {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--text-default-grey);
}
.qa-source-text {
  margin: 0.25rem 0 0;
  font-size: 0.75rem;
  color: var(--text-mention-grey);
  font-style: italic;
}
.qa-card :deep(.fr-accordion__btn) {
  font-size: 0.75rem;
  padding: 0.25rem 0;
  min-height: unset;
  background: none;
}
.qa-card :deep(.fr-accordion) {
  border-top: none;
}
</style>
