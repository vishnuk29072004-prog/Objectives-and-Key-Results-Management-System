import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useSnackbar } from 'notistack'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import RateReviewIcon from '@mui/icons-material/RateReview'
import EditIcon from '@mui/icons-material/Edit'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import {
  aiGenerateSubtask,
  editSubtask,
  executeSubtask,
  getObjectiveProgress,
  getObjectiveTasks,
  reviewSubtask,
  updateSubtask,
} from '../services/api'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState, LoadingBlock } from '../components/common/PageStates'
import {
  DeadlineChip,
  FormDialog,
  MarkdownPanel,
  ProgressBar,
  StatusBadge,
} from '../components/common/UiKit'
import { clampPercent, formatDate } from '../utils/helpers'
import { Stack } from '../components/common/Stack'

export default function TasksPage() {
  const { objectives, refreshAll } = useAppData()
  const [params, setParams] = useSearchParams()
  const routeParams = useParams()
  const navigate = useNavigate()
  const { enqueueSnackbar } = useSnackbar()
  const selectedId =
    Number(routeParams.id) || Number(params.get('objective')) || objectives[0]?.id || null

  const [tasks, setTasks] = useState([])
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [actionOpen, setActionOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [activeSubtask, setActiveSubtask] = useState(null)
  const [resultText, setResultText] = useState('')
  const [comment, setComment] = useState('')
  const [aiPreview, setAiPreview] = useState('')

  const load = useCallback(async (objectiveId) => {
    if (!objectiveId) return
    setLoading(true)
    setError(null)
    try {
      const [tRes, pRes] = await Promise.all([
        getObjectiveTasks(objectiveId),
        getObjectiveProgress(objectiveId),
      ])
      setTasks(tRes.data?.tasks || [])
      setProgress(pRes.data?.summary || null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  useEffect(() => {
    if (selectedId) load(selectedId)
  }, [selectedId, load])

  const openAction = (subtask) => {
    setActiveSubtask(subtask)
    setResultText(subtask.result || subtask.ai_generated_result || '')
    setComment(subtask.comment || '')
    setAiPreview(subtask.ai_generated_result || '')
    setActionOpen(true)
  }

  const runAiGenerate = async () => {
    if (!activeSubtask) return
    setActionLoading(true)
    try {
      const res = await aiGenerateSubtask(activeSubtask.id)
      setAiPreview(res.data?.result || '')
      setResultText(res.data?.result || '')
      enqueueSnackbar('AI result generated', { variant: 'success' })
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const runExecute = async () => {
    if (!activeSubtask) return
    setActionLoading(true)
    try {
      const res = await executeSubtask(activeSubtask.id)
      setAiPreview(res.data?.result || '')
      setResultText(res.data?.result || resultText)
      enqueueSnackbar(res.data?.message || 'Executed', { variant: 'success' })
      await load(selectedId)
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const saveUpdate = async () => {
    if (!activeSubtask) return
    setActionLoading(true)
    try {
      await updateSubtask(activeSubtask.id, { result: resultText, comment })
      enqueueSnackbar('Subtask updated', { variant: 'success' })
      setActionOpen(false)
      await load(selectedId)
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const saveEdit = async () => {
    if (!activeSubtask) return
    setActionLoading(true)
    try {
      await editSubtask(activeSubtask.id, resultText)
      enqueueSnackbar('Result edited', { variant: 'success' })
      await load(selectedId)
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const onReview = async (status) => {
    if (!activeSubtask) return
    setActionLoading(true)
    try {
      await reviewSubtask(activeSubtask.id, status)
      enqueueSnackbar(`Marked as ${status}`, { variant: 'success' })
      setActionOpen(false)
      await load(selectedId)
      refreshAll()
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const selectedObjective = objectives.find((o) => o.id === selectedId)

  return (
    <Box>
      <PageHeader
        title="Tasks"
        subtitle="Tasks & expandable subtasks from GET /api/objectives/{id}/tasks"
        actions={
          <FormControl size="small" sx={{ minWidth: 260 }}>
            <InputLabel>Objective</InputLabel>
            <Select
              label="Objective"
              value={selectedId || ''}
              onChange={(e) => setParams({ objective: String(e.target.value) })}
            >
              {objectives.map((o) => (
                <MenuItem key={o.id} value={o.id}>
                  #{o.id} · {o.objective.slice(0, 48)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        }
      />

      {progress && (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={3}>
          <Chip label={`Tasks ${progress.completedTasks}/${progress.totalTasks}`} />
          <Chip label={`Subtasks ${progress.completedSubtasks}/${progress.totalSubtasks}`} />
          <Chip color="primary" label={`Objective ${clampPercent(progress.objectiveCompletion)}%`} />
          <Box sx={{ flex: 1, minWidth: 160 }}>
            <ProgressBar value={progress.objectiveCompletion} />
          </Box>
        </Stack>
      )}

      {error && <ErrorState message={error} onRetry={() => load(selectedId)} />}
      {loading && <LoadingBlock rows={4} />}

      {!loading && !tasks.length && (
        <EmptyState
          title="No tasks for this objective"
          description={selectedObjective ? 'Backend returned an empty task list.' : 'Select or create an objective first.'}
          action={<Button onClick={() => navigate('/objectives')}>Go to Objectives</Button>}
        />
      )}

      <Stack spacing={1.5}>
        {tasks.map((task) => (
          <Accordion key={task.id} defaultExpanded={task.progress < 100} sx={{ borderRadius: 2, '&:before': { display: 'none' }, border: '1px solid', borderColor: 'divider' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }} width="100%" pr={2}>
                <Typography fontWeight={700} sx={{ flex: 1 }}>
                  {task.name}
                </Typography>
                <DeadlineChip deadline={task.deadline} />
                <Chip size="small" label={`${clampPercent(task.progress)}%`} color="primary" variant="outlined" />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <ProgressBar value={task.progress} label="Task completion" />
              <Typography variant="caption" color="text.secondary" display="block" mt={1} mb={2}>
                Deadline {formatDate(task.deadline)} · {task.subtasks?.length || 0} subtasks
              </Typography>
              <Stack spacing={1.5}>
                {(task.subtasks || []).map((st) => (
                  <Box
                    key={st.id}
                    sx={{
                      p: 1.75,
                      borderRadius: 2,
                      bgcolor: 'action.hover',
                      display: 'flex',
                      flexDirection: { xs: 'column', md: 'row' },
                      gap: 1.5,
                      alignItems: { md: 'center' },
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {st.name}
                      </Typography>
                      <Stack direction="row" spacing={1} mt={0.75} flexWrap="wrap" useFlexGap>
                        <StatusBadge status={st.status} />
                        <DeadlineChip deadline={st.deadline} />
                        <Chip size="small" variant="outlined" label={`Weight ${st.weight ?? 1}`} />
                      </Stack>
                    </Box>
                    <Button size="small" variant="outlined" onClick={() => openAction(st)}>
                      Manage
                    </Button>
                  </Box>
                ))}
              </Stack>
            </AccordionDetails>
          </Accordion>
        ))}
      </Stack>

      <FormDialog
        open={actionOpen}
        title={activeSubtask ? `Subtask #${activeSubtask.id}` : 'Subtask'}
        onClose={() => setActionOpen(false)}
        onSubmit={saveUpdate}
        submitLabel="Save update"
        loading={actionLoading}
        maxWidth="md"
      >
        <Stack spacing={2}>
          <Typography variant="body2" color="text.secondary">
            {activeSubtask?.name}
          </Typography>
          <TextField
            label="Result"
            multiline
            minRows={5}
            fullWidth
            value={resultText}
            onChange={(e) => setResultText(e.target.value)}
          />
          <TextField
            label="Comment"
            fullWidth
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          {aiPreview && <MarkdownPanel title="AI Generated Result" content={aiPreview} />}
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Button startIcon={<AutoAwesomeIcon />} onClick={runAiGenerate} disabled={actionLoading}>
              AI Generate
            </Button>
            <Button startIcon={<PlayArrowIcon />} onClick={runExecute} disabled={actionLoading}>
              Agentic Execute
            </Button>
            <Button startIcon={<EditIcon />} onClick={saveEdit} disabled={actionLoading}>
              Edit Result
            </Button>
            <Button
              startIcon={<RateReviewIcon />}
              color="success"
              onClick={() => onReview('approved')}
              disabled={actionLoading}
            >
              Approve
            </Button>
            <Button color="warning" onClick={() => onReview('pending')} disabled={actionLoading}>
              Pending
            </Button>
            <Button color="error" onClick={() => onReview('rejected')} disabled={actionLoading}>
              Reject
            </Button>
          </Stack>
        </Stack>
      </FormDialog>
    </Box>
  )
}
