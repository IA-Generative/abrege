import { beforeEach, describe, expect, it, vi } from 'vitest'

const keycloakInstance = {
  authenticated: true,
  token: 'current-access-token',
  refreshTokenParsed: undefined as { exp?: number } | undefined,
  timeSkew: 0,
  updateToken: vi.fn(),
  login: vi.fn(),
}

vi.mock('keycloak-js', () => ({
  default: vi.fn(() => keycloakInstance),
}))

async function loadKeycloakUtils () {
  vi.resetModules()
  return await import('./keycloak')
}

function secondsFromNow (offset: number) {
  return Math.floor(Date.now() / 1000) + offset
}

describe('getValidToken', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    keycloakInstance.authenticated = true
    keycloakInstance.token = 'current-access-token'
    keycloakInstance.timeSkew = 0
    keycloakInstance.refreshTokenParsed = { exp: secondsFromNow(3600) }
    keycloakInstance.updateToken.mockResolvedValue(true)
  })

  it('refreshes the token and returns it while the session is alive', async () => {
    const { getValidToken } = await loadKeycloakUtils()

    await expect(getValidToken()).resolves.toBe('current-access-token')
    expect(keycloakInstance.updateToken).toHaveBeenCalledTimes(1)
  })

  it('never calls the token endpoint once the refresh token has expired', async () => {
    const { getValidToken, SessionExpiredError } = await loadKeycloakUtils()
    keycloakInstance.refreshTokenParsed = { exp: secondsFromNow(-1) }

    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)
    expect(keycloakInstance.updateToken).not.toHaveBeenCalled()
  })

  it('treats a refresh token expiring within the buffer as already dead', async () => {
    const { getValidToken, SessionExpiredError } = await loadKeycloakUtils()
    keycloakInstance.refreshTokenParsed = { exp: secondsFromNow(10) }

    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)
    expect(keycloakInstance.updateToken).not.toHaveBeenCalled()
  })

  it('sends the user back to the SSO once, not once per pending request', async () => {
    const { getValidToken, SessionExpiredError } = await loadKeycloakUtils()
    keycloakInstance.refreshTokenParsed = { exp: secondsFromNow(-1) }

    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)
    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)
    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)

    expect(keycloakInstance.login).toHaveBeenCalledTimes(1)
  })

  it('reports a refresh the server refuses as an expired session, not as a transport failure', async () => {
    const { getValidToken, SessionExpiredError } = await loadKeycloakUtils()
    keycloakInstance.updateToken.mockRejectedValue(new Error('Server responded with an invalid status.'))

    await expect(getValidToken()).rejects.toBeInstanceOf(SessionExpiredError)
    expect(keycloakInstance.login).toHaveBeenCalledTimes(1)
  })
})
