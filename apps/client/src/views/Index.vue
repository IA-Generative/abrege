<script setup lang="ts">
import DocumentDownload from '@gouvfr/dsfr/dist/artwork/pictograms/document/document-download.svg'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ComminitySVG from '@/assets/pictograms/community.svg'
import DocumentSearch from '@/assets/pictograms/document-search.svg'
import ResumeCard from '@/assets/resume-card.png'

import CopiedTextTab from '@/components/CopiedTextTab.vue'
import ResumeInfoBulle from '@/components/ResumeInfoBulle.vue'
import UploadDocumentTab from '@/components/UploadDocumentTab.vue'
import UrlTab from '@/components/UrlTab.vue'
import TaskTab from '@/components/TaskTab.vue'

const TAB_ROUTES = ['text', 'url', 'document', 'tasks'] as const

const route = useRoute()
const router = useRouter()

const screenWidth = ref(window.innerWidth)
const isMobile = ref(screenWidth.value < 768)
const firstTabTitle = ref(isMobile.value ? 'd\'un texte' : 'd\'un texte copié/collé')

const tabs = ref([
  { label: firstTabTitle, slot: 'tab-0-content' },
  { label: 'd\'une URL', slot: 'tab-1-content' },
  { label: 'd\'un document téléchargé', slot: 'tab-2-content' },
  { label: 'des tâches', slot: 'tab-3-content' },
])

const activeTab = computed({
  get: () => {
    const idx = TAB_ROUTES.indexOf(route.params.tab as any)
    return idx >= 0 ? idx : 0
  },
  set: (idx: number) => {
    router.replace({ name: 'resume-tab', params: { tab: TAB_ROUTES[idx] } })
  },
})

const myOtherTools = ref([
  {
    title: 'Converser avec le Chatbot',
    to: '/outils-mirai/chat',
    imgSrc: ComminitySVG,
  },
  {
    title: 'Reconnaître un texte scanné',
    to: '/outils-mirai/ocr',
    imgSrc: DocumentSearch,
  },
  {
    title: 'Faire un compte rendu',
    to: '/outils-mirai/compte-rendu',
    imgSrc: DocumentDownload,
  },
])
</script>

<template>
  <div class="main-page">
    <SideBar :other-tools="myOtherTools" />
    <div class="main-page__container">
      <div class="page-title">
        <h1 class="flex gap-3">
          <!-- TODO: Change SVG with dsfr pictogram (when they update the lib and add the pictogram) -->
          <img
            class="hidden md:block"
            src="@/assets/pictograms/pen.svg"
            alt="pen-pictogram"
          >
          <span>Résumer un texte à partir...</span>
        </h1>
      </div>
      <div>
        <CustomTabs v-model="activeTab" :tabs-data="tabs">
          <template #tab-0-content>
            <ResumeInfoBulle />
            <CopiedTextTab />
          </template>
          <template #tab-1-content>
            <ResumeInfoBulle />
            <UrlTab />
          </template>
          <template #tab-2-content>
            <ResumeInfoBulle />
            <UploadDocumentTab />
          </template>
          <template #tab-3-content>
            <ResumeInfoBulle />
            <TaskTab />
          </template>
        </CustomTabs>
      </div>
      <!-- FIXME : Decomment for authentication
      v-if="isLoggedIn"
      <div v-else>
        <NotAuthenticated />
      </div>
      -->
      <CustomCard
        :img-src="ResumeCard"
        img-alt="image de stylo sur feuille de papier"
        title="Comment utiliser “Résumer un texte” ?"
        description="Sélectionnez l'onglet correspondant à la provenance de votre texte à résumer. Vous pouvez résumé un texte à partir :"
        infos="
            <ul>
              <li>
                d'un texte copié-collé ;
              </li>
              <li>
                d'une URL (lien internet) ;
              </li>
              <li>
                d'un document téléchargé.
              </li>
            </ul>
            <p class='text-sm! mt-4!'>Vous pouvez ensuite régler les paramètres que vous souhaitez appliquer à la génération de votre résumé.</p>
            <p class='text-sm!'>Cliquez sur “Générer”, pour que votre texte soit résumé par l’intelligence artificielle.</p>
          "
        hint="<span style='font-weight:bold'>💡 J'essaie 'Résumer un texte' :</span> tentez de générer un résumé de texte de loi que vous trouvez long en copiant le contenu textuel dans l'outil !"
      />
    </div>
  </div>
</template>

<style>
.tab-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.is-generating-container{
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

li {
  list-style-type: '- ';
  line-height: 1.5rem;
}

.page-title {
  margin-top: 35px;
}

.page-title img {
  vertical-align: middle;
}
</style>
