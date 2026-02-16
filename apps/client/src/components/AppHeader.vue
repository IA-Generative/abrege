<script setup lang="ts">
import type { DsfrHeaderProps } from '@gouvminint/vue-dsfr'
import { computed } from 'vue'
import { getKeycloak } from '@/utils/keycloak'

const keycloak = getKeycloak()
const isLoggedIn = computed(() => keycloak.authenticated)

const whenLoggedLinks: DsfrHeaderProps['quickLinks'] = [
  {
    label: 'Se déconnecter',
    icon: 'fr-icon-logout-box-r-line',
    to: '/logout',
  },
]

const whenNotLoggedLinks: DsfrHeaderProps['quickLinks'] = [
  {
    label: 'Se connecter',
    to: '/login',
    icon: 'fr-icon-user-fill',
  },
]

const quickLinks = computed<DsfrHeaderProps['quickLinks']>(() => {
  if (isLoggedIn.value) {
    return whenLoggedLinks
  }
  else {
    return whenNotLoggedLinks
  }
})

function redirectTo (url: string): void {
  window.open(url, '_blank', 'noopener, noreferrer')
}

const serviceTitle = 'Résumer un texte'
const serviceDescription = 'Produire une synthèse de documents volumineux'
const logoText = ['Ministère', 'de l’intérieur']
</script>

<template>
  <DsfrHeader
    :service-title="serviceTitle"
    :service-description="serviceDescription"
    :quick-links="quickLinks"
    :logo-text="logoText"
  >
    <template #before-quick-links>
      <DsfrDropdown
        :main-button="{
          label: 'Applications MIrAI',
          icon: 'fr-icon-grid-fill',
          size: 'sm',
        }"
        class="max-sm:self-end"
        :buttons="[
          {
            label: 'Portail MIrAI',
            onClick: () => redirectTo('https://mirai.interieur.gouv.fr/'),
          },
          {
            label: 'MIrAI Chat',
            onClick: () => redirectTo('https://chat.mirai.interieur.gouv.fr/'),
          },
          {
            label: 'MIrAI Compte rendu',
            onClick: () => redirectTo('https://compte-rendu.mirai.interieur.gouv.fr/'),
          },
          {
            label: 'OCR',
            onClick: () => redirectTo('https://ocr.mirai.interieur.gouv.fr/'),
          },
        ]"
      />
    </template>
  </DsfrHeader>
</template>

<style scoped>
:deep() div.fr-notice__body > p {
  display: flex;
  flex-direction: column;
}

/* Breakpoint used in dsfr, close to tw md: */
@media (min-width: 48em) {
  :deep() div.fr-notice__body > p {
    display: flex;
    flex-direction: row;
  }

  :deep() .fr-notice__title {
    margin-bottom: 0;
  }
}

:deep(.fr-badge) {
  background-color: #e8edff;
  color: #0063cb;
}

:deep(.fr-accordion__btn) {
  display: inline-flex;
  align-items: center;
}

:deep(.fr-accordion__btn[aria-expanded='true']) {
  background-color: var(--background-open-blue-france);
  color: var(--background-action-high-blue-france);
}

:deep(.fr-accordion__btn[aria-expanded='true']:hover) {
  background-color: var(--background-open-blue-france-hover);
}

:deep(.fr-accordion__btn[aria-expanded='true']):active {
  background-color: var(--background-open-blue-france-active);
}

/* Prevent the displaying of the icon for external links on the left of the buttons */
:deep(.fr-btn[target='_blank']::after) {
  display: none !important; /* enlève l'icône à droite */
}

/* Recreate the icon for external links, but puts it on the right of the button */
:deep(.fr-btn[target='_blank']::before),
:deep(.fr-accordion__btn::before) {
  content: '';
  display: inline-block;
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
  flex-shrink: 0;

  background-color: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zM5 5h6V3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-6h-2v6H5V5z'/%3E%3C/svg%3E")
    no-repeat center / contain;
}
</style>
