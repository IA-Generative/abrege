<script lang="ts" setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'

import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'
import { useParallelUrlProcessing } from '@/composables/use-parallel-url-processing'
import type { components } from '@/api/types/api.schema'
import FileParamsModal from './FileParamsModal.vue'
import ResumeResultModal from './ResumeResultModal.vue'

type TaskModel = components['schemas']['TaskModel']

const abregeStore = useAbregeStore()
const { addErrorMessage } = useToaster()

const parallelProcessing = useParallelUrlProcessing()
const urlStates = parallelProcessing.urlStates
const mergeState = parallelProcessing.mergeState

const resumeResults = ref<{ filename: string, task: TaskModel }[]>([])
const showResultModal = ref(false)
const showResultModalIndex = ref(0)

const isLoading = ref(false)
const mergeEnabled = ref(false)
const showMergeParams = ref(false)
const mergeParams = ref({
  language: 'French',
  size: null as number | null,
  customPrompt: null as string | null,
})

const expandedUrlIndex = ref<number | null>(null)

const { errors, defineField, resetForm } = useForm({
  validationSchema: yup.object({
    currentUrl: yup.string().required("L'URL est requise.").url("L'URL doit être valide."),
  }),
})

const [currentUrl, currentUrlAttrs] = defineField('currentUrl')

function addUrl () {
  const url = (currentUrl.value ?? '').trim()
  if (!url) return
  abregeStore.urlList.push(url)
  abregeStore.urlListParams.push({ customPrompt: null, language: null, size: null })
  parallelProcessing.syncUrls(abregeStore.urlList.length)
  resetForm()
}

function removeUrl (index: number) {
  abregeStore.urlList.splice(index, 1)
  abregeStore.urlListParams.splice(index, 1)
  parallelProcessing.syncUrls(abregeStore.urlList.length)
}

function openUrlParams (index: number) {
  expandedUrlIndex.value = index
}

function closeUrlParams () {
  expandedUrlIndex.value = null
}

async function onSubmit () {
  if (!abregeStore.urlList.length) return
  try {
    isLoading.value = true
    resumeResults.value = []

    const params = abregeStore.urlListParams.map(p => ({
      customPrompt: p?.customPrompt ?? null,
      language: p?.language ?? null,
      size: p?.size ?? null,
    }))

    const results = await parallelProcessing.processAll(abregeStore.urlList, params, mergeEnabled.value)
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

function newSearch () {
  resumeResults.value = []
  showResultModal.value = false
  abregeStore.urlList.splice(0)
  abregeStore.urlListParams.splice(0)
  parallelProcessing.syncUrls(0)
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

    <!-- URL input -->
    <DsfrInputGroup
      v-model="currentUrl"
      :label-visible="true"
      label="Entrer une URL"
      v-bind="currentUrlAttrs"
      :error-message="errors.currentUrl"
      @keydown.enter.prevent="addUrl"
    />
    <div class="url-add-row">
      <DsfrButton
        type="button"
        size="sm"
        label="Ajouter l'URL"
        icon="ri:add-line"
        secondary
        :disabled="isLoading"
        @click="addUrl"
      />
    </div>

    <!-- URL list -->
    <div class="url-list-container">
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
              :title="url"
            >{{ url }}</a>
            <div class="url-list-actions">
              <DsfrButton
                size="sm"
                label="Paramètres"
                tertiary
                :disabled="isLoading"
                @click="openUrlParams(index)"
              />
              <DsfrButton
                size="sm"
                label="Retirer"
                secondary
                :disabled="isLoading"
                @click="removeUrl(index)"
              />
            </div>
          </div>
          <!-- Progress bar per URL -->
          <ProgressBar
            v-if="urlStates[index]?.status === 'processing'"
            :visible="true"
            :progress="urlStates[index].percentage"
          />
          <!-- Result button -->
          <div
            v-if="urlStates[index]?.status === 'done' || urlStates[index]?.status === 'error'"
            class="url-list-result"
          >
            <DsfrButton
              size="sm"
              :label="urlStates[index]?.status === 'error' ? 'Échec' : 'Voir le résumé'"
              :disabled="urlStates[index]?.status !== 'done'"
              secondary
              @click="() => {
                const resultIndex = resumeResults.findIndex(r => r.filename === url)
                if (resultIndex >= 0) {
                  showResultModalIndex = resultIndex
                  showResultModal = true
                }
              }"
            />
            <span
              v-if="urlStates[index]?.status === 'error'"
              class="url-error-msg"
            >{{ urlStates[index].error }}</span>
          </div>
        </li>

        <!-- Merge item -->
        <li
          v-if="abregeStore.urlList.length > 1"
          class="url-list-item url-list-item--merge"
        >
          <div class="url-list-row">
            <label class="url-list-label">
              <input
                v-model="mergeEnabled"
                type="checkbox"
                class="fr-mr-1w"
                :disabled="isLoading"
              />
              Résumé global
            </label>
            <div class="url-list-actions">
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
            class="url-list-result"
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
              class="url-error-msg"
            >{{ mergeState.error }}</span>
          </div>
        </li>
      </ul>
    </div>

    <FileParamsModal
      v-if="expandedUrlIndex !== null && abregeStore.urlListParams[expandedUrlIndex]"
      :item-label="abregeStore.urlList[expandedUrlIndex]"
      item-icon="fr-icon-links-line"
      :params="abregeStore.urlListParams[expandedUrlIndex]"
      @close="closeUrlParams"
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
      description="Les URLs sont traitées en parallèle. Le temps de traitement varie en fonction du contenu de chaque page."
      class="fr-mb-2w"
    />

    <DsfrButton
      size="lg"
      label="Générer"
      :disabled="isLoading || !abregeStore.urlList.length"
      @click="onSubmit"
    />
  </form>
</template>

<style scoped>
.url-add-row {
  margin-bottom: 1rem;
}

.url-list-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
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
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.75rem;
  background: var(--grey-975-75, #f6f6f6);
  border-radius: 4px;
  gap: 0.5rem;
}

.url-list-item--merge {
  border-left: 3px solid var(--blue-france-sun-113-625, #000091);
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

.url-list-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.url-error-msg {
  font-size: 0.75rem;
  color: var(--text-default-error);
}
</style>
