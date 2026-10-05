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

Voir le [SDK Python](../sdk/python/README.md) : `login()` gère ce cycle automatiquement (rafraîchissement
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

| POST | `/task/{id}/extract-details` | (Re)lance l'extraction Q&R, entités, relations et chunks d'une tâche terminée | Bearer (propriétaire) |

Le code HTTP de `GET /task/{id}` reflète l'état de la tâche : `201` créée, `202` en file ou démarrée, `206` en cours,
`200` terminée, `208` nouvelle tentative, `500` échec ou annulée, `504` délai dépassé.

Dans les listes, `offset` est un **numéro de page** (à partir de 1) et `limit` la taille de page.

Une tâche appartenant à un autre utilisateur renvoie `404` (pas `403`), pour ne pas révéler
son existence.

#### Résultats des extractions optionnelles (`/task/{id}/...`)

Q&R (`/qa`), entités (`/entities`), relations (`/relationships`), sujets (`/topics`) et chunks (`/chunks`) :
lecture paginée (`GET`), lecture unitaire (`GET .../{item_id}`, sauf `topics`) et suppression (`DELETE .../{item_id}`),
toujours limitées au propriétaire de la tâche. Les routes d'écriture (`POST`) sont **internes** : réservées au worker,
authentifiées par `X-Internal-Token`. Détail de chaque extraction dans [document-insights.md](document-insights.md) ;
référence complète dans le Swagger (`/api/docs`).
