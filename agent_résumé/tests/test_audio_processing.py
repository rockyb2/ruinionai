import math
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from audio_processing import AudioValidationError, audio_input_format, merge_audio_segments


class AudioValidationTests(unittest.TestCase):
    def test_known_formats_and_codec_parameters(self):
        self.assertEqual(audio_input_format('audio/webm;codecs=opus'), 'matroska')
        self.assertEqual(audio_input_format('audio/mp4'), 'mov')
        with self.assertRaises(AudioValidationError):
            audio_input_format('application/x-mpegurl')

    def test_empty_segment_list_is_rejected(self):
        with self.assertRaises(AudioValidationError):
            merge_audio_segments([])

    def test_missing_ffmpeg_reports_configuration_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'audio'
            path.write_bytes(b'audio')
            with patch('audio_processing.shutil.which', return_value=None):
                with self.assertRaisesRegex(RuntimeError, 'FFmpeg'):
                    merge_audio_segments([(path, 'audio/webm')])


@unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg is required for media integration tests')
class AudioMergeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def tone(self, name, frequency, seconds=1):
        path = self.directory / name
        samples = [int(12000 * math.sin(2 * math.pi * frequency * index / 16000))
                   for index in range(int(seconds * 16000))]
        with wave.open(str(path), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        return path

    def test_mixed_webm_and_mp4_retain_duration_and_order(self):
        parts = []
        for index, (frequency, extension, codec, mime) in enumerate([
            (440, 'webm', 'libopus', 'audio/webm;codecs=opus'),
            (880, 'm4a', 'aac', 'audio/mp4'),
        ]):
            source = self.tone(f'{index}.wav', frequency)
            target = self.directory / f'{index}.{extension}'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-c:a', codec, str(target)], check=True)
            parts.append((target, mime))

        merged = self.directory / 'merged.mp3'
        merged.write_bytes(merge_audio_segments(parts))
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(merged), '-ar', '16000', '-ac', '1',
                                  '-f', 's16le', 'pipe:1'], check=True, capture_output=True).stdout
        samples = struct.unpack(f'<{len(decoded) // 2}h', decoded)
        self.assertAlmostEqual(len(samples) / 16000, 2, delta=0.15)
        # Verify content order, not just that FFmpeg created a file.
        for start, expected in [(0.2, 440), (1.2, 880)]:
            section = samples[int(start * 16000):int((start + 0.5) * 16000)]
            crossings = sum(a <= 0 < b for a, b in zip(section, section[1:]))
            self.assertAlmostEqual(crossings / 0.5, expected, delta=10)

    def test_invalid_audio_is_rejected_before_transcription(self):
        path = self.directory / 'bad.webm'
        path.write_bytes(b'not an audio file')
        with self.assertRaises(AudioValidationError):
            merge_audio_segments([(path, 'audio/webm')])

    def test_duration_limit_is_enforced(self):
        path = self.tone('long.wav', 440, seconds=2)
        with patch('audio_processing.MAX_AUDIO_SECONDS', 1):
            with self.assertRaisesRegex(AudioValidationError, 'durée'):
                merge_audio_segments([(path, 'audio/wav')])


if __name__ == '__main__':
    unittest.main()
