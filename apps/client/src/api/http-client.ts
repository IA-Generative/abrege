import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'

import { getValidToken } from '@/utils/keycloak'

function isSsoBypassed (): boolean {
  return (import.meta.env && import.meta.env.DEV)
    || import.meta.env.VITE_SSO_BYPASS === 'true'
    || (globalThis as any).VITE_SSO_BYPASS === 'true'
}

function createHttpClient (baseURL: string): AxiosInstance {
  const httpClient = axios.create({
    baseURL,
    withCredentials: false,
    headers: {
      Accept: 'application/json',
    },
  })

  httpClient.interceptors.request.use(
    async (config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> => {
      if (isSsoBypassed()) {
        return config
      }

      const token = await getValidToken()
      if (config.headers && typeof config.headers.set === 'function') {
        config.headers.set('Authorization', `Bearer ${token}`)
      }
      return config
    },
    (error: AxiosError) => Promise.reject(error)
  )

  return httpClient
}

export default createHttpClient
