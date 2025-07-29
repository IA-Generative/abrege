declare module 'vue-matomo' {
  import type { App } from 'vue'
  import type { Router } from 'vue-router'

  interface MatomoOptions {
    host: string
    siteId: number
    trackerFileName?: string
    router?: Router
    enableLinkTracking?: boolean
    requireConsent?: boolean
    trackInitialView?: boolean
  }

  const VueMatomo: {
    install: (app: App, options: MatomoOptions) => void
  }

  export default VueMatomo
}
