import type { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'

import { getKeycloak, getUserProfile } from '@/utils/keycloak'

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

  // Intercepteur pour ajouter le token et les headers utilisateur à chaque requête
  httpClient.interceptors.request.use(
    (config: CustomAxiosRequestConfig): CustomAxiosRequestConfig => {
      const keycloak = getKeycloak()
      if (keycloak.authenticated && keycloak.token) {
        if (config.headers && typeof config.headers.set === 'function') {
          config.headers.set('Authorization', `${keycloak.tokenParsed?.typ || 'Bearer'} ${keycloak.token}`)

          // Send user id
          const userId = keycloak.subject || keycloak.tokenParsed?.sub
          if (userId) {
            config.headers.set('X-User-Id', userId)
          }

          // Ajouter les headers X-User-Id et X-Roles
          try {
            const userProfile = getUserProfile()
            config.headers.set('X-User-Id', userProfile.id)
            config.headers.set('X-Roles', userProfile.groups?.join(',') || '')
          }
          catch (error) {
            console.warn('Impossible de récupérer le profil utilisateur pour les headers:', error)
          }
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

              // Remettre les headers utilisateur lors du retry
              try {
                const userProfile = getUserProfile()
                originalRequest.headers.set('X-User-Id', userProfile.id)
                originalRequest.headers.set('X-Roles', userProfile.groups?.join(',') || '')
              }
              catch (profileError) {
                console.warn('Impossible de récupérer le profil utilisateur lors du retry:', profileError)
              }
            }
            return httpClient(originalRequest)
          }
        }
        catch (refreshError) {
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
