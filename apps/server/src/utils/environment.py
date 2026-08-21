import os

from src.utils.logger import logger_abrege

DEFAULT_ENVIRONMENT = "development"


def resolve_environment() -> str:
    """Retourne l'environnement de déploiement, en alertant s'il n'est pas défini.

    Un ENVIRONMENT absent tague silencieusement tous les events Sentry en
    "development" : les erreurs de production se noient alors parmi celles du
    local. C'est ce qui masquait les erreurs du worker de prod.
    """
    environment = os.getenv("ENVIRONMENT")
    if not environment:
        logger_abrege.warning(
            f"ENVIRONMENT n'est pas defini, repli sur '{DEFAULT_ENVIRONMENT}' : les events Sentry de ce deploiement seront mal etiquetes"
        )
        return DEFAULT_ENVIRONMENT
    return environment
