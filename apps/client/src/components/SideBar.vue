<script lang="ts" setup>
import type { DsfrTileProps } from '@gouvminint/vue-dsfr'
import { RouterLink } from 'vue-router'
import ComminitySVG from '@/assets/pictograms/community.svg'
import PenSVG from '@/assets/pictograms/pen.svg'
import { USER_REVIEW_URL } from '@/utils/constants'
import { PORTAIL_URL, TCHAP_CANAL_URL } from '@/utils/constants'
import { openLink } from '@/utils/methods'

defineProps({
  otherTools: {
    name: 'otherTools',
    type: Array as () => DsfrTileProps[],
    required: true,
    default: () => [
      {
        title: 'Converser avec le Chatbot',
        to: '/webui',
        imgSrc: ComminitySVG,
      },
      {
        title: 'Résumer un texte',
        to: '/resume',
        imgSrc: PenSVG,
      },
    ],
  },
})

const donneMonAvisTitle: string = 'Aidez-nous à améliorer MIrAI'
const donneMonAvisDescription: string = 'Testez les outils de MIrAI, rapportez un bug ou suggérez des améliorations !'
const donneMonAvisButtonText: string = 'Je donne mon avis'
const donneMonAvisButtonUrl: string = USER_REVIEW_URL

const donneMonAvisButton = {
  label: donneMonAvisButtonText,
  icon: 'ri-external-link-line',
  iconRight: true,
  onClick: () => {
    openLink(donneMonAvisButtonUrl)
  },
}
</script>

<template>
  <div class="side-bar__container">
    <div class="flex flex-col gap-6 md:gap-8">
      <div class="side-bar__about">
        <h3 class="side-bar__about__title">
          À savoir sur MIrAI
        </h3>
        <p class="side-bar__cgu__text">
          Veuillez impérativement consulter les <a
            class="side-bar__about__text"
            :href="`${PORTAIL_URL}/cgu`"
            target="_blank"
          >
            conditions d'utilisation
          </a> de MIrAI.
        </p>
        <p>
          Pour vous former et utiliser au mieux les fonctionnalités des outils de MIrAI, rendez-vous sur <a
            class="side-bar__about__text"
            :href="`${PORTAIL_URL}/faq/introduction`"
            target="_blank"
          >
            Introduction et acculturation à l'IA
          </a>.
        </p>
        <p>
          Une question ? RDV sur notre <a
            :href="TCHAP_CANAL_URL"
            target="_blank"
          >canal Tchap</a> pour échanger avec la communauté MIrAI.
        </p>
      </div>
      <DsfrCallout
        :title="donneMonAvisTitle"
        :content="donneMonAvisDescription"
        :button="donneMonAvisButton"
      />
    </div>
    <div class="flex flex-col gap-8">
      <h4>Essayez également...</h4>
      <div
        v-for="(tool, index) in $props.otherTools"
        :key="index"
        class="tools__container__item"
      >
        <DsfrTile
          :key="index"
          :title="tool.title"
          :to="PORTAIL_URL + tool.to"
          :icon="false"
          horizontal
          :img-src="tool.imgSrc"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
h4{
  margin-bottom: 0;
}
.side-bar__container{
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-bottom: 2rem;
}
.side-bar__about{
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.5rem;
  border: 1px solid var(--border-default-grey);
}
.side-bar__about p{
  font-size: 0.925rem;
  margin-bottom: 0;
}
.side-bar__about__title{
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0;
}
.side-bar__about__text{
  font-weight: 700;
  color: var(--text-title-blue-france);
}

.side-bar__cgu__text{
  font-weight: 700;
}
:deep(.fr-tile__title){
  font-size: 1rem;
}
:deep(.fr-btn){
  text-wrap: nowrap;
}
:deep(.fr-callout){
  margin-bottom: 0;
}

@media (min-width: 576px) {

}

@media (min-width: 768px) {

}

@media (min-width: 992px) {

}

@media (min-width: 1248px) {
  .side-bar__container{
    display: flex;
    flex-direction: column;
    gap: 2rem;
    width: 35%;
    margin: 2.5rem 0;
  }
  .side-bar__about{
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1.5rem;
    border: 1px solid var(--border-default-grey);
  }
  .side-bar__about p{
    font-size: 0.925rem;
    margin-bottom: 0;
  }
  .side-bar__about__title{
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0;
  }
  .side-bar__about__text{
    font-weight: 700;
    color: var(--text-title-blue-france);
  }
}
</style>
