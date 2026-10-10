import { useCallback, useEffect, useState } from 'react'
import './App.css'
import UploadForm from './components/UploadForm'
import ReportView from './components/ReportView'
import HistoryList from './components/HistoryList'
import AuthForm from './components/AuthForm'
import { apiFetch, clearToken, getToken, setToken, setUnauthorizedHandler } from './api'

function App() {
  const [tab, setTab] = useState('analyze')
  const [report, setReport] = useState(null)
  const [user, setUser] = useState(null)
  const [checkingSession, setCheckingSession] = useState(() => Boolean(getToken()))

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setReport(null)
    setTab('analyze')
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
  }, [logout])

  // Restore the session from a saved token.
  useEffect(() => {
    if (!getToken()) return
    apiFetch('/api/auth/me')
      .then(setUser)
      .catch(() => {})
      .finally(() => setCheckingSession(false))
  }, [])

  const handleAuthenticated = ({ access_token, user: authedUser }) => {
    setToken(access_token)
    setUser(authedUser)
  }

  return (
    <div className="frame">
      <header className="letterhead">
        <h1>Resume Analyzer</h1>
        <p className="tagline">Get your resume marked up before you hit send.</p>
        {user && (
          <div className="account-bar">
            <span>{user.email}</span>
            <button type="button" className="link-button" onClick={logout}>
              Sign out
            </button>
          </div>
        )}
      </header>

      {checkingSession ? (
        <p className="note">Checking your session…</p>
      ) : !user ? (
        <main className="page">
          <AuthForm onAuthenticated={handleAuthenticated} />
        </main>
      ) : (
        <>
      <nav className="tab-row" aria-label="Views">
        <button
          type="button"
          className={tab === 'analyze' ? 'active' : ''}
          aria-current={tab === 'analyze'}
          onClick={() => setTab('analyze')}
        >
          Analyze
        </button>
        <button
          type="button"
          className={tab === 'history' ? 'active' : ''}
          aria-current={tab === 'history'}
          onClick={() => setTab('history')}
        >
          History
        </button>
      </nav>

      <main className="page">
        {tab === 'analyze' && (
          <>
            <p className="page-intro">
              Drop in a resume and paste the job posting. You'll get it back with keywords,
              gaps, and phrasing marked in red.
            </p>
            <UploadForm onAnalyzed={setReport} />
            <ReportView report={report} />
          </>
        )}

        {tab === 'history' && <HistoryList />}
      </main>
        </>
      )}
    </div>
  )
}

export default App
