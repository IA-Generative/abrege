declare module 'vue-matomo' {
  interface MatomoOptions {
    host: string
    siteId: number
    trackerFileName?: string
    // biome-ignore lint/suspicious/noExplicitAny: <explanation>
    router?: any
    enableLinkTracking?: boolean
    requireConsent?: boolean
    trackInitialView?: boolean
  }

  const VueMatomo: {
    // biome-ignore lint/suspicious/noExplicitAny: <explanation>
    install: (app: any, options: MatomoOptions) => void
  }

  export default VueMatomo
}
