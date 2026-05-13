import { useState, useRef, useEffect } from 'react'
import EmailDraftCard from './EmailDraftCard'

const BASE = 'http://localhost:8000'

const s = {
  root: { flex: 1, maxWidth: '860px', width: '100%', margin: '0 auto', padding: '32px 24px' },
  section: {
    background: 'var(--bg-1)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '20px 24px',
    marginBottom: '12px',
  },
  sectionTitle: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '13px',
    color: 'var(--text)',
    letterSpacing: '-0.01em',
    marginBottom: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  badge: {
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '99px',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    letterSpacing: '0.04em',
  },
  uploadRow: { display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' },
  uploadBtn: {
    padding: '7px 16px',
    background: 'var(--bg-3)',
    border: '1px solid var(--border-bright)',
    borderRadius: 'var(--radius)',
    color: 'var(--text-2)',
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.04em',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
  fileName: { fontSize: '11px', color: 'var(--accent)', fontFamily: 'var(--font-mono)' },
  hint: { fontSize: '11px', color: 'var(--text-3)', marginTop: '8px', lineHeight: 1.6 },
  generateBtn: {
    width: '100%',
    padding: '12px',
    background: 'var(--accent)',
    color: '#000',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontSize: '12px',
    fontWeight: 700,
    letterSpacing: '0.06em',
    cursor: 'pointer',
    transition: 'opacity 150ms ease',
    marginBottom: '24px',
    fontFamily: 'var(--font-mono)',
  },
  divider: { height: '1px', background: 'var(--border)', margin: '24px 0' },
  draftHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
    flexWrap: 'wrap',
    gap: '10px',
  },
  draftTitle: {
    fontFamily: 'var(--font-display)',
    fontWeight: 800,
    fontSize: '18px',
    letterSpacing: '-0.03em',
    color: 'var(--text)',
  },
  batchRow: { display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' },
  selectAllBtn: {
    padding: '5px 12px',
    background: 'none',
    border: '1px solid var(--border-bright)',
    borderRadius: 'var(--radius)',
    color: 'var(--text-2)',
    fontSize: '10px',
    letterSpacing: '0.04em',
    cursor: 'pointer',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    transition: 'all 150ms ease',
  },
  sendBtn: {
    padding: '8px 20px',
    background: 'var(--accent)',
    color: '#000',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.06em',
    cursor: 'pointer',
    fontFamily: 'var(--font-mono)',
    transition: 'opacity 150ms ease',
  },
  resultsSection: {
    marginTop: '24px',
    background: 'var(--bg-1)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '20px 24px',
  },
  resultRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid var(--border)',
    fontSize: '12px',
  },
  spinner: {
    display: 'inline-block',
    width: '12px',
    height: '12px',
    border: '2px solid var(--border-bright)',
    borderTopColor: 'var(--accent)',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
  },
}

function StatusBadge({ ok }) {
  return (
    <span style={{
      ...s.badge,
      background: ok ? 'rgba(0,229,160,0.12)' : 'rgba(255,77,106,0.12)',
      color: ok ? 'var(--accent)' : 'var(--red)',
    }}>
      {ok ? 'READY' : 'NEEDED'}
    </span>
  )
}

export default function ColdMailer() {
  const [resumeFile, setResumeFile] = useState(null)
  const [contactsFile, setContactsFile] = useState(null)
  const [resumeCached, setResumeCached] = useState(false)
  const [contacts, setContacts] = useState([])
  const [drafts, setDrafts] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [phase, setPhase] = useState('setup')
  const [generating, setGenerating] = useState(false)
  const [sending, setSending] = useState(false)
  const [sendResults, setSendResults] = useState([])
  const [attachResume, setAttachResume] = useState(true)
  const [error, setError] = useState(null)
  const [resumeLoading, setResumeLoading] = useState(false)
  const [contactsLoading, setContactsLoading] = useState(false)
  const resumeRef = useRef()
  const contactsRef = useRef()

  useEffect(() => {
    fetch(`${BASE}/mailer/resume-context`)
      .then(r => r.json())
      .then(d => setResumeCached(d.cached))
      .catch(() => {})
  }, [])

  async function handleResumeUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setResumeFile(file)
    setResumeLoading(true)
    setError(null)

    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch(`${BASE}/mailer/parse-resume`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail)
      setResumeCached(true)
    } catch (e) {
      setError(`Resume parse failed: ${e.message}`)
    } finally {
      setResumeLoading(false)
    }
  }

  async function handleContactsUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setContactsFile(file)
    setContactsLoading(true)
    setError(null)

    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch(`${BASE}/mailer/parse-contacts`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setContacts(data.contacts)
    } catch (e) {
      setError(`Contacts parse failed: ${e.message}`)
    } finally {
      setContactsLoading(false)
    }
  }

  async function handleGenerate() {
    if (!resumeCached || contacts.length === 0) return
    setGenerating(true)
    setError(null)
    setDrafts([])
    setSelected(new Set())

    try {
      const res = await fetch(`${BASE}/mailer/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contacts),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setDrafts(data.drafts)
      setSelected(new Set(data.drafts.map(d => d.id)))
      setPhase('review')
    } catch (e) {
      setError(`Generation failed: ${e.message}`)
    } finally {
      setGenerating(false)
    }
  }

  function updateDraft(id, field, value) {
    setDrafts(prev => prev.map(d => d.id === id ? { ...d, [field]: value } : d))
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === drafts.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(drafts.map(d => d.id)))
    }
  }

  async function handleSend() {
    const toSend = drafts.filter(d => selected.has(d.id))
    if (toSend.length === 0) return
    setSending(true)
    setError(null)

    try {
      const res = await fetch(`${BASE}/mailer/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drafts: toSend, attach_resume: attachResume }),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setSendResults(data.results)
      setPhase('done')
    } catch (e) {
      setError(`Send failed: ${e.message}`)
    } finally {
      setSending(false)
    }
  }

  const canGenerate = resumeCached && contacts.length > 0 && !generating

  return (
    <main style={s.root}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Resume section */}
      <div style={s.section}>
        <div style={s.sectionTitle}>
          Resume
          {resumeLoading
            ? <span style={s.badge}>...</span>
            : <StatusBadge ok={resumeCached} />}
        </div>
        <div style={s.uploadRow}>
          <input
            ref={resumeRef}
            type="file"
            accept=".pdf"
            style={{ display: 'none' }}
            onChange={handleResumeUpload}
          />
          <button
            style={s.uploadBtn}
            onClick={() => resumeRef.current.click()}
            onMouseEnter={e => {
              e.target.style.borderColor = 'var(--accent)'
              e.target.style.color = 'var(--accent)'
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = 'var(--border-bright)'
              e.target.style.color = 'var(--text-2)'
            }}
          >
            {resumeCached ? 'RE-UPLOAD PDF' : 'UPLOAD PDF'}
          </button>
          {resumeFile && <span style={s.fileName}>{resumeFile.name}</span>}
          {resumeLoading && <span style={s.spinner} />}
        </div>
        {resumeCached && (
          <div style={{ ...s.hint, color: 'var(--accent)', marginTop: '8px' }}>
            Resume context cached. No need to re-upload unless the resume changes.
          </div>
        )}
        <div style={s.hint}>
          PDF is parsed once and key info is cached locally in resume_context.yml.
          Attaching the original PDF to emails is optional.
        </div>
      </div>

      {/* Contacts section */}
      <div style={s.section}>
        <div style={s.sectionTitle}>
          Contacts
          {contactsLoading
            ? <span style={s.badge}>...</span>
            : <StatusBadge ok={contacts.length > 0} />}
          {contacts.length > 0 && (
            <span style={{ ...s.badge, background: 'var(--accent-dim)', color: 'var(--accent)' }}>
              {contacts.length} loaded
            </span>
          )}
        </div>
        <div style={s.uploadRow}>
          <input
            ref={contactsRef}
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={handleContactsUpload}
          />
          <button
            style={s.uploadBtn}
            onClick={() => contactsRef.current.click()}
            onMouseEnter={e => {
              e.target.style.borderColor = 'var(--accent)'
              e.target.style.color = 'var(--accent)'
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = 'var(--border-bright)'
              e.target.style.color = 'var(--text-2)'
            }}
          >
            {contacts.length > 0 ? 'RE-UPLOAD EXCEL' : 'UPLOAD EXCEL'}
          </button>
          {contactsFile && <span style={s.fileName}>{contactsFile.name}</span>}
          {contactsLoading && <span style={s.spinner} />}
        </div>
        <div style={s.hint}>
          Required columns: <span style={{ color: 'var(--text-2)' }}>Company Name, Role, Manager Email</span>
          {'  '}Optional: Manager Name, Company Description, Job URL
        </div>
      </div>

      {error && (
        <div style={{
          padding: '10px 16px',
          background: 'var(--red-dim)',
          border: '1px solid var(--red)',
          borderRadius: 'var(--radius)',
          color: 'var(--red)',
          fontSize: '12px',
          marginBottom: '12px',
          fontFamily: 'var(--font-mono)',
        }}>
          {error}
        </div>
      )}

      {/* Attach resume toggle */}
      {phase !== 'done' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '11px',
            color: 'var(--text-2)',
            cursor: 'pointer',
            userSelect: 'none',
          }}>
            <input
              type="checkbox"
              checked={attachResume}
              onChange={e => setAttachResume(e.target.checked)}
              style={{ accentColor: 'var(--accent)', width: '13px', height: '13px' }}
            />
            ATTACH RESUME PDF TO EMAILS
          </label>
        </div>
      )}

      {/* Generate button */}
      {phase !== 'done' && (
        <button
          style={{ ...s.generateBtn, opacity: canGenerate ? 1 : 0.4, cursor: canGenerate ? 'pointer' : 'not-allowed' }}
          disabled={!canGenerate}
          onClick={handleGenerate}
        >
          {generating
            ? 'GENERATING EMAILS...'
            : contacts.length > 0
              ? `GENERATE ${contacts.length} EMAIL${contacts.length !== 1 ? 'S' : ''}`
              : 'GENERATE EMAILS'}
        </button>
      )}

      {/* Drafts review */}
      {drafts.length > 0 && phase === 'review' && (
        <>
          <div style={s.divider} />
          <div style={s.draftHeader}>
            <span style={s.draftTitle}>Review Drafts</span>
            <div style={s.batchRow}>
              <span style={{ fontSize: '11px', color: 'var(--text-3)' }}>
                {selected.size} of {drafts.length} selected
              </span>
              <button
                style={s.selectAllBtn}
                onClick={toggleAll}
                onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
                onMouseLeave={e => e.target.style.borderColor = 'var(--border-bright)'}
              >
                {selected.size === drafts.length ? 'DESELECT ALL' : 'SELECT ALL'}
              </button>
              <button
                style={{
                  ...s.sendBtn,
                  opacity: selected.size > 0 && !sending ? 1 : 0.4,
                  cursor: selected.size > 0 && !sending ? 'pointer' : 'not-allowed',
                }}
                disabled={selected.size === 0 || sending}
                onClick={handleSend}
              >
                {sending ? 'SENDING...' : `SEND ${selected.size} EMAIL${selected.size !== 1 ? 'S' : ''}`}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {drafts.map((draft, i) => (
              <EmailDraftCard
                key={draft.id}
                draft={draft}
                index={i}
                selected={selected.has(draft.id)}
                onToggle={() => toggleSelect(draft.id)}
                onChange={(field, value) => updateDraft(draft.id, field, value)}
              />
            ))}
          </div>
        </>
      )}

      {/* Send results */}
      {phase === 'done' && sendResults.length > 0 && (
        <div style={s.resultsSection}>
          <div style={{ ...s.sectionTitle, marginBottom: '16px' }}>
            Send Results
          </div>
          {sendResults.map(r => (
            <div key={r.id} style={s.resultRow}>
              <span style={{ color: 'var(--text-2)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                {r.to}
              </span>
              <span style={{
                color: r.status === 'sent' ? 'var(--accent)' : 'var(--red)',
                fontWeight: 600,
                letterSpacing: '0.04em',
                fontSize: '11px',
              }}>
                {r.status === 'sent' ? 'SENT' : `FAILED: ${r.error}`}
              </span>
            </div>
          ))}
          <button
            style={{ ...s.selectAllBtn, marginTop: '16px' }}
            onClick={() => {
              setPhase('setup')
              setDrafts([])
              setContacts([])
              setContactsFile(null)
              setSendResults([])
              setSelected(new Set())
            }}
          >
            START OVER
          </button>
        </div>
      )}
    </main>
  )
}
