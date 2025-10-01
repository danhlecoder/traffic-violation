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

// API quản lý camera và vùng vẽ
export type Point = { x: number; y: number }
export type CameraRegionDto = { stopLine?: [Point, Point]; roi?: Point[] }
export type CameraDto = { id: string; name: string; rtsp: string; location: string; regions?: CameraRegionDto }

export async function listCameras(): Promise<CameraDto[]> {
  const resp = await fetch(`${getApiBase()}/api/cameras`)
  if (!resp.ok) throw new Error('load cameras failed')
  return await resp.json()
}

export async function upsertCamera(cam: CameraDto): Promise<void> {
  const resp = await fetch(`${getApiBase()}/api/cameras`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cam) })
  if (!resp.ok) throw new Error('upsert camera failed')
}

export async function updateCameraRegions(id: string, regions: CameraRegionDto): Promise<void> {
  const resp = await fetch(`${getApiBase()}/api/cameras/${encodeURIComponent(id)}/regions`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(regions) })
  if (!resp.ok) throw new Error('update regions failed')
}

export async function deleteCamera(id: string): Promise<void> {
  const resp = await fetch(`${getApiBase()}/api/cameras/${encodeURIComponent(id)}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('delete camera failed')
}


