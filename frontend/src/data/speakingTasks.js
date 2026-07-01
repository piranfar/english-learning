/**
 * American English speaking task bank and generators.
 */

export const SPEAKING_LEVELS = [
  { id: 'B1', label: 'B1 / B-level support' },
  { id: 'normal', label: 'B2 / intermediate' },
  { id: 'professional', label: 'Academic / B2+' },
]

export const EVALUATION_MODES = [
  { id: 'beginner', label: 'Beginner' },
  { id: 'normal', label: 'Normal' },
  { id: 'advanced', label: 'Advanced / TOEFL reviewer' },
]

export const PRACTICE_TYPES = [
  { id: 'daily_conversation', label: 'Daily conversation' },
  { id: 'interview_practice', label: 'Interview practice' },
  { id: 'talk_about_article', label: 'Talk about an article' },
  { id: 'talk_about_picture', label: 'Talk about a picture' },
  { id: 'opinion_agree_disagree', label: 'Opinion: agree or disagree' },
  { id: 'one_minute_talk', label: 'One-minute talk' },
  { id: 'situation_response', label: 'Situation response' },
  { id: 'follow_up_conversation', label: 'Follow-up conversation' },
  { id: 'toefl_speaking', label: 'TOEFL-style speaking' },
  { id: 'academic_presentation', label: 'Academic presentation' },
  { id: 'job_phd_interview', label: 'Job / PhD interview' },
]

const LEVEL_TIMING = {
  B1: { prep: 20, speak: 45 },
  normal: { prep: 25, speak: 60 },
  professional: { prep: 30, speak: 90 },
}

const LEVEL_FOCUS = {
  B1: ['basic grammar', 'clear pronunciation', 'simple connectors', 'confidence'],
  normal: ['fluency', 'grammar', 'vocabulary', 'pronunciation clarity'],
  professional: [
    'professional phrasing',
    'academic vocabulary',
    'structure',
    'concise delivery',
  ],
}

const TASK_TEMPLATES = [
  // Daily conversation
  {
    type: 'daily_conversation',
    level: 'B1',
    title: 'Talk about your daily routine',
    prompt: 'Talk about your daily routine for 45 seconds.',
    support_phrases: ['I usually...', 'In the morning...', 'After that...', 'At night...'],
  },
  {
    type: 'daily_conversation',
    level: 'B1',
    title: 'Describe your weekend',
    prompt: 'Describe what you did last weekend in about 45 seconds.',
    support_phrases: ['On Saturday...', 'I went to...', 'It was...', 'I enjoyed...'],
  },
  {
    type: 'daily_conversation',
    level: 'normal',
    title: 'Introduce yourself',
    prompt: 'Introduce yourself as if you just moved to Jersey City. Speak for about one minute.',
    support_phrases: ['My name is...', 'I moved here because...', 'I work/study...'],
  },
  {
    type: 'daily_conversation',
    level: 'normal',
    title: 'Talk about your favorite food',
    prompt: 'Explain your favorite food and why you like it. Speak for one minute.',
    support_phrases: ['My favorite food is...', 'I like it because...', 'I often eat it when...'],
  },
  {
    type: 'daily_conversation',
    level: 'professional',
    title: 'Describe your current role',
    prompt: 'Briefly describe your current work or study role and main responsibilities (90 seconds).',
    support_phrases: ['I currently work as...', 'My main responsibilities include...'],
  },
  // Interview
  {
    type: 'interview_practice',
    level: 'B1',
    title: 'Tell me about yourself',
    prompt: 'Answer: Tell me about yourself. Keep it simple and clear (45 seconds).',
    support_phrases: ['I am from...', 'I study/work...', 'I am interested in...'],
  },
  {
    type: 'interview_practice',
    level: 'normal',
    title: 'Why this program?',
    prompt: 'Answer: Why do you want to join this program or university?',
    support_phrases: ['I am interested in...', 'This program will help me...'],
  },
  {
    type: 'job_phd_interview',
    level: 'professional',
    title: 'Research background',
    prompt:
      'Summarize your research background and explain why you are interested in this PhD program (90 seconds).',
    support_phrases: [
      'My research background is mainly in...',
      'I developed experience in...',
      'I am particularly interested in...',
    ],
  },
  {
    type: 'job_phd_interview',
    level: 'professional',
    title: 'Why should we accept you?',
    prompt: 'Answer: Why should we accept you into this program or position?',
    support_phrases: ['I bring...', 'My strengths include...', 'I can contribute by...'],
  },
  // Opinion
  {
    type: 'opinion_agree_disagree',
    level: 'B1',
    title: 'Online learning',
    prompt:
      'Do you agree that online learning is better than classroom learning? Give your opinion with one reason and an example.',
    support_phrases: ['I agree/disagree because...', 'For example...', 'In conclusion...'],
  },
  {
    type: 'opinion_agree_disagree',
    level: 'normal',
    title: 'AI in education',
    prompt:
      'Do you agree that AI will improve education? State your opinion, two reasons, an example, and a short conclusion.',
    support_phrases: ['I believe...', 'First...', 'Second...', 'For instance...'],
  },
  {
    type: 'opinion_agree_disagree',
    level: 'professional',
    title: 'Work while studying',
    prompt:
      'Should graduate students work while studying? Present a clear academic-style argument in 90 seconds.',
    support_phrases: ['From an academic perspective...', 'One compelling reason is...'],
  },
  // One minute
  {
    type: 'one_minute_talk',
    level: 'B1',
    title: 'A skill to improve',
    prompt: 'Describe an important skill you want to improve. Speak for one minute.',
    support_phrases: ['One skill I want to improve is...', 'I want to improve it because...'],
  },
  {
    type: 'one_minute_talk',
    level: 'normal',
    title: 'A person who influenced you',
    prompt: 'Talk about a person who influenced you. Speak for one minute.',
    support_phrases: ['The person who influenced me is...', 'They taught me...'],
  },
  {
    type: 'one_minute_talk',
    level: 'professional',
    title: 'A problem in your field',
    prompt: 'Explain an important problem in your field and why it matters (90 seconds).',
    support_phrases: ['A key challenge in my field is...', 'This matters because...'],
  },
  // Situation
  {
    type: 'situation_response',
    level: 'B1',
    title: 'Late for a meeting',
    prompt: 'You are late for a meeting. Apologize and explain briefly.',
    support_phrases: ['I am sorry I am late...', 'The reason is...', 'It will not happen again...'],
  },
  {
    type: 'situation_response',
    level: 'normal',
    title: 'Ask professor for extension',
    prompt: 'You need to ask your professor for more time on an assignment. What would you say?',
    support_phrases: ['Professor..., I am writing/speaking because...', 'Would it be possible to...'],
  },
  {
    type: 'situation_response',
    level: 'professional',
    title: 'Polite disagreement',
    prompt: 'You disagree politely with a colleague about a project deadline. Respond professionally.',
    support_phrases: ['I understand your point, however...', 'Could we consider...'],
  },
  // Picture (text scene)
  {
    type: 'talk_about_picture',
    level: 'B1',
    title: 'Park scene',
    prompt:
      'Describe this scene: A sunny park with families, children playing, and people walking dogs. Say what you see and what may be happening.',
    support_phrases: ['I can see...', 'Maybe they are...', 'It looks like...'],
  },
  {
    type: 'talk_about_picture',
    level: 'normal',
    title: 'Busy café',
    prompt:
      'Describe this scene: A busy café in a city. Students with laptops, friends talking, and a barista making coffee. Make a prediction about what happens next.',
    support_phrases: ['In the foreground...', 'It seems that...', 'I think next...'],
  },
  // Academic / TOEFL
  {
    type: 'academic_presentation',
    level: 'professional',
    title: 'Mini presentation',
    prompt: 'Give a 90-second mini presentation explaining a recent topic you studied in your field.',
    support_phrases: ['Today I will explain...', 'The main point is...', 'In summary...'],
  },
  {
    type: 'toefl_speaking',
    level: 'normal',
    title: 'TOEFL independent-style',
    prompt:
      'Some people prefer to study in groups. Others prefer to study alone. Which do you prefer and why?',
    support_phrases: ['I prefer...', 'One reason is...', 'Another reason is...'],
  },
  {
    type: 'follow_up_conversation',
    level: 'normal',
    title: 'Follow-up practice',
    prompt: 'Answer the question naturally. After your answer, the coach will ask one follow-up question.',
    support_phrases: ['I think...', 'The main reason is...', 'For example...'],
  },
  {
    type: 'talk_about_article',
    level: 'normal',
    title: 'Article summary',
    prompt:
      'Summarize the article you pasted. Explain the main idea, one key detail, and your opinion.',
    support_phrases: ['The main idea is...', 'One important detail is...', 'In my opinion...'],
  },
]

function pickRandom(items) {
  return items[Math.floor(Math.random() * items.length)]
}

export function generateTask(practiceType, level, { articleText = '' } = {}) {
  const timing = LEVEL_TIMING[level] || LEVEL_TIMING.normal
  const focus = LEVEL_FOCUS[level] || LEVEL_FOCUS.normal

  let candidates = TASK_TEMPLATES.filter(
    (t) => t.type === practiceType && t.level === level,
  )
  if (candidates.length === 0) {
    candidates = TASK_TEMPLATES.filter((t) => t.type === practiceType)
  }
  if (candidates.length === 0) {
    candidates = TASK_TEMPLATES.filter((t) => t.level === level)
  }
  const base = pickRandom(candidates.length ? candidates : TASK_TEMPLATES)

  const id = `${base.type}_${level}_${Date.now()}`
  const task = {
    id,
    type: practiceType,
    level,
    title: base.title,
    prompt: base.prompt,
    prep_seconds: practiceType === 'one_minute_talk' ? 20 : timing.prep,
    speak_seconds: practiceType === 'one_minute_talk' ? 60 : timing.speak,
    support_phrases: base.support_phrases || [],
    evaluation_focus: focus,
    goals: [
      'Speak clearly in American English',
      'Complete the task',
      'Use natural grammar and vocabulary',
    ],
    article_text: practiceType === 'talk_about_article' ? articleText : '',
  }

  if (practiceType === 'talk_about_article' && !articleText.trim()) {
    task.prompt =
      'Paste an article below, then summarize it, explain the main idea, and give your opinion.'
  }

  return task
}

export function buildSpeakingEvaluationMessage({
  task,
  answer,
  inputMode = 'voice',
  followUp = false,
  previousAnswer = '',
  evaluationMode = 'normal',
}) {
  const lines = [
    `User mode: ${evaluationMode}`,
    `Speaking level: ${task.level}`,
    `Practice type: ${task.type}`,
    `Task title: ${task.title}`,
    `Speaking task prompt: ${task.prompt}`,
    `Input mode: ${inputMode}`,
    `Expected speaking time: ${task.speak_seconds} seconds`,
    `Preparation time: ${task.prep_seconds} seconds`,
    `Evaluation focus: ${(task.evaluation_focus || []).join(', ')}`,
  ]

  if (inputMode === 'typed') {
    lines.push('Note: Typed input only — pronunciation and intonation scoring is limited.')
  } else {
    lines.push('Note: Response was transcribed from audio. Delivery scoring is transcript-based.')
  }

  if (task.article_text?.trim()) {
    lines.push('', 'Article context:', task.article_text.trim())
  }

  if (followUp) {
    lines.push('', '[Follow-up turn]', `Previous answer: ${previousAnswer}`, '', 'Student follow-up answer:', answer)
  } else {
    lines.push('', 'Transcript:', answer)
  }

  lines.push('', 'Return JSON only matching the required schema.')
  return lines.join('\n')
}

export function getTrackForPracticeType(practiceType) {
  return practiceType === 'toefl_speaking' ? 'toefl_speaking' : 'speaking_coach'
}
