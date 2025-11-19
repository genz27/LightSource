import { useAuthStore } from '@/stores/auth'
import router from '@/router'

function computeRoot(): string {
  const envBase = import.meta.env.VITE_API_BASE_URL
  if (envBase && envBase.trim()) return envBase.replace(/\/$/, '')
  const { protocol, hostname, port } = location
  const apiPort = '8000'
  const root = (port && port !== '') ? `${protocol}//${hostname}:${port}` : `${protocol}//${hostname}`
  if (port === apiPort) return root
  return `${protocol}//${hostname}:${apiPort}`
}
const ROOT = computeRoot()
const API_PREFIX = '/api'
const apiUrl = (path: string) => `${ROOT}${API_PREFIX}${path}`

async function request(path: string, init: RequestInit = {}) {
  const auth = useAuthStore()
  const doFetch = async () => {
    const headers: Record<string, string> = {
      ...(init.headers as Record<string, string> || {}),
    }
    if (!headers['Content-Type'] && init.body && !(init.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    if (auth.token) {
      headers['Authorization'] = `Bearer ${auth.token}`
    }
    const resp = await fetch(apiUrl(path), { ...init, headers })
    const text = await resp.text()
    const data = text ? JSON.parse(text) : null
    return { resp, data }
  }
  let { resp, data } = await doFetch()
  if (resp.status === 401) {
    let refreshed = false
    try { refreshed = await auth.rotateTokens() } catch {}
    if (refreshed) {
      ({ resp, data } = await doFetch())
    }
    if (resp.status === 401) {
      try { auth.logout() } catch {}
      try { router.push('/auth') } catch { location.href = '/auth' }
    }
  }
  if (!resp.ok) {
    throw { status: resp.status, data }
  }
  return data
}

export async function get(path: string) {
  return request(path)
}

export async function post(path: string, body?: unknown, init: RequestInit = {}) {
  return request(path, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body), ...init })
}

export async function put(path: string, body?: unknown, init: RequestInit = {}) {
  return request(path, { method: 'PUT', body: body instanceof FormData ? body : JSON.stringify(body), ...init })
}

export async function del(path: string) {
  return request(path, { method: 'DELETE' })
}

export async function patch(path: string, body?: unknown, init: RequestInit = {}) {
  return request(path, { method: 'PATCH', body: body instanceof FormData ? body : JSON.stringify(body), ...init })
}

async function requestText(path: string, init: RequestInit = {}) {
  const auth = useAuthStore()
  const doFetch = async () => {
    const headers: Record<string, string> = {
      ...(init.headers as Record<string, string> || {}),
    }
    if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`
    const resp = await fetch(apiUrl(path), { ...init, headers })
    const text = await resp.text()
    return { resp, text }
  }
  let { resp, text } = await doFetch()
  if (resp.status === 401) {
    let refreshed = false
    try { refreshed = await auth.rotateTokens() } catch {}
    if (refreshed) {
      ({ resp, text } = await doFetch())
    }
    if (resp.status === 401) {
      try { auth.logout() } catch {}
      try { router.push('/auth') } catch { location.href = '/auth' }
    }
  }
  if (!resp.ok) {
    throw { status: resp.status, data: text }
  }
  return text
}

export async function getText(path: string) { return requestText(path) }