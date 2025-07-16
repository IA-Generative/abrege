import type { IResumeResult } from '@/interfaces/IResume'
import { ref, toRefs } from 'vue'

import { useAbregeStore } from '@/stores/abrege'
import useToaster from './use-toaster'

export function useResumeGenerator (asyncFunction: (...args: any[]) => Promise<IResumeResult>) {
  const isGenerating = ref(false)
  const progress = ref(0)
  const result = ref<IResumeResult | null | undefined>(null)
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
    catch (error) {
      if (!error.response) {
        addMessage({
          type: 'error',
          title: 'Erreur de connexion',
          description: 'Impossible de se connecter à l\'API.',
          timeout: 3000,
        })
      }
      else {
        addMessage({
          type: 'error',
          title: 'Erreur',
          description: error.response.data?.detail ?? 'Problème serveur',
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
