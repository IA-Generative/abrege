<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import { ref, computed } from 'vue'

type TaskModel = components['schemas']['TaskModel']

const props = defineProps<{
  results: { filename: string, task: TaskModel }[]
  initialIndex?: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'reGenerate'): void
}>()

const currentIndex = ref(props.initialIndex ?? 0)

const currentResult = computed(() => props.results[currentIndex.value])

function prev () {
  if (currentIndex.value > 0) currentIndex.value--
}
function next () {
  if (currentIndex.value < props.results.length - 1) currentIndex.value++
}

function onEsc (e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', onEsc))
onBeforeUnmount(() => window.removeEventListener('keydown', onEsc))
</script>

<template>
  <Teleport to="body">
    <div
      class="modal-overlay"
      @click.self="emit('close')"
    >
      <div
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resume-modal-title"
        @click.stop
      >
        <!-- Header -->
        <div class="modal-header">
          <h2
            id="resume-modal-title"
            class="fr-h5 fr-mb-0"
          >
            Résultats
          </h2>
          <button
            class="fr-btn--close fr-btn"
            aria-label="Fermer la fenêtre modale"
            @click="emit('close')"
          >
            Fermer
          </button>
        </div>

        <!-- File tabs navigation -->
        <div
          v-if="results.length > 1"
          class="modal-tabs"
        >
          <button
            v-for="(item, index) in results"
            :key="index"
            class="tab-btn"
            :class="{ 'tab-btn--active': index === currentIndex }"
            :title="item.filename"
            @click="currentIndex = index"
          >
            <span class="fr-icon-file-line fr-mr-1v" aria-hidden="true" />
            <span class="tab-btn-label">{{ item.filename }}</span>
          </button>
        </div>

        <!-- File name for single result -->
        <div
          v-else
          class="modal-single-filename"
        >
          <div class="modal-filename-row">
            <span class="fr-icon-file-line fr-mr-1v" aria-hidden="true" />
            <span>{{ results[0]?.filename }}</span>
          </div>
          <div
            v-if="currentResult?.task"
            class="modal-filename-meta fr-text--sm fr-mt-1v"
          >
            <span class="fr-mr-3w">
              <strong>ID :</strong>
              <code style="font-size: 0.8em">{{ currentResult.task.id }}</code>
            </span>
            <span>
              <strong>Type :</strong> {{ currentResult.task.type ?? '—' }}
            </span>
          </div>
        </div>

        <!-- Result content -->
        <div class="modal-body">
          <ResumeResult
            v-if="currentResult"
            :resume-result="currentResult.task"
            @re-generate="emit('reGenerate')"
          />
        </div>

        <!-- Footer navigation -->
        <div
          v-if="results.length > 1"
          class="modal-footer"
        >
          <DsfrButton
            :disabled="currentIndex === 0"
            label="Précédent"
            secondary
            icon="ri:arrow-left-line"
            @click="prev"
          />
          <span class="modal-footer-count">{{ currentIndex + 1 }} / {{ results.length }}</span>
          <DsfrButton
            :disabled="currentIndex === results.length - 1"
            label="Suivant"
            secondary
            icon-right
            icon="ri:arrow-right-line"
            @click="next"
          />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 4px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem 0.75rem;
  border-bottom: 1px solid var(--border-default-grey);
}

.modal-tabs {
  display: flex;
  gap: 0;
  overflow-x: auto;
  border-bottom: 1px solid var(--border-default-grey);
}

.tab-btn {
  display: flex;
  align-items: center;
  padding: 0.6rem 1rem;
  font-size: 0.875rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  color: var(--text-mention-grey);
  flex-shrink: 0;
  max-width: 180px;
}

.tab-btn--active {
  border-bottom-color: var(--border-plain-blue-france);
  color: var(--text-active-blue-france);
  font-weight: 600;
}

.tab-btn-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-single-filename {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  color: var(--text-mention-grey);
  border-bottom: 1px solid var(--border-default-grey);
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-default-grey);
}

.modal-footer-count {
  font-size: 0.875rem;
  color: var(--text-mention-grey);
}
</style>
