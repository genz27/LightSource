<template>
  <div class="admin-assets">
    <section class="panel">
      <div class="assets-header">
        <h2>Assets</h2>
        <div class="assets-controls">
          <select v-model="type">
            <option value="">All types</option>
            <option value="image">Image</option>
            <option value="video">Video</option>
            <option value="audio">Audio</option>
          </select>
          <select v-model="provider">
            <option value="">All providers</option>
            <option v-for="p in providers" :key="p.name" :value="p.name">{{ p.display_name || p.name }}</option>
          </select>
          <select v-model="pub">
            <option :value="undefined">All</option>
            <option :value="true">Public</option>
            <option :value="false">Private</option>
          </select>
          <input v-model="owner" placeholder="Owner ID" />
          <button class="pill sm" @click="load">Search</button>
          <select v-model="sort">
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="provider">Provider</option>
            <option value="type">Type</option>
          </select>
          <button class="pill sm" @click="reset">Reset</button>
        </div>
      </div>
      <div class="grid" v-if="loading">
        <div class="card skeleton" v-for="n in 8" :key="n">
          <div class="preview skeleton-box"></div>
          <div class="info">
            <div class="title skeleton-line"></div>
            <div class="meta skeleton-line"></div>
          </div>
          <div class="card-actions">
            <div class="skeleton-pill"></div>
            <div class="skeleton-pill"></div>
          </div>
        </div>
      </div>
      <div v-else-if="assets.length">
        <div class="assets-grid">
          <div class="asset-card" v-for="a in sortedAssets" :key="a.id" @click="openDetails(a)">
            <div class="asset-badges">
              <span class="badge" v-if="a.is_public">Public</span>
              <span class="badge ghost" v-else>Private</span>
              <span class="provider-badge" v-if="a.provider">{{ a.provider }}</span>
            </div>
            <div class="asset-preview">
              <img v-if="a.type==='image'" :src="a.preview_url || a.url" alt="" />
              <video v-else-if="a.type==='video'" class="asset-video" :poster="videoPoster(a)" :src="a.url" preload="auto" muted playsinline crossorigin="anonymous" :data-id="a.id" @loadeddata="onVideoLoaded" @error="onVideoError"></video>
              <div v-else class="asset-icon"></div>
            </div>
            <div class="asset-info">
              <h4>{{ a.id }}</h4>
              <div class="asset-meta">
                <span class="asset-type">{{ a.type }}</span>
                <span class="asset-date">{{ fmtDate(a.created_at) }}</span>
              </div>
            </div>
            <div class="asset-actions" @click.stop>
              <button class="action-btn" :title="a.is_public ? 'Unpublish' : 'Publish'" @click="togglePublic(a)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path v-if="a.is_public" d="M3 12a9 9 0 1 0 18 0 9 9 0 1 0-18 0zm9-4v8m-4-4h8" />
                  <path v-else d="M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18zm-3 10 3-3 3 3" />
                </svg>
              </button>
              <a class="action-btn" :href="a.url" target="_blank" title="Open">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 3h7v7" /><path d="M10 14 21 3" /><path d="M21 21H3V3" />
                </svg>
              </a>
              <button class="action-btn" title="Copy URL" @click="copy(a.url)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <rect x="2" y="2" width="13" height="13" rx="2" ry="2" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div class="pager">
          <button class="pill sm" @click="prevPage" :disabled="page<=1">Prev</button>
          <span class="muted">Page {{ page }} · 10/page</span>
          <button class="pill sm" @click="nextPage" :disabled="assets.length < limit">Next</button>
        </div>
      </div>
      <div v-else class="muted">No assets</div>
      <div v-if="selected" class="asset-sidebar" :class="{ open: showSidebar }">
        <div class="sidebar-header">
          <h3>Asset Details</h3>
          <button class="close-btn" @click="closeDetails">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div class="sidebar-content">
          <div class="asset-preview-large">
            <img v-if="selected?.type==='image'" :src="selected?.preview_url || selected?.url" :alt="selected?.id" />
            <video v-else-if="selected?.type==='video'" class="asset-preview-video" :poster="selected?.preview_url || ''" :src="selected?.url" preload="metadata" controls playsinline muted></video>
            <div v-else class="asset-icon"></div>
          </div>
          <div class="asset-details">
            <h4>{{ selected?.id }}</h4>
            <div class="detail-row"><span>Type</span><span>{{ selected?.type }}</span></div>
            <div class="detail-row"><span>Provider</span><span>{{ selected?.provider || '—' }}</span></div>
            <div class="detail-row"><span>Owner</span><span>{{ selected?.owner_id || '—' }}</span></div>
            <div class="detail-row"><span>Created</span><span>{{ fmtDate(selected?.created_at) }}</span></div>
          </div>
          <div class="sidebar-actions">
            <button class="pill" v-if="selected" @click="togglePublic(selected)">{{ selected.is_public ? 'Unpublish' : 'Publish' }}</button>
            <a class="pill accent" :href="selected?.url" target="_blank">Open</a>
            <button class="ghost" @click="copy(selected?.url || '')">Copy URL</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listAssets, patchAssetPublic } from '@/api/admin'
import { get as httpGet } from '@/api/client'

interface AdminAsset { id: string; type: string; url: string; preview_url?: string; provider?: string; created_at?: string; is_public?: boolean; owner_id?: string; meta?: Record<string, unknown> }
interface ProviderInfo { name: string; display_name?: string }
const assets = ref<AdminAsset[]>([])
const type = ref('')
const provider = ref('')
const pub = ref<boolean | undefined>(undefined)
const owner = ref('')
const page = ref(1)
const limit = ref(10)
const loading = ref(false)
const providers = ref<ProviderInfo[]>([])
const sort = ref<'newest'|'oldest'|'provider'|'type'>('newest')
const sortedAssets = computed(() => {
  const list = [...assets.value]
  if (sort.value === 'newest') list.sort((a,b) => (new Date(b.created_at||0).getTime()) - (new Date(a.created_at||0).getTime()))
  else if (sort.value === 'oldest') list.sort((a,b) => (new Date(a.created_at||0).getTime()) - (new Date(b.created_at||0).getTime()))
  else if (sort.value === 'provider') list.sort((a,b) => (a.provider||'').localeCompare(b.provider||''))
  else if (sort.value === 'type') list.sort((a,b) => (a.type||'').localeCompare(b.type||''))
  return list
})

const selected = ref<AdminAsset | null>(null)
const showSidebar = ref(false)
const openDetails = (a: AdminAsset) => { selected.value = a; showSidebar.value = true }
const closeDetails = () => { showSidebar.value = false }

const DEFAULT_POSTER = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMWE0MWQxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwTDEyMCA4MEwxNDAgMTAwTDEyMCAxMjBMMTAwIDEwMFoiIGZpbGw9IiM2NjY2NjYiLz4KPC9zdmc+'
const posterCache = ref<Record<string, string>>({})
const videoPoster = (a: AdminAsset) => {
  const id = a.id
  const cached = posterCache.value[id]
  if (cached) return cached
  const p = a.preview_url || ''
  const isImage = p.startsWith('data:image/') || /(png|jpg|jpeg|webp)$/i.test(p)
  return isImage ? p : DEFAULT_POSTER
}
const onVideoLoaded = (e: Event) => {
  const v = e.target as HTMLVideoElement
  try {
    v.muted = true
    const p = v.play()
    if (p && typeof (p as Promise<void>).then === 'function') {
      ;(p as Promise<void>).then(() => setTimeout(() => v.pause(), 80)).catch(() => {})
    }
    const id = v.dataset.id || ''
    if (id && v.videoWidth && v.videoHeight) {
      const canvas = document.createElement('canvas')
      canvas.width = v.videoWidth
      canvas.height = v.videoHeight
      const ctx = canvas.getContext('2d')
      if (ctx) {
        try {
          ctx.drawImage(v, 0, 0, canvas.width, canvas.height)
          const dataUrl = canvas.toDataURL('image/jpeg', 0.6)
          if (dataUrl && dataUrl.startsWith('data:image/')) {
            posterCache.value[id] = dataUrl
            v.poster = dataUrl
          }
        } catch {}
      }
    }
  } catch {}
}
const onVideoError = (e: Event) => {
  const v = e.target as HTMLVideoElement
  try { v.poster = DEFAULT_POSTER } catch {}
}

const load = async () => {
  loading.value = true
  try {
    const data = await listAssets({ type: type.value || undefined, provider: provider.value || undefined, public: pub.value, owner_id: owner.value || undefined, page: page.value, limit: limit.value })
    assets.value = (data ?? []) as AdminAsset[]
  } finally {
    loading.value = false
  }
}

const reset = async () => { type.value=''; provider.value=''; pub.value=undefined; owner.value=''; page.value=1; sort.value='newest'; await load() }

const prevPage = async () => { if (page.value > 1) { page.value -= 1; await load() } }
const nextPage = async () => { page.value += 1; await load() }

const togglePublic = async (a: AdminAsset) => {
  try { await patchAssetPublic(a.id, !a.is_public); await load() } catch {}
}

const fmtDate = (s?: string) => {
  try { return s ? new Date(s).toLocaleString() : '' } catch { return s || '' }
}

const copy = async (text: string) => {
  try { await navigator.clipboard.writeText(text) } catch {}
}

onMounted(async () => {
  try { providers.value = await httpGet('/providers') } catch {}
  await load()
})
</script>

<style scoped>
.admin-assets { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.assets-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.assets-controls { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.assets-controls > * { flex: 0 0 auto; }
.assets-controls { margin-bottom: 12px; }
input, select { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); }
.assets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.asset-card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; position: relative; transition: all .2s ease; }
.asset-card:hover { transform: translateY(-4px); border-color: var(--accent); box-shadow: 0 8px 32px rgba(0,0,0,.3); }
.asset-preview { position: relative; aspect-ratio: 16/9; overflow: hidden; background: var(--panel-soft); }
.asset-preview img { width: 100%; height: 100%; object-fit: cover; }
.asset-video { width: 100%; height: 100%; object-fit: cover; background: var(--panel-soft); }
.asset-icon { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: var(--muted); opacity: .6; }
.asset-badges { position: absolute; top: 8px; left: 8px; display: flex; gap: 6px; z-index: 2; }
.badge { background: var(--accent); color: #1a1a1a; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge.ghost { background: rgba(255,255,255,.2); color: #fff; }
.provider-badge { background: var(--panel-soft); color: var(--text); border: 1px solid var(--border); padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.asset-info { padding: 16px; }
.asset-info h4 { margin: 0 0 8px 0; color: var(--text); font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.asset-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--muted); }
.asset-type { background: var(--accent); color: #1a1a1a; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.asset-actions { position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; opacity: 0; transition: opacity .3s ease; }
.asset-card:hover .asset-actions { opacity: 1; }
.action-btn { background: rgba(0,0,0,.8); border: none; border-radius: 4px; padding: 6px; cursor: pointer; transition: all .2s ease; font-size: 12px; color: white; }
.action-btn:hover { background: var(--accent); color: #111; }
.muted { color: var(--muted); }
.pager { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }

.asset-sidebar { position: fixed; top: 0; right: -400px; width: 400px; height: 100vh; background: var(--panel); border-left: 1px solid var(--border); transition: right .3s ease; z-index: 100; display: flex; flex-direction: column; }
.asset-sidebar.open { right: 0; }
.sidebar-header { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border); }
.sidebar-header h3 { margin: 0; color: var(--text); }
.close-btn { background: none; border: none; color: var(--muted); cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: var(--panel-soft); color: var(--text); }
.sidebar-content { flex: 1; overflow-y: auto; padding: 24px; }
.asset-preview-large { margin-bottom: 24px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.asset-preview-large img { width: 100%; height: auto; display: block; }
.asset-preview-video { width: 100%; height: auto; display: block; background: var(--panel-soft); max-height: 60vh; }
.asset-details { margin-bottom: 24px; }
.asset-details h4 { margin: 0 0 16px 0; color: var(--text); font-size: 18px; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.detail-row:last-child { border-bottom: none; }
.sidebar-actions { display: flex; gap: 12px; justify-content: flex-end; }

/* skeleton */
.skeleton { border: 1px solid var(--border); border-radius: 12px; background: #111116; }
.skeleton-box { aspect-ratio: 16/9; background: linear-gradient(90deg, #191924 25%, #1f1f2c 50%, #191924 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
.skeleton-line { height: 12px; margin: 6px 0; border-radius: 6px; background: linear-gradient(90deg, #191924 25%, #1f1f2c 50%, #191924 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
.skeleton-pill { height: 24px; width: 64px; border-radius: 999px; background: linear-gradient(90deg, #191924 25%, #1f1f2c 50%, #191924 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
</style>