import { useState } from 'react'

function UploadForm({ onAnalyzed }) {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!resumeFile) {
      setError('Please choose a resume file (.pdf or .md).')
      return
    }
    if (!jobDescription.trim()) {
      setError('Please paste the job description.')
      return
    }

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('resume', resumeFile)
    formData.append('job_description', jobDescription)

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Analysis failed')
      }
      onAnalyzed(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <label className="field">
        <span>Resume (.pdf or .md)</span>
        <input
          type="file"
          accept=".pdf,.md"
          onChange={(event) => setResumeFile(event.target.files[0] ?? null)}
        />
      </label>

      <label className="field">
        <span>Job description</span>
        <textarea
          rows={10}
          placeholder="Paste the job description here..."
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Analyze fit'}
      </button>

      {error && (
        <p data-testid="analyze-error" className="error-text">
          {error}
        </p>
      )}
    </form>
  )
}

export default UploadForm
