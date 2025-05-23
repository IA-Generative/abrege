#!/bin/sh
set -e

URL="${LLM_GUARD_URL:-http://localhost:8000}/healthz"
TIMEOUT=180  # secondes
INTERVAL=5   # secondes entre chaque tentative
ELAPSED=0

echo "⏳ Attente de LLM Guard à ${URL} (timeout ${TIMEOUT}s)..."

until curl --silent --fail "${URL}"; do
  if [ $ELAPSED -ge $TIMEOUT ]; then
    >&2 echo "❌ Timeout après ${TIMEOUT}s : LLM Guard n'est toujours pas prêt."
    exit 1
  fi
  >&2 echo "🔄 LLM Guard non prêt - nouvelle tentative dans ${INTERVAL}s..."
  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

echo "✅ LLM Guard est prêt !"
exec "$@"
