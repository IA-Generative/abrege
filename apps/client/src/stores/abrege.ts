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

  async function sendDocumentAndPoll () {
    if (!fileUpload.value) {
      error.value = 'Aucun fichier sélectionné'
      return Promise.reject(error.value)
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

  const formattedPercentage = computed(() =>
    taskData.value && taskData.value.percentage != null
      ? Math.round(taskData.value.percentage * 100)
      : 0,
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
  }
})
