import { ref, onMounted } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

const http = createHttpClient(ABREGE_API_URL)

export function useApiVersion () {
  const version = ref<string | null>(null)

  onMounted(async () => {
    try {
      const { data } = await http.get<{ version: string }>('/health')
      version.value = data.version ?? null
    }
    catch {
      version.value = null
    }
  })

  return { version }
}
