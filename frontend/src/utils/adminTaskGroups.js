/**
 * Group AI task types by learner-facing skill area for admin UI.
 */

export const TASK_GROUP_ORDER = [
  'Grammar & lessons',
  'Reading',
  'Listening',
  'Speaking',
  'Writing',
  'Vocabulary',
  'TOEFL',
  'Other',
]

const TASK_TYPE_GROUPS = {
  grammar_coach: 'Grammar & lessons',
  lesson_recommendation: 'Grammar & lessons',
  reading_coach: 'Reading',
  reading_quiz: 'Reading',
  reading_generate: 'Reading',
  reading_simulation: 'Reading',
  listening_coach: 'Listening',
  listening_quiz: 'Listening',
  listening_practice_generate: 'Listening',
  speaking_coach: 'Speaking',
  shadowing_coach: 'Speaking',
  writing_coach: 'Writing',
  writing_edit_coach: 'Writing',
  writing_edit_generate: 'Writing',
  writing_paraphrase_coach: 'Writing',
  writing_paraphrase_generate: 'Writing',
  writing_paraphrase_check: 'Writing',
  writing_lesson_coach: 'Writing',
  writing_prompt_outline_coach: 'Writing',
  sentence_builder_coach: 'Writing',
  paragraph_builder_coach: 'Writing',
  writing_revision_compare: 'Writing',
  vocab_builder: 'Vocabulary',
  toefl_speaking: 'TOEFL',
  toefl_writing: 'TOEFL',
}

export const TASK_TYPE_LABELS = {
  grammar_coach: 'Grammar coach (Lesson chat)',
  lesson_recommendation: 'Lesson recommendation',
  reading_coach: 'Reading coach',
  reading_quiz: 'Reading quiz',
  reading_generate: 'Reading generation',
  reading_simulation: 'Reading simulation',
  listening_coach: 'Listening coach',
  listening_quiz: 'Listening quiz',
  listening_practice_generate: 'Listening practice generation',
  speaking_coach: 'Speaking coach',
  shadowing_coach: 'Shadowing coach',
  writing_coach: 'Writing coach',
  writing_edit_coach: 'Writing edit',
  writing_edit_generate: 'Writing edit generate',
  writing_paraphrase_coach: 'Paraphrase coach',
  writing_paraphrase_generate: 'Paraphrase generate',
  writing_paraphrase_check: 'Paraphrase check',
  writing_lesson_coach: 'Writing lessons',
  writing_prompt_outline_coach: 'Writing outline',
  sentence_builder_coach: 'Sentence builder',
  paragraph_builder_coach: 'Paragraph builder',
  writing_revision_compare: 'Writing revision compare',
  vocab_builder: 'Vocabulary builder',
  toefl_speaking: 'TOEFL speaking',
  toefl_writing: 'TOEFL writing',
}

export function taskGroupForType(taskType) {
  return TASK_TYPE_GROUPS[taskType] || 'Other'
}

export function taskLabelForType(taskType) {
  return TASK_TYPE_LABELS[taskType] || taskType
}

export function groupPromptsBySkill(prompts) {
  const grouped = new Map()
  for (const group of TASK_GROUP_ORDER) {
    grouped.set(group, [])
  }
  for (const prompt of prompts) {
    const group = taskGroupForType(prompt.task_type)
    if (!grouped.has(group)) grouped.set(group, [])
    grouped.get(group).push(prompt)
  }
  return TASK_GROUP_ORDER.map((group) => ({
    group,
    prompts: (grouped.get(group) || []).sort((a, b) => {
      const labelA = taskLabelForType(a.task_type)
      const labelB = taskLabelForType(b.task_type)
      if (labelA !== labelB) return labelA.localeCompare(labelB)
      return a.provider.localeCompare(b.provider)
    }),
  })).filter((entry) => entry.prompts.length > 0)
}
