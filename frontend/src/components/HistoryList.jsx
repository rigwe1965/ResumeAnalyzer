import { useEffect, useState } from 'react'
import ReportView from './ReportView'

function HistoryList() {
  const [analyses, setAnalyses] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const loadAnalyses = async () => {
      try {
        const res = await fetch('/api/analyses')
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to load history')
        if (!cancelled) setAnalyses(data)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadAnalyses()
    return () => {
      cancelled = true
    }
  }, [])

  const viewDetail = async (id) => {
    setError(null)
    try {
      const res = await fetch(`/api/analyses/${id}`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to load analysis')
      setSelected(data)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <p>Loading history...</p>
  if (error) return <p className="error-text">{error}</p>
  if (analyses.length === 0) return <p>No analyses yet.</p>

  return (
    <div className="history-list">
      <table>
        <thead>
          <tr>
            <th>Resume</th>
            <th>Score</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((item) => (
            <tr
              key={item.id}
              onClick={() => viewDetail(item.id)}
              className={selected?.id === item.id ? 'selected' : ''}
            >
              <td>{item.resume_filename}</td>
              <td>{item.score}</td>
              <td>{new Date(item.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && <ReportView report={selected} />}
    </div>
  )
}

export default HistoryList
