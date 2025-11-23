<template>
  <div class="admin-providers">
    <section class="panel">
      <div class="header">
        <h2>Providers</h2>
        <button class="pill accent sm" @click="showCreate = true">Create</button>
      </div>
      <div class="list" v-if="providers.length">
        <div class="row" v-for="p in providers" :key="p.name">
          <div class="col">
            <div class="name">{{ p.display_name }} ({{ p.name }})</div>
            <div class="meta">{{ p.models?.join(', ') || '—' }} · {{ p.capabilities?.join(', ') || '—' }}</div>
            <div class="meta">{{ p.base_url || '—' }}</div>
          </div>
          <div class="actions">
            <button class="pill sm" @click="openEdit(p)">Edit</button>
            <button class="pill sm" @click="toggleEnabled(p)">{{ p.enabled ? 'Disable' : 'Enable' }}</button>
            <button class="pill sm" @click="test(p)">Test</button>
            <button class="pill sm" @click="openSecret(p)">Secret</button>
            <button class="pill sm" @click="remove(p)">Delete</button>
          </div>
        </div>
      </div>
      <div v-else class="muted">No providers</div>
    </section>

    <div class="modal" v-if="showCreate">
      <div class="modal-body">
        <h3>Create Provider</h3>
        <div class="form-grid">
          <div class="section-title">Preset</div>
          <select v-model="preset">
            <option value="">Preset</option>
            <option value="qwen">Qwen (ModelScope)</option>
            <option value="flux">FLUX (ModelScope)</option>
            <option value="majicflus">MajicFLuS (ModelScope)</option>
            <option value="sora2">Sora2 (Video)</option>
          </select>
          
          <div class="section-title">Basics</div>
          <div class="row-2">
            <input v-model="newName" placeholder="name" />
            <input v-model="newDisplay" placeholder="display_name" />
          </div>
          <input v-model="newBase" placeholder="base_url" />
          <div class="hint">Leave empty to use default of the preset</div>
          <input v-model="newNotes" placeholder="notes" />

          <div class="section-title">Capabilities</div>
          <label class="switch">
            <input type="checkbox" v-model="newEnabled" />
            <span>Enabled</span>
          </label>
          <div class="caps">
            <label class="switch"><input type="checkbox" v-model="capImage" /><span>Image</span></label>
            <label class="switch"><input type="checkbox" v-model="capEditImage" /><span>Image Edit</span></label>
            <label class="switch"><input type="checkbox" v-model="capVideo" /><span>Video</span></label>
          </div>
          <div class="section-title">Image API</div>
          <div class="caps">
            <label class="switch"><input type="checkbox" v-model="capChatCompletions" /><span>chat/completions</span></label>
            <label class="switch"><input type="checkbox" v-model="capImagesGenerations" /><span>images/generations</span></label>
          </div>
          <input v-model="newCaps" placeholder="additional capabilities (comma, optional)" />
          <div class="hint">Use the API flags to control whether image requests use chat completions or images/generations.</div>
          
          <div class="section-title">Models</div>
          <input v-model="newModels" placeholder="models (comma)" />
          <div class="models-presets">
            <label class="chip"><input type="checkbox" value="qwen-image" v-model="modelPresets" /><span>qwen-image</span></label>
            <label class="chip"><input type="checkbox" value="qwen-image-edit" v-model="modelPresets" /><span>qwen-image-edit</span></label>
            <label class="chip"><input type="checkbox" value="MusePublic/489_ckpt_FLUX_1" v-model="modelPresets" /><span>MusePublic/489_ckpt_FLUX_1</span></label>
            <label class="chip"><input type="checkbox" value="MAILAND/majicflus_v1" v-model="modelPresets" /><span>MAILAND/majicflus_v1</span></label>
            <label class="chip"><input type="checkbox" value="sora2-video" v-model="modelPresets" /><span>sora2-video</span></label>
          </div>
          
          <div class="section-title">Credentials</div>
          <input v-model="newToken" placeholder="api_token (optional)" />
        </div>
        <div class="actions-row">
          <button class="pill sm" @click="showCreate=false">Cancel</button>
          <button class="pill accent sm" @click="create">Create</button>
        </div>
      </div>
    </div>

    <div class="modal" v-if="secretTarget">
      <div class="modal-body">
        <h3>Update Secret · {{ secretTarget.name }}</h3>
        <div class="form-grid">
          <input v-model="secretToken" placeholder="api_token" />
        </div>
        <div class="actions-row">
          <button class="pill sm" @click="secretTarget=null;secretToken=''">Cancel</button>
          <button class="pill accent sm" @click="saveSecret">Save</button>
        </div>
      </div>
    </div>

  <div class="modal" v-if="editTarget">
    <div class="modal-body">
      <h3>Edit Provider · {{ editTarget.name }}</h3>
      <div class="form-grid">
        <input v-model="editBase" placeholder="base_url" />
        <input v-model="editNotes" placeholder="notes" />
        <input v-model="editModels" placeholder="models (comma)" />
        <div class="section-title">Capabilities</div>
        <div class="caps">
          <label class="switch"><input type="checkbox" v-model="editCapImage" /><span>Image</span></label>
          <label class="switch"><input type="checkbox" v-model="editCapEditImage" /><span>Image Edit</span></label>
          <label class="switch"><input type="checkbox" v-model="editCapVideo" /><span>Video</span></label>
        </div>
        <div class="section-title">Image API</div>
        <div class="caps">
          <label class="switch"><input type="checkbox" v-model="editCapChatCompletions" /><span>chat/completions</span></label>
          <label class="switch"><input type="checkbox" v-model="editCapImagesGenerations" /><span>images/generations</span></label>
        </div>
        <input v-model="editCaps" placeholder="additional capabilities (comma, optional)" />
      </div>
      <div class="actions-row">
        <button class="pill sm" @click="closeEdit">Cancel</button>
        <button class="pill accent sm" @click="saveEdit">Save</button>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { get, patch, post } from '@/api/client'
import { createProvider, deleteProvider } from '@/api/admin'

interface Provider { name: string; display_name?: string; models?: string[]; capabilities?: string[]; base_url?: string; notes?: string; enabled?: boolean }
const providers = ref<Provider[]>([])
const showCreate = ref(false)
const preset = ref('')
const newName = ref('')
const newDisplay = ref('')
const newModels = ref('')
const newCaps = ref('')
const newBase = ref('')
const newNotes = ref('')
const newEnabled = ref(true)
const capImage = ref(true)
const capEditImage = ref(false)
const capVideo = ref(false)
const capChatCompletions = ref(true)
const capImagesGenerations = ref(false)
const modelPresets = ref<string[]>([])
const newToken = ref('')
const secretTarget = ref<{ name: string } | null>(null)
const secretToken = ref('')

interface Provider { name: string; display_name?: string; models?: string[]; capabilities?: string[]; base_url?: string; notes?: string; enabled?: boolean }
const editTarget = ref<Provider | null>(null)
const editBase = ref('')
const editNotes = ref('')
const editModels = ref('')
const editCaps = ref('')
const editCapImage = ref(false)
const editCapEditImage = ref(false)
const editCapVideo = ref(false)
const editCapChatCompletions = ref(false)
const editCapImagesGenerations = ref(false)

const capabilityFlags = ['image', 'edit_image', 'video', 'chat-completions', 'images-generations']

const parseExtraCaps = (caps: string[] = []) => caps.filter(c => !capabilityFlags.includes(c)).join(', ')

const buildCapabilities = (options: { image?: boolean; edit_image?: boolean; video?: boolean; chat?: boolean; generations?: boolean; extra?: string }) => {
  const caps = new Set<string>()
  if (options.image) caps.add('image')
  if (options.edit_image) caps.add('edit_image')
  if (options.video) caps.add('video')
  if (options.chat) caps.add('chat-completions')
  if (options.generations) caps.add('images-generations')
  if (options.extra) {
    options.extra.split(',').map(s => s.trim()).filter(Boolean).forEach(c => caps.add(c))
  }
  return Array.from(caps)
}

const load = async () => {
  try { providers.value = await get('/providers') } catch { providers.value = [] }
}

const toggleEnabled = async (p: Provider) => {
  try { await patch(`/providers/${p.name}`, { enabled: !p.enabled }); await load() } catch {}
}

const test = async (p: Provider) => {
  try { await post(`/providers/${p.name}/test`) } catch {}
}

const openSecret = (p: Provider) => { secretTarget.value = p }
const saveSecret = async () => {
  if (!secretTarget.value) return
  try { await patch(`/providers/${secretTarget.value.name}/secret`, { api_token: secretToken.value }); secretTarget.value=null; secretToken.value=''; await load() } catch {}
}

const remove = async (p: Provider) => {
  try { await deleteProvider(p.name); await load() } catch {}
}

const create = async () => {
  try {
    const caps = buildCapabilities({
      image: capImage.value,
      edit_image: capEditImage.value,
      video: capVideo.value,
      chat: capChatCompletions.value,
      generations: capImagesGenerations.value,
      extra: newCaps.value,
    })
    const modelsInput = newModels.value.split(',').map(s=>s.trim()).filter(Boolean)
    const models = Array.from(new Set([...modelsInput, ...modelPresets.value]))
    await createProvider({ name: newName.value, display_name: newDisplay.value, models, capabilities: caps, base_url: newBase.value || undefined, notes: newNotes.value || undefined, enabled: newEnabled.value })
    if (newToken.value) {
      try { await patch(`/providers/${newName.value}/secret`, { api_token: newToken.value }) } catch {}
    }
    showCreate.value = false
    preset.value=''; newName.value=''; newDisplay.value=''; newModels.value=''; newCaps.value=''; newBase.value=''; newNotes.value=''; newEnabled.value=true; capImage.value=true; capEditImage.value=false; capVideo.value=false; capChatCompletions.value=true; capImagesGenerations.value=false; modelPresets.value=[]; newToken.value=''
    await load()
  } catch {}
}

const openEdit = (p: Provider) => {
  editTarget.value = p
  editBase.value = p.base_url || ''
  editNotes.value = p.notes || ''
  editModels.value = Array.isArray(p.models) ? p.models.join(', ') : ''
  const caps = Array.isArray(p.capabilities) ? p.capabilities : []
  editCapImage.value = caps.includes('image')
  editCapEditImage.value = caps.includes('edit_image')
  editCapVideo.value = caps.includes('video')
  editCapChatCompletions.value = caps.includes('chat-completions')
  editCapImagesGenerations.value = caps.includes('images-generations')
  editCaps.value = parseExtraCaps(caps)
}

const closeEdit = () => {
  editTarget.value = null
}

const saveEdit = async () => {
  if (!editTarget.value) return
  try {
    const caps = buildCapabilities({
      image: editCapImage.value,
      edit_image: editCapEditImage.value,
      video: editCapVideo.value,
      chat: editCapChatCompletions.value,
      generations: editCapImagesGenerations.value,
      extra: editCaps.value,
    })
    await patch(`/providers/${editTarget.value.name}`, { base_url: editBase.value || null, notes: editNotes.value || null, models: editModels.value.split(',').map(s=>s.trim()).filter(Boolean), capabilities: caps })
    editTarget.value = null
    await load()
  } catch {}
}

onMounted(load)
watch(preset, (v) => {
  if (v === 'qwen') {
    newName.value = 'qwen'
    newDisplay.value = 'Qwen'
    newBase.value = 'https://api-inference.modelscope.cn/'
    capImage.value = true; capEditImage.value = true; capVideo.value = false; capChatCompletions.value = true; capImagesGenerations.value = false
    modelPresets.value = ['qwen-image','qwen-image-edit']
    newCaps.value = ''
  } else if (v === 'flux') {
    newName.value = 'flux'
    newDisplay.value = 'FLUX'
    newBase.value = 'https://api-inference.modelscope.cn/'
    capImage.value = true; capEditImage.value = false; capVideo.value = false; capChatCompletions.value = true; capImagesGenerations.value = false
    modelPresets.value = ['MusePublic/489_ckpt_FLUX_1']
    newCaps.value = ''
  } else if (v === 'majicflus') {
    newName.value = 'majicflus'
    newDisplay.value = 'MajicFLuS'
    newBase.value = 'https://api-inference.modelscope.cn/'
    capImage.value = true; capEditImage.value = false; capVideo.value = false; capChatCompletions.value = true; capImagesGenerations.value = false
    modelPresets.value = ['MAILAND/majicflus_v1']
    newCaps.value = ''
  } else if (v === 'sora2') {
    newName.value = 'sora2'
    newDisplay.value = 'Sora2'
    newBase.value = 'https://sora2api.airgzn.top/'
    capImage.value = false; capEditImage.value = false; capVideo.value = true; capChatCompletions.value = false; capImagesGenerations.value = false
    modelPresets.value = ['sora2-video']
    newCaps.value = ''
  }
})
</script>

<style scoped>
.admin-providers { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 12px; }
.header .pill { margin-left: auto; }
.list { display: grid; gap: 10px; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; border: 1px solid var(--border); border-radius: 12px; padding: 12px; background: #111116; }
.name { font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.actions > * { flex: 0 0 auto; }
.muted { color: var(--muted); }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-body { width: 480px; max-width: 90vw; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow); }
.form-grid { display: grid; gap: 8px; }
input { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); }
.form-grid select { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); }
.caps { display: flex; gap: 12px; align-items: center; }
.models-presets { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.models-presets .chip { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); cursor: pointer; user-select: none; }
.models-presets .chip input { display: none; }
.models-presets .chip span { font-size: 13px; }
.models-presets .chip:has(input:checked) { border-color: var(--accent); background: rgba(245, 158, 11, 0.12); }
.section-title { margin-top: 8px; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.hint { font-size: 12px; color: var(--muted); margin-top: -4px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.actions-row { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); }
</style>