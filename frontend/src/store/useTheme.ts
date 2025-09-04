import { create } from 'zustand'

export type ThemeMode = 'system' | 'light' | 'dark'

interface ThemeState {
  mode: ThemeMode
  isDark: boolean
  setMode: (m: ThemeMode) => void
  computeIsDark: (m?: ThemeMode) => boolean
}

function systemPrefersDark() {
  if (typeof window === 'undefined') return true
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useTheme = create<ThemeState>((set, get) => ({
  mode: (localStorage.getItem('theme-mode') as ThemeMode) || 'system',
  isDark: true,
  setMode: (m) => {
    localStorage.setItem('theme-mode', m)
    const isDark = get().computeIsDark(m)
    set({ mode: m, isDark })
  },
  computeIsDark: (m) => {
    const mode = m ?? get().mode
    return mode === 'dark' || (mode === 'system' && systemPrefersDark())
  },
}))

