import os

import requests
from src.utils.logger import logger_abrege

LLM_GUARD_API_KEY = os.environ.get("LLM_GUARD_API_KEY", "llm_guard")
LLM_GUARD_BASE_URL = os.environ.get("LLM_GUARD_URL", "http://0.0.0.0:8000")


class LLMGuardMaliciousPromptException(Exception):
    scores = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.scores = kwargs.get("scores", {})

    def __str__(self):
        scanners = [scanner for scanner, score in self.scores.items() if score > 0]

        return f"LLM Guard detected a malicious prompt. Scanners triggered: {', '.join(scanners)}; scores: {self.scores}"


class LLMGuardRequestException(Exception):
    pass


class LLMGuard:
    def __init__(self, llm_guard_base_url: str, llm_guard_api_key: str):
        self.llm_guard_base_url = llm_guard_base_url
        self.llm_guard_api_key = llm_guard_api_key
        logger_abrege.debug(self.llm_guard_base_url)
        logger_abrege.debug(self.llm_guard_api_key)

    def request_llm_guard_prompt(self, prompt: str):
        try:
            response = requests.post(
                url=f"{self.llm_guard_base_url}/analyze/prompt",
                json={"prompt": prompt},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.llm_guard_api_key}",
                },
            )

            response_json = response.json()
            logger_abrege.debug(response_json)
        except requests.RequestException as err:
            raise LLMGuardRequestException(err)

        if not response_json["is_valid"]:
            raise LLMGuardMaliciousPromptException(scores=response_json["scanners"])

        return response_json["sanitized_prompt"]

    def get_health(self):
        try:
            url = f"{self.llm_guard_base_url}/healthz"
            logger_abrege.info(url)
            response = requests.get(
                url=url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.llm_guard_api_key}",
                },
            )
            logger_abrege.info("Connected to llm-guard")
            response_json = response.json()
        except requests.RequestException as err:
            logger_abrege.error(err)
            raise LLMGuardRequestException(err)

        return response_json


llm_guard = LLMGuard(llm_guard_api_key=LLM_GUARD_API_KEY, llm_guard_base_url=LLM_GUARD_BASE_URL)

try:
    llm_guard.get_health()
except Exception as e:
    logger_abrege.warning(str(e))
    llm_guard = None
logger_abrege.debug(llm_guard)
