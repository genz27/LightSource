<template>
  <AppLayout>
    <div class="assets">
      <div class="assets-header">
        <h2>Asset Library</h2>
        <div class="assets-controls">
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search assets..."
              @input="filterAssets"
            />
          </div>
          <select v-model="selectedFilter" @change="filterAssets">
            <option value="all">All Types</option>
            <option value="image">Images</option>
            <option value="video">Videos</option>
            <option value="audio">Audio</option>
          </select>
          <select v-model="selectedProvider" @change="filterAssets">
            <option value="">All Providers</option>
            <option v-for="p in providers" :key="p.name" :value="p.name">{{ p.display_name }}</option>
          </select>
          <select v-model="selectedVisibility" @change="filterAssets">
            <option value="all">All</option>
            <option value="public">Public</option>
            <option value="private">Private</option>
          </select>
          <div class="view-switch">
            <button class="pill sm" :class="{ active: onlyMine }" @click="setMine(true)">My Assets</button>
            <button class="pill sm" :class="{ active: !onlyMine }" @click="setMine(false)">Public</button>
          </div>
          <select v-model="sortBy" @change="sortAssets">
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name">Name A-Z</option>
            <option value="size">Size</option>
          </select>
          <button class="pill accent" @click="uploadAsset">
            Upload
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="muted">Loading...</div>
      <div v-else-if="loadError" class="error">{{ loadError }}</div>

      <div v-if="!isLoading && !loadError && filteredAssets.length === 0" class="muted">No assets</div>
      <div class="assets-grid">
        <div 
          v-for="asset in filteredAssets" 
          :key="asset.id"
          class="asset-card"
          @click="selectAsset(asset)"
        >
          <div class="asset-badges">
            <span class="badge" v-if="asset.isPublic">Public</span>
            <span class="badge ghost" v-else>Private</span>
            <span class="provider-badge" v-if="asset.provider">{{ asset.provider }}</span>
          </div>
          <div class="asset-preview">
            <img 
              v-if="asset.type === 'image'"
              :src="asset.thumbnail" 
              :alt="asset.name"
              @error="handleImageError"
            />
            <video 
              v-else-if="asset.type === 'video'"
              class="asset-video"
              :poster="videoPoster(asset)"
              :src="asset.url"
              preload="auto"
              muted
              playsinline
              crossorigin="anonymous"
              :data-id="asset.id"
              @loadeddata="onVideoLoaded"
              @error="onVideoError"
            >
              <source :src="asset.url" type="video/mp4" />
            </video>
            <div v-if="asset.status && asset.status !== 'completed'" class="asset-overlay">
              <span class="badge ghost">{{ asset.status === 'running' ? `Processing ${asset.progress}%` : 'Queued' }}</span>
            </div>
            <div v-else-if="asset.type === 'audio'" class="asset-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/>
                <circle cx="18" cy="16" r="3"/>
              </svg>
            </div>
            <div class="asset-duration" v-if="asset.duration">
              {{ formatDuration(asset.duration) }}
            </div>
          </div>
          <div class="asset-info">
            <h4>{{ asset.name }}</h4>
            <p v-if="asset.size">{{ formatFileSize(asset.size) }}</p>
            <div class="asset-meta">
              <span class="asset-type">{{ asset.type }}</span>
              <span class="asset-date">{{ formatDate(asset.createdAt) }}</span>
            </div>
          </div>
          <div class="asset-actions" @click.stop>
            <button 
              class="action-btn"
              @click="downloadAsset(asset)"
              title="Download"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </button>
            <button 
              class="action-btn delete"
              v-if="canToggle(asset)"
              @click="deleteAsset(asset)"
              title="Delete"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                <line x1="10" y1="11" x2="10" y2="17"/>
                <line x1="14" y1="11" x2="14" y2="17"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div class="pager" v-if="!isLoading && !loadError && filteredAssets.length">
        <button class="pill sm" :disabled="page <= 1" @click="prevPage">Prev</button>
        <span class="muted">Page {{ page }}</span>
        <button class="pill sm" :disabled="assets.length < limit" @click="nextPage">Next</button>
      </div>

      <div v-if="selectedAsset" class="asset-sidebar" :class="{ open: showSidebar }">
        <div class="sidebar-header">
          <h3>Asset Details</h3>
          <button class="close-btn" @click="closeSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="sidebar-content">
          <div class="asset-preview-large">
            <img 
              v-if="selectedAsset.type === 'image'"
              :src="selectedAsset.url" 
              :alt="selectedAsset.name"
              @error="handleImageError"
            />
            <video v-else-if="selectedAsset.type === 'video'" class="asset-preview-video" :poster="videoPoster(selectedAsset)" :src="selectedAsset.url" preload="metadata" controls playsinline muted @error="onVideoError">
              <source :src="selectedAsset.url" type="video/mp4" />
            </video>
            <div v-else-if="selectedAsset.type === 'audio'" class="asset-preview-audio">
              <div class="audio-placeholder">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
                <p>Audio Player</p>
              </div>
            </div>
          </div>
          <div class="asset-details">
            <h4>{{ selectedAsset.name }}</h4>
            <div class="detail-row">
              <span>Type:</span>
              <span>{{ selectedAsset.type }}</span>
            </div>
            <div class="detail-row">
              <span>Size:</span>
              <span>{{ formatFileSize(selectedAsset.size) }}</span>
            </div>
            <div class="detail-row">
              <span>Provider:</span>
              <span>{{ selectedAsset.provider || '—' }}</span>
            </div>
            <div class="detail-row">
              <span>Visibility:</span>
              <span>{{ selectedAsset.isPublic ? 'Public' : 'Private' }}</span>
            </div>
            <div class="detail-row">
              <span>Created:</span>
              <span>{{ formatDate(selectedAsset.createdAt) }}</span>
            </div>
            <div v-if="selectedAsset.duration" class="detail-row">
              <span>Duration:</span>
              <span>{{ formatDuration(selectedAsset.duration) }}</span>
            </div>
            <div class="detail-row">
              <span>Dimensions:</span>
              <span>{{ selectedAsset.dimensions || 'N/A' }}</span>
            </div>
          </div>
          <div class="sidebar-actions">
            <button class="pill" v-if="selectedAsset && canToggle(selectedAsset)" @click="togglePublic(selectedAsset)">{{ selectedAsset.isPublic ? 'Unpublish' : 'Publish' }}</button>
            <button class="pill accent" @click="useAsset(selectedAsset)">
              Use in Generator
            </button>
            <button class="ghost" @click="closeSidebar">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <div v-if="showUploadModal" class="modal-overlay" @click="closeUploadModal">
      <div class="modal" @click.stop>
        <h3>Upload Asset</h3>
        <div class="upload-area" @drop="handleDrop" @dragover.prevent>
          <div v-if="!uploadFile" class="upload-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            <p>Drag and drop files here or click to browse</p>
            <input 
              ref="fileInput"
              type="file" 
              @change="handleFileSelect"
              accept="image/*,video/*,audio/*"
              style="display: none"
            />
            <button class="pill" @click="($refs.fileInput as HTMLInputElement).click()">Browse Files</button>
          </div>
          <div v-else class="upload-preview">
            <h4>{{ uploadFile.name }}</h4>
            <p>{{ formatFileSize(uploadFile.size) }}</p>
            <button class="ghost" @click="uploadFile = null">Remove</button>
          </div>
        </div>
        <div class="modal-actions">
          <button class="ghost" @click="closeUploadModal">Cancel</button>
          <button 
            class="pill accent" 
            @click="confirmUpload"
            :disabled="!uploadFile"
          >
            Upload
          </button>
        </div>
          <div class="upload-options">
            <label class="option">
              <input type="checkbox" v-model="isPublicUpload" />
            <span>Publish publicly</span>
            </label>
            <input class="provider-input" v-model="providerInput" placeholder="Provider (optional)" />
          </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { listAssets as listAssetsApi, deleteAsset as deleteAssetApi, uploadAsset as uploadAssetApi, patchAssetPublic as patchAssetPublicApi } from '@/api/assets'
import { useAuthStore } from '@/stores/auth'
import { get as apiGet } from '@/api/client'

interface Asset {
  id: string
  name: string
  type: 'image' | 'video' | 'audio'
  size: number
  url: string
  thumbnail: string
  createdAt: string
  duration?: string
  dimensions?: string
  provider?: string
  isPublic: boolean
  ownerId?: string
  status?: 'queued' | 'running' | 'completed' | 'failed' | 'canceled'
  progress?: number
  jobId?: string
  isPending?: boolean
  prompt?: string
  style?: string
  seed?: number | null
  orientation?: 'landscape' | 'portrait' | null
}

type ProviderResponseDTO = { provider?: string; model?: string; request?: { prompt?: string; size?: string }; raw?: { input?: { prompt?: string; seed?: number; width?: number; height?: number } } }
type MetaDTO = { filename?: string; size?: string | number; style?: string; seed?: number | null; orientation?: 'landscape' | 'portrait' | null; model?: string; provider_response?: ProviderResponseDTO }
type AssetDTO = { id: string; type: 'image' | 'video' | 'audio'; provider?: string | null; url: string; preview_url?: string | null; meta?: MetaDTO | null; is_public: boolean; created_at: string; owner_id?: string | null }
type APIError = { status?: number; data?: { detail?: string; message?: string } }
type JobKind = 'text_to_image' | 'image_to_image' | 'text_to_video' | 'image_to_video'
type JobOutDTO = { id: string; prompt: string; kind: JobKind; model?: string | null; provider?: string | null; is_public: boolean; params?: Record<string, unknown> | null; status: 'queued' | 'running' | 'completed' | 'failed' | 'canceled'; progress: number; asset_id?: string | null; error?: string | null; created_at: string; updated_at: string; owner_id?: string | null }
type JobStatusOutDTO = { id: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'canceled'; progress: number; asset_id?: string | null; error?: string | null; updated_at: string }

const router = useRouter()
const auth = useAuthStore()
const searchQuery = ref('')
const selectedFilter = ref('all')
const selectedVisibility = ref<'all' | 'public' | 'private'>('all')
const providers = ref<{ name: string; display_name: string }[]>([])
const selectedProvider = ref('')
const sortBy = ref('newest')
const showSidebar = ref(false)
const showUploadModal = ref(false)
const uploadFile = ref<File | null>(null)
const onlyMine = ref(true)

const assets = ref<Asset[]>([])
const pendingAssets = ref<Asset[]>([])
const isLoading = ref(false)
const loadError = ref<string | null>(null)
const page = ref(1)
const limit = ref(20)

const selectedAsset = ref<Asset | null>(null)

const DEFAULT_POSTER = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMWE0MWQxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwTDEyMCA4MEwxNDAgMTAwTDEyMCAxMjBMMTAwIDEwMFoiIGZpbGw9IiM2NjY2NjYiLz4KPC9zdmc+'

const sanitizeUrl = (u: string | null | undefined): string => {
  if (!u) return ''
  return String(u).trim().replace(/^`+|`+$/g, '')
}

const mapAsset = (dto: AssetDTO): Asset => {
  const meta = dto.meta || {}
  const sz = meta.size as unknown
  const isSizeString = typeof sz === 'string' && /\d+x\d+/i.test(sz as string)
  const isSizeNumber = typeof sz === 'number' && Number.isFinite(sz as number)
  const pr = (meta.provider_response || {}) as ProviderResponseDTO
  const req = pr.request || {}
  const raw: { prompt?: string; seed?: number } = (pr && pr.raw && pr.raw.input) ? (pr.raw.input as { prompt?: string; seed?: number }) : {}
  const prompt = (req.prompt || raw.prompt) || undefined
  const style = typeof meta.style === 'string' ? meta.style || undefined : undefined
  const seed = typeof meta.seed === 'number' ? meta.seed : (typeof raw.seed === 'number' ? raw.seed : null)
  const orientation = (meta.orientation ?? null) as 'landscape' | 'portrait' | null
  return {
    id: dto.id,
    name: meta.filename ? meta.filename : dto.id,
    type: dto.type,
    size: isSizeNumber ? Number(sz as number) : 0,
    url: sanitizeUrl(dto.url),
    thumbnail: sanitizeUrl(dto.preview_url || dto.url),
    createdAt: dto.created_at,
    provider: dto.provider || undefined,
    isPublic: !!dto.is_public,
    ownerId: dto.owner_id || undefined,
    dimensions: isSizeString ? String(sz) : undefined,
    prompt,
    style,
    seed,
    orientation,
  }
}

const loadAssets = async () => {
  isLoading.value = true
  loadError.value = null
  try {
    const data = await listAssetsApi({ 
      type: selectedFilter.value !== 'all' ? selectedFilter.value : undefined,
      provider: selectedProvider.value || undefined,
      public: selectedVisibility.value === 'all' ? undefined : (selectedVisibility.value === 'public'),
      owner_only: onlyMine.value || undefined,
      page: page.value,
      limit: limit.value,
    })
    const items = (data && data.items) ? data.items : []
    assets.value = items.map(mapAsset)
  } catch (e: unknown) {
    const err = e as APIError
    const d = err?.data
    loadError.value = (d?.detail || d?.message) || 'Failed to load'
  } finally {
    isLoading.value = false
  }
}

const mapJobToAsset = (job: JobOutDTO): Asset => {
  const kind: JobKind = job.kind
  const type: 'image' | 'video' | 'audio' = (kind === 'text_to_video' || kind === 'image_to_video') ? 'video' : 'image'
  const isPending = job.status !== 'completed'
  return {
    id: `job_${job.id}`,
    name: `Pending: ${job.prompt}`,
    type,
    size: 0,
    url: '',
    thumbnail: DEFAULT_POSTER,
    createdAt: job.created_at,
    provider: job.provider || undefined,
    isPublic: !!job.is_public,
    ownerId: job.owner_id || undefined,
    status: job.status,
    progress: job.progress,
    jobId: job.id,
    isPending,
  } as Asset
}

const loadPendingJobs = async () => {
  try {
    const qs = new URLSearchParams()
    if (onlyMine.value) qs.set('owner_only', 'true')
    qs.set('limit', '20')
    const active = await apiGet(`/jobs/active?${qs.toString()}`) as JobStatusOutDTO[]
    const ids = Array.isArray(active) ? active.map(j => j.id) : []
    const jobs = await Promise.all(ids.map(id => apiGet(`/jobs/${id}`).catch(() => null)))
    const items: Asset[] = []
    for (const j of jobs) {
      if (!j) continue
      const job = j as JobOutDTO
      const hasAsset = !!job.asset_id && assets.value.some(a => a.id === job.asset_id)
      if (hasAsset) continue
      items.push(mapJobToAsset(job))
    }
    pendingAssets.value = items
  } catch {}
}

const loadProviders = async () => {
  try {
    const data = await apiGet('/providers') as { name: string; display_name: string }[]
    providers.value = Array.isArray(data) ? data : []
  } catch {}
}

onMounted(async () => {
  if (!auth.user) {
    onlyMine.value = false
    selectedVisibility.value = 'public'
  }
  await Promise.all([loadProviders(), loadAssets()])
  await loadPendingJobs()
  startPendingPoll()
})
let pendingPollTimer: number | null = null
const startPendingPoll = () => {
  if (pendingPollTimer !== null) { clearInterval(pendingPollTimer); pendingPollTimer = null }
  pendingPollTimer = window.setInterval(() => { loadPendingJobs() }, 2000)
}
onUnmounted(() => { if (pendingPollTimer !== null) { clearInterval(pendingPollTimer); pendingPollTimer = null } })
const filteredAssets = computed(() => {
  let filtered = [...pendingAssets.value, ...assets.value]

  // Filter by search query
  if (searchQuery.value) {
    filtered = filtered.filter(asset => 
      asset.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // Filter by type
  if (selectedFilter.value !== 'all') {
    filtered = filtered.filter(asset => asset.type === selectedFilter.value)
  }
  if (onlyMine.value && auth.user) {
    const uid = auth.user.id
    filtered = filtered.filter(asset => asset.ownerId ? asset.ownerId === uid : true)
  }

  // Sort assets
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'newest':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      case 'oldest':
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      case 'name':
        return a.name.localeCompare(b.name)
      case 'size':
        return b.size - a.size
      default:
        return 0
    }
  })

  return filtered
})

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMWE0MWQxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwTDEyMCA4MEwxNDAgMTAwTDEyMCAxMjBMMTAwIDEwMFoiIGZpbGw9IiM2NjY2NjYiLz4KPC9zdmc+'
}

const filterAssets = () => {
  page.value = 1
  loadAssets()
  loadPendingJobs()
}

const sortAssets = () => {
  // Computed property handles sorting
}

const setMine = (flag: boolean) => {
  onlyMine.value = flag
  selectedVisibility.value = flag ? 'all' : 'public'
  page.value = 1
  loadAssets()
  loadPendingJobs()
}
const prevPage = async () => { if (page.value > 1) { page.value -= 1; await loadAssets() } }
const nextPage = async () => { page.value += 1; await loadAssets() }
const posterCache = ref<Record<string, string>>({})

const videoPoster = (asset: Asset) => {
  const cached = posterCache.value[asset.id]
  if (cached) return cached
  const t = asset.thumbnail || ''
  const isImage = t.startsWith('data:image/') || /\.(png|jpg|jpeg|webp)$/i.test(t)
  return isImage ? t : DEFAULT_POSTER
}

const onVideoLoaded = (e: Event) => {
  const v = e.target as HTMLVideoElement
  try {
    v.muted = true
    const p = v.play()
    if (p && typeof p.then === 'function') {
      p.then(() => setTimeout(() => v.pause(), 80)).catch(() => {})
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

const canToggle = (asset: Asset | null) => {
  if (!asset) return false
  const u = auth.user
  if (!u) return false
  if (u.role === 'admin') return true
  return asset.ownerId && u.id === asset.ownerId
}

const togglePublic = async (asset: Asset | null) => {
  if (!asset) return
  if (!canToggle(asset)) { alert('Unauthorized'); return }
  try {
    const updated = await patchAssetPublicApi(asset.id, !asset.isPublic)
    const mapped = mapAsset(updated as AssetDTO)
    assets.value = assets.value.map(a => a.id === mapped.id ? mapped : a)
    selectedAsset.value = mapped
  } catch {}
}
const selectAsset = (asset: Asset) => {
  selectedAsset.value = asset
  showSidebar.value = true
}

const closeSidebar = () => {
  selectedAsset.value = null
  showSidebar.value = false
}

const downloadAsset = (asset: Asset) => {
  const link = document.createElement('a')
  link.href = asset.url
  link.download = asset.name
  link.click()
}

const deleteAsset = async (asset: Asset) => {
  if (!canToggle(asset)) { alert('Unauthorized'); return }
  if (!confirm(`Are you sure you want to delete "${asset.name}"?`)) return
  try {
    await deleteAssetApi(asset.id)
    assets.value = assets.value.filter(a => a.id !== asset.id)
    if (selectedAsset.value?.id === asset.id) {
      closeSidebar()
    }
  } catch (e: unknown) {
    const err = e as APIError
    const d = err?.data
    const msg = (d?.detail || d?.message) || 'Delete failed'
    alert(msg)
  }
}

const useAsset = (asset: Asset) => {
  try {
    if (asset && asset.url) {
      sessionStorage.setItem('generator_source_url', asset.url)
      sessionStorage.setItem('generator_source_type', asset.type)
      if (asset.prompt) sessionStorage.setItem('generator_prompt', asset.prompt)
      if (asset.dimensions) sessionStorage.setItem('generator_size', asset.dimensions)
      if (asset.style) sessionStorage.setItem('generator_style', asset.style)
      if (asset.seed !== null && asset.seed !== undefined) sessionStorage.setItem('generator_seed', String(asset.seed))
      if (asset.orientation) sessionStorage.setItem('generator_orientation', asset.orientation)
    }
  } catch {}
  router.push('/generator')
}

const uploadAsset = () => {
  showUploadModal.value = true
}

const closeUploadModal = () => {
  showUploadModal.value = false
  uploadFile.value = null
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    uploadFile.value = files[0] as File
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    uploadFile.value = files[0] as File
  }
}

const isPublicUpload = ref(true)
const providerInput = ref('')

const confirmUpload = async () => {
  if (!uploadFile.value) return
  try {
    const dto = await uploadAssetApi(uploadFile.value, isPublicUpload.value, providerInput.value || undefined)
    const item = mapAsset(dto)
    assets.value.unshift(item)
    closeUploadModal()
  } catch (e: unknown) {
    const err = e as APIError
    const d = err?.data
    const msg = (d?.detail || d?.message) || 'Upload failed'
    alert(msg)
  }
}

const formatFileSize = (bytes: number) => {
  if (typeof bytes !== 'number' || !Number.isFinite(bytes)) return '—'
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const formatDuration = (duration: string) => {
  return duration
}
</script>

<style scoped>
.assets {
  display: grid;
  gap: 24px;
}

.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.assets-header h2 {
  margin: 0;
  color: var(--text);
}

.assets-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.view-switch {
  display: flex;
  gap: 6px;
}

.view-switch .pill.sm.active {
  background: var(--accent);
  color: #1a1a1a;
}

.search-box {
  position: relative;
}

.search-box input {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-soft);
  color: var(--text);
  font-family: inherit;
  min-width: 200px;
}

.search-box input:focus {
  outline: none;
  border-color: var(--accent);
}

.assets-controls select {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-soft);
  color: var(--text);
  font-family: inherit;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
}

.asset-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.asset-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.asset-preview {
  position: relative;
  aspect-ratio: 16/9;
  overflow: hidden;
  background: var(--panel-soft);
}
.asset-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
}

.asset-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.asset-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: var(--panel-soft);
}

.asset-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--muted);
  opacity: 0.6;
}

.asset-icon svg {
  width: 48px;
  height: 48px;
}

.asset-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.asset-badges {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  gap: 6px;
  z-index: 2;
}

.badge {
  background: var(--accent);
  color: #1a1a1a;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.badge.ghost {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.provider-badge {
  background: var(--panel-soft);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.asset-info {
  padding: 16px;
}

.asset-info h4 {
  margin: 0 0 8px 0;
  color: var(--text);
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-info p {
  margin: 0 0 12px 0;
  color: var(--muted);
  font-size: 14px;
}

.asset-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--muted);
}

.asset-type {
  background: var(--accent);
  color: #1a1a1a;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.asset-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.asset-card:hover .asset-actions {
  opacity: 1;
}

.action-btn {
  background: rgba(0, 0, 0, 0.8);
  border: none;
  border-radius: 4px;
  padding: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  color: white;
}

.action-btn:hover {
  background: var(--accent);
}

.action-btn.delete:hover {
  background: #ef4444;
}

.asset-sidebar {
  position: fixed;
  top: 0;
  right: -400px;
  width: 400px;
  height: 100vh;
  background: var(--panel);
  border-left: 1px solid var(--border);
  transition: right 0.3s ease;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.asset-sidebar.open {
  right: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--border);
}

.sidebar-header h3 {
  margin: 0;
  color: var(--text);
}

.close-btn {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.close-btn:hover {
  background: var(--panel-soft);
  color: var(--text);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.asset-preview-large {
  margin-bottom: 24px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.asset-preview-large img {
  width: 100%;
  height: auto;
  display: block;
}

.asset-preview-video {
  width: 100%;
  height: auto;
  display: block;
  background: var(--panel-soft);
  max-height: 60vh;
}

.video-placeholder,
.audio-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  background: var(--panel-soft);
  color: var(--muted);
  text-align: center;
}

.video-placeholder svg,
.audio-placeholder svg {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.asset-details {
  margin-bottom: 24px;
}

.asset-details h4 {
  margin: 0 0 16px 0;
  color: var(--text);
  font-size: 18px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span:first-child {
  color: var(--muted);
}

.detail-row span:last-child {
  color: var(--text);
  font-weight: 500;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 24px 0;
  color: var(--text);
}

.upload-area {
  border: 2px dashed var(--border);
  border-radius: 8px;
  padding: 48px 24px;
  text-align: center;
  margin-bottom: 24px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover {
  border-color: var(--accent);
  background: var(--panel-soft);
}

.upload-placeholder svg {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  display: block;
  margin-left: auto;
  margin-right: auto;
  opacity: 0.6;
}

.upload-placeholder p {
  margin: 0 0 16px 0;
  color: var(--muted);
}

.upload-preview {
  text-align: center;
}

.upload-preview h4 {
  margin: 0 0 8px 0;
  color: var(--text);
}

.upload-preview p {
  margin: 0 0 16px 0;
  color: var(--muted);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.upload-options {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.upload-options .option {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text);
}

.provider-input {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-soft);
  color: var(--text);
}

.error { color: #ef4444; }

@media (max-width: 768px) {
  .assets-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .assets-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box input {
    min-width: auto;
  }
  
  .assets-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
  
  .asset-sidebar {
    width: 100%;
    right: -100%;
  }
}
</style>
const videoPoster = (asset: Asset) => {
  const t = asset.thumbnail || ''
  const isImage = t.startsWith('data:image/') || /\.(png|jpg|jpeg|webp)$/i.test(t)
  return isImage ? t : DEFAULT_POSTER
}

const onVideoLoaded = (e: Event) => {
  const v = e.target as HTMLVideoElement
  try {
    v.muted = true
    const p = v.play()
    if (p && typeof p.then === 'function') {
      p.then(() => setTimeout(() => v.pause(), 80)).catch(() => {})
    }
  } catch {}
}

const onVideoError = (e: Event) => {
  const v = e.target as HTMLVideoElement
  try { v.poster = DEFAULT_POSTER } catch {}
}
const setMine = (flag: boolean) => {
  onlyMine.value = flag
  selectedVisibility.value = flag ? 'all' : 'public'
  loadAssets()
}