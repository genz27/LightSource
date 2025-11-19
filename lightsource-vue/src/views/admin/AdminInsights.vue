<template>
  <div class="admin-insights">
    <section class="panel">
      <h2>Metrics</h2>
      <div class="metrics-grid">
        <div class="stat"><strong>Running</strong><p>{{ metrics?.running ?? 0 }}</p></div>
        <div class="stat"><strong>Requests</strong><p>{{ metrics?.requests_total ?? 0 }}</p></div>
        <div class="stat"><strong>Rate limited</strong><p>{{ metrics?.rate_limited_total ?? 0 }}</p></div>
        <div class="stat"><strong>Avg duration</strong><p>{{ (metrics?.avg_duration_sec ?? 0).toFixed(2) }}s</p></div>
      </div>
      <div class="transitions" v-if="metrics?.transitions">
        <div class="transition" v-for="(v,k) in metrics.transitions" :key="k">{{ k }} · {{ v }}</div>
      </div>
    </section>

    

    <section class="panel">
      <h2>Exports</h2>
      <div class="actions">
        <button class="pill sm" @click="downloadCsv('/admin/export/users','users.csv')">Users</button>
        <button class="pill sm" @click="downloadCsv('/admin/export/jobs','jobs.csv')">Jobs</button>
        <button class="pill sm" @click="downloadCsv('/admin/export/assets','assets.csv')">Assets</button>
        <button class="pill sm" @click="downloadCsv('/admin/export/wallets','wallets.csv')">Wallets</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMetrics } from '@/api/admin'
import { getText } from '@/api/client'

interface Metrics { running?: number; requests_total?: number; rate_limited_total?: number; avg_duration_sec?: number; transitions?: Record<string, number> }

const metrics = ref<Metrics | null>(null)

const loadMetrics = async () => { try { metrics.value = await getMetrics() } catch {} }

const downloadCsv = async (path: string, name: string) => {
  const text = await getText(path)
  const blob = new Blob([text], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

onMounted(() => { loadMetrics() })
</script>

<style scoped>
.admin-insights { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.panel h2 { margin: 0 0 12px 0; }
.metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.stat { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: #111116; }
.transitions { display: grid; gap: 8px; margin-top: 12px; }
.transition { border: 1px solid var(--border); border-radius: 10px; padding: 8px; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 12px; }
.controls { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.controls > * { flex: 0 0 auto; }
input { padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--panel-soft); color: var(--text); font-size: 13px; }
.advanced { margin-top: 8px; }
.logs { display: grid; gap: 8px; }
.log { border: 1px solid var(--border); border-radius: 10px; padding: 10px; background: #111116; }
.log-title { font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; margin-top: 8px; }
.actions > * { flex: 0 0 auto; }
.muted { color: var(--muted); }
.pager { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }
</style>