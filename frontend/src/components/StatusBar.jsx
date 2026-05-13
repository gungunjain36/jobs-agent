import { useState } from 'react'
import { pauseAgent, resumeAgent } from '../hooks/useApi'

const s = {
  bar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    borderBottom: '1px solid var(--border)',
    background: 'var(--bg-1)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    gap: '16px',
    flexWrap: 'wrap',
  },
  left: { display: 'flex', alignItems: 'center', gap: '20px' },
  logo: {
    fontFamily: 'var(--font-display)',
    fontWeight: 800,
    fontSize: '15px',
    letterSpacing: '-0.02em',
    color: 'var(--accent)',
  },
  sep: { width: '1px', height: '16px', background: 'var(--border-bright)' },
  statusPill: {
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
    fontSize: '11px',
    color: 'var(--text-2)',
    letterSpacing: '0.04em',
  },
  dot: {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  stats: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
    fontSize: '11px',
    color: 'var(--text-2)',
  },
  stat: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '1px' },
  statVal: { color: 'var(--text)', fontWeight: 500, fontSize: '13px' },
  statLabel: { fontSize: '10px', color: 'var(--text-3)', letterSpacing: '0.06em', textTransform: 'uppercase' },
  right: { display: 'flex', alignItems: 'center', gap: '8px' },
  btn: {
    padding: '5px 12px',
    fontSize: '11px',
    borderRadius: 'var(--radius)',
    fontWeight: 500,
    letterSpacing: '0.03em',
    transition: 'all 150ms ease',
  },
  error: {
    fontSize: '11px',
    color: 'var(--red)',
    background: 'var(--red-dim)',
    padding: '4px 10px',
    borderRadius: 'var(--radius)',
  },
}

export default function StatusBar({ status, error, onRefresh }) {
  const [busy, setBusy] = useState(false)
  const running = status?.state === 'running'

  async function toggle() {
    setBusy(true)
    try {
      running ? await pauseAgent() : await resumeAgent()
      setTimeout(onRefresh, 400)
    } finally {
      setBusy(false)
    }
  }

  return (
    <header style={s.bar}>
      <div style={s.left}>
        <span style={s.logo}>JOBS AGENT</span>
        <div style={s.sep} />
        {error ? (
          <span style={s.error}>API offline</span>
        ) : (
          <div style={s.statusPill}>
            <span style={{
              ...s.dot,
              background: running ? 'var(--accent)' : 'var(--text-3)',
              animation: running ? 'pulse-dot 2s infinite' : 'none',
              boxShadow: running ? '0 0 6px var(--accent)' : 'none',
            }} />
            {status ? (running ? 'RUNNING' : 'PAUSED') : 'CONNECTING...'}
          </div>
        )}
        {status && (
          <div style={s.stats}>
            <div style={s.sep} />
            <div style={s.stat}>
              <span style={s.statVal}>{status.total_tracked}</span>
              <span style={s.statLabel}>tracked</span>
            </div>
            <div style={s.sep} />
            <div style={s.stat}>
              <span style={s.statVal}>{status.new_this_session}</span>
              <span style={s.statLabel}>this session</span>
            </div>
            <div style={s.sep} />
            <div style={s.stat}>
              <span style={s.statVal}>{status.poll_interval_minutes}m</span>
              <span style={s.statLabel}>interval</span>
            </div>
          </div>
        )}
      </div>
      <div style={s.right}>
        {status && (
          <button
            onClick={toggle}
            disabled={busy}
            style={{
              ...s.btn,
              background: running ? 'var(--red-dim)' : 'var(--accent-dim)',
              color: running ? 'var(--red)' : 'var(--accent)',
              opacity: busy ? 0.6 : 1,
            }}
          >
            {busy ? '...' : running ? 'PAUSE' : 'RESUME'}
          </button>
        )}
      </div>
    </header>
  )
}
