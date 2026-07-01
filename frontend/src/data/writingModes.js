/**
 * Writing mode configuration, prompts, and helpers.
 */

export const WRITING_EVALUATION_MODES = [
  { id: 'beginner', label: 'Beginner' },
  { id: 'normal', label: 'Normal' },
  { id: 'toefl_reviewer', label: 'TOEFL reviewer' },
]

export const WRITING_LEVELS = [
  { id: 'B1', label: 'B1 support' },
  { id: 'normal', label: 'Normal' },
  { id: 'professional', label: 'Professional / academic' },
]

export const WRITING_MODES = [
  { id: 'toefl_writing', label: 'TOEFL writing', track: 'toefl_writing' },
  { id: 'academic_paragraph', label: 'Academic paragraph', track: 'writing_coach' },
  { id: 'opinion_paragraph', label: 'Opinion paragraph', track: 'writing_coach' },
  { id: 'email_writing', label: 'Email writing', track: 'writing_coach' },
  { id: 'summary_writing', label: 'Summary writing', track: 'writing_coach' },
  { id: 'article_response', label: 'Article response', track: 'writing_coach' },
  { id: 'compare_contrast', label: 'Compare and contrast', track: 'writing_coach' },
  { id: 'problem_solution', label: 'Problem and solution', track: 'writing_coach' },
]

const LEVEL_ADJUSTMENTS = {
  B1: { wordScale: 0.75, timeScale: 0.7 },
  normal: { wordScale: 1, timeScale: 1 },
  professional: { wordScale: 1.15, timeScale: 1.1 },
}

const MODE_DEFAULTS = {
  toefl_writing: {
    wordMin: 180,
    wordMax: 250,
    timeMinutes: 30,
    goal: 'State your opinion, give two reasons with examples, and conclude clearly.',
    planning: [
      'Topic sentence / opinion',
      'Reason 1',
      'Example',
      'Reason 2',
      'Example',
      'Conclusion',
    ],
  },
  academic_paragraph: {
    wordMin: 150,
    wordMax: 200,
    timeMinutes: 15,
    goal: 'Present one main idea with evidence and academic tone.',
    planning: ['Topic sentence', 'Supporting point 1', 'Evidence', 'Supporting point 2', 'Conclusion'],
  },
  opinion_paragraph: {
    wordMin: 120,
    wordMax: 150,
    timeMinutes: 10,
    goal: 'Give your opinion, explain two reasons, and include examples.',
    planning: ['Opinion', 'Reason 1', 'Example', 'Reason 2', 'Conclusion'],
  },
  email_writing: {
    wordMin: 100,
    wordMax: 150,
    timeMinutes: 10,
    goal: 'Write a clear, polite email with purpose, details, and closing.',
    planning: ['Greeting', 'Purpose', 'Details', 'Request/action', 'Closing'],
  },
  summary_writing: {
    wordMin: 80,
    wordMax: 120,
    timeMinutes: 10,
    goal: 'Summarize the main idea in your own words without adding new opinions.',
    planning: ['Main idea', 'Key detail 1', 'Key detail 2', 'Brief conclusion'],
  },
  article_response: {
    wordMin: 150,
    wordMax: 200,
    timeMinutes: 15,
    goal: 'Summarize the article, react to the main idea, and support your view.',
    planning: ['Summary', 'Main idea', 'Your reaction', 'Support/example', 'Conclusion'],
  },
  compare_contrast: {
    wordMin: 150,
    wordMax: 200,
    timeMinutes: 15,
    goal: 'Compare two ideas with clear similarities and differences.',
    planning: ['Introduction', 'Similarity', 'Difference 1', 'Difference 2', 'Conclusion'],
  },
  problem_solution: {
    wordMin: 150,
    wordMax: 200,
    timeMinutes: 15,
    goal: 'Describe a problem and propose a practical solution with support.',
    planning: ['Problem', 'Why it matters', 'Solution', 'Example', 'Conclusion'],
  },
}

const SENTENCE_STARTERS = {
  B1: [
    'In my opinion, ...',
    'One reason is that ...',
    'For example, ...',
    'Another reason is ...',
    'As a result, ...',
    'I think ... because ...',
  ],
  normal: [
    'In my opinion, ...',
    'One reason is that ...',
    'For example, ...',
    'Another reason is ...',
    'As a result, ...',
    'This shows that ...',
    'However, ...',
  ],
  professional: [
    'From an academic perspective, ...',
    'One compelling reason is that ...',
    'For instance, ...',
    'Furthermore, ...',
    'Consequently, ...',
    'This demonstrates that ...',
    'Nevertheless, ...',
  ],
}

const PROMPT_BANK = {
  toefl_writing: [
    'What is your favorite season of the year? Explain why you like it and what activities you enjoy during that season.',
    'Do you agree or disagree: It is better to study alone than in a group? Use specific reasons and examples.',
    'Some people prefer living in a big city. Others prefer living in a small town. Which do you prefer and why?',
    'Do you agree that technology has made communication easier? Support your answer with examples.',
  ],
  academic_paragraph: [
    'Explain one important concept in your field and why it matters for future research.',
    'Describe a scientific method you use and how it helps you answer research questions.',
  ],
  opinion_paragraph: [
    'Do you think online learning is as effective as classroom learning? Explain your view.',
    'Should students have part-time jobs while studying? Give your opinion with reasons.',
  ],
  email_writing: [
    'Write an email to your professor asking for a one-week extension on an assignment. Explain your reason politely.',
    'Write an email to a colleague confirming a meeting time and agenda.',
  ],
  summary_writing: [
    'Summarize the main idea of a recent article or lecture you read in 100–120 words.',
  ],
  article_response: [
    'Read the idea below and respond: "Remote work improves productivity for many employees." Do you agree?',
  ],
  compare_contrast: [
    'Compare studying in your home country with studying in the United States.',
  ],
  problem_solution: [
    'Describe a common problem for international students and suggest one practical solution.',
  ],
}

function scaleWords(min, max, level) {
  const scale = LEVEL_ADJUSTMENTS[level]?.wordScale ?? 1
  if (level === 'B1') {
    return {
      wordMin: Math.max(60, Math.round(min * scale)),
      wordMax: Math.max(80, Math.round(max * scale)),
    }
  }
  if (level === 'professional') {
    return {
      wordMin: Math.round(min * scale),
      wordMax: Math.round(max * scale),
    }
  }
  return { wordMin: min, wordMax: max }
}

function scaleTime(minutes, level) {
  const scale = LEVEL_ADJUSTMENTS[level]?.timeScale ?? 1
  if (level === 'B1') {
    if (minutes >= 30) return 10
    return Math.max(5, Math.round(minutes * scale))
  }
  return Math.max(5, Math.round(minutes * scale))
}

export function getModeConfig(modeId, level = 'normal') {
  const base = MODE_DEFAULTS[modeId] || MODE_DEFAULTS.opinion_paragraph
  const { wordMin, wordMax } = scaleWords(base.wordMin, base.wordMax, level)
  const timeMinutes = scaleTime(base.timeMinutes, level)

  if (modeId === 'toefl_writing' && level === 'B1') {
    return {
      ...base,
      wordMin: 120,
      wordMax: 150,
      timeMinutes: 10,
      goal: base.goal,
      planning: base.planning,
      sentenceStarters: SENTENCE_STARTERS.B1,
    }
  }

  return {
    ...base,
    wordMin,
    wordMax,
    timeMinutes,
    planning: base.planning,
    sentenceStarters: SENTENCE_STARTERS[level] || SENTENCE_STARTERS.normal,
  }
}

export function generateWritingPrompt(modeId, level = 'normal') {
  const config = getModeConfig(modeId, level)
  const bank = PROMPT_BANK[modeId] || PROMPT_BANK.opinion_paragraph
  const promptText = bank[Math.floor(Math.random() * bank.length)]

  return {
    id: `${modeId}_${level}_${Date.now()}`,
    mode: modeId,
    level,
    track: WRITING_MODES.find((m) => m.id === modeId)?.track || 'writing_coach',
    prompt: promptText,
    wordMin: config.wordMin,
    wordMax: config.wordMax,
    timeMinutes: config.timeMinutes,
    goal: config.goal,
    planning: config.planning,
    sentenceStarters: config.sentenceStarters,
  }
}

export function buildWritingEvaluationMessage({
  task,
  draft,
  wordCount,
  articleText = '',
  evaluationMode = 'normal',
}) {
  const lines = [
    `User mode: ${evaluationMode}`,
    `Writing level: ${task.level}`,
    `Writing type: ${task.mode}`,
    `Prompt: ${task.prompt}`,
    `Target word count: ${task.wordMin}–${task.wordMax}`,
    `Student word count: ${wordCount}`,
    `Recommended time: ${task.timeMinutes} minutes`,
    `Writing goal: ${task.goal}`,
  ]

  if (wordCount < task.wordMin) {
    lines.push('Note: Answer is shorter than target range.')
  } else if (wordCount > task.wordMax) {
    lines.push('Note: Answer is longer than target range.')
  }

  if (articleText.trim()) {
    lines.push('', '[Source text]', articleText.trim())
  }

  lines.push('', 'Student answer:', draft.trim())
  lines.push('', 'Return JSON only matching the required schema.')
  return lines.join('\n')
}

export function buildSampleAnswerMessage(task) {
  return `[Sample answer request]

Level: ${task.level}
Mode: ${task.mode}
Prompt: ${task.prompt}
Target word count: ${task.wordMin}–${task.wordMax}

Write a strong but realistic sample answer by an English learner at this level.
Do NOT make it sound like a professional native writer.
Use clear organization, natural vocabulary, and a few advanced but learnable phrases.
Return Markdown with:
## Sample answer
## Why this answer is good
## Useful phrases from the sample`
}

export function countWords(text) {
  if (!text?.trim()) return 0
  return text.trim().split(/\s+/).filter(Boolean).length
}

export function wordCountStatus(count, min, max) {
  if (count === 0) return { status: 'empty', message: '' }
  if (count < min) return { status: 'short', message: 'Add more details.' }
  if (count > max) return { status: 'long', message: 'Try to be more concise.' }
  return { status: 'good', message: 'Good length.' }
}

export function getTrackForMode(modeId) {
  return WRITING_MODES.find((m) => m.id === modeId)?.track || 'writing_coach'
}
