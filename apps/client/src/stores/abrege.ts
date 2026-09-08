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

export interface QAItemRow {
  id: string
  task_id: string
  chunk_index: number
  page: number | null
  source_text: string
  question: string
  answer: string
  model_name: string | null
  created_at: number
}

export interface EntityRow {
  id: string
  task_id: string
  chunk_index: number
  type: string
  text: string
  contexts: string[] | null
  pages: number[] | null
  model_name: string | null
  created_at: number
}

export interface RelationshipRow {
  id: string
  task_id: string
  chunk_index: number | null
  source_entity_id: string
  target_entity_id: string
  relationship_type: string
  description: string | null
  model_name: string | null
  created_at: number
}

export interface TopicRow {
  id: string
  task_id: string
  topic: string
  confidence: number
  explanation: string | null
  model_name: string | null
  created_at: number
}

export interface ChunkRow {
  id: string
  task_id: string
  chunk_index: number
  position: number
  page: number | null
  text: string
  model_name: string | null
  created_at: number
}

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
    extractQa: true,
  }
  const paramsValue = ref(paramsInitialValue)

  async function healthCheck (): Promise<boolean> {
    try {
      const { data } = await http.get<{ status: string }>('/health')
      if (data.status !== 'healthy') {
        throw new Error(`Statut inattendu: ${data.status}`)
      }
      return true
    } catch (err: any) {
      error.value = err.message ?? 'Erreur inconnue lors du health check.'
      return false
    }
  }

  async function getTask (taskId: string): Promise<TaskModel> {
    try {
      if (SSO_BYPASS) {
        const mock = MOCK_TASKS.find(t => t.id === taskId)
        if (mock) return mock
      }
      const { data } = await http.get<TaskModel>(`/task/${taskId}`)
      return data
    } catch (err: any) {
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
    } catch (err: any) {
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
        extract_qa: paramsValue.value.extractQa,
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
    } catch (err: any) {
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
        extract_qa: paramsValue.value.extractQa,
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
    } catch (err: any) {
      let errorMessage = 'Erreur lors de l\'envoi du fichier.'
      if (err.response) {
        const status = err.response.status
        if (status === 413) {
          errorMessage = 'Fichier trop volumineux pour le serveur'
        } else if (status === 415) {
          errorMessage = 'Type de fichier non supporté'
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message
        }
      } else if (err.message) {
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
    } catch (error) {
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
      id: 'mock-1',
      user_id: 'dev',
      type: 'text-url',
      status: 'completed',
      percentage: 1,
      created_at: Date.now() / 1000 - 3600,
      updated_at: Date.now() / 1000 - 3500,
      input: { url: 'https://example.com/article' } as any,
      output: { type: 'summary', summary: 'Ceci est un résumé généré automatiquement pour tester l\'affichage de la modale.', word_count: 12, created_at: 0, model_name: 'mock', model_version: '1', texts_found: [], percentage: 1, nb_llm_calls: 1, partial_summaries: [] },
      parameters: null,
      ...({ qa_entities_status: 'completed', relationships_status: 'completed', topics_status: 'completed' } as any),
    },
    {
      id: 'mock-2',
      user_id: 'dev',
      type: 'document',
      status: 'completed',
      percentage: 1,
      created_at: Date.now() / 1000 - 7200,
      updated_at: Date.now() / 1000 - 7100,
      input: { raw_filename: 'rapport_annuel.pdf' } as any,
      output: { type: 'summary', summary: 'Résumé du rapport annuel : les indicateurs sont en hausse de 12% sur l\'année.', word_count: 15, created_at: 0, model_name: 'mock', model_version: '1', texts_found: [], percentage: 1, nb_llm_calls: 2, partial_summaries: [] },
      parameters: null,
    },
    {
      id: 'mock-3',
      user_id: 'dev',
      type: 'text-url',
      status: 'in_progress',
      percentage: 0.6,
      created_at: Date.now() / 1000 - 120,
      updated_at: Date.now() / 1000 - 60,
      input: { text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' } as any,
      output: null,
      parameters: null,
    },
    {
      id: 'mock-4',
      user_id: 'dev',
      type: 'text-url',
      status: 'failed',
      percentage: 0,
      created_at: Date.now() / 1000 - 86400,
      updated_at: Date.now() / 1000 - 86300,
      input: { url: 'https://example.com/broken' } as any,
      output: null,
      parameters: null,
    },
  ]

  async function fetchUserTasks (page = 1, page_size = 100) {
    try {
      const { data } = await http.get(`/task/user/`, { params: { offset: page, limit: page_size } })
      userTasksPaginated.value.total = data.total ?? 0
      userTasksPaginated.value.page = data.page ?? page
      userTasksPaginated.value.page_size = data.page_size ?? page_size
      userTasksPaginated.value.items = data.items ?? []
    } catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les tâches: ${err?.message ?? err}` })
    }
  }

  // ----- QA ITEMS (per task) -----
  const qaItems = ref<QAItemRow[]>([])
  const qaItemsLoading = ref(false)

  const MOCK_QA_ITEMS: QAItemRow[] = [
    {
      id: 'qa-mock-1', task_id: 'mock-1', chunk_index: 0, page: 1,
      source_text: 'Le rapport annuel indique une hausse de 12% du chiffre d\'affaires sur l\'exercice, portée par la croissance à l\'international.',
      question: 'De combien le chiffre d\'affaires a-t-il augmenté ?',
      answer: '12% sur l\'exercice.',
      model_name: 'gpt-4',
      created_at: Date.now() / 1000 - 3500,
    },
    {
      id: 'qa-mock-2', task_id: 'mock-1', chunk_index: 0, page: 1,
      source_text: 'Le rapport annuel indique une hausse de 12% du chiffre d\'affaires sur l\'exercice, portée par la croissance à l\'international.',
      question: 'Quel facteur explique principalement cette croissance ?',
      answer: 'La croissance à l\'international.',
      model_name: 'gpt-4',
      created_at: Date.now() / 1000 - 3499,
    },
    {
      id: 'qa-mock-3', task_id: 'mock-1', chunk_index: 1, page: 2,
      source_text: 'Les effectifs sont passés de 320 à 410 collaborateurs, principalement dans les équipes techniques et commerciales.',
      question: 'Combien de collaborateurs compte l\'entreprise désormais ?',
      answer: '410 collaborateurs.',
      model_name: 'gpt-4',
      created_at: Date.now() / 1000 - 3400,
    },
    {
      id: 'qa-mock-4', task_id: 'mock-1', chunk_index: 1, page: 2,
      source_text: 'Les effectifs sont passés de 320 à 410 collaborateurs, principalement dans les équipes techniques et commerciales.',
      question: 'Quelles équipes ont le plus grandi ?',
      answer: 'Les équipes techniques et commerciales.',
      model_name: 'gpt-4',
      created_at: Date.now() / 1000 - 3399,
    },
    {
      id: 'qa-mock-5', task_id: 'mock-1', chunk_index: 2, page: 3,
      source_text: 'Un nouveau centre de données a été inauguré à Lyon en mars, renforçant la résilience de l\'infrastructure.',
      question: 'Où se situe le nouveau centre de données ?',
      answer: 'À Lyon.',
      model_name: 'gpt-4',
      created_at: Date.now() / 1000 - 3300,
    },
  ]

  const qaItemsTotal = ref(0)
  const qaItemsPage = ref(1)
  const qaItemsPageSize = ref(20)

  async function fetchQAItems (taskId: string, page = 1, pageSize = 20) {
    qaItemsLoading.value = true
    try {
      if (SSO_BYPASS) {
        qaItems.value = MOCK_QA_ITEMS
        qaItemsTotal.value = MOCK_QA_ITEMS.length
        qaItemsPage.value = 1
        qaItemsPageSize.value = MOCK_QA_ITEMS.length
        return
      }
      // Backend response is paginated: { total, page, page_size, items }
      const { data } = await http.get<{ total: number, page: number, page_size: number, items: QAItemRow[] }>(
        `/task/${taskId}/qa`,
        { params: { offset: page, limit: pageSize } },
      )
      qaItems.value = data.items ?? []
      qaItemsTotal.value = data.total ?? 0
      qaItemsPage.value = data.page ?? page
      qaItemsPageSize.value = data.page_size ?? pageSize
    }
    catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les questions/réponses: ${err?.message ?? err}` })
      qaItems.value = []
      qaItemsTotal.value = 0
    }
    finally {
      qaItemsLoading.value = false
    }
  }

  // ----- ENTITIES & RELATIONSHIPS (per task) -----
  const entities = ref<EntityRow[]>([])
  const relationships = ref<RelationshipRow[]>([])
  const entitiesLoading = ref(false)

  const MOCK_ENTITIES: EntityRow[] = [
    { id: 'ent-mock-1', task_id: 'mock-1', chunk_index: 0, type: 'PERSON', text: 'Marie Curie', contexts: ['Marie Curie a reçu le prix Nobel'], pages: [1], model_name: 'gpt-4', created_at: 0 },
    { id: 'ent-mock-2', task_id: 'mock-1', chunk_index: 0, type: 'ORGANIZATION', text: 'Académie des Sciences', contexts: ['membre de l\'Académie des Sciences'], pages: [1], model_name: 'gpt-4', created_at: 0 },
    { id: 'ent-mock-3', task_id: 'mock-1', chunk_index: 1, type: 'DATE', text: '1903-12-10', contexts: ['remise du prix le 10 décembre 1903'], pages: [2], model_name: 'gpt-4', created_at: 0 },
    { id: 'ent-mock-4', task_id: 'mock-1', chunk_index: 1, type: 'LOCATION', text: 'Paris', contexts: ['la cérémonie s\'est tenue à Paris'], pages: [2], model_name: 'gpt-4', created_at: 0 },
    { id: 'ent-mock-5', task_id: 'mock-1', chunk_index: 2, type: 'PERSON', text: 'Pierre Curie', contexts: ['Pierre Curie, son époux et co-lauréat'], pages: [3], model_name: 'gpt-4', created_at: 0 },
    { id: 'ent-mock-6', task_id: 'mock-1', chunk_index: 2, type: 'ORGANIZATION', text: 'Université de Paris', contexts: ['professeure à l\'Université de Paris'], pages: [3], model_name: 'gpt-4', created_at: 0 },
  ]

  const MOCK_RELATIONSHIPS: RelationshipRow[] = [
    { id: 'rel-mock-1', task_id: 'mock-1', chunk_index: 0, source_entity_id: 'ent-mock-1', target_entity_id: 'ent-mock-2', relationship_type: 'MEMBRE_DE', description: 'Marie Curie est membre de l\'Académie des Sciences', model_name: 'gpt-4', created_at: 0 },
    { id: 'rel-mock-2', task_id: 'mock-1', chunk_index: null, source_entity_id: 'ent-mock-1', target_entity_id: 'ent-mock-3', relationship_type: 'RECOMPENSEE_LE', description: 'Prix Nobel reçu le 10 décembre 1903', model_name: 'gpt-4', created_at: 0 },
    { id: 'rel-mock-3', task_id: 'mock-1', chunk_index: null, source_entity_id: 'ent-mock-3', target_entity_id: 'ent-mock-4', relationship_type: 'A_LIEU_A', description: 'La cérémonie du 10 décembre 1903 a eu lieu à Paris', model_name: 'gpt-4', created_at: 0 },
    { id: 'rel-mock-4', task_id: 'mock-1', chunk_index: 2, source_entity_id: 'ent-mock-1', target_entity_id: 'ent-mock-5', relationship_type: 'EPOUX_DE', description: 'Marie Curie est l\'épouse de Pierre Curie', model_name: 'gpt-4', created_at: 0 },
    { id: 'rel-mock-5', task_id: 'mock-1', chunk_index: null, source_entity_id: 'ent-mock-1', target_entity_id: 'ent-mock-6', relationship_type: 'PROFESSEURE_A', description: 'Marie Curie est professeure à l\'Université de Paris', model_name: 'gpt-4', created_at: 0 },
    { id: 'rel-mock-6', task_id: 'mock-1', chunk_index: null, source_entity_id: 'ent-mock-5', target_entity_id: 'ent-mock-6', relationship_type: 'PROFESSEUR_A', description: 'Pierre Curie enseigne également à l\'Université de Paris', model_name: 'gpt-4', created_at: 0 },
  ]

  async function fetchEntitiesAndRelationships (taskId: string) {
    entitiesLoading.value = true
    try {
      if (SSO_BYPASS) {
        entities.value = MOCK_ENTITIES
        relationships.value = MOCK_RELATIONSHIPS
        return
      }
      const [entitiesRes, relationshipsRes] = await Promise.all([
        http.get<{ items: EntityRow[] }>(`/task/${taskId}/entities`, { params: { offset: 1, limit: 200 } }),
        http.get<{ items: RelationshipRow[] }>(`/task/${taskId}/relationships`, { params: { offset: 1, limit: 200 } }),
      ])
      entities.value = entitiesRes.data.items ?? []
      relationships.value = relationshipsRes.data.items ?? []
    }
    catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les entités/relations: ${err?.message ?? err}` })
      entities.value = []
      relationships.value = []
    }
    finally {
      entitiesLoading.value = false
    }
  }

  // ----- TOPICS (per task) -----
  const topics = ref<TopicRow[]>([])
  const topicsLoading = ref(false)

  const MOCK_TOPICS: TopicRow[] = [
    {
      id: 'topic-mock-1', task_id: 'mock-1', topic: 'finance', confidence: 0.92,
      explanation: 'Le résumé mentionne une hausse de 12% du chiffre d\'affaires et des indicateurs financiers en amélioration.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-2', task_id: 'mock-1', topic: 'ressources humaines', confidence: 0.58,
      explanation: 'Le résumé évoque la croissance des effectifs et des équipes.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-3', task_id: 'mock-1', topic: 'infrastructure', confidence: 0.31,
      explanation: 'Mention brève d\'un nouveau centre de données, sans développement approfondi.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-4', task_id: 'mock-1', topic: 'international', confidence: 0.67,
      explanation: 'La croissance est portée par le développement à l\'international.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-5', task_id: 'mock-1', topic: 'stratégie d\'entreprise', confidence: 0.55,
      explanation: 'Le résumé décrit des orientations stratégiques générales de l\'entreprise.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-6', task_id: 'mock-1', topic: 'recrutement', confidence: 0.44,
      explanation: 'Mention du recrutement dans les équipes techniques et commerciales.',
      model_name: 'gpt-4',
      created_at: 0,
    },
    {
      id: 'topic-mock-7', task_id: 'mock-1', topic: 'immobilier', confidence: 0.22,
      explanation: 'Référence indirecte à l\'implantation du nouveau centre de données.',
      model_name: 'gpt-4',
      created_at: 0,
    },
  ]

  async function fetchTopics (taskId: string) {
    topicsLoading.value = true
    try {
      if (SSO_BYPASS) {
        topics.value = MOCK_TOPICS
        return
      }
      // No cap on the number of topics: page through the whole (paginated) backend result.
      const pageSize = 50
      const all: TopicRow[] = []
      let page = 1
      let total = Infinity
      while (all.length < total) {
        const { data } = await http.get<{ total: number, items: TopicRow[] }>(
          `/task/${taskId}/topics`,
          { params: { offset: page, limit: pageSize } },
        )
        total = data.total ?? 0
        all.push(...(data.items ?? []))
        if (!data.items || data.items.length === 0) break
        page += 1
      }
      topics.value = all
    }
    catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les sujets: ${err?.message ?? err}` })
      topics.value = []
    }
    finally {
      topicsLoading.value = false
    }
  }

  // ----- CHUNKS (per task) — semantic chunking, done LLM-side at map time -----
  const chunks = ref<ChunkRow[]>([])
  const chunksLoading = ref(false)
  const chunksTotal = ref(0)
  const chunksPage = ref(1)
  const chunksPageSize = ref(20)

  const MOCK_CHUNKS: ChunkRow[] = [
    { id: 'chunk-mock-1', task_id: 'mock-1', chunk_index: 0, position: 0, page: 1, text: 'Le rapport annuel indique une hausse de 12% du chiffre d\'affaires sur l\'exercice.', model_name: 'gpt-4', created_at: 0 },
    { id: 'chunk-mock-2', task_id: 'mock-1', chunk_index: 0, position: 1, page: 1, text: 'Cette croissance est portée par le développement à l\'international.', model_name: 'gpt-4', created_at: 0 },
    { id: 'chunk-mock-3', task_id: 'mock-1', chunk_index: 1, position: 0, page: 2, text: 'Les effectifs sont passés de 320 à 410 collaborateurs.', model_name: 'gpt-4', created_at: 0 },
    { id: 'chunk-mock-4', task_id: 'mock-1', chunk_index: 1, position: 1, page: 2, text: 'La croissance a surtout concerné les équipes techniques et commerciales.', model_name: 'gpt-4', created_at: 0 },
    { id: 'chunk-mock-5', task_id: 'mock-1', chunk_index: 2, position: 0, page: 3, text: 'Un nouveau centre de données a été inauguré à Lyon en mars.', model_name: 'gpt-4', created_at: 0 },
    { id: 'chunk-mock-6', task_id: 'mock-1', chunk_index: 2, position: 1, page: 3, text: 'Cette implantation renforce la résilience de l\'infrastructure du groupe.', model_name: 'gpt-4', created_at: 0 },
  ]

  async function fetchChunks (taskId: string, page = 1, pageSize = 20) {
    chunksLoading.value = true
    try {
      if (SSO_BYPASS) {
        chunks.value = MOCK_CHUNKS
        chunksTotal.value = MOCK_CHUNKS.length
        chunksPage.value = 1
        chunksPageSize.value = MOCK_CHUNKS.length
        return
      }
      const { data } = await http.get<{ total: number, page: number, page_size: number, items: ChunkRow[] }>(
        `/task/${taskId}/chunks`,
        { params: { offset: page, limit: pageSize } },
      )
      chunks.value = data.items ?? []
      chunksTotal.value = data.total ?? 0
      chunksPage.value = data.page ?? page
      chunksPageSize.value = data.page_size ?? pageSize
    }
    catch (err: any) {
      addErrorMessage({ title: 'Erreur', description: `Impossible de récupérer les chunks: ${err?.message ?? err}` })
      chunks.value = []
      chunksTotal.value = 0
    }
    finally {
      chunksLoading.value = false
    }
  }

  // kept for backward compatibility (no-op stoppers)
  function startPollingUserTasks (page = 1, page_size = 100) {
    fetchUserTasks(page, page_size)
  }

  function stopPollingUserTasks () { /* no-op: polling removed */ }

  // ----- CANCEL TASK -----
  async function cancelTask (taskId: string) {
    try {
      const { data } = await http.post<TaskModel>(`/task/${taskId}/cancel`)
      const idx = userTasksPaginated.value.items.findIndex(t => t.id === taskId)
      if (idx !== -1) { userTasksPaginated.value.items[idx] = data }
      addSuccessMessage({ title: 'Tâche annulée', description: 'La tâche a été annulée avec succès.' })
      return data
    } catch (err: any) {
      addErrorMessage({ title: 'Annulation impossible', description: `Erreur lors de l'annulation: ${err?.message ?? err}` })
      throw err
    }
  }

  // ----- DELETE TASK -----
  async function deleteTask (taskId: string) {
    try {
      await http.delete(`/task/${taskId}`)
      userTasksPaginated.value.items = userTasksPaginated.value.items.filter(t => t.id !== taskId)
      userTasksPaginated.value.total = Math.max(0, userTasksPaginated.value.total - 1)
      addSuccessMessage({ title: 'Tâche supprimée', description: 'La tâche a été supprimée avec succès.' })
    } catch (err: any) {
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
    getTask,
    downloadContentSummary,
    // task list management
    userTasksPaginated,
    fetchUserTasks,
    startPollingUserTasks,
    stopPollingUserTasks,
    cancelTask,
    deleteTask,
    // qa items
    qaItems,
    qaItemsLoading,
    qaItemsTotal,
    qaItemsPage,
    qaItemsPageSize,
    fetchQAItems,
    // entities & relationships
    entities,
    relationships,
    entitiesLoading,
    fetchEntitiesAndRelationships,
    // topics
    topics,
    topicsLoading,
    fetchTopics,
    // chunks
    chunks,
    chunksLoading,
    chunksTotal,
    chunksPage,
    chunksPageSize,
    fetchChunks,
  }
})
