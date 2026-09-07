
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
| `MAX_CONTEXT_SIZE` | | Taille max du contexte en tokens | `128000` |
| `TOKENIZER_MODEL_NAME` | | Modèle HuggingFace pour le comptage de tokens | `gpt-4` |
| `HF_TOKEN` | | Token HuggingFace, lu implicitement par `huggingface_hub` quand `TOKENIZER_MODEL_NAME` pointe vers un repo gated (ex. `mistralai/*`) — sans quoi le téléchargement du tokenizer échoue silencieusement à la première tâche | — |

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
| `REDIS_SENTINEL_ENABLED` | | Active la résolution du master via Redis Sentinel. Si non défini, déduit de la présence de `REDIS_SENTINEL_HOSTS` | `false` |
| `REDIS_SENTINEL_HOSTS` | | Hôtes Sentinel, séparés par des virgules (`host1:26379,host2:26379`). Quand Sentinel est actif, `REDIS_HOST`/`REDIS_PORT` sont ignorés | — |
| `REDIS_SENTINEL_MASTER_NAME` | | Nom du master surveillé par les sentinels. Ancien nom déprécié : `REDIS_SENTINEL_SERVICE_NAME` | `mymaster` |

---

### Stockage objet (S3-compatible, ex. MinIO)

Le client S3 (`boto3`) est construit inconditionnellement — il n'y a pas de bascule
MinIO/S3 séparée : pointer `AWS_ENDPOINT_URL` vers une instance MinIO fait exactement la
même chose.

| Variable | Obligatoire | Description | Valeur par défaut |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` | ✅ | Clé d'accès | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | ✅ | Clé secrète | `minioadmin` |
| `AWS_ENDPOINT_URL` | | URL du endpoint S3/MinIO | `http://localhost:9000` |
| `AWS_DEFAULT_REGION` | | Région AWS | `us-east-1` |
| `AWS_BUCKET_NAME` | | Nom du bucket | `test` |

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

Toutes les variables peuvent être définies dans un fichier `.env` à la racine du projet. Le chargement est fait automatiquement grâce à `pydantic_settings`.

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

