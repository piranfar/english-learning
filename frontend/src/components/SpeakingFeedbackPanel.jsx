import AssistantMessage from './AssistantMessage'
import AudioRecorder from './AudioRecorder'
import TextToSpeechButton from './TextToSpeechButton'
import { stripSpeakingFeedbackBlock } from '../utils/messageContent'

const TYPED_ONLY_NOTICE =
  'Typed practice can evaluate grammar, vocabulary, and organization. Pronunciation cannot be evaluated without audio.'

const RUBRIC_ORDER = ['fluency', 'grammar', 'vocabulary', 'organization']

const RUBRIC_LABELS = {
  fluency: 'Fluency',
  grammar: 'Grammar',
  vocabulary: 'Vocabulary',
  organization: 'Organization',
  pronunciation_clarity: 'Fluency',
  intonation_rhythm: 'Fluency',
  task_completion: 'Organization',
}

function RubricItem({ name, item }) {
  if (!item) return null
  const score = typeof item === 'object' ? item.score : item
  const max = typeof item === 'object' ? item.max || 4 : 4
  const reason = typeof item === 'object' ? item.reason : ''
  const nextStep = typeof item === 'object' ? item.next_step : ''

  return (
    <div className="speaking-breakdown-item">
      <div className="speaking-rubric-head">
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

export default function SpeakingFeedbackPanel({
  transcript = '',
  reply = '',
  speakingFeedback = null,
  inputMode = 'voice',
  onRepeatSubmit,
  repeatLoading = false,
}) {
  if (!reply && !transcript) return null

  const sf = speakingFeedback || {}
  const cleanReply = stripSpeakingFeedbackBlock(reply)
  const isTyped = inputMode === 'typed' || sf.input_mode === 'typed'
  const repeatAnswer = sf.repeat_answer || sf.model_answer || sf.natural_version || sf.corrected_version || ''
  const modelAnswer = sf.model_answer || sf.natural_version || ''
  const repeatTask = sf.repeat_task_recommendation || sf.recommended_next_task || ''
  const rubric = sf.rubric || {}
  const mainMistakes = sf.main_mistakes || []

  return (
    <div className="speaking-feedback-panel">
      {transcript && (
        <section className="card speaking-feedback-section">
          <h2>Your transcript</h2>
          <p>{transcript}</p>
        </section>
      )}

      {isTyped && (
        <section className="card speaking-feedback-section">
          <p className="speaking-typed-notice">{TYPED_ONLY_NOTICE}</p>
        </section>
      )}

      {sf.overall_score != null && (
        <section className="card speaking-feedback-section">
          <h2>Evaluation</h2>
          <p className="speaking-overall-score">
            Overall score: <strong>{sf.overall_score}/100</strong>
            {sf.cefr_estimate && (
              <span className="muted"> · Estimated level: {sf.cefr_estimate}</span>
            )}
          </p>

          {Object.keys(rubric).length > 0 ? (
            <div className="speaking-breakdown-grid">
              {orderedRubricEntries(rubric).map(([key, value]) => (
                <RubricItem key={key} name={key} item={value} />
              ))}
            </div>
          ) : (
            sf.breakdown && (
              <div className="speaking-breakdown-grid">
                {orderedRubricEntries(sf.breakdown).map(([key, value]) => (
                  <RubricItem key={key} name={key} item={{ score: value, max: 4 }} />
                ))}
              </div>
            )
          )}
        </section>
      )}

      {!isTyped && sf.pronunciation_notes && (
        <section className="card speaking-feedback-section">
          <h2>Pronunciation / intonation notes</h2>
          <p>{sf.pronunciation_notes}</p>
          {sf.pronunciation_limited && (
            <p className="muted">
              Based on your transcript only — not a full acoustic analysis.
            </p>
          )}
        </section>
      )}

      {sf.positive_comment && (
        <section className="card speaking-feedback-section">
          <h2>Positive note</h2>
          <p>{sf.positive_comment}</p>
        </section>
      )}

      {mainMistakes.length > 0 && (
        <section className="card speaking-feedback-section">
          <h2>Main mistakes</h2>
          <div className="speaking-mistake-table">
            {mainMistakes.map((row, index) => (
              <article key={index} className="speaking-mistake-row">
                {row.area && (
                  <p>
                    <span className="label">Area</span> {row.area}
                  </p>
                )}
                <p>
                  <span className="label">Wrong</span> {row.wrong}
                </p>
                {row.correct && (
                  <p>
                    <span className="label">Correct</span> {row.correct}
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
        <section className="card speaking-feedback-section">
          <h2>Coach feedback</h2>
          <AssistantMessage content={cleanReply} />
        </section>
      )}

      {sf.corrected_version && (
        <section className="card speaking-feedback-section">
          <h2>Corrected transcript</h2>
          <p>{sf.corrected_version}</p>
        </section>
      )}

      {modelAnswer && (
        <section className="card speaking-feedback-section">
          <h2>Better model answer</h2>
          <p>{modelAnswer}</p>
        </section>
      )}

      {sf.vocabulary_upgrades?.length > 0 && (
        <section className="card speaking-feedback-section">
          <h2>Vocabulary upgrade</h2>
          <ul>
            {sf.vocabulary_upgrades.map((item, index) => (
              <li key={index}>
                Instead of &ldquo;{item.instead_of}&rdquo; try:{' '}
                {(item.try || []).join(', ')}
              </li>
            ))}
          </ul>
        </section>
      )}

      {repeatAnswer && (
        <section className="card speaking-feedback-section">
          <h2>Practice improved answer</h2>
          <p className="speaking-repeat-text">{repeatAnswer}</p>
          <div className="speaking-repeat-actions">
            <TextToSpeechButton text={repeatAnswer} label="Listen" size="sm" />
          </div>
          {onRepeatSubmit && (
            <div className="speaking-repeat-recorder">
              <p className="muted">Record again and compare your attempt.</p>
              <AudioRecorder
                onSubmit={onRepeatSubmit}
                loading={repeatLoading}
                submitLabel="Submit repeat attempt"
              />
            </div>
          )}
        </section>
      )}

      {sf.follow_up_question && (
        <section className="card speaking-feedback-section">
          <h2>Follow-up question</h2>
          <p>{sf.follow_up_question}</p>
        </section>
      )}

      {repeatTask && (
        <section className="card speaking-feedback-section">
          <h2>Repeat task recommendation</h2>
          <p>{repeatTask}</p>
        </section>
      )}
    </div>
  )
}
