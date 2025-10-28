/**
 * Camera Service - API for camera management
 */

import { apiClient } from './api-client'
import { config } from '../config'
import type { Camera, CameraRegion, VehicleDensity } from '../types/api'

/**
 * Lấy stream URL cho camera
 */
export function getStreamUrl(rtsp: string): string {
  return `${config.apiBase}/v1/stream?src=${encodeURIComponent(rtsp)}`
}

/**
 * Lấy danh sách tất cả cameras
 */
export async function listCameras(): Promise<Camera[]> {
  return apiClient.get<Camera[]>('/v1/cameras')
}

/**
 * Lấy chi tiết một camera theo ID
 */
export async function getCamera(id: string): Promise<Camera> {
  return apiClient.get<Camera>(`/v1/cameras/${encodeURIComponent(id)}`)
}

/**
 * Tạo hoặc cập nhật camera
 */
export async function upsertCamera(camera: Camera): Promise<void> {
  await apiClient.post('/v1/cameras', camera)
}

/**
 * Cập nhật ROI/stopline cho camera
 */
export async function updateCameraRegions(
  id: string,
  regions: CameraRegion
): Promise<void> {
  await apiClient.put(`/v1/cameras/${encodeURIComponent(id)}/regions`, regions)
}

/**
 * Xóa camera theo ID
 */
export async function deleteCamera(id: string): Promise<void> {
  try {
    await apiClient.delete(`/v1/cameras/${encodeURIComponent(id)}`)
  } catch (error: any) {
    // 404 = already deleted, treat as success
    if (error.status !== 404) throw error
  }
}

/**
 * Lấy mật độ phương tiện cho stream
 */
export async function getCameraDensity(rtsp: string): Promise<VehicleDensity> {
  return apiClient.get<VehicleDensity>(
    `/v1/stream/density?src=${encodeURIComponent(rtsp)}`
  )
}
