<script setup lang="ts">
import { computed, ref } from 'vue'
import CarouselSection from './CarouselSection.vue'
import TaskChunksResults from './TaskChunksResults.vue'
import TaskEntitiesResults from './TaskEntitiesResults.vue'
import TaskQAResults from './TaskQAResults.vue'
import TaskTopicsResults from './TaskTopicsResults.vue'

const props = defineProps<{
  taskId: string
  parameters?: {
    extract_qa?: boolean
    extract_entities?: boolean
    extract_chunks?: boolean
    classify_topics?: boolean
  } | null
  qaEntitiesStatus?: string | null
  relationshipsStatus?: string | null
  topicsStatus?: string | null
}>()

const opened = ref(false)

// Each side extraction is opt-in per task (see ParamsResume.vue): only offer what was requested.
const sections = computed(() => {
  const result = []
  if (props.parameters?.classify_topics) {
    result.push({
      title: 'Classification des sujets',
      description: 'Les grands thèmes du document avec un score de confiance et une explication pour chacun, pour mieux classer vos documents.',
      component: TaskTopicsResults,
      props: { taskId: props.taskId, status: props.topicsStatus },
    })
  }
  if (props.parameters?.extract_qa) {
    result.push({
      title: 'Questions / réponses',
      description: 'Les questions qu\'un lecteur pourrait se poser sur le document, avec la réponse tirée du texte et l\'endroit d\'où elle vient.',
      component: TaskQAResults,
      props: { taskId: props.taskId, status: props.qaEntitiesStatus },
    })
  }
  if (props.parameters?.extract_entities) {
    result.push({
      title: 'Entités et relations',
      description: 'Les éléments importants repérés dans le document (personnes, dates, montants…) et les liens entre eux, en liste ou en graphe.',
      component: TaskEntitiesResults,
      props: { taskId: props.taskId, entitiesStatus: props.qaEntitiesStatus, relationshipsStatus: props.relationshipsStatus },
    })
  }
  if (props.parameters?.extract_chunks) {
    result.push({
      title: 'Chunks sémantiques',
      description: 'Le document découpé en passages cohérents par thème, pour retrouver l\'endroit exact d\'une information.',
      component: TaskChunksResults,
      props: { taskId: props.taskId, status: props.qaEntitiesStatus },
    })
  }
  return result
})
</script>

<template>
  <div v-if="sections.length > 0">
    <DsfrButton
      label="Analyse du document"
      icon="ri-list-check-2"
      secondary
      size="sm"
      @click="opened = true"
    />
    <DsfrModal
      v-if="opened"
      :opened="opened"
      title="Analyse du document"
      size="xl"
      @close="opened = false"
    >
      <CarouselSection
        title="Analyse du document"
        :sections="sections"
        :collapsible="false"
      >
        <template #default="{ section }">
          <component
            :is="section.component"
            v-bind="section.props"
          />
        </template>
      </CarouselSection>
    </DsfrModal>
  </div>
</template>
