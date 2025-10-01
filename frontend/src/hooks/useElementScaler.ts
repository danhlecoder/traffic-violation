import { useCallback, useRef } from 'react'

export function useElementScaler<T extends HTMLElement = HTMLDivElement>() {
  const ref = useRef<T | null>(null)

  const toPixel = useCallback((pt: { x: number; y: number }) => {
    const el = ref.current
    if (!el) return { x: 0, y: 0 }
    const rect = el.getBoundingClientRect()
    return { x: pt.x * rect.width, y: pt.y * rect.height }
  }, [])

  const toRelative = useCallback((clientX: number, clientY: number) => {
    const el = ref.current
    if (!el) return { x: 0, y: 0 }
    const rect = el.getBoundingClientRect()
    const x = (clientX - rect.left) / rect.width
    const y = (clientY - rect.top) / rect.height
    return { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) }
  }, [])

  return { ref, toPixel, toRelative }
}




