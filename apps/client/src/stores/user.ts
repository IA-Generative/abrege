import type { IUser } from '@/interfaces/IUser.js'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getKeycloak, getUserProfile, keycloakLogin, keycloakLogout, keycloakRegister } from '../utils/keycloak'

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

  const setUserProfile = async () => {
    userProfile.value = SSO_BYPASS ? MOCK_USER : getUserProfile()
  }

  const setIsLoggedIn = async () => {
    if (SSO_BYPASS) {
      isLoggedIn.value = true
      userProfile.value = MOCK_USER
      return
    }
    const keycloak = getKeycloak()
    if (keycloak.authenticated !== isLoggedIn.value) {
      isLoggedIn.value = keycloak.authenticated
      if (isLoggedIn.value) {
        await setUserProfile()
      }
    }
  }

  const login = () => keycloakLogin()

  const register = () => keycloakRegister()

  const logout = () => keycloakLogout()

  return {
    isLoggedIn,
    setIsLoggedIn,
    userProfile,
    setUserProfile,
    login,
    register,
    logout,
  }
})
