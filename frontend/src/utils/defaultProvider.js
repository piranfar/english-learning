export const DEFAULT_AI_PROVIDER = 'ollama'
export const DEFAULT_STT_PROVIDER = 'openai_whisper'

export function uniqueProviders(prompts, filter = () => true) {
  return [...new Set(
    (prompts || []).filter(filter).map((prompt) => prompt.provider).filter(Boolean),
  )]
}

export function pickDefaultProvider(prompts, filter = () => true, fallback = DEFAULT_AI_PROVIDER) {
  const options = uniqueProviders(prompts, filter)
  return options[0] || fallback
}
