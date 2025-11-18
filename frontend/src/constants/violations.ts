// Centralized constants for violations domain
import type { Violation, ViolationStatus } from '../store/useStore'

export const VIOLATION_STATUSES: ViolationStatus[] = [
  'Mới',
  'Đã xác nhận',
  'Đã bỏ qua',
]

export type AntdStatusColor = 'default' | 'processing' | 'success' | 'error' | 'warning'

export const STATUS_TAG_COLOR: Record<ViolationStatus, AntdStatusColor> = {
  'Mới': 'warning',
  'Đã xác nhận': 'processing',
  'Đã bỏ qua': 'error',
}

export function violationTypeToTagColor(t: string): 'red' | 'cyan' | 'gold' {
  const x = t.toLowerCase()
  if (x.includes('đèn đỏ')) return 'red'
  if (x.includes('tốc độ')) return 'cyan'
  return 'gold'
}

export function getViolationTypes(v: Partial<Violation> & { types?: string[] }): string[] {
  if (Array.isArray(v?.types) && v.types.length) return v.types
  if (Array.isArray((v as any)?.violationTags) && (v as any).violationTags.length) return (v as any).violationTags as string[]
  if (v?.type) return [v.type]
  return []
}
