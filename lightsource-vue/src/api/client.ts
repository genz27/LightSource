import { useAuthStore } from '@/stores/auth'
import router from '@/router'

function computeRoot(): string {
  const envBase = import.meta.env.VITE_API_BASE_URL
  if (envBase && envBase.trim()) return envBase.replace(/\/$/, '')
  return location.origin
}
let BASE: string | null = null
const API_PREFIX = '/api'
async function resolveBase(): Promise<string> {
  if (BASE) return BASE
  const base = computeRoot()
  try {
    const r = await fetch(`${base}${API_PREFIX}/health`, { method: 'GET' })
    if (r.ok) {
      try { const j = await r.json(); if (j && j.status === 'ok') { BASE = base; return BASE } } catch {}
    }
  } catch {}
  try {
    const u = new URL(base)
    const f = `${u.protocol}//${u.hostname}:8000`
    const r2 = await fetch(`${f}${API_PREFIX}/health`, { method: 'GET' })
    if (r2.ok) {
      try { const j2 = await r2.json(); if (j2 && j2.status === 'ok') { BASE = f; return BASE } } catch {}
    }
  } catch {}
  BASE = base
  return BASE
}
async function apiUrl(path: string): Promise<string> {
  const b = await resolveBase()
  return `${b}${API_PREFIX}${path}`
}

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
    const url = await apiUrl(path)
    const resp = await fetch(url, { ...init, headers })
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
    const url = await apiUrl(path)
    const resp = await fetch(url, { ...init, headers })
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