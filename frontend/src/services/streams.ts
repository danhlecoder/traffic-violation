/** Utilities to work with backend stream & snapshot APIs */

export function getApiBase(): string {
  const base = (import.meta as any)?.env?.VITE_API_BASE
  if (base) return String(base)
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

export function buildStreamUrl(rtsp: string): string {
  return `${getApiBase()}/api/stream?src=${encodeURIComponent(rtsp)}`
}

// Snapshot API đã loại bỏ; dùng ảnh đang hiển thị hoặc POST /api/detect/stopline

export type Point = { x: number; y: number }
export type CameraRegionDto = { stopLine?: [Point, Point] | null; roi?: Point[] | null }
export type CameraDto = { id: string; name: string; rtsp: string; location: string; regions?: CameraRegionDto }

export async function detectStopLine(rtsp: string): Promise<[Point, Point] | null> {
  // Deprecated: use POST /api/detect/stopline with displayed image or
  // GET /api/snapshot?detect=1 when needed directly.
  throw new Error('detectStopLine is deprecated')
}

// API quản lý camera và vùng vẽ

export async function listCameras(): Promise<CameraDto[]> {
  const resp = await fetch(`${getApiBase()}/api/cameras`)
  if (!resp.ok) throw new Error('load cameras failed')
  return await resp.json()
}

export async function getCamera(id: string): Promise<CameraDto> {
  const resp = await fetch(`${getApiBase()}/api/cameras/${encodeURIComponent(id)}`)
  if (!resp.ok) throw new Error('get camera failed')
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
  // Nếu server trả 404 (đã không tồn tại) thì vẫn coi như xóa thành công
  if (!resp.ok && resp.status !== 404) throw new Error('delete camera failed')
}


