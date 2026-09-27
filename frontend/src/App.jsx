import { useState } from 'react'
import './App.css'
import UploadForm from './components/UploadForm'
import ReportView from './components/ReportView'
import HistoryList from './components/HistoryList'

function App() {
  const [tab, setTab] = useState('analyze')
  const [report, setReport] = useState(null)

  return (
    <div className="frame">
      <header className="letterhead">
        <h1>Resume Analyzer</h1>
        <p className="tagline">Get your resume marked up before you hit send.</p>
      </header>

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
    </div>
  )
}

export default App
