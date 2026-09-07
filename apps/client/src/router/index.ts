import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/stores/user'
import ResumeView from '@/views/Index.vue'
import TaskDetailView from '@/views/TaskDetail.vue'

// L'authentification passe entièrement par le backend (BFF) : le navigateur ne fait
// jamais de redirection OIDC lui-même. `checkAuth` interroge `/api/auth/me` (cookie de
// session), et une navigation complète vers `/api/auth/login?redirect=...` déclenche le
// flow côté backend, qui revient directement sur la route demandée après le callback.
function authGuard () {
  return async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ) => {
    const userStore = useUserStore()
    const isLoggedIn = await userStore.checkAuth()
    if (!isLoggedIn) {
      userStore.login(to.fullPath)
      return
    }
    next()
  }
}

const routes = [
  {
    path: '/',
    redirect: '/text',
  },
  {
    path: '/:tab(text|url|document|tasks)',
    name: 'resume-tab',
    component: ResumeView,
    beforeEnter: authGuard(),
  },
  {
    path: '/task/:task_id',
    name: 'task-detail',
    component: TaskDetailView,
    beforeEnter: authGuard(),
  },
  {
    path: '/login',
    name: 'Login',
    // `login`/`logout` sont des navigations complètes (voir utils/auth.ts) - le guard
    // n'atteint jamais `next()` car le navigateur quitte la SPA avant sa résolution.
    beforeEnter: () => {
      const userStore = useUserStore()
      userStore.login()
    },
    component: ResumeView,
  },
  {
    path: '/logout',
    name: 'Logout',
    beforeEnter: () => {
      const userStore = useUserStore()
      void userStore.logout()
    },
    component: ResumeView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
