<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { storeToRefs } from 'pinia'

import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import FileParamsModal from './FileParamsModal.vue'
import ParamsResume from './ParamsResume.vue'
import ResumeResult from './ResumeResult.vue'

type TaskModel = components['schemas']['TaskModel']

const uploadLabel = 'Ajouter des fichiers'
const uploadHint = 'Taille maximale : 200MB par fichier. Formats supportés (texte, présentation, audio et vidéo) : PDF, DOC, DOCX, PPTX, ODT, ODP, TXT. Les images scannées ne fonctionnent pas.'
const uploadAccept = ['.pdf', '.docx', '.pptx', '.txt', '.odt', '.odp', '.doc']
const generateButtonLabel = 'Générer'
const isLoading = ref(false)

const abregeStore = useAbregeStore()
const { addErrorMessage } = useToaster()

const {
  taskData,
  isPolling,
  formattedPercentage,
  status,
  error: storeError,
} = storeToRefs(abregeStore)

const resumeResults = ref<TaskModel[]>([])
const percentage = computed(() => formattedPercentage.value)

function handleFileChange (files: FileList | File[]) {
  const fileArray = Array.isArray(files) ? files : Array.from(files)
  if (fileArray.length) {
    abregeStore.fileUpload = fileArray
    abregeStore.fileParams = fileArray.map(() => ({ customPrompt: null, language: null, size: null }))
  }
}
async function onSubmit () {
  try {
    isLoading.value = true
    for (const [i, file] of abregeStore.fileUpload.entries()) {
      const fp = abregeStore.fileParams[i]
      await abregeStore.sendDocumentAndPoll(file, fp?.customPrompt, fp?.language, fp?.size)

      if (taskData.value?.id) {
        const result = await abregeStore.downloadContentSummary(taskData.value.id)
        resumeResults.value.push(result)
      }
      else if (storeError.value) {
        addErrorMessage({
          title: 'Erreur lors de la génération de résumé :',
          description: storeError.value,
        })
      }
    }

    abregeStore.reset()
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
  abregeStore.fileUpload = abregeStore.fileUpload.filter((_, i) => i !== index)
  abregeStore.fileParams = abregeStore.fileParams.filter((_, i) => i !== index)
}

const expandedFileIndex = ref<number | null>(null)

function openFileParams (index: number) {
  expandedFileIndex.value = index
}

function closeFileParams () {
  expandedFileIndex.value = null
}

function newSearch () {
  resumeResults.value = []
  abregeStore.reset()
}

if (storeError.value) {
  addErrorMessage({
    title: 'Erreur : ',
    description: storeError.value,
  })
}
</script>

<template>
  <form
    class="tab-container"
    @submit.prevent
  >
    <ResumeResult
      v-for="(result, index) in resumeResults"
      :key="index"
      :resume-result="result"
      @re-generate="newSearch"
    />
    <DsfrFileUpload
      :label="uploadLabel"
      :hint="uploadHint"
      :accept="uploadAccept"
      multiple
      @change="handleFileChange"
    />
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
              :disabled="isPolling || isLoading"
              @click="openFileParams(index)"
            />
            <DsfrButton
              size="sm"
              label="Retirer"
              secondary
              :disabled="isPolling || isLoading"
              @click="removeFile(index)"
            />
          </div>
        </div>
      </li>
    </ul>
    <FileParamsModal
      v-if="expandedFileIndex !== null && abregeStore.fileParams[expandedFileIndex]"
      :file-name="abregeStore.fileUpload[expandedFileIndex].name"
      :params="abregeStore.fileParams[expandedFileIndex]"
      @close="closeFileParams"
    />
    <ParamsResume />
    <div
      v-if="isPolling"
      class="is-generating-container"
    >
      <ProgressBar
        :visible="isPolling"
        :progress="percentage"
      />
      <DsfrAlert
        type="info"
        description="Le temps de traitement varie en fonction de la taille de la source, dans certains cas cela peut prendre quelques minutes."
      />
    </div>
    <DsfrButton
      size="lg"
      :label="generateButtonLabel"
      :disabled="isPolling || !abregeStore.fileUpload.length || isLoading"
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
</style>
