# Sécurité & Configuration Keycloak

L'authentification suit un modèle **Backend-for-Frontend (BFF)** : le frontend ne parle jamais
directement à Keycloak et ne détient aucun jeton. C'est le backend (`abrege_service`) qui
possède tout le flow OAuth2 Authorization Code + PKCE, via `/api/auth/{login,callback,logout,me}`
(`api/routes/auth.py`). Le navigateur ne reçoit qu'un cookie de session opaque
(`httpOnly`, `Secure` en production) ; les jetons Keycloak (access/refresh) restent côté backend,
dans Redis (`api/core/security/session.py`).

Un `Authorization: Bearer <token>` reste accepté en parallèle pour les appels de service à
service (par exemple le SDK Python) : ce token est un jeton Keycloak vérifié par introspection,
jamais le cookie de session (`api/core/security/factory.py`).

Pour que ce flow fonctionne correctement, **toutes les valeurs de configuration Keycloak doivent
être définies via un gestionnaire de secrets** (Vault ou équivalent) — jamais commitées.

## Variables requises

- `KEYCLOAK_URL` : URL de Keycloak jointe **par le backend** (échange de code, refresh,
  introspection, logout). Exemple : `https://keycloak.example.com`
- `KEYCLOAK_PUBLIC_URL` : URL de Keycloak vue **par le navigateur** lors de la redirection de
  login. Optionnelle — retombe sur `KEYCLOAK_URL` si absente ; à renseigner uniquement si le
  backend et le navigateur ne résolvent pas Keycloak de la même façon (typiquement en dev local,
  voir plus bas).
- `KEYCLOAK_REALM` : Nom du realm Keycloak utilisé
- `KEYCLOAK_CLIENT_ID` : ID du client OpenID configuré dans Keycloak — **doit être un client
  confidentiel** (`publicClient: false`), jamais public : seul le backend échange le code
  d'autorisation, le navigateur ne doit avoir aucun moyen de s'authentifier directement auprès de
  Keycloak.
- `KEYCLOAK_CLIENT_SECRET` : Secret du client confidentiel
- `BACKEND_PUBLIC_URL` : URL publique de cette API. Sert à construire le `redirect_uri` fixe
  envoyé à Keycloak (`{BACKEND_PUBLIC_URL}/api/auth/callback`) — **doit correspondre exactement**
  à une redirect URI enregistrée sur le client Keycloak.
- `FRONTEND_URL` : URL publique du frontend. Sert d'origine CORS autorisée (une origine explicite
  est obligatoire dès lors que le cookie de session est envoyé avec les requêtes —
  `allow_origins: ["*"]` est rejeté par les navigateurs en présence de `allow_credentials: true`),
  de cible de redirection après le callback de login, et de `post_logout_redirect_uri` après le
  logout — **doit aussi être enregistrée comme redirect URI post-logout valide** sur le client
  Keycloak, sans quoi `/api/auth/logout` échoue à rediriger l'utilisateur après la fin de sa
  session SSO.

**Aucune valeur par défaut ne doit être utilisée en production.**
Toutes ces valeurs doivent être stockées et injectées de façon sécurisée via un gestionnaire de
secrets.

## Cookie de session

En complément, ces variables contrôlent le cookie de session posé sur le navigateur — leurs
défauts (`src/config/keycloak.py`) sont déjà corrects pour un déploiement HTTPS et n'ont
normalement pas besoin d'être surchargés en production :

- `SESSION_COOKIE_NAME` (défaut `abrege_session`)
- `SESSION_COOKIE_SECURE` (défaut `True`) : **ne jamais désactiver en production** — ce cookie
  porte l'accès à la session utilisateur, il doit toujours être limité à HTTPS. Ne le passer à
  `False` qu'en dev local HTTP.
- `SESSION_COOKIE_SAMESITE` (défaut `lax`)
- `SESSION_TTL_SECONDS` (défaut `604800`, 7 jours) : plafond côté Redis, l'expiration réelle reste
  bornée par celle du refresh token Keycloak.

## Bonnes pratiques

- **Ne jamais** committer ces valeurs dans le code source.
- Toujours utiliser un gestionnaire de secrets pour injecter ces variables à l'exécution.
- Vérifier que toutes les variables sont bien présentes avant de démarrer l'application.
- Le client Keycloak doit rester confidentiel (`publicClient: false`) : le navigateur n'a jamais
  besoin d'un secret ou d'un flow public, seul le backend parle à Keycloak.
- `SESSION_COOKIE_SECURE` doit rester à `True` dès que le trafic passe par HTTPS, c'est-à-dire
  partout hors dev local.

## Actions requises côté Keycloak (déploiement)

Le passage au modèle BFF change le rôle du client Keycloak désigné par `KEYCLOAK_CLIENT_ID` :

- [ ] **Enregistrer `/api/auth/callback` comme redirect URI** sur ce client.
- [ ] **Enregistrer l'URL du frontend comme redirect URI post-logout** (`post.logout.redirect.uris`)
  sur ce client.
- [ ] **Passer le client de public à confidentiel** (`publicClient: false`) : le navigateur
  ne parle plus du tout à Keycloak, seul le backend en a besoin.
- [ ] **Supprimer/nettoyer les `VITE_KEYCLOAK_*` / `VITE_REDIRECT_URI`** dans la configuration de
  déploiement du frontend — devenus morts avec le passage en BFF, le frontend ne les lit plus.

---
Pour plus d'informations, consultez la documentation Keycloak et celle de votre gestionnaire de
secrets.
