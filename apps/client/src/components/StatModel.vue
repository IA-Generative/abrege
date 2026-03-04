<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal fr-card" @click.stop>
      <header class="modal-header">
        <h3 class="fr-h3">Statistiques des tâches</h3>
        <button class="modal-close" @click="close">✕</button>
      </header>

      <section class="modal-section charts two-columns">
        <div class="chart-col">
          <div class="section-title">Statistiques globales</div>
          <div class="section-content center-col">
            <div class="stat-row"><strong>Total de tâches :</strong> {{ stats.global_stats.total_tasks }}</div>
            <div class="chart-block">
              <svg :width="180" :height="180" viewBox="0 0 32 32" class="pie">
                <template v-for="(v, i) in globalSlices" :key="i">
                  <path :d="v.path" :fill="v.color" stroke="#fff" stroke-width="0.6" stroke-linejoin="round" stroke-linecap="round"></path>
                </template>
                <circle cx="16" cy="16" r="5" fill="#fff"></circle>
              </svg>
              <div class="legend">
                <div v-for="(item, idx) in globalLegend" :key="idx" class="legend-item">
                  <span class="legend-color" :style="{ background: item.color }"></span>
                  <span class="legend-label">{{ item.label }}: {{ item.value }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-col">
          <div class="section-title">Statistiques utilisateur</div>
          <div class="section-content center-col">
            <div class="stat-row"><strong>Utilisateur :</strong> Vous </div>
            <div class="stat-row"><strong>Total :</strong> {{ stats.user_stats.total_tasks }}</div>
            <div class="chart-block">
              <svg :width="180" :height="180" viewBox="0 0 32 32" class="pie">
                <template v-for="(v, i) in userSlices" :key="i">
                  <path :d="v.path" :fill="v.color" stroke="#fff" stroke-width="0.6" stroke-linejoin="round" stroke-linecap="round"></path>
                </template>
                <circle cx="16" cy="16" r="5" fill="#fff"></circle>
              </svg>
              <div class="legend">
                <div v-for="(item, idx) in userLegend" :key="idx" class="legend-item">
                  <span class="legend-color" :style="{ background: item.color }"></span>
                  <span class="legend-label">{{ item.label }}: {{ item.value }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer class="modal-footer">
        <button class="fr-btn fr-btn--secondary" @click="close">Fermer</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
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

function polarToCartesian(cx, cy, r, angle) {
  const a = (angle - 90) * Math.PI / 180.0
  return { x: cx + (r * Math.cos(a)), y: cy + (r * Math.sin(a)) }
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle)
  const end = polarToCartesian(cx, cy, r, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  const d = [
    `M ${cx} ${cy}`,
    `L ${start.x} ${start.y}`,
    `A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
    'Z',
  ].join(' ')
  return d
}

// fetch real stats from backend
const loadStats = async () => {
  loading.value = true
  error.value = null
  try {
    const { data } = await http.get('/tasks/stats')
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

const userSlices = computed(() => {
  const items = stats.user_stats.tasks_stats || {}
  const entries = Object.entries(items)
  const total = entries.reduce((s, [, v]) => s + (v || 0), 0) || 1
  let angle = 0
  return entries.map(([k, v], i) => {
    const portion = ((v || 0) / total) * 360
    const path = describeArc(16, 16, 16, angle, angle + portion)
    angle += portion
    return { label: k, value: v || 0, color: COLORS[i % COLORS.length], path }
  })
})

const userLegend = computed(() => userSlices.value.map(s => ({ label: s.label, value: s.value, color: s.color })))

const globalSlices = computed(() => {
  const items = stats.global_stats.tasks_stats || {}
  const entries = Object.entries(items)
  const total = entries.reduce((s, [, v]) => s + (v || 0), 0) || 1
  let angle = 0
  return entries.map(([k, v], i) => {
    const portion = ((v || 0) / total) * 360
    const path = describeArc(16, 16, 16, angle, angle + portion)
    angle += portion
    return { label: k, value: v || 0, color: COLORS[i % COLORS.length], path }
  })
})

const globalLegend = computed(() => globalSlices.value.map(s => ({ label: s.label, value: s.value, color: s.color })))
</script>

<style scoped>
.modal-close { background: transparent; border: none; font-size: 1.25rem; cursor: pointer; }
.stat-row { margin-bottom: 6px; }

.charts { display: flex; gap: 1rem; align-items: center; }
.chart-col { flex: 1; }
.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 90px; text-transform: capitalize; }
.bar-wrap { flex: 1; background: #f3f4f6; height: 18px; border-radius: 8px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg,#60a5fa,#3b82f6); }
.bar-value { width: 32px; text-align: right; }
.center { display:flex; align-items:center; gap:12px; }
.legend { display:flex; flex-direction:column; gap:6px; }
.legend-item { display:flex; gap:8px; align-items:center; }
.legend-color { width:14px; height:14px; display:inline-block; border-radius:3px; }

.pie { transform: rotate(-90deg); }
.two-columns .chart-col { display:flex; flex-direction:column; align-items:center; gap:12px; }
.center-col { display:flex; flex-direction:column; align-items:center; gap:8px; }
.chart-block { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:240px; gap:8px; }

</style>
