/**
 * Camera Service - API for camera management
 */

import { apiClient } from './api-client'
import { config } from '../config'
import type { Camera, CameraRegion, VehicleDensity } from '../types/api'

/**
 * Get stream URL for a camera
 */
export function getStreamUrl(rtsp: string): string {
  return `${config.apiBase}/api/stream?src=${encodeURIComponent(rtsp)}`
}

/**
 * List all cameras
 */
export async function listCameras(): Promise<Camera[]> {
  return apiClient.get<Camera[]>('/api/cameras')
}

/**
 * Get single camera by ID
 */
export async function getCamera(id: string): Promise<Camera> {
  return apiClient.get<Camera>(`/api/cameras/${encodeURIComponent(id)}`)
}

/**
 * Create or update camera
 */
export async function upsertCamera(camera: Camera): Promise<void> {
  await apiClient.post('/api/cameras', camera)
}

/**
 * Update camera regions (stopLine, ROI)
 */
export async function updateCameraRegions(
  id: string,
  regions: CameraRegion
): Promise<void> {
  await apiClient.put(`/api/cameras/${encodeURIComponent(id)}/regions`, regions)
}

/**
 * Delete camera
 */
export async function deleteCamera(id: string): Promise<void> {
  try {
    await apiClient.delete(`/api/cameras/${encodeURIComponent(id)}`)
  } catch (error: any) {
    // 404 = already deleted, treat as success
    if (error.status !== 404) throw error
  }
}

/**
 * Get vehicle density for a camera
 */
export async function getCameraDensity(rtsp: string): Promise<VehicleDensity> {
  return apiClient.get<VehicleDensity>(
    `/api/density/camera?src=${encodeURIComponent(rtsp)}`
  )
}
