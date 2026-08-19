import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const GENDERS = ['male', 'female', 'other']

export function PatientNewPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    cnic: '',
    full_name: '',
    date_of_birth: '',
    gender: 'male',
    blood_group: '',
    phone: '',
    address: '',
    consent_sharing: true,
  })
  const [error, setError] = useState('')

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    try {
      const payload = {
        ...form,
        blood_group: form.blood_group || null,
        phone: form.phone || null,
        address: form.address || null,
      }
      const patient = await api.post('/patients', payload)
      navigate(`/patients/${patient.id}`)
    } catch (err) {
      setError(
        typeof err.detail === 'string'
          ? err.detail
          : 'Please check the form (CNIC must look like 12345-1234567-1).',
      )
    }
  }

  return (
    <main>
      <h1>Add Patient</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="cnic">CNIC</label>
        <input
          id="cnic"
          value={form.cnic}
          onChange={(e) => update('cnic', e.target.value)}
          placeholder="12345-1234567-1"
          required
        />

        <label htmlFor="full_name">Full name</label>
        <input id="full_name" value={form.full_name} onChange={(e) => update('full_name', e.target.value)} required />

        <label htmlFor="date_of_birth">Date of birth</label>
        <input
          id="date_of_birth"
          type="date"
          value={form.date_of_birth}
          onChange={(e) => update('date_of_birth', e.target.value)}
          required
        />

        <label htmlFor="gender">Gender</label>
        <select id="gender" value={form.gender} onChange={(e) => update('gender', e.target.value)} required>
          {GENDERS.map((g) => (
            <option key={g} value={g}>
              {g[0].toUpperCase() + g.slice(1)}
            </option>
          ))}
        </select>

        <label htmlFor="blood_group">Blood group</label>
        <input
          id="blood_group"
          value={form.blood_group}
          onChange={(e) => update('blood_group', e.target.value)}
          placeholder="e.g. O+"
        />

        <label htmlFor="phone">Phone</label>
        <input id="phone" type="tel" value={form.phone} onChange={(e) => update('phone', e.target.value)} />

        <label htmlFor="address">Address</label>
        <input id="address" value={form.address} onChange={(e) => update('address', e.target.value)} />

        <label>
          <input
            type="checkbox"
            checked={form.consent_sharing}
            onChange={(e) => update('consent_sharing', e.target.checked)}
          />
          Patient consents to sharing this record across facilities
        </label>

        <button type="submit">Create patient</button>
        {error && <p className="form-error">{error}</p>}
      </form>
    </main>
  )
}
