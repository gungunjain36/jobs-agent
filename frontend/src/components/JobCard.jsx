const s = {
  card: {
    background: 'var(--bg-1)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: '16px',
    transition: 'border-color 150ms ease, background 150ms ease',
    animation: 'fadeUp 250ms ease both',
    cursor: 'default',
  },
  left: { flex: 1, minWidth: 0 },
  title: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '14px',
    color: 'var(--text)',
    letterSpacing: '-0.01em',
    marginBottom: '4px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  company: {
    fontSize: '12px',
    color: 'var(--accent)',
    fontWeight: 500,
    marginBottom: '6px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  meta: {
    display: 'flex',
    gap: '14px',
    fontSize: '11px',
    color: 'var(--text-3)',
    flexWrap: 'wrap',
  },
  metaItem: { display: 'flex', alignItems: 'center', gap: '4px' },
  right: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '8px',
    flexShrink: 0,
  },
  date: {
    fontSize: '10px',
    color: 'var(--text-3)',
    letterSpacing: '0.04em',
    whiteSpace: 'nowrap',
  },
  applyBtn: {
    padding: '5px 12px',
    background: 'var(--accent-dim)',
    color: 'var(--accent)',
    borderRadius: 'var(--radius)',
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.04em',
    transition: 'all 150ms ease',
    whiteSpace: 'nowrap',
    border: '1px solid transparent',
  },
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return iso.slice(0, 10)
  }
}

export default function JobCard({ job, index }) {
  return (
    <div
      style={{ ...s.card, animationDelay: `${index * 40}ms` }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--border-bright)'
        e.currentTarget.style.background = 'var(--bg-2)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.background = 'var(--bg-1)'
      }}
    >
      <div style={s.left}>
        <div style={s.title}>{job.title || 'Untitled Role'}</div>
        <div style={s.company}>
          <span style={{ color: 'var(--border-bright)', fontSize: '10px' }}>▸</span>
          {job.company || 'Unknown Company'}
        </div>
        <div style={s.meta}>
          {job.seen_at && (
            <span style={s.metaItem}>
              <span style={{ color: 'var(--text-3)' }}>tracked</span>
              {formatDate(job.seen_at)}
            </span>
          )}
        </div>
      </div>
      <div style={s.right}>
        {job.seen_at && <span style={s.date}>{formatDate(job.seen_at)}</span>}
        <a
          href={job.apply_link || '#'}
          target="_blank"
          rel="noreferrer"
          style={s.applyBtn}
          onMouseEnter={e => {
            e.target.style.background = 'var(--accent)'
            e.target.style.color = '#000'
          }}
          onMouseLeave={e => {
            e.target.style.background = 'var(--accent-dim)'
            e.target.style.color = 'var(--accent)'
          }}
        >
          APPLY →
        </a>
      </div>
    </div>
  )
}
