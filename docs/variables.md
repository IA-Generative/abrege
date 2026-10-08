
## Variables d'environnement

Ce projet utilise plusieurs fichiers de configuration via `pydantic_settings` pour centraliser les variables d'environnement. Voici un aperçu complet des variables utilisées, regroupées par service ou module.

Les variables marquées **obligatoires** doivent être définies. Les autres ont une valeur par défaut.

---

### LLM / API OpenAI-compatible

Noms harmonisés avec ocr-api (voir issue #356) : les anciens noms restent acceptés via un
alias déprécié (`_DEPRECATED_ENV_ALIASES` dans `abrege_service/config/openai.py`), qui logue un
avertissement et retombe sur la nouvelle variable — la migration côté déploiement n'a donc pas
besoin d'être en lockstep avec la release.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | Clé d'API (compatible OpenAI) | `sk-XXXXXXXXXXXXXXXX` |
| `OPENAI_API_BASE_URL` | ✅ | URL de base du hub LLM. Aucun repli sur l'API publique OpenAI : absente → échec explicite au démarrage. Ancien nom déprécié : `OPENAI_API_BASE` | — |
| `OPENAI_API_MODEL` | | Modèle LLM texte. Repli sur l'alias générique du hub (`chat`), jamais un nom de moteur concret, sauf en parlant directement à un provider (ex. Ollama local) | `chat` |
| `OPENAI_VLM_MODEL_NAME` | | Modèle VLM (utilisé quand `OCR_SERVICE_LLM=LLM`). Même logique d'alias générique | `chat` |
| `QA_MODEL_NAME` | | Modèle dédié aux questions/réponses. Non défini : réutilise `OPENAI_API_MODEL` | — |
| `ENTITY_MODEL_NAME` | | Modèle dédié à l'extraction d'entités, aussi utilisé pour la passe de relations globales. Non défini : réutilise `OPENAI_API_MODEL` | — |
| `CHUNK_MODEL_NAME` | | Modèle dédié au découpage sémantique (chunks). Non défini : réutilise `OPENAI_API_MODEL` | — |
| `TOPIC_MODEL_NAME` | | Modèle dédié à la classification des sujets. Non défini : réutilise `OPENAI_API_MODEL` | — |

Voir [document-insights.md](document-insights.md) pour le détail des extractions optionnelles.

---

### Base de données

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `DATABASE_URL` | ✅ | URL de connexion PostgreSQL (`postgresql://user:pass@host:port/db`). En Docker Compose, utiliser le nom du service comme hôte (`@db:5432`) | `sqlite:///./example.db` (fallback) |

---

### Redis / Celery broker

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `REDIS_HOST` | ✅ | Hôte Redis | `localhost` |
| `REDIS_PORT` | | Port Redis | `6379` |
| `REDIS_DB` | | Numéro de la base Redis | `0` |
| `REDIS_QUEUE_NAME` | | Nom de la file Redis | `redis-queue` |
| `REDIS_PASSWORD` | | Mot de passe Redis (authentifie le master résolu) | — |
| `REDIS_TLS` | | Activer TLS (`rediss://`) | `false` |
| `REDIS_SENTINEL_ENABLED` | | Active la résolution du master via Redis Sentinel. Si non défini, déduit de la présence de `REDIS_SENTINEL_HOSTS` | `false` |
| `REDIS_SENTINEL_HOSTS` | | Hôtes Sentinel, séparés par des virgules (`host1:26379,host2:26379`). Quand Sentinel est actif, `REDIS_HOST`/`REDIS_PORT` sont ignorés | — |
| `REDIS_SENTINEL_MASTER_NAME` | | Nom du master surveillé par les sentinels. Ancien nom déprécié : `REDIS_SENTINEL_SERVICE_NAME` | `mymaster` |
| `REDIS_SENTINEL_PASSWORD` | | Mot de passe pour authentifier les nœuds Sentinel eux-mêmes (peut différer de `REDIS_PASSWORD`). Retombe sur `REDIS_PASSWORD` si non défini | — |

---

### Stockage objet (S3-compatible, ex. RustFS)

Le client S3 (`boto3`) est construit inconditionnellement — il n'y a pas de bascule
RustFS/S3 séparée : pointer `AWS_ENDPOINT_URL` vers une instance RustFS (ou toute autre
implémentation S3-compatible) fait exactement la même chose.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` | ✅ | Clé d'accès | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | ✅ | Clé secrète | `minioadmin` |
| `AWS_ENDPOINT_URL` | | URL du endpoint S3/RustFS | `http://localhost:9000` |
| `AWS_DEFAULT_REGION` | | Région AWS | `us-east-1` |
| `AWS_BUCKET_NAME` | | Nom du bucket | `test` |

---

### Sécurité API

Le mode `keycloak` suit un modèle **Backend-for-Frontend (BFF)** : le navigateur ne parle
jamais directement à Keycloak et ne détient aucun jeton. C'est le backend qui possède tout le
flow OAuth2 Authorization Code + PKCE, via `/api/auth/{login,callback,logout,me}`. Le
navigateur ne reçoit qu'un cookie de session opaque (`httpOnly`, `Secure` en production) ; les
jetons Keycloak (access/refresh) restent côté backend, dans Redis. Un `Authorization: Bearer
<token>` reste accepté en parallèle pour les appels de service à service (ex. le SDK), vérifié
par introspection Keycloak. Voir [docs/security/readme.md](security/readme.md) pour le détail.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `VERIFY_TOKEN_MODEL` | ✅ en production | Mode de vérification des tokens : `keycloak` \| `full-access` (pas d'auth, dev) \| `dev` (tokens statiques) | `keycloak` |
| `KEYCLOAK_URL` | si `VERIFY_TOKEN_MODEL=keycloak` | URL du serveur Keycloak, jointe par le backend | `http://localhost:8080` |
| `KEYCLOAK_PUBLIC_URL` | | URL de Keycloak vue par le navigateur lors de la redirection de login. Retombe sur `KEYCLOAK_URL` si absente ; utile seulement quand backend et navigateur ne résolvent pas Keycloak de la même façon (ex. dev local en docker compose) | — |
| `KEYCLOAK_REALM` | si `VERIFY_TOKEN_MODEL=keycloak` | Nom du realm Keycloak | `master` |
| `KEYCLOAK_CLIENT_ID` | si `VERIFY_TOKEN_MODEL=keycloak` | Client ID Keycloak — doit être un client confidentiel (`publicClient: false`) | `your-client-id` |
| `KEYCLOAK_CLIENT_SECRET` | si `VERIFY_TOKEN_MODEL=keycloak` | Secret du client confidentiel | `secret` |
| `BACKEND_PUBLIC_URL` | si `VERIFY_TOKEN_MODEL=keycloak` | URL publique de cette API, sert à construire le `redirect_uri` fixe envoyé à Keycloak (`{BACKEND_PUBLIC_URL}/api/auth/callback`) — doit correspondre exactement à une redirect URI enregistrée sur le client Keycloak | `http://localhost:5000` |
| `FRONTEND_URL` | si `VERIFY_TOKEN_MODEL=keycloak` | URL publique du frontend — origine CORS autorisée (obligatoire dès lors que le cookie de session est envoyé avec les requêtes), cible de redirection après login/logout — doit aussi être enregistrée comme redirect URI post-logout sur le client Keycloak | `http://localhost:8082` |
| `SESSION_COOKIE_NAME` | | Nom du cookie de session posé sur le navigateur | `abrege_session` |
| `SESSION_COOKIE_SECURE` | | Cookie limité à HTTPS — ne jamais désactiver en production | `true` |
| `SESSION_COOKIE_SAMESITE` | | `lax` \| `strict` \| `none` | `lax` |
| `SESSION_TTL_SECONDS` | | Plafond de durée de session côté Redis, borné en pratique par l'expiration du refresh token Keycloak | `604800` (7 jours) |

---

### OCR

Quand l'API OCR externe est utilisée (`OCR_SERVICE_LLM` ≠ `LLM`), le worker doit s'authentifier
auprès d'elle (`src/clients/ocr_client.py`). Une config incomplète échoue **au démarrage du
worker** avec un message explicite, plutôt qu'à la première tâche déléguée à l'OCR (voir issue
#354).

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `OCR_SERVICE_LLM` | | Mettre `LLM` pour utiliser le VLM local au lieu de l'API OCR externe | — |
| `OCR_BACKEND_URL` | si `OCR_SERVICE_LLM` ≠ `LLM` | URL de l'API OCR externe | — |
| `OCR_API_KEY` | si `OCR_SERVICE_LLM` ≠ `LLM` (voie recommandée) | Clé statique envoyée en `Authorization: Bearer` — aucune dépendance à Keycloak. Provisionnée côté ocr comme une clé `API_KEYS` par consommateur | — |
| `OCR_KEYCLOAK_USERNAME` / `OCR_KEYCLOAK_PASSWORD` | repli, avec `KEYCLOAK_URL`/`CLIENT_ID`/`REALM` | Alternative à `OCR_API_KEY` : authentification Keycloak par mot de passe (Resource Owner Password Credentials), pour un compte de service provisionné comme utilisateur Keycloak classique | — |
| `KEYCLOAK_URL`/`KEYCLOAK_CLIENT_ID`/`KEYCLOAK_REALM`/`KEYCLOAK_CLIENT_SECRET` | repli si ni `OCR_API_KEY` ni `OCR_KEYCLOAK_USERNAME`/`PASSWORD` | Dernier repli : client-credentials Keycloak (même client que celui de la section Sécurité API) | — |

---

### Communication interne worker ↔ API

Le worker enregistre les résultats des extractions optionnelles (Q&R, entités, relations, chunks, sujets) en appelant des routes **internes** de l'API (`POST /api/task/{id}/qa`, `/entities`, `/relationships/global`, `/chunks`, `/topics`). Ces routes ne sont pas destinées aux utilisateurs : elles sont protégées par un secret partagé entre l'API et le worker.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `INTERNAL_SERVICE_TOKEN` | ✅ pour les extractions optionnelles | Secret partagé, envoyé par le worker dans l'en-tête `X-Internal-Token`. **Doit être identique côté API et côté worker.** Non défini : l'API refuse (401) tous les appels internes, et les extractions échouent | — |
| `ABREGE_API_BASE_URL` | | URL de l'API telle que le worker l'atteint depuis le réseau interne (sans `/api`). Le défaut est le nom du service docker compose : à surcharger ailleurs (ex. `http://abrege-api` sous Kubernetes) | `http://abrege_api:5000` |

---

### LLM Guard (optionnel)

Filtre le `custom_prompt` des requêtes de résumé. **Désactivé tant que `LLM_GUARD_URL` n'est pas défini.**

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `LLM_GUARD_URL` | | URL de l'API LLM Guard. Absente : aucun filtrage | — |
| `LLM_GUARD_API_KEY` | | Clé d'API LLM Guard | `llm_guard` |

---

### Worker Celery

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `CELERY_APP_NAME` | | Nom de l'application Celery | `default` |
| `MAX_CONCURRENCY_LLM_CALL` | | Nombre max d'appels LLM simultanés | `5` |
| `MAX_MODEL_TOKEN` | | Taille de contexte (en tokens) que le worker suppose pour le LLM de résumé : elle détermine la taille des fragments du map-reduce | `128000` |

---

### Caches et fichiers temporaires

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `CACHE_FOLDER` | | Dossier de cache (téléchargements, URLs…) | `/app/.cache` |

---

### Observabilité

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `ENVIRONMENT` | | Environnement d'exécution : `development` \| `production` \| `testing` | `development` |
| `SENTRY_API_DSN` | | DSN Sentry pour l'API FastAPI | — |
| `SENTRY_WORKER_DSN` | | DSN Sentry pour le worker Celery | — |
| `SEND_DEFAULT_PII` | | Envoyer les PII à Sentry | `false` |
| `LANGFUSE_PUBLIC_KEY` | | Clé publique Langfuse — **si absent, Langfuse est désactivé** | — |
| `LANGFUSE_SECRET_KEY` | si `LANGFUSE_PUBLIC_KEY` défini | Clé secrète Langfuse | — |
| `LANGFUSE_HOST` | si `LANGFUSE_PUBLIC_KEY` défini | URL de l'instance Langfuse | `https://cloud.langfuse.com` |
| `LANGFUSE_ENVIRONMENT` | si `LANGFUSE_PUBLIC_KEY` défini | Environnement de tracing Langfuse | `local` |
| `SERVICE_NAME` | | Nom de service ajouté aux logs JSON | `abrege` |
| `POD_NAME` / `POD_NAMESPACE` / `NODE_NAME` | | Métadonnées ajoutées aux logs JSON. À fournir via la downward API de Kubernetes (`fieldRef`) ; absentes, les champs restent vides | — |

---

### Frontend (Vite)

Lues par le client à la compilation (`import.meta.env`) ou au chargement (`window.VITE_*`). Avec le chart Helm, `frontend.viteEnv` génère un `config.js` monté dans le conteneur : les valeurs peuvent donc changer **sans reconstruire l'image**.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `VITE_ABREGE_API_URL` | ✅ | URL de l'API **avec le préfixe `/api`** (ex. `http://localhost:5000/api`) : le front appelle `${VITE_ABREGE_API_URL}/auth/login`, `/task/...` | — |
| `VITE_PORTAIL_URL` | | URL du portail MIrAI (liens CGU, FAQ, autres outils) | — |
| `VITE_USER_REVIEW_URL` | | URL du bouton « Donner mon avis » | — |
| `VITE_TCHAP_CANAL_URL` | | URL du canal Tchap de support | — |
| `VITE_MATOMO_SITE_URL` / `VITE_MATOMO_SITE_ID` | | Instance et identifiant de site Matomo (statistiques) | — |
| `VITE_SENTRY_FRONTEND_DSN` | | DSN Sentry du front. Absent : Sentry désactivé | — |
| `VITE_ENVIRONMENT` | | Environnement remonté à Sentry | — |
| `FRONT_PORT` | | Port du serveur de développement Vite (et des tests Playwright) | — |
| `VITE_USERNAME_KEYCLOAK` / `VITE_PASSWORD_KEYCLOAK` | tests E2E uniquement | Compte de test utilisé par Playwright (`playwright/login-helper.ts`). Jamais lues par l'application | — |

---

Toutes les variables peuvent être définies dans un fichier `.env` à la racine du projet. Le chargement est fait automatiquement grâce à `pydantic_settings`.

En développement avec docker compose, `.env.local` (versionné) fournit des valeurs d'exemple et un `.env` optionnel (ignoré par git) les surcharge : le dernier fichier l'emporte. Les entrées `environment:` du compose passent avant les deux, et celles qui contiennent `${VAR:-défaut}` lisent `VAR` dans le shell ou dans `.env`, pas dans `.env.local`.

## Volumes Docker

| Volume | Service | Chemin dans le conteneur | Description |
|---|---|---|---|
| `postgres_data` | `db` | `/var/lib/postgresql/data` | Données PostgreSQL persistantes |
| `rustfs_data` | `rustfs` | `/data` | Données RustFS persistantes |
| `./apps/server/abrege_service/` | `abrege_service` | `/app/abrege_service/` | Code source du worker (hot-reload) |
| `./apps/server/src/` | `abrege_service`, `abrege_api`, `migration` | `/app/src/` | Bibliothèque partagée (hot-reload) |
| `./apps/server/tests/` | `abrege_service`, `abrege_api` | `/app/tests/` | Tests (hot-reload) |
| `./apps/server/api/` | `abrege_api` | `/app/api/` | Code source de l'API (hot-reload) |
| `./apps/server/migration/` | `migration` | `/app/migration/` | Scripts de migration Alembic |
| `./apps/client/` | `abrege_frontend` | `/app/` | Code source frontend (hot-reload) |

