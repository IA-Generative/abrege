import type { IUser } from '@/interfaces/IUser.js'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getKeycloak, getUserProfile, keycloakLogin, keycloakLogout, keycloakRegister } from '../utils/keycloak'

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref<boolean>()
  const userProfile = ref<IUser>()

  const setUserProfile = async () => {
    userProfile.value = getUserProfile()
  }

  const setIsLoggedIn = async () => {
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
