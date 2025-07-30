<script lang="ts" setup>
import type { components } from '@/api/types/api.schema'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { onMounted, ref } from 'vue'
import useToaster from '@/composables/use-toaster'
import { useAbregeStore } from '@/stores/abrege'

type TaskModel = components['schemas']['TaskModel']

const props = defineProps({
  resumeResult: {
    name: 'resumeResult',
    type: Object as () => TaskModel,
    required: true,
  },
})

const emit = defineEmits(['inFocus', 'reGenerate'])

const { addErrorMessage } = useToaster()

const tags = ref<string[]>([
  'Synthèse',
  props.resumeResult.parameters?.language === 'French'
    ? 'Français'
    : props.resumeResult.parameters?.language === 'English'
      ? 'Anglais'
      : props.resumeResult.parameters?.language || '',
  // `${props.resumeResult.output.word_count} mots`,
]) // Tags du résumé

const speech = ref<SpeechSynthesisUtterance | null>(null) // Stocke l'instance de SpeechSynthesisUtterance
const isSpeaking = ref<boolean>(false)
const textQueue = ref<string[]>([]) // File d’attente des textes à lire
const currentIndex = ref<number>(0) // Index du texte en cours de lecture

// Vérifie si l'output contient un résumé
function hasSummary (output: TaskModel['output']): output is components['schemas']['SummaryModel'] {
  return !!(output as components['schemas']['SummaryModel'])?.summary?.length
}

function speakMultipleTexts (texts: string[]) {
  if (!texts.length) {
    addErrorMessage({
      title: 'Erreur',
      description: 'Aucun texte à lire.',
    })
    return
  }

  stopSpeech() // Arrêter toute lecture en cours
  textQueue.value = texts // Charger la file d’attente
  currentIndex.value = 0
  speakNextText()
}

function speakNextText () {
  if (speech.value && currentIndex.value < textQueue.value.length) {
    speech.value.text = textQueue.value[currentIndex.value]
    window.speechSynthesis.speak(speech.value)
    isSpeaking.value = true
  }
}
function stopSpeech () {
  window.speechSynthesis.cancel()
  isSpeaking.value = false
}
function reGenerate () {
  stopSpeech()
  emit('reGenerate')
}
function copyOnClipboard () {
  stopSpeech()
  if (hasSummary(props.resumeResult.output)) {
    navigator.clipboard.writeText(props.resumeResult.output.summary)
  }
  else {
    addErrorMessage({
      title: 'Erreur',
      description: 'Le résumé est vide, rien à copier.',
    })
  }
}
function renderMarkdown (markdownText: string) {
  const html = marked.parse(markdownText) as string
  return DOMPurify.sanitize(html)
}

onMounted (() => {
  // Initialise l'objet de synthèse vocale une seule fois
  const abregeStore = useAbregeStore()
  const { paramsValue } = abregeStore
  const speechLanguage = paramsValue.selectOptionSelected === 'French' ? 'fr-FR' : 'en-EN'
  speech.value = new SpeechSynthesisUtterance()
  speech.value.lang = speechLanguage // Langue française
  speech.value.rate = 0.8 // Vitesse normale
  speech.value.pitch = 1 // Tonalité normale

  // Quand la lecture d'un texte se termine, passer au suivant
  speech.value.onend = () => {
    currentIndex.value++
    if (currentIndex.value < textQueue.value.length) {
      speakNextText()
    }
    else {
      isSpeaking.value = false
    }
  }
})
</script>

<template>
  <div class="resume-container">
    <div class="resume-content">
      <div class="resume-content-header">
        <div class="resume-content-tag">
          <div
            v-for="(tag, index) in tags"
            :key="index"
            class="tag"
          >
            {{ tag }}
          </div>
        </div>
        <span class="resume-content-words">
          {{ ($props.resumeResult.output as components['schemas']['SummaryModel'])?.word_count || 0 }} mots générés
        </span>
      </div>
      <div class="resume-content-result">
        <div
          v-html="renderMarkdown(
            hasSummary($props.resumeResult.output)
              ? $props.resumeResult.output.summary
              : '',
          )"
        />
      </div>
    </div>
    <div class="resume-container-buttons">
      <DsfrButton
        :icon="{ name: 'ri:volume-up-fill', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
        @click="speakMultipleTexts([
          hasSummary($props.resumeResult.output)
            ? $props.resumeResult.output.summary
            : '',
        ])"
      />
      <DsfrButton
        :icon="{ name: 'ri-refresh-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
        @click="reGenerate"
      />
      <DsfrButton
        :icon="{ name: 'ri-file-copy-line', fill: 'var(--border-plain-blue-france))' }"
        icon-only
        tertiary
        no-outline
        @click="copyOnClipboard"
      />
    </div>
  </div>
</template>

<style scoped>
.resume-container {
   display: flex;
   flex-direction: column;
   gap: 1rem;
}
.resume-content {
   display: flex;
   flex-direction: column;
   padding: 1.5rem;
   border: 1px solid var(--border-default-grey);
   gap: 1rem;
}
.resume-content-result{
   display: flex;
   justify-content: space-between;
   flex-direction: column;
}
.resume-content-header {
   display: flex;
   flex-direction: column;
   gap: 0.5rem;
}
.resume-content-tag {
   display: flex;
   gap: 0.5rem;
}
.resume-content-words {
   font-size: 0.75rem;
   color: var(--text-mention-grey);
}
.resume-container-buttons{
    display: flex;
    gap: 0.5rem;
}
.tag {
    background-color: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    border-radius: 12px;
    padding: 2px 8px;
}
</style>
