import { useCallback, useEffect, useState } from 'react'
import type { Point } from '../types/regions'

type Mode = 'idle' | 'draw-line'

export function useRegionDrawing(
  onCommitLine: (p1: Point, p2: Point) => Promise<void> | void,
) {
  const [mode, setMode] = useState<Mode>('idle')
  const [tempLine, setTempLine] = useState<{ p1?: Point; p2?: Point }>({})

  const cancel = useCallback(() => {
    setMode('idle')
    setTempLine({})
  }, [])

  const clickAddPoint = useCallback((pt: Point) => {
    if (mode === 'draw-line') {
      if (!tempLine.p1) setTempLine({ p1: pt })
      else if (!tempLine.p2) setTempLine({ p1: tempLine.p1, p2: pt })
      else setTempLine({ p1: pt })
    }
  }, [mode, tempLine])

  const commitLine = useCallback(async () => {
    if (tempLine.p1 && tempLine.p2) {
      await onCommitLine(tempLine.p1, tempLine.p2)
      setTempLine({})
      setMode('idle')
    }
  }, [onCommitLine, tempLine])

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (mode === 'draw-line') {
        if (e.key === 'Escape') cancel()
        if (e.key === 'Enter') commitLine()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mode, cancel, commitLine])

  return { mode, setMode, tempLine, clickAddPoint, commitLine, cancel }
}


