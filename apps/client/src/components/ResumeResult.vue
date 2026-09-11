<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed, onMounted, ref } from 'vue'
import TaskChunksModal from '@/components/TaskChunksModal.vue'
import TaskEntitiesModal from '@/components/TaskEntitiesModal.vue'
import TaskQAModal from '@/components/TaskQAModal.vue'
import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'

// The generated schema doesn't yet know about these — the API already returns them.
type TaskModel = components['schemas']['TaskModel'] & {
  qa_entities_status?: string | null
  relationships_status?: string | null
}
type SummaryModel = components['schemas']['SummaryModel']

const props = defineProps({
  resumeResult: {
    name: 'resumeResult',
    type: Object as () => TaskModel,
    required: true,
  },
})

const emit = defineEmits(['inFocus', 'reGenerate'])

const { addErrorMessage } = useToaster()

function hasSummary (output: TaskModel['output']): output is SummaryModel {
  return !!(output as SummaryModel)?.summary?.length
}

const summaryOutput = computed<SummaryModel | null>(() =>
  hasSummary(props.resumeResult.output) ? (props.resumeResult.output as SummaryModel) : null,
)

const qaModalOpened = ref(false)
const entitiesModalOpened = ref(false)
const chunksModalOpened = ref(false)

// Each side extraction is opt-in per task (see ParamsResume.vue) - only offer a button for
// what was actually requested, rather than one that always opens an empty modal.
const detailsButtons = computed(() => {
  const buttons = []
  if (props.resumeResult.parameters?.extract_qa) {
    buttons.push({ label: 'Questions / réponses', icon: 'ri-question-answer-line', onClick: () => { qaModalOpened.value = true } })
  }
  if (props.resumeResult.parameters?.extract_entities) {
    buttons.push({ label: 'Entités & relations', icon: 'ri-node-tree', onClick: () => { entitiesModalOpened.value = true } })
  }
  if (props.resumeResult.parameters?.extract_chunks) {
    buttons.push({ label: 'Chunks', icon: 'ri-file-list-3-line', onClick: () => { chunksModalOpened.value = true } })
  }
  return buttons
})

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

function speakMultipleTexts (texts: string[]) {
  if (!texts.length) {
    addErrorMessage({ title: 'Erreur', description: 'Aucun texte à lire.' })
    return
  }
  stopSpeech()
  textQueue.value = texts
  currentIndex.value = 0
  speakNextText()
}

function speakNextText () {
  if (speech.value && currentIndex.value < textQueue.value.length) {
    speech.value.text = textQueue.value[currentIndex.value]
    window.speechSynthesis.speak(speech.value)
    isSpeaking.value = true
  }
}

function stopSpeech () {
  window.speechSynthesis.cancel()
  isSpeaking.value = false
}

function reGenerate () {
  stopSpeech()
  emit('reGenerate')
}

function copyOnClipboard () {
  stopSpeech()
  if (hasSummary(props.resumeResult.output)) {
    navigator.clipboard.writeText(props.resumeResult.output.summary)
  } else {
    addErrorMessage({ title: 'Erreur', description: 'Le résumé est vide, rien à copier.' })
  }
}

function renderMarkdown (markdownText: string) {
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
          <div
            v-for="(tag, index) in tags"
            :key="index"
            class="tag"
          >
            {{ tag }}
          </div>
        </div>
        <span class="resume-content-words">
          {{ summaryOutput?.word_count || 0 }} mots générés
        </span>
      </div>

      <div
        class="resume-content-result"
        v-html="renderMarkdown(summaryOutput?.summary ?? '')"
      />

      <div
        v-if="detailsButtons.length > 0"
        class="details-wrapper"
      >
        <DsfrDropdown
          :main-button="{ label: 'Analyse du document', icon: 'ri-list-check-2', size: 'sm' }"
          :buttons="detailsButtons"
        />
      </div>

      <TaskQAModal
        v-if="resumeResult.parameters?.extract_qa"
        :opened="qaModalOpened"
        :task-id="resumeResult.id"
        :status="resumeResult.qa_entities_status"
        @close="qaModalOpened = false"
      />
      <TaskEntitiesModal
        v-if="resumeResult.parameters?.extract_entities"
        :opened="entitiesModalOpened"
        :task-id="resumeResult.id"
        :entities-status="resumeResult.qa_entities_status"
        :relationships-status="resumeResult.relationships_status"
        @close="entitiesModalOpened = false"
      />
      <TaskChunksModal
        v-if="resumeResult.parameters?.extract_chunks"
        :opened="chunksModalOpened"
        :task-id="resumeResult.id"
        :status="resumeResult.qa_entities_status"
        @close="chunksModalOpened = false"
      />
    </div>

    <div class="resume-container-buttons">
      <DsfrButton
        :icon="{ name: 'ri:volume-up-fill', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
        @click="speakMultipleTexts([summaryOutput?.summary ?? ''])"
      />
      <DsfrButton
        :icon="{ name: 'ri-refresh-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
        @click="reGenerate"
      />
      <DsfrButton
        :icon="{ name: 'ri-file-copy-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
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
