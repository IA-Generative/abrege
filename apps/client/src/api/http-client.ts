import type { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'

import { getKeycloak } from '@/utils/keycloak'

interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

function createHttpClient (baseURL: string): AxiosInstance {
  const httpClient = axios.create({
    baseURL,
    withCredentials: false,
    headers: {
      Accept: 'application/json',
    },
  })

  // Intercepteur pour ajouter le token à chaque requête
  httpClient.interceptors.request.use(
    (config: CustomAxiosRequestConfig): CustomAxiosRequestConfig => {
      const keycloak = getKeycloak()
      if (keycloak.authenticated && keycloak.token) {
        if (config.headers && typeof config.headers.set === 'function') {
          config.headers.set('Authorization', `Bearer ${keycloak.token}`)
        }
      }
      return config
    },
    (error: AxiosError) => Promise.reject(error)
  )

  // Intercepteur pour gérer les erreurs 401 (token expiré)
  httpClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as CustomAxiosRequestConfig
      if (originalRequest && error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true
        const keycloak = getKeycloak()
        try {
          const refreshed = await keycloak.updateToken(30)
          if (refreshed) {
            if (originalRequest.headers && typeof originalRequest.headers.set === 'function') {
              originalRequest.headers.set('Authorization', `Bearer ${keycloak.token}`)
            }
            return httpClient(originalRequest)
          }
        } catch (refreshError) {
          console.error('Echec du rafraîchissement du token :', refreshError)
          await keycloak.login()
        }
      }
      return Promise.reject(error)
    }
  )

  return httpClient
}

export default createHttpClient
