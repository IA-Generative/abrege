/**
 *
 * @Status - Errors :
 *    - CREATED = "created"  # Tâche instanciée mais pas encore mise en file
 *    - QUEUED = "queued"  # En attente dans une file de traitement
 *    - STARTED = "started"  # A commencé à être traitée
 *    - IN_PROGRESS = "in_progress"
 *    - COMPLETED = "completed"  # Traitée avec succès
 *    - FAILED = "failed"  # Erreur fatale
 *    - RETRYING = "retrying"  # En cours de nouvelle tentative après échec
 *    - CANCELED = "canceled"  # Annulée manuellement ou par logique métier
 *
 *    - CREATED,  # 201 - Tâche créée, pas encore traitée
 *    - ACCEPTED,  # 202 - Tâche en file d’attente
 *    - STARTED,  # 202 - Traitement démarré
 *    - PARTIAL_CONTENT,  # 206 - Traitement en cours
 *    - OK, # 200 - Traitement terminé avec succès
 *    - INTERNAL_SERVER_ERROR,  # 500 - Échec du traitement
 *    - ALREADY_REPORTED,  # 208 - Nouvelle tentative en cours
 *    - INTERNAL_SERVER_ERROR,  # 500 - Traitement annulé
 *    - GATEWAY_TIMEOUT,  # 504 - Temps d’attente dépassé
 */
import type { components } from '@/api/types/api.schema'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import createHttpClient from '@/api/http-client'
import useToaster from '@/composables/use-toaster'
import { ABREGE_API_URL } from '@/utils/constants'

type TaskModel = components['schemas']['TaskModel']

const http = createHttpClient(ABREGE_API_URL)

const { addErrorMessage, addSuccessMessage } = useToaster()

const VALID_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'application/vnd.oasis.opendocument.text',
  'application/vnd.oasis.opendocument.presentation',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  // Ajout pour .doc et .txt :
  'application/msword',
  'text/plain',
  // Other formats :
  // 'audio/mpeg',
  // 'video/mp4',
  // 'audio/wav',
]

export const useAbregeStore = defineStore('abrege', () => {
  const textToResume = ref('')
  const urlToResume = ref('')
  const urlList = ref<string[]>([])
  const urlListParams = ref<{ customPrompt: string | null, language: string | null, size: number | null }[]>([])
  const fileUpload = ref<File[]>([])
  const fileParams = ref<{ customPrompt: string | null, language: string | null, size: number | null }[]>([])

  const status = ref<string | null>(null)
  const percentage = ref<number>(0)
  const taskData = ref<TaskModel | null>(null)
  const isPolling = ref(false)
  const error = ref<string | undefined>(undefined)
  const position = ref<number | null>(null)
  const previousPosition = ref<number | null>(null)

  const paramsInitialValue = {
    inputValue: null,
    selectOptionSelected: 'French',
    selectOptionText: 'Français (par défaut)',
    customPrompt: null,
  }
  const paramsValue = ref(paramsInitialValue)

  async function healthCheck (): Promise<boolean> {
    try {
      const { data } = await http.get<{ status: string }>('/health')
      if (data.status !== 'healthy') {
        throw new Error(`Statut inattendu: ${data.status}`)
      }
      return true
    }
    catch (err: any) {
      error.value = err.message ?? 'Erreur inconnue lors du health check.'
      return false
    }
  }

  async function getTask (taskId: string): Promise<TaskModel> {
    try {
      const { data } = await http.get<TaskModel>(`/task/${taskId}`)
      return data
    }
    catch (err: any) {
      addErrorMessage({
        title: 'Erreur :',
        description: `Erreur lors de la récupération de la tâche ${taskId}: ${err}`,
      })
      throw new Error(`Impossible de récupérer l'état de la tâche: ${err.message ?? 'Erreur inconnue'}`)
    }
  }

  async function pollTask (
    taskId: string,
    intervalMs = 2000,
  ) {
    status.value = null
    percentage.value = 0
    taskData.value = null
    error.value = undefined
    isPolling.value = true
    previousPosition.value = null

    try {
      const check = async (): Promise<void> => {
        const task = await getTask(taskId)

        status.value = task.status

        switch (task.status) {
          case 'in_progress':
            status.value = task.status
            percentage.value = task.percentage || 0
            taskData.value = task
            break

          case 'completed':
            addSuccessMessage({
              title: 'Tâche terminée avec succès :',
              description: 'Vous pouvez accéder au résumé.',
            })
            status.value = task.status
            taskData.value = task
            isPolling.value = false
            return

          case 'failed':
            addErrorMessage({
              title: 'Échec du traitement :',
              description: 'Une erreur est survenue lors du traitement OCR.',
            })
            error.value = 'La génération de résumé a échoué'
            isPolling.value = false
            return

          case 'queued': {
            const currentPosition = (task.position ?? 0) + 1
            position.value = currentPosition

            if (previousPosition.value !== currentPosition) {
              addSuccessMessage({
                title: 'Vous êtes en file d\'attente :',
                description: `Il y a ${position.value} document(s) en attente.`,
                timeout: 0,
              })
              previousPosition.value = currentPosition
            }

            status.value = task.status
            break
          }

          default:
            break
        }

        await new Promise(res => setTimeout(res, intervalMs))
        await check()
      }
      await check()
    }
    catch (err: any) {
      error.value = err.message ?? 'Erreur inconnue lors du polling.'
      isPolling.value = false
    }
  }

  /**
   * Vérifie le type de fichier avant envoi
   */
  function validateFile (file: File): { valid: boolean, message?: string } {
    // Vérification du type MIME
    if (!VALID_MIME_TYPES.includes(file.type)) {
      return {
        valid: false,
        message: `Type de fichier non supporté: ${file.type}. Utilisez PDF, JPEG ou PNG.`,
      }
    }
    // Vérification de la taille (200 Mo max)
    const MAX_SIZE = 200 * 1024 * 1024 // 200 Mo en octets
    if (file.size > MAX_SIZE) {
      return {
        valid: false,
        message: `Fichier trop volumineux: ${(file.size / (1024 * 1024)).toFixed(2)} Mo. Maximum: 200 Mo.`,
      }
    }
    return {
      valid: true,
      message: 'Type et taille de fichier valides.',
    }
  }

  function reset () {
    status.value = null
    percentage.value = 0
    taskData.value = null
    isPolling.value = false
    error.value = undefined
  }

  async function sendContentAndPoll (type: 'text' | 'url', contentOverride?: string, overrideParams?: { customPrompt?: string | null, language?: string | null, size?: number | null }) {
    const ok = await healthCheck()
    if (!ok) {
      return
    }

    const resolvedLanguage = overrideParams?.language ?? paramsValue.value.selectOptionSelected
    const resolvedSize = overrideParams?.size != null ? overrideParams.size : Number(paramsValue.value.inputValue)
    const resolvedPrompt = overrideParams?.customPrompt !== undefined ? overrideParams.customPrompt : paramsValue.value.customPrompt

    const defaultContent = type === 'url' ? urlToResume.value : textToResume.value
    const body = {
      content: { [type]: contentOverride ?? defaultContent },
      parameters: {
        language: resolvedLanguage,
        size: resolvedSize,
        custom_prompt: resolvedPrompt,
      },
    }

    try {
      const { data: task } = await http.post<TaskModel>(
        `/task/text-url`,
        body,
      )

      if (!task || !task.id) {
        throw new Error('Réponse API invalide: ID de tâche manquant')
      }

      await pollTask(task.id)
    }
    catch (err: any) {
      error.value = err.message || 'Erreur lors de l\'envoi du contenu.'
      isPolling.value = false
      throw error
    }
  }

  async function sendDocumentAndPoll (file: File, fileCustomPrompt?: string | null, fileLanguage?: string | null, fileSize?: number | null) {
    const validation = validateFile(file)
    if (!validation.valid) {
      error.value = validation.message
      return
    }

    const ok = await healthCheck()
    if (!ok) {
      return
    }

    try {
      const formData = new FormData()
      formData.append('file', file)
      const resolvedPrompt = fileCustomPrompt !== undefined ? fileCustomPrompt : paramsValue.value.customPrompt
      const resolvedLanguage = fileLanguage !== undefined && fileLanguage !== null ? fileLanguage : paramsValue.value.selectOptionSelected
      const resolvedSize = fileSize !== undefined && fileSize !== null ? fileSize : Number(paramsValue.value.inputValue)
      formData.append('parameters', JSON.stringify({
        language: resolvedLanguage,
        size: resolvedSize,
        custom_prompt: resolvedPrompt,
      }))

      const { data: task } = await http.post<TaskModel>(
        `/task/document`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        },
      )

      if (!task || !task.id) {
        throw new Error('Réponse API invalide: ID de tâche manquant')
      }

      await pollTask(task.id)
    }
    catch (err: any) {
      // Extraire le message d'erreur le plus pertinent
      let errorMessage = 'Erreur lors de l\'envoi du fichier.'
      if (err.response) {
        // Erreur de l'API avec réponse
        const status = err.response.status
        if (status === 413) {
          errorMessage = 'Fichier trop volumineux pour le serveur'
        }
        else if (status === 415) {
          errorMessage = 'Type de fichier non supporté'
        }
        else if (err.response.data && err.response.data.message) {
          errorMessage = err.response.data.message
        }
      }
      else if (err.message) {
        errorMessage = err.message
      }
      error.value = errorMessage
      isPolling.value = false
    }
  }

  /**
   * Récupère le résumé d'un texte ou d'un lien ou d'un fichier.
   */
  async function downloadContentSummary (taskId: string): Promise<TaskModel> {
    try {
      const response = await http.get<TaskModel>(
        `/task/${taskId}`,
      )
      const data = response.data
      return data
    }
    catch (error) {
      addErrorMessage({
        title: 'Erreur :',
        description: `Erreur lors de la récupération du texte résumé : ${error}.`,
      })
      throw error
    }
  }

  // ----- POLLING FOR USER TASKS -----
  const userTasksPaginated = ref({
    total: 0,
    page: 1,
    page_size: 10,
    items: [] as TaskModel[],
  })

  let _stopUserTasksPolling = false

  async function _pollUserTasksLoop (page = 1, page_size = 10, intervalMs = 100000) {
    _stopUserTasksPolling = false
    while (!_stopUserTasksPolling) {
      try {
        const { data } = await http.get(`/task/user/`, { params: { offset: page, limit: page_size } })
        userTasksPaginated.value.total = data.total ?? 0
        userTasksPaginated.value.page = data.page ?? page
        userTasksPaginated.value.page_size = data.page_size ?? page_size
        userTasksPaginated.value.items = data.items ?? []
      }
      catch (err: any) {
        // swallow errors during polling
      }
      // wait before next poll
      // stop early if requested
      const wait = new Promise(resolve => setTimeout(resolve, intervalMs))
      await wait
    }
  }

  function startPollingUserTasks (page = 1, page_size = 10, intervalMs = 3000) {
    // stop any existing poll
    stopPollingUserTasks()
    // load immediately and then continue polling
    _pollUserTasksLoop(page, page_size, intervalMs)
  }

  function stopPollingUserTasks () {
    _stopUserTasksPolling = true
  }

  // One-shot fetch for user tasks (useful when we don't want continuous polling)
  async function fetchUserTasks (page = 1, page_size = 10) {
    try {
      const { data } = await http.get(`/task/user/`, { params: { offset: page, limit: page_size } })
      userTasksPaginated.value.total = data.total ?? 0
      userTasksPaginated.value.page = data.page ?? page
      userTasksPaginated.value.page_size = data.page_size ?? page_size
      userTasksPaginated.value.items = data.items ?? []
    }
    catch (err: any) {
      // keep existing behavior: swallow errors here (UI may show nothing)
    }
  }

  // ----- DELETE TASK (wrapped here so UI can use store for actions) -----
  async function deleteTask (taskId: string) {
    try {
      await http.delete(`/task/${taskId}`)
      addSuccessMessage({ title: 'Tâche supprimée', description: 'La tâche a été supprimée avec succès.' })
    }
    catch (err: any) {
      addErrorMessage({ title: 'Suppression impossible', description: `Erreur lors de la suppression: ${err?.message ?? err}` })
      throw err
    }
  }

  async function mergeTasksAndPoll (taskIds: string[]) {
    const ok = await healthCheck()
    if (!ok) return

    try {
      const { data: task } = await http.post<TaskModel>('/tasks/merge/', taskIds)
      if (!task || !task.id) {
        throw new Error('Réponse API invalide: ID de tâche manquant')
      }
      await pollTask(task.id)
    }
    catch (err: any) {
      error.value = err.message || 'Erreur lors du merge des tâches.'
      isPolling.value = false
      throw err
    }
  }

  const formattedPercentage = computed(() =>
    taskData.value && taskData.value.percentage != null
      ? Math.round(taskData.value.percentage * 100)
      : 0,
  )

  return {
    // State
    textToResume,
    urlToResume,
    urlList,
    urlListParams,
    fileUpload,
    fileParams,
    paramsValue,
    taskData,
    position,
    status,
    percentage,
    isPolling,
    error,
    formattedPercentage,

    // actions
    reset,
    sendContentAndPoll,
    sendDocumentAndPoll,
    downloadContentSummary,
    mergeTasksAndPoll,
    // polling & management
    userTasksPaginated,
    startPollingUserTasks,
    stopPollingUserTasks,
    fetchUserTasks,
    deleteTask,
  }
})
