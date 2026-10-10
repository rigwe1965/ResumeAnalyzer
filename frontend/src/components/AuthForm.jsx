import { useState } from 'react'
import { apiFetch } from '../api'

function AuthForm({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const isRegister = mode === 'register'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await apiFetch(
        `/api/auth/${isRegister ? 'register' : 'login'}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        },
        { auth: false },
      )
      onAuthenticated(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="upload-form auth-form">
      <p className="page-intro">
        {isRegister
          ? 'Create an account to keep your analyses private.'
          : 'Sign in to analyze a resume and see your history.'}
      </p>

      <label className="field">
        <span className="field-label">Email</span>
        <input
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <label className="field">
        <span className="field-label">Password</span>
        {isRegister && <span className="field-hint">8–128 characters</span>}
        <input
          type="password"
          autoComplete={isRegister ? 'new-password' : 'current-password'}
          required
          minLength={isRegister ? 8 : undefined}
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>

      <button type="submit" className="stamp-button" disabled={loading}>
        {loading ? 'One moment…' : isRegister ? 'Create account' : 'Sign in'}
      </button>

      {error && (
        <p data-testid="auth-error" className="note note-red">
          {error}
        </p>
      )}

      <button
        type="button"
        className="link-button"
        onClick={() => {
          setMode(isRegister ? 'login' : 'register')
          setError(null)
        }}
      >
        {isRegister ? 'Already have an account? Sign in' : 'No account yet? Create one'}
      </button>
    </form>
  )
}

export default AuthForm
