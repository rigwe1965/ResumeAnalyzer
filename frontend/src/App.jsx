import { useState } from 'react'
import './App.css'
import UploadForm from './components/UploadForm'
import ReportView from './components/ReportView'
import HistoryList from './components/HistoryList'

function App() {
  const [tab, setTab] = useState('analyze')
  const [report, setReport] = useState(null)

  return (
    <section id="center">
      <h1>Resume Analyzer</h1>
      <p>Upload a resume and a job description to get a fitment score and recommendations.</p>

      <nav className="tabs">
        <button
          type="button"
          className={tab === 'analyze' ? 'active' : ''}
          onClick={() => setTab('analyze')}
        >
          Analyze
        </button>
        <button
          type="button"
          className={tab === 'history' ? 'active' : ''}
          onClick={() => setTab('history')}
        >
          History
        </button>
      </nav>

      {tab === 'analyze' && (
        <>
          <UploadForm onAnalyzed={setReport} />
          <ReportView report={report} />
        </>
      )}

      {tab === 'history' && <HistoryList />}
    </section>
  )
}

export default App
