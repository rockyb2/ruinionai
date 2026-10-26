"""The model returns data only. No generated code, tools or agent loop."""

import json
import os
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints
from observability import sanitized_observation
from prompts.meeting_system import build_meeting_system_prompt

NonEmptyText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60000)
]

MAX_WRITING_MODELS = 2
SUMMARY_MAX_TOKENS = 8000
SUMMARY_REQUEST_TIMEOUT_SECONDS = 120


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Action(ContentModel):
    action: NonEmptyText
    responsable: NonEmptyText | None = None
    echeance: NonEmptyText | None = None
    statut: Literal["décidée", "proposée", "à confirmer"]


class Sujet(ContentModel):
    titre: NonEmptyText
    contexte: NonEmptyText
    points_discutes: list[NonEmptyText]
    informations_importantes: list[NonEmptyText]
    propositions: list[NonEmptyText]
    decisions: list[NonEmptyText]
    actions: list[Action]
    questions_ouvertes: list[NonEmptyText]
    risques_blocages: list[NonEmptyText]
    incertitudes: list[NonEmptyText]


class Report(ContentModel):
    resume_long: NonEmptyText
    sujets: list[Sujet]


class MeetingContent(ContentModel):
    summary_short: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
    ]
    report: Report

    def summaries(self):
        def bullets(items):
            return "\n".join(f"- {item}" for item in items) or "Non précisé"

        report = self.report
        decisions = []
        actions = []
        questions = []
        risks = []
        subject_sections = []

        for subject in report.sujets:
            subject_sections.append("\n".join([
                f"Dossier : {subject.titre}",
                f"Contexte : {subject.contexte}",
                "Points discutés :",
                bullets(subject.points_discutes),
                "Informations importantes :",
                bullets(subject.informations_importantes),
                "Propositions non validées :",
                bullets(subject.propositions),
                "Incertitudes et contradictions :",
                bullets(subject.incertitudes),
            ]))
            decisions.extend(
                f"[{subject.titre}] {decision}" for decision in subject.decisions
            )
            actions.extend(
                " | ".join([
                    f"Action : [{subject.titre}] {item.action}",
                    f"Responsable : {item.responsable or 'Non précisé'}",
                    f"Échéance : {item.echeance or 'Non précisée'}",
                    f"Statut : {item.statut}",
                ])
                for item in subject.actions
            )
            questions.extend(
                f"[{subject.titre}] {question}"
                for question in subject.questions_ouvertes
            )
            risks.extend(
                f"[{subject.titre}] {risk}" for risk in subject.risques_blocages
            )

        sections = [
            ("1. Résumé long", report.resume_long),
            ("2. Points importants", "\n\n".join(subject_sections) or "Non précisé"),
            ("3. Décisions prises", bullets(decisions)),
            ("4. Actions à faire", bullets(actions)),
            ("5. Questions ouvertes", bullets(questions)),
            ("6. Risques ou blocages", bullets(risks)),
        ]
        return {
            "summary_short": self.summary_short,
            "summary_long": "\n\n".join(f"{title}\n{text}" for title, text in sections),
        }


def normalize_model(model):
    model = model.strip().replace("o*/", "openrouter/", 1)
    if model.startswith(("mistral-", "ministral-")):
        return "mistral/" + model
    if model.startswith(
        (
            "anthropic/",
            "deepseek/",
            "google/",
            "meta-llama/",
            "mistralai/",
            "nex-agi/",
            "nvidia/",
            "openai/",
            "qwen/",
            "x-ai/",
        )
    ):
        model = "openrouter/" + model
    return model


def configured_models():
    # SUMMARY_MODEL_IDS defines the ordered fallback list in Docker. The named
    # variables below remain compatible with installations that do not set it.
    selected = os.getenv("SUMMARY_MODEL_IDS", "").strip()
    if selected:
        values = selected.split(",")
    else:
        values = [
            os.getenv(name, "")
            for name in ("MISTRAL_MODEL_ID", "MISTRAL_MODEL_ID2", "MISTRAL_MODEL_ID3")
        ]
        values += [
            os.getenv("OPENROUTER_MODEL_ID") or os.getenv("OPENROUTER_MODEL", "")
        ]
        values += [
            os.getenv(name, "") for name in ("NEX_AGI_MODEL_ID", "NEX_AGI_MODEL_ID2")
        ]
    models = list(
        dict.fromkeys(normalize_model(value) for value in values if value.strip())
    )
    return models[:MAX_WRITING_MODELS]


def generate_content(context, model):
    from litellm import completion

    key_name = {
        "mistral": "MISTRAL_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai": "ZAI_API_KEY",
    }.get(model.split("/", 1)[0])
    api_key = os.getenv(key_name, "").strip() if key_name else None
    if key_name and not api_key:
        raise ValueError(f"Configuration manquante : {key_name}.")
    system = build_meeting_system_prompt(MeetingContent.model_json_schema())

    supports_json_mode = not (
        model.startswith("openrouter/") and model.endswith(":free")
    )
    options = {"response_format": {"type": "json_object"}} if supports_json_mode else {}

    # L’import est effectué ici, après le chargement des variables
    # d’environnement par l’application.
    from langfuse import get_client

    langfuse = get_client()

    messages = [
        {
            "role": "system",
            "content": system,
        },
        {
            "role": "user",
            "content": json.dumps(context, ensure_ascii=False),
        },
    ]

    try:
        with sanitized_observation(
            langfuse.start_as_current_observation(
                as_type="generation",
                name="generation-compte-rendu",
                model=model,
                input={
                    "transcription_characters": len(context.get("transcription") or ""),
                    "context_field_count": len(context),
                },
                model_parameters={
                    "max_tokens": SUMMARY_MAX_TOKENS,
                    "timeout": SUMMARY_REQUEST_TIMEOUT_SECONDS,
                    "temperature": 0,
                    "json_mode": supports_json_mode,
                },
                metadata={
                    "feature": "meeting-summary",
                },
            ),
            "La génération du compte rendu a échoué.",
        ) as generation:
            response = completion(
                model=model,
                api_key=api_key,
                messages=messages,
                max_tokens=SUMMARY_MAX_TOKENS,
                temperature=0,
                timeout=SUMMARY_REQUEST_TIMEOUT_SECONDS,
                num_retries=0,
                **options,
            )

            choice = response.choices[0]
            content = (choice.message.content or "").strip()

            # LiteLLM fournit généralement les informations de consommation
            # dans response.usage.
            usage = getattr(response, "usage", None)
            usage_details = {}

            if usage is not None:
                prompt_tokens = getattr(usage, "prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None)
                total_tokens = getattr(usage, "total_tokens", None)

                if prompt_tokens is not None:
                    usage_details["input"] = prompt_tokens

                if completion_tokens is not None:
                    usage_details["output"] = completion_tokens

                if total_tokens is not None:
                    usage_details["total"] = total_tokens

            # Keep only operational metrics in Langfuse. The response body may
            # contain the summary, transcript excerpts or participant data.
            update_values = {
                "output": {
                    "status": "received",
                    "response_characters": len(content),
                },
                "metadata": {
                    "finish_reason": choice.finish_reason,
                    "response_validated": False,
                },
            }

            if usage_details:
                update_values["usage_details"] = usage_details

            generation.update(**update_values)

            if choice.finish_reason != "stop":
                raise ValueError("Réponse interrompue ou incomplète.")

            if not supports_json_mode:
                fenced = re.fullmatch(
                    r"```(?:json)?\s*([\s\S]*?)\s*```",
                    content,
                    re.IGNORECASE,
                )

                if fenced:
                    content = fenced.group(1)

            result = MeetingContent.model_validate_json(content).summaries()

            # La validation Pydantic a réussi.
            generation.update(
                output={
                    "status": "completed",
                    "summary_short_characters": len(result["summary_short"]),
                    "summary_long_characters": len(result["summary_long"]),
                },
                metadata={
                    "finish_reason": choice.finish_reason,
                    "response_validated": True,
                },
            )

            return result

    finally:
        # generate_content est exécutée dans un sous-processus court.
        # Sans flush, le processus pourrait s’arrêter avant l’envoi de la trace.
        langfuse.flush()

    # response = completion(
    #     model=model,
    #     api_key=api_key,
    #     messages=[
    #         {"role": "system", "content": system},
    #         {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
    #     ],
    #     max_tokens=3000,
    #     timeout=25,
    #     num_retries=0,
    #     **options,
    # )
    # choice = response.choices[0]
    # if choice.finish_reason != "stop":
    #     raise ValueError("Réponse interrompue ou incomplète.")
    # content = (choice.message.content or "").strip()
    # if not supports_json_mode:
    #     fenced = re.fullmatch(
    #         r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE
    #     )
    #     if fenced:
    #         content = fenced.group(1)
    return MeetingContent.model_validate_json(content).summaries()
