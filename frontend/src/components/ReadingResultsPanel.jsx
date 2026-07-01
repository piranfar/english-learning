import { Link } from 'react-router-dom'
import { formatReadingSkillLabel } from '../services/readingStorage'

const SKILL_ORDER = [
  'main_idea',
  'detail',
  'inference',
  'vocabulary',
  'grammar_context',
  'complete_words',
  'sentence_meaning',
]

export default function ReadingResultsPanel({ result, onRetry, onGenerateNew }) {
  if (!result) return null

  const skillScores = result.skill_scores || {}
  const orderedSkills = [
    ...SKILL_ORDER.filter((skill) => skill in skillScores),
    ...Object.keys(skillScores).filter((skill) => !SKILL_ORDER.includes(skill)),
  ]

  return (
    <section className="reading-results-panel card">
      <h3>Review results</h3>
      <p className="reading-score-headline">
        Score: {result.score.correct}/{result.score.total} ({result.score.percent}%)
      </p>

      {result.practice_toefl_estimate && (
        <p className="muted reading-toefl-estimate">
          Practice reading estimate: {result.practice_toefl_estimate.score} / {result.practice_toefl_estimate.scale}
          {' — '}
          {result.practice_toefl_estimate.label}
        </p>
      )}

      {orderedSkills.length > 0 && (
        <div className="reading-skill-bars">
          {orderedSkills.map((skill) => (
            <div key={skill} className="reading-skill-bar-row">
              <span className="reading-skill-bar-label">{formatReadingSkillLabel(skill)}</span>
              <div className="reading-skill-bar-track">
                <div
                  className="reading-skill-bar-fill"
                  style={{ width: `${skillScores[skill]}%` }}
                />
              </div>
              <span className="reading-skill-bar-value">{skillScores[skill]}%</span>
            </div>
          ))}
        </div>
      )}

      {result.mistake_pattern && (
        <p className="reading-mistake-pattern">{result.mistake_pattern}</p>
      )}

      {result.next_drill?.instruction && (
        <div className="reading-next-drill">
          <strong>{result.next_drill.title || 'Recommended next drill'}</strong>
          <p>{result.next_drill.instruction}</p>
        </div>
      )}

      {result.mistakes_saved > 0 ? (
        <p className="muted">
          {result.mistakes_saved} wrong answer{result.mistakes_saved === 1 ? '' : 's'} saved to{' '}
          <Link to="/mistakes">Mistake Clinic</Link>.
        </p>
      ) : (
        <p className="muted">Great work — no mistakes to review.</p>
      )}

      <div className="reading-results-actions">
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          Retry this passage
        </button>
        <button type="button" onClick={onGenerateNew}>
          Generate new practice
        </button>
      </div>
    </section>
  )
}
