<script lang="ts" setup>

const props = defineProps<{
  fileName: string
  params: { customPrompt: string | null, language: string | null, size: number | null }
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const selectOptions = [
  { value: 'French', text: 'Français (par défaut)' },
  { value: 'English', text: 'Anglais' },
]

const selectedLanguage = computed({
  get: () => props.params.language ?? 'French',
  set: (value: string) => {
    props.params.language = value
  },
})

const selectedSize = computed({
  get: () => props.params.size,
  set: (value: number | null) => {
    props.params.size = value
  },
})

const selectedPrompt = computed({
  get: () => props.params.customPrompt,
  set: (value: string | null) => {
    props.params.customPrompt = value
  },
})

function onEsc (e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', onEsc))
onBeforeUnmount(() => window.removeEventListener('keydown', onEsc))
</script>

<template>
  <div
    class="modal-overlay"
    @click.self="emit('close')"
  >
    <div
      class="modal"
      @click.stop
    >
      <div class="modal-header">
        <button
          class="fr-btn--close fr-btn"
          aria-label="Fermer la fenêtre modale"
          @click="emit('close')"
        >
          Fermer
        </button>
      </div>

      <div class="modal-content fr-px-4w fr-pb-2w">
        <h1 class="fr-h4 fr-mb-1w">
          <span
            class="fr-icon-settings-5-line fr-mr-1w"
            aria-hidden="true"
          />
          Paramètres du fichier
        </h1>
        <p class="fr-text--sm fr-text-mention--grey fr-mb-3w">
          <span
            class="fr-icon-file-line fr-mr-1v"
            aria-hidden="true"
          />
          {{ fileName }}
        </p>
        <p class="fr-hint-text fr-mb-3w">
          Ces paramètres s'appliquent uniquement à ce fichier. Laissez une valeur vide pour utiliser les paramètres globaux.
        </p>

        <div class="fr-mb-3w">
          <DsfrSelect
            v-model="selectedLanguage"
            label="Langue du résumé"
            :options="selectOptions"
          />
        </div>
        <div class="fr-mb-3w">
          <DsfrInput
            v-model="selectedSize"
            label="Nombre de mots"
            label-visible
            placeholder="4000 (par défaut)"
            hint="Le résumé contiendra un nombre de mots approximatif"
            type="number"
          />
        </div>
        <div class="fr-mb-3w">
          <DsfrInput
            v-model="selectedPrompt"
            :label-visible="true"
            :is-textarea="true"
            label="Instruction spécifique"
            hint='Ex : "utilise un ton très formel" ou "liste les points importants"'
          />
        </div>
      </div>

      <div class="modal-footer fr-px-4w fr-pb-4w">
        <DsfrButton
          label="Valider"
          @click="emit('close')"
        />
      </div>
    </div>
  </div>
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
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 4px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.5rem 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
}

:deep(textarea) {
  min-height: 100px;
}
</style>
