<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { storeToRefs } from 'pinia'

import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import { generateRandomUUID } from '@/utils/uniqueId'
import ParamsResume from './ParamsResume.vue'
import ResumeResult from './ResumeResult.vue'

type TaskModel = components['schemas']['TaskModel']

const uploadLabel = 'Ajouter un fichier'
const uploadHint = 'Taille maximale : 200MB par fichier. Formats supportés (texte, présentation, audio et vidéo) : PDF, DOCX, PPTX, ODT, ODP, TXT. Les images scannées ne fonctionnent pas.'
const uploadAccept = ['.pdf', '.docx', '.pptx', '.txt', '.odt', '.odp']
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

const userId = ref<string>(generateRandomUUID())
const resumeResult = ref<TaskModel>()
const percentage = computed(() => formattedPercentage.value)

function handleFileChange (files: FileList | File[]) {
  const file = Array.isArray(files) ? files[0] : files[0] || null
  if (file) {
    abregeStore.fileUpload = file
  }
}
async function onSubmit () {
  try {
    isLoading.value = true
    await abregeStore.sendDocumentAndPoll(userId.value)

    if (taskData.value && taskData.value.id) {
      resumeResult.value = await abregeStore.downloadContentSummary(taskData.value.id)
    }
    else if (storeError.value) {
      throw new Error(storeError.value)
    }
    else if (!taskData.value?.id) {
      throw new Error('Aucune tâche valide trouvée pour le résumé.')
    }

    await (new Promise(resolve => setTimeout(resolve, 1000)))

    if (status.value === 'completed') {
      abregeStore.reset()
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

function newSearch () {
  resumeResult.value = undefined
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
      v-if="resumeResult"
      :resume-result="resumeResult"
      @re-generate="newSearch"
    />
    <DsfrFileUpload
      :label="uploadLabel"
      :hint="uploadHint"
      :accept="uploadAccept"
      @change="handleFileChange"
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
      :disabled="isPolling || !abregeStore.fileUpload || isLoading"
      @click="onSubmit"
    />
  </form>
</template>
