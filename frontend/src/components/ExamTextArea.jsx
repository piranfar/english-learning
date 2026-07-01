import { useEffect, useId, useState } from 'react'

const ASSISTANT_SELECTORS = [
  'grammarly-extension',
  'grammarly-desktop-integration',
  '[data-grammarly-part]',
  '.lt-toolbar',
  '[data-lt-installed]',
]

function detectWritingAssistant() {
  try {
    return ASSISTANT_SELECTORS.some((selector) => document.querySelector(selector))
  } catch {
    return false
  }
}

export default function ExamTextArea({
  examMode = true,
  showExamModeNote,
  showAssistantWarning,
  className = '',
  id,
  'data-testid': dataTestId,
  ...props
}) {
  const generatedId = useId()
  const textareaId = id || generatedId
  const [assistantDetected, setAssistantDetected] = useState(false)

  const shouldShowExamNote = showExamModeNote ?? examMode
  const shouldShowAssistantWarning = showAssistantWarning ?? examMode

  useEffect(() => {
    if (!examMode) return undefined

    function check() {
      setAssistantDetected(detectWritingAssistant())
    }

    check()

    const delayedChecks = [1000, 3000].map((delay) => window.setTimeout(check, delay))
    let observer = null

    if (typeof MutationObserver !== 'undefined' && document.body) {
      observer = new MutationObserver(check)
      observer.observe(document.body, { childList: true, subtree: true })
    }

    return () => {
      delayedChecks.forEach((timerId) => window.clearTimeout(timerId))
      observer?.disconnect()
    }
  }, [examMode])

  return (
    <div className="exam-text-area-wrap">
      <textarea
        id={textareaId}
        className={`exam-text-area ${className}`.trim()}
        spellCheck={false}
        autoCorrect="off"
        autoCapitalize="off"
        autoComplete="off"
        data-gramm="false"
        data-gramm_editor="false"
        data-enable-grammarly="false"
        data-lt-active="false"
        data-lt-toolbar="false"
        data-testid={dataTestId}
        {...props}
      />

      {shouldShowExamNote && (
        <p className="exam-text-area-note muted">
          Exam mode: browser spellcheck and writing-assistant support are disabled. For realistic
          practice, disable Grammarly or similar extensions.
        </p>
      )}

      {shouldShowAssistantWarning && assistantDetected && (
        <p className="exam-text-area-warning" role="status">
          Writing assistant detected. For accurate practice, please disable it for this site.
        </p>
      )}
    </div>
  )
}
