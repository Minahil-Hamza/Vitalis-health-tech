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
      <main>
        <h1 className="form-error">Access restricted</h1>
        <p>{error}</p>
      </main>
    )
  }
  if (!records) return <main><p>Loading...</p></main>

  return (
    <main>
      <h1>Timeline</h1>
      <p>
        <Link to={`/patients/${patientId}`}>Back to summary</Link>
      </p>
      {records.length > 0 ? (
        <ul>
          {records.map((r) => (
            <li key={r.id}>
              <strong>{r.record_type}</strong> — {r.title}
              <br />
              <small>
                {r.facility_name} &middot; {r.author_name} &middot; {r.created_at}
              </small>
              <p>{r.details}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p>No records yet.</p>
      )}
    </main>
  )
}
