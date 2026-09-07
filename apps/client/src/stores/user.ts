import type { IUser } from '@/interfaces/IUser.js'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchMe, login, logout } from '../utils/auth'

const SSO_BYPASS = import.meta.env.VITE_SSO_BYPASS === 'true' || (globalThis as any).VITE_SSO_BYPASS === 'true'

const MOCK_USER: IUser = {
  id: 'dev',
  email: 'dev@local.fr',
  firstName: 'Dev',
  lastName: 'Local',
  groups: [],
}

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref<boolean>(SSO_BYPASS ? true : undefined as any)
  const userProfile = ref<IUser | undefined>(SSO_BYPASS ? MOCK_USER : undefined)

  const checkAuth = async () => {
    if (SSO_BYPASS) {
      isLoggedIn.value = true
      userProfile.value = MOCK_USER
      return true
    }
    // Already confirmed by a previous check this session - skip the `/api/auth/me`
    // round trip. A session that expires afterwards surfaces as a 401 on the next API
    // call, which the http-client interceptor already sends through `login()`.
    if (isLoggedIn.value) {
      return true
    }
    const profile = await fetchMe()
    userProfile.value = profile ?? undefined
    isLoggedIn.value = !!profile
    return isLoggedIn.value
  }

  return {
    isLoggedIn,
    userProfile,
    checkAuth,
    login,
    logout,
  }
})
