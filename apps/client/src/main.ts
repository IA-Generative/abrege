import { createPinia } from 'pinia'
import { createApp } from 'vue'

import VueMatomo from 'vue-matomo'

import App from './App.vue'

import router from './router/index'

import { MATOMO_SITE_ID, MATOMO_SITE_URL } from './utils/constants'

import '@gouvfr/dsfr/dist/core/core.main.min.css'
import '@gouvfr/dsfr/dist/component/component.main.min.css'

import '@gouvfr/dsfr/dist/utility/utility.main.min.css'
import '@gouvminint/vue-dsfr/styles'

import '@gouvfr/dsfr/dist/scheme/scheme.min.css'

import './main.css'

declare global {
  interface Window {
    // biome-ignore lint/suspicious/noExplicitAny: <explanation>
    _paq: any[]
  }
}

async function initializeApp () {
  createApp(App)
    .use(createPinia())
    .use(router)
    .use(VueMatomo, {
      host: MATOMO_SITE_URL,
      siteId: MATOMO_SITE_ID,
      router,
      debug: true,
    })
    .mount('#app')

  window._paq.push(['trackPageView'])
}

initializeApp()
