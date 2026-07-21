import { useCallback, useEffect, useState } from 'react'
import { useSnackbar } from 'notistack'
import {
  Box,
  Button,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import {
  getAgenticAnalysis,
  getAiRecommendation,
  getAiSummary,
  getProgressDrift,
} from '../services/api'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader, ErrorState, EmptyState } from '../components/common/PageStates'
import { MarkdownPanel, MotionCard, ProgressBar } from '../components/common/UiKit'
import StatCard from '../components/common/StatCard'
import { clampPercent, deriveAiHealthScore, deriveProductivityScore } from '../utils/helpers'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

export default function AiInsightsPage() {
  const { objectives, overview, reminders, refreshAll } = useAppData()
  const { enqueueSnackbar } = useSnackbar()
  const [objectiveId, setObjectiveId] = useState(objectives[0]?.id || '')
  const [summary, setSummary] = useState('')
  const [recommendation, setRecommendation] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [drift, setDrift] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  useEffect(() => {
    if (!objectiveId && objectives[0]?.id) setObjectiveId(objectives[0].id)
  }, [objectives, objectiveId])

  const loadInsights = useCallback(async () => {
    if (!objectiveId) return
    setLoading(true)
    setError(null)
    try {
      const [sum, rec, ana, dr] = await Promise.allSettled([
        getAiSummary(objectiveId),
        getAiRecommendation(objectiveId),
        getAgenticAnalysis(objectiveId),
        getProgressDrift(objectiveId),
      ])
      if (sum.status === 'fulfilled') setSummary(sum.value.data?.summary || '')
      else setSummary('')
      if (rec.status === 'fulfilled') setRecommendation(rec.value.data?.recommendation || null)
      else setRecommendation(null)
      if (ana.status === 'fulfilled') setAnalysis(ana.value.data || null)
      else setAnalysis(null)
      if (dr.status === 'fulfilled') setDrift(dr.value.data || null)
      else setDrift(null)

      const failed = [sum, rec, ana, dr].filter((r) => r.status === 'rejected')
      if (failed.length === 4) {
        setError(failed[0].reason?.message || 'All AI endpoints failed')
      }
    } catch (err) {
      setError(err.message)
      enqueueSnackbar(err.message, { variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [objectiveId, enqueueSnackbar])

  useEffect(() => {
    loadInsights()
  }, [loadInsights])

  const selected = objectives.find((o) => o.id === Number(objectiveId))
  const forecast = selected ? clampPercent(selected.progress) : 0
  const risk =
    forecast < 30 ? 'High' : forecast < 60 ? 'Medium' : 'Low'

  return (
    <Box>
      <PageHeader
        title="AI Insights"
        subtitle="Live AI summary, recommendations, agentic analysis & drift from FastAPI"
        actions={
          <Stack direction="row" spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 260 }}>
              <InputLabel>Objective</InputLabel>
              <Select
                label="Objective"
                value={objectiveId || ''}
                onChange={(e) => setObjectiveId(e.target.value)}
              >
                {objectives.map((o) => (
                  <MenuItem key={o.id} value={o.id}>
                    #{o.id} · {o.objective.slice(0, 42)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AutoAwesomeIcon />}
              onClick={loadInsights}
              disabled={loading || !objectiveId}
            >
              Refresh AI
            </Button>
          </Stack>
        }
      />

      {error && <ErrorState message={error} onRetry={loadInsights} />}

      <Grid container spacing={2.5} mb={2}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard
            title="Goal Prediction"
            value={`${forecast}%`}
            subtitle="Current completion as forecast baseline"
            color={COLORS.primary}
            loading={loading && !selected}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard
            title="Completion Forecast"
            value={selected ? `${clampPercent(selected.progress)}%` : '€”'}
            subtitle="From objective progress field"
            color={COLORS.success}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard
            title="Risk Analysis"
            value={risk}
            subtitle={`AI health ${deriveAiHealthScore(overview, reminders)} · Productivity ${deriveProductivityScore(overview)}`}
            color={risk === 'High' ? COLORS.danger : risk === 'Medium' ? COLORS.warning : COLORS.success}
          />
        </Grid>
      </Grid>

      {!objectives.length && (
        <EmptyState title="No objectives" description="Create an objective to unlock AI insights." />
      )}

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                AI Summary
              </Typography>
              {selected && <ProgressBar value={selected.progress} />}
              <Box mt={2}>
                {summary ? (
                  <MarkdownPanel content={summary} />
                ) : (
                  <EmptyState title={loading ? 'Generating€¦' : 'No summary'} description="GET /api/objectives/{id}/ai-summary" />
                )}
              </Box>
            </CardContent>
          </MotionCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                AI Recommendations
              </Typography>
              {recommendation ? (
                <MarkdownPanel content={recommendation} />
              ) : (
                <EmptyState title={loading ? 'Generating€¦' : 'No recommendations'} description="GET /api/objectives/{id}/ai-recommendation" />
              )}
            </CardContent>
          </MotionCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                Agentic Analysis
              </Typography>
              {analysis ? (
                <Stack spacing={2}>
                  <MarkdownPanel title="Progress Analysis" content={analysis.progress_analysis} />
                  <MarkdownPanel title="AI Recommendation" content={analysis.ai_recommendation} />
                  {analysis.agent_messages && (
                    <MarkdownPanel title="Agent Messages" content={analysis.agent_messages} />
                  )}
                </Stack>
              ) : (
                <EmptyState title={loading ? 'Loading€¦' : 'No analysis'} description="GET /api/agentic/objectives/{id}/analysis" />
              )}
            </CardContent>
          </MotionCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                Smart Suggestions / Drift
              </Typography>
              {drift ? (
                <MarkdownPanel content={JSON.stringify(drift.drift_analysis || drift, null, 2)} />
              ) : (
                <EmptyState title={loading ? 'Loading€¦' : 'No drift data'} description="GET /api/deadlines/progress-drift/{id}" />
              )}
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
