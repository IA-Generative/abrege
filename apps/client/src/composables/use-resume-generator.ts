import type { AxiosError } from 'axios'
import type { components } from '@/api/types/api.schema'
import { ref, toRefs } from 'vue'

import { useAbregeStore } from '@/stores/abrege'
import useToaster from './use-toaster'

type TaskModel = components['schemas']['TaskModel']

interface ErrorWithDetail {
  response: {
    data: {
      detail: string
    }
  }
}

// Vérifie si l'erreur a une propriété detail
function isErrorWithDetail (error: unknown): error is ErrorWithDetail {
  return (
    typeof error === 'object'
    && error !== null
    && 'response' in error
    && typeof (error as ErrorWithDetail).response?.data?.detail === 'string'
  )
}

export function useResumeGenerator (asyncFunction: (...args: any[]) => Promise<TaskModel>) {
  const isGenerating = ref(false)
  const progress = ref(0)
  const result = ref<TaskModel | null | undefined>(null)
  const { addMessage } = useToaster()

  const abregeStore = useAbregeStore()
  const { paramsValue } = toRefs(abregeStore)

  const generate = async (...args: any[]) => {
    isGenerating.value = true
    result.value = null

    // Simuler une barre de progression
    const interval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += 10
      }
    }, 300)

    try {
      const response = await asyncFunction(...args)
      result.value = response
    }
    catch (error: unknown) {
      if (!(error as AxiosError)?.response) {
        addMessage({
          type: 'error',
          title: 'Erreur de connexion',
          description: 'Impossible de se connecter à l\'API.',
          timeout: 3000,
        })
      }
      else {
        const errorMessage = isErrorWithDetail(error)
          ? error.response.data.detail
          : 'Problème serveur'

        addMessage({
          type: 'error',
          title: 'Erreur',
          description: errorMessage,
          timeout: 3000,
        })
      }
    }
    finally {
      clearInterval(interval)
      progress.value = 100
      setTimeout(() => {
        isGenerating.value = false
        progress.value = 0
      }, 500)
    }
  }

  return {
    isGenerating,
    progress,
    result,
    generate,
    paramsValue,
  }
}
