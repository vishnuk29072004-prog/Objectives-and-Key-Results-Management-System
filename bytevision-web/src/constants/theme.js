export const COLORS = {
  primary: '#2563EB',
  secondary: '#3B82F6',
  success: '#22C55E',
  warning: '#F59E0B',
  danger: '#EF4444',
  background: '#F8FAFC',
  card: '#FFFFFF',
  darkBg: '#0F172A',
  darkCard: '#1E293B',
  text: '#0F172A',
  textMuted: '#64748B',
  border: '#E2E8F0',
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: 'Dashboard' },
  { label: 'Objectives', path: '/objectives', icon: 'Flag' },
  { label: 'Tasks', path: '/tasks', icon: 'TaskAlt' },
  { label: 'Subtasks', path: '/subtasks', icon: 'AccountTree' },
  { label: 'Reminders', path: '/reminders', icon: 'NotificationsActive' },
  { label: 'Analytics', path: '/analytics', icon: 'Analytics' },
  { label: 'AI Insights', path: '/ai-insights', icon: 'AutoAwesome' },
  { label: 'Settings', path: '/settings', icon: 'Settings' },
  { label: 'Profile', path: '/profile', icon: 'Person' },
]

export const STATUS_COLORS = {
  approved: 'success',
  completed: 'success',
  pending: 'warning',
  rejected: 'error',
  overdue: 'error',
  due_today: 'warning',
  upcoming: 'info',
}
