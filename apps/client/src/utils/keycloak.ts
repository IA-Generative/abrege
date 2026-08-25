import type { KeycloakConfig, KeycloakInitOptions } from 'keycloak-js'
import type { IUser } from '@/interfaces/IUser.ts'
import Keycloak from 'keycloak-js'

import {
  KEYCLOAK_CLIENT_ID,
  KEYCLOAK_REALM,
  KEYCLOAK_REDIRECT_URI,
  KEYCLOAK_URL,
} from './constants'

export const keycloakInitOptions: KeycloakInitOptions = {
  onLoad: 'check-sso',
  flow: 'standard',
  redirectUri: KEYCLOAK_REDIRECT_URI,
}

export const keycloakConfig: KeycloakConfig = {
  url: KEYCLOAK_URL,
  realm: KEYCLOAK_REALM,
  clientId: KEYCLOAK_CLIENT_ID,
}

let keycloak: Keycloak

// Depuis Keycloak 26.6.5/26.7.0, une redirect_uri dont la query string contient un paramètre
// de réponse OIDC est rejetée (protection HTTP Parameter Pollution), avant même la comparaison
// avec les valid redirect URIs du client - un wildcard ne rattrape donc pas le coup.
const OIDC_RESPONSE_PARAMS = [
  'code',
  'state',
  'session_state',
  'iss',
  'error',
  'error_description',
  'id_token',
  'access_token',
  'token_type',
  'expires_in',
  'response',
  'kc_action',
  'kc_action_status',
]

function stripOidcParams (url: URL): boolean {
  return OIDC_RESPONSE_PARAMS.reduce((mutated, param) => {
    if (!url.searchParams.has(param)) {
      return mutated
    }
    url.searchParams.delete(param)
    return true
  }, false)
}

function buildUri (url: URL, withHash = false): string {
  const query = url.searchParams.toString()
  return `${url.origin}${url.pathname}${query ? `?${query}` : ''}${withHash ? url.hash : ''}`
}

// redirect_uri sûre : l'URL courante débarrassée des paramètres de réponse OIDC.
function currentRedirectUri (): string {
  const url = new URL(window.location.href)
  stripOidcParams(url)
  return buildUri(url)
}

// Nettoie la barre d'adresse. `redirectToSSO` (router) n'envoie pas de response_mode, donc
// Keycloak répond en `query` et laisse code/session_state/iss dans l'URL : keycloak-js, qui
// lit le fragment, ne les consomme jamais et ils repartiraient dans la redirect_uri suivante.
function cleanAuthParamsFromUrl () {
  const url = new URL(window.location.href)
  if (!stripOidcParams(url)) {
    return
  }
  window.history.replaceState({}, document.title, buildUri(url, true))
}

function isRefreshTokenValid (keycloak: Keycloak): boolean {
  const refreshExp = keycloak.refreshTokenParsed?.exp
  const now = Date.now() / 1000
  return typeof refreshExp === 'number' && refreshExp > now
}

function getTokenExpiration (keycloak: Keycloak): number | null {
  const tokenExp = keycloak.tokenParsed?.exp
  return typeof tokenExp === 'number' ? tokenExp : null
}

export function getKeycloak () {
  if (!keycloak) {
    keycloak = new Keycloak(keycloakConfig)
    keycloak.onAuthSuccess = () => {
      if (isRefreshTokenValid(keycloak)) {
        return
      }
      console.warn('Keycloak misconfiguration: refreshToken should not expire before token')
      const tokenExp = getTokenExpiration(keycloak)
      if (tokenExp) {
        const refreshTokenDelay = (tokenExp * 1000 - Date.now()) / 2
        setTimeout(() => {
          keycloak.updateToken()
        }, refreshTokenDelay)
      }
    }
    keycloak.onTokenExpired = () => {
      keycloak.updateToken(30)
    }
  }
  return keycloak
}

export function getUserProfile (): IUser {
  try {
    const keycloak = getKeycloak()
    const { email, sub: id, given_name: firstName, family_name: lastName, groups } = keycloak.idTokenParsed as { email: string, sub: string, given_name: string, family_name: string, groups: string[] }
    return {
      email,
      id,
      firstName,
      lastName,
      groups,
    }
  }
  catch (error) {
    if (error instanceof Error) {
      throw new TypeError(error.message)
    }
    throw new Error('échec de récupération du profil keycloak de l\'utilisateur')
  }
}

export async function keycloakInit () {
  cleanAuthParamsFromUrl()
  const redirectUri = currentRedirectUri()
  try {
    const { onLoad, flow } = keycloakInitOptions
    const keycloak = getKeycloak()
    await keycloak.init({
      onLoad,
      flow,
      redirectUri,
    })
  }
  catch (error) {
    if (error instanceof Error) {
      throw new TypeError(error.message)
    }
    throw new Error('échec d\'initialisation du keycloak')
  }
}

export async function keycloakLogin () {
  try {
    const keycloak = getKeycloak()
    const redirectUri = currentRedirectUri()
    await keycloak.login({ redirectUri })
  }
  catch (error) {
    if (error instanceof Error) {
      throw new TypeError(error.message)
    }
    throw new Error('échec de connexion au keycloak')
  }
}

export async function keycloakRegister () {
  try {
    const keycloak = getKeycloak()
    const redirectUri = currentRedirectUri()
    await keycloak.register({ redirectUri })
  }
  catch (error) {
    if (error instanceof Error) {
      throw new TypeError(error.message)
    }
    throw new Error('échec de l\'inscription avec keycloak')
  }
}

export async function keycloakLogout () {
  try {
    const keycloak = getKeycloak()
    await keycloak.logout()
  }
  catch (error) {
    if (error instanceof Error) {
      throw new TypeError(error.message)
    }
    throw new Error('échec de déconnexion du keycloak')
  }
}

export async function getAuthTokens () {
  const keycloak = getKeycloak()

  if (!keycloak.authenticated) {
    throw new Error('L\'utilisateur n\'est pas authentifié')
  }

  return {
    accessToken: keycloak.token,
    refreshToken: keycloak.refreshToken,
    idToken: keycloak.idToken,
  }
}
