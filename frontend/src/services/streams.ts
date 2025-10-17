/**
 * DEPRECATED: Use camera.service.ts instead
 * 
 * This file is kept for backward compatibility only.
 * All new code should import from camera.service.ts
 */

// Re-export from new camera service
export {
  getStreamUrl as buildStreamUrl,
  listCameras,
  getCamera,
  upsertCamera,
  updateCameraRegions,
  deleteCamera,
  getCameraDensity
} from './camera.service'

// Re-export types
export type {
  Camera as CameraDto,
  CameraRegion as CameraRegionDto,
  Point,
  VehicleDensity as VehicleDensityInfo
} from '../types/api'

import { config } from '../config'

/** @deprecated Use config.apiBase from ../config instead */
export function getApiBase(): string {
  return config.apiBase
}


