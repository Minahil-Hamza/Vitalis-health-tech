import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { api } from './api'

vi.mock('./api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
  ApiError: class ApiError extends Error {},
}))

function renderAt(path) {
  window.history.pushState({}, '', path)
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('redirects an unauthenticated visitor from the dashboard to /login', async () => {
    api.get.mockRejectedValue(new Error('not authenticated'))

    renderAt('/')

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Vitalis' })).toBeInTheDocument())
  })

  it('shows the dashboard for an authenticated user', async () => {
    api.get.mockResolvedValue({
      id: '1',
      full_name: 'Dr. Test',
      role: 'doctor',
      facility_id: 'f1',
      facility_name: 'Test Clinic',
    })

    renderAt('/')

    await waitFor(() => expect(screen.getByText('Welcome, Dr. Test')).toBeInTheDocument())
    expect(screen.getByText('Test Clinic')).toBeInTheDocument()
    // Non-admin shouldn't see the admin dashboard link.
    expect(screen.queryByText('Admin dashboard')).not.toBeInTheDocument()
  })

  it('shows the admin dashboard link for an admin user', async () => {
    api.get.mockResolvedValue({
      id: '1',
      full_name: 'Admin Person',
      role: 'admin',
      facility_id: 'f1',
      facility_name: 'Test Clinic',
    })

    renderAt('/')

    await waitFor(() => expect(screen.getByText('Admin dashboard')).toBeInTheDocument())
  })
})
