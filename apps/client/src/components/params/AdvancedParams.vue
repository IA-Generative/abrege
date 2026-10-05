<script lang="ts" setup>
import CarouselSection from '../CarouselSection.vue'
import ChunksParams from './ChunksParams.vue'
import EntitiesParams from './EntitiesParams.vue'
import QaParams from './QaParams.vue'
import TopicsParams from './TopicsParams.vue'

const sections = [
  {
    title: 'Questions/réponses',
    description: 'Génère automatiquement des questions qu\'un lecteur pourrait se poser sur le document, avec leur réponse tirée du texte. Pratique pour réviser un contenu long ou préparer une FAQ.',
    component: QaParams,
  },
  {
    title: 'Entités et relations',
    description: 'Repère les éléments importants cités dans le document (personnes, organisations, lieux, dates…) et les liens entre eux. Vous pouvez décrire précisément ceux que vous cherchez.',
    component: EntitiesParams,
  },
  {
    title: 'Chunks sémantiques',
    description: 'Découpe le document en passages cohérents par thème et les conserve, pour retrouver ensuite l\'endroit exact d\'où vient une information.',
    component: ChunksParams,
  },
  {
    title: 'Classification des sujets',
    description: 'Rattache le document à un ou plusieurs sujets (ex : recrutement, finance) avec un score de confiance, pour mieux classer vos documents. Vous pouvez imposer vos propres sujets.',
    component: TopicsParams,
  },
]
</script>

<template>
  <CarouselSection
    title="Paramètres avancés"
    :sections="sections"
  >
    <template #default="{ section }">
      <component :is="section.component" />
    </template>
  </CarouselSection>
</template>
