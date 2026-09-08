<script setup lang="ts">
import { computed, watch } from 'vue'
import { useAbregeStore } from '@/stores/abrege'

const props = defineProps<{
  opened: boolean
  taskId: string
  status?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const abrege = useAbregeStore()

const headers = ['Question', 'Réponse', 'Page', 'Chunk', 'Texte source', 'Modèle']

const rows = computed(() =>
  abrege.qaItems.map(item => [
    item.question,
    item.answer,
    item.page != null ? String(item.page) : '—',
    String(item.chunk_index),
    item.source_text.length > 90 ? `${item.source_text.slice(0, 90)}…` : item.source_text,
    item.model_name ?? '—',
  ]),
)

const pageCount = computed(() => Math.max(1, Math.ceil(abrege.qaItemsTotal / abrege.qaItemsPageSize)))

function loadPage (page: number) {
  abrege.fetchQAItems(props.taskId, page, abrege.qaItemsPageSize)
}

function close () {
  emit('close')
}

watch(
  () => props.opened,
  (opened) => {
    if (opened) loadPage(1)
  },
)
</script>

<template>
  <DsfrModal
    v-if="opened"
    :opened="opened"
    title="Questions / Réponses"
    size="xl"
    @close="close"
  >
    <div class="qa-modal-subtitle-row">
      <p class="fr-text--sm fr-text-mention--grey qa-modal-subtitle">
        Tâche {{ taskId }} — {{ abrege.qaItemsTotal }} paire(s) générée(s)
      </p>
      <ExtractionStatusBadge :status="status" label="Extraction" />
    </div>

    <div v-if="abrege.qaItemsLoading" class="fr-mt-4w">
      <p class="fr-text--sm">
        Chargement…
      </p>
    </div>

    <div v-else-if="abrege.qaItems.length === 0" class="fr-alert fr-alert--info fr-mt-2w">
      <p>Aucune question/réponse disponible pour cette tâche.</p>
    </div>

    <template v-else>
      <DsfrTable
        title="Questions et réponses extraites"
        :headers="headers"
        :rows="rows"
        class="fr-mt-2w"
      />

      <div v-if="pageCount > 1" class="qa-modal-pagination fr-mt-2w">
        <DsfrButton
          label="Précédent"
          icon="ri-arrow-left-s-line"
          tertiary
          size="sm"
          :disabled="abrege.qaItemsPage <= 1"
          @click="loadPage(abrege.qaItemsPage - 1)"
        />
        <span class="fr-text--sm">Page {{ abrege.qaItemsPage }} / {{ pageCount }}</span>
        <DsfrButton
          label="Suivant"
          icon="ri-arrow-right-s-line"
          icon-right
          tertiary
          size="sm"
          :disabled="abrege.qaItemsPage >= pageCount"
          @click="loadPage(abrege.qaItemsPage + 1)"
        />
      </div>
    </template>
  </DsfrModal>
</template>

<style scoped>
.qa-modal-subtitle-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}
.qa-modal-subtitle {
  margin-top: 0;
  margin-bottom: 0;
}
.qa-modal-pagination {
  display: flex;
  align-items: center;
  gap: 1rem;
}
</style>
