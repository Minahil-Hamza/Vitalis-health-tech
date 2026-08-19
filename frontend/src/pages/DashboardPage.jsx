import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { api } from '../api'

export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [cnic, setCnic] = useState('')
  const [error, setError] = useState('')
  const [searching, setSearching] = useState(false)

  async function handleSearch(event) {
    event.preventDefault()
    setError('')
    setSearching(true)
    try {
      const patient = await api.get(`/patients/search?cnic=${encodeURIComponent(cnic)}`)
      navigate(`/patients/${patient.id}`)
    } catch {
      setError('No patient found with that CNIC.')
    } finally {
      setSearching(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Welcome, {user.full_name}</h1>
        <p>{user.facility_name}</p>
      </div>

      <div className="card">
        <h2>Find a patient</h2>
        <form onSubmit={handleSearch}>
          <label htmlFor="search-cnic">CNIC</label>
          <input
            id="search-cnic"
            value={cnic}
            onChange={(e) => setCnic(e.target.value)}
            placeholder="12345-1234567-1"
            required
          />
          <button type="submit" disabled={searching}>
            {searching ? 'Searching…' : 'Search'}
          </button>
          {error && <p className="form-error">{error}</p>}
        </form>
      </div>

      <div className="grid grid-2">
        <Link to="/patients/new" className="card card-link">
          <h2>+ Add new patient</h2>
          <p className="muted">Register a patient with a validated CNIC.</p>
        </Link>
        {user.role === 'admin' && (
          <Link to="/admin" className="card card-link">
            <h2>Admin dashboard</h2>
            <p className="muted">Manage staff and view facility activity.</p>
          </Link>
        )}
      </div>
    </>
  )
}
