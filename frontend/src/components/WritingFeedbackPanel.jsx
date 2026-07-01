import AssistantMessage from './AssistantMessage'
import CollapsibleNativeNote from './CollapsibleNativeNote'
import { stripWritingFeedbackBlock } from '../utils/messageContent'

const RUBRIC_ORDER = [
  'task_response',
  'organization',
  'grammar_accuracy',
  'vocabulary_range',
  'academic_tone',
  'sentence_variety',
]

const RUBRIC_LABELS = {
  task_response: 'Task response',
  task_fulfillment: 'Task response',
  organization: 'Organization',
  grammar_accuracy: 'Grammar accuracy',
  grammar: 'Grammar accuracy',
  vocabulary_range: 'Vocabulary range',
  vocabulary: 'Vocabulary range',
  academic_tone: 'Academic tone',
  sentence_variety: 'Sentence variety',
  development: 'Development / details',
  development_details: 'Development / details',
}

function RubricItem({ name, item }) {
  if (!item) return null
  const score = typeof item === 'object' ? item.score : item
  const max = typeof item === 'object' ? item.max || 4 : 4
  const reason = typeof item === 'object' ? item.reason : ''
  const nextStep = typeof item === 'object' ? item.next_step : ''

  return (
    <div className="writing-rubric-item">
      <div className="writing-rubric-head">
        <strong>{RUBRIC_LABELS[name] || name.replace(/_/g, ' ')}</strong>
        <span>{score}/{max}</span>
      </div>
      {reason && <p className="muted">{reason}</p>}
      {nextStep && (
        <p>
          <span className="label">Next step</span> {nextStep}
        </p>
      )}
    </div>
  )
}

function orderedRubricEntries(rubric) {
  const entries = Object.entries(rubric || {})
  const orderIndex = (key) => {
    const idx = RUBRIC_ORDER.indexOf(key)
    return idx === -1 ? RUBRIC_ORDER.length : idx
  }
  return entries.sort(([a], [b]) => orderIndex(a) - orderIndex(b))
}

export default function WritingFeedbackPanel({
  originalAnswer = '',
  reply = '',
  writingFeedback = null,
  toeflFeedback = null,
  corrections = [],
}) {
  if (!reply && !writingFeedback && !toeflFeedback) return null

  const wf = writingFeedback || {}
  const tf = toeflFeedback || {}
  const cleanReply = stripWritingFeedbackBlock(reply)

  const mainMistakes =
    wf.main_mistakes?.length > 0
      ? wf.main_mistakes
      : tf.main_mistakes?.length > 0
        ? tf.main_mistakes
        : []

  const sentenceCorrections =
    wf.sentence_corrections?.length > 0
      ? wf.sentence_corrections
      : tf.sentence_corrections?.length > 0
        ? tf.sentence_corrections
        : corrections.map((c) => ({
            original: c.original,
            corrected: c.corrected,
            why: c.reason,
          }))

  const rubric = wf.rubric || tf.rubric_details || {}
  const toeflScores = tf.scores || {}
  const recommendedRevision =
    wf.recommended_revision_task || tf.recommended_revision_task || wf.next_task || tf.next_task

  return (
    <div className="writing-feedback-panel">
      {originalAnswer && (
        <section className="card writing-feedback-section">
          <h2>Your original answer</h2>
          <p className="writing-original-text">{originalAnswer}</p>
        </section>
      )}

      {(wf.overall_score != null ||
        tf.estimated_toefl_score != null ||
        Object.keys(rubric).length > 0 ||
        Object.keys(toeflScores).length > 0) && (
        <section className="card writing-feedback-section">
          <h2>Score</h2>
          {wf.overall_score != null && (
            <p className="writing-overall-score">
              Overall: <strong>{wf.overall_score}/100</strong>
            </p>
          )}
          {tf.estimated_toefl_score != null && (
            <p className="writing-toefl-estimate">
              Estimated TOEFL writing score:{' '}
              <strong>{tf.estimated_toefl_score}/5</strong>
              <span className="muted"> (practice estimate, not an official ETS score)</span>
            </p>
          )}
          {wf.word_count_note && <p className="muted">{wf.word_count_note}</p>}
          {Object.keys(rubric).length > 0 && (
            <div className="writing-rubric-grid">
              {orderedRubricEntries(rubric).map(([key, value]) => (
                <RubricItem key={key} name={key} item={value} />
              ))}
            </div>
          )}
          {Object.keys(toeflScores).length > 0 && Object.keys(rubric).length === 0 && (
            <div className="writing-rubric-grid">
              {orderedRubricEntries(toeflScores).map(([key, value]) => (
                <RubricItem
                  key={key}
                  name={key}
                  item={
                    tf.rubric_details?.[key] || {
                      score: value,
                      max: 4,
                      reason: tf.feedback,
                    }
                  }
                />
              ))}
            </div>
          )}
        </section>
      )}

      {(wf.positive_comment || wf.main_problem) && (
        <section className="card writing-feedback-section">
          <h2>Teacher summary</h2>
          {wf.positive_comment && (
            <p>
              <span className="label">Positive</span> {wf.positive_comment}
            </p>
          )}
          {wf.main_problem && (
            <p>
              <span className="label">Main problem</span> {wf.main_problem}
            </p>
          )}
        </section>
      )}

      {mainMistakes.length > 0 && (
        <section className="card writing-feedback-section">
          <h2>Main mistakes</h2>
          <div className="writing-correction-table">
            {mainMistakes.map((row, index) => (
              <article key={index} className="writing-correction-row">
                <p>
                  <span className="label">Wrong</span> {row.wrong || row.original}
                </p>
                {(row.correct || row.corrected) && (
                  <p>
                    <span className="label">Correct</span> {row.correct || row.corrected}
                  </p>
                )}
                {row.reason && (
                  <p>
                    <span className="label">Why</span> {row.reason}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {cleanReply && (
        <section className="card writing-feedback-section">
          <h2>Teacher feedback</h2>
          <AssistantMessage content={cleanReply} corrections={corrections} />
        </section>
      )}

      {sentenceCorrections.length > 0 && (
        <section className="card writing-feedback-section">
          <h2>Sentence-level corrections</h2>
          <div className="writing-correction-table">
            {sentenceCorrections.map((row, index) => (
              <article key={index} className="writing-correction-row">
                <p>
                  <span className="label">Original</span> {row.original}
                </p>
                <p>
                  <span className="label">Corrected</span> {row.corrected}
                </p>
                {row.why && (
                  <p>
                    <span className="label">Why</span> {row.why}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {(wf.corrected_version || wf.natural_version || wf.high_score_sample || tf.corrected_version) && (
        <section className="card writing-feedback-section">
          <h2>Improve my answer</h2>
          {(wf.corrected_version || tf.corrected_version) && (
            <div className="writing-version-block">
              <span className="label">Corrected answer</span>
              <p>{wf.corrected_version || tf.corrected_version}</p>
            </div>
          )}
          {(wf.natural_version || tf.natural_version) && (
            <div className="writing-version-block">
              <span className="label">Better natural version</span>
              <p>{wf.natural_version || tf.natural_version}</p>
            </div>
          )}
          {(wf.high_score_sample || tf.high_score_sample) && (
            <div className="writing-version-block">
              <span className="label">High-score learner version</span>
              <p>{wf.high_score_sample || tf.high_score_sample}</p>
            </div>
          )}
        </section>
      )}

      {wf.useful_phrases?.length > 0 && (
        <section className="card writing-feedback-section">
          <h2>Useful phrases</h2>
          <ul>
            {wf.useful_phrases.map((phrase) => (
              <li key={phrase}>{phrase}</li>
            ))}
          </ul>
        </section>
      )}

      {recommendedRevision && (
        <section className="card writing-feedback-section">
          <h2>Recommended revision task</h2>
          <p>{recommendedRevision}</p>
        </section>
      )}

      {tf.persian_summary && (
        <section className="card writing-feedback-section">
          <CollapsibleNativeNote note={tf.persian_summary} />
        </section>
      )}
    </div>
  )
}
