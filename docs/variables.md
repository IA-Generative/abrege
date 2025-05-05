
## Variables d'environnement

Ce projet utilise plusieurs fichiers de configuration via `pydantic_settings` pour centraliser les variables d'environnement. Voici un aperçu complet des variables utilisées, regroupées par service ou module.

### `OpenAISettings` (`abrege_service`)

| Variable           | Description                         | Valeur par défaut |
| ------------------ | ----------------------------------- | ----------------- |
| `OPENAI_API_BASE`  | URL de base de l'API OpenAI         | -                 |
| `OPENAI_API_KEY`   | Clé d'API OpenAI                    | -                 |
| `OPENAI_API_MODEL` | Modèle à utiliser                   | `"gemma3"`        |
| `MAX_TOKENS`       | Nombre maximum de tokens (ex: Qwen) | `128000`          |

---

### `CelerySettings`

| Variable          | Description                 | Valeur par défaut |
| ----------------- | --------------------------- | ----------------- |
| `CELERY_APP_NAME` | Nom de l'application Celery | `"default"`       |

---

### `ConnectorSettings`

| Variable          | Description                               | Valeur par défaut |
| ----------------- | ----------------------------------------- | ----------------- |
| `S3_AVAILABLE`    | Activer/désactiver l'utilisation de S3    | `"False"`         |
| `MINIO_AVAILABLE` | Activer/désactiver l'utilisation de MinIO | `"True"`          |

---

### `MinioSettings`

| Variable            | Description                 | Valeur par défaut  |
| ------------------- | --------------------------- | ------------------ |
| `MINIO_BUCKET_NAME` | Nom du bucket MinIO         | `"test"`           |
| `MINIO_END_POINT`   | Adresse de l'instance MinIO | `"localhost:9000"` |
| `MINIO_ACCESS_KEY`  | Clé d'accès MinIO           | `"minioadmin"`     |
| `MINIO_SECRET_KEY`  | Clé secrète MinIO           | `"minioadmin"`     |

---

### `RedisSettings`

| Variable           | Description          | Valeur par défaut |
| ------------------ | -------------------- | ----------------- |
| `REDIS_HOST`       | Hôte Redis           | `"localhost"`     |
| `REDIS_PORT`       | Port Redis           | `6379`            |
| `REDIS_QUEUE_NAME` | Nom de la file Redis | `"redis-queue"`   |

---

### `S3Settings`

| Variable         | Description      | Valeur par défaut  |
| ---------------- | ---------------- | ------------------ |
| `S3_BUCKET_NAME` | Nom du bucket S3 | `"test"`           |
| `S3_END_POINT`   | Endpoint S3      | `"localhost:9000"` |
| `S3_ACCESS_KEY`  | Clé d'accès S3   | `"S3admin"`        |
| `S3_SECRET_KEY`  | Clé secrète S3   | `"S3admin"`        |
| `S3_REGION`      | Région S3        | `"fr-par"`         |

---

Toutes les variables peuvent être définies dans un fichier `.env` à la racine du projet. Le chargement est fait automatiquement grâce à `pydantic_settings`.
