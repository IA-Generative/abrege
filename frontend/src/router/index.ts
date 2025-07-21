import { createRouter, createWebHistory } from 'vue-router'
import ResumeView from '@/views/Index.vue'

const routes = [
  {
    path: '/',
    name: 'resume',
    component: ResumeView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
