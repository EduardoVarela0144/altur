import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import CallsList from './pages/CallsList'
import CallDetail from './pages/CallDetail'
import Analytics from './pages/Analytics'
import Login from './pages/Login'
import { useAuth } from './hooks/useAuth'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<CallsList />} />
                <Route path="/calls/:id" element={<CallDetail />} />
                <Route path="/analytics" element={<Analytics />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}

export default App
