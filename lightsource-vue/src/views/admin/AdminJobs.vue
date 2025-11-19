<template>
  <div class="admin-jobs">
    <section class="panel">
      <div class="header">
        <h2>Jobs</h2>
        <div class="controls">
          <select v-model="status">
            <option value="">All status</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="canceled">Canceled</option>
          </select>
          <select v-model="kind">
            <option value="">All kinds</option>
            <option value="text_to_image">Text to image</option>
            <option value="text_to_video">Text to video</option>
            <option value="image_to_video">Image to video</option>
          </select>
          <input v-model="owner" placeholder="Owner ID" />
          <button class="pill sm" @click="load">Search</button>
          <button class="pill sm" @click="showAdvanced = !showAdvanced">Advanced</button>
        </div>
        <div class="controls advanced" v-if="showAdvanced">
          <input v-model="created_from" type="datetime-local" />
          <input v-model="created_to" type="datetime-local" />
          <button class="pill sm" @click="load">Apply</button>
        </div>
      </div>
      <div v-if="jobs.length">
        <div class="list">
          <div class="row" v-for="j in jobs" :key="j.id" @click="open(j)" style="cursor:pointer;">
          <div class="col">
            <div class="name">{{ j.kind }}</div>
            <div class="meta">{{ j.status }} · {{ j.progress }}% · {{ j.updated_at }}</div>
            <div class="meta">Owner: {{ usernames[j.owner_id || ''] || j.owner_id || '—' }}</div>
          </div>
          <div class="actions">
            <button class="pill sm" @click.stop="open(j)">View</button>
            <button class="pill sm" @click.stop="cancel(j.id)" :disabled="j.status !== 'running' && j.status !== 'queued'">Cancel</button>
          </div>
          </div>
        </div>
        <div class="pager">
          <button class="pill sm" @click="prevPage" :disabled="page<=1">Prev</button>
          <span class="muted">Page {{ page }} · 10/page</span>
          <button class="pill sm" @click="nextPage" :disabled="jobs.length < limit">Next</button>
        </div>
      </div>
      <div v-else class="muted">No jobs</div>
      <div v-if="selected" class="job-sidebar" :class="{ open: showSidebar }">
        <div class="sidebar-header">
          <h3>Job Details</h3>
          <button class="close-btn" @click="close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div class="sidebar-content">
          <div class="job-preview-large">
            <img v-if="isImage" :src="detail?.image_url || detail?.result_url || ''" alt="" />
            <video v-else-if="isVideo" class="job-preview-video" :poster="DEFAULT_POSTER" :src="detail?.video_url || detail?.result_url || ''" preload="metadata" controls playsinline muted></video>
            <div v-else class="job-icon"></div>
          </div>
          <div class="job-details">
            <h4>{{ selected?.id }}</h4>
            <div class="detail-row"><span>Status</span><span>{{ detail?.status || selected?.status }}</span></div>
            <div class="detail-row"><span>Progress</span><span>{{ detail?.progress ?? selected?.progress ?? 0 }}%</span></div>
            <div class="detail-row"><span>Kind</span><span>{{ selected?.kind }}</span></div>
            <div class="detail-row"><span>Model</span><span>{{ detail?.model || selected?.model || '—' }}</span></div>
            <div class="detail-row"><span>Provider</span><span>{{ selected?.provider || '—' }}</span></div>
            <div class="detail-row"><span>Owner</span><span>{{ usernames[selected?.owner_id || ''] || selected?.owner_id || '—' }}</span></div>
            <div class="detail-row"><span>Updated</span><span>{{ selected?.updated_at }}</span></div>
            <div class="detail-row"><span>Prompt</span><span style="max-width:60%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ selected?.prompt || '—' }}</span></div>
          </div>
          <div class="sidebar-actions">
            <button class="pill sm" @click.stop="cancel(selected!.id)" :disabled="selected?.status !== 'running' && selected?.status !== 'queued'">Cancel</button>
            <a class="pill accent sm" v-if="detail?.result_url" :href="String(detail?.result_url)" target="_blank">Open Result</a>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listJobs, cancelJob, getJob, getJobStatus, getUser } from '@/api/admin'

interface AdminJob { id: string; kind: string; status: string; progress?: number; updated_at?: string; prompt?: string; model?: string; provider?: string; owner_id?: string; is_public?: boolean; asset_id?: string }
const jobs = ref<AdminJob[]>([])
const usernames = ref<Record<string, string>>({})
const status = ref('')
const kind = ref('')
const owner = ref('')
const created_from = ref('')
const created_to = ref('')
const showAdvanced = ref(false)
const page = ref(1)
const limit = ref(10)

const load = async () => {
  try {
    const data = await listJobs({ status: status.value || undefined, kind: kind.value || undefined, owner_id: owner.value || undefined, created_from: created_from.value || undefined, created_to: created_to.value || undefined, page: page.value, limit: limit.value })
    jobs.value = (data ?? []) as AdminJob[]
  } catch {}
  try {
    const ids = Array.from(new Set(jobs.value.map(j => j.owner_id).filter(Boolean))) as string[]
    const missing = ids.filter(id => !(id in usernames.value))
    const results = await Promise.all(missing.map(id => getUser(id).catch(() => null)))
    for (let i = 0; i < missing.length; i++) {
      const id = missing[i]
      const u = results[i] as { username?: string } | null
      if (id && u && typeof u?.username === 'string') usernames.value[id] = String(u.username)
    }
  } catch {}
}

const prevPage = async () => { if (page.value > 1) { page.value -= 1; await load() } }
const nextPage = async () => { page.value += 1; await load() }

const cancel = async (id: string) => {
  try { await cancelJob(id); await load() } catch {}
}

onMounted(load)

const selected = ref<AdminJob | null>(null)
const showSidebar = ref(false)
const DEFAULT_POSTER = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMWE0MWQxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwTDEyMCA4MEwxNDAgMTAwTDEyMCAxMjBMMTAwIDEwMFoiIGZpbGw9IiM2NjY2NjYiLz4KPC9zdmc+'
type JobDetailPayload = { status?: string; progress?: number; model?: string; prompt?: string; error_message?: string; result_url?: string; video_url?: string; image_url?: string; provider_debug?: Record<string, unknown> }
const detail = ref<JobDetailPayload | null>(null)
const isVideo = computed(() => selected.value?.kind === 'text_to_video' || selected.value?.kind === 'image_to_video')
const isImage = computed(() => selected.value?.kind === 'text_to_image')
const open = async (j: AdminJob) => {
  selected.value = j
  showSidebar.value = true
  try {
    const full = await getJob(j.id)
    selected.value = (full ?? j) as AdminJob
  } catch {}
  try {
    const s = await getJobStatus(j.id)
    detail.value = (s ?? null) as JobDetailPayload | null
  } catch {}
}
const close = () => { showSidebar.value = false }
</script>

<style scoped>
.admin-jobs { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 12px; }
.controls { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.controls > * { flex: 0 0 auto; }
.controls input, .controls select { padding: 8px 10px; font-size: 13px; border-radius: 8px; min-width: 140px; }
.advanced { margin-top: 8px; }
input, select { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); }
.list { display: grid; gap: 10px; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; border: 1px solid var(--border); border-radius: 12px; padding: 12px; background: #111116; }
.name { font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.muted { color: var(--muted); }
.pager { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }
.job-sidebar { position: fixed; top: 0; right: -420px; width: 420px; height: 100vh; background: var(--panel); border-left: 1px solid var(--border); transition: right .3s ease; z-index: 100; display: flex; flex-direction: column; }
.job-sidebar.open { right: 0; }
.sidebar-header { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border); }
.sidebar-header h3 { margin: 0; color: var(--text); }
.close-btn { background: none; border: none; color: var(--muted); cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: var(--panel-soft); color: var(--text); }
.sidebar-content { flex: 1; overflow-y: auto; padding: 24px; }
.job-preview-large { margin-bottom: 24px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.job-preview-large img { width: 100%; height: auto; display: block; }
.job-preview-video { width: 100%; height: auto; display: block; background: var(--panel-soft); max-height: 60vh; }
.job-icon { display: grid; place-items: center; height: 180px; background: var(--panel-soft); color: var(--muted); }
.job-details { margin-bottom: 24px; }
.job-details h4 { margin: 0 0 16px 0; color: var(--text); font-size: 18px; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.detail-row:last-child { border-bottom: none; }
.sidebar-actions { display: flex; gap: 12px; justify-content: flex-end; }
</style>