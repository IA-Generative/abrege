## Routes de l'API

Documentation interactive (Swagger) exposée par le service lui-même : `<base_url>/api/docs`
(OpenAPI JSON : `<base_url>/api/openapi.json`). Cette page liste les routes pour référence
rapide ; le Swagger reste la source de vérité pour les schémas de requête/réponse détaillés.

Toutes les routes sont préfixées par `/api`, sauf celles d'authentification, déjà préfixées
par `/api/auth`. Sauf mention contraire, une route protégée attend un `Authorization: Bearer
<token>` (jeton Keycloak) ou le cookie de session BFF posé par `/api/auth/callback`.

---

### Authentification (`/api/auth`)

| Méthode | Route | Description | Authentification |
|---|---|---|---|
| GET | `/login` | Démarre le flux OAuth2/PKCE navigateur, redirige vers Keycloak | Publique |
| GET | `/callback` | Callback OAuth2 : échange le code contre des tokens, ouvre une session BFF (cookie) | Publique |
| POST | `/token` | Échange `username`/`password` contre un token Keycloak (Resource Owner Password Credentials), pour le SDK/scripts. Le secret client ne quitte jamais le backend | Publique (rate-limitée) |
| POST | `/refresh` | Échange un `refresh_token` (obtenu via `/token`) contre un token d'accès frais, sans redemander les identifiants | Publique (rate-limitée) |
| POST | `/logout` | Termine la session BFF et révoque le refresh token Keycloak | Session BFF |
| GET | `/me` | Identité de l'utilisateur courant (id, email, nom, groupes) | Session BFF |

`POST /token` et `POST /refresh` renvoient tous les deux :

```json
{
  "access_token": "...",
  "expires_in": 300,
  "refresh_token": "...",
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

Voir le [SDK Python](../sdk/README.md) : `login()` gère ce cycle automatiquement (rafraîchissement
transparent de l'access token avant expiration).

---

### Santé (`/api`)

| Méthode | Route | Description | Authentification |
|---|---|---|---|
| GET | `/health` | Statut du service et de ses dépendances (Redis, etc.) | Publique |

---

### Tâches (`/api`)

Créer une tâche de résumé (texte, URL ou document), puis suivre son avancement et récupérer
son résultat via son `id`.

| Méthode | Route | Description | Authentification |
|---|---|---|---|
| POST | `/task/text-url` | Crée une tâche de résumé à partir d'un texte brut ou d'une URL | Bearer |
| POST | `/task/document` | Crée une tâche de résumé à partir d'un fichier uploadé (PDF, DOCX, ODT, ODP, PNG…) | Bearer |
| GET | `/task/{id}` | Détail d'une tâche (statut, position dans la file, résultat une fois terminée) | Bearer (propriétaire) |
| GET | `/task/user/` | Liste paginée des tâches de l'utilisateur courant (`offset`, `limit`) | Bearer |
| POST | `/task/{id}/cancel` | Annule une tâche encore en file/active | Bearer (propriétaire) |
| DELETE | `/task/{id}` | Supprime une tâche terminée et ses fichiers associés (doit être annulée d'abord si active) | Bearer (propriétaire) |

Une tâche appartenant à un autre utilisateur renvoie `404` (pas `403`), pour ne pas révéler
son existence.
