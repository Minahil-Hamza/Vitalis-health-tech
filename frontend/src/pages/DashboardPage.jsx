import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { api } from '../api'

export function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [cnic, setCnic] = useState('')
  const [error, setError] = useState('')

  async function handleSearch(event) {
    event.preventDefault()
    setError('')
    try {
      const patient = await api.get(`/patients/search?cnic=${encodeURIComponent(cnic)}`)
      navigate(`/patients/${patient.id}`)
    } catch {
      setError('No patient found with that CNIC.')
    }
  }

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <main>
      <h1>Welcome, {user.full_name}</h1>
      <p>Role: {user.role}</p>
      <p>Facility: {user.facility_name}</p>

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
        <button type="submit">Search</button>
        {error && <p className="form-error">{error}</p>}
      </form>
      <p>
        <Link to="/patients/new">+ Add new patient</Link>
      </p>
      {user.role === 'admin' && (
        <p>
          <Link to="/admin">Admin dashboard</Link>
        </p>
      )}

      <button type="button" onClick={handleLogout}>
        Log out
      </button>
    </main>
  )
}
