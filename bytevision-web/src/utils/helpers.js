import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import isToday from 'dayjs/plugin/isToday'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'

dayjs.extend(relativeTime)
dayjs.extend(isToday)
dayjs.extend(isSameOrBefore)

export { dayjs }

export function formatDate(value, format = 'MMM D, YYYY') {
  if (!value) return '—'
  const d = dayjs(value)
  return d.isValid() ? d.format(format) : String(value)
}

export function formatRelative(value) {
  if (!value) return '—'
  const d = dayjs(value)
  return d.isValid() ? d.fromNow() : String(value)
}

export function getDeadlineStatus(deadline) {
  if (!deadline) return 'upcoming'
  const d = dayjs(deadline)
  if (!d.isValid()) return 'upcoming'
  if (d.isBefore(dayjs(), 'day')) return 'overdue'
  if (d.isToday()) return 'due_today'
  return 'upcoming'
}

export function clampPercent(value) {
  const n = Number(value) || 0
  return Math.max(0, Math.min(100, Math.round(n * 100) / 100))
}

export function deriveProductivityScore(overview) {
  if (!overview) return 0
  const progress = Number(overview.overall_progress) || 0
  const overdue = Number(overview.overdue_count) || 0
  const total = Number(overview.total_objectives) || 1
  const penalty = Math.min(40, (overdue / Math.max(total * 5, 1)) * 40)
  return clampPercent(Math.max(0, progress - penalty + 20))
}

export function deriveAiHealthScore(overview, reminders) {
  if (!overview) return 0
  const progress = Number(overview.overall_progress) || 0
  const overdueShare = reminders?.filter((r) => r.status === 'overdue').length || 0
  const health = progress * 0.7 + Math.max(0, 30 - overdueShare)
  return clampPercent(health)
}

export function groupReminders(reminders = []) {
  const groups = { overdue: [], due_today: [], upcoming: [] }
  reminders.forEach((r) => {
    const status = (r.status || getDeadlineStatus(r.deadline)).toLowerCase().replace(/\s+/g, '_')
    if (status.includes('overdue')) groups.overdue.push(r)
    else if (status.includes('today') || status.includes('due_today')) groups.due_today.push(r)
    else groups.upcoming.push(r)
  })
  return groups
}
