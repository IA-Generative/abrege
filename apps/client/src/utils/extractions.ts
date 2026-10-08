export interface TaskExtractionState {
  parameters?: {
    extract_qa?: boolean
    extract_entities?: boolean
    extract_chunks?: boolean
    classify_topics?: boolean
  } | null
  qa_entities_status?: string | null
  relationships_status?: string | null
  topics_status?: string | null
}

const SETTLED = new Set(['completed', 'failed'])

const isSettled = (status?: string | null) => SETTLED.has(status ?? '')

/**
 * True while a requested side extraction (Q&A, entities, relationships, chunks, topics) has not
 * reached a final state. A status that is still `null` counts as pending: right after the summary
 * completes the worker may not have written it yet.
 */
export function hasPendingExtractions (task: TaskExtractionState): boolean {
  const params = task.parameters ?? {}

  if ((params.extract_qa || params.extract_entities || params.extract_chunks) && !isSettled(task.qa_entities_status)) {
    return true
  }
  // The global relationships pass only runs once Q&A/entities/chunks completed successfully.
  if (params.extract_entities && task.qa_entities_status === 'completed' && !isSettled(task.relationships_status)) {
    return true
  }
  return !!params.classify_topics && !isSettled(task.topics_status)
}
