import { useState } from 'react'
import { triggerSearch } from '../hooks/useApi'

const s = {
  wrap: {
    display: 'flex',
    gap: '8px',
    marginBottom: '24px',
  },
  inputWrap: {
    flex: 1,
    position: 'relative',
  },
  prefix: {
    position: 'absolute',
    left: '14px',
    top: '50%',
    transform: 'translateY(-50%)',
    color: 'var(--accent)',
    fontSize: '13px',
    pointerEvents: 'none',
    userSelect: 'none',
  },
  input: {
    width: '100%',
    background: 'var(--bg-2)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '10px 14px 10px 30px',
    color: 'var(--text)',
    fontSize: '13px',
    transition: 'border-color 150ms ease',
  },
  btn: {
    padding: '10px 18px',
    background: 'var(--accent)',
    color: '#000',
    borderRadius: 'var(--radius)',
    fontSize: '12px',
    fontWeight: 700,
    letterSpacing: '0.05em',
    transition: 'all 150ms ease',
    whiteSpace: 'nowrap',
  },
  filterBtn: {
    padding: '10px 14px',
    background: 'var(--bg-2)',
    color: 'var(--text-2)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: '12px',
    transition: 'all 150ms ease',
  },
  toast: {
    fontSize: '11px',
    color: 'var(--accent)',
    marginTop: '6px',
    animation: 'fadeUp 200ms ease',
  },
}

export default function SearchPanel({ onSearch }) {
  const [query, setQuery] = useState('')
  const [toast, setToast] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleAgent() {
    if (!query.trim()) return
    setBusy(true)
    try {
      await triggerSearch(query.trim())
      setToast(`Search queued: "${query.trim()}"`)
      setTimeout(() => setToast(''), 3000)
    } finally {
      setBusy(false)
    }
  }

  function handleFilter(e) {
    e.preventDefault()
    onSearch(query.trim() || null)
  }

  return (
    <div>
      <div style={s.wrap}>
        <div style={s.inputWrap}>
          <span style={s.prefix}>&gt;</span>
          <input
            style={s.input}
            placeholder="Search jobs or trigger agent search..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleFilter(e)}
            onFocus={e => e.target.style.borderColor = 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
        </div>
        <button
          style={s.filterBtn}
          onClick={handleFilter}
        >
          FILTER
        </button>
        <button
          style={{ ...s.btn, opacity: busy ? 0.7 : 1 }}
          onClick={handleAgent}
          disabled={busy || !query.trim()}
          onMouseEnter={e => e.target.style.background = '#00ffb3'}
          onMouseLeave={e => e.target.style.background = 'var(--accent)'}
        >
          {busy ? 'QUEUING...' : 'RUN AGENT'}
        </button>
      </div>
      {toast && <div style={s.toast}>{toast}</div>}
    </div>
  )
}
