import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
} from '@mui/material'
import { useAuth } from '../hooks/useAuth'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const navigate = useNavigate()
  const { login, register, loginLoading, registerLoading, loginError, registerError } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (isRegister) {
        await register(username, password, email || undefined)
        setIsRegister(false)
        setUsername('')
        setPassword('')
        setEmail('')
      } else {
        await login(username, password)
        navigate('/')
      }
    } catch (error) {
      // Error handled by hook
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: '#F5F5F5',
      }}
    >
      <Card sx={{ maxWidth: 400, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#1976D2', mb: 3, textAlign: 'center' }}>
            Altur
          </Typography>
          <Typography variant="h6" gutterBottom sx={{ mb: 3, textAlign: 'center' }}>
            {isRegister ? 'Create Account' : 'Sign In'}
          </Typography>

          {(loginError || registerError) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {loginError?.message || registerError?.message || 'Authentication failed'}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label={isRegister ? "Username" : "Username or Email"}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              sx={{ mb: 2 }}
            />
            {isRegister && (
              <TextField
                fullWidth
                label="Email (optional)"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{ mb: 2 }}
              />
            )}
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              sx={{ mb: 3 }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loginLoading || registerLoading}
              sx={{ bgcolor: '#1976D2', mb: 2 }}
            >
              {isRegister ? (registerLoading ? 'Creating...' : 'Register') : loginLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => {
                setIsRegister(!isRegister)
                setUsername('')
                setPassword('')
                setEmail('')
              }}
            >
              {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Login

