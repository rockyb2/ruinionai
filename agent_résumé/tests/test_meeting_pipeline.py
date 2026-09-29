"""Real HTTP/ORM lifecycle tests; providers are mocked, Word rendering is real."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "pipeline-tests-only-not-a-production-secret-key")
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError
from auth.dependencies import get_current_user
from database import Base, get_db
from meeting_content import MeetingContent, configured_models, generate_content
from meeting_processing import claim_next, process_claim, recover_expired, run_stage, save_owned, stage_timeout, StageError
from models import Meeting, Organization, OrganizationMember, User
from processing_task import _transcribe_recording, execute
from routes.meetings import router

CONTENT = {
    "summary_short": "Le calendrier est validé. Awa enverra le planning.",
    "report": {"resume_long": "L’équipe a validé le calendrier de lancement.",
               "points_importants": ["Le calendrier"], "decisions": ["Calendrier validé"],
               "actions": [{"action": "Envoyer le planning", "responsable": "Awa", "echeance": "Non précisé"}],
               "questions_ouvertes": [], "risques_blocages": []},
}
SUMMARIES = MeetingContent.model_validate(CONTENT).summaries()


class MeetingPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {"AUDIO_DIR": str(self.directory / "audio"),
                                                    "REPORTS_DIR": str(self.directory / "reports")})
        self.environment.start()
        self.engine = create_engine("sqlite:///" + str(self.directory / "test.db"), connect_args={"check_same_thread": False})
        event.listen(self.engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            db.add_all([Organization(id=1, name="Équipe"), Organization(id=2, name="Autre")])
            db.add_all([User(id=1, first_name="Awa", last_name="Koné", email="awa@example.test", is_active=True),
                        User(id=2, first_name="Autre", email="other@example.test", is_active=True)])
            db.flush()
            db.add_all([OrganizationMember(id=1, user_id=1, organization_id=1, role="owner", status="active"),
                        OrganizationMember(id=2, user_id=2, organization_id=2, role="owner", status="active")])
            db.add(Meeting(id=1, organization_id=1, title="Budget d’équipe", created_by_user_id=1,
                           participants="Awa", transcription="Le calendrier est validé. Awa envoie le planning."))
            db.commit()
        self.user_id = 1
        app = FastAPI()
        app.include_router(router)
        def get_test_db():
            with self.sessions() as db:
                yield db
        def current_user(db=Depends(get_db)):
            return db.get(User, self.user_id)
        app.dependency_overrides[get_db] = get_test_db
        app.dependency_overrides[get_current_user] = current_user
        self.client = TestClient(app, headers={"X-Organization-Id": "1"})

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        self.environment.stop()
        self.temp.cleanup()

    def get(self):
        response = self.client.get("/meetings/1")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def enqueue(self):
        response = self.client.post("/meetings/1/summary")
        self.assertEqual(response.status_code, 202, response.text)
        return response.json()

    def change(self, **values):
        with self.sessions() as db:
            meeting = db.get(Meeting, 1)
            for key, value in values.items():
                setattr(meeting, key, value)
            db.commit()

    def work(self, runner):
        claim = claim_next(self.sessions)
        self.assertIsNotNone(claim)
        with patch("meeting_processing.configured_models", return_value=["first", "second"]):
            asyncio.run(process_claim(*claim, self.sessions, runner))

    def test_atomic_queue_and_claim_are_idempotent_under_concurrency(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda _: self.enqueue(), range(4)))
        self.assertTrue(all(result["processing_status"] == "queued" for result in results))
        with ThreadPoolExecutor(max_workers=4) as executor:
            claims = list(executor.map(lambda _: claim_next(self.sessions), range(4)))
        self.assertEqual(sum(claim is not None for claim in claims), 1)
        self.assertEqual(self.enqueue()["processing_status"], "writing")
        self.assertNotIn("processing_token", self.get())

    def test_content_commits_before_real_word_and_completed_request_reuses_result(self):
        self.enqueue()
        async def runner(payload, timeout):
            if payload["stage"] == "writing":
                self.assertEqual(timeout, 30)
                return SUMMARIES
            with self.sessions() as db:
                saved = db.get(Meeting, 1)
                self.assertEqual(saved.summary_short, SUMMARIES["summary_short"])
                self.assertEqual(saved.processing_status, "building")
                self.assertIsNone(saved.report_path)
            return execute(payload)
        self.work(runner)
        result = self.get()
        self.assertEqual(result["processing_status"], "completed")
        self.assertTrue(Path(result["report_path"]).is_file())
        self.assertEqual(self.client.get("/meetings/1/report").status_code, 200)
        self.assertEqual(self.client.post("/meetings/1/summary").status_code, 200)
        self.assertIsNone(claim_next(self.sessions))

    def test_word_failure_retains_summaries_and_retry_only_builds_word(self):
        self.enqueue()
        calls = []
        async def fails_word(payload, timeout):
            calls.append(payload["stage"])
            if payload["stage"] == "writing":
                return SUMMARIES
            raise StageError("Word indisponible")
        self.work(fails_word)
        result = self.get()
        self.assertEqual(result["processing_status"], "failed")
        self.assertEqual(result["summary_short"], SUMMARIES["summary_short"])
        self.enqueue()
        async def only_word(payload, timeout):
            self.assertEqual(payload["stage"], "building")
            return execute(payload)
        self.work(only_word)
        self.assertEqual(calls, ["writing", "building"])
        self.assertEqual(self.get()["processing_status"], "completed")

    def test_two_model_limit_and_fallback(self):
        self.enqueue()
        calls = []
        async def fail(payload, timeout):
            calls.append(payload["model"])
            raise StageError("Réponse invalide")
        self.work(fail)
        self.assertEqual(calls, ["first", "second"])
        result = self.get()
        self.assertEqual(result["processing_status"], "failed")
        self.assertEqual(result["processing_error"],
                         "Le résumé et le compte rendu n’ont pas pu être générés. Réessayez dans quelques instants.")
        self.assertIsNone(result["summary_short"])
        self.enqueue()
        async def fallback(payload, timeout):
            if payload["stage"] == "building":
                return execute(payload)
            if payload["model"] == "first":
                raise StageError("Connexion impossible")
            return SUMMARIES
        self.work(fallback)
        self.assertEqual(self.get()["processing_status"], "completed")

    def test_interrupted_lease_retains_text_and_rejects_late_writes(self):
        self.change(**SUMMARIES, processing_status="building", processing_token="old",
                    processing_expires_at=datetime.utcnow() - timedelta(seconds=1))
        recover_expired(self.sessions)
        self.assertEqual(self.get()["processing_status"], "failed")
        self.enqueue()
        claim = claim_next(self.sessions)
        with self.assertRaises(StageError):
            save_owned(1, "old", {"summary_short": "Wrong late result"}, self.sessions)
        self.assertEqual(self.get()["summary_short"], SUMMARIES["summary_short"])
        self.assertIsNotNone(claim)

    def test_upload_persists_order_and_queues_without_calling_provider(self):
        self.change(transcription=None)
        payload = [('files', ('first.webm', b'first', 'audio/webm')), ('files', ('second.m4a', b'second', 'audio/mp4'))]
        response = self.client.post('/meetings/1/audio', files=payload)
        self.assertEqual(response.status_code, 202, response.text)
        self.assertEqual(response.json()["processing_status"], "queued")
        with self.sessions() as db:
            manifest = db.get(Meeting, 1).audio_manifest
            self.assertEqual([Path(part["path"]).read_bytes() for part in manifest], [b'first', b'second'])
        again = self.client.post('/meetings/1/audio', files=payload)
        self.assertEqual(again.status_code, 202)
        with self.sessions() as db:
            self.assertEqual(db.get(Meeting, 1).audio_manifest, manifest)
        calls = []
        async def runner(payload, timeout):
            calls.append(payload["stage"])
            if payload["stage"] == "preparing":
                path = self.directory / "audio" / "playback.mp3"
                path.write_bytes(b"0123456789")
                return {"audio_path": str(path), "audio_duration": 60}
            if payload["stage"] == "transcribing":
                return {"transcription": "Bonjour", "transcription_segments": [{"start": 0, "end": 2, "text": "Bonjour"}]}
            if payload["stage"] == "writing":
                return SUMMARIES
            return execute(payload)
        self.work(runner)
        self.assertEqual(calls, ["preparing", "transcribing", "writing", "building"])
        audio = self.client.get('/meetings/1/audio', headers={"Range": "bytes=2-4"})
        self.assertEqual(audio.status_code, 206)
        self.assertEqual(audio.content, b"234")
        self.assertEqual(audio.headers["cache-control"], "private, no-store")
        self.assertTrue(self.get()["audio_available"])
        self.assertEqual(self.get()["transcription_segments"][0]["start"], 0)

    def test_audio_validation_limits_and_authorization(self):
        self.change(transcription=None)
        for files, status in [
            (None, 400),
            ({'file': ('empty.mp3', b'', 'audio/mpeg')}, 422),
            ({'file': ('evil.html', b'<script>', 'text/html')}, 422),
            ([('file', ('a.mp3', b'one', 'audio/mpeg')), ('files', ('b.webm', b'two', 'audio/webm'))], 400),
        ]:
            self.assertEqual(self.client.post('/meetings/1/audio', files=files).status_code, status)
        with patch('routes.meetings.MAX_AUDIO_BYTES', 5):
            self.assertEqual(self.client.post('/meetings/1/audio', files=[
                ('files', ('a.webm', b'123', 'audio/webm')), ('files', ('b.webm', b'456', 'audio/webm')),
            ]).status_code, 413)
        self.assertFalse(self.get()["has_source_audio"])
        self.user_id = 2
        self.client.headers['X-Organization-Id'] = '2'
        for suffix in ('', '/audio', '/report'):
            self.assertEqual(self.client.get('/meetings/1' + suffix).status_code, 404)
        self.assertEqual(self.client.post('/meetings/1/summary').status_code, 404)
        self.assertEqual(self.client.post('/meetings/1/audio', files={'file': ('a.mp3', b'a', 'audio/mpeg')}).status_code, 404)

    def test_audio_path_is_confined_and_legacy_audio_absence_is_honest(self):
        self.assertFalse(self.get()['audio_available'])
        self.assertEqual(self.client.get('/meetings/1/audio').status_code, 404)
        outside = self.directory / 'private.txt'
        outside.write_text('not audio')
        self.change(audio_path=str(outside))
        self.assertEqual(self.client.get('/meetings/1/audio').status_code, 404)


class ModelBoundaryTests(unittest.TestCase):
    def test_long_transcription_timeout_scales_by_ten_minute_chunks(self):
        self.assertEqual(stage_timeout("transcribing", 60), 120)
        self.assertEqual(stage_timeout("transcribing", 2469), 480)
        self.assertEqual(stage_timeout("writing", 2469), 30)

    @patch("processing_task._split_audio")
    @patch("transcription_service.transcribe_audio_with_segments")
    def test_long_recording_merges_chunks_and_offsets(self, transcribe, split):
        split.return_value = [(Path("one.mp3"), 0.0, 600.0),
                              (Path("two.mp3"), 600.0, 20.0)]
        transcribe.side_effect = [
            {"transcription": "Premier", "transcription_segments": [
                {"start": 1.0, "end": 2.0, "text": "Premier"}]},
            {"transcription": "Second", "transcription_segments": [
                {"start": 601.0, "end": 602.0, "text": "Second"}]},
        ]
        with patch.object(Path, "read_bytes", return_value=b"audio"):
            result = _transcribe_recording(Path("recording.mp3"), 920)
        self.assertEqual(result["transcription"], "Premier Second")
        self.assertEqual(result["transcription_segments"][-1]["start"], 601.0)
        self.assertEqual(transcribe.call_args_list[1].kwargs["timestamp_offset"], 600.0)

    def test_invalid_json_empty_and_missing_sections_are_rejected(self):
        for invalid in ['print("hello")', '{"summary_short":"ok"}', json.dumps({**CONTENT, "summary_short": "  "})]:
            with self.assertRaises(ValidationError):
                MeetingContent.model_validate_json(invalid)
        value = json.loads(json.dumps(CONTENT))
        value['report'].pop('decisions')
        with self.assertRaises(ValidationError):
            MeetingContent.model_validate(value)

    def test_model_config_deduplicates_and_keeps_all_fallbacks(self):
        with patch.dict(os.environ, {"OPENROUTER_MODEL_ID": "o*/nvidia/test", "MISTRAL_MODEL_ID": "mistral/test", "MISTRAL_MODEL_ID2": "third"}, clear=True):
            self.assertEqual(configured_models(), ['mistral/test', 'third', 'openrouter/nvidia/test'])
        with patch.dict(os.environ, {"SUMMARY_MODEL_IDS": "o*/nvidia/test,mistral-small-2603,mistral/ignored"}, clear=True):
            self.assertEqual(configured_models(), ['openrouter/nvidia/test', 'mistral/mistral-small-2603', 'mistral/ignored'])

    def test_free_model_uses_validated_json_without_unsupported_json_mode(self):
        answer = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(
            content="```json\n" + json.dumps(CONTENT, ensure_ascii=False) + "\n```"))])
        completion = Mock(return_value=answer)
        fake_litellm = ModuleType("litellm")
        fake_litellm.completion = completion
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-key"}, clear=True), \
             patch.dict(sys.modules, {"litellm": fake_litellm}):
            result = generate_content({"transcription": "Awa envoie le planning."}, "openrouter/nvidia/nemotron-3.5-lightning:free")
        self.assertEqual(result, SUMMARIES)
        arguments = completion.call_args.kwargs
        self.assertNotIn("response_format", arguments)
        self.assertEqual(arguments["max_tokens"], 3000)
        self.assertEqual(arguments["num_retries"], 0)

    def test_mistral_uses_json_mode_and_rejects_incomplete_response(self):
        answer = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(
            content=json.dumps(CONTENT, ensure_ascii=False)))])
        completion = Mock(return_value=answer)
        fake_litellm = ModuleType("litellm")
        fake_litellm.completion = completion
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"}, clear=True), \
             patch.dict(sys.modules, {"litellm": fake_litellm}):
            self.assertEqual(generate_content({"transcription": "Awa envoie le planning."}, "mistral/mistral-small-2603"), SUMMARIES)
        self.assertEqual(completion.call_args.kwargs["response_format"], {"type": "json_object"})

    def test_timeout_kills_process_and_waits_for_exit(self):
        class SlowProcess:
            returncode = None
            killed = False
            async def wait(self):
                if self.killed:
                    self.returncode = -9
                    return -9
                await asyncio.sleep(60)
            def kill(self):
                self.killed = True
        process = SlowProcess()
        with patch('meeting_processing.asyncio.create_subprocess_exec', new=AsyncMock(return_value=process)):
            with self.assertRaisesRegex(StageError, 'Délai'):
                asyncio.run(run_stage({'stage': 'writing'}, .01))
        self.assertTrue(process.killed)
        self.assertEqual(process.returncode, -9)


if __name__ == '__main__':
    unittest.main()
