import type { components } from '@/api/types/api.schema'
import { onMounted, ref } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

type Health = components['schemas']['Health']

const http = createHttpClient(ABREGE_API_URL)

export function useBackendHealth () {
  const health = ref<Health | null>(null)
  const loading = ref(false)
  const error = ref(false)

  async function fetchHealth () {
    loading.value = true
    error.value = false
    try {
      const { data } = await http.get<Health>('/health')
      health.value = data
    } catch {
      error.value = true
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchHealth)

  return { health, loading, error }
}
