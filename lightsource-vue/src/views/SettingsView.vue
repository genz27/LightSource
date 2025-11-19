<template>
  <AppLayout>
    <div class="settings">
      <section class="panel">
        <h2>Profile</h2>
        <div class="row">
          <div class="field">
            <label>Email</label>
            <div class="value">{{ user?.email || '—' }}</div>
          </div>
          <div class="field">
            <label>Username</label>
            <div class="value">{{ user?.username || '—' }}</div>
          </div>
          <div class="field">
            <label>Role</label>
            <div class="value">{{ user?.role || 'User' }}</div>
          </div>
        </div>
        <div class="actions-row">
          <button class="pill" @click="openUpdateProfile">Update profile</button>
          <button class="pill" @click="openChangePassword">Change password</button>
          <button class="pill accent" @click="handleLogout">Logout</button>
        </div>
      </section>

      <section class="panel">
        <h2>Tokens</h2>
        <div class="row">
          <div class="field">
            <label>Access token</label>
            <div class="value monospace">{{ maskedToken }}</div>
          </div>
        </div>
        <div class="actions-row">
          <button class="pill" :disabled="!token" @click="copyToken">Copy Token</button>
          <button class="pill" :disabled="!token" @click="rotateToken">Rotate Token</button>
        </div>
      </section>

  

      <section class="panel">
        <h2>Balance</h2>
        <div class="row">
          <div class="field">
            <label>Balance</label>
            <div class="value">{{ formattedBalance }}</div>
          </div>
          <div class="field">
            <label>Last Updated</label>
            <div class="value">{{ lastUpdated || '—' }}</div>
          </div>
        </div>
        
      </section>
    </div>
  </AppLayout>
  <div v-if="showUpdate" class="modal">
    <div class="modal-body">
      <h3>Update Profile</h3>
      <div class="field">
        <label>Email</label>
        <input v-model="profileForm.email" type="email" />
      </div>
      <div class="field">
        <label>Username</label>
        <input v-model="profileForm.username" type="text" />
      </div>
      <div class="actions-row">
        <button class="pill" @click="showUpdate=false">Cancel</button>
        <button class="pill accent" :disabled="submittingUpdate" @click="submitUpdateProfile">Save</button>
      </div>
    </div>
  </div>

  <div v-if="showPwd" class="modal">
    <div class="modal-body">
      <h3>Change Password</h3>
      <div class="field">
        <label>Current password</label>
        <input v-model="pwdForm.current" type="password" />
      </div>
      <div class="field">
        <label>New password</label>
        <input v-model="pwdForm.next" type="password" />
      </div>
      <div class="field">
        <label>Confirm new password</label>
        <input v-model="pwdForm.confirm" type="password" />
      </div>
      <div class="actions-row">
        <button class="pill" @click="showPwd=false">Cancel</button>
        <button class="pill accent" :disabled="submittingPwd" @click="submitChangePassword">Submit</button>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { computed, reactive, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/client'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const token = computed(() => authStore.token)

const maskedToken = computed(() => {
  const t = token.value || ''
  if (!t) return '—'
  const start = t.slice(0, 4)
  const end = t.slice(-4)
  return `${start}${'•'.repeat(Math.max(0, t.length - 8))}${end}`
})

const copyToken = async () => {
  if (!token.value) return
  try {
    await navigator.clipboard.writeText(token.value)
    alert('Access token copied to clipboard!')
  } catch {
    alert('Failed to copy token. Please copy manually.')
  }
}

const rotateToken = async () => {
  if (!token.value) return
  const ok = await authStore.rotateTokens()
  alert(ok ? 'Token rotated' : 'Token rotated locally (demo)')
}

const handleLogout = () => {
  authStore.logout()
}

onMounted(async () => {
  if (authStore.isAuthenticated && !user.value) {
    try { await authStore.fetchMe() } catch {}
  }
})

const balance = ref<number>(0)
const lastUpdated = ref<string>('')

const formattedBalance = computed(() => {
  return balance.value.toFixed(2)
})

const loadBalance = async () => {
  try {
    const data = await get('/billing/wallet')
    balance.value = parseFloat(data.balance ?? balance.value)
    lastUpdated.value = new Date(data.updated_at).toLocaleString()
    return
  } catch {}
  const b = localStorage.getItem('ls_balance')
  const u = localStorage.getItem('ls_balance_updated')
  balance.value = b ? parseFloat(b) : 1000
  lastUpdated.value = u || new Date().toLocaleString()
}

//

// refreshBalance removed per requirements

// TopUp removed per requirements

onMounted(() => {
  loadBalance()
})

const showUpdate = ref(false)
const profileForm = reactive({
  email: '',
  username: ''
})
const openUpdateProfile = () => {
  profileForm.email = user.value?.email || ''
  profileForm.username = user.value?.username || ''
  showUpdate.value = true
}
const submittingUpdate = ref(false)
const submitUpdateProfile = async () => {
  if (submittingUpdate.value) return
  submittingUpdate.value = true
  const ok = await authStore.updateProfile({ email: profileForm.email, username: profileForm.username })
  submittingUpdate.value = false
  if (ok) {
    showUpdate.value = false
    alert('Profile updated')
  } else {
    alert('Failed to update profile')
  }
}

const showPwd = ref(false)
const pwdForm = reactive({
  current: '',
  next: '',
  confirm: ''
})
const openChangePassword = () => {
  pwdForm.current = ''
  pwdForm.next = ''
  pwdForm.confirm = ''
  showPwd.value = true
}
const submittingPwd = ref(false)
const submitChangePassword = async () => {
  if (submittingPwd.value) return
  if (!pwdForm.current || !pwdForm.next || pwdForm.next !== pwdForm.confirm) {
    alert('Invalid password inputs')
    return
  }
  submittingPwd.value = true
  const ok = await authStore.changePassword(pwdForm.current, pwdForm.next)
  submittingPwd.value = false
  if (ok) {
    showPwd.value = false
    alert('Password changed')
  } else {
    alert('Failed to change password')
  }
}
</script>

<style scoped>
.settings {
  display: grid;
  gap: 24px;
  grid-template-columns: 1fr 1fr;
  min-height: 80vh;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
}

.panel h2 {
  margin: 0 0 16px 0;
  color: var(--text);
}

.row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 6px;
}

.field label {
  color: var(--muted);
  font-size: 13px;
}

.value {
  background: #111116;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
  color: var(--text);
}

.monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.value.monospace {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.actions-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--panel-soft);
  color: var(--text);
}

@media (max-width: 767px) {
  .settings {
    gap: 16px;
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .settings {
    grid-template-columns: 1fr;
  }
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-body {
  width: 480px;
  max-width: 90vw;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow);
}
</style>