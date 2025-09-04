import toast from 'react-hot-toast'
import { Violation } from '../store/useStore'

export function sendZalo(violation: Violation, token: string, targetId: string) {
  // Giả lập gọi API gửi Zalo
  return new Promise<void>((resolve) => {
    setTimeout(() => {
      toast.success(`Đã gửi vi phạm ${violation.id} tới Zalo`)
      resolve()
    }, 800)
  })
}

export function confirmViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 300))
}

export function skipViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 200))
}

