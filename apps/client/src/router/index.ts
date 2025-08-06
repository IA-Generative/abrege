import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/stores/user'
import { KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM, KEYCLOAK_REDIRECT_URI, KEYCLOAK_URL } from '@/utils/constants'
import { getKeycloak } from '@/utils/keycloak'
import ResumeView from '@/views/Index.vue'

function redirectToSSO () {
  const loginUrl = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth?client_id=${encodeURIComponent(KEYCLOAK_CLIENT_ID)}&redirect_uri=${encodeURIComponent(KEYCLOAK_REDIRECT_URI)}&response_type=code`
  window.location.href = loginUrl
}

// Force la redirection explicite vers le serveur
// Si l'utilisateur n'est pas authentifié, provoque
// alors le processus SSO (trappé par oauth2-proxy)
function authGuard (_path: string) {
  return async (
    _to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ) => {
    const keycloak = getKeycloak()
    if (!keycloak.authenticated) {
      redirectToSSO()
      return
    }
    next()
  }
}

const routes = [
  {
    path: '/',
    name: 'resume',
    component: ResumeView,
    beforeEnter: authGuard('/'),
  },
  {
    path: '/login',
    name: 'Login',
    beforeEnter: async (_to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
      const userStore = useUserStore()
      await userStore.login()
      next()
    },
    component: ResumeView,
  },
  {
    path: '/logout',
    name: 'Logout',
    beforeEnter: async (_to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
      const userStore = useUserStore()
      await userStore.logout()
      next()
    },
    component: ResumeView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
