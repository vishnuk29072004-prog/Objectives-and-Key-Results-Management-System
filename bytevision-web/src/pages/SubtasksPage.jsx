import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Box,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  CardContent,
} from '@mui/material'
import { getObjectiveTasks } from '../services/api'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState, LoadingBlock } from '../components/common/PageStates'
import { DeadlineChip, MotionCard, StatusBadge } from '../components/common/UiKit'
import { formatDate } from '../utils/helpers'
import { Stack } from '../components/common/Stack'

export default function SubtasksPage() {
  const { objectives, refreshAll } = useAppData()
  const [objectiveId, setObjectiveId] = useState(objectives[0]?.id || '')
  const [statusFilter, setStatusFilter] = useState('all')
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  useEffect(() => {
    if (!objectiveId && objectives[0]?.id) setObjectiveId(objectives[0].id)
  }, [objectives, objectiveId])

  const load = useCallback(async () => {
    if (!objectiveId) return
    setLoading(true)
    setError(null)
    try {
      const res = await getObjectiveTasks(objectiveId)
      const flat = []
      ;(res.data?.tasks || []).forEach((task) => {
        ;(task.subtasks || []).forEach((st) => {
          flat.push({
            ...st,
            taskId: task.id,
            taskName: task.name,
          })
        })
      })
      setRows(flat)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [objectiveId])

  useEffect(() => {
    load()
  }, [load])

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return rows
    return rows.filter((r) => String(r.status).toLowerCase() === statusFilter)
  }, [rows, statusFilter])

  const statuses = useMemo(() => {
    const s = new Set(rows.map((r) => String(r.status || 'pending').toLowerCase()))
    return ['all', ...Array.from(s)]
  }, [rows])

  return (
    <Box>
      <PageHeader
        title="Subtasks"
        subtitle="Flattened subtask list derived from objective tasks API"
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel>Objective</InputLabel>
              <Select
                label="Objective"
                value={objectiveId || ''}
                onChange={(e) => setObjectiveId(e.target.value)}
              >
                {objectives.map((o) => (
                  <MenuItem key={o.id} value={o.id}>
                    #{o.id} · {o.objective.slice(0, 40)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Status</InputLabel>
              <Select label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                {statuses.map((s) => (
                  <MenuItem key={s} value={s}>
                    {s}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        }
      />

      {error && <ErrorState message={error} onRetry={load} />}
      {loading && <LoadingBlock rows={5} />}

      {!loading && !filtered.length && (
        <EmptyState title="No subtasks" description="No subtasks returned for this objective/filter." />
      )}

      <Stack spacing={1.5}>
        {filtered.map((st) => (
          <MotionCard key={st.id}>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ md: 'center' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Task: {st.taskName}
                  </Typography>
                  <Typography fontWeight={700}>{st.name}</Typography>
                </Box>
                <StatusBadge status={st.status} />
                <DeadlineChip deadline={st.deadline} />
                <Chip size="small" variant="outlined" label={`Weight ${st.weight ?? 1}`} />
                <Chip size="small" variant="outlined" label={`Due ${formatDate(st.deadline)}`} />
              </Stack>
            </CardContent>
          </MotionCard>
        ))}
      </Stack>
    </Box>
  )
}
