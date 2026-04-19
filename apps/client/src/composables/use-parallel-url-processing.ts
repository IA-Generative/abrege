import type { components } from '@/api/types/api.schema'
import { ref } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

type TaskModel = components['schemas']['TaskModel']

export type UrlProcessingState = {
  status: 'idle' | 'processing' | 'done' | 'error'
  percentage: number
  result: TaskModel | null
  error: string | null
}

export type MergeProcessingState = {
  status: 'idle' | 'pending' | 'processing' | 'done' | 'error'
  percentage: number
  taskId: string | null
  result: TaskModel | null
  error: string | null
}

const POLL_INTERVAL_MS = 2000
const http = createHttpClient(ABREGE_API_URL)

async function submitUrl (
  url: string,
  params: { customPrompt?: string | null, language?: string | null, size?: number | null },
): Promise<string> {
  const { data: task } = await http.post<TaskModel>('/task/text-url', {
    content: { url },
    parameters: {
      language: params.language ?? 'French',
      size: params.size ?? null,
      custom_prompt: params.customPrompt ?? null,
    },
  })
  if (!task?.id) throw new Error('Réponse API invalide : ID de tâche manquant')
  return task.id
}

async function pollUntilDone (
  taskId: string,
  onProgress: (percentage: number, status: string) => void,
): Promise<TaskModel> {
  return new Promise((resolve, reject) => {
    const check = async () => {
      try {
        const { data: task } = await http.get<TaskModel>(`/task/${taskId}`)
        onProgress(task.percentage ?? 0, task.status)
        if (task.status === 'completed') return resolve(task)
        if (task.status === 'failed' || task.status === 'canceled' || task.status === 'timeout') {
          return reject(new Error(`Tâche échouée avec le statut : ${task.status}`))
        }
        setTimeout(check, POLL_INTERVAL_MS)
      }
      catch (err: any) {
        reject(err)
      }
    }
    check()
  })
}

export function useParallelUrlProcessing () {
  const urlStates = ref<UrlProcessingState[]>([])
  const mergeState = ref<MergeProcessingState>({
    status: 'idle',
    percentage: 0,
    taskId: null,
    result: null,
    error: null,
  })

  function syncUrls (count: number) {
    while (urlStates.value.length < count) {
      urlStates.value.push({ status: 'idle', percentage: 0, result: null, error: null })
    }
    urlStates.value = urlStates.value.slice(0, count)
  }

  function resetMergeState () {
    mergeState.value = { status: 'idle', percentage: 0, taskId: null, result: null, error: null }
  }

  async function processAll (
    urls: string[],
    params: { customPrompt?: string | null, language?: string | null, size?: number | null }[],
    mergeEnabled = false,
  ): Promise<{ filename: string, task: TaskModel }[]> {
    urlStates.value = urls.map(() => ({ status: 'idle', percentage: 0, result: null, error: null }))
    resetMergeState()

    const results: ({ filename: string, task: TaskModel } | null)[] = Array(urls.length).fill(null)

    // Submit all URLs in parallel
    const taskIds: (string | null)[] = await Promise.all(
      urls.map(async (url, i) => {
        urlStates.value[i].status = 'processing'
        try {
          const id = await submitUrl(url, params[i] ?? {})
          return id
        }
        catch (err: any) {
          urlStates.value[i].status = 'error'
          urlStates.value[i].error = err.message ?? 'Échec de l\'envoi'
          return null
        }
      }),
    )

    const validTaskIds = taskIds.filter((id): id is string => id !== null)

    // Launch merge as soon as IDs are known
    let mergePollPromise: Promise<void> | null = null
    if (mergeEnabled && validTaskIds.length > 1) {
      try {
        mergeState.value.status = 'pending'
        const { data: mergeTask } = await http.post<TaskModel>('/tasks/merge/', validTaskIds)
        if (!mergeTask?.id) throw new Error('Réponse API invalide : ID de merge manquant')
        mergeState.value.taskId = mergeTask.id
        mergeState.value.status = 'processing'

        mergePollPromise = pollUntilDone(mergeTask.id, (percentage) => {
          mergeState.value.percentage = percentage * 100
        }).then((task) => {
          mergeState.value.status = 'done'
          mergeState.value.percentage = 100
          mergeState.value.result = task
        }).catch((err: any) => {
          mergeState.value.status = 'error'
          mergeState.value.error = err.message ?? 'Échec du merge'
        })
      }
      catch (err: any) {
        mergeState.value.status = 'error'
        mergeState.value.error = err.message ?? 'Échec de la création du merge'
      }
    }

    // Poll all in parallel
    await Promise.all(
      taskIds.map(async (taskId, i) => {
        if (!taskId) return
        try {
          const task = await pollUntilDone(taskId, (percentage) => {
            if (urlStates.value[i].status !== 'error') {
              urlStates.value[i].percentage = percentage * 100
            }
          })
          urlStates.value[i].status = 'done'
          urlStates.value[i].percentage = 100
          urlStates.value[i].result = task
          results[i] = { filename: urls[i], task }
        }
        catch (err: any) {
          urlStates.value[i].status = 'error'
          urlStates.value[i].error = err.message ?? 'Échec du traitement'
        }
      }),
    )

    if (mergePollPromise) await mergePollPromise

    return results.filter((r): r is { filename: string, task: TaskModel } => r !== null)
  }

  return { urlStates, mergeState, syncUrls, processAll }
}
