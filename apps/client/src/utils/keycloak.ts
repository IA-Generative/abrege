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

export function getKeycloak () {
  if (!keycloak) {
    keycloak = new Keycloak(keycloakConfig)
    keycloak.onAuthSuccess = () => {
      if (!(keycloak.refreshTokenParsed?.exp && keycloak.tokenParsed?.exp && keycloak.refreshTokenParsed.exp > keycloak.tokenParsed.exp)) {
        return
      }
      console.warn('KeyclKeycloak misconfiguration : refreshToken should not expire before token.akl')
      const refreshTokenDelay = (keycloak.tokenParsed.exp * 100 - Date.now()) / 2
      setTimeout(() => {
        keycloak.updateToken()
      }, refreshTokenDelay)
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
    const { email, sub: id, given_name: firstName, family_name: lastName, groups } = keycloak.idTokenParsed as { email: string, sub: string, given_name: string, firstName: string, family_name: string, lastName: string, groups: string[] }
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
  const currentUrl = new URL(window.location.href)
  const redirectUri = `${window.location.origin}${currentUrl.pathname}${currentUrl.search}`
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
    const currentUrl = new URL(window.location.href)
    const redirectUri = `${window.location.origin}${currentUrl.pathname}${currentUrl.search}`
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
    const currentUrl = new URL(window.location.href)
    const redirectUri = `${window.location.origin}${currentUrl.pathname}${currentUrl.search}`
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
