import { describe, expect, it } from 'vitest'
import { describeError } from './error-codes'

describe('describeError', () => {
  it('returns nothing without a code', () => {
    expect(describeError(null)).toBeUndefined()
    expect(describeError(undefined)).toBeUndefined()
  })

  it('gives a hint and the code', () => {
    expect(describeError(101)).toBe('Le modèle a mis trop de temps à répondre. (code 101)')
  })

  it('falls back to a generic hint for an unknown code', () => {
    expect(describeError(4242)).toBe('Erreur inattendue. (code 4242)')
  })
})
