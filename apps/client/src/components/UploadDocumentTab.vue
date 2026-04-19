<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { storeToRefs } from 'pinia'

import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import { useParallelFileProcessing } from '@/composables/use-parallel-file-processing'
import FileParamsModal from './FileParamsModal.vue'
import ResumeResultModal from './ResumeResultModal.vue'

type TaskModel = components['schemas']['TaskModel']

const uploadAccept = ['.pdf', '.docx', '.pptx', '.txt', '.odt', '.odp', '.doc', '.mp3', '.wav', '.ogg', '.mp4', '.m4a', '.flac', '.aac', '.webm', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg', '.3gp', '.3g2', '.m4v', '.ts']
const generateButtonLabel = 'Générer'
const isLoading = ref(false)

const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerFilePicker () {
  fileInputRef.value?.click()
}

function handleFileAdd (event: Event) {
  const input = event.target as HTMLInputElement
  const newFiles = Array.from(input.files ?? [])
  if (!newFiles.length) return
  const existing = abregeStore.fileUpload
  const combined = [...existing, ...newFiles]
  abregeStore.fileUpload = combined
  abregeStore.fileParams = combined.map((_, i) => abregeStore.fileParams[i] ?? { customPrompt: null, language: null, size: null })
  parallelProcessing.syncFiles(combined.length)
  input.value = ''
}

const abregeStore = useAbregeStore()
const { addErrorMessage } = useToaster()

const parallelProcessing = useParallelFileProcessing()
const fileStates = parallelProcessing.fileStates
const mergeState = parallelProcessing.mergeState

const resumeResults = ref<{ filename: string, task: TaskModel }[]>([])
const showResultModal = ref(false)
const showResultModalIndex = ref(0)

const mergeEnabled = ref(false)
const showMergeParams = ref(false)
const mergeParams = ref({
  language: 'French',
  size: null as number | null,
  customPrompt: null as string | null,
})

async function onSubmit () {
  try {
    isLoading.value = true
    resumeResults.value = []

    const files = abregeStore.fileUpload
    const params = abregeStore.fileParams.map(fp => ({
      customPrompt: fp?.customPrompt ?? null,
      language: fp?.language ?? null,
      size: fp?.size ?? null,
    }))

    const results = await parallelProcessing.processAll(files, params, mergeEnabled.value)
    resumeResults.value = results

    if (mergeEnabled.value && mergeState.value.status === 'done' && mergeState.value.result) {
      resumeResults.value.push({ filename: 'Résumé global', task: mergeState.value.result })
    }
  }
  catch (error) {
    addErrorMessage({
      title: 'Erreur lors de la génération de résumé :',
      description: `${error}`,
    })
  }
  finally {
    isLoading.value = false
  }
}

function removeFile (index: number) {
  abregeStore.fileUpload = abregeStore.fileUpload.filter((_: File, i: number) => i !== index)
  abregeStore.fileParams = abregeStore.fileParams.filter((_: unknown, i: number) => i !== index)
  parallelProcessing.syncFiles(abregeStore.fileUpload.length)
}

const expandedFileIndex = ref<number | null>(null)
const showFormatsTooltip = ref(false)

function openFileParams (index: number) {
  expandedFileIndex.value = index
}

function closeFileParams () {
  expandedFileIndex.value = null
}

function newSearch () {
  resumeResults.value = []
  showResultModal.value = false
  parallelProcessing.syncFiles(abregeStore.fileUpload.length)
  abregeStore.reset()
}
</script>

<template>
  <form
    class="tab-container"
    @submit.prevent
  >
    <ResumeResultModal
      v-if="showResultModal && resumeResults.length"
      :results="resumeResults"
      :initial-index="showResultModalIndex"
      @close="showResultModal = false"
      @re-generate="newSearch"
    />
    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      :accept="uploadAccept.join(',')"
      multiple
      class="sr-only"
      @change="handleFileAdd"
    />

    <!-- File list with add button -->
    <div class="file-list-container">
      <ul
        v-if="abregeStore.fileUpload.length"
        class="file-list"
      >
      <li
        v-for="(file, index) in abregeStore.fileUpload"
        :key="index"
        class="file-list-item"
      >
        <div class="file-list-row">
          <span class="file-list-name">{{ file.name }}</span>
          <div class="file-list-actions">
            <DsfrButton
              size="sm"
              label="Paramètres"
              tertiary
              :disabled="isLoading"
              @click="openFileParams(index)"
            />
            <DsfrButton
              size="sm"
              label="Retirer"
              secondary
              :disabled="isLoading"
              @click="removeFile(index)"
            />
          </div>
        </div>
        <!-- Progress bar per file -->
        <ProgressBar
          v-if="fileStates[index]?.status === 'processing' || fileStates[index]?.status === 'uploading'"
          :visible="true"
          :progress="fileStates[index].percentage"
          :text="fileStates[index]?.status === 'uploading' ? 'Envoi...' : undefined"
        />
        <!-- Result button per file -->
        <div
          v-if="fileStates[index]?.status === 'done' || fileStates[index]?.status === 'error'"
          class="file-list-result"
        >
          <DsfrButton
            size="sm"
            :label="fileStates[index]?.status === 'error' ? 'Échec' : 'Voir le résumé'"
            :disabled="fileStates[index]?.status !== 'done'"
            secondary
            @click="() => {
              const resultIndex = resumeResults.findIndex(r => r.filename === file.name)
              if (resultIndex >= 0) {
                showResultModalIndex = resultIndex
                showResultModal = true
              }
            }"
          />
          <span
            v-if="fileStates[index]?.status === 'error'"
            class="file-error-msg"
          >{{ fileStates[index].error }}</span>
        </div>
      </li>

      <!-- Merge item -->
      <li
        v-if="abregeStore.fileUpload.length > 1"
        class="file-list-item file-list-item--merge"
      >
        <div class="file-list-row">
          <label class="file-list-name">
            <input
              v-model="mergeEnabled"
              type="checkbox"
              class="fr-mr-1w"
              :disabled="isLoading"
            />
            Résumé global
          </label>
          <div class="file-list-actions">
            <DsfrButton
              size="sm"
              label="Paramètres"
              tertiary
              :disabled="isLoading || !mergeEnabled"
              @click="showMergeParams = true"
            />
          </div>
        </div>
        <ProgressBar
          v-if="mergeState.status === 'processing' || mergeState.status === 'pending'"
          :visible="true"
          :progress="mergeState.percentage"
          :text="mergeState.status === 'pending' ? 'En attente...' : undefined"
        />
        <div
          v-if="mergeState.status === 'done' || mergeState.status === 'error'"
          class="file-list-result"
        >
          <DsfrButton
            size="sm"
            :label="mergeState.status === 'error' ? 'Échec' : 'Voir le résumé global'"
            :disabled="mergeState.status !== 'done'"
            secondary
            @click="() => {
              const idx = resumeResults.findIndex(r => r.filename === 'Résumé global')
              if (idx >= 0) { showResultModalIndex = idx; showResultModal = true }
            }"
          />
          <span
            v-if="mergeState.status === 'error'"
            class="file-error-msg"
          >{{ mergeState.error }}</span>
        </div>
      </li>
      </ul>

      <DsfrButton
        size="sm"
        label="Ajouter un fichier"
        icon="ri:add-line"
        secondary
        :disabled="isLoading"
        @click="triggerFilePicker"
      />
      <div class="file-hint-row">
        <button
          type="button"
          class="file-hint-btn"
          aria-label="Formats supportés"
          @mouseenter="showFormatsTooltip = true"
          @mouseleave="showFormatsTooltip = false"
          @focus="showFormatsTooltip = true"
          @blur="showFormatsTooltip = false"
        >
          <span class="fr-icon-information-line" aria-hidden="true" /> Formats supportés
        </button>
        <div
          v-if="showFormatsTooltip"
          class="file-formats-tooltip"
          role="tooltip"
        >
          <p class="tooltip-section-title">Documents</p>
          <p>PDF, DOC, DOCX, PPTX, ODT, ODP, TXT</p>
          <p class="tooltip-section-title">Vidéo</p>
          <p>MP4, AVI, MOV, MKV, WMV, FLV, WebM, MPEG, 3GP, M4V, TS</p>
          <p class="tooltip-section-title">Audio</p>
          <p>MP3, WAV, OGG, MP4, M4A, AAC, FLAC, WebM</p>
          <p class="tooltip-limit">200 Mo max par fichier</p>
        </div>
      </div>
    </div>
    <FileParamsModal
      v-if="expandedFileIndex !== null && abregeStore.fileParams[expandedFileIndex]"
      :item-label="abregeStore.fileUpload[expandedFileIndex].name"
      :params="abregeStore.fileParams[expandedFileIndex]"
      @close="closeFileParams"
    />
    <FileParamsModal
      v-if="showMergeParams"
      item-label="Résumé global"
      item-icon="ri:git-merge-line"
      :params="mergeParams"
      @close="showMergeParams = false"
    />
    <DsfrAlert
      v-if="isLoading"
      type="info"
      description="Les fichiers sont traités en parallèle. Le temps de traitement varie en fonction de la taille de chaque fichier."
      class="fr-mb-2w"
    />
    <DsfrButton
      size="lg"
      :label="generateButtonLabel"
      :disabled="isLoading || !abregeStore.fileUpload.length"
      @click="onSubmit"
    />
  </form>
</template>

<style scoped>
.file-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-list-item {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.75rem;
  background: var(--grey-975-75, #f6f6f6);
  border-radius: 4px;
  gap: 0.5rem;
}

.file-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.file-list-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.file-list-name {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.file-list-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-error-msg {
  font-size: 0.75rem;
  color: var(--text-default-error);
}

.file-list-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.file-waiting {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-mention-grey);
}

.file-hint {
  margin: 0;
}

.file-hint-row {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.file-hint-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.8rem;
  color: var(--text-action-high-blue-france, #000091);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.file-hint-btn:hover {
  text-decoration: underline;
}

.file-formats-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  white-space: nowrap;
  z-index: 100;
  font-size: 0.8rem;
  line-height: 1.5;
}

.file-formats-tooltip p {
  margin: 0;
}

.tooltip-section-title {
  font-weight: 700;
  margin-top: 0.4rem !important;
  color: var(--text-title-grey, #3a3a3a);
}

.tooltip-section-title:first-child {
  margin-top: 0 !important;
}

.tooltip-limit {
  margin-top: 0.5rem !important;
  color: var(--text-mention-grey, #777);
  font-style: italic;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.merge-section {
  margin: 1rem 0;
  padding: 1rem;
  background: var(--blue-france-975-75, #f5f5fe);
  border-left: 3px solid var(--blue-france-sun-113-625, #000091);
  border-radius: 4px;
}

.merge-params {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
