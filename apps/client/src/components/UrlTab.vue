<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { useForm } from 'vee-validate'
import * as yup from 'yup'

import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import FileParamsModal from './FileParamsModal.vue'
import ResumeResult from './ResumeResult.vue'

type TaskModel = components['schemas']['TaskModel']

const inputLabel = 'Entrer une URL'
const generateButtonLabel = 'Générer'

const abregeStore = useAbregeStore()
const { addErrorMessage } = useToaster()

const resumeResults = ref<TaskModel[]>([])
const isGenerating = ref(false)
const mergeEnabled = ref(false)
const mergeParams = ref({
  language: 'French',
  size: null as number | null,
  customPrompt: null as string | null,
})
const languageOptions = [
  { value: 'French', text: 'Français (par défaut)' },
  { value: 'English', text: 'Anglais' },
]
const percentage = computed<number>(() =>
  abregeStore.taskData && abregeStore.taskData.percentage != null
    ? Math.round(abregeStore.taskData.percentage * 100)
    : 0,
)

const { errors, defineField, resetForm } = useForm({
  validationSchema: yup.object({
    currentUrl: yup.string().required('L\'URL est requise.').url('L\'URL doit être valide.'),
  }),
})

const [currentUrl, currentUrlAttrs] = defineField('currentUrl')

function addUrl () {
  const url = (currentUrl.value ?? '').trim()
  if (!url) return
  abregeStore.urlList.push(url)
  abregeStore.urlListParams.push({ customPrompt: null, language: null, size: null })
  resetForm()
}

function removeUrl (index: number) {
  abregeStore.urlList.splice(index, 1)
  abregeStore.urlListParams.splice(index, 1)
}

const expandedUrlIndex = ref<number | null>(null)

function openUrlParams (index: number) {
  expandedUrlIndex.value = index
}

function closeUrlParams () {
  expandedUrlIndex.value = null
}

async function onSubmit () {
  if (!abregeStore.urlList.length) return
  try {
    isGenerating.value = true
    const taskIds: string[] = []
    for (const [i, url] of abregeStore.urlList.entries()) {
      const p = abregeStore.urlListParams[i]
      await abregeStore.sendContentAndPoll('url', url, {
        customPrompt: p?.customPrompt,
        language: p?.language,
        size: p?.size,
      })
      if (abregeStore.taskData?.id) {
        taskIds.push(abregeStore.taskData.id)
        const result = await abregeStore.downloadContentSummary(abregeStore.taskData.id)
        resumeResults.value.push(result)
      }
      else if (abregeStore.error) {
        addErrorMessage({ title: 'Erreur :', description: abregeStore.error })
      }
    }

    if (mergeEnabled.value && taskIds.length > 1) {
      await abregeStore.mergeTasksAndPoll(taskIds)
      if (abregeStore.taskData?.id) {
        const mergeResult = await abregeStore.downloadContentSummary(abregeStore.taskData.id)
        resumeResults.value.push(mergeResult)
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
    isGenerating.value = false
  }
}

function newSearch () {
  resumeResults.value = []
  abregeStore.urlList.splice(0)
  abregeStore.urlListParams.splice(0)
  abregeStore.reset()
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

    <DsfrInputGroup
      v-model="currentUrl"
      :label-visible="true"
      :label="inputLabel"
      v-bind="currentUrlAttrs"
      :error-message="errors.currentUrl"
      @keydown.enter.prevent="addUrl"
    />
    <div class="url-add-row">
      <button
        type="button"
        class="url-add-btn fr-btn fr-btn--icon-left fr-icon-add-line"
        :disabled="isGenerating"
        @click="addUrl"
      >
        Ajouter l'URL
      </button>
    </div>

    <ul
      v-if="abregeStore.urlList.length"
      class="url-list"
    >
      <li
        v-for="(url, index) in abregeStore.urlList"
        :key="index"
        class="url-list-item"
      >
        <div class="url-list-row">
          <a
            :href="url"
            target="_blank"
            rel="noopener noreferrer"
            class="url-list-label"
          >{{ url }}</a>
          <div class="url-list-actions">
            <DsfrButton
              size="sm"
              label="Paramètres"
              tertiary
              :disabled="isGenerating"
              @click="openUrlParams(index)"
            />
            <DsfrButton
              size="sm"
              label="Retirer"
              secondary
              :disabled="isGenerating"
              @click="removeUrl(index)"
            />
          </div>
        </div>
      </li>
    </ul>

    <div
      v-if="abregeStore.urlList.length > 1"
      class="merge-section"
    >
      <DsfrCheckbox
        v-model="mergeEnabled"
        label="Résumer l'ensemble des URLs"
        name="merge-urls"
      />
      <div
        v-if="mergeEnabled"
        class="merge-params"
      >
        <div class="merge-param-row">
          <DsfrSelect
            v-model="mergeParams.language"
            label="Langue du résumé global"
            :options="languageOptions"
          />
        </div>
        <div class="merge-param-row">
          <DsfrInput
            v-model="mergeParams.size"
            label="Nombre de mots"
            label-visible
            placeholder="4000 (par défaut)"
            hint="Nombre de mots approximatif pour le résumé global"
            type="number"
          />
        </div>
        <div class="merge-param-row">
          <DsfrInput
            v-model="mergeParams.customPrompt"
            :label-visible="true"
            :is-textarea="true"
            label="Instruction pour le résumé global"
            hint="Laissez vide pour un résumé synthétique par défaut"
          />
        </div>
      </div>
    </div>

    <FileParamsModal
      v-if="expandedUrlIndex !== null && abregeStore.urlListParams[expandedUrlIndex]"
      :item-label="abregeStore.urlList[expandedUrlIndex]"
      item-icon="fr-icon-links-line"
      :params="abregeStore.urlListParams[expandedUrlIndex]"
      @close="closeUrlParams"
    />

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
      :disabled="isGenerating || !abregeStore.urlList.length"
      @click="onSubmit"
    />
  </form>
</template>

<style scoped>
.url-add-row {
  margin-bottom: 1rem;
}

.url-add-btn {
  background-color: var(--blue-france-sun-113-625, #000091);
  color: white;
}

.url-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.url-list-item {
  padding: 0.5rem 0.75rem;
  background: var(--grey-975-75, #f6f6f6);
  border-radius: 4px;
}

.url-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.url-list-label {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.url-list-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
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

