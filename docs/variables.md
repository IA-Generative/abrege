
## Variables d'environnement

Ce projet utilise plusieurs fichiers de configuration via `pydantic_settings` pour centraliser les variables d'environnement. Voici un aperçu complet des variables utilisées, regroupées par service ou module.

Les variables marquées **obligatoires** doivent être définies. Les autres ont une valeur par défaut.

`.env.sample` est le **seul** fichier d'environnement versionné : il liste toutes
les variables ci-dessous avec des valeurs par défaut fonctionnelles pour le stack
`make up`, et jamais de secret. Ton `.env` local n'est pas versionné.

---

### Ports publiés sur la machine hôte

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `API_PORT` | | Port hôte de l'API. À surcharger dans ton `.env` si 5000 est déjà pris — c'est le cas par défaut sur macOS, où AirPlay Receiver l'occupe. `VITE_ABREGE_API_URL` en est dérivée par `docker-compose.yaml`, il n'y a donc que cette variable à changer | `5000` |
| `FRONT_PORT` | | Port du serveur de développement Vite (dans le conteneur) | `3000` |

---

### LLM / API OpenAI-compatible

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | Clé d'API (compatible OpenAI) | `sk-XXXXXXXXXXXXXXXX` |
| `OPENAI_API_BASE` | ✅ | URL de base de l'API | `https://api.openai.com/v1` |
| `OPENAI_API_MODEL` | | Modèle LLM texte | `gemma3` |
| `OPENAI_VLM_MODEL_NAME` | | Modèle VLM (utilisé quand `OCR_SERVICE_LLM=LLM`) | `mistral-small-3.1-24b-instruct-2503` |
| `MAX_CONTEXT_SIZE` | | Taille max du contexte en tokens | `128000` |
| `TOKENIZER_MODEL_NAME` | | Modèle HuggingFace pour le comptage de tokens | `gpt-4` |
| `HF_TOKEN` | | Token HuggingFace pour télécharger le tokenizer | — |

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
| `REDIS_QUEUE_NAME` | | Nom de la file Redis | `redis-queue` |
| `REDIS_PASSWORD` | | Mot de passe Redis | — |
| `REDIS_TLS` | | Activer TLS (`rediss://`) | `false` |
| `REDIS_SENTINEL_HOSTS` | | Hôtes Sentinel, séparés par des virgules (`host1:26379,host2:26379`). Quand défini, `REDIS_HOST`/`REDIS_PORT` sont ignorés | — |
| `REDIS_SENTINEL_SERVICE_NAME` | | Nom du service Sentinel (master) | `mymaster` |

---

### Stockage objet (MinIO / S3)

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` | ✅ | Clé d'accès AWS/MinIO | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | ✅ | Clé secrète AWS/MinIO | `minioadmin` |
| `AWS_ENDPOINT_URL` | | URL du endpoint S3/MinIO | `http://localhost:9000` |
| `AWS_DEFAULT_REGION` | | Région AWS | `us-east-1` |
| `S3_AVAILABLE` | | Activer le connecteur S3 | `False` |
| `MINIO_AVAILABLE` | | Activer le connecteur MinIO | `True` |
| `MINIO_BUCKET_NAME` | | Nom du bucket MinIO | `test` |
| `MINIO_END_POINT` | | Adresse de l'instance MinIO | `localhost:9000` |
| `MINIO_ACCESS_KEY` | | Clé d'accès MinIO | `minioadmin` |
| `MINIO_SECRET_KEY` | | Clé secrète MinIO | `minioadmin` |
| `AWS_BUCKET_NAME` | | Nom du bucket S3 | `test` |

---

### Sécurité API

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `VERIFY_TOKEN_MODEL` | ✅ en production | Mode de vérification des tokens : `keycloak` \| `full-access` (pas d'auth, dev) \| `dev` (tokens statiques) | `keycloak` |
| `KEYCLOAK_URL` | si `VERIFY_TOKEN_MODEL=keycloak` | URL du serveur Keycloak | `http://localhost:8080` |
| `KEYCLOAK_REALM` | si `VERIFY_TOKEN_MODEL=keycloak` | Nom du realm Keycloak | `master` |
| `KEYCLOAK_CLIENT_ID` | si `VERIFY_TOKEN_MODEL=keycloak` | Client ID Keycloak | `your-client-id` |
| `KEYCLOAK_CLIENT_SECRET` | si `VERIFY_TOKEN_MODEL=keycloak` | Secret du client Keycloak | `secret` |

---

### OCR

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `OCR_SERVICE_LLM` | | Mettre `LLM` pour utiliser le VLM local au lieu de l'API OCR externe | — |
| `OCR_BACKEND_URL` | si `OCR_SERVICE_LLM` ≠ `LLM` | URL de l'API OCR externe | — |

---

### Worker Celery

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `CELERY_APP_NAME` | | Nom de l'application Celery | `default` |
| `MAX_CONCURRENCY_LLM_CALL` | | Nombre max d'appels LLM simultanés | `5` |

---

### Caches et fichiers temporaires

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `CACHE_FOLDER` | | Dossier de cache (téléchargements, URLs…) | `/app/.cache` |
| `PYPANDOC_PANDOC_FOLDER` | | Chemin vers le binaire `pandoc` (auto-détecté si vide) | — |

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

---

### Frontend (Vite)

Ces variables sont lues au build par Vite et exposées au navigateur : **aucune ne doit contenir de secret.**

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `VITE_ABREGE_API_URL` | ✅ | URL de l'API vue depuis le navigateur. **Ne pas la définir dans `.env`** : `docker-compose.yaml` la dérive d'`API_PORT` pour que le port ne soit déclaré qu'à un seul endroit | `http://localhost:${API_PORT}/api` |
| `VITE_ENVIRONMENT` | | Environnement affiché côté frontend | `development` |
| `VITE_SSO_BYPASS` | | Contourne l'authentification Keycloak en développement | `false` |
| `VITE_KEYCLOAK_URL` | si SSO actif | URL du serveur Keycloak | — |
| `VITE_KEYCLOAK_CLIENT_ID` | si SSO actif | Client ID Keycloak | — |
| `VITE_KEYCLOAK_REALM` | si SSO actif | Realm Keycloak | — |
| `VITE_REDIRECT_URI` | si SSO actif | URI de redirection après authentification | `http://localhost:8082` |
| `VITE_PORTAIL_URL` | | Lien vers le portail Mirai | — |
| `VITE_USER_REVIEW_URL` | | Lien vers le formulaire de retour utilisateur | — |
| `VITE_TCHAP_CANAL_URL` | | Lien vers le canal Tchap | — |
| `VITE_MATOMO_SITE_URL` | | URL de l'instance Matomo | — |
| `VITE_MATOMO_SITE_ID` | | Identifiant du site Matomo | — |
| `VITE_SENTRY_FRONTEND_DSN` | | DSN Sentry du frontend | — |

---

### Tests E2E (Playwright)

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `VITE_USERNAME_KEYCLOAK` | pour les tests E2E | Identifiant du compte de test Keycloak. **Secret : à renseigner dans ton `.env` local uniquement** | — |
| `VITE_PASSWORD_KEYCLOAK` | pour les tests E2E | Mot de passe du compte de test Keycloak. **Secret : à renseigner dans ton `.env` local uniquement** | — |

---

Toutes les variables peuvent être définies dans un fichier `.env` à la racine du projet. Le chargement est fait automatiquement grâce à `pydantic_settings`. Ce fichier n'est pas versionné : partir de `.env.sample` (`cp .env.sample .env`) et n'y ajouter que ses secrets et ses surcharges locales.

## Volumes Docker

| Volume | Service | Chemin dans le conteneur | Description |
|---|---|---|---|
| `postgres_data` | `db` | `/var/lib/postgresql/data` | Données PostgreSQL persistantes |
| `minio_data` | `minio` | `/data` | Données MinIO persistantes |
| `./apps/server/abrege_service/` | `abrege_service` | `/app/abrege_service/` | Code source du worker (hot-reload) |
| `./apps/server/src/` | `abrege_service`, `abrege_api`, `migration` | `/app/src/` | Bibliothèque partagée (hot-reload) |
| `./apps/server/tests/` | `abrege_service`, `abrege_api` | `/app/tests/` | Tests (hot-reload) |
| `./apps/server/api/` | `abrege_api` | `/app/api/` | Code source de l'API (hot-reload) |
| `./apps/server/migration/` | `migration` | `/app/migration/` | Scripts de migration Alembic |
| `./apps/client/` | `abrege_frontend` | `/app/` | Code source frontend (hot-reload) |

