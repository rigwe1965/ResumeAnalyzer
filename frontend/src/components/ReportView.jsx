function KeywordLine({ words }) {
  if (!words || words.length === 0) return null

  return (
    <section className="annotation">
      <h3>Missing keywords</h3>
      <p className="keyword-line">
        {words.map((word, index) => (
          <span className="keyword" key={index}>
            {word}
          </span>
        ))}
      </p>
    </section>
  )
}

function ChangeBarList({ title, items }) {
  if (!items || items.length === 0) return null

  return (
    <section className="annotation">
      <h3>{title}</h3>
      <ul className="margin-notes change-bars">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

function CaretList({ title, items }) {
  if (!items || items.length === 0) return null

  return (
    <section className="annotation">
      <h3>{title}</h3>
      <ul className="margin-notes carets">
        {items.map((item, index) => (
          <li key={index}>
            <span className="caret" aria-hidden="true">
              ^
            </span>
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}

function ReportView({ report }) {
  if (!report) return null

  const tone = report.score >= 70 ? 'good' : 'needs-work'

  return (
    <div className="report" data-testid="analysis-report">
      <div className="grade">
        <span className={`grade-circle grade-${tone}`}>
          <span className="grade-number">{report.score}</span>
        </span>
        <span className="grade-label">out of 100 fitment</span>
      </div>

      <KeywordLine words={report.missing_keywords} />
      <ChangeBarList title="Skill gaps" items={report.skill_gaps} />
      <CaretList title="Phrasing suggestions" items={report.phrasing_suggestions} />
    </div>
  )
}

export default ReportView
