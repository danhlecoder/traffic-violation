/**
 * Application Configuration
 */

export const config = {
  /** API base URL - từ env hoặc auto-detect */
  apiBase: (() => {
    const envBase = (import.meta as any).env?.VITE_API_BASE
    if (envBase) return String(envBase)
    return `${window.location.protocol}//${window.location.hostname}:8000`
  })(),

  /** Polling intervals (ms) */
  polling: {
    violations: 5000,
    density: 2000,
    cameras: 10000,
  },

  /** Pagination */
  pagination: {
    defaultPageSize: 10,
    pageSizeOptions: [5, 10, 20, 50],
  },

  /** Stream settings */
  stream: {
    defaultFps: 30,
    defaultQuality: 80,
  },
} as const
