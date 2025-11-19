import { get, post, del, patch } from '@/api/client'

type QueryParams = Record<string, string | number | boolean | null | undefined>

function buildQuery(params: QueryParams = {}) {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.append(k, String(v))
  })
  const q = sp.toString()
  return q ? `?${q}` : ''
}

// Users
export function listUsers(params: QueryParams = {}) {
  return get(`/admin/users${buildQuery(params)}`)
}
export function getUser(id: string) { return get(`/admin/users/${id}`) }
export function createUser(payload: { email: string, username: string, password: string, role: string }) {
  return post('/admin/users', payload)
}
export function patchUserRole(id: string, payload: { role: string }) {
  return patch(`/admin/users/${id}/role`, payload)
}
export function patchUser(id: string, payload: { email?: string, username?: string }) {
  return patch(`/admin/users/${id}`, payload)
}
export function deleteUser(id: string) { return del(`/admin/users/${id}`) }
export function resetUserPassword(id: string, payload: { new_password: string }) {
  return post(`/admin/users/${id}/reset-password`, payload)
}

// Wallets & Transactions
export function listWallets(params: QueryParams = {}) {
  return get(`/admin/wallets${buildQuery(params)}`)
}
export function getWallet(user_id: string) { return get(`/admin/wallets/${user_id}`) }
export function listWalletTxs(user_id: string, params: QueryParams = {}) { return get(`/admin/wallets/${user_id}/transactions${buildQuery(params)}`) }
export function adjustWallet(user_id: string, payload: { amount: number, description?: string }) {
  return post(`/admin/wallets/${user_id}/adjust`, payload)
}

// Jobs
export function listJobs(params: QueryParams = {}) {
  return get(`/admin/jobs${buildQuery(params)}`)
}
export function cancelJob(job_id: string) { return post(`/admin/jobs/${job_id}/cancel`) }
export function getJob(id: string) { return get(`/jobs/${id}`) }
export function getJobStatus(id: string, params: QueryParams = {}) { return get(`/jobs/${id}/status${buildQuery(params)}`) }

// Assets
export function listAssets(params: QueryParams = {}) {
  return get(`/admin/assets${buildQuery(params)}`)
}
export function patchAssetPublic(asset_id: string, isPublic: boolean) {
  return patch(`/admin/assets/${asset_id}?public=${isPublic}`)
}

// Providers (placeholders for future UI)
export function createProvider(payload: unknown) { return post('/admin/providers', payload) }
export function getProvider(name: string) { return get(`/admin/providers/${name}`) }
export function deleteProvider(name: string) { return del(`/admin/providers/${name}`) }

// Metrics & Audit & Exports
export function getMetrics() { return get('/admin/metrics') }
export function listAuditLogs(params: QueryParams = {}) {
  return get(`/admin/audit/logs${buildQuery(params)}`)
}
export function exportUsers() { return get('/admin/export/users') }
export function exportJobs() { return get('/admin/export/jobs') }
export function exportAssets() { return get('/admin/export/assets') }
export function exportWallets() { return get('/admin/export/wallets') }

// Runtime config
export function getAdminConfig() { return get('/admin/config') }
export function patchAdminConfig(payload: { debug?: boolean, prices?: Record<string, number> }) { return patch('/admin/config', payload) }