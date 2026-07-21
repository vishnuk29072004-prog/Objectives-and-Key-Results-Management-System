import { useMemo, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
  Badge,
  alpha,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import RefreshIcon from '@mui/icons-material/Refresh'
import DashboardIcon from '@mui/icons-material/Dashboard'
import FlagIcon from '@mui/icons-material/Flag'
import TaskAltIcon from '@mui/icons-material/TaskAlt'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import SettingsIcon from '@mui/icons-material/Settings'
import PersonIcon from '@mui/icons-material/Person'
import { motion, AnimatePresence } from 'framer-motion'
import { useThemeMode } from '../contexts/ThemeContext'
import { useAppData } from '../contexts/AppDataContext'
import { NAV_ITEMS } from '../constants/theme'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

const DRAWER_WIDTH = 260

const ICONS = {
  Dashboard: DashboardIcon,
  Flag: FlagIcon,
  TaskAlt: TaskAltIcon,
  AccountTree: AccountTreeIcon,
  NotificationsActive: NotificationsActiveIcon,
  Analytics: AnalyticsIcon,
  AutoAwesome: AutoAwesomeIcon,
  Settings: SettingsIcon,
  Person: PersonIcon,
}

export default function AppLayout() {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { mode, toggleTheme, settings } = useThemeMode()
  const { reminders, refreshAll, loading } = useAppData()

  const overdueCount = useMemo(
    () => reminders.filter((r) => String(r.status).toLowerCase().includes('overdue')).length,
    [reminders]
  )

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2.5,
              background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.secondary})`,
              display: 'grid',
              placeItems: 'center',
              color: '#fff',
              fontWeight: 800,
              fontSize: 18,
            }}
          >
            bV
          </Box>
          <Box>
            <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>
              byteVision
            </Typography>
            <Typography variant="caption" color="text.secondary">
              AI OKR Platform
            </Typography>
          </Box>
        </Stack>
      </Box>
      <Divider />
      <List sx={{ px: 1.5, py: 2, flex: 1 }}>
        {NAV_ITEMS.map((item) => {
          const Icon = ICONS[item.icon] || DashboardIcon
          const selected = location.pathname === item.path
          const showBadge = item.path === '/reminders' && overdueCount > 0
          return (
            <ListItemButton
              key={item.path}
              selected={selected}
              onClick={() => {
                navigate(item.path)
                if (isMobile) setMobileOpen(false)
              }}
              sx={{
                mb: 0.5,
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: alpha(COLORS.primary, mode === 'dark' ? 0.2 : 0.1),
                  color: COLORS.primary,
                  '& .MuiListItemIcon-root': { color: COLORS.primary },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                {showBadge ? (
                  <Badge badgeContent={overdueCount} color="error" max={99}>
                    <Icon fontSize="small" />
                  </Badge>
                ) : (
                  <Icon fontSize="small" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                slotProps={{
                  primary: {
                    sx: { fontWeight: selected ? 700 : 500, fontSize: 14 },
                  },
                }}
              />
            </ListItemButton>
          )
        })}
      </List>
      <Box sx={{ p: 2 }}>
        <Stack
          direction="row"
          spacing={1.5}
          alignItems="center"
          sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: 'action.hover',
            cursor: 'pointer',
          }}
          onClick={() => navigate('/profile')}
        >
          <Avatar sx={{ width: 36, height: 36, bgcolor: COLORS.primary, fontSize: 14 }}>
            {(settings.profileName || 'U').charAt(0).toUpperCase()}
          </Avatar>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="body2" fontWeight={700} noWrap>
              {settings.profileName || 'User'}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              {settings.profileRole}
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(12px)',
          borderBottom: `1px solid ${theme.palette.divider}`,
          color: 'text.primary',
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} aria-label="Open navigation" sx={{ mr: 1 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" fontWeight={700} sx={{ flexGrow: 1 }}>
            {NAV_ITEMS.find((n) => n.path === location.pathname)?.label || 'byteVision'}
          </Typography>
          <Tooltip title="Refresh data">
            <span>
              <IconButton onClick={refreshAll} disabled={loading} aria-label="Refresh">
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={mode === 'dark' ? 'Light mode' : 'Dark mode'}>
            <IconButton onClick={toggleTheme} aria-label="Toggle theme">
              {mode === 'dark' ? <LightModeOutlinedIcon /> : <DarkModeOutlinedIcon />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: DRAWER_WIDTH },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          open
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ type: 'spring', stiffness: 280, damping: 28 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </Box>
      </Box>
    </Box>
  )
}
