<template>
  <div class="admin-users">
    <section class="panel">
      <div class="header">
        <h2>Users</h2>
        <div class="controls">
          <input v-model="q" placeholder="Search email/username" />
          <select v-model="role">
            <option value="">All roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <button class="pill sm" @click="load">Search</button>
          <button class="pill accent sm" @click="showCreate = true">Create</button>
        </div>
      </div>
      <div class="list" v-if="users.length">
        <div class="row" v-for="u in users" :key="u.id">
          <div class="col">
            <div class="name">{{ u.username }}</div>
            <div class="meta">{{ u.email }} · {{ u.role }}</div>
          </div>
          <div class="actions">
            <button class="pill sm" @click="openEdit(u)">Edit</button>
            <button class="pill sm" @click="setRole(u.id, u.role === 'admin' ? 'user' : 'admin')">{{ u.role === 'admin' ? 'Make user' : 'Make admin' }}</button>
            <button class="pill sm" @click="openWallet(u)">Wallet</button>
            <button class="pill sm" @click="remove(u.id)">Delete</button>
          </div>
        </div>
      </div>
      <div v-else class="muted">No users</div>
    </section>

    <section v-if="walletUser" class="panel">
      <div class="wallet-header">
        <h2>Wallet · {{ walletUser.username }}</h2>
        <button class="pill sm" @click="closeWallet">Close</button>
      </div>
      <div class="wallet-grid" v-if="wallet">
        <div class="stat"><strong>Balance</strong><p>{{ wallet.balance }} {{ wallet.currency }}</p></div>
        <div class="stat"><strong>Frozen</strong><p>{{ wallet.frozen }}</p></div>
        <div class="stat"><strong>Updated</strong><p>{{ wallet.updated_at }}</p></div>
      </div>
      
      <div class="txs" v-if="txs.length">
        <div class="tx" v-for="t in txs" :key="t.id">
          <div class="tx-main">
            <div>{{ t.type }}</div>
            <div class="meta">{{ t.amount }} · {{ t.created_at }}</div>
          </div>
        </div>
      </div>
      <div v-else class="muted">No transactions</div>
    </section>

    <div class="modal" v-if="showCreate">
      <div class="modal-body">
        <h3>Create User</h3>
        <div class="form-grid">
          <input v-model="newEmail" placeholder="Email" />
          <input v-model="newUsername" placeholder="Username" />
          <input v-model="newPassword" type="password" placeholder="Password" />
          <select v-model="newRole">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="actions-row">
          <button class="pill sm" @click="showCreate=false">Cancel</button>
          <button class="pill accent sm" @click="create">Create</button>
        </div>
      </div>
    </div>

    <div class="modal" v-if="editTarget">
      <div class="modal-body">
        <h3>Edit User</h3>
        <p class="muted">ID: {{ editDetails?.id || editTarget?.id }}</p>
        <p class="muted">Created: {{ editDetails?.created_at || '—' }}</p>
        <div class="form-grid">
          <input v-model="editEmail" placeholder="Email" />
          <input v-model="editUsername" placeholder="Username" />
          <select v-model="editRole">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="actions-row">
          <button class="pill sm" @click="closeEdit">Cancel</button>
          <button class="pill accent sm" @click="saveEdit">Save</button>
        </div>
        <h4>Reset Password</h4>
        <div class="form-grid">
          <input v-model="resetPwd1" type="password" placeholder="New password" />
          <input v-model="resetPwd2" type="password" placeholder="Confirm password" />
        </div>
        <div class="actions-row">
          <button class="pill sm" :disabled="!resetPwd1 || resetPwd1 !== resetPwd2" @click="resetPassword">Reset</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listUsers, createUser, patchUserRole, patchUser, deleteUser, getWallet, listWalletTxs, getUser, resetUserPassword } from '@/api/admin'

interface UserItem { id: string; email: string; username: string; role: string }
interface Wallet { balance: number; currency: string; frozen?: number; updated_at?: string }
interface Tx { id: string; type: string; amount: number; created_at: string }

const users = ref<UserItem[]>([])
const q = ref('')
const role = ref('')

const showCreate = ref(false)
const newEmail = ref('')
const newUsername = ref('')
const newPassword = ref('')
const newRole = ref('user')

const walletUser = ref<UserItem | null>(null)
const wallet = ref<Wallet | null>(null)
const txs = ref<Tx[]>([])

const editTarget = ref<{ id: string, role: string, email: string, username: string } | null>(null)
const editDetails = ref<{ id: string, email: string, username: string, role: string, created_at?: string } | null>(null)
const editRole = ref('user')
const editEmail = ref('')
const editUsername = ref('')
const resetPwd1 = ref('')
const resetPwd2 = ref('')

const load = async () => {
  try { const data = await listUsers({ q: q.value || undefined, role: role.value || undefined, limit: 50 }); users.value = (data ?? []) as UserItem[] } catch {}
}

const create = async () => {
  try {
    await createUser({ email: newEmail.value, username: newUsername.value, password: newPassword.value, role: newRole.value })
    showCreate.value = false
    newEmail.value = ''
    newUsername.value = ''
    newPassword.value = ''
    newRole.value = 'user'
    await load()
  } catch {}
}

const setRole = async (id: string, r: string) => {
  try { await patchUserRole(id, { role: r }); await load() } catch {}
}

const remove = async (id: string) => {
  try { await deleteUser(id); await load() } catch {}
}

const openWallet = async (u: UserItem) => {
  walletUser.value = u
  try { const w = await getWallet(u.id); wallet.value = (w ?? null) as Wallet | null } catch { wallet.value = null }
  try { const t = await listWalletTxs(u.id); txs.value = (t ?? []) as Tx[] } catch { txs.value = [] }
}

const closeWallet = () => {
  walletUser.value = null
  wallet.value = null
  txs.value = []
}



const openEdit = async (u: { id: string, role: string, email: string, username: string }) => {
  editTarget.value = u
  editRole.value = u.role
  editEmail.value = u.email
  editUsername.value = u.username
  try {
    const full = await getUser(u.id)
    editDetails.value = (full ?? null) as { id: string, email: string, username: string, role: string, created_at?: string } | null
  } catch {
    editDetails.value = null
  }
}

const closeEdit = () => {
  editTarget.value = null
  editDetails.value = null
  resetPwd1.value = ''
  resetPwd2.value = ''
}

const saveEdit = async () => {
  if (!editTarget.value) return
  try {
    await patchUser(editTarget.value.id, { email: editEmail.value, username: editUsername.value })
    await patchUserRole(editTarget.value.id, { role: editRole.value })
    editTarget.value = null
    await load()
  } catch {}
}

const resetPassword = async () => {
  if (!editTarget.value) return
  if (!resetPwd1.value || resetPwd1.value !== resetPwd2.value) return
  try {
    await resetUserPassword(editTarget.value.id, { new_password: resetPwd1.value })
    resetPwd1.value = ''
    resetPwd2.value = ''
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.admin-users { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 12px; }
.controls { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.controls > * { flex: 0 0 auto; }
.controls input, .controls select { padding: 8px 10px; font-size: 13px; border-radius: 8px; min-width: 140px; }
input, select { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-soft); color: var(--text); }
.list { display: grid; gap: 10px; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; border: 1px solid var(--border); border-radius: 12px; padding: 12px; background: #111116; }
.name { font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.muted { color: var(--muted); }
.wallet-header { display: flex; justify-content: space-between; align-items: center; }
.wallet-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
.stat { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: #111116; }
.actions-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.txs { display: grid; gap: 8px; margin-top: 12px; }
.tx { border: 1px solid var(--border); border-radius: 10px; padding: 10px; background: #111116; }
.tx .meta { color: var(--muted); font-size: 13px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-body { width: 480px; max-width: 90vw; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow); }
.form-grid { display: grid; gap: 8px; }
</style>