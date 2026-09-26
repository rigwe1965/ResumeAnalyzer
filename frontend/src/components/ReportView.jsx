function ReportSection({ title, items }) {
  if (!items || items.length === 0) return null

  return (
    <div className="report-section">
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function ReportView({ report }) {
  if (!report) return null

  return (
    <div className="report-view" data-testid="analysis-report">
      <div className="score-badge">
        <span className="score-value">{report.score}</span>
        <span className="score-label">/ 100 fitment score</span>
      </div>

      <ReportSection title="Missing keywords" items={report.missing_keywords} />
      <ReportSection title="Skill gaps" items={report.skill_gaps} />
      <ReportSection title="Phrasing suggestions" items={report.phrasing_suggestions} />
    </div>
  )
}

export default ReportView
