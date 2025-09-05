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

