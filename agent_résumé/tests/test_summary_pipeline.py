"""Vérifie la sauvegarde du résumé après l'appel à BuildWord, sans API externe."""

import importlib.util
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


HAS_DEPENDENCIES = all(importlib.util.find_spec(name) for name in ("fastapi", "sqlalchemy", "docx"))

if HAS_DEPENDENCIES:
    os.environ.setdefault("DATABASE_URL", "sqlite://")
    os.environ.setdefault("SECRET_KEY", "summary-tests-only-not-a-production-secret-key")
    from routes import meetings
    from tools import BuildWord


@unittest.skipUnless(HAS_DEPENDENCIES, "Run inside the backend image")
class SummaryPipelineTests(unittest.TestCase):
    def test_summary_is_extracted_and_saved_after_build_word(self):
        meeting = SimpleNamespace(
            id=42,
            title="Réunion test",
            transcription="Le calendrier est validé. Awa envoie le planning.",
            participants="Awa, Boris",
            created_at=datetime(2026, 9, 20, 9, 0),
            summary_short=None,
            summary_long=None,
            report_path=None,
        )
        auth_context = SimpleNamespace(
            membership=SimpleNamespace(organization=SimpleNamespace(name="Entreprise test"))
        )
        db = Mock()
        output = """RESUME_COURT:
Le calendrier est validé.
COMPTE_RENDU_DETAILLE:
1. Résumé long
Le calendrier a été discuté.
2. Points importants
- Le lancement est planifié.
3. Décisions prises
- Le calendrier est validé.
4. Actions à faire
- Action : Envoyer le planning | Responsable : Awa | Échéance : Non précisée
5. Questions ouvertes
Non précisé
6. Risques ou blocages
Non précisé"""

        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"REPORTS_DIR": directory}):
            def fake_agent(prompt):
                self.assertIn('template="meeting_report"', prompt)
                result = BuildWord().forward(
                    title=meeting.title,
                    date="20/09/2026 09:00",
                    body=output,
                    filename="meeting-42-test",
                    template="meeting_report",
                    organization="Entreprise test",
                    participants=meeting.participants,
                )
                self.assertTrue(Path(directory, "meeting-42-test.docx").exists(), result)
                return output + "\nWORD_PATH:\n" + str(Path(directory, "meeting-42-test.docx"))

            with patch.object(meetings, "get_meeting_for_current_org", return_value=meeting), \
                 patch.object(meetings, "build_report_filename_stem", return_value="meeting-42-test"), \
                 patch.object(meetings, "run_with_model_fallback", side_effect=fake_agent):
                result = meetings.summarize_meeting(42, db, auth_context)

            self.assertIs(result, meeting)
            self.assertEqual(meeting.summary_short, "Le calendrier est validé.")
            self.assertIn("Le calendrier a été discuté.", meeting.summary_long)
            self.assertTrue(Path(meeting.report_path).exists())
            db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
