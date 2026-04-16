<script lang="ts" setup>
interface LabelDefinition {
  label: string
  definition: string
}

const labels = ref<LabelDefinition[]>([])
const currentLabel = ref('')
const currentDefinition = ref('')
const labelError = ref('')
const definitionError = ref('')
const files = ref<File[]>([])
const classificationResult = ref<{ label: string, confidence: number }[] | null>(null)
const isGenerating = ref(false)

const uploadLabel = 'Ajouter des fichiers à classifier'
const uploadHint = 'Taille maximale : 200MB par fichier. Formats supportés : PDF, DOC, DOCX, PPTX, ODT, ODP, TXT.'
const uploadAccept = ['.pdf', '.docx', '.pptx', '.txt', '.odt', '.odp', '.doc']

function handleFileChange (fileList: FileList | File[]) {
  const fileArray = Array.isArray(fileList) ? fileList : Array.from(fileList)
  if (fileArray.length) {
    files.value = fileArray
  }
}

function removeFile (index: number) {
  files.value = files.value.filter((_: File, i: number) => i !== index)
}

function addLabel () {
  labelError.value = ''
  definitionError.value = ''
  const label = currentLabel.value.trim()
  const definition = currentDefinition.value.trim()
  if (!label) {
    labelError.value = 'Le nom du label est requis.'
  }
  if (!definition) {
    definitionError.value = 'La définition est requise pour chaque label.'
  }
  if (!label || !definition) return
  labels.value.push({ label, definition })
  currentLabel.value = ''
  currentDefinition.value = ''
}

function removeLabel (index: number) {
  labels.value.splice(index, 1)
}

async function onSubmit () {
  if (!labels.value.length || !files.value.length) return
  isGenerating.value = true
  // Mock : simuler un délai + résultat
  await new Promise(resolve => setTimeout(resolve, 1500))
  classificationResult.value = labels.value.map(l => ({
    label: l.label,
    confidence: Math.round(Math.random() * 100),
  })).sort((a, b) => b.confidence - a.confidence)
  isGenerating.value = false
}

function newSearch () {
  classificationResult.value = null
  files.value = []
  labels.value = []
}
</script>

<template>
  <form
    class="tab-container"
    @submit.prevent
  >
    <!-- Résultat -->
    <div
      v-if="classificationResult"
      class="classification-result"
    >
      <h3>Résultat de la classification</h3>
      <ul class="result-list">
        <li
          v-for="(item, index) in classificationResult"
          :key="index"
          class="result-item"
        >
          <span class="result-label">{{ item.label }}</span>
          <div class="result-bar-container">
            <div
              class="result-bar"
              :style="{ width: item.confidence + '%' }"
            />
          </div>
          <span class="result-confidence">{{ item.confidence }}%</span>
        </li>
      </ul>
      <DsfrButton
        label="Nouvelle classification"
        secondary
        @click="newSearch"
      />
    </div>

    <!-- Formulaire -->
    <template v-else>
      <!-- Labels -->
      <div class="labels-section">
        <h4 class="labels-title">
          <span class="fr-icon-price-tag-3-line labels-title-icon" aria-hidden="true" />
          Définir les catégories
        </h4>
        <p class="fr-hint-text">
          Ajoutez au moins deux labels avec leur définition pour classifier vos documents.
        </p>

        <div class="label-card">
          <div class="label-card-inputs">
            <DsfrInputGroup
              :error-message="labelError"
              class="label-input-field"
            >
              <DsfrInput
                v-model="currentLabel"
                label="Nom du label"
                label-visible
                placeholder="Ex : Urgent"
                @focus="labelError = ''"
              />
            </DsfrInputGroup>
            <DsfrInputGroup
              :error-message="definitionError"
              class="definition-input-field"
            >
              <DsfrInput
                v-model="currentDefinition"
                label="Définition (obligatoire)"
                label-visible
                :is-textarea="true"
                placeholder="Ex : Le document traite d'un sujet nécessitant une action immédiate"
                @focus="definitionError = ''"
              />
            </DsfrInputGroup>
          </div>
          <button
            type="button"
            class="label-add-btn fr-btn fr-btn--icon-left fr-icon-add-line"
            @click="addLabel"
          >
            Ajouter le label
          </button>
        </div>

        <TransitionGroup
          name="label-list"
          tag="ul"
          class="label-list"
        >
          <li
            v-for="(item, index) in labels"
            :key="item.label + '-' + index"
            class="label-list-item"
          >
            <div class="label-list-row">
              <div class="label-list-info">
                <span class="label-list-name">
                  <span class="fr-icon-price-tag-3-line label-tag-icon" aria-hidden="true" />
                  {{ item.label }}
                </span>
                <span class="label-list-definition">{{ item.definition }}</span>
              </div>
              <button
                type="button"
                class="label-remove-btn fr-btn fr-btn--tertiary-no-outline fr-btn--icon-left fr-icon-delete-line"
                :disabled="isGenerating"
                @click="removeLabel(index)"
              >
                Retirer
              </button>
            </div>
          </li>
        </TransitionGroup>
      </div>

      <!-- Fichiers à classifier -->
      <DsfrFileUpload
        :label="uploadLabel"
        :hint="uploadHint"
        :accept="uploadAccept"
        multiple
        @change="handleFileChange"
      />
      <ul
        v-if="files.length"
        class="file-list"
      >
        <li
          v-for="(file, index) in files"
          :key="index"
          class="file-list-item"
        >
          <div class="file-list-row">
            <span class="file-list-name">{{ file.name }}</span>
            <DsfrButton
              size="sm"
              label="Retirer"
              secondary
              :disabled="isGenerating"
              @click="removeFile(index)"
            />
          </div>
        </li>
      </ul>

      <!-- Génération -->
      <div
        v-if="isGenerating"
        class="is-generating-container"
      >
        <DsfrAlert
          type="info"
          description="Classification en cours..."
        />
      </div>

      <DsfrButton
        size="lg"
        label="Classifier"
        :disabled="isGenerating || labels.length < 2 || !files.length"
        @click="onSubmit"
      />
    </template>
  </form>
</template>

<style scoped>
.labels-section {
  border: none;
  padding: 0;
  margin: 0;
}

.labels-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.125rem;
}

.labels-title-icon {
  color: var(--blue-france-sun-113-625, #000091);
}

.label-card {
  margin-top: 1rem;
  padding: 1.25rem;
  background: var(--blue-france-975-75, #f5f5fe);
  border-radius: 8px;
  border: 1px solid var(--border-default-grey, #e5e5e5);
}

.label-card-inputs {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.label-input-field {
  flex: 1;
}

.definition-input-field {
  flex: 2;
}

.label-add-btn {
  background-color: var(--blue-france-sun-113-625, #000091);
  color: white;
}

.label-list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.label-list-item {
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--border-default-grey, #e5e5e5);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.label-list-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* TransitionGroup animations */
.label-list-enter-active {
  transition: all 0.3s ease;
}
.label-list-leave-active {
  transition: all 0.2s ease;
}
.label-list-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.label-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.label-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.label-list-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.label-list-name {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--blue-france-sun-113-625, #000091);
}

.label-tag-icon {
  font-size: 0.875rem;
}

.label-list-definition {
  font-size: 0.85rem;
  color: var(--text-mention-grey, #666);
  line-height: 1.4;
}

.label-remove-btn {
  flex-shrink: 0;
  color: var(--text-default-error, #ce0500);
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-list-item {
  padding: 0.5rem 0.75rem;
  background: var(--grey-975-75, #f6f6f6);
  border-radius: 4px;
}

.file-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.file-list-name {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

/* Résultat */
.classification-result {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.classification-result h3 {
  margin: 0;
}

.result-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.result-label {
  font-weight: bold;
  min-width: 120px;
}

.result-bar-container {
  flex: 1;
  height: 1.25rem;
  background: var(--grey-975-75, #f6f6f6);
  border-radius: 4px;
  overflow: hidden;
}

.result-bar {
  height: 100%;
  background: var(--blue-france-sun-113-625, #000091);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.result-confidence {
  min-width: 3rem;
  text-align: right;
  font-weight: bold;
}
</style>
