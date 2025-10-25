import { apiClient } from './api-client'

export interface ViolationAPIResponse {
  total: number
  limit: number
  offset: number
  data: Array<{
    id: string
    timestamp: string
    camera_id: string
    camera_name?: string
    location?: string
    vehicle_type: string
    license_plate?: string
    bbox: number[]
    confidence: number
    violation_type: string
    status: string
    images: {
      full_frame: string
      vehicle_crop?: string
      plate_crop?: string
    }
  }>
}

export async function getViolations(params?: {
  camera_id?: string
  vehicle_type?: string
  status?: string
  limit?: number
  offset?: number
}): Promise<ViolationAPIResponse> {
  const query = new URLSearchParams()
  if (params?.camera_id) query.append('camera_id', params.camera_id)
  if (params?.vehicle_type) query.append('vehicle_type', params.vehicle_type)
  if (params?.status) query.append('status', params.status)
  if (params?.limit) query.append('limit', params.limit.toString())
  if (params?.offset) query.append('offset', params.offset.toString())
  
  const response = await apiClient.get<ViolationAPIResponse>(`/api/violations?${query.toString()}`)
  return response
}

export function confirmViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 300))
}

export function skipViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 200))
}
