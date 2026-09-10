// use-app-version.ts
import type { components } from '@/api/types/api.schema'
import { ref } from 'vue'

import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

type Health = components['schemas']['Health']

const http = createHttpClient(ABREGE_API_URL)

const frontendVersion = __APP_VERSION__
const backendVersion = ref<string | null>(null)

async function fetchBackendVersion () {
  if (backendVersion.value) {
    return
  }
  try {
    const { data } = await http.get<Health>('/health')
    backendVersion.value = data.version
  } catch {
    backendVersion.value = null
  }
}

function useAppVersion () {
  return {
    frontendVersion,
    backendVersion,
    fetchBackendVersion,
  }
}

export default useAppVersion
