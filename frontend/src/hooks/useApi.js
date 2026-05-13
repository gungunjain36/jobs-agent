import { useState, useEffect, useCallback } from 'react'

const BASE = 'http://localhost:8000'

export function useStatus(interval = 10000) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/agent/status`)
      if (!res.ok) throw new Error(res.statusText)
      setData(await res.json())
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    fetch_()
    const id = setInterval(fetch_, interval)
    return () => clearInterval(id)
  }, [fetch_, interval])

  return { data, error, refetch: fetch_ }
}

export function useJobs(limit = 30) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetch_ = useCallback(async (q) => {
    setLoading(true)
    try {
      const url = q
        ? `${BASE}/jobs/search?q=${encodeURIComponent(q)}&limit=${limit}`
        : `${BASE}/jobs?limit=${limit}`
      const res = await fetch(url)
      setData(await res.json())
    } catch {
      setData([])
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => { fetch_() }, [fetch_])

  return { data, loading, refetch: fetch_ }
}

export async function pauseAgent() {
  const res = await fetch(`${BASE}/agent/pause`, { method: 'POST' })
  return res.json()
}

export async function resumeAgent() {
  const res = await fetch(`${BASE}/agent/resume`, { method: 'POST' })
  return res.json()
}

export async function triggerSearch(keyword) {
  const res = await fetch(`${BASE}/agent/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keyword }),
  })
  return res.json()
}
