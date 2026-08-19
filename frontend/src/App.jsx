import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { PatientNewPage } from './pages/PatientNewPage'
import { PatientSummaryPage } from './pages/PatientSummaryPage'
import { PatientTimelinePage } from './pages/PatientTimelinePage'
import { AccessHistoryPage } from './pages/AccessHistoryPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'

const CREATE_PATIENT_ROLES = ['admin', 'doctor', 'pharmacist', 'receptionist']

export default function App() {
  return (
    <AuthProvider>
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
    </AuthProvider>
  )
}
