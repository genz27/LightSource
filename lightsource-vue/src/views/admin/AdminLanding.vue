<template>
  <div class="admin-landing">
    <section class="panel">
      <h2>Overview</h2>
      <div class="grid">
        <div class="stat">
          <strong>Running</strong>
          <p>{{ metrics?.running ?? 0 }}</p>
        </div>
        <div class="stat">
          <strong>Avg duration</strong>
          <p>{{ (metrics?.avg_duration_sec ?? 0).toFixed(2) }}s</p>
        </div>
        <div class="stat">
          <strong>Jobs</strong>
          <p>{{ jobs.length }}</p>
        </div>
        <div class="stat">
          <strong>Assets</strong>
          <p>{{ assets.length }}</p>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Debug</h2>
      <div class="debug-row">
        <label class="switch">
          <input type="checkbox" :checked="debugEnabled" @change="toggleDebug($event)" />
          <span>Provider debug (global switch)</span>
        </label>
        <span class="muted">When enabled, /jobs/{id}/status returns provider_debug</span>
      </div>
    </section>

    <section class="panel">
      <h2>Pricing</h2>
      <div class="pricing-grid">
        <div class="pricing-item">
          <label>Text → Image</label>
          <input type="number" min="0" step="0.1" v-model.number="prices.text_to_image" />
        </div>
        <div class="pricing-item">
          <label>Image → Image</label>
          <input type="number" min="0" step="0.1" v-model.number="prices.image_to_image" />
        </div>
        <div class="pricing-item">
          <label>Text → Video</label>
          <input type="number" min="0" step="0.1" v-model.number="prices.text_to_video" />
        </div>
        <div class="pricing-item">
          <label>Image → Video</label>
          <input type="number" min="0" step="0.1" v-model.number="prices.image_to_video" />
        </div>
      </div>
      <div class="actions">
        <button class="pill sm" @click="savePrices">Save</button>
      </div>
      <p class="muted">Changes take effect immediately. Generator page shows and charges latest prices.</p>
    </section>

    <section class="panel">
      <h2>Recent jobs</h2>
      <div v-if="jobs.length">
        <div class="jobs">
          <div class="job" v-for="j in jobs" :key="j.id">
          <div class="job-row">
            <div class="job-main">
              <div class="job-title">{{ j.kind }}</div>
              <div class="job-meta">{{ j.status }} · {{ j.progress }}%</div>
            </div>
            <div class="job-actions">
              <button class="pill" @click="cancel(j.id)" :disabled="j.status !== 'running' && j.status !== 'queued'">Cancel</button>
            </div>
          </div>
        </div>
        <div class="pager">
          <button class="pill sm" @click="prevJobs" :disabled="page<=1">Prev</button>
          <span class="muted">Page {{ page }} · 10/page</span>
          <button class="pill sm" @click="nextJobs" :disabled="jobs.length < limit">Next</button>
        </div>
        </div>
      </div>
      <div v-if="!jobs.length" class="muted">No jobs</div>
    </section>

    <section class="panel">
      <h2>Quick actions</h2>
      <div class="actions">
        <RouterLink to="/generator" class="pill sm">Create job</RouterLink>
        <RouterLink to="/assets" class="pill sm">View assets</RouterLink>
        <RouterLink to="/admin/users" class="pill sm">Manage users</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMetrics, listJobs, listAssets, cancelJob, getAdminConfig, patchAdminConfig } from '@/api/admin'

interface Metrics { running?: number; avg_duration_sec?: number }
interface AdminJob { id: string; kind: string; status: string; progress?: number }
interface AdminAsset { id: string }
const metrics = ref<Metrics | null>(null)
const jobs = ref<AdminJob[]>([])
const assets = ref<AdminAsset[]>([])
const page = ref(1)
const limit = ref(10)
const debugEnabled = ref<boolean>(false)
const prices = ref<{ text_to_image: number, image_to_image: number, text_to_video: number, image_to_video: number }>({ text_to_image: 5.0, image_to_image: 5.0, text_to_video: 20.0, image_to_video: 12.0 })

const load = async () => {
  try { const m = await getMetrics(); metrics.value = (m ?? null) as Metrics | null } catch {}
  try { const j = await listJobs({ page: page.value, limit: limit.value }); jobs.value = (j ?? []) as AdminJob[] } catch {}
  try { const a = await listAssets({ limit: 20 }); assets.value = (a ?? []) as AdminAsset[] } catch {}
  try { const c = await getAdminConfig(); debugEnabled.value = Boolean((c ?? {}).debug); const p = (c ?? {}).prices; if (p && typeof p === 'object') { prices.value = { text_to_image: Number(p.text_to_image ?? 5), image_to_image: Number(p.image_to_image ?? (p.text_to_image ?? 5)), text_to_video: Number(p.text_to_video ?? 20), image_to_video: Number(p.image_to_video ?? 12) } } } catch {}
}

const cancel = async (id: string) => {
  try { await cancelJob(id); await load() } catch {}
}

const prevJobs = async () => { if (page.value > 1) { page.value -= 1; await load() } }
const nextJobs = async () => { page.value += 1; await load() }

const toggleDebug = async (e: Event) => {
  const checked = (e.target as HTMLInputElement)?.checked ?? false
  try { await patchAdminConfig({ debug: checked }); debugEnabled.value = checked } catch {}
}

const savePrices = async () => {
  try { await patchAdminConfig({ prices: prices.value }) } catch {}
}

onMounted(load)
</script>

<style scoped>
.admin-landing {
  display: grid;
  gap: 16px;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}
.panel h2 { margin: 0 0 12px 0; }

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.stat {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #111116;
}

.jobs {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.job {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  background: #111116;
}

.job-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.job-main { display: grid; gap: 6px; }
.job-title { font-weight: 700; }
.job-meta { color: var(--muted); font-size: 13px; }
.muted { color: var(--muted); }
.debug-row { display: flex; gap: 10px; align-items: center; }
.switch { display: flex; gap: 8px; align-items: center; }
.actions { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; margin-top: 8px; }
.actions > * { flex: 0 0 auto; }
.pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-bottom: 12px; }
.pricing-item { display: grid; gap: 6px; }
.pricing-item input { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--panel-soft); color: var(--text); }
.pager { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }
</style>