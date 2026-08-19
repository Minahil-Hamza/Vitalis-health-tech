import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'

// Route-level code splitting: each page (and PatientSummaryPage's Three.js-heavy
// Body3D in particular) only loads when its route is actually visited, instead of
// bloating the initial bundle every visitor downloads just to see the login page.
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const PatientNewPage = lazy(() => import('./pages/PatientNewPage').then((m) => ({ default: m.PatientNewPage })))
const PatientSummaryPage = lazy(() =>
  import('./pages/PatientSummaryPage').then((m) => ({ default: m.PatientSummaryPage })),
)
const PatientTimelinePage = lazy(() =>
  import('./pages/PatientTimelinePage').then((m) => ({ default: m.PatientTimelinePage })),
)
const AccessHistoryPage = lazy(() =>
  import('./pages/AccessHistoryPage').then((m) => ({ default: m.AccessHistoryPage })),
)
const AdminDashboardPage = lazy(() =>
  import('./pages/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage })),
)

const CREATE_PATIENT_ROLES = ['admin', 'doctor', 'pharmacist', 'receptionist']

function RouteLoading() {
  return <p className="route-loading">Loading...</p>
}

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<RouteLoading />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/new"
            element={
              <ProtectedRoute roles={CREATE_PATIENT_ROLES}>
                <PatientNewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:patientId"
            element={
              <ProtectedRoute>
                <PatientSummaryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:patientId/timeline"
            element={
              <ProtectedRoute>
                <PatientTimelinePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:patientId/access-history"
            element={
              <ProtectedRoute>
                <AccessHistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}
