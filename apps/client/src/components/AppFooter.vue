<script setup lang="ts">
import { useBackendHealth } from '@/composables/use-backend-health'
import { ABREGE_API_URL } from '@/utils/constants'

const APP_VERSION = __APP_VERSION__
const GITHUB_REPO_URL = 'https://github.com/IA-Generative/abrege'
const API_DOCS_URL = `${ABREGE_API_URL}/docs`

const { health, loading, error } = useBackendHealth()
</script>

<template>
  <footer
    class="fr-footer fr-mt-auto"
    role="contentinfo"
  >
    <div class="fr-container">
      <div class="fr-footer__body">
        <div class="fr-footer__bottom">
          <ul class="fr-footer__bottom-list">
            <li class="fr-footer__bottom-item">
              <a
                class="fr-footer__bottom-link"
                :href="GITHUB_REPO_URL"
                target="_blank"
                rel="noopener noreferrer"
              >
                <span
                  class="fr-icon-github-fill fr-icon--sm"
                  aria-hidden="true"
                />
                Code source
              </a>
            </li>
            <li class="fr-footer__bottom-item">
              <a
                class="fr-footer__bottom-link"
                :href="API_DOCS_URL"
                target="_blank"
                rel="noopener noreferrer"
              >
                <span
                  class="fr-icon-code-s-slash-line fr-icon--sm"
                  aria-hidden="true"
                />
                Documentation de l'API
              </a>
            </li>
            <li class="fr-footer__bottom-item">
              <span class="fr-text--xs fr-text--disabled">
                Frontend&nbsp;<strong>v{{ APP_VERSION }}</strong>
              </span>
            </li>
            <li class="fr-footer__bottom-item">
              <template v-if="loading">
                <span class="fr-text--xs fr-text--disabled">Backend&nbsp;…</span>
              </template>
              <template v-else-if="error || !health">
                <span
                  class="fr-text--xs"
                  style="color: var(--text-default-error);"
                >
                  <span
                    class="fr-icon-close-circle-fill fr-icon--sm"
                    aria-hidden="true"
                  />
                  Backend&nbsp;injoignable
                </span>
              </template>
              <template v-else>
                <span
                  class="fr-text--xs"
                  :style="health.status === 'healthy'
                    ? 'color: var(--text-default-success)'
                    : 'color: var(--text-default-warning)'"
                >
                  <span
                    :class="health.status === 'healthy'
                      ? 'fr-icon-checkbox-circle-fill'
                      : 'fr-icon-warning-fill'"
                    class="fr-icon--sm"
                    aria-hidden="true"
                  />
                  Backend&nbsp;<strong>v{{ health.version }}</strong>&nbsp;—&nbsp;{{ health.status }}
                </span>
              </template>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </footer>
</template>
