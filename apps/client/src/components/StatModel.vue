<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="relative bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_24px_80px_-12px_rgba(0,0,0,0.15)] w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border border-white/60">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100/80">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </div>
          <div>
            <h2 class="text-base font-semibold text-slate-800">Statistiques des tâches</h2>
            <p class="text-[11px] text-slate-400">Vue d'ensemble globale et personnelle</p>
          </div>
        </div>
        <button
          class="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Fermer"
          @click="close"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Period selector -->
      <div class="flex items-center gap-1.5 px-6 py-2.5 border-b border-slate-100/80 bg-slate-50/50">
        <span class="text-[11px] font-medium text-slate-400 mr-1">Période :</span>
        <button
          v-for="p in PERIODS"
          :key="p.key"
          class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
          :class="selectedPeriod === p.key
            ? 'bg-indigo-500 text-white shadow-sm'
            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'"
          @click="selectedPeriod = p.key"
        >
          {{ p.label }}
        </button>
      </div>

      <!-- Content -->
      <div class="overflow-y-auto px-6 py-5 space-y-5 flex-1">

        <!-- Loading -->
        <div v-if="loading" class="py-12 flex flex-col items-center gap-3 text-slate-400">
          <svg class="w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
          <span class="text-sm">Chargement…</span>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="rounded-2xl bg-red-50 border border-red-100 px-5 py-4 text-sm text-red-600">
          {{ error }}
        </div>

        <template v-else>
          <!-- KPI totals -->
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-gradient-to-br from-indigo-50 to-indigo-100/60 border border-indigo-100/50 px-5 py-4">
              <p class="text-[28px] font-extrabold text-indigo-700 tabular-nums leading-none">{{ stats.global_stats.total_tasks }}</p>
              <p class="text-[11px] font-medium text-indigo-400 mt-1.5 uppercase tracking-wider">Tâches globales</p>
            </div>
            <div class="rounded-2xl bg-gradient-to-br from-violet-50 to-violet-100/60 border border-violet-100/50 px-5 py-4">
              <p class="text-[28px] font-extrabold text-violet-700 tabular-nums leading-none">{{ stats.user_stats.total_tasks }}</p>
              <p class="text-[11px] font-medium text-violet-400 mt-1.5 uppercase tracking-wider">Mes tâches</p>
            </div>
          </div>

          <!-- Charts row -->
          <div class="grid grid-cols-2 gap-4">

            <!-- Global chart -->
            <div class="rounded-2xl border border-slate-100 bg-white px-5 py-4">
              <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Répartition globale</h3>
              <div class="flex flex-col items-center gap-4">
                <svg viewBox="0 0 36 36" class="w-32 h-32 mx-auto">
                  <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#f1f5f9" stroke-width="3.5" />
                  <circle
                    v-for="seg in globalDonut"
                    :key="seg.label"
                    cx="18" cy="18" r="15.9155"
                    fill="none"
                    :stroke="seg.color"
                    stroke-width="3.5"
                    :stroke-dasharray="seg.dasharray"
                    :stroke-dashoffset="seg.dashoffset"
                    stroke-linecap="butt"
                    style="transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dasharray 0.5s ease"
                  />
                  <text x="18" y="18" text-anchor="middle" dominant-baseline="middle" class="text-[7px] font-bold fill-slate-700" style="font-size:7px;font-weight:700">{{ stats.global_stats.total_tasks }}</text>
                </svg>
                <div class="w-full space-y-1.5">
                  <div v-for="item in globalDonut" :key="item.label" class="flex items-center gap-2 text-[11px]">
                    <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: item.color }" />
                    <span class="flex-1 text-slate-500 capitalize">{{ item.label }}</span>
                    <span class="font-semibold tabular-nums text-slate-700">{{ item.value }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- User chart -->
            <div class="rounded-2xl border border-slate-100 bg-white px-5 py-4">
              <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Mes tâches</h3>
              <div v-if="userDonut.length === 0" class="py-6 text-center text-[11px] text-slate-400">
                Aucune tâche pour l'instant
              </div>
              <div v-else class="flex flex-col items-center gap-4">
                <svg viewBox="0 0 36 36" class="w-32 h-32 mx-auto">
                  <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#f1f5f9" stroke-width="3.5" />
                  <circle
                    v-for="seg in userDonut"
                    :key="seg.label"
                    cx="18" cy="18" r="15.9155"
                    fill="none"
                    :stroke="seg.color"
                    stroke-width="3.5"
                    :stroke-dasharray="seg.dasharray"
                    :stroke-dashoffset="seg.dashoffset"
                    stroke-linecap="butt"
                    style="transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dasharray 0.5s ease"
                  />
                  <text x="18" y="18" text-anchor="middle" dominant-baseline="middle" style="font-size:7px;font-weight:700;fill:#334155">{{ stats.user_stats.total_tasks }}</text>
                </svg>
                <div class="w-full space-y-1.5">
                  <div v-for="item in userDonut" :key="item.label" class="flex items-center gap-2 text-[11px]">
                    <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: item.color }" />
                    <span class="flex-1 text-slate-500 capitalize">{{ item.label }}</span>
                    <span class="font-semibold tabular-nums text-slate-700">{{ item.value }}</span>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- Bar breakdown (global) -->
          <div v-if="globalDonut.length > 0" class="rounded-2xl border border-slate-100 bg-white px-5 py-4">
            <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Détail par statut</h3>
            <div class="space-y-2.5">
              <div v-for="item in globalDonut" :key="item.label" class="flex items-center gap-3 text-[11px]">
                <span class="w-24 shrink-0 capitalize text-slate-500">{{ item.label }}</span>
                <div class="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :style="{ width: globalPct(item.value), background: item.color }"
                  />
                </div>
                <span class="w-6 text-right font-semibold tabular-nums text-slate-600">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { defineEmits } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

const emit = defineEmits(['close'])

function close() {
  emit('close')
}

const http = createHttpClient(ABREGE_API_URL)

// loading / error
const loading = ref(false)
const error = ref(null)

// Period filter
const PERIODS = [
  { key: 'all', label: 'Tout' },
  { key: 'today', label: "Aujourd'hui" },
  { key: '7d', label: '7 jours' },
  { key: '30d', label: '30 jours' },
  { key: '90d', label: '90 jours' },
]
const selectedPeriod = ref('today')

function getPeriodTimestamps(key) {
  if (key === 'all') return {}
  const now = Math.floor(Date.now() / 1000)
  const days = { today: 0, '7d': 7, '30d': 30, '90d': 90 }[key] ?? 0
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  if (days > 0) start.setDate(start.getDate() - days)
  return { start_date: Math.floor(start.getTime() / 1000), end_date: now }
}

// reactive stats container (will be filled by the backend)
const stats = reactive({
  global_stats: {
    total_tasks: 0,
    tasks_stats: {},
  },
  user_stats: {
    user_id: null,
    total_tasks: 0,
    tasks_stats: {},
  },
})

const COLORS = ['#4caf50', '#2196f3', '#ff9800', '#e91e63', '#9c27b0']

// fetch real stats from backend
const loadStats = async () => {
  loading.value = true
  error.value = null
  try {
    const params = getPeriodTimestamps(selectedPeriod.value)
    const { data } = await http.get('/tasks/stats', { params })
    if (data) {
      stats.global_stats = data.global_stats ?? stats.global_stats
      stats.user_stats = data.user_stats ?? stats.user_stats
    }
  }
  catch (e) {
    error.value = e?.message ?? String(e)
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})

watch(selectedPeriod, () => {
  loadStats()
})

// Donut chart: r=15.9155 → circumference=100, start from top (dashoffset=25)
function buildDonut(tasksStats, total) {
  const entries = Object.entries(tasksStats || {})
  let cumulative = 0
  return entries.map(([k, v], i) => {
    const val = v || 0
    const percent = total > 0 ? (val / total) * 100 : 0
    const dashoffset = 25 - cumulative
    cumulative += percent
    return {
      label: k,
      value: val,
      color: COLORS[i % COLORS.length],
      dasharray: `${percent} ${100 - percent}`,
      dashoffset,
    }
  })
}

const globalDonut = computed(() =>
  buildDonut(stats.global_stats.tasks_stats, stats.global_stats.total_tasks),
)

const userDonut = computed(() =>
  buildDonut(stats.user_stats.tasks_stats, stats.user_stats.total_tasks),
)

function globalPct(value) {
  const total = stats.global_stats.total_tasks || 1
  return `${Math.round((value / total) * 100)}%`
}
</script>
