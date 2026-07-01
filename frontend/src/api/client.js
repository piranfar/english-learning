const API_BASE = '/api'

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^|;)\\s*${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

let csrfReady = false

export async function ensureCsrf() {
  if (csrfReady && getCookie('csrftoken')) {
    return
  }
  await fetch(`${API_BASE}/csrf/`, { credentials: 'include' })
  csrfReady = true
}

async function apiRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = { ...(options.headers || {}) }

  if (options.json !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    await ensureCsrf()
    const token = getCookie('csrftoken')
    if (token) {
      headers['X-CSRFToken'] = token
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
    body:
      options.json !== undefined
        ? JSON.stringify(options.json)
        : options.body,
  })

  const contentType = response.headers.get('content-type') || ''
  let data = null
  if (contentType.includes('application/json')) {
    data = await response.json()
  } else if (!response.ok) {
    data = { detail: `Request failed (${response.status})` }
  }

  if (!response.ok) {
    const message =
      data?.detail ||
      (typeof data === 'object' && data !== null
        ? Object.entries(data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ')
        : null) ||
      `Request failed (${response.status})`
    throw new Error(message)
  }

  return data
}

export function getMe() {
  return apiRequest('/auth/me/')
}

export async function login(username, password) {
  await ensureCsrf()
  return apiRequest('/auth/login/', {
    method: 'POST',
    json: { username, password },
  })
}

export async function logout() {
  return apiRequest('/auth/logout/', { method: 'POST', json: {} })
}

export function getDashboard() {
  return apiRequest('/dashboard/')
}

export function getReadiness() {
  return apiRequest('/readiness/')
}

export function getPrompts() {
  return apiRequest('/prompts/')
}

export function getAdminPrompts() {
  return apiRequest('/admin/prompts/')
}

export async function updateAdminPrompt(promptId, payload) {
  return apiRequest(`/admin/prompts/${promptId}/`, {
    method: 'PATCH',
    json: payload,
  })
}

export async function resetAdminPrompt(promptId) {
  return apiRequest(`/admin/prompts/${promptId}/reset/`, {
    method: 'POST',
    json: {},
  })
}

export function getMistakes() {
  return apiRequest('/mistakes/')
}

export async function recordVocabQuizMistake({
  word,
  wrongAnswer = '',
  meaningEn = '',
  meaningFa = '',
  example = '',
  quizMode = '',
}) {
  return apiRequest('/mistakes/vocab/', {
    method: 'POST',
    json: {
      word,
      wrong_answer: wrongAnswer,
      meaning_en: meaningEn,
      meaning_fa: meaningFa,
      example,
      quiz_mode: quizMode,
    },
  })
}

export function getTodayPlan() {
  return apiRequest('/plan/today/')
}

export async function generateTodayPlan() {
  return apiRequest('/plan/today/generate/', {
    method: 'POST',
    json: {},
  })
}

export function getVocabSeeds({
  cefrLevel = '',
  category = '',
  search = '',
  approved = '',
  limit = '',
  random = false,
} = {}) {
  const params = new URLSearchParams()
  if (cefrLevel) params.set('cefr_level', cefrLevel)
  if (category) params.set('category', category)
  if (search) params.set('search', search)
  if (approved !== '') params.set('approved', String(approved))
  if (limit) params.set('limit', String(limit))
  if (random) params.set('random', 'true')
  const query = params.toString()
  return apiRequest(`/vocab/seeds/${query ? `?${query}` : ''}`)
}

export function getVocabCategoryStats() {
  return apiRequest('/vocab/category-stats/')
}

export async function addRandomFromCategory({ category, count = 10, cefrLevel = '' }) {
  return apiRequest('/vocab/add-random-from-category/', {
    method: 'POST',
    json: {
      category,
      count,
      ...(cefrLevel ? { cefr_level: cefrLevel } : {}),
    },
  })
}

export function getVocabCategories() {
  return apiRequest('/vocab/categories/')
}

export function getDueVocab() {
  return apiRequest('/vocab/due/')
}

export async function reviewVocabItem(itemId, quality) {
  return apiRequest(`/vocab/${itemId}/review/`, {
    method: 'POST',
    json: { quality },
  })
}

export async function addVocabFromSeed(seedId) {
  return apiRequest(`/vocab/from-seed/${seedId}/`, {
    method: 'POST',
    json: {},
  })
}

/** @deprecated Use addVocabFromSeed(seedId) */
export async function addVocabFromSeedLegacy(seed) {
  return addVocabFromSeed(seed.id)
}

export async function updatePlanItem(itemId, completed) {
  return apiRequest('/plan/today/', {
    method: 'POST',
    json: { item_id: itemId, completed },
  })
}

export async function sendChatMessage(payload) {
  return apiRequest('/chat/', {
    method: 'POST',
    json: payload,
  })
}

export async function submitWritingEdit({
  text,
  editStrength = 'standard',
  targetStyle = 'simple_american_english',
  languageLevel = 'normal',
  aiProvider,
}) {
  return apiRequest('/writing/edit/', {
    method: 'POST',
    json: {
      text,
      edit_strength: editStrength,
      target_style: targetStyle,
      language_level: languageLevel,
      ai_provider: aiProvider,
    },
  })
}

export async function compareWritingRevision({
  originalAnswer,
  revisedAnswer,
  prompt = '',
  provider,
}) {
  return apiRequest('/writing/revision/compare/', {
    method: 'POST',
    json: {
      original_answer: originalAnswer,
      revised_answer: revisedAnswer,
      prompt,
      provider,
    },
  })
}

export async function generateWritingEditPractice({
  targetStyle = 'simple_american_english',
  languageLevel = 'normal',
  aiProvider,
}) {
  return apiRequest('/writing/edit/generate/', {
    method: 'POST',
    json: {
      target_style: targetStyle,
      language_level: languageLevel,
      ai_provider: aiProvider,
    },
  })
}

export async function generateParaphrasePractice({
  targetLevel = 'simple_american_english',
  difficulty = 'easy',
  textType = 'one_sentence',
  languageLevel = 'normal',
  aiProvider,
}) {
  return apiRequest('/writing/paraphrasing/generate/', {
    method: 'POST',
    json: {
      target_level: targetLevel,
      difficulty,
      text_type: textType,
      language_level: languageLevel,
      ai_provider: aiProvider,
    },
  })
}

export async function checkParaphrase({
  targetLevel = 'simple_american_english',
  languageLevel = 'normal',
  originalText,
  learnerParaphrase,
  aiProvider,
}) {
  return apiRequest('/writing/paraphrasing/check/', {
    method: 'POST',
    json: {
      target_level: targetLevel,
      language_level: languageLevel,
      original_text: originalText,
      learner_paraphrase: learnerParaphrase,
      ai_provider: aiProvider,
    },
  })
}

export function getLessonRecommendation() {
  return apiRequest('/lesson/recommendation/')
}

export function getLessonTopics() {
  return apiRequest('/lesson/topics/')
}

export async function startRecommendedLesson(topicId, provider = 'ollama') {
  return apiRequest('/lesson/start-recommended/', {
    method: 'POST',
    json: { topic_id: topicId, provider },
  })
}

export async function completeLesson(topicId, score = 80, notes = '') {
  return apiRequest('/lesson/complete/', {
    method: 'POST',
    json: { topic_id: topicId, score, notes },
  })
}

function appendAudioToForm(form, audioBlob, fieldName = 'audio') {
  const filename =
    audioBlob instanceof File
      ? audioBlob.name
      : `recording.${(audioBlob.type || 'audio/webm').split('/').pop() || 'webm'}`
  form.append(fieldName, audioBlob, filename)
}

export async function transcribeAudio(audioBlob, provider = '') {
  const form = new FormData()
  appendAudioToForm(form, audioBlob)
  if (provider) {
    form.append('provider', provider)
  }
  const data = await postForm('/transcribe/', form)
  return data.transcript || data.text || ''
}

export async function submitSpeakingAudio({
  audioBlob,
  scenario,
  sessionId,
  provider,
  level = '',
  evaluationMode = '',
  taskType = '',
  taskTitle = '',
  taskPrompt = '',
  articleText = '',
  evaluationFocus = '',
  prepTime,
  speakTime,
  duration,
}) {
  const form = new FormData()
  appendAudioToForm(form, audioBlob)
  form.append('scenario', scenario)
  if (level) form.append('level', level)
  if (evaluationMode) form.append('evaluation_mode', evaluationMode)
  if (taskType) form.append('task_type', taskType)
  if (taskTitle) form.append('task_title', taskTitle)
  if (taskPrompt) form.append('task_prompt', taskPrompt)
  if (articleText) form.append('article_text', articleText)
  if (evaluationFocus) form.append('evaluation_focus', evaluationFocus)
  if (prepTime != null) form.append('prep_time', String(prepTime))
  if (speakTime != null) form.append('speak_time', String(speakTime))
  if (duration != null) form.append('duration', String(duration))
  if (sessionId) {
    form.append('session_id', String(sessionId))
  }
  if (provider) {
    form.append('provider', provider)
  }
  return postForm('/speaking/attempt-audio/', form)
}

export function getShadowingItems() {
  return apiRequest('/shadowing/items/')
}

export async function submitShadowingText(itemId, transcript) {
  return apiRequest(`/shadowing/items/${itemId}/attempt/`, {
    method: 'POST',
    json: { transcript },
  })
}

export async function submitShadowingAudio(itemId, audioBlob, durationSeconds) {
  const form = new FormData()
  appendAudioToForm(form, audioBlob)
  if (durationSeconds != null) {
    form.append('duration', String(durationSeconds))
  }
  return postForm(`/shadowing/items/${itemId}/attempt-audio/`, form)
}

export async function postForm(path, formData) {
  await ensureCsrf()
  const headers = {}
  const token = getCookie('csrftoken')
  if (token) {
    headers['X-CSRFToken'] = token
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
    headers,
  })

  const contentType = response.headers.get('content-type') || ''
  let data = null
  if (contentType.includes('application/json')) {
    data = await response.json()
  }

  if (!response.ok) {
    const message = data?.detail || `Request failed (${response.status})`
    throw new Error(message)
  }

  return data
}

export { apiRequest }
