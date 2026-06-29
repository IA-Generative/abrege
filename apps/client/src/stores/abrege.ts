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

const VALID_MIME_TYPES = new Set([
  'application/pdf',
  'image/jpeg',
  'image/png',
  'application/vnd.oasis.opendocument.text',
  'application/vnd.oasis.opendocument.presentation',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/msword',
  'text/plain',
])

export const useAbregeStore = defineStore('abrege', () => {
  const textToResume = ref('')
  const urlToResume = ref('')
  const fileUpload = ref<File | null>(null)

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
    if (!VALID_MIME_TYPES.has(file.type)) {
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

  async function sendContentAndPoll (type: 'text' | 'url') {
    const ok = await healthCheck()
    if (!ok) {
      return
    }

    const body = {
      content: { [type]: type === 'url' ? urlToResume.value : textToResume.value },
      parameters: {
        language: paramsValue.value.selectOptionSelected,
        size: Number(paramsValue.value.inputValue),
        custom_prompt: paramsValue.value.customPrompt,
      },
    }

    try {
      const { data: task } = await http.post<TaskModel>(
        `/task/text-url`,
        body,
      )

      if (!task?.id) {
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

  async function sendDocumentAndPoll () {
    if (!fileUpload.value) {
      error.value = 'Aucun fichier sélectionné'
      throw new Error(error.value)
    }

    const validation = validateFile(fileUpload.value)
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
      formData.append('file', fileUpload.value)
      formData.append('parameters', JSON.stringify({
        language: paramsValue.value.selectOptionSelected,
        size: Number(paramsValue.value.inputValue),
        custom_prompt: paramsValue.value.customPrompt,
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

      if (!task?.id) {
        throw new Error('Réponse API invalide: ID de tâche manquant')
      }

      await pollTask(task.id)
    }
    catch (err: any) {
      let errorMessage = 'Erreur lors de l\'envoi du fichier.'
      if (err.response) {
        const status = err.response.status
        if (status === 413) {
          errorMessage = 'Fichier trop volumineux pour le serveur'
        }
        else if (status === 415) {
          errorMessage = 'Type de fichier non supporté'
        }
        else if (err.response.data?.message) {
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

  // ----- USER TASKS LIST -----
  const userTasksPaginated = ref({
    total: 0,
    page: 1,
    page_size: 100,
    items: [] as TaskModel[],
  })

  const SSO_BYPASS = import.meta.env.VITE_SSO_BYPASS === 'true'

  const MOCK_TASKS: TaskModel[] = [
    {
      id: 'mock-1', user_id: 'dev', type: 'text-url', status: 'completed', percentage: 1,
      created_at: Date.now() / 1000 - 3600, updated_at: Date.now() / 1000 - 3500,
      input: { url: 'https://example.com/article' } as any,
      output: { type: 'summary', summary: 'Ceci est un résumé généré automatiquement pour tester l\'affichage de la modale.', word_count: 12, created_at: 0, model_name: 'mock', model_version: '1', texts_found: [], percentage: 1, nb_llm_calls: 1, partial_summaries: [] },
      parameters: null,
    },
    {
      id: 'mock-2', user_id: 'dev', type: 'document', status: 'completed', percentage: 1,
      created_at: Date.now() / 1000 - 7200, updated_at: Date.now() / 1000 - 7100,
      input: { raw_filename: 'rapport_annuel.pdf' } as any,
      output: { type: 'summary', summary: 'Résumé du rapport annuel : les indicateurs sont en hausse de 12% sur l\'année.', word_count: 15, created_at: 0, model_name: 'mock', model_version: '1', texts_found: [], percentage: 1, nb_llm_calls: 2, partial_summaries: [] },
      parameters: null,
    },
    {
      id: 'mock-3', user_id: 'dev', type: 'text-url', status: 'in_progress', percentage: 0.6,
      created_at: Date.now() / 1000 - 120, updated_at: Date.now() / 1000 - 60,
      input: { text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' } as any,
      output: null,
      parameters: null,
    },
    {
      id: 'mock-4', user_id: 'dev', type: 'text-url', status: 'failed', percentage: 0,
      created_at: Date.now() / 1000 - 86400, updated_at: Date.now() / 1000 - 86300,
      input: { url: 'https://example.com/broken' } as any,
      output: null,
      parameters: null,
    },
  ]

  async function fetchUserTasks (page = 1, page_size = 100) {
    if (SSO_BYPASS) {
      userTasksPaginated.value.total = MOCK_TASKS.length
      userTasksPaginated.value.page = page
      userTasksPaginated.value.page_size = page_size
      userTasksPaginated.value.items = MOCK_TASKS
      return
    }
    try {
      const { data } = await http.get(`/task/user/`, { params: { offset: page, limit: page_size } })
      userTasksPaginated.value.total = data.total ?? 0
      userTasksPaginated.value.page = data.page ?? page
      userTasksPaginated.value.page_size = data.page_size ?? page_size
      userTasksPaginated.value.items = data.items ?? []
    }
    catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les tâches: ${err?.message ?? err}` })
    }
  }

  // kept for backward compatibility (no-op stoppers)
  function startPollingUserTasks (page = 1, page_size = 100) {
    fetchUserTasks(page, page_size)
  }

  function stopPollingUserTasks () { /* no-op: polling removed */ }

  // ----- DELETE TASK -----
  async function deleteTask (taskId: string) {
    try {
      await http.delete(`/task/${taskId}`)
      userTasksPaginated.value.items = userTasksPaginated.value.items.filter(t => t.id !== taskId)
      userTasksPaginated.value.total = Math.max(0, userTasksPaginated.value.total - 1)
      addSuccessMessage({ title: 'Tâche supprimée', description: 'La tâche a été supprimée avec succès.' })
    }
    catch (err: any) {
      addErrorMessage({ title: 'Suppression impossible', description: `Erreur lors de la suppression: ${err?.message ?? err}` })
      throw err
    }
  }

  const formattedPercentage = computed(() =>
    taskData.value?.percentage == null
      ? 0
      : Math.round(taskData.value.percentage * 100),
  )

  return {
    // State
    textToResume,
    urlToResume,
    fileUpload,
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
    // task list management
    userTasksPaginated,
    fetchUserTasks,
    startPollingUserTasks,
    stopPollingUserTasks,
    deleteTask,
  }
})
