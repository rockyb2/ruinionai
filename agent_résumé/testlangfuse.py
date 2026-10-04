from pathlib import Path

from dotenv import load_dotenv

# Charge d’abord le .env racine du projet.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Charge ensuite agent_résumé/.env si certaines variables y sont définies.
load_dotenv(Path(__file__).resolve().parent / ".env")

# L’import vient après le chargement des variables.
from langfuse import get_client


langfuse = get_client()


def test_langfuse():
    if not langfuse.auth_check():
        raise RuntimeError(
            "Connexion Langfuse impossible. Vérifiez les clés et LANGFUSE_BASE_URL."
        )

    print("Connexion Langfuse réussie.")

    # Cette observation principale représente le traitement complet d’une réunion.
    with langfuse.start_as_current_observation(
        as_type="span",
        name="traitement-reunion-test",
        input={
            "meeting_id": 999,
            "title": "Réunion de démonstration",
        },
        metadata={
            "organization_id": 1,
            "environment": "development",
        },
    ) as traitement:

        # Première étape du traitement.
        with langfuse.start_as_current_observation(
            as_type="span",
            name="transcription",
            input={
                "audio_duration_seconds": 120,
            },
        ) as transcription:
            transcription.update(
                output={
                    "status": "completed",
                    "segments": 18,
                    "characters": 850,
                }
            )

        # Simulation d’un appel à un modèle.
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="generation-compte-rendu",
            model="modele-de-test",
            input=[
                {
                    "role": "system",
                    "content": "Produis un compte rendu structuré.",
                },
                {
                    "role": "user",
                    "content": "Transcription fictive utilisée uniquement pour le test.",
                },
            ],
            model_parameters={
                "temperature": 0.2,
                "max_tokens": 1000,
            },
        ) as generation:
            generation.update(
                output={
                    "summary_short": "Résumé fictif de la réunion.",
                    "status": "completed",
                },
                usage_details={
                    "input": 25,
                    "output": 12,
                    "total": 37,
                },
            )

        traitement.update(
            output={
                "status": "completed",
                "document_created": True,
            }
        )

    # Attend l’envoi des événements avant la fermeture du script.
    langfuse.flush()

    print("Trace envoyée à Langfuse.")


if __name__ == "__main__":
    test_langfuse()