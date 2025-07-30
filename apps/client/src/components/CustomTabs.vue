<script setup lang="ts">
import { computed, ref } from 'vue'

interface TabData {
  label: string
  slot?: string
}

const props = defineProps<{
  tabsData: TabData[]
}>()

const tabListId = 'dynamic-tabs'
const activeTab = ref(0)

// Générer les onglets à partir de la prop tabsData
const tabs = computed(() =>
  props.tabsData.map((tab, index) => ({
    id: `tab-${index}`,
    panelId: `panel-${index}`,
    label: tab.label,
    slot: tab.slot || `tab-${index}-content`, // Utiliser un slot par défaut si non spécifié
  })),
)

function activateTab (index: number) {
  activeTab.value = index
}
</script>

<template>
  <div class="tabs">
    <!-- Liste des onglets -->
    <div
      role="tablist"
      class="tabs__list"
      :aria-labelledby="tabListId"
    >
      <button
        v-for="(tab, index) in tabs"
        :id="tab.id"
        :key="tab.id"
        role="tab"
        :aria-controls="tab.panelId"
        :aria-selected="activeTab === index"
        :tabindex="activeTab === index ? 0 : -1"
        class="fr-tabs__tab"
        @click="activateTab(index)"
        @keydown.enter="activateTab(index)"
        @keydown.space.prevent="activateTab(index)"
        @keydown.arrow-right.prevent="activateTab((index + 1) % tabs.length)"
        @keydown.arrow-left.prevent="activateTab((index - 1 + tabs.length) % tabs.length)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Contenu associé -->
    <div
      v-for="(tab, index) in tabs"
      v-show="activeTab === index"
      :id="tab.panelId"
      :key="tab.panelId"
      role="tabpanel"
      :aria-labelledby="tab.id"
      class="tabs__panel"
    >
      <slot
        :name="tab.slot"
        :is-active="activeTab === index"
      />
    </div>
  </div>
</template>

  <style scoped>
  .tabs {
    display: flex;
    flex-direction: column;
  }
  .tabs__list {
    display: flex;
    padding-left: 1rem;
    overflow: auto;
  }
  .tabs__panel {
    display: block;
    padding: 1.5rem;
    border: 1px solid var(--border-default-grey);
  }
  </style>
