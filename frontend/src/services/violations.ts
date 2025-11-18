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
    track_id?: string  // Track ID string (format: 5 ký tự alphanumeric + hhmmss)
    speed?: number  // Tốc độ tính bằng km/h
    bbox: number[]
    confidence: number
    violation_tags: string[]  // Chỉ dùng violation_tags
    violation_history?: Array<{
      type?: string
      timestamp?: string
      speed?: number
    }>
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

  const response = await apiClient.get<ViolationAPIResponse>(`/v1/violations?${query.toString()}`)
  return response
}

export async function updateViolation(trackId: string, updateData: {
  violation_tags?: string[]  // Chỉ dùng violation_tags
  vehicle_type?: string
  license_plate?: string
}) {
  const response = await apiClient.put(`/v1/violations/${trackId}`, updateData)
  return response
}

export async function confirmViolation(trackId: string, updateData?: {
  violation_tags?: string[]  // Chỉ dùng violation_tags
  vehicle_type?: string
  license_plate?: string
}) {
  // Nếu có updateData, update trước khi confirm
  if (updateData) {
    await updateViolation(trackId, updateData)
  }
  // Update status thành confirmed
  // Backend sẽ tự động gửi Discord notification
  await apiClient.put(`/v1/violations/${trackId}`, { status: 'confirmed' })
}

export async function skipViolation(trackId: string) {
  // Update status thành skipped
  await apiClient.put(`/v1/violations/${trackId}`, { status: 'skipped' })
}
