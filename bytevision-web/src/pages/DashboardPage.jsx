import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Typography,
} from '@mui/material'
import FlagIcon from '@mui/icons-material/Flag'
import TaskAltIcon from '@mui/icons-material/TaskAlt'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ScheduleIcon from '@mui/icons-material/Schedule'
import { useAppData } from '../contexts/AppDataContext'
import StatCard from '../components/common/StatCard'
import { PageHeader, ErrorState, EmptyState } from '../components/common/PageStates'
import { ProgressBar, DeadlineChip, MotionCard } from '../components/common/UiKit'
import { ChartCard, DonutChart, SimpleBarChart, SimpleLineChart } from '../components/charts/Charts'
import {
  clampPercent,
  deriveAiHealthScore,
  deriveProductivityScore,
  formatDate,
  formatRelative,
} from '../utils/helpers'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { overview, statistics, urgentItems, objectives, reminders, loading, error, refreshAll } =
    useAppData()

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  const productivity = deriveProductivityScore(overview)
  const aiHealth = deriveAiHealthScore(overview, reminders)

  const statusPie = useMemo(() => {
    if (!overview) return []
    return [
      { name: 'Active', value: overview.active_objectives || 0 },
      { name: 'Completed', value: overview.completed_objectives || 0 },
    ].filter((d) => d.value > 0)
  }, [overview])

  const categoryBars = useMemo(() => {
    if (!statistics?.by_category) return []
    return Object.entries(statistics.by_category).map(([name, v]) => ({
      name: name.trim() || 'Uncategorized',
      value: clampPercent(v.progress),
      count: v.count,
    }))
  }, [statistics])

  const ownerBars = useMemo(() => {
    if (!statistics?.by_owner) return []
    return Object.entries(statistics.by_owner).map(([name, v]) => ({
      name: name.trim() || 'Unassigned',
      value: clampPercent(v.progress),
    }))
  }, [statistics])

  const progressLine = useMemo(() => {
    return [...objectives]
      .sort((a, b) => a.id - b.id)
      .map((o) => ({
        name: `Obj ${o.id}`,
        progress: clampPercent(o.progress),
      }))
  }, [objectives])

  const overdueTasks = urgentItems?.overdue_tasks || []
  const dueSoon = urgentItems?.due_soon_tasks || []
  const recentReminders = reminders.slice(0, 6)

  if (error && !overview) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Enterprise OKR overview" />
        <ErrorState message={error} onRetry={refreshAll} />
      </>
    )
  }

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Live metrics from your FastAPI OKR backend"
        actions={
          <Button variant="contained" onClick={() => navigate('/objectives')}>
            Manage Objectives
          </Button>
        }
      />

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Overall Progress"
            value={`${clampPercent(overview?.overall_progress)}%`}
            icon={<TrendingUpIcon />}
            color={COLORS.primary}
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Objectives"
            value={overview?.total_objectives ?? '€”'}
            subtitle={`${overview?.active_objectives ?? 0} active · ${overview?.completed_objectives ?? 0} completed`}
            icon={<FlagIcon />}
            color={COLORS.secondary}
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Overdue Tasks"
            value={overview?.overdue_count ?? overdueTasks.length}
            subtitle={`${overview?.due_soon_count ?? dueSoon.length} due soon`}
            icon={<WarningAmberIcon />}
            color={COLORS.danger}
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Pending Reminders"
            value={reminders.length}
            icon={<ScheduleIcon />}
            color={COLORS.warning}
            loading={loading && !reminders.length}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Productivity Score"
            value={productivity}
            subtitle="Derived from progress & overdue load"
            icon={<TaskAltIcon />}
            color={COLORS.success}
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="AI Health Score"
            value={aiHealth}
            subtitle="Progress weighted with reminder risk"
            icon={<AutoAwesomeIcon />}
            color="#8B5CF6"
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Completed Objectives"
            value={overview?.completed_objectives ?? 0}
            color={COLORS.success}
            loading={loading && !overview}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Upcoming Deadlines"
            value={overview?.due_soon_count ?? dueSoon.length}
            color={COLORS.warning}
            loading={loading && !overview}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Objective Status" subtitle="Active vs completed">
            {statusPie.length ? (
              <DonutChart data={statusPie} />
            ) : (
              <EmptyState title="No status data" description="Create objectives to populate this chart." />
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Category Progress" subtitle="From /api/dashboard/statistics">
            {categoryBars.length ? (
              <SimpleBarChart data={categoryBars} />
            ) : (
              <EmptyState title="No category data" />
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Owner Performance" subtitle="Average progress by owner">
            {ownerBars.length ? (
              <SimpleBarChart data={ownerBars} color={COLORS.secondary} />
            ) : (
              <EmptyState title="No owner data" />
            )}
          </ChartCard>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <ChartCard title="Objective Progress Trend" subtitle="Progress per objective from live API">
            {progressLine.length ? (
              <SimpleLineChart
                data={progressLine}
                lines={[{ key: 'progress', color: COLORS.primary }]}
              />
            ) : (
              <EmptyState title="No objectives yet" />
            )}
          </ChartCard>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                Recent Reminders
              </Typography>
              {recentReminders.length === 0 ? (
                <EmptyState title="No reminders" description="Reminder API returned an empty list." />
              ) : (
                <List dense disablePadding>
                  {recentReminders.map((r, i) => (
                    <ListItem key={`${r.name}-${i}`} divider sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontWeight={600} noWrap>
                            {r.name}
                          </Typography>
                        }
                        secondary={
                          <Stack direction="row" spacing={1} alignItems="center" mt={0.5}>
                            <Chip size="small" label={r.status} color={String(r.status).includes('overdue') ? 'error' : 'warning'} />
                            <Typography variant="caption">{formatDate(r.deadline)}</Typography>
                          </Stack>
                        }
                        slotProps={{
                          secondary: { component: 'div' },
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
              <Button fullWidth sx={{ mt: 1 }} onClick={() => navigate('/reminders')}>
                View all reminders
              </Button>
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Objectives Snapshot
              </Typography>
              <Stack spacing={2}>
                {objectives.slice(0, 5).map((o) => (
                  <Box key={o.id}>
                    <Stack direction="row" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2" fontWeight={600} noWrap sx={{ maxWidth: '70%' }}>
                        {o.objective}
                      </Typography>
                      <DeadlineChip deadline={o.deadline} />
                    </Stack>
                    <ProgressBar value={o.progress} />
                  </Box>
                ))}
                {!objectives.length && !loading && (
                  <EmptyState title="No objectives" action={<Button onClick={() => navigate('/objectives')}>Create one</Button>} />
                )}
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Overdue / Urgent Items
              </Typography>
              <Stack spacing={1.5}>
                {overdueTasks.slice(0, 6).map((t) => (
                  <Box
                    key={t.id}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: 'action.hover',
                    }}
                  >
                    <Typography variant="body2" fontWeight={600}>
                      {t.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t.objective_name} · {t.days_overdue}d overdue · due {formatDate(t.deadline)}
                    </Typography>
                  </Box>
                ))}
                {!overdueTasks.length && !loading && (
                  <EmptyState title="No overdue tasks" description="Great €” urgent-items API reports none." />
                )}
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>

      {overview && (
        <Typography variant="caption" color="text.secondary" display="block" mt={3}>
          Last refreshed {formatRelative(new Date().toISOString())} · Backend overview fields only
        </Typography>
      )}
    </Box>
  )
}
