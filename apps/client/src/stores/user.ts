import type { IUser } from '@/interfaces/IUser.js'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchMe, login, logout } from '../utils/auth'

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref<boolean>()
  const userProfile = ref<IUser>()

  const checkAuth = async () => {
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
