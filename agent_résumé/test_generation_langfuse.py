import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

# Les imports applicatifs viennent après le chargement du .env.
from meeting_content import configured_models, generate_content


def main():
    models = configured_models()

    if not models:
        raise RuntimeError(
            "Aucun modèle configuré dans SUMMARY_MODEL_IDS."
        )

    # Tu peux définir TEST_MODEL_ID pour choisir un modèle précis.
    model = os.getenv("TEST_MODEL_ID", "").strip() or models[0]

    context = {
        "title": "Réunion fictive de test Langfuse",
        "organization": "Organisation de démonstration",
        "participants": "Awa, Karim",
        "date": "02/10/2026 10:00",
        "transcription": (
            "Awa propose de publier la nouvelle version vendredi. "
            "Karim doit terminer les tests avant jeudi à 17 heures. "
            "L’équipe valide cette organisation. "
            "Le principal risque identifié est un retard dans les tests."
        ),
    }

    print(f"Modèle appelé : {model}")
    print("Génération en cours...")

    result = generate_content(context, model)

    print("\nGénération réussie.")
    print("\nRésumé court :")
    print(result["summary_short"])

    print("\nCompte rendu :")
    print(result["summary_long"])

    print("\nConsulte maintenant la trace dans Langfuse.")


if __name__ == "__main__":
    main()