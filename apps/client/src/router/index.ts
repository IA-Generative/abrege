import type { RouteLocationNormalized } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import ResumeView from '@/views/Index.vue'

const routes = [
  {
    path: '/',
    name: 'resume',
    component: ResumeView,
  },
  {
    path: '/login',
    name: 'Login',
    beforeEnter: async (_to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
      const userStore = useUserStore()
      await userStore.login()
    },
    component: ResumeView,
  },
  {
    path: '/register',
    name: 'Register',
    beforeEnter: async (_to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
      const userStore = useUserStore()
      await userStore.register()
    },
    component: ResumeView,
  },
  {
    path: '/logout',
    name: 'Logout',
    beforeEnter: async (_to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
      const userStore = useUserStore()
      await userStore.logout()
    },
    component: ResumeView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
