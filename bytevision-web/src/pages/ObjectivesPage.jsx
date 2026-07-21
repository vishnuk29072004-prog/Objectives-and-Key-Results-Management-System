import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useSnackbar } from 'notistack'
import {
  Box,
  Button,
  CardContent,
  Chip,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import VisibilityIcon from '@mui/icons-material/Visibility'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import SummarizeIcon from '@mui/icons-material/Summarize'
import RefreshIcon from '@mui/icons-material/Refresh'
import {
  createObjective,
  getAiRecommendation,
  getAiSummary,
  getObjectiveSuggestion,
  getRequiredInputs,
  recalculateObjectiveDeadlines,
} from '../services/api'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState } from '../components/common/PageStates'
import {
  DeadlineChip,
  FormDialog,
  MarkdownPanel,
  MotionCard,
  ProgressBar,
  SearchField,
} from '../components/common/UiKit'
import { clampPercent, formatDate } from '../utils/helpers'
import { Stack } from '../components/common/Stack'

const PAGE_SIZE = 6

export default function ObjectivesPage() {
  const navigate = useNavigate()
  const { enqueueSnackbar } = useSnackbar()
  const { objectives, loading, error, refreshAll } = useAppData()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('progress_desc')
  const [filterCategory, setFilterCategory] = useState('all')
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [suggestion, setSuggestion] = useState('')
  const [requiredInputs, setRequiredInputs] = useState([])
  const [aiPanel, setAiPanel] = useState({ open: false, title: '', content: null, loading: false })

  const { register, handleSubmit, reset, watch } = useForm({
    defaultValues: { objective: '', deadline: '', category: '', owner: '' },
  })
  const objectiveText = watch('objective')

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  const categories = useMemo(() => {
    const set = new Set(objectives.map((o) => (o.category || '').trim()).filter(Boolean))
    return ['all', ...Array.from(set)]
  }, [objectives])

  const filtered = useMemo(() => {
    let list = [...objectives]
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (o) =>
          o.objective?.toLowerCase().includes(q) ||
          o.owner?.toLowerCase().includes(q) ||
          o.category?.toLowerCase().includes(q)
      )
    }
    if (filterCategory !== 'all') {
      list = list.filter((o) => (o.category || '').trim() === filterCategory)
    }
    list.sort((a, b) => {
      if (sort === 'progress_desc') return (b.progress || 0) - (a.progress || 0)
      if (sort === 'progress_asc') return (a.progress || 0) - (b.progress || 0)
      if (sort === 'deadline_asc') return String(a.deadline).localeCompare(String(b.deadline))
      if (sort === 'deadline_desc') return String(b.deadline).localeCompare(String(a.deadline))
      return a.id - b.id
    })
    return list
  }, [objectives, search, sort, filterCategory])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const loadSuggestion = useCallback(async () => {
    if (!objectiveText?.trim()) return
    try {
      const [sug, req] = await Promise.all([
        getObjectiveSuggestion(objectiveText),
        getRequiredInputs(objectiveText),
      ])
      setSuggestion(sug.data?.suggestion || '')
      setRequiredInputs(req.data?.inputs || [])
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    }
  }, [objectiveText, enqueueSnackbar])

  const onCreate = handleSubmit(async (values) => {
    setCreating(true)
    try {
      await createObjective({
        objective: values.objective,
        deadline: values.deadline,
        category: values.category || null,
        owner: values.owner || null,
      })
      enqueueSnackbar('Objective created €” AI is breaking down tasks', { variant: 'success' })
      setCreateOpen(false)
      reset()
      setSuggestion('')
      setRequiredInputs([])
      await refreshAll()
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setCreating(false)
    }
  })

  const openAi = async (type, objectiveId) => {
    setAiPanel({ open: true, title: type === 'summary' ? 'AI Summary' : 'AI Recommendation', content: null, loading: true })
    try {
      const res =
        type === 'summary' ? await getAiSummary(objectiveId) : await getAiRecommendation(objectiveId)
      setAiPanel((p) => ({
        ...p,
        loading: false,
        content: type === 'summary' ? res.data?.summary : res.data?.recommendation,
      }))
    } catch (err) {
      setAiPanel((p) => ({ ...p, loading: false, content: err.message }))
      enqueueSnackbar(err.message, { variant: 'error' })
    }
  }

  const onRecalc = async (id) => {
    try {
      await recalculateObjectiveDeadlines(id)
      enqueueSnackbar('Deadlines recalculated', { variant: 'success' })
      refreshAll()
    } catch (err) {
      enqueueSnackbar(err.message, { variant: 'error' })
    }
  }

  return (
    <Box>
      <PageHeader
        title="Objectives"
        subtitle={`${objectives.length} objectives from GET /api/objectives`}
        actions={
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            New Objective
          </Button>
        }
      />

      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={1.5}
        mb={3}
        alignItems={{ md: 'center' }}
      >
        <SearchField value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search objectives€¦" />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Category</InputLabel>
          <Select
            label="Category"
            value={filterCategory}
            onChange={(e) => { setFilterCategory(e.target.value); setPage(1) }}
          >
            {categories.map((c) => (
              <MenuItem key={c} value={c}>
                {c === 'all' ? 'All categories' : c}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Sort</InputLabel>
          <Select label="Sort" value={sort} onChange={(e) => setSort(e.target.value)}>
            <MenuItem value="progress_desc">Progress †“</MenuItem>
            <MenuItem value="progress_asc">Progress †‘</MenuItem>
            <MenuItem value="deadline_asc">Deadline †‘</MenuItem>
            <MenuItem value="deadline_desc">Deadline †“</MenuItem>
            <MenuItem value="id">ID</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {error && <ErrorState message={error} onRetry={refreshAll} />}

      {!loading && !filtered.length && (
        <EmptyState
          title="No objectives match"
          description="Adjust filters or create a new objective via POST /api/objectives."
          action={
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
              Create Objective
            </Button>
          }
        />
      )}

      <Grid container spacing={2.5}>
        {pageItems.map((o) => (
          <Grid key={o.id} size={{ xs: 12, md: 6, lg: 4 }}>
            <MotionCard sx={{ height: '100%' }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Chip size="small" label={o.category?.trim() || 'Uncategorized'} />
                  <DeadlineChip deadline={o.deadline} />
                </Stack>
                <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1, minHeight: 48 }}>
                  {o.objective}
                </Typography>
                <Stack direction="row" spacing={1} mb={2} flexWrap="wrap" useFlexGap>
                  <Chip size="small" variant="outlined" label={`Owner: ${o.owner?.trim() || 'Unassigned'}`} />
                  <Chip size="small" variant="outlined" label={`ID ${o.id}`} />
                </Stack>
                <ProgressBar value={o.progress} label={`Completion ${clampPercent(o.progress)}%`} />
                <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                  Deadline {formatDate(o.deadline)}
                </Typography>
                <Stack direction="row" spacing={0.5} mt={2} flexWrap="wrap" useFlexGap>
                  <Tooltip title="View tasks">
                    <IconButton size="small" color="primary" onClick={() => navigate(`/objectives/${o.id}`)} aria-label="View">
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="AI Summary">
                    <IconButton size="small" onClick={() => openAi('summary', o.id)} aria-label="AI Summary">
                      <SummarizeIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="AI Recommendation">
                    <IconButton size="small" onClick={() => openAi('rec', o.id)} aria-label="AI Recommendation">
                      <AutoAwesomeIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Recalculate deadlines">
                    <IconButton size="small" onClick={() => onRecalc(o.id)} aria-label="Recalculate">
                      <RefreshIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Button size="small" onClick={() => navigate(`/tasks?objective=${o.id}`)}>
                    Tasks
                  </Button>
                </Stack>
              </CardContent>
            </MotionCard>
          </Grid>
        ))}
      </Grid>

      {pageCount > 1 && (
        <Stack alignItems="center" mt={3}>
          <Pagination count={pageCount} page={page} onChange={(_, p) => setPage(p)} color="primary" />
        </Stack>
      )}

      <FormDialog
        open={createOpen}
        title="Create Objective"
        onClose={() => setCreateOpen(false)}
        onSubmit={onCreate}
        loading={creating}
        submitLabel="Create with AI"
        maxWidth="md"
      >
        <Stack spacing={2} mt={1}>
          <TextField
            label="Objective"
            multiline
            minRows={3}
            fullWidth
            required
            {...register('objective', { required: true })}
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Deadline"
              type="date"
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
              {...register('deadline', { required: true })}
            />
            <TextField label="Category" fullWidth {...register('category')} />
            <TextField label="Owner" fullWidth {...register('owner')} />
          </Stack>
          <Button onClick={loadSuggestion} disabled={!objectiveText?.trim()}>
            Get AI suggestion & required inputs
          </Button>
          {suggestion && <MarkdownPanel title="AI Suggestion" content={suggestion} />}
          {requiredInputs.length > 0 && (
            <MarkdownPanel title="Required Inputs" content={requiredInputs} />
          )}
        </Stack>
      </FormDialog>

      <FormDialog
        open={aiPanel.open}
        title={aiPanel.title}
        onClose={() => setAiPanel({ open: false, title: '', content: null, loading: false })}
        onSubmit={() => setAiPanel({ open: false, title: '', content: null, loading: false })}
        submitLabel="Close"
        loading={aiPanel.loading}
        maxWidth="md"
      >
        {aiPanel.loading ? (
          <Typography>Generating from backend€¦</Typography>
        ) : (
          <MarkdownPanel content={aiPanel.content} />
        )}
      </FormDialog>
    </Box>
  )
}
