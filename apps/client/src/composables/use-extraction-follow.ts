import type { Ref } from 'vue'
import type { TaskExtractionState } from '@/utils/extractions'
import { useAbregeStore } from '@/stores/abrege'
import { hasPendingExtractions } from '@/utils/extractions'

/**
 * Keeps a task shown on the main page up to date after its summary completed: Q&A, entities,
 * chunks and topics keep running in the background, so the displayed task is refreshed until every
 * requested extraction has settled. `minTicks` keeps polling a few rounds even when everything
 * looks settled (right after a retry the status stays "failed" until the worker picks the job up).
 */
export default function useExtractionFollow<T extends { id: string } & TaskExtractionState> (result: Ref<T | undefined>) {
  const abrege = useAbregeStore()
  let latestRun = 0

  async function follow (minTicks = 3, intervalMs = 3000, maxMs = 3 * 60 * 1000) {
    const taskId = result.value?.id
    if (!taskId) { return }
    const run = ++latestRun
    const startedAt = Date.now()
    for (let tick = 0; Date.now() - startedAt < maxMs; tick++) {
      const current = result.value
      // Stop when a newer run took over, or when another task replaced / cleared the result.
      if (run !== latestRun || !current || current.id !== taskId) { return }
      if (tick >= minTicks && !hasPendingExtractions(current)) { return }
      await new Promise(resolve => setTimeout(resolve, intervalMs))
      try {
        const task = await abrege.getTask(taskId)
        if (run === latestRun && result.value?.id === taskId) { result.value = task as unknown as T }
      } catch {
        return
      }
    }
  }

  return { follow }
}
