<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { useForm } from 'vee-validate'
import { watch } from 'vue'
import * as yup from 'yup'
import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import ParamsResume from './ParamsResume.vue'
import ResumeResult from './ResumeResult.vue'

type TaskModel = components['schemas']['TaskModel']

// Champs du formulaire
const inputLabel = 'Copier/coller un texte'
const generateButtonLabel = 'Générer'

const abregeStore = useAbregeStore()
const { addErrorMessage } = useToaster()

const resumeResult = ref<TaskModel>()
const isGenerating = ref(false)
const percentage = computed<number>(() =>
  abregeStore.taskData && abregeStore.taskData.percentage != null
    ? Math.round(abregeStore.taskData.percentage * 100)
    : 0,
)

// Schéma de validation avec Yup
const { handleSubmit, errors, defineField } = useForm({
  validationSchema: yup.object({
    textToResume: yup.string()
      .required('Le texte est requis.')
      .min(200, 'Le texte doit contenir au moins 200 caractères.'),
  }),
})

const [textToResume, textToResumeAttrs] = defineField('textToResume')
watch(textToResume, (newValue) => {
  abregeStore.textToResume = newValue
})

const onSubmit = handleSubmit(async () => {
  try {
    isGenerating.value = true
    await abregeStore.sendContentAndPoll('text')
    if (abregeStore.taskData && abregeStore.taskData.id) {
      resumeResult.value = await abregeStore.downloadContentSummary(abregeStore.taskData.id)
    }
    else {
      throw new Error('Aucune tâche valide trouvée pour le résumé.')
    }
    await (new Promise(resolve => setTimeout(resolve, 1000)))
    isGenerating.value = false
    abregeStore.reset()
  }
  catch (error) {
    addErrorMessage({
      title: 'Erreur lors de la génération de résumé :',
      description: `${error}`,
    })
    isGenerating.value = false
  }
})

function newSearch () {
  isGenerating.value = false
  resumeResult.value = undefined
  onSubmit()
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
    <div>
      <DsfrInputGroup
        v-model="textToResume"
        :label-visible="true"
        :is-textarea="true"
        :label="inputLabel"
        v-bind="textToResumeAttrs"
        :error-message="errors.textToResume"
      />
    </div>
    <ParamsResume />
    <div
      v-if="isGenerating"
      class="is-generating-container"
    >
      <ProgressBar
        :visible="isGenerating"
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
      :disabled="isGenerating"
      @click="onSubmit"
    />
  </form>
</template>

<style scoped>
  :deep(textarea){
    min-height: 114px;
  }
  @media (min-width: 768px) {
    textarea {
      min-height: 144px;
    }
  }
</style>
