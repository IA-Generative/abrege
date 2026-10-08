import { describe, expect, it } from 'vitest'
import { hasPendingExtractions } from './extractions'

describe('hasPendingExtractions', () => {
  it('is false when no extraction was requested', () => {
    expect(hasPendingExtractions({ parameters: {} })).toBe(false)
    expect(hasPendingExtractions({ parameters: null })).toBe(false)
    expect(hasPendingExtractions({})).toBe(false)
  })

  it('is true while a requested extraction has no status yet', () => {
    expect(hasPendingExtractions({ parameters: { extract_qa: true } })).toBe(true)
    expect(hasPendingExtractions({ parameters: { classify_topics: true } })).toBe(true)
  })

  it('is true while an extraction is in progress or pending', () => {
    expect(hasPendingExtractions({ parameters: { extract_chunks: true }, qa_entities_status: 'in_progress' })).toBe(true)
    expect(hasPendingExtractions({ parameters: { classify_topics: true }, topics_status: 'pending' })).toBe(true)
  })

  it('is false once every requested extraction is completed or failed', () => {
    expect(hasPendingExtractions({
      parameters: { extract_qa: true, extract_entities: true, classify_topics: true },
      qa_entities_status: 'completed',
      relationships_status: 'completed',
      topics_status: 'failed',
    })).toBe(false)
  })

  it('waits for the relationships pass only after entities completed', () => {
    const base = { parameters: { extract_entities: true } }
    expect(hasPendingExtractions({ ...base, qa_entities_status: 'completed', relationships_status: 'pending' })).toBe(true)
    expect(hasPendingExtractions({ ...base, qa_entities_status: 'completed', relationships_status: null })).toBe(true)
    // entities failed: the relationships pass never runs, do not wait for it forever
    expect(hasPendingExtractions({ ...base, qa_entities_status: 'failed', relationships_status: null })).toBe(false)
  })

  it('ignores the statuses of extractions that were not requested', () => {
    expect(hasPendingExtractions({
      parameters: { extract_qa: true },
      qa_entities_status: 'completed',
      topics_status: 'pending',
    })).toBe(false)
  })
})
