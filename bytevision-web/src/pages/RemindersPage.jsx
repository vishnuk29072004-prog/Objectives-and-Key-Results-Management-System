import { useEffect, useMemo, useState } from 'react'
import { useSnackbar } from 'notistack'
import {
  Box,
  Button,
  CardContent,
  Chip,
  Grid,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import {
  getSchedulerStatus,
  startScheduler,
  stopScheduler,
  testReminders,
  triggerReminders,
} from '../services/api'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState } from '../components/common/PageStates'
import { DeadlineChip, MotionCard } from '../components/common/UiKit'
import { groupReminders, formatDate, formatRelative } from '../utils/helpers'
import StatCard from '../components/common/StatCard'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

export default function RemindersPage() {
  const { reminders, urgentItems, refreshAll, loading, error } = useAppData()
  const { enqueueSnackbar } = useSnackbar()
  const [tab, setTab] = useState(0)
  const [scheduler, setScheduler] = useState(null)
  const [busy, setBusy] = useState(false)

  const groups = useMemo(() => groupReminders(reminders), [reminders])

  useEffect(() => {
    refreshAll()
    getSchedulerStatus()
      .then((res) => setScheduler(res.data?.status || null))
      .catch(() => {})
  }, [refreshAll])

  const tabItems = [
    { key: 'overdue', label: 'Overdue', list: groups.overdue },
    { key: 'due_today', label: 'Due Today', list: groups.due_today },
    { key: 'upcoming', label: 'Upcoming', list: groups.upcoming },
    { key: 'all', label: 'All', list: reminders },
  ]

  const current = tabItems[tab]?.list || []

  const run = async (fn, okMsg) => {
    setBusy(true)
    try {
      const res = await fn()
      enqueueSnackbar(okMsg || res.data?.message || 'Done', { variant: 'success' })
      const status = await getSchedulerStatus()
      setScheduler(status.data?.status || null)
      await refreshAll()
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box>
      <PageHeader
        title="Reminders"
        subtitle="Timeline from GET /reminders/check/ + scheduler APIs"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Button
              variant="contained"
              startIcon={<NotificationsActiveIcon />}
              disabled={busy}
              onClick={() => run(triggerReminders, 'Reminders triggered')}
            >
              Trigger
            </Button>
            <Button disabled={busy} onClick={() => run(testReminders, 'Reminder test complete')}>
              Test
            </Button>
            <Button
              startIcon={<PlayArrowIcon />}
              disabled={busy || scheduler?.is_running}
              onClick={() => run(startScheduler)}
            >
              Start Scheduler
            </Button>
            <Button
              color="warning"
              startIcon={<StopIcon />}
              disabled={busy || !scheduler?.is_running}
              onClick={() => run(stopScheduler)}
            >
              Stop
            </Button>
          </Stack>
        }
      />

      {error && <ErrorState message={error} onRetry={refreshAll} />}

      <Grid container spacing={2.5} mb={3}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard title="Total" value={reminders.length} loading={loading} color={COLORS.primary} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard title="Overdue" value={groups.overdue.length} loading={loading} color={COLORS.danger} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard title="Due Today" value={groups.due_today.length} loading={loading} color={COLORS.warning} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Scheduler"
            value={scheduler?.is_running ? 'Running' : 'Stopped'}
            subtitle={scheduler?.next_run ? `Next ${formatRelative(scheduler.next_run)}` : '€”'}
            color={COLORS.success}
          />
        </Grid>
      </Grid>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }} variant="scrollable">
        {tabItems.map((t) => (
          <Tab key={t.key} label={`${t.label} (${t.list.length})`} />
        ))}
      </Tabs>

      {!current.length && !loading && (
        <EmptyState title="No reminders in this view" description="Reminder API returned no matching items." />
      )}

      <Stack spacing={1.5}>
        {current.map((r, i) => (
          <MotionCard key={`${r.type}-${r.name}-${i}`}>
            <CardContent>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
                <Chip size="small" label={r.type} />
                <Box sx={{ flex: 1 }}>
                  <Typography fontWeight={700}>{r.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {r.objective}
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  color={String(r.status).includes('overdue') ? 'error' : 'warning'}
                  label={r.status}
                />
                <DeadlineChip deadline={r.deadline} />
                <Typography variant="caption">{formatDate(r.deadline)}</Typography>
              </Stack>
            </CardContent>
          </MotionCard>
        ))}
      </Stack>

      {(urgentItems?.overdue_subtasks?.length > 0 || urgentItems?.due_soon_subtasks?.length > 0) && (
        <Box mt={4}>
          <Typography variant="h6" fontWeight={700} mb={1}>
            Urgent Subtasks (dashboard API)
          </Typography>
          <Stack spacing={1}>
            {[...(urgentItems.overdue_subtasks || []), ...(urgentItems.due_soon_subtasks || [])]
              .slice(0, 10)
              .map((s) => (
                <MotionCard key={`urg-${s.id}`}>
                  <CardContent>
                    <Typography fontWeight={600}>{s.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Deadline {formatDate(s.deadline)}
                    </Typography>
                  </CardContent>
                </MotionCard>
              ))}
          </Stack>
        </Box>
      )}
    </Box>
  )
}
