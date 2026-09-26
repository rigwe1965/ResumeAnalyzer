import { useState } from 'react'
import './App.css'

function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const pingGemini = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/ping-gemini')
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Request failed')
      }
      setResult(data.response)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="center">
      <h1>Resume Analyzer</h1>
      <p>Full-stack smoke test: frontend &rarr; backend &rarr; Gemini</p>
      <button type="button" onClick={pingGemini} disabled={loading}>
        {loading ? 'Pinging Gemini...' : 'Ping Gemini'}
      </button>
      {result && <p data-testid="gemini-result">{result}</p>}
      {error && <p data-testid="gemini-error" style={{ color: 'red' }}>{error}</p>}
    </section>
  )
}

export default App
