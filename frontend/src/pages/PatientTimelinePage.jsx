import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'

export function PatientTimelinePage() {
  const { patientId } = useParams()
  const [records, setRecords] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get(`/patients/${patientId}/timeline`)
      .then(setRecords)
      .catch((err) => setError(typeof err.detail === 'string' ? err.detail : 'Could not load the timeline.'))
  }, [patientId])

  if (error) {
    return (
      <>
        <h1 className="form-error">Access restricted</h1>
        <p>{error}</p>
      </>
    )
  }
  if (!records) return <p className="route-loading">Loading...</p>

  return (
    <>
      <div className="page-header">
        <h1>Timeline</h1>
        <p>
          <Link to={`/patients/${patientId}`}>&larr; Back to summary</Link>
        </p>
      </div>

      {records.length > 0 ? (
        <ul className="entry-list entry-list-stacked">
          {records.map((r) => (
            <li key={r.id}>
              <div>
                <span className="badge">{r.record_type.replace('_', ' ')}</span>{' '}
                <strong>{r.title}</strong>
                {r.drug_name && <span className="badge badge-role">{r.drug_name}</span>}
                <span className="entry-meta">
                  {r.facility_name} &middot; {r.author_name} &middot; {r.created_at}
                </span>
              </div>
              <p className="entry-details">{r.details}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">No records yet.</p>
      )}
    </>
  )
}
