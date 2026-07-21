import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Generic async data fetcher with loading / error / retry.
 * @param {() => Promise<any>} fetcher
 * @param {{ immediate?: boolean, deps?: any[] }} options
 */
export function useApi(fetcher, { immediate = true, deps = [] } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(Boolean(immediate))
  const [error, setError] = useState(null)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetcherRef.current(...args)
      const payload = result?.data !== undefined ? result.data : result
      setData(payload)
      return payload
    } catch (err) {
      setError(err.message || 'Request failed')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const retry = useCallback(() => execute(), [execute])

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate, execute, ...deps])

  return { data, loading, error, execute, retry, setData }
}

export default useApi
