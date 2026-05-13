const s = {
  wrap: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
    marginBottom: '24px',
  },
  label: {
    fontSize: '10px',
    color: 'var(--text-3)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    alignSelf: 'center',
    marginRight: '4px',
    whiteSpace: 'nowrap',
  },
  chip: {
    padding: '3px 10px',
    background: 'var(--bg-2)',
    border: '1px solid var(--border)',
    borderRadius: '20px',
    fontSize: '11px',
    color: 'var(--text-2)',
    letterSpacing: '0.02em',
  },
}

export default function KeywordChips({ keywords = [], location }) {
  if (!keywords.length) return null
  return (
    <div style={s.wrap}>
      <span style={s.label}>watching</span>
      {keywords.map(k => (
        <span key={k} style={s.chip}>{k}</span>
      ))}
      {location && (
        <>
          <span style={{ ...s.label, marginLeft: '8px' }}>in</span>
          <span style={{ ...s.chip, borderColor: 'var(--accent)', color: 'var(--accent)', background: 'var(--accent-dim)' }}>
            {location}
          </span>
        </>
      )}
    </div>
  )
}
