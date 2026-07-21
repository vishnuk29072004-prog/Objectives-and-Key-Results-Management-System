import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material'
import { createAppTheme } from '../styles/theme'

const ThemeContext = createContext(null)

const STORAGE_KEY = 'bytevision-theme'
const SETTINGS_KEY = 'bytevision-settings'

const defaultSettings = {
  language: 'en',
  notificationsEnabled: true,
  emailDigests: true,
  compactMode: false,
  profileName: '',
  profileEmail: '',
  profileRole: 'OKR Manager',
}

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState(() => localStorage.getItem(STORAGE_KEY) || 'light')
  const [settings, setSettings] = useState(() => {
    try {
      return { ...defaultSettings, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}') }
    } catch {
      return defaultSettings
    }
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  useEffect(() => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  }, [settings])

  const toggleTheme = useCallback(() => {
    setMode((m) => (m === 'light' ? 'dark' : 'light'))
  }, [])

  const updateSettings = useCallback((patch) => {
    setSettings((prev) => ({ ...prev, ...patch }))
  }, [])

  const theme = useMemo(() => createAppTheme(mode), [mode])

  const value = useMemo(
    () => ({ mode, toggleTheme, setMode, settings, updateSettings }),
    [mode, toggleTheme, settings, updateSettings]
  )

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  )
}

export function useThemeMode() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProvider')
  return ctx
}
