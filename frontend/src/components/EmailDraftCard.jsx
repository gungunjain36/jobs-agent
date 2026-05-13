import { useState } from 'react'

const s = {
  card: {
    background: 'var(--bg-1)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    transition: 'border-color 150ms ease',
    animation: 'fadeUp 250ms ease both',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 18px',
    cursor: 'pointer',
    userSelect: 'none',
  },
  checkbox: { accentColor: 'var(--accent)', width: '14px', height: '14px', cursor: 'pointer', flexShrink: 0 },
  headerText: { flex: 1, minWidth: 0 },
  company: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '13px',
    color: 'var(--text)',
    letterSpacing: '-0.01em',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  meta: {
    display: 'flex',
    gap: '10px',
    fontSize: '11px',
    color: 'var(--text-3)',
    marginTop: '2px',
    flexWrap: 'wrap',
  },
  to: { color: 'var(--accent)', fontFamily: 'var(--font-mono)' },
  expandBtn: {
    padding: '4px 10px',
    background: 'none',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: '10px',
    color: 'var(--text-3)',
    cursor: 'pointer',
    letterSpacing: '0.04em',
    fontFamily: 'var(--font-mono)',
    flexShrink: 0,
    transition: 'all 150ms ease',
  },
  body: {
    borderTop: '1px solid var(--border)',
    padding: '16px 18px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  label: {
    fontSize: '10px',
    color: 'var(--text-3)',
    letterSpacing: '0.06em',
    fontWeight: 600,
    marginBottom: '4px',
    fontFamily: 'var(--font-mono)',
  },
  input: {
    width: '100%',
    background: 'var(--bg-2)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '8px 12px',
    color: 'var(--text)',
    fontSize: '12px',
    fontFamily: 'var(--font-mono)',
    transition: 'border-color 150ms ease',
    outline: 'none',
  },
  textarea: {
    width: '100%',
    background: 'var(--bg-2)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '10px 12px',
    color: 'var(--text)',
    fontSize: '12px',
    fontFamily: 'var(--font-mono)',
    resize: 'vertical',
    minHeight: '180px',
    lineHeight: 1.6,
    transition: 'border-color 150ms ease',
    outline: 'none',
  },
}

export default function EmailDraftCard({ draft, index, selected, onToggle, onChange }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      style={{
        ...s.card,
        animationDelay: `${index * 40}ms`,
        borderColor: selected ? 'var(--border-bright)' : 'var(--border)',
      }}
    >
      <div
        style={s.header}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <input
          type="checkbox"
          style={s.checkbox}
          checked={selected}
          onChange={onToggle}
          onClick={e => e.stopPropagation()}
        />
        <div style={s.headerText} onClick={() => setExpanded(x => !x)}>
          <div style={s.company}>
            {draft.company_name}
            <span style={{ color: 'var(--text-3)', fontWeight: 400, fontFamily: 'var(--font-mono)', fontSize: '11px', marginLeft: '8px' }}>
              {draft.role}
            </span>
          </div>
          <div style={s.meta}>
            <span style={s.to}>{draft.to_email}</span>
            {draft.to_name && <span>{draft.to_name}</span>}
            <span style={{ color: 'var(--text-3)' }}>
              {draft.subject.length > 50 ? draft.subject.slice(0, 50) + '...' : draft.subject}
            </span>
          </div>
        </div>
        <button
          style={s.expandBtn}
          onClick={() => setExpanded(x => !x)}
          onMouseEnter={e => {
            e.target.style.borderColor = 'var(--accent)'
            e.target.style.color = 'var(--accent)'
          }}
          onMouseLeave={e => {
            e.target.style.borderColor = 'var(--border)'
            e.target.style.color = 'var(--text-3)'
          }}
        >
          {expanded ? 'COLLAPSE' : 'EDIT'}
        </button>
      </div>

      {expanded && (
        <div style={s.body}>
          <div>
            <div style={s.label}>TO</div>
            <input
              style={s.input}
              value={draft.to_email}
              onChange={e => onChange('to_email', e.target.value)}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
          <div>
            <div style={s.label}>SUBJECT</div>
            <input
              style={s.input}
              value={draft.subject}
              onChange={e => onChange('subject', e.target.value)}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
          <div>
            <div style={s.label}>BODY</div>
            <textarea
              style={s.textarea}
              value={draft.body}
              onChange={e => onChange('body', e.target.value)}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
        </div>
      )}
    </div>
  )
}
