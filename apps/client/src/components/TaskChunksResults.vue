<script setup lang="ts">
import { computed, ref, watch } from 'vue'
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

// Loaded in one page (rather than the store's default 20/page) so the search box below
// searches the whole task's chunks, not just whatever page happens to be on screen.
const PAGE_SIZE = 200

const searchQuery = ref('')

const headers = ['Page', 'Chunk', 'Position', 'Texte', 'Modèle']

const filteredChunks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) { return abrege.chunks }
  return abrege.chunks.filter(c => c.text.toLowerCase().includes(q))
})

const rows = computed(() =>
  filteredChunks.value.map(c => [
    c.page != null ? String(c.page) : '—',
    String(c.chunk_index),
    String(c.position),
    c.text.length > 120 ? `${c.text.slice(0, 120)}…` : c.text,
    c.model_name ?? '—',
  ]),
)

const pageCount = computed(() => Math.max(1, Math.ceil(abrege.chunksTotal / abrege.chunksPageSize)))

function loadPage (page: number) {
  abrege.fetchChunks(props.taskId, page, PAGE_SIZE)
}

function close () {
  emit('close')
}

watch(
  () => props.opened,
  (opened) => {
    if (opened) {
      searchQuery.value = ''
      loadPage(1)
    }
  },
)
</script>

<template>
  <DsfrModal
    v-if="opened"
    :opened="opened"
    title="Chunks"
    size="xl"
    @close="close"
  >
    <div class="chunks-modal-subtitle-row">
      <p class="fr-text--sm fr-text-mention--grey chunks-modal-subtitle">
        Tâche {{ taskId }} — {{ abrege.chunksTotal }} chunk(s) sémantique(s)
      </p>
      <ExtractionStatusBadge
        :status="status"
        label="Extraction"
      />
    </div>

    <div
      v-if="abrege.chunksLoading"
      class="fr-mt-4w"
    >
      <p class="fr-text--sm">
        Chargement…
      </p>
    </div>

    <div
      v-else-if="abrege.chunks.length === 0"
      class="fr-alert fr-alert--info fr-mt-2w"
    >
      <p>Aucun chunk disponible pour cette tâche.</p>
    </div>

    <template v-else>
      <DsfrSearchBar
        v-model="searchQuery"
        label="Rechercher dans les chunks"
        placeholder="Rechercher un texte…"
        class="fr-mt-2w"
      />

      <p
        v-if="rows.length === 0"
        class="fr-text--sm fr-text-mention--grey fr-mt-2w"
      >
        Aucun résultat pour « {{ searchQuery }} ».
      </p>
      <DsfrTable
        v-else
        title="Chunks sémantiques"
        :headers="headers"
        :rows="rows"
        class="fr-mt-2w"
      />

      <div
        v-if="pageCount > 1"
        class="chunks-modal-pagination fr-mt-2w"
      >
        <DsfrButton
          label="Précédent"
          icon="ri-arrow-left-s-line"
          tertiary
          size="sm"
          :disabled="abrege.chunksPage <= 1"
          @click="loadPage(abrege.chunksPage - 1)"
        />
        <span class="fr-text--sm">Page {{ abrege.chunksPage }} / {{ pageCount }}</span>
        <DsfrButton
          label="Suivant"
          icon="ri-arrow-right-s-line"
          icon-right
          tertiary
          size="sm"
          :disabled="abrege.chunksPage >= pageCount"
          @click="loadPage(abrege.chunksPage + 1)"
        />
      </div>
    </template>
  </DsfrModal>
</template>

<style scoped>
.chunks-modal-subtitle-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}
.chunks-modal-subtitle {
  margin-top: 0;
  margin-bottom: 0;
}
.chunks-modal-pagination {
  display: flex;
  align-items: center;
  gap: 1rem;
}
</style>
