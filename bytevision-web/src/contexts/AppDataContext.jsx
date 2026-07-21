import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import {
  getObjectives,
  getDashboardOverview,
  getDashboardStatistics,
  getUrgentItems,
  checkReminders,
} from '../services/api'

const AppDataContext = createContext(null)

export function AppDataProvider({ children }) {
  const [objectives, setObjectives] = useState([])
  const [overview, setOverview] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [urgentItems, setUrgentItems] = useState(null)
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastFetched, setLastFetched] = useState(null)

  const refreshAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [objRes, ovRes, stRes, urgRes, remRes] = await Promise.all([
        getObjectives(),
        getDashboardOverview(),
        getDashboardStatistics(),
        getUrgentItems(),
        checkReminders(),
      ])
      setObjectives(objRes.data?.objectives || [])
      setOverview(ovRes.data?.overview || null)
      setStatistics(stRes.data?.statistics || null)
      setUrgentItems(urgRes.data?.urgent_items || null)
      setReminders(remRes.data?.reminders || [])
      setLastFetched(new Date().toISOString())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const value = useMemo(
    () => ({
      objectives,
      overview,
      statistics,
      urgentItems,
      reminders,
      loading,
      error,
      lastFetched,
      refreshAll,
      setObjectives,
    }),
    [objectives, overview, statistics, urgentItems, reminders, loading, error, lastFetched, refreshAll]
  )

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
}

export function useAppData() {
  const ctx = useContext(AppDataContext)
  if (!ctx) throw new Error('useAppData must be used within AppDataProvider')
  return ctx
}
