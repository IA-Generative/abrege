import type { components } from '@/api/types/api.schema'
import { ref } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

type TaskModel = components['schemas']['TaskModel']

export type FileProcessingState = {
  status: 'idle' | 'uploading' | 'processing' | 'done' | 'error'
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

async function submitDocument (
  file: File,
  params: { customPrompt?: string | null, language?: string | null, size?: number | null },
): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('parameters', JSON.stringify({
    language: params.language ?? 'French',
    size: params.size ?? null,
    custom_prompt: params.customPrompt ?? null,
  }))

  const { data: task } = await http.post<TaskModel>('/task/document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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

export function useParallelFileProcessing () {
  const fileStates = ref<FileProcessingState[]>([])
  const mergeState = ref<MergeProcessingState>({
    status: 'idle',
    percentage: 0,
    taskId: null,
    result: null,
    error: null,
  })

  function resetMergeState () {
    mergeState.value = { status: 'idle', percentage: 0, taskId: null, result: null, error: null }
  }

  function initStates (count: number) {
    fileStates.value = Array.from({ length: count }, () => ({
      status: 'idle',
      percentage: 0,
      result: null,
      error: null,
    }))
  }

  function syncFiles (count: number) {
    while (fileStates.value.length < count) {
      fileStates.value.push({ status: 'idle', percentage: 0, result: null, error: null })
    }
    fileStates.value = fileStates.value.slice(0, count)
  }

  async function processAll (
    files: File[],
    params: { customPrompt?: string | null, language?: string | null, size?: number | null }[],
    mergeEnabled = false,
  ): Promise<{ filename: string, task: TaskModel }[]> {
    initStates(files.length)
    resetMergeState()

    const results: ({ filename: string, task: TaskModel } | null)[] = Array(files.length).fill(null)

    // Submit all files in parallel
    const taskIds: (string | null)[] = await Promise.all(
      files.map(async (file, i) => {
        fileStates.value[i].status = 'uploading'
        try {
          const id = await submitDocument(file, params[i] ?? {})
          fileStates.value[i].status = 'processing'
          return id
        }
        catch (err: any) {
          fileStates.value[i].status = 'error'
          fileStates.value[i].error = err.message ?? 'Échec de l\'envoi'
          return null
        }
      }),
    )

    const validTaskIds = taskIds.filter((id): id is string => id !== null)

    // Lancer le merge dès que les IDs sont connus (le serveur attend la fin des sous-tâches)
    let mergePollPromise: Promise<void> | null = null
    if (mergeEnabled && validTaskIds.length > 1) {
      try {
        mergeState.value.status = 'pending'
        const { data: mergeTask } = await http.post<TaskModel>('/tasks/merge/', validTaskIds)
        if (!mergeTask?.id) throw new Error('Réponse API invalide : ID de merge manquant')
        mergeState.value.taskId = mergeTask.id
        mergeState.value.status = 'processing'

        mergePollPromise = pollUntilDone(mergeTask.id, (percentage, _status) => {
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

    // Poll all tasks in parallel
    await Promise.all(
      taskIds.map(async (taskId, i) => {
        if (!taskId) return
        try {
          const task = await pollUntilDone(taskId, (percentage, status) => {
            if (fileStates.value[i].status !== 'error') {
              fileStates.value[i].percentage = percentage * 100
              if (status === 'queued') fileStates.value[i].status = 'processing'
            }
          })
          fileStates.value[i].status = 'done'
          fileStates.value[i].percentage = 100
          fileStates.value[i].result = task
          results[i] = { filename: files[i].name, task }
        }
        catch (err: any) {
          fileStates.value[i].status = 'error'
          fileStates.value[i].error = err.message ?? 'Échec du traitement'
        }
      }),
    )

    // Attendre la fin du merge si lancé
    if (mergePollPromise) await mergePollPromise

    return results.filter((r): r is { filename: string, task: TaskModel } => r !== null)
  }

  return { fileStates, mergeState, syncFiles, processAll }
}
