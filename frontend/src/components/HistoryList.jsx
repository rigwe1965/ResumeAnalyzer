import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import ReportView from './ReportView'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function HistoryList() {
  const [analyses, setAnalyses] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const loadAnalyses = async () => {
      try {
        const data = await apiFetch('/api/analyses')
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
      const data = await apiFetch(`/api/analyses/${id}`)
      setSelected(data)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <p className="note">Opening the folder…</p>
  if (error) return <p className="note note-red">{error}</p>
  if (analyses.length === 0) {
    return <p className="note">This folder is empty. Analyze a resume to file your first report.</p>
  }

  return (
    <div className="ledger-wrap">
      <ul className="ledger">
        {analyses.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={selected?.id === item.id ? 'ledger-row selected' : 'ledger-row'}
              onClick={() => viewDetail(item.id)}
            >
              <span className="ledger-name">{item.resume_filename}</span>
              <span className="ledger-leader" aria-hidden="true" />
              <span className="ledger-score">{item.score}</span>
              <span className="ledger-date">{formatDate(item.created_at)}</span>
            </button>
          </li>
        ))}
      </ul>

      {selected && <ReportView report={selected} />}
    </div>
  )
}

export default HistoryList
