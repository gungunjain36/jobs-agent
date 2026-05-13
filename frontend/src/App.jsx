import { useState } from 'react'
import { useStatus, useJobs } from './hooks/useApi'
import StatusBar from './components/StatusBar'
import SearchPanel from './components/SearchPanel'
import JobCard from './components/JobCard'
import KeywordChips from './components/KeywordChips'

const s = {
  layout: { minHeight: '100vh', display: 'flex', flexDirection: 'column' },
  main: { flex: 1, maxWidth: '860px', width: '100%', margin: '0 auto', padding: '32px 24px' },
  header: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginBottom: '28px',
    gap: '12px',
    flexWrap: 'wrap',
  },
  heading: {
    fontFamily: 'var(--font-display)',
    fontWeight: 800,
    fontSize: '22px',
    letterSpacing: '-0.03em',
    color: 'var(--text)',
  },
  count: {
    fontSize: '12px',
    color: 'var(--text-3)',
    letterSpacing: '0.04em',
  },
  jobs: { display: 'flex', flexDirection: 'column', gap: '6px' },
  empty: {
    textAlign: 'center',
    padding: '64px 24px',
    color: 'var(--text-3)',
    fontSize: '13px',
  },
  emptyIcon: { fontSize: '32px', marginBottom: '12px', opacity: 0.4 },
  emptyTitle: { color: 'var(--text-2)', marginBottom: '6px', fontFamily: 'var(--font-display)', fontWeight: 600 },
  skeletonCard: {
    height: '80px',
    marginBottom: '6px',
  },
  lastCycle: {
    fontSize: '10px',
    color: 'var(--text-3)',
    marginBottom: '28px',
    letterSpacing: '0.03em',
  },
  divider: {
    height: '1px',
    background: 'var(--border)',
    margin: '24px 0',
  },
}

export default function App() {
  const { data: status, error, refetch: refetchStatus } = useStatus(10000)
  const { data: jobs, loading, refetch: refetchJobs } = useJobs(50)
  const [filterQuery, setFilterQuery] = useState(null)

  function handleSearch(q) {
    setFilterQuery(q)
    refetchJobs(q)
  }

  const displayJobs = jobs || []

  return (
    <div style={s.layout}>
      <StatusBar status={status} error={error} onRefresh={refetchStatus} />

      <main style={s.main}>
        {status && (
          <KeywordChips keywords={status.keywords} location={status.location} />
        )}

        <div style={s.header}>
          <h1 style={s.heading}>
            {filterQuery ? `Results for "${filterQuery}"` : 'Tracked Jobs'}
          </h1>
          {!loading && (
            <span style={s.count}>
              {displayJobs.length} job{displayJobs.length !== 1 ? 's' : ''}
              {filterQuery && (
                <button
                  onClick={() => handleSearch(null)}
                  style={{
                    marginLeft: '10px',
                    background: 'none',
                    color: 'var(--accent)',
                    fontSize: '11px',
                    padding: 0,
                    textDecoration: 'underline',
                    cursor: 'pointer',
                  }}
                >
                  clear
                </button>
              )}
            </span>
          )}
        </div>

        <SearchPanel onSearch={handleSearch} />

        {status?.last_cycle && status.last_cycle !== 'never' && (
          <div style={s.lastCycle}>
            last cycle: {status.last_cycle} UTC
          </div>
        )}

        <div style={s.divider} />

        <div style={s.jobs}>
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton" style={s.skeletonCard} />
            ))
          ) : displayJobs.length === 0 ? (
            <div style={s.empty}>
              <div style={s.emptyIcon}>◎</div>
              <div style={s.emptyTitle}>No jobs found</div>
              <div>
                {filterQuery
                  ? 'Try a different search term'
                  : 'The agent will populate jobs on the next poll cycle'}
              </div>
            </div>
          ) : (
            displayJobs.map((job, i) => (
              <JobCard key={job.job_id || i} job={job} index={i} />
            ))
          )}
        </div>
      </main>

      <footer style={{
        borderTop: '1px solid var(--border)',
        padding: '14px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '10px',
        color: 'var(--text-3)',
        letterSpacing: '0.04em',
      }}>
        <span>JOBS AGENT — AI-POWERED JOB TRACKER</span>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
          style={{ color: 'var(--text-3)', transition: 'color 150ms' }}
          onMouseEnter={e => e.target.style.color = 'var(--accent)'}
          onMouseLeave={e => e.target.style.color = 'var(--text-3)'}
        >
          API DOCS →
        </a>
      </footer>
    </div>
  )
}
