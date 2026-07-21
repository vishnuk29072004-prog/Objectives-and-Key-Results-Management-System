import axios from 'axios'
import { API_BASE_URL } from '../constants/theme'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.response?.data?.message ||
      error.message ||
      'Network request failed'
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
  }
)

/** Health */
export const getHealth = () => api.get('/api/health')

/** Objectives */
export const getObjectives = () => api.get('/api/objectives')
export const createObjective = (payload) => api.post('/api/objectives', payload)
export const createAgenticObjective = (payload) => api.post('/api/agentic/objectives', payload)
export const getObjectiveSuggestion = (objective) =>
  api.post('/api/objective-suggestion', { objective })
export const getRequiredInputs = (objective) =>
  api.post('/api/required-inputs', { objective })
export const getObjectiveTasks = (objectiveId) =>
  api.get(`/api/objectives/${objectiveId}/tasks`)
export const getObjectiveProgress = (objectiveId) =>
  api.get(`/api/objectives/${objectiveId}/progress`)
export const getAiRecommendation = (objectiveId) =>
  api.get(`/api/objectives/${objectiveId}/ai-recommendation`)
export const getAiSummary = (objectiveId) =>
  api.get(`/api/objectives/${objectiveId}/ai-summary`)
export const getAgenticAnalysis = (objectiveId) =>
  api.get(`/api/agentic/objectives/${objectiveId}/analysis`)

/** Subtasks */
export const updateSubtask = (subtaskId, payload) =>
  api.post(`/api/subtasks/${subtaskId}/update`, payload)
export const reviewSubtask = (subtaskId, status) =>
  api.post(`/api/subtasks/${subtaskId}/review`, { status })
export const editSubtask = (subtaskId, result) =>
  api.post(`/api/subtasks/${subtaskId}/edit`, { result })
export const aiGenerateSubtask = (subtaskId) =>
  api.post(`/api/subtasks/${subtaskId}/ai-generate`)
export const regenerateSubtask = (subtaskId) =>
  api.post(`/api/subtasks/${subtaskId}/regenerate`)
export const executeSubtask = (subtaskId) =>
  api.post(`/api/agentic/subtasks/${subtaskId}/execute`)

/** Reminders */
export const checkReminders = () => api.get('/reminders/check/')
export const triggerReminders = () => api.post('/api/reminders/trigger')
export const testReminders = () => api.get('/api/reminders/test')
export const getSchedulerStatus = () => api.get('/api/reminders/scheduler/status')
export const startScheduler = () => api.post('/api/reminders/scheduler/start')
export const stopScheduler = () => api.post('/api/reminders/scheduler/stop')

/** Dashboard */
export const getDashboardOverview = () => api.get('/api/dashboard/overview')
export const getDashboardStatistics = () => api.get('/api/dashboard/statistics')
export const getUrgentItems = () => api.get('/api/dashboard/urgent-items')

/** Progress / Deadlines */
export const updateAllProgress = () => api.post('/api/progress/update-all')
export const recalculateDeadlines = () => api.post('/api/deadlines/recalculate')
export const recalculateObjectiveDeadlines = (objectiveId) =>
  api.post(`/api/deadlines/recalculate/${objectiveId}`)
export const validateBoundaries = (objectiveId) =>
  api.post(`/api/deadlines/validate-boundaries?objective_id=${objectiveId}`)
export const getProgressDrift = (objectiveId) =>
  api.get(`/api/deadlines/progress-drift/${objectiveId}`)
export const shiftDeadlines = (objectiveId, shiftDays, reason = 'manual') =>
  api.post(`/api/deadlines/shift/${objectiveId}?shift_days=${shiftDays}&reason=${encodeURIComponent(reason)}`)
export const autoAdjustDeadlines = (objectiveId) =>
  api.post(`/api/deadlines/auto-adjust/${objectiveId}`)
export const validateShift = (objectiveId, shiftDays) =>
  api.post(`/api/deadlines/validate-shift/${objectiveId}?shift_days=${shiftDays}`)
export const dependencyAdjust = (objectiveId) =>
  api.post(`/api/deadlines/dependency-adjust/${objectiveId}`)
export const getShiftHistory = (objectiveId) =>
  api.get(`/api/deadlines/shift-history/${objectiveId}`)

export default api
