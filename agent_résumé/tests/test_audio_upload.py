"""Exercise the multipart endpoint without calling a provider or a real database."""
import importlib.util
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

HAS_DEPENDENCIES = all(importlib.util.find_spec(name) for name in ['fastapi', 'sqlalchemy', 'elevenlabs'])

if HAS_DEPENDENCIES:
    # These values are for this isolated test process only.
    os.environ['DATABASE_URL'] = 'sqlite://'
    os.environ['SECRET_KEY'] = 'audio-tests-only-not-a-production-secret-key'
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from routes import meetings


@unittest.skipUnless(HAS_DEPENDENCIES, 'Run inside the backend image with its Python dependencies')
class AudioUploadTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(meetings.router)
        self.db = Mock()
        app.dependency_overrides[meetings.get_db] = lambda: self.db
        app.dependency_overrides[meetings.get_auth_context] = lambda: SimpleNamespace()
        self.client = TestClient(app)
        self.meeting = SimpleNamespace(id=1, title='Test', transcription=None)
        self.lookup = patch.object(meetings, 'get_meeting_for_current_org', return_value=self.meeting)
        self.lookup.start()
        self.transcriber = patch.object(meetings, 'transcribe_audio', return_value='Bonjour tout le monde.')
        self.transcribe = self.transcriber.start()

    def tearDown(self):
        self.client.close()
        self.lookup.stop()
        self.transcriber.stop()

    def test_imported_file_keeps_existing_contract(self):
        response = self.client.post('/meetings/1/audio', files={'file': ('test.mp3', b'audio', 'audio/mpeg')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['transcription'], 'Bonjour tout le monde.')
        self.assertEqual(self.transcribe.call_args.kwargs['audio_bytes'], b'audio')

    def test_segments_are_joined_in_order_then_transcribed_once(self):
        def merge(parts):
            self.assertEqual([path.read_bytes() for path, _ in parts], [b'first', b'second'])
            self.assertEqual([mime for _, mime in parts], ['audio/webm', 'audio/mp4'])
            return b'merged audio'
        with patch.object(meetings, 'merge_audio_segments', side_effect=merge):
            response = self.client.post('/meetings/1/audio', files=[
                ('files', ('first.webm', b'first', 'audio/webm')),
                ('files', ('second.m4a', b'second', 'audio/mp4')),
            ])
        self.assertEqual(response.status_code, 200)
        self.transcribe.assert_called_once_with(audio_bytes=b'merged audio', file_name='note-vocale.mp3',
                                                content_type='audio/mpeg', language='fr')

    def test_ambiguous_or_empty_upload_does_not_call_provider(self):
        for payload in [None, [
            ('file', ('one.mp3', b'one', 'audio/mpeg')),
            ('files', ('two.webm', b'two', 'audio/webm')),
        ]]:
            response = self.client.post('/meetings/1/audio', files=payload)
            self.assertEqual(response.status_code, 400)
        self.transcribe.assert_not_called()

    def test_size_limit_covers_all_parts(self):
        with patch.object(meetings, 'MAX_AUDIO_BYTES', 5):
            response = self.client.post('/meetings/1/audio', files=[
                ('files', ('one.webm', b'123', 'audio/webm')),
                ('files', ('two.webm', b'456', 'audio/webm')),
            ])
        self.assertEqual(response.status_code, 413)
        self.transcribe.assert_not_called()

    def test_authorization_happens_before_audio_processing(self):
        with patch.object(meetings, 'get_meeting_for_current_org', side_effect=HTTPException(404, 'Not found')):
            response = self.client.post('/meetings/1/audio', files={'file': ('test.mp3', b'audio', 'audio/mpeg')})
        self.assertEqual(response.status_code, 404)
        self.transcribe.assert_not_called()

    def test_empty_segment_does_not_call_provider(self):
        response = self.client.post('/meetings/1/audio', files=[('files', ('empty.webm', b'', 'audio/webm'))])
        self.assertEqual(response.status_code, 422)
        self.transcribe.assert_not_called()


if __name__ == '__main__':
    unittest.main()
