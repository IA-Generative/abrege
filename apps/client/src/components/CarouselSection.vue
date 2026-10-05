<script lang="ts" setup generic="T extends { title: string, description: string }">
import { computed, ref, useId } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  sections: T[]
  collapsible?: boolean
}>(), {
  collapsible: true,
})

const panelId = useId()
const toggled = ref(false)
const isOpen = computed(() => !props.collapsible || toggled.value)
const current = ref(0)

const currentSection = computed(() => props.sections[current.value] as T)
const isFirst = computed(() => current.value === 0)
const isLast = computed(() => current.value === props.sections.length - 1)
const previousLabel = computed(() => isFirst.value ? 'Précédent' : `Précédent : ${props.sections[current.value - 1]?.title}`)
const nextLabel = computed(() => isLast.value ? 'Suivant' : `Suivant : ${props.sections[current.value + 1]?.title}`)
const previousTooltip = computed(() => props.sections[current.value - 1]?.description)
const nextTooltip = computed(() => props.sections[current.value + 1]?.description)
</script>

<template>
  <div
    v-if="sections.length > 0"
    class="carousel-section"
  >
    <h3
      v-if="collapsible"
      class="carousel-section__heading"
    >
      <button
        type="button"
        class="carousel-section__toggle"
        :aria-expanded="isOpen"
        :aria-controls="panelId"
        @click="toggled = !toggled"
      >
        {{ title }}
      </button>
    </h3>
    <div
      v-if="isOpen"
      :id="panelId"
      class="carousel-section__panel"
    >
      <div
        class="carousel-section__card"
        aria-live="polite"
      >
        <p class="carousel-section__title fr-text--bold">
          {{ currentSection.title }}
          <span
            v-if="sections.length > 1"
            class="carousel-section__counter"
          >({{ current + 1 }}/{{ sections.length }})</span>
        </p>
        <p class="carousel-section__description">
          {{ currentSection.description }}
        </p>
        <slot
          :section="currentSection"
          :index="current"
        />
      </div>
      <div
        v-if="sections.length > 1"
        class="carousel-section__nav"
      >
        <DsfrButton
          :label="previousLabel"
          :title="previousTooltip"
          secondary
          icon="ri-arrow-left-line"
          :disabled="isFirst"
          @click="current--"
        />
        <DsfrButton
          :label="nextLabel"
          :title="nextTooltip"
          secondary
          icon="ri-arrow-right-line"
          icon-right
          :disabled="isLast"
          @click="current++"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
  .carousel-section {
    margin-top: 2rem;
  }
  .carousel-section__heading {
    margin: 0;
  }
  .carousel-section__toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 1rem;
    font: inherit;
    font-weight: 700;
    color: var(--text-action-high-blue-france);
    text-align: left;
    background: transparent;
    border: 0;
    border-bottom: 1px solid var(--border-default-grey);
    cursor: pointer;
  }
  .carousel-section__toggle::after {
    flex-shrink: 0;
    width: 0.5rem;
    height: 0.5rem;
    margin-left: 1rem;
    border-right: 2px solid currentcolor;
    border-bottom: 2px solid currentcolor;
    content: '';
    transform: rotate(45deg);
    transition: transform 0.2s ease;
  }
  .carousel-section__toggle[aria-expanded='true']::after {
    transform: rotate(-135deg);
  }
  .carousel-section__panel {
    padding-top: 1rem;
  }
  .carousel-section:not(:has(.carousel-section__heading)) {
    margin-top: 0;
  }
  .carousel-section:not(:has(.carousel-section__heading)) .carousel-section__panel {
    padding-top: 0;
  }
  .carousel-section__card {
    padding: 1rem 1.5rem 1.5rem;
    border: 1px solid var(--border-default-grey);
  }
  .carousel-section__title {
    margin: 0;
  }
  .carousel-section__description {
    margin: 0.25rem 0 0;
    color: var(--text-mention-grey);
    font-size: 0.875rem;
  }
  .carousel-section__counter {
    font-weight: normal;
    color: var(--text-mention-grey);
  }
  .carousel-section__nav {
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
  }
  @media (prefers-reduced-motion: reduce) {
    .carousel-section__toggle::after {
      transition: none;
    }
  }
</style>
