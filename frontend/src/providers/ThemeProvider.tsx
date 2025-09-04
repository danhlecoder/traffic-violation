import { ReactNode, useEffect, useMemo } from 'react'
import { ConfigProvider, theme as antdTheme } from 'antd'
import viVN from 'antd/locale/vi_VN'
import { useTheme } from '../store/useTheme'

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const { mode, isDark, setMode, computeIsDark } = useTheme()

  // Sync with system when mode = system
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (mode === 'system') {
        const dark = computeIsDark('system')
        useTheme.setState({ isDark: dark })
      }
    }
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [mode, computeIsDark])

  // On mount: compute current
  useEffect(() => {
    useTheme.setState({ isDark: computeIsDark() })
    // Ensure mode stored
    if (!localStorage.getItem('theme-mode')) localStorage.setItem('theme-mode', mode)
  }, [])

  // Apply data-theme to <html>
  useEffect(() => {
    const el = document.documentElement
    el.setAttribute('data-theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const algorithm = isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm

  const tokens = useMemo(() => {
    // Thiết kế lại bảng màu: ưu tiên xanh navy (primary) và đỏ (nhấn), phù hợp logo
    // Áp dụng tông nền dịu mắt, tương phản cao, giữ borderRadius thống nhất
    return isDark
      ? {
          colorPrimary: '#273375', // navy 700
          colorInfo: '#3abff8',
          colorSuccess: '#22c55e',
          colorWarning: '#f59e0b',
          colorError: '#e11d48', // đỏ trầm
          colorBgBase: '#0b1020', // nền tổng thể
          colorBgContainer: '#11172a', // khối container/card
          colorBorder: '#263043',
          colorText: '#e6edf7',
          colorTextSecondary: '#9bb3cf',
          colorLink: '#7aa2ff',
          borderRadius: 12,
        }
      : {
          colorPrimary: '#2b3a8a', // navy 600
          colorInfo: '#0ea5e9',
          colorSuccess: '#16a34a',
          colorWarning: '#f59e0b',
          colorError: '#dc2626', // đỏ tươi
          colorBgBase: '#f5f7fb',
          colorBgContainer: '#ffffff',
          colorBorder: '#dbe3f0',
          colorText: '#0f172a',
          colorTextSecondary: '#4b5563',
          colorLink: '#335cff',
          borderRadius: 12,
        }
  }, [isDark])

  return (
    <ConfigProvider locale={viVN} theme={{ algorithm, token: tokens }}>
      {children}
    </ConfigProvider>
  )
}
