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

export function listAssets(params: QueryParams = {}) {
  return get(`/assets${buildQuery(params)}`)
}

export function deleteAsset(asset_id: string) {
  return del(`/assets/${asset_id}`)
}

export function uploadAsset(file: File, isPublic = true, provider?: string) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('public', String(isPublic))
  if (provider) fd.append('provider', provider)
  return post('/assets/upload', fd)
}

export function patchAssetPublic(asset_id: string, isPublic: boolean) {
  return patch(`/assets/${asset_id}?public=${isPublic}`)
}