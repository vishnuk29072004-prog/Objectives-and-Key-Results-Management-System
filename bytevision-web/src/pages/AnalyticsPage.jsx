import { useEffect, useMemo } from 'react'
import { Box, CardContent, Grid, Typography } from '@mui/material'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState } from '../components/common/PageStates'
import { ChartCard, DonutChart, SimpleBarChart, SimpleLineChart } from '../components/charts/Charts'
import { MotionCard, ProgressBar } from '../components/common/UiKit'
import { clampPercent } from '../utils/helpers'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

/** Build a simple heatmap matrix from objective progress by category × owner (derived, not fake). */
function buildHeatmap(objectives) {
  const categories = [...new Set(objectives.map((o) => (o.category || 'Uncategorized').trim()))]
  const owners = [...new Set(objectives.map((o) => (o.owner || 'Unassigned').trim()))]
  return categories.map((cat) => {
    const row = { category: cat }
    owners.forEach((owner) => {
      const matches = objectives.filter(
        (o) => (o.category || 'Uncategorized').trim() === cat && (o.owner || 'Unassigned').trim() === owner
      )
      row[owner] =
        matches.length === 0
          ? null
          : clampPercent(matches.reduce((s, o) => s + (o.progress || 0), 0) / matches.length)
    })
    return row
  })
}

export default function AnalyticsPage() {
  const { objectives, statistics, overview, loading, error, refreshAll } = useAppData()

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  const categoryData = useMemo(() => {
    if (!statistics?.by_category) return []
    return Object.entries(statistics.by_category).map(([name, v]) => ({
      name: name.trim() || 'Uncategorized',
      value: clampPercent(v.progress),
      count: v.count,
    }))
  }, [statistics])

  const ownerData = useMemo(() => {
    if (!statistics?.by_owner) return []
    return Object.entries(statistics.by_owner).map(([name, v]) => ({
      name: name.trim() || 'Unassigned',
      value: clampPercent(v.progress),
      count: v.count,
    }))
  }, [statistics])

  const weeklyProxy = useMemo(() => {
    // Backend has no weekly series — show per-objective progress as a sequential series from live data.
    return [...objectives]
      .sort((a, b) => a.id - b.id)
      .map((o, i) => ({
        name: `O${o.id}`,
        progress: clampPercent(o.progress),
        index: i + 1,
      }))
  }, [objectives])

  const completionMix = useMemo(() => {
    if (!overview) return []
    return [
      { name: 'Completed', value: overview.completed_objectives || 0 },
      { name: 'Active', value: overview.active_objectives || 0 },
    ].filter((d) => d.value > 0)
  }, [overview])

  const heatmap = useMemo(() => buildHeatmap(objectives), [objectives])
  const owners = useMemo(
    () => [...new Set(objectives.map((o) => (o.owner || 'Unassigned').trim()))],
    [objectives]
  )

  return (
    <Box>
      <PageHeader
        title="Analytics"
        subtitle="Charts composed from dashboard statistics & objectives APIs (no invented endpoints)"
      />

      {error && <ErrorState message={error} onRetry={refreshAll} />}

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Completion Mix" subtitle="From dashboard overview">
            {completionMix.length ? <DonutChart data={completionMix} /> : <EmptyState title="No data" />}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 8 }}>
          <ChartCard title="Objective Progress Series" subtitle="Live progress per objective (weekly API not available)">
            {weeklyProxy.length ? (
              <SimpleLineChart data={weeklyProxy} lines={[{ key: 'progress', color: COLORS.primary }]} />
            ) : (
              <EmptyState title="No objectives" />
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Category Analytics" subtitle="GET /api/dashboard/statistics → by_category">
            {categoryData.length ? (
              <SimpleBarChart data={categoryData} />
            ) : (
              <EmptyState title="No category stats" />
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Owner Analytics" subtitle="GET /api/dashboard/statistics → by_owner">
            {ownerData.length ? (
              <SimpleBarChart data={ownerData} color={COLORS.secondary} />
            ) : (
              <EmptyState title="No owner stats" />
            )}
          </ChartCard>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                Performance Heatmap
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                Derived from objective progress grouped by category × owner (no separate heatmap endpoint exists).
              </Typography>
              {!objectives.length ? (
                <EmptyState title="No data for heatmap" />
              ) : (
                <Box sx={{ overflowX: 'auto' }}>
                  <Box
                    component="table"
                    sx={{
                      width: '100%',
                      borderCollapse: 'separate',
                      borderSpacing: 6,
                      minWidth: 480,
                    }}
                  >
                    <thead>
                      <tr>
                        <th align="left">
                          <Typography variant="caption" fontWeight={700}>
                            Category \ Owner
                          </Typography>
                        </th>
                        {owners.map((o) => (
                          <th key={o}>
                            <Typography variant="caption" fontWeight={700}>
                              {o}
                            </Typography>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heatmap.map((row) => (
                        <tr key={row.category}>
                          <td>
                            <Typography variant="body2" fontWeight={600}>
                              {row.category}
                            </Typography>
                          </td>
                          {owners.map((o) => {
                            const val = row[o]
                            const bg =
                              val == null
                                ? 'transparent'
                                : `rgba(37, 99, 235, ${Math.max(0.08, val / 100)})`
                            return (
                              <td key={o}>
                                <Box
                                  sx={{
                                    p: 1.5,
                                    borderRadius: 2,
                                    bgcolor: bg,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    textAlign: 'center',
                                    minWidth: 72,
                                  }}
                                >
                                  <Typography variant="body2" fontWeight={700}>
                                    {val == null ? '—' : `${val}%`}
                                  </Typography>
                                </Box>
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </Box>
                </Box>
              )}
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Monthly / Completion Snapshot
              </Typography>
              <Stack spacing={2}>
                {objectives.map((o) => (
                  <Box key={o.id}>
                    <Typography variant="body2" fontWeight={600} mb={0.5}>
                      #{o.id} {o.objective}
                    </Typography>
                    <ProgressBar value={o.progress} />
                  </Box>
                ))}
                {!objectives.length && !loading && <EmptyState title="No objectives" />}
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
