const GRAMMAR_STEP_HEADERS = [
  /###\s*1\.\s*Simple explanation/i,
  /###\s*2\.\s*Persian explanation/i,
  /###\s*3\.\s*Pronunciation/i,
  /###\s*4\.\s*Examples/i,
  /###\s*5\.\s*Common mistakes/i,
  /###\s*6\.\s*Mini practice/i,
]

export function courseIdFromTopic(topic) {
  if (!topic) return ''
  if (topic.slug) return `grammar_${topic.slug}`
  if (topic.id) return `grammar_topic_${topic.id}`
  return `grammar_${String(topic.title || 'lesson')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')}`
}

export function extractPracticeQuestions(content) {
  if (!content) return []
  const sectionMatch = content.match(/###\s*6\.\s*Mini practice[\s\S]*?(?=###\s*7\.|$)/i)
  if (!sectionMatch) return []
  const section = sectionMatch[0]
  const numbered = section.match(/^\s*\d+\.\s+(.+)$/gm) || []
  return numbered.map((line) => line.replace(/^\s*\d+\.\s+/, '').trim()).filter(Boolean)
}

export function detectCompletedSteps(content) {
  if (!content) return []
  const completed = []
  GRAMMAR_STEP_HEADERS.forEach((pattern, index) => {
    if (pattern.test(content)) completed.push(index + 1)
  })
  return completed
}

export function deriveSessionProgress(session) {
  const messages = session?.messages || []
  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')
  const assistantContent = lastAssistant?.content || ''

  const completedSteps = detectCompletedSteps(assistantContent)
  const practiceQuestions = extractPracticeQuestions(assistantContent)
  const userMessages = messages.filter((m) => m.role === 'user')
  const userAnswers = userMessages.map((m) => m.content)

  let completedPractice = 0
  if (practiceQuestions.length > 0) {
    const firstPracticeIndex = messages.findIndex(
      (m) => m.role === 'assistant' && /###\s*6\.\s*Mini practice/i.test(m.content || ''),
    )
    if (firstPracticeIndex >= 0) {
      completedPractice = messages
        .slice(firstPracticeIndex + 1)
        .filter((m) => m.role === 'user').length
    }
  } else {
    completedPractice = Math.max(0, userMessages.length - 1)
  }

  const currentStep = completedSteps.length > 0 ? Math.max(...completedSteps) : 1
  const courseId = session.courseId || session.progress?.course_id || ''
  const courseTitle = session.courseTitle || session.title || session.progress?.course_title || ''

  const correctionResults = messages
    .filter((m) => m.role === 'assistant' && m.corrections?.length)
    .flatMap((m) => m.corrections)

  return {
    course_id: courseId,
    course_title: courseTitle,
    current_step: currentStep,
    completed_steps: completedSteps,
    total_steps: 6,
    completed_practice_questions: Math.min(completedPractice, practiceQuestions.length || completedPractice),
    total_practice_questions: practiceQuestions.length,
    status: session.progress?.status === 'completed' ? 'completed' : 'in_progress',
    last_message_at: session.lastUpdatedAt || new Date().toISOString(),
    practiceQuestions,
    userAnswers,
    correctionResults,
  }
}

export function buildWelcomeBackMessage(session) {
  const progress = session.progress || deriveSessionProgress(session)
  const title = progress.course_title || session.title || 'your lesson'
  const step = progress.current_step || 1
  const practiceNum = (progress.completed_practice_questions || 0) + 1

  if (progress.total_practice_questions > 0 && progress.completed_practice_questions < progress.total_practice_questions) {
    return `Welcome back. You were learning ${title}. Let's continue from practice question ${practiceNum}.`
  }
  if (progress.completed_steps?.length >= progress.total_steps) {
    return `Welcome back. You were learning ${title}. Let's continue where you left off.`
  }
  return `Welcome back. You were learning ${title}. Let's continue from step ${step}.`
}

export function mergeSessionUpdate(existing, partial) {
  const base = existing || {}
  const mergedMessages = partial.messages ?? base.messages ?? []
  const draft = {
    ...base,
    ...partial,
    messages: mergedMessages,
    lastUpdatedAt: new Date().toISOString(),
  }
  const derived = deriveSessionProgress(draft)
  return {
    ...draft,
    practiceQuestions: derived.practiceQuestions,
    userAnswers: derived.userAnswers,
    correctionResults: derived.correctionResults,
    progress: {
      ...derived,
      status: partial.progress?.status || base.progress?.status || derived.status,
    },
  }
}
