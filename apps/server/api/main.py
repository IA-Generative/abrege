from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP, AuthConfig
from api.core.security.factory import TokenVerifier
from api.utils.fastapi_mcp_patch import patch_fastapi_mcp_recursion
from api.routes.health import router as health_router
from api.routes.summarize import router as summarize_router
from api.routes.document_summary import doc_router
from api.routes.task import router as task_router
from api.routes.v1.chunk import router as chunk_router
from api.routes.v1.leaderboard import router as leaderboard_router
from api.routes.v1.chat import router as chat_router
from src import __version__, __name__ as name
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title=name,
    description="",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redocs",
    openapi_url="/api/openapi.json",
)
Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(summarize_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
app.include_router(chunk_router, prefix="/api")
app.include_router(leaderboard_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


# Dépendances de sécurité réutilisées pour protéger l'endpoint MCP,
# identiques à celles de l'API HTTP (vérification du token).
_secure = [Depends(TokenVerifier)]

# Corrige la récursion infinie de fastapi-mcp (<=0.4.0) sur les schémas
# OpenAPI auto-référents. Doit être appelé avant de construire FastApiMCP.
patch_fastapi_mcp_recursion()

# Expose l'API FastAPI existante comme serveur MCP. FastAPI et MCP coexistent
# dans la même application : l'API HTTP reste accessible et le serveur MCP est
# monté (sécurisé) sur /api/mcp.
mcp = FastApiMCP(
    app,
    name=name,
    description=f"MCP server exposing the {name} API endpoints as tools.",
    auth_config=AuthConfig(
        dependencies=_secure,
    ),
)
mcp.mount_http(mount_path="/api/mcp")
