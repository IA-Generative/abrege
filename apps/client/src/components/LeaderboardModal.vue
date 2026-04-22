<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="relative bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_24px_80px_-12px_rgba(0,0,0,0.15)] w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border border-white/60">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100/80">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>
          </div>
          <div>
            <h2 class="text-base font-semibold text-slate-800">Leaderboard</h2>
            <p class="text-[11px] text-slate-400">Classement par nombre de tâches</p>
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
            ? 'bg-amber-500 text-white shadow-sm'
            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'"
          @click="selectedPeriod = p.key"
        >
          {{ p.label }}
        </button>
      </div>

      <!-- Tab selector: Global / Par type -->
      <div class="flex items-center gap-1.5 px-6 py-2.5 border-b border-slate-100/80 overflow-x-auto no-scrollbar">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all"
          :class="selectedTab === t.key
            ? 'bg-slate-800 text-white shadow-sm'
            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'"
          @click="selectedTab = t.key"
        >
          {{ t.label }}
        </button>
      </div>

      <!-- Content -->
      <div class="overflow-y-auto px-6 py-5 flex-1">

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
        <!-- My position card -->
        <div v-if="myEntry" class="mb-4 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/60 px-5 py-3 flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-amber-500 uppercase tracking-wider">Votre position</p>
            <p class="text-2xl font-extrabold text-amber-600 tabular-nums">#{{ myRank }} <span class="text-sm font-medium text-amber-400">/ {{ totalParticipants }}</span></p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-extrabold text-amber-600 tabular-nums">{{ myEntry.taskCount }}</p>
            <p class="text-[11px] text-amber-400">tâches</p>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="displayedEntries.length === 0" class="py-8 text-center text-sm text-slate-400">
          Aucune donnée pour cette période
        </div>

        <!-- Leaderboard rows -->
        <div v-else class="space-y-2">
          <template v-for="(entry, idx) in displayedEntries" :key="entry.rank">
            <!-- Gap separator -->
            <div v-if="idx > 0 && entry.rank - displayedEntries[idx - 1].rank > 1" class="flex items-center gap-2 py-1 px-4">
              <div class="flex-1 border-t border-dashed border-slate-200" />
              <span class="text-[10px] text-slate-300">···</span>
              <div class="flex-1 border-t border-dashed border-slate-200" />
            </div>

            <div
              class="flex items-center gap-3 px-4 py-3 rounded-2xl transition-all"
              :class="entryClass(entry)"
            >
              <!-- Rank -->
              <div class="w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold shrink-0" :class="rankClass(entry.rank)">
                <template v-if="entry.rank === 1">🥇</template>
                <template v-else-if="entry.rank === 2">🥈</template>
                <template v-else-if="entry.rank === 3">🥉</template>
                <template v-else>{{ entry.rank }}</template>
              </div>

              <!-- User info -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-700 truncate">
                  <template v-if="entry.isMe">
                    Vous
                  </template>
                  <template v-else>
                    Utilisateur #{{ entry.rank }}
                  </template>
                </p>
              </div>

              <!-- Task count -->
              <div class="text-right shrink-0">
                <p class="text-lg font-extrabold tabular-nums" :class="entry.isMe ? 'text-amber-600' : 'text-slate-700'">{{ entry.taskCount }}</p>
                <p class="text-[10px] text-slate-400">tâches</p>
              </div>
            </div>
          </template>
        </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import createHttpClient from '@/api/http-client'
import { ABREGE_API_URL } from '@/utils/constants'

const emit = defineEmits<{ close: [] }>()
const close = () => emit('close')
const http = createHttpClient(ABREGE_API_URL)

const PERIODS = [
  { key: 'all', label: 'Tout' },
  { key: 'today', label: "Aujourd'hui" },
  { key: '7d', label: '7 jours' },
  { key: '30d', label: '30 jours' },
  { key: '90d', label: '90 jours' },
]

const TABS = [
  { key: 'global', label: 'Toutes tâches' },
  { key: 'abrege', label: 'Résumé' },
  { key: 'merge', label: 'Fusion' },
  { key: 'classification', label: 'Classification' },
]

const selectedPeriod = ref('today')
const selectedTab = ref('global')
const loading = ref(false)
const error = ref<string | null>(null)

type LeaderboardEntry = { rank: number; username: string; taskCount: number; isMe: boolean }

// API response
const displayedEntries = ref<LeaderboardEntry[]>([])
const myRank = ref<number | null>(null)
const totalParticipants = ref(0)

function getPeriodTimestamps(key: string): { start_date?: number; end_date?: number } {
  if (key === 'all') return {}
  const now = Math.floor(Date.now() / 1000)
  const days: Record<string, number> = { today: 0, '7d': 7, '30d': 30, '90d': 90 }
  const d = days[key] ?? 0
  if (d === 0) {
    // today: start of day
    const startOfDay = new Date()
    startOfDay.setHours(0, 0, 0, 0)
    return { start_date: Math.floor(startOfDay.getTime() / 1000), end_date: now }
  }
  return { start_date: now - d * 86400, end_date: now }
}

async function fetchLeaderboard() {
  loading.value = true
  error.value = null
  try {
    const params: Record<string, any> = {}
    const period = getPeriodTimestamps(selectedPeriod.value)
    if (period.start_date) params.start_date = period.start_date
    if (period.end_date) params.end_date = period.end_date
    if (selectedTab.value !== 'global') params.task_type = selectedTab.value

    const { data } = await http.get('/v1/leaderboard', { params })

    myRank.value = data.my_rank ?? null
    totalParticipants.value = data.total_participants ?? 0
    displayedEntries.value = (data.entries ?? []).map((e: any) => ({
      rank: e.rank,
      username: e.user_id,
      taskCount: e.task_count,
      isMe: e.is_me,
    }))
  }
  catch (e: any) {
    error.value = 'Impossible de charger le classement'
    console.error('Leaderboard fetch error', e)
  }
  finally {
    loading.value = false
  }
}

const myEntry = computed(() => displayedEntries.value.find(e => e.isMe) ?? null)

onMounted(() => fetchLeaderboard())
watch([selectedPeriod, selectedTab], () => fetchLeaderboard())

function entryClass(entry: LeaderboardEntry) {
  if (entry.isMe) return 'bg-amber-50 border border-amber-200 shadow-sm'
  if (entry.rank === 1) return 'bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200/60'
  return 'bg-slate-50/60 border border-slate-100'
}

function rankClass(rank: number) {
  if (rank === 1) return 'text-yellow-600'
  if (rank === 2) return 'text-slate-400'
  if (rank === 3) return 'text-amber-700'
  return 'text-slate-400 bg-slate-100 rounded-lg'
}
</script>
