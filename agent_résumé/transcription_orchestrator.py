"""Orchestration des fournisseurs de transcription audio."""

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_IDS = (
    "elevenlabs/scribe_v2",
    "mistral/voxtral-mini-latest",
)

SUPPORTED_PROVIDERS = {
    "elevenlabs",
    "mistral",
}

MAX_ATTEMPTS_PER_PROVIDER = 2
DEFAULT_RETRY_DELAY_SECONDS = 5
MAX_RETRY_DELAY_SECONDS = 60

@dataclass(frozen=True)
class TranscriptionProvider:
    name: str
    model_id: str

    @property
    def identifier(self):
        return f"{self.name}/{self.model_id}"


@dataclass(frozen=True)
class ProviderFailure:
    provider: str
    model_id: str
    error_type: str
    status_code: int | None


class InvalidTranscriptionResult(ValueError):
    """Le fournisseur a retourné une transcription inutilisable."""


class AllTranscriptionProvidersFailed(RuntimeError):
    """Tous les fournisseurs configurés ont échoué."""

    def __init__(self, failures):
        self.failures = failures

        super().__init__(
            "Tous les fournisseurs de transcription ont échoué."
        )


def configured_transcription_providers():
    """
    Lit la liste définie dans TRANSCRIPTION_PROVIDER_IDS.

    Exemple :
    elevenlabs/scribe_v2,mistral/voxtral-mini-latest
    """
    raw_value = os.getenv(
        "TRANSCRIPTION_PROVIDER_IDS",
        ",".join(DEFAULT_PROVIDER_IDS),
    )

    providers = []
    seen = set()

    for raw_identifier in raw_value.split(","):
        identifier = raw_identifier.strip()

        if not identifier:
            continue

        provider_name, separator, model_id = identifier.partition("/")

        provider_name = provider_name.strip().lower()
        model_id = model_id.strip()

        if (
            not separator
            or not provider_name
            or not model_id
        ):
            raise ValueError(
                "Chaque fournisseur de transcription doit utiliser "
                "le format fournisseur/modèle."
            )

        if provider_name not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Fournisseur de transcription inconnu : "
                f"{provider_name}."
            )

        normalized_identifier = (
            f"{provider_name}/{model_id}"
        )

        if normalized_identifier in seen:
            continue

        seen.add(normalized_identifier)

        providers.append(
            TranscriptionProvider(
                name=provider_name,
                model_id=model_id,
            )
        )

    if not providers:
        raise ValueError(
            "Aucun fournisseur de transcription n’est configuré."
        )

    return providers


def _status_code(error):
    """Extrait un code HTTP sans lire le corps de la réponse."""
    status = getattr(error, "status_code", None)

    if isinstance(status, int):
        return status

    response = getattr(error, "response", None)
    status = getattr(response, "status_code", None)

    if isinstance(status, int):
        return status

    return None


def _retry_after_seconds(error):
    """Lit Retry-After lorsqu’un fournisseur le transmet."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)

    if not headers:
        headers = getattr(error, "headers", None)

    if not headers:
        return None

    value = headers.get("retry-after")

    if value is None:
        value = headers.get("Retry-After")

    try:
        delay = float(value)
    except (TypeError, ValueError):
        return None

    return max(
        0,
        min(delay, MAX_RETRY_DELAY_SECONDS),
    )


def _is_retryable(error):
    """Détermine si une deuxième tentative est raisonnable."""
    status = _status_code(error)

    if status in {408, 425, 429}:
        return True

    if status is not None and status >= 500:
        return True

    error_name = type(error).__name__.lower()

    return any(
        marker in error_name
        for marker in (
            "timeout",
            "connection",
            "connect",
            "ratelimit",
            "rate_limit",
        )
    )


def _validate_result(result):
    """Vérifie le contrat commun des adaptateurs."""
    if not isinstance(result, dict):
        raise InvalidTranscriptionResult(
            "Le fournisseur a retourné un résultat invalide."
        )

    transcription = result.get("transcription")
    segments = result.get("transcription_segments")

    if not isinstance(transcription, str):
        raise InvalidTranscriptionResult(
            "La transcription n’est pas du texte."
        )

    if not transcription.strip():
        raise InvalidTranscriptionResult(
            "La transcription est vide."
        )

    if not isinstance(segments, list) or not segments:
        raise InvalidTranscriptionResult(
            "Les segments de transcription sont absents."
        )

    return result


def transcribe_with_fallback(
    executors: dict[str, Callable[[str], dict]],
    sleep_function=time.sleep,
):
    """
    Exécute les fournisseurs dans l’ordre configuré.

    Chaque executor reçoit le model_id et doit retourner le contrat
    commun contenant transcription et transcription_segments.
    """
    failures = []

    for provider in configured_transcription_providers():
        executor = executors.get(provider.name)

        if executor is None:
            failures.append(
                ProviderFailure(
                    provider=provider.name,
                    model_id=provider.model_id,
                    error_type="MissingExecutor",
                    status_code=None,
                )
            )
            continue

        for attempt in range(1, MAX_ATTEMPTS_PER_PROVIDER + 1):
            try:
                result = executor(provider.model_id)

                return _validate_result(result)

            except Exception as error:
                status = _status_code(error)

                failures.append(
                    ProviderFailure(
                        provider=provider.name,
                        model_id=provider.model_id,
                        error_type=type(error).__name__,
                        status_code=status,
                    )
                )

                logger.warning(
                    "Transcription provider %s failed "
                    "(attempt %s/%s, error=%s, status=%s)",
                    provider.identifier,
                    attempt,
                    MAX_ATTEMPTS_PER_PROVIDER,
                    type(error).__name__,
                    status,
                )

                can_retry = (
                    attempt < MAX_ATTEMPTS_PER_PROVIDER
                    and _is_retryable(error)
                )

                if not can_retry:
                    break

                delay = _retry_after_seconds(error)

                if delay is None:
                    delay = DEFAULT_RETRY_DELAY_SECONDS

                sleep_function(delay)

    raise AllTranscriptionProvidersFailed(failures)
