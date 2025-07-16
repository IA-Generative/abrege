export interface IResumeTask {
  id: string
  user_id: string
  type: string
  status: string
  percentage: number
  input: {
    type: 'url' | 'text' | string
    created_at: number
    extras: {
      prompt: string | null
    }
    text: string
  }
  output: {
    type: string
    created_at: number
    model_name: string
    model_version: string
    updated_at: number
    texts_found: string[]
    percentage: number
    extras: Record<string, unknown>
    summary: string
    word_count: number
  }
  parameters: {
    temperature: number
    language: string
    size: number
    extras: Record<string, unknown>
    method: string
    custom_prompt: string
  }
  position: number | null
  created_at: number
  updated_at: number
  extras: Record<string, unknown>

}
