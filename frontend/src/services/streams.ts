/** Utilities to work with backend stream & snapshot APIs */

export function getApiBase(): string {
  const base = (import.meta as any)?.env?.VITE_API_BASE
  if (base) return String(base)
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

export function buildStreamUrl(rtsp: string): string {
  return `${getApiBase()}/api/stream?src=${encodeURIComponent(rtsp)}`
}

export function buildSnapshotUrl(rtsp: string): string {
  return `${getApiBase()}/api/snapshot?src=${encodeURIComponent(rtsp)}`
}

export async function fetchSnapshotBlob(rtsp: string): Promise<Blob> {
  const url = buildSnapshotUrl(rtsp)
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`snapshot failed: ${resp.status}`)
  return await resp.blob()
}


