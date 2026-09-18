import type { AxiosError, AxiosInstance } from 'axios'
import axios from 'axios'

import { login } from '@/utils/auth'

function createHttpClient (baseURL: string): AxiosInstance {
  const httpClient = axios.create({
    baseURL,
    // BFF : le navigateur ne détient aucun jeton, seulement le cookie de session
    // `httpOnly` posé par `/api/auth/callback`. Il doit être envoyé sur chaque appel.
    withCredentials: true,
    headers: {
      Accept: 'application/json',
    },
  })

  // Le rafraîchissement du token se fait désormais côté backend (SessionStore), de façon
  // transparente. Un 401 ici signifie que la session backend elle-même n'est plus valide
  // (jamais authentifié, ou refresh token Keycloak expiré) : il n'y a rien à rejouer,
  // seule une nouvelle connexion peut résoudre la situation.
  httpClient.interceptors.response.use(
    response => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        login()
      }
      return Promise.reject(error)
    },
  )

  return httpClient
}

export default createHttpClient
