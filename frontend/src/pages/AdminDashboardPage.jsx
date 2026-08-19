import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

const ROLES = ['doctor', 'pharmacist', 'nurse', 'receptionist', 'admin']

export function AdminDashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const dashboard = await api.get('/admin')
      setData(dashboard)
    } catch (err) {
      setError(typeof err.detail === 'string' ? err.detail : 'Could not load the admin dashboard.')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleDeactivate(userId) {
    try {
      await api.post(`/admin/users/${userId}/deactivate`)
      load()
    } catch (err) {
      alert(typeof err.detail === 'string' ? err.detail : 'Could not deactivate that user.')
    }
  }

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
        <h1>Admin dashboard</h1>
        <p>
          <Link to="/">&larr; Back to dashboard</Link>
        </p>
      </div>

      <div className="grid grid-2" style={{ marginBottom: '1.25rem' }}>
        <div className="stat-tile">
          <span className="stat-value">{data.patients_created}</span>
          <span className="stat-label">Patients created</span>
        </div>
        <div className="stat-tile">
          <span className="stat-value">{data.records_this_month}</span>
          <span className="stat-label">Records this month</span>
        </div>
      </div>

      <div className="card">
        <h2>Staff</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.staff.map((member) => (
                <tr key={member.id}>
                  <td>{member.full_name}</td>
                  <td>{member.email}</td>
                  <td>
                    <span className="badge badge-role">{member.role}</span>
                  </td>
                  <td>
                    <span className={`badge ${member.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {member.is_active ? 'Active' : 'Deactivated'}
                    </span>
                  </td>
                  <td>
                    {member.is_active && member.id !== user.id && (
                      <button type="button" className="btn-sm" onClick={() => handleDeactivate(member.id)}>
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <AddStaffForm onAdded={load} />
      </div>
    </>
  )
}

function AddStaffForm({ onAdded }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'doctor' })
  const [error, setError] = useState('')

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    try {
      await api.post('/admin/users', form)
      setForm({ full_name: '', email: '', password: '', role: 'doctor' })
      onAdded()
    } catch (err) {
      setError(typeof err.detail === 'string' ? err.detail : 'Please check the form.')
    }
  }

  return (
    <>
      <h2>Add staff</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="full_name">Full name</label>
        <input id="full_name" value={form.full_name} onChange={(e) => update('full_name', e.target.value)} required />
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={form.email}
          onChange={(e) => update('email', e.target.value)}
          required
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={form.password}
          onChange={(e) => update('password', e.target.value)}
          required
        />
        <label htmlFor="role">Role</label>
        <select id="role" value={form.role} onChange={(e) => update('role', e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r[0].toUpperCase() + r.slice(1)}
            </option>
          ))}
        </select>
        <button type="submit">Add staff</button>
        {error && <p className="form-error">{error}</p>}
      </form>
    </>
  )
}
