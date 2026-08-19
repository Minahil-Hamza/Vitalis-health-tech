import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, ApiError } from '../api'
import { Body3D } from '../components/Body3D'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { SafetyBlockedBanner, SafetyWarningBanner, MIN_OVERRIDE_LENGTH } from '../components/SafetyBanners'

const RECORD_TYPES = ['visit', 'prescription', 'lab_report', 'admission', 'discharge']
const SEVERITIES = ['mild', 'moderate', 'severe']
const BODY_REGIONS = [
  ['', 'Not localized / systemic'],
  ['head', 'Head'],
  ['chest', 'Chest'],
  ['abdomen', 'Abdomen'],
  ['pelvis', 'Pelvis'],
  ['left_arm', 'Left arm'],
  ['right_arm', 'Right arm'],
  ['left_leg', 'Left leg'],
  ['right_leg', 'Right leg'],
  ['back', 'Back'],
  ['general', 'General'],
]

export function PatientSummaryPage() {
  const { patientId } = useParams()
  const [patient, setPatient] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const data = await api.get(`/patients/${patientId}`)
      setPatient(data)
      setError('')
    } catch (err) {
      setError(typeof err.detail === 'string' ? err.detail : 'Could not load this patient.')
    }
  }, [patientId])

  useEffect(() => {
    load()
  }, [load])

  if (error) {
    return (
      <>
        <h1 className="form-error">Access restricted</h1>
        <p>{error}</p>
      </>
    )
  }
  if (!patient) return <p className="route-loading">Loading...</p>

  return (
    <>
      {patient.allergies.length > 0 && (
        <div className="allergy-banner">
          <div>
            <strong>Allergy warning</strong>
            <ul>
              {patient.allergies.map((a) => (
                <li key={a.id}>
                  {a.substance} ({a.severity})
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h1 style={{ marginBottom: 0 }}>{patient.full_name}</h1>
          {patient.is_creating_facility && (
            <Link to={`/patients/${patientId}/access-history`} className="btn-sm-link">
              View access history
            </Link>
          )}
        </div>
        <p className="muted">
          CNIC {patient.cnic} &middot; {patient.gender} &middot; DOB {patient.date_of_birth}
          {patient.blood_group && <> &middot; Blood group {patient.blood_group}</>}
        </p>
      </div>

      <div className="card">
        <h2>Chronic conditions</h2>
        <ErrorBoundary
          fallback={<p className="body3d-empty">The 3D view couldn't be displayed — see the list below.</p>}
        >
          <Body3D conditions={patient.conditions} />
        </ErrorBoundary>
        {patient.conditions.length > 0 ? (
          <ul className="entry-list">
            {patient.conditions.map((c) => (
              <li key={c.id}>
                <span>
                  {c.name}
                  {c.diagnosed_date ? <span className="entry-meta">diagnosed {c.diagnosed_date}</span> : null}
                </span>
                {c.body_region && <span className="badge">{c.body_region.replace('_', ' ')}</span>}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No chronic conditions recorded.</p>
        )}
        <ConditionForm patientId={patientId} onAdded={load} />
      </div>

      <div className="card">
        <h2>Allergies</h2>
        {patient.allergies.length === 0 && <p className="muted">No known allergies.</p>}
        <AllergyForm patientId={patientId} onAdded={load} />
      </div>

      <div className="card">
        <h2>Medications</h2>
        <h3>Current</h3>
        {patient.active_medications.length > 0 ? (
          <ul className="entry-list">
            {patient.active_medications.map((m) => (
              <li key={m.id}>
                <span>
                  {m.drug_name} {m.dose} <span className="entry-meta">{m.frequency}</span>
                </span>
                <StopMedicationButton patientId={patientId} medicationId={m.id} onStopped={load} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No current medications.</p>
        )}

        {patient.past_medications.length > 0 && (
          <>
            <h3>Past</h3>
            <ul className="entry-list">
              {patient.past_medications.map((m) => (
                <li key={m.id}>
                  <span>
                    {m.drug_name} {m.dose} <span className="entry-meta">{m.frequency}</span>
                  </span>
                  <span className="badge badge-inactive">stopped {m.stopped_at}</span>
                </li>
              ))}
            </ul>
          </>
        )}
        <MedicationForm patientId={patientId} onAdded={load} />
      </div>

      <div className="card">
        <div className="card-header">
          <h2 style={{ marginBottom: 0 }}>Recent records</h2>
          <Link to={`/patients/${patientId}/timeline`}>View full timeline</Link>
        </div>
        {patient.records.length > 0 ? (
          <ul className="entry-list entry-list-stacked">
            {patient.records.map((r) => (
              <li key={r.id}>
                <div>
                  <span className="badge">{r.record_type.replace('_', ' ')}</span> <strong>{r.title}</strong>
                  {r.drug_name && <span className="badge badge-role">{r.drug_name}</span>}
                  <span className="entry-meta">
                    {r.facility_name} &middot; {r.author_name} &middot; {r.created_at}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No records yet.</p>
        )}
        <RecordForm patientId={patientId} onAdded={load} />
      </div>
    </>
  )
}

function AllergyForm({ patientId, onAdded }) {
  const [substance, setSubstance] = useState('')
  const [severity, setSeverity] = useState('mild')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    try {
      await api.post(`/patients/${patientId}/allergies`, { substance, severity })
      setSubstance('')
      onAdded()
    } catch (err) {
      setError(typeof err.detail === 'string' ? err.detail : 'Please check the form.')
    }
  }

  return (
    <details className="add-form">
      <summary>+ Add allergy</summary>
      <form onSubmit={handleSubmit}>
        <label htmlFor="substance">Substance</label>
        <input id="substance" value={substance} onChange={(e) => setSubstance(e.target.value)} required />
        <label htmlFor="severity">Severity</label>
        <select id="severity" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s[0].toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <button type="submit">Add allergy</button>
        {error && <p className="form-error">{error}</p>}
      </form>
    </details>
  )
}

function ConditionForm({ patientId, onAdded }) {
  const [form, setForm] = useState({ name: '', diagnosed_date: '', body_region: '', notes: '' })
  const [error, setError] = useState('')

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    try {
      await api.post(`/patients/${patientId}/conditions`, {
        name: form.name,
        diagnosed_date: form.diagnosed_date || null,
        body_region: form.body_region || null,
        notes: form.notes || null,
      })
      setForm({ name: '', diagnosed_date: '', body_region: '', notes: '' })
      onAdded()
    } catch (err) {
      setError(typeof err.detail === 'string' ? err.detail : 'Please check the form.')
    }
  }

  return (
    <details className="add-form">
      <summary>+ Add condition</summary>
      <form onSubmit={handleSubmit}>
        <label htmlFor="condition_name">Name</label>
        <input id="condition_name" value={form.name} onChange={(e) => update('name', e.target.value)} required />
        <label htmlFor="diagnosed_date">Diagnosed</label>
        <input
          id="diagnosed_date"
          type="date"
          value={form.diagnosed_date}
          onChange={(e) => update('diagnosed_date', e.target.value)}
        />
        <label htmlFor="body_region">Body region</label>
        <select id="body_region" value={form.body_region} onChange={(e) => update('body_region', e.target.value)}>
          {BODY_REGIONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <label htmlFor="condition_notes">Notes</label>
        <textarea id="condition_notes" value={form.notes} onChange={(e) => update('notes', e.target.value)} />
        <button type="submit">Add condition</button>
        {error && <p className="form-error">{error}</p>}
      </form>
    </details>
  )
}

function StopMedicationButton({ patientId, medicationId, onStopped }) {
  async function handleClick() {
    try {
      await api.post(`/patients/${patientId}/medications/${medicationId}/stop`)
      onStopped()
    } catch {
      alert('Could not stop medication.')
    }
  }
  return (
    <button type="button" className="btn-sm" onClick={handleClick}>
      Stop
    </button>
  )
}

function MedicationForm({ patientId, onAdded }) {
  const emptyForm = { drug_name: '', brand_name: '', dose: '', frequency: '', started_at: '' }
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [blocked, setBlocked] = useState(null)
  const [overrideReason, setOverrideReason] = useState('')
  const [warnings, setWarnings] = useState([])

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function buildPayload(reason) {
    const payload = { ...form, brand_name: form.brand_name || null }
    if (reason) payload.override_reason = reason
    return payload
  }

  function handleSuccess(result) {
    setForm(emptyForm)
    setBlocked(null)
    setOverrideReason('')
    setError('')
    setWarnings(result && result.warnings ? result.warnings : [])
    onAdded()
  }

  async function trySave(payload) {
    try {
      const result = await api.post(`/patients/${patientId}/medications`, payload)
      handleSuccess(result)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setBlocked(err.detail)
      } else {
        setError(typeof err.detail === 'string' ? err.detail : 'Please check the form.')
      }
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setWarnings([])
    await trySave(buildPayload())
  }

  async function handleConfirmOverride() {
    if (overrideReason.trim().length < MIN_OVERRIDE_LENGTH) {
      setError(`Override reason must be at least ${MIN_OVERRIDE_LENGTH} characters.`)
      return
    }
    setError('')
    await trySave(buildPayload(overrideReason.trim()))
  }

  function handleCancelOverride() {
    setBlocked(null)
    setOverrideReason('')
    setError('')
  }

  return (
    <details className="add-form" open={!!blocked || undefined}>
      <summary>+ Add medication</summary>
      <SafetyWarningBanner warnings={warnings} />
      {blocked ? (
        <SafetyBlockedBanner
          detail={blocked}
          drugName={form.drug_name}
          overrideReason={overrideReason}
          onChangeReason={setOverrideReason}
          onConfirm={handleConfirmOverride}
          onCancel={handleCancelOverride}
          error={error}
        />
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="drug_name">Drug name</label>
          <input
            id="drug_name"
            value={form.drug_name}
            onChange={(e) => update('drug_name', e.target.value)}
            required
          />
          <label htmlFor="brand_name">Brand name</label>
          <input id="brand_name" value={form.brand_name} onChange={(e) => update('brand_name', e.target.value)} />
          <label htmlFor="dose">Dose</label>
          <input id="dose" value={form.dose} onChange={(e) => update('dose', e.target.value)} required />
          <label htmlFor="frequency">Frequency</label>
          <input
            id="frequency"
            value={form.frequency}
            onChange={(e) => update('frequency', e.target.value)}
            required
          />
          <label htmlFor="started_at">Started</label>
          <input
            id="started_at"
            type="date"
            value={form.started_at}
            onChange={(e) => update('started_at', e.target.value)}
            required
          />
          <button type="submit">Add medication</button>
          {error && <p className="form-error">{error}</p>}
        </form>
      )}
    </details>
  )
}

function RecordForm({ patientId, onAdded }) {
  const emptyForm = { record_type: 'visit', title: '', details: '', drug_name: '' }
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [blocked, setBlocked] = useState(null)
  const [overrideReason, setOverrideReason] = useState('')
  const [warnings, setWarnings] = useState([])

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function buildPayload(reason) {
    const payload = { record_type: form.record_type, title: form.title, details: form.details }
    if (form.record_type === 'prescription') payload.drug_name = form.drug_name
    if (reason) payload.override_reason = reason
    return payload
  }

  function handleSuccess(result) {
    setForm(emptyForm)
    setBlocked(null)
    setOverrideReason('')
    setError('')
    setWarnings(result && result.warnings ? result.warnings : [])
    onAdded()
  }

  async function trySave(payload) {
    try {
      const result = await api.post(`/patients/${patientId}/records`, payload)
      handleSuccess(result)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setBlocked(err.detail)
      } else {
        setError(typeof err.detail === 'string' ? err.detail : 'Please check the form.')
      }
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setWarnings([])
    await trySave(buildPayload())
  }

  async function handleConfirmOverride() {
    if (overrideReason.trim().length < MIN_OVERRIDE_LENGTH) {
      setError(`Override reason must be at least ${MIN_OVERRIDE_LENGTH} characters.`)
      return
    }
    setError('')
    await trySave(buildPayload(overrideReason.trim()))
  }

  function handleCancelOverride() {
    setBlocked(null)
    setOverrideReason('')
    setError('')
  }

  return (
    <details className="add-form" open={!!blocked || undefined}>
      <summary>+ Add record</summary>
      <SafetyWarningBanner warnings={warnings} />
      {blocked ? (
        <SafetyBlockedBanner
          detail={blocked}
          drugName={form.drug_name}
          overrideReason={overrideReason}
          onChangeReason={setOverrideReason}
          onConfirm={handleConfirmOverride}
          onCancel={handleCancelOverride}
          error={error}
        />
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="record_type">Type</label>
          <select id="record_type" value={form.record_type} onChange={(e) => update('record_type', e.target.value)}>
            {RECORD_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace('_', ' ')}
              </option>
            ))}
          </select>
          {form.record_type === 'prescription' && (
            <>
              <label htmlFor="record_drug_name">Drug name</label>
              <input
                id="record_drug_name"
                value={form.drug_name}
                onChange={(e) => update('drug_name', e.target.value)}
                required
              />
            </>
          )}
          <label htmlFor="title">Title</label>
          <input id="title" value={form.title} onChange={(e) => update('title', e.target.value)} required />
          <label htmlFor="details">Details</label>
          <textarea id="details" value={form.details} onChange={(e) => update('details', e.target.value)} required />
          <button type="submit">Add record</button>
          {error && <p className="form-error">{error}</p>}
        </form>
      )}
    </details>
  )
}
