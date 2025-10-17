/**
 * useVehicleDensity Hook - Poll vehicle density for cameras
 */

import { useEffect, useState } from 'react'
import { getCameraDensity } from '../services/camera.service'
import { config } from '../config'

export function useVehicleDensity(rtsp: string | null, enabled = true) {
  const [density, setDensity] = useState<number>(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!rtsp || !enabled) return

    const fetchDensity = async () => {
      try {
        setLoading(true)
        const data = await getCameraDensity(rtsp)
        setDensity(data.count)
      } catch {
        // Silently fail
      } finally {
        setLoading(false)
      }
    }

    fetchDensity()
    const interval = setInterval(fetchDensity, config.polling.density)

    return () => clearInterval(interval)
  }, [rtsp, enabled])

  return { density, loading }
}
