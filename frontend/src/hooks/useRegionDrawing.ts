import { useCallback, useEffect, useState } from 'react'
import type { Point } from '../types/regions'

type Mode = 'idle' | 'draw-line' | 'draw-roi'

export function useRegionDrawing(
  onCommitLine: (p1: Point, p2: Point) => Promise<void> | void,
  onCommitRoi: (pts: Point[]) => Promise<void> | void
) {
  const [mode, setMode] = useState<Mode>('idle')
  const [tempLine, setTempLine] = useState<{ p1?: Point; p2?: Point }>({})
  const [tempRoi, setTempRoi] = useState<Point[]>([])

  const cancel = useCallback(() => {
    setMode('idle')
    setTempLine({})
    setTempRoi([])
  }, [])

  const clickAddPoint = useCallback((pt: Point) => {
    if (mode === 'draw-line') {
      if (!tempLine.p1) setTempLine({ p1: pt })
      else if (!tempLine.p2) setTempLine({ p1: tempLine.p1, p2: pt })
      else setTempLine({ p1: pt })
    } else if (mode === 'draw-roi') {
      setTempRoi((prev) => [...prev, pt])
    }
  }, [mode, tempLine])

  const commitLine = useCallback(async () => {
    if (tempLine.p1 && tempLine.p2) {
      await onCommitLine(tempLine.p1, tempLine.p2)
      setTempLine({})
      setMode('idle')
    }
  }, [onCommitLine, tempLine])

  const commitRoi = useCallback(async () => {
    if (tempRoi.length >= 3) {
      await onCommitRoi(tempRoi)
      setTempRoi([])
      setMode('idle')
    }
  }, [onCommitRoi, tempRoi])

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (mode === 'draw-roi') {
        if (e.key === 'Escape') cancel()
        if (e.key === 'Enter') { e.preventDefault(); commitRoi() }
        if (e.key === 'Backspace') setTempRoi((prev) => prev.slice(0, -1))
      } else if (mode === 'draw-line') {
        if (e.key === 'Escape') cancel()
        if (e.key === 'Enter') commitLine()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mode, cancel, commitLine, commitRoi])

  return { mode, setMode, tempLine, tempRoi, clickAddPoint, commitLine, commitRoi, cancel }
}


