<template>
  <AppLayout>
    <div class="generator">
      <div class="generator-form">
        <h2>AI Generator</h2>
        <div class="balance-bar">
          <span>Balance: {{ walletBalance !== null ? walletBalance.toFixed(2) : '—' }}</span>
          <span>Estimated cost: {{ estimatedCost.toFixed(2) }}</span>
          <span v-if="lastCharge>0" class="muted">Last charged: {{ lastCharge.toFixed(2) }}</span>
          <span v-if="walletBalance !== null && walletBalance < estimatedCost" class="insufficient">Insufficient balance</span>
        </div>
        <form @submit.prevent="generateContent">
          <div class="form-group">
            <label>Prompt</label>
            <textarea 
              v-model="form.prompt" 
              placeholder="Describe what you want to create..."
              rows="4"
              required
            ></textarea>
            <div class="input-hint">Be descriptive and specific for better results</div>
          </div>

          <div class="form-group">
            <label>Mode</label>
            <select v-model="form.mode">
              <option value="text_to_image">Text → Image</option>
              <option value="image_to_image">Image → Image</option>
              <option value="text_to_video">Text → Video</option>
              <option value="image_to_video">Image → Video</option>
            </select>
          </div>

          <div class="form-group">
            <label>Model</label>
            <select v-if="isImageMode" v-model="form.model">
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <div v-else class="muted">Model: {{ availableModels[0] || 'sora2-video' }}</div>
          </div>

          <div class="form-row">
            <div class="form-group" v-if="isImageMode">
              <label>Size</label>
              <select v-model="form.size">
                <option value="768x768">Square (768x768)</option>
                <option value="1024x1024">Square (1024x1024)</option>
                <option value="1280x1280">Square (1280x1280)</option>
                <option value="1500x1500">Square (1500x1500)</option>
                <option value="1280x720">Landscape (1280x720)</option>
                <option value="1366x768">Landscape (1366x768)</option>
                <option value="1440x900">Landscape (1440x900)</option>
                <option value="1500x1000">Landscape (1500x1000)</option>
                <option value="720x1280">Portrait (720x1280)</option>
                <option value="768x1366">Portrait (768x1366)</option>
                <option value="900x1440">Portrait (900x1440)</option>
                <option value="1000x1500">Portrait (1000x1500)</option>
              </select>
            </div>

            <div class="form-group" v-if="isImageMode">
              <label>Seed</label>
              <input 
                type="number" 
                min="0" 
                step="1" 
                v-model.number="form.seed"
                placeholder="Leave blank for random seed"
              />
              <div class="input-hint">Set a fixed seed for reproducible results</div>
            </div>
          </div>

          <div class="form-group" v-if="isImageMode">
            <label>Style (Optional)</label>
            <input 
              v-model="form.style" 
              type="text" 
              placeholder="e.g., cyberpunk, watercolor, photorealistic"
            />
          </div>

          <div class="form-group" v-if="form.mode === 'text_to_video' || form.mode === 'image_to_video'">
            <label>Orientation</label>
            <div class="segmented">
              <button type="button" :class="['pill', 'segmented-item', { active: form.orientation === 'landscape' }]" @click="form.orientation = 'landscape'">
                <svg class="segmented-icon" viewBox="0 0 24 24">
                  <rect x="3" y="7" width="18" height="10" rx="3"/>
                </svg>
                <span>Landscape</span>
              </button>
              <button type="button" :class="['pill', 'segmented-item', { active: form.orientation === 'portrait' }]" @click="form.orientation = 'portrait'">
                <svg class="segmented-icon" viewBox="0 0 24 24">
                  <rect x="7" y="3" width="10" height="18" rx="3"/>
                </svg>
                <span>Portrait</span>
              </button>
            </div>
          </div>

          <div class="form-group" v-if="form.mode === 'image_to_image' || form.mode === 'image_to_video'">
            <label>Source Image</label>
            <div class="upload-area" :class="{ 'dragging': dropActive }" @dragover.prevent="onDragOver" @dragenter.prevent="onDragEnter" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop">
              <input id="source-file" type="file" accept="image/*" multiple class="file-input" @change="onSelectSourceImages" />
              <label for="source-file" class="pill accent upload-btn">Choose Image</label>
              <button type="button" class="pill" style="margin-left:8px" @click="openFilePicker">Add More Images</button>
              <div v-if="sourceImageFiles.length" class="file-selected">{{ sourceImageFiles.length }} file(s) selected</div>
              <div class="preview-grid" v-if="sourceItems.length">
                <div class="preview-item" v-for="(item, i) in sourceItems" :key="item.src + ':' + i">
                  <img :src="item.src" alt="preview" class="preview-thumb" @error="handleImageError" />
                  <button type="button" class="remove-btn" @click="removeSource(item)">✕</button>
                </div>
              </div>
              <div class="upload-actions">
                <button class="ghost" @click="clearAllSources">Clear All</button>
              </div>
              <div class="input-hint">Paste URL(s) or choose images. You can drag & drop files here.</div>
            </div>
          </div>

            <div class="form-actions">
              <button 
                type="submit" 
                class="pill accent"
                :disabled="isGenerating || (((form.mode === 'text_to_video') || (form.mode === 'image_to_video')) && walletBalance !== null && walletBalance < estimatedCost)"
              >
                {{ isGenerating ? 'Generating...' : 'Generate' }}
              </button>
            <button 
              v-if="currentJobId"
              type="button" 
              class="ghost"
              @click="cancelCurrentJob"
              :disabled="isGenerating && currentStatus === 'running'"
            >
              Cancel Job
            </button>
            <button 
              type="button" 
              class="ghost"
              @click="resetForm"
              :disabled="isGenerating"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      <div class="generator-results">
        <div class="workspace-header">
          <h3>Comparison</h3>
        </div>
        <div class="workspace">
          <div :class="['workspace-canvas', latestResult ? getAspectClass(latestResult) : 'aspect-landscape']">
            <template v-if="latestResult">
              <video v-if="latestResult.video" :src="latestResult.video" controls playsinline muted></video>
              <img v-else :src="latestResult.image" :alt="latestResult.prompt" @error="handleImageError" />
            </template>
            <div v-else class="workspace-placeholder">
              <svg class="minimal-icon" viewBox="0 0 48 48">
                <rect x="6" y="10" width="36" height="28" rx="4"/>
                <circle cx="16" cy="20" r="3"/>
                <path d="M12 32 L22 24 L28 30 L36 22"/>
              </svg>
              <p>Your generated content will appear here</p>
            </div>
            <div v-if="isGenerating" class="workspace-overlay">
              <div class="loader"></div>
              <p>Job {{ currentJobId }} · {{ currentStatus }} · {{ progress }}%</p>
            </div>
          </div>
        </div>

        <div class="results-header">
          <h3>Recent Generations <span class="count" v-if="results.length">{{ results.length }}</span></h3>
          <button class="pill" @click="clearResults">Clear All</button>
        </div>

        <div v-if="results.length === 0 && !isGenerating" class="empty-state">
          <svg class="minimal-icon" viewBox="0 0 48 48">
            <rect x="6" y="10" width="36" height="28" rx="4"/>
            <circle cx="16" cy="20" r="3"/>
            <path d="M12 32 L22 24 L28 30 L36 22"/>
          </svg>
          <p>Your generated content will appear here</p>
        </div>

        <div v-else class="results-grid">
          <div v-for="result in results" :key="result.id" class="result-card">
            <div :class="['result-image', getAspectClass(result)]">
              <video v-if="result.video" :src="result.video" controls playsinline muted></video>
              <img v-else :src="result.image" :alt="result.prompt" @error="handleImageError" />
              <div class="result-overlay">
                <button class="action-btn" @click="viewFullSize(result)" title="View Full Size">🔍</button>
                <button class="action-btn" @click="downloadMedia(result)" title="Download">💾</button>
                <button class="action-btn" @click="regenerate(result)" title="Regenerate">🔄</button>
                <button class="action-btn delete" @click="deleteResult(result)" title="Delete">🗑️</button>
              </div>
            </div>
            <div class="result-info">
              <p class="result-prompt">{{ truncateText(result.prompt, 80) }}</p>
            <div class="result-meta">
              <div class="meta-left">
                <span class="result-model">{{ result.model || '—' }}</span>
                <span class="media-tag">{{ result.video ? 'Video' : 'Image' }}</span>
              </div>
              <span class="result-date">{{ formatDate(result.createdAt) }}</span>
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Full Size Modal -->
    <div v-if="fullSizeResult" class="modal-overlay" @click="fullSizeResult = null">
      <div class="modal" @click.stop>
        <video v-if="fullSizeResult.video" :src="fullSizeResult.video" controls playsinline class="full-size-image"></video>
        <img v-else :src="fullSizeResult.image" :alt="fullSizeResult.prompt" class="full-size-image" />
        <div class="modal-actions">
          <button class="ghost" @click="fullSizeResult = null">Close</button>
          <button class="pill accent" @click="downloadMedia(fullSizeResult)">Download</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { get, post } from '@/api/client'

interface GenerationResult {
  id: string
  prompt: string
  image?: string
  video?: string
  model: string
  size: string
  seed: number | null
  style?: string
  createdAt: string
  orientation?: 'landscape' | 'portrait'
}

interface GenerationForm {
  prompt: string
  mode: 'text_to_image' | 'text_to_video' | 'image_to_image' | 'image_to_video'
  model: string
  size: string
  seed: number | null
  style: string
  orientation: 'landscape' | 'portrait'
}

const form = reactive<GenerationForm>({
  prompt: '',
  mode: 'text_to_image',
  model: '',
  size: '1024x1024',
  seed: null,
  style: '',
  orientation: 'landscape'
})

interface ProviderInfo { name: string; display_name?: string; models: string[]; capabilities: string[]; enabled: boolean; notes?: string; base_url?: string }
const providers = ref<ProviderInfo[]>([])
const walletBalance = ref<number | null>(null)
const prices = ref<Record<string, number>>({ text_to_image: 5.0, text_to_video: 20.0, image_to_video: 12.0 })
const estimatedCost = computed<number>(() => {
  const kind = form.mode === 'image_to_image' ? 'image_to_image' : form.mode
  return prices.value[kind as keyof typeof prices.value] || 0
})
const availableModels = computed<string[]>(() => {
  const p = providers.value
  const models: string[] = []
  const wantImage = form.mode === 'text_to_image' || form.mode === 'image_to_image'
  const wantVideo = form.mode === 'text_to_video' || form.mode === 'image_to_video'
  for (const item of p) {
    if (wantImage && item.capabilities.includes('image')) {
      for (const m of item.models || []) models.push(m)
    }
    if (wantVideo && item.capabilities.includes('video')) {
      for (const m of item.models || []) models.push(m)
    }
  }
  const unique = Array.from(new Set(models))
  if (form.mode === 'text_to_image') {
    return unique.filter(m => !m.includes('edit')).length ? unique.filter(m => !m.includes('edit')) : ['qwen-image']
  }
  if (form.mode === 'image_to_image') {
    const edits = unique.filter(m => m.includes('edit'))
    return edits.length ? edits : ['qwen-image-edit']
  }
  return unique.length ? unique : ['sora2-video']
})

const results = ref<GenerationResult[]>([])
const jobModelMap = ref<Record<string, string>>({})
const latestResult = computed((): GenerationResult | null => results.value[0] ?? null)
const isGenerating = ref(false)
const fullSizeResult = ref<GenerationResult | null>(null)
const currentJobId = ref<string | null>(null)
const currentStatus = ref<string>('queued')
const progress = ref<number>(0)
const lastCharge = ref<number>(0)
let pollTimer: number | null = null
const isImageMode = computed(() => form.mode === 'text_to_image' || form.mode === 'image_to_image')
const sourceImagePreview = ref<string | null>(null)
const sourceImageText = ref<string>('')
const sourceImageFile = ref<File | null>(null)
const sourceImageFiles = ref<File[]>([])
const sourceFilePreviews = ref<string[]>([])
const dropActive = ref(false)

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMWE0MWQxIi8+CjxwYXRoIGQ9Ik0xMDAgMTAwTDEyMCA4MEwxNDAgMTAwTDEyMCAxMjBMMTAwIDEwMFoiIGZpbGw9IiM2NjY2NjYiLz4KPC9zdmc+'
}

//

const pollStatus = async (jobId: string) => {
  if (pollTimer !== null) { clearInterval(pollTimer); pollTimer = null }
  currentJobId.value = jobId
  pollTimer = window.setInterval(async () => {
    try {
      const s = await get(`/jobs/${jobId}/status`)
      currentStatus.value = s.status
      progress.value = s.progress
      if (s.status === 'completed' || s.status === 'failed' || s.status === 'canceled') {
        if (pollTimer !== null) { clearInterval(pollTimer); pollTimer = null }
        isGenerating.value = false
        if (s.status === 'completed') {
          await loadResult(jobId)
        }
      }
    } catch {
      if (pollTimer !== null) { clearInterval(pollTimer); pollTimer = null }
      isGenerating.value = false
    }
  }, 1500)
}

const loadResult = async (jobId: string) => {
  try {
    if (isImageMode.value) {
      const r = await get(`/v1/images/${jobId}`)
      const url = r?.result_url || r?.image_url
      if (url) pushResult(jobId, url, false)
    } else {
      const r = await get(`/v1/videos/${jobId}`)
      const url = r?.video_url || r?.result_url
      if (url) pushResult(jobId, url, true)
    }
  } catch {}
}

const pushResult = (jobId: string, url: string, isVideo: boolean) => {
  const base = {
    id: jobId,
    prompt: form.prompt,
    model: (jobModelMap.value[jobId] || form.model || '—'),
    size: form.size,
    seed: form.seed,
    style: form.style,
    createdAt: new Date().toISOString()
  } as GenerationResult
  if (isVideo) { base.video = url; base.orientation = form.orientation } else { base.image = url }
  results.value.unshift(base)
  try { delete jobModelMap.value[jobId] } catch {}
}

const onSelectSourceImages = (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  addFiles(files)
  const first = files[0]
  sourceImageFile.value = first || null
  if (first) {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      sourceImageText.value = result
      sourceImagePreview.value = result
    }
    reader.readAsDataURL(first)
  } else {
    sourceImagePreview.value = null
    sourceImageText.value = ''
  }
}

const addFiles = (files: File[]) => {
  for (const f of files) {
    sourceImageFiles.value.push(f)
    const reader = new FileReader()
    reader.onload = () => { sourceFilePreviews.value.push(reader.result as string) }
    reader.readAsDataURL(f)
  }
}

const onDragOver = () => { dropActive.value = true }
const onDragEnter = () => { dropActive.value = true }
const onDragLeave = () => { dropActive.value = false }
const onDrop = (e: DragEvent) => {
  dropActive.value = false
  const dt = e.dataTransfer
  if (!dt) return
  const files = dt.files ? Array.from(dt.files) : []
  if (files.length) addFiles(files)
}

const openFilePicker = () => { const el = document.getElementById('source-file') as HTMLInputElement | null; el?.click() }

const _extFromMime = (mime: string) => {
  const m = (mime || '').toLowerCase()
  if (m.includes('jpeg')) return 'jpg'
  if (m.includes('png')) return 'png'
  if (m.includes('bmp')) return 'bmp'
  if (m.includes('tiff')) return 'tiff'
  if (m.includes('webp')) return 'webp'
  return 'jpg'
}

const makeUploadFileName = (file: File) => {
  const name = file.name || 'image'
  const ext = name.includes('.') ? name.split('.').pop()!.toLowerCase() : _extFromMime(file.type || '')
  const rand = Math.random().toString(36).slice(2, 8)
  return `ls-${Date.now()}-${rand}.${ext}`
}

const uploadToExternal = async (file: File): Promise<string> => {
  const fname = makeUploadFileName(file)
  const fd = new FormData()
  fd.append('file', file)
  fd.append('filename', fname)
  const resp = await post('/v1/uploads/external', fd)
  const url = (resp && (resp.url as string)) || ''
  if (!url) throw new Error('upload failed')
  return url
}

const parseUrls = (text: string): string[] => {
  const parts = (text || '').split(/[\s,;]+/).map(s => s.trim()).filter(Boolean)
  return parts.filter(u => u.startsWith('http://') || u.startsWith('https://'))
}

const sourceItems = computed<{ kind: 'file' | 'url'; src: string; index: number }[]>(() => {
  const files = sourceFilePreviews.value.map((src, i) => ({ kind: 'file' as const, src, index: i }))
  const urls = parseUrls(sourceImageText.value).map((src, i) => ({ kind: 'url' as const, src, index: i }))
  return [...files, ...urls]
})

const removeSource = (item: { kind: 'file' | 'url'; index: number }) => {
  if (item.kind === 'file') {
    sourceImageFiles.value.splice(item.index, 1)
    sourceFilePreviews.value.splice(item.index, 1)
  } else {
    const urls = parseUrls(sourceImageText.value)
    urls.splice(item.index, 1)
    sourceImageText.value = urls.join(' ')
  }
}

const clearAllSources = () => { sourceImageFiles.value = []; sourceFilePreviews.value = []; sourceImageText.value = ''; sourceImagePreview.value = null }
watch(sourceImageText, (val) => { const v = (val || '').trim(); sourceImagePreview.value = v ? v : null })

const generateContent = async () => {
  try {
    if (isImageMode.value) {
      const parts = (form.size || '').split('x')
      if (parts.length === 2) {
        const w = Number(parts[0]); const h = Number(parts[1])
        if (Number.isFinite(w) && Number.isFinite(h)) {
          if (w > 1500 || h > 1500) {
            alert('Size must be within 1500x1500')
            return
          }
        }
      }
    }
    const kindForPrice = form.mode === 'image_to_image' ? 'image_to_image' : form.mode
    const required = Number((prices.value as Record<string, number>)[kindForPrice]) || 0
    try {
      const w = await get('/billing/wallet') as { balance: number }
      walletBalance.value = typeof w?.balance === 'number' ? w.balance : walletBalance.value
      const isVideoKind = (form.mode === 'text_to_video') || (form.mode === 'image_to_video')
      if (typeof w?.balance === 'number' && isVideoKind && w.balance < required) {
        alert('Insufficient balance. Cannot generate content.')
        return
      }
    } catch {}
    const hasSource = ((sourceImageText.value || '').trim().length > 0) || (sourceImageFiles.value.length > 0)
    if (form.mode === 'image_to_image' && (form.model || '').includes('edit') && !hasSource) {
      form.mode = 'text_to_image'
      form.model = availableModels.value[0] || 'qwen-image'
    }
    isGenerating.value = true
    currentStatus.value = 'queued'
    progress.value = 0
    if (form.mode === 'image_to_image' && (form.model || '').includes('edit')) {
      if (!sourceImageText.value && sourceImageFiles.value.length === 0) throw new Error('source image required')
      const textVal = (sourceImageText.value || '').trim()
      const urls: string[] = []
      if (sourceImageFiles.value.length > 0) {
        currentStatus.value = 'uploading'
        for (const f of sourceImageFiles.value) {
          const u = await uploadToExternal(f)
          urls.push(u)
        }
      } else {
        const parsed = parseUrls(textVal)
        if (parsed.length === 0) throw new Error('Qwen Image Edit requires accessible URL(s)')
        urls.push(...parsed)
      }
      const payload: Record<string, unknown> = { model: form.model || (availableModels.value[0] ?? 'qwen-image-edit'), prompt: form.prompt, size: form.size }
      if (urls.length > 1) payload.images = urls
      else payload.image = urls[0]
      const res = await post('/v1/images/edits', payload)
      const imageId = (res && (res.image_id as string)) || null
      if (imageId) { jobModelMap.value[imageId] = String(payload.model || '') }
      const charged = Number((res && (res.price_charged as number)) || 0)
      if (isFinite(charged) && charged > 0) {
        lastCharge.value = charged
        try { const w = await get('/billing/wallet') as { balance: number }; walletBalance.value = typeof w?.balance === 'number' ? w.balance : walletBalance.value } catch {}
      }
      if (imageId) await pollStatus(imageId)
      else { isGenerating.value = false }
    } else if (form.mode === 'image_to_video') {
      if (!sourceImageText.value) throw new Error('source image required')
      const modelName = `sora2-video-${form.orientation}`
      const payload: Record<string, unknown> = { model: modelName, prompt: form.prompt, image: sourceImageText.value }
      const res = await post('/v1/videos', payload)
      const videoId = (res && (res.video_id as string)) || null
      if (videoId) { jobModelMap.value[videoId] = modelName }
      if (videoId) await pollStatus(videoId)
      else { isGenerating.value = false }
    } else if (form.mode === 'text_to_video') {
      const modelName = `sora2-video-${form.orientation}`
      const payload: Record<string, unknown> = { model: modelName, prompt: form.prompt }
      const res = await post('/v1/videos', payload)
      const videoId = (res && (res.video_id as string)) || null
      if (videoId) { jobModelMap.value[videoId] = modelName }
      if (videoId) await pollStatus(videoId)
      else { isGenerating.value = false }
    } else {
      const fd = new FormData()
      fd.append('prompt', form.prompt)
      fd.append('kind', form.mode)
      fd.append('model', form.model || (availableModels.value[0] ?? 'qwen-image'))
      fd.append('is_public', 'true')
      if (isImageMode.value) {
        fd.append('size', form.size)
        fd.append('style', form.style || '')
        if (form.seed !== null && !Number.isNaN(form.seed)) fd.append('seed', String(form.seed))
      }
      const job = await post('/jobs', fd)
      try {
        const m = fd.get('model')
        jobModelMap.value[job.id] = typeof m === 'string' ? m : (form.model || '')
      } catch {}
      await pollStatus(job.id)
    }
  } catch (e: unknown) {
    const err = e as { status?: number; data?: { detail?: string; message?: string } }
    const status = err?.status
    const detail = err?.data?.detail || err?.data?.message || ''
    if (status === 401) {
      try { window.location.href = '/auth' } catch {}
      return
    }
    if (status === 402) {
      alert(typeof detail === 'string' ? detail : 'Insufficient balance. Cannot generate content.')
    }
    isGenerating.value = false
  }
}

const cancelCurrentJob = async () => {
  const jid = currentJobId.value
  if (!jid) return
  try { await post(`/jobs/${jid}/cancel`); currentStatus.value = 'canceled' } catch {}
}

const resetForm = () => {
  form.prompt = ''
  form.mode = 'text_to_image'
  form.model = availableModels.value[0] || 'qwen-image'
  form.size = '1024x1024'
  form.seed = null
  form.style = ''
  form.orientation = 'landscape'
  sourceImageText.value = ''
}

const viewFullSize = (result: GenerationResult) => { fullSizeResult.value = result }

const downloadMedia = (result: GenerationResult) => { const link = document.createElement('a'); const isVideo = !!result.video; link.href = isVideo ? (result.video as string) : (result.image as string); link.download = isVideo ? `generated-${result.id}.mp4` : `generated-${result.id}.png`; link.click() }

const regenerate = (result: GenerationResult) => {
  form.prompt = result.prompt
  form.model = result.model
  form.size = result.size
  form.seed = result.seed
  form.style = result.style || ''
  document.querySelector('.generator-form')?.scrollIntoView({ behavior: 'smooth' })
}

const deleteResult = (result: GenerationResult) => {
  const index = results.value.findIndex(r => r.id === result.id)
  if (index > -1) results.value.splice(index, 1)
}

const clearResults = () => { results.value = [] }

const truncateText = (text: string, maxLength: number) => { return text.length > maxLength ? text.substring(0, maxLength) + '...' : text }

const formatDate = (dateString: string) => { const d = new Date(dateString); const mm = String(d.getMonth()+1).padStart(2,'0'); const dd = String(d.getDate()).padStart(2,'0'); const hh = String(d.getHours()).padStart(2,'0'); const mi = String(d.getMinutes()).padStart(2,'0'); return `${mm}/${dd} ${hh}:${mi}` }

const getAspectClass = (result: GenerationResult) => {
  if (result.video) {
    return result.orientation === 'portrait' ? 'aspect-portrait' : 'aspect-landscape'
  }
  const parts = (result.size || '').split('x')
  if (parts.length === 2) {
    const w = Number(parts[0])
    const h = Number(parts[1])
    if (!Number.isNaN(w) && !Number.isNaN(h)) {
      if (w === h) return 'aspect-square'
      return w > h ? 'aspect-landscape' : 'aspect-portrait'
    }
  }
  return 'aspect-square'
}

onMounted(async () => {
  try { providers.value = await get('/providers') } catch {}
  try { const w = await get('/billing/wallet') as { balance: number }; walletBalance.value = typeof w?.balance === 'number' ? w.balance : null } catch {}
  try { const p = await get('/billing/prices') as Record<string, number>; if (p && typeof p === 'object') prices.value = p } catch {}
  form.model = availableModels.value[0] || 'qwen-image'
  try {
    const url = sessionStorage.getItem('generator_source_url') || ''
    const type = sessionStorage.getItem('generator_source_type') || 'image'
    const presetPrompt = sessionStorage.getItem('generator_prompt') || ''
    const presetSize = sessionStorage.getItem('generator_size') || ''
    const presetStyle = sessionStorage.getItem('generator_style') || ''
    const presetSeedRaw = sessionStorage.getItem('generator_seed') || ''
    const presetOrientation = sessionStorage.getItem('generator_orientation') || ''
    if (url && (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/'))) {
      sourceImageText.value = url
      if (type === 'image') {
        form.mode = 'image_to_image'
      }
      if (presetPrompt) {
        form.prompt = presetPrompt
      }
      if (presetStyle) {
        form.style = presetStyle
      }
      if (presetSize && /\d+x\d+/i.test(presetSize)) {
        form.size = presetSize
      }
      const seedNum = Number(presetSeedRaw)
      if (Number.isFinite(seedNum)) {
        form.seed = seedNum
      }
      if (presetOrientation === 'landscape' || presetOrientation === 'portrait') {
        form.orientation = presetOrientation as 'landscape' | 'portrait'
      }
      try {
        const img = new Image()
        img.onload = () => {
          const w = img.naturalWidth
          const h = img.naturalHeight
          if (w && h) {
            if (!presetSize) {
              if (Math.abs(w - h) < 2) {
                form.size = '1024x1024'
              } else if (w > h) {
                form.size = '1280x720'
              } else {
                form.size = '720x1280'
              }
            }
          }
        }
        img.src = url
      } catch {}
    }
    sessionStorage.removeItem('generator_source_url')
    sessionStorage.removeItem('generator_source_type')
    sessionStorage.removeItem('generator_prompt')
    sessionStorage.removeItem('generator_size')
    sessionStorage.removeItem('generator_style')
    sessionStorage.removeItem('generator_seed')
    sessionStorage.removeItem('generator_orientation')
  } catch {}
})

watch(() => form.mode, () => {
  form.model = availableModels.value[0] || (isImageMode.value ? 'qwen-image' : 'sora2-video')
})
</script>

<style scoped>
.generator {
  width: 100%;
  max-width: var(--container-width, 1200px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 32px;
  min-height: 60vh;
}

.generator-form,
.generator-results {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
}

.generator-form h2,
.results-header h3 {
  margin: 0 0 24px 0;
  color: var(--text);
}

.balance-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.balance-bar .insufficient { color: #ff6b6b; font-weight: 600; }

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.workspace {
  margin-bottom: 24px;
}

.workspace-canvas {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel-soft);
  aspect-ratio: 16/9;
  max-width: 720px;
  margin: 0 auto;
}

.workspace-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: var(--muted);
}

.workspace-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
}

.workspace-canvas img,
.workspace-canvas video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text);
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-soft);
  color: var(--text);
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.input-hint {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--muted);
}

.minimal-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  stroke: var(--muted);
  fill: none;
  stroke-width: 2px;
  opacity: 0.8;
}

.loader {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: #fff;
  animation: spin 1s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-flow: dense;
}

.result-card {
  background: var(--panel-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.result-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.result-image {
  position: relative;
  overflow: hidden;
}
.aspect-square { aspect-ratio: 1; }
.aspect-landscape { aspect-ratio: 16/9; }
.aspect-portrait { aspect-ratio: 9/16; }

.result-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.result-image video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.result-image:hover .result-overlay {
  opacity: 1;
}

.action-btn {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 999px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.action-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
}

.action-btn.delete:hover {
  background: #ef4444;
  border-color: #ef4444;
}

.result-info {
  padding: 16px;
}

.result-prompt {
  margin: 0 0 12px 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.4;
}

.result-meta {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: var(--muted);
}
.meta-left { display: inline-flex; gap: 6px; min-width: 0; align-items: center; }
.result-model { display: inline-block; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.result-date { white-space: nowrap; }
.media-tag { margin-left: 8px; background: var(--pill); border: 1px solid var(--border); color: var(--text); padding: 2px 8px; border-radius: 999px; font-size: 11px; }

.upload-area { border: 2px dashed var(--border); border-radius: 8px; padding: 24px; text-align: center; transition: all 0.2s ease; background: var(--panel-soft); }
.upload-area.dragging { border-color: var(--accent); background: rgba(255,255,255,0.04); }
.upload-placeholder svg { display: block; margin: 0 auto 12px; opacity: 0.7; }
.upload-placeholder p { margin: 0 0 8px 0; color: var(--muted); }
.preview-thumb { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }
.preview-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; }
.preview-item { position: relative; aspect-ratio: 16/9; }
.remove-btn { position: absolute; top: 6px; right: 6px; border: none; background: rgba(0,0,0,0.6); color: #fff; border-radius: 50%; width: 24px; height: 24px; line-height: 24px; text-align: center; cursor: pointer; }
.upload-actions { display: flex; justify-content: center; gap: 8px; margin-top: 12px; }

.file-input { position: absolute; opacity: 0; width: 1px; height: 1px; pointer-events: none; }
.upload-btn { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.file-selected { margin-top: 8px; font-size: 12px; color: var(--muted); }
.upload-auth { margin-top: 12px; text-align: left; }

.segmented { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.segmented-item { display: flex; align-items: center; justify-content: center; width: 100%; gap: 8px; background: var(--pill); border: 1px solid var(--border); color: var(--text); }
.segmented-item.active { background: var(--accent); border-color: var(--accent); color: var(--text); }
.segmented-icon { width: 18px; height: 18px; }

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
  padding: 24px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.full-size-image {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 8px;
  margin-bottom: 16px;
}

@media (max-width: 1024px) {
  .generator {
    grid-template-columns: 1fr;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
  .results-grid { grid-template-columns: repeat(2, 1fr); }
  .workspace-canvas { max-width: 600px; }
}

@media (max-width: 768px) {
  .results-grid { grid-template-columns: 1fr; }
  .workspace-canvas { max-width: 100%; }
}

.results-header .count { margin-left: 8px; font-size: 12px; color: var(--muted); }
</style>