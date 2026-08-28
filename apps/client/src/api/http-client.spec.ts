import type { InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const getValidToken = vi.fn()

vi.mock('@/utils/keycloak', () => ({
  getValidToken,
  SessionExpiredError: class SessionExpiredError extends Error {},
}))

const { default: createHttpClient } = await import('./http-client')

function clientWithSpyAdapter () {
  const adapter = vi.fn(async (config: InternalAxiosRequestConfig) => ({
    data: {},
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  }))
  const httpClient = createHttpClient('https://api.test')
  httpClient.defaults.adapter = adapter
  return { httpClient, adapter }
}

describe('http client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('DEV', false)
    vi.stubEnv('VITE_SSO_BYPASS', 'false')
  })

  afterEach(() => vi.unstubAllEnvs())

  it('attaches the freshly refreshed token to every request', async () => {
    getValidToken.mockResolvedValue('fresh-token')
    const { httpClient, adapter } = clientWithSpyAdapter()

    await httpClient.get('/tasks')

    expect(adapter.mock.calls[0]![0].headers.Authorization).toBe('Bearer fresh-token')
  })

  it('never sends a request without an Authorization header when the session is dead', async () => {
    getValidToken.mockRejectedValue(new Error('Session expired'))
    const { httpClient, adapter } = clientWithSpyAdapter()

    await expect(httpClient.get('/tasks')).rejects.toThrow()
    expect(adapter).not.toHaveBeenCalled()
  })
})
