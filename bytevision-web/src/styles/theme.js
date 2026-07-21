import { createTheme, alpha } from '@mui/material/styles'
import { COLORS } from '../constants/theme'

export function createAppTheme(mode = 'light') {
  const isDark = mode === 'dark'

  return createTheme({
    palette: {
      mode,
      primary: { main: COLORS.primary, light: COLORS.secondary },
      secondary: { main: COLORS.secondary },
      success: { main: COLORS.success },
      warning: { main: COLORS.warning },
      error: { main: COLORS.danger },
      background: {
        default: isDark ? COLORS.darkBg : COLORS.background,
        paper: isDark ? COLORS.darkCard : COLORS.card,
      },
      text: {
        primary: isDark ? '#F8FAFC' : COLORS.text,
        secondary: isDark ? '#94A3B8' : COLORS.textMuted,
      },
      divider: isDark ? alpha('#FFF', 0.08) : COLORS.border,
    },
    typography: {
      fontFamily: '"Inter", system-ui, -apple-system, sans-serif',
      h1: { fontWeight: 800, letterSpacing: '-0.02em' },
      h2: { fontWeight: 700, letterSpacing: '-0.02em' },
      h3: { fontWeight: 700, letterSpacing: '-0.01em' },
      h4: { fontWeight: 700 },
      h5: { fontWeight: 600 },
      h6: { fontWeight: 600 },
      button: { fontWeight: 600, textTransform: 'none' },
      body1: { fontWeight: 400 },
      body2: { fontWeight: 400 },
      subtitle1: { fontWeight: 500 },
      subtitle2: { fontWeight: 500 },
    },
    shape: { borderRadius: 12 },
    shadows: [
      'none',
      '0 1px 2px rgba(15, 23, 42, 0.04)',
      '0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)',
      '0 4px 6px -1px rgba(15, 23, 42, 0.06), 0 2px 4px -1px rgba(15, 23, 42, 0.04)',
      '0 10px 15px -3px rgba(15, 23, 42, 0.06), 0 4px 6px -2px rgba(15, 23, 42, 0.04)',
      '0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 10px 10px -5px rgba(15, 23, 42, 0.03)',
      ...Array(19).fill('0 20px 25px -5px rgba(15, 23, 42, 0.08)'),
    ],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarWidth: 'thin',
            scrollbarColor: isDark ? '#334155 transparent' : '#CBD5E1 transparent',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            padding: '8px 16px',
            boxShadow: 'none',
            '&:hover': { boxShadow: 'none' },
          },
          contained: {
            background: `linear-gradient(135deg, ${COLORS.primary} 0%, ${COLORS.secondary} 100%)`,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            border: `1px solid ${isDark ? alpha('#FFF', 0.06) : COLORS.border}`,
            boxShadow: isDark
              ? '0 4px 24px rgba(0,0,0,0.25)'
              : '0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.03)',
            backgroundImage: isDark
              ? 'linear-gradient(145deg, rgba(255,255,255,0.03) 0%, transparent 100%)'
              : 'none',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: 'none' },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: `1px solid ${isDark ? alpha('#FFF', 0.06) : COLORS.border}`,
            backgroundImage: isDark
              ? 'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)'
              : 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { fontWeight: 600, borderRadius: 8 },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: { borderRadius: 999, height: 8 },
        },
      },
    },
  })
}
