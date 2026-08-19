import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { api } from '../api'

export function AccessHistoryPage() {
  const { patientId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const page = Number(searchParams.get('page') || '1')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setData(null)
    api
      .get(`/patients/${patientId}/access-history?page=${page}`)
      .then(setData)
      .catch((err) => setError(typeof err.detail === 'string' ? err.detail : 'Could not load access history.'))
  }, [patientId, page])

  if (error) {
    return (
      <>
        <h1 className="form-error">Access restricted</h1>
        <p>{error}</p>
      </>
    )
  }
  if (!data) return <p className="route-loading">Loading...</p>

  return (
    <>
      <div className="page-header">
        <h1>Access History</h1>
        <p>
          <Link to={`/patients/${patientId}`}>&larr; Back to summary</Link>
        </p>
      </div>

      <div className="card">
        {data.entries.length > 0 ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Action</th>
                  <th>Staff</th>
                  <th>Facility</th>
                  <th>Override reason</th>
                </tr>
              </thead>
              <tbody>
                {data.entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.timestamp}</td>
                    <td>
                      <span className="badge">{entry.action.replace(/_/g, ' ')}</span>
                    </td>
                    <td>{entry.user_name || '—'}</td>
                    <td>{entry.facility_name || '—'}</td>
                    <td>{entry.override_reason || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">No access history yet.</p>
        )}

        <div className="pagination">
          {page > 1 && (
            <button type="button" className="btn-sm" onClick={() => setSearchParams({ page: String(page - 1) })}>
              &laquo; Previous
            </button>
          )}
          <span className="muted">
            Page {data.page} of {data.total_pages}
          </span>
          {page < data.total_pages && (
            <button type="button" className="btn-sm" onClick={() => setSearchParams({ page: String(page + 1) })}>
              Next &raquo;
            </button>
          )}
        </div>
      </div>
    </>
  )
}
