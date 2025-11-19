<template>
  <div class="admin-billing">
    <section class="panel">
      <div class="header">
        <h2>Wallets</h2>
        <div class="controls">
          <input v-model="currency" placeholder="Currency" />
          <button class="pill sm" @click="load">Search</button>
          <button class="pill sm" @click="showAdvanced = !showAdvanced">Advanced</button>
        </div>
        <div class="controls advanced" v-if="showAdvanced">
          <input v-model.number="min" type="number" placeholder="Balance ≥" />
          <input v-model.number="max" type="number" placeholder="Balance ≤" />
          <input v-model="updated_after" type="datetime-local" />
          <button class="pill sm" @click="load">Apply</button>
        </div>
      </div>
      <div class="list" v-if="wallets.length">
        <div class="row" v-for="w in wallets" :key="w.owner_id" @click="open(w)" style="cursor:pointer;">
          <div class="col">
            <div class="name">{{ usernames[w.owner_id] || w.owner_id }}</div>
            <div class="meta">ID: {{ w.owner_id }} · {{ w.balance }} {{ w.currency }} · frozen {{ w.frozen }}</div>
          </div>
          <div class="actions">
            <button class="pill sm" @click.stop="open(w)">Open</button>
            <button class="pill sm" @click.stop="open(w)">Edit</button>
          </div>
        </div>
        <div class="pager">
          <button class="pill sm" @click="prevWallets" :disabled="walletPage<=1">Prev</button>
          <span class="muted">Page {{ walletPage }} · {{ walletLimit }}/page</span>
          <button class="pill sm" @click="nextWallets">Next</button>
        </div>
      </div>
      <div v-else class="muted">No wallets</div>
    </section>

    <section v-if="current" class="panel">
      <div class="wallet-header">
        <h2>Wallet · {{ current.owner_id }}</h2>
        <button class="pill sm" @click="current=null; txs=[]">Close</button>
      </div>
      <div class="wallet-grid">
        <div class="stat"><strong>Balance</strong><p>{{ current.balance }} {{ current.currency }}</p></div>
        <div class="stat"><strong>Frozen</strong><p>{{ current.frozen }}</p></div>
        <div class="stat"><strong>Updated</strong><p>{{ current.updated_at }}</p></div>
      </div>
      <div class="wallet-actions">
        <div class="form-card">
          <div class="form-title">Adjust Balance</div>
          <div class="form-row">
            <input v-model.number="delta" type="number" placeholder="Amount (positive)" />
            <input v-model="desc" placeholder="Note" />
          </div>
          <div class="form-actions">
            <button class="pill accent sm" @click="applyAdd">Add Balance</button>
            <button class="pill sm" @click="applySubtract">Subtract Balance</button>
          </div>
        </div>
        <div class="form-card">
          <div class="form-title">Set Balance</div>
          <div class="form-row">
            <input v-model.number="target" type="number" placeholder="Set balance to" />
          </div>
          <div class="form-actions">
            <button class="pill sm" @click="applySetTo">Set</button>
          </div>
        </div>
      </div>
      <div class="txs" v-if="txs.length">
        <div class="tx" v-for="t in txs" :key="t.id">
          <div class="tx-main">
            <div>{{ t.type }}</div>
            <div class="meta">{{ t.amount }} · {{ t.created_at }}</div>
          </div>
        </div>
        <div class="pager">
          <button class="pill sm" @click="prevTxs" :disabled="txPage<=1">Prev</button>
          <span class="muted">Page {{ txPage }} · {{ txLimit }}/page</span>
          <button class="pill sm" @click="nextTxs" :disabled="txs.length < txLimit">Next</button>
        </div>
      </div>
      <div v-else class="muted">No transactions</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listWallets, listWalletTxs, adjustWallet, getWallet, getUser } from '@/api/admin'

interface Wallet { owner_id: string; balance: number; currency: string; frozen?: number; updated_at?: string }
interface Tx { id: string; type: string; amount: number; created_at: string }

const wallets = ref<Wallet[]>([])
const usernames = ref<Record<string, string>>({})
const walletPage = ref(1)
const walletLimit = ref(20)
const currency = ref('')
const min = ref<number | undefined>(undefined)
const max = ref<number | undefined>(undefined)
const updated_after = ref('')
const showAdvanced = ref(false)

const current = ref<Wallet | null>(null)
const txs = ref<Tx[]>([])
const txPage = ref(1)
const txLimit = ref(10)
const delta = ref<number>(0)
const desc = ref('')
const target = ref<number | undefined>(undefined)

const load = async () => {
  try { const data = await listWallets({ currency: currency.value || undefined, balance_min: min.value, balance_max: max.value, updated_after: updated_after.value || undefined, page: walletPage.value, limit: walletLimit.value }); wallets.value = (data ?? []) as Wallet[] } catch { wallets.value = [] }
  try {
    const ids = Array.from(new Set(wallets.value.map(w => w.owner_id)))
    const missing = ids.filter(id => !(id in usernames.value))
    const results = await Promise.all(missing.map(id => getUser(id).catch(() => null)))
    for (let i = 0; i < missing.length; i++) {
      const id = missing[i]
      const u = results[i] as { username?: string } | null
      if (id && u && typeof u.username === 'string') usernames.value[id] = u.username
    }
  } catch {}
}

const prevWallets = async () => { if (walletPage.value > 1) { walletPage.value -= 1; await load() } }
const nextWallets = async () => { walletPage.value += 1; await load() }

const loadTxs = async (owner_id: string) => {
  try { const tdata = await listWalletTxs(owner_id, { page: txPage.value, limit: txLimit.value }); txs.value = (tdata ?? []) as Tx[] } catch { txs.value = [] }
}

const open = async (w: Wallet) => {
  const wdata = await getWallet(w.owner_id)
  current.value = (wdata ?? null) as Wallet | null
  txPage.value = 1
  txLimit.value = 10
  await loadTxs(w.owner_id)
}

const prevTxs = async () => { if (txPage.value > 1 && current.value) { txPage.value -= 1; await loadTxs(current.value.owner_id) } }
const nextTxs = async () => { if (current.value) { txPage.value += 1; await loadTxs(current.value.owner_id) } }

const applyAdd = async () => {
  if (!current.value) return
  const amt = Math.abs(Number(delta.value || 0))
  if (!isFinite(amt) || amt <= 0) return
  try { await adjustWallet(current.value.owner_id, { amount: amt, description: desc.value }); await open(current.value) } catch {}
}

const applySubtract = async () => {
  if (!current.value) return
  const amt = Math.abs(Number(delta.value || 0))
  if (!isFinite(amt) || amt <= 0) return
  try { await adjustWallet(current.value.owner_id, { amount: -amt, description: desc.value }); await open(current.value) } catch {}
}

const applySetTo = async () => {
  if (!current.value) return
  const t = Number(target.value ?? NaN)
  if (!isFinite(t)) return
  const curr = Number(current.value.balance || 0)
  const d = t - curr
  if (Math.abs(d) < 1e-9) return
  try { await adjustWallet(current.value.owner_id, { amount: d, description: desc.value || `set to ${t}` }); await open(current.value); } catch {}
}

onMounted(load)
</script>

<style scoped>
.admin-billing { display: grid; gap: 16px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 12px; }
.controls { display: flex; gap: 6px; flex-wrap: nowrap; overflow-x: auto; align-items: center; }
.controls > * { flex: 0 0 auto; }
input { padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--panel-soft); color: var(--text); font-size: 13px; }
.advanced { margin-top: 8px; }
.list { display: grid; gap: 10px; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; border: 1px solid var(--border); border-radius: 12px; padding: 12px; background: #111116; }
.name { font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.muted { color: var(--muted); }
.wallet-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.wallet-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
.stat { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: #111116; }
.wallet-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-top: 12px; }
.form-card { border: 1px solid var(--border); border-radius: 12px; padding: 12px; background: var(--panel-soft); display: grid; gap: 10px; }
.form-title { font-weight: 700; color: var(--text); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.form-row input { width: 100%; }
.form-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.txs { display: grid; gap: 8px; margin-top: 12px; }
.tx { border: 1px solid var(--border); border-radius: 10px; padding: 10px; background: #111116; }
.tx .meta { color: var(--muted); font-size: 13px; }
.pager { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }
</style>