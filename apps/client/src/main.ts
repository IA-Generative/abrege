import * as Sentry from '@sentry/vue'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

// @ts-expect-error vue-matomo
import VueMatomo from 'vue-matomo'
import App from './App.vue'
import router from './router/index'
import { ENVIRONMENT, MATOMO_SITE_ID, MATOMO_SITE_URL, SENTRY_FRONTEND_DSN } from './utils/constants'

import '@gouvfr/dsfr/dist/core/core.main.min.css'
import '@gouvfr/dsfr/dist/component/component.main.min.css'

import '@gouvfr/dsfr/dist/utility/utility.main.min.css'
import '@gouvminint/vue-dsfr/styles'

import '@gouvfr/dsfr/dist/scheme/scheme.min.css'
import './main.css'

declare global {
  interface Window {
    _paq: Array<(string | number | boolean | object)[]>
  }
}

function initializeApp () {
  const app = createApp(App)

  if (SENTRY_FRONTEND_DSN) {
    try {
      Sentry.init({
        app,
        dsn: SENTRY_FRONTEND_DSN,
        environment: ENVIRONMENT,
        sendDefaultPii: false,
      })
    } catch (e) {
      console.error('Sentry initialization failed, continuing without it:', e)
    }
  }

  app
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
