/**
 * useCameras Hook - Manage cameras data
 */

import { useEffect, useState } from 'react'
import { listCameras } from '../services/camera.service'
import type { Camera } from '../types/api'

export function useCameras(autoLoad = true) {
  const [cameras, setCameras] = useState<Camera[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listCameras()
      setCameras(data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (autoLoad) {
      load()
    }
  }, [autoLoad])

  return { cameras, loading, error, reload: load }
}
