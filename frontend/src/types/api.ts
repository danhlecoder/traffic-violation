/**
 * API Types - Data transfer objects
 */

export type Point = { x: number; y: number }

export type CameraRegion = {
  stopLine?: [Point, Point] | null
  roi?: Point[] | null
}

export type Camera = {
  id: string
  name: string
  rtsp: string
  location: string
  regions?: CameraRegion
}

export type VehicleDensity = {
  count: number
  level: 'empty' | 'low' | 'medium' | 'high'
  description: string
}

export type ViolationType =
  | 'Vượt đèn đỏ'
  | 'Quá tốc độ'
  | 'Không đội mũ bảo hiểm'

export type ViolationStatus = 'Mới' | 'Đã xử lý' | 'Đã bỏ qua'

export type Violation = {
  id: string
  type: ViolationType
  cameraId: string
  cameraName: string
  location: string
  time: string
  speed?: number
  plate?: string
  vehicleType?: string
  confidence: number
  images: {
    overview: string
    vehicle: string
    plate: string
  }
  status: ViolationStatus
}
