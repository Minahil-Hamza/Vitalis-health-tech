import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="navbar">
        <Link to="/" className="navbar-brand">
          <span className="navbar-logo">V</span>
          Vitalis
        </Link>
        {user && (
          <div className="navbar-user">
            <span className="navbar-user-name">{user.full_name}</span>
            <span className="badge badge-role">{user.role}</span>
            <button type="button" className="btn-ghost" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </header>
      <main className="page-container">{children}</main>
    </div>
  )
}
