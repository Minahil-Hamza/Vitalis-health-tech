import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../AuthContext'
import { LoginPage } from './LoginPage'
import { api } from '../api'

vi.mock('../api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
  ApiError: class ApiError extends Error {},
}))

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockRejectedValue(new Error('not authenticated'))
  })

  it('shows the server error message when login fails', async () => {
    api.post.mockRejectedValue({ status: 401, detail: 'Invalid email or password' })
    const user = userEvent.setup()

    renderLoginPage()

    await user.type(screen.getByLabelText('Email'), 'wrong@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Log in' }))

    await waitFor(() => expect(screen.getByText('Invalid email or password')).toBeInTheDocument())
  })

  it('calls the login API with the entered credentials', async () => {
    api.post.mockResolvedValue({ access_token: 'abc' })
    const user = userEvent.setup()

    renderLoginPage()

    await user.type(screen.getByLabelText('Email'), 'admin@clinic.pk')
    await user.type(screen.getByLabelText('Password'), 'Secret123!')
    await user.click(screen.getByRole('button', { name: 'Log in' }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'admin@clinic.pk',
        password: 'Secret123!',
      }),
    )
  })
})
