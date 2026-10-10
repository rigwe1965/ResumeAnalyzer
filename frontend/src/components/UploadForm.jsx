import { useState } from 'react'
import { apiFetch } from '../api'

function UploadForm({ onAnalyzed }) {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!resumeFile) {
      setError('Choose a resume file first — .pdf or .md.')
      return
    }
    if (!jobDescription.trim()) {
      setError('Paste the job description before analyzing.')
      return
    }

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('resume', resumeFile)
    formData.append('job_description', jobDescription)

    try {
      const data = await apiFetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })
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
        <span className="field-label">Resume</span>
        <span className="field-hint">.pdf or .md</span>
        <input
          type="file"
          accept=".pdf,.md"
          onChange={(event) => setResumeFile(event.target.files[0] ?? null)}
        />
        {resumeFile && <span className="file-tab">{resumeFile.name}</span>}
      </label>

      <label className="field">
        <span className="field-label">Job description</span>
        <textarea
          rows={9}
          placeholder="Paste the posting here — requirements, responsibilities, all of it."
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
        />
      </label>

      <button type="submit" className="stamp-button" disabled={loading}>
        {loading ? 'Marking it up…' : 'Analyze fit'}
      </button>

      {error && (
        <p data-testid="analyze-error" className="note note-red">
          {error}
        </p>
      )}
    </form>
  )
}

export default UploadForm
