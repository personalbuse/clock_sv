import unittest
from src.audio.vad import VAD


class TestVAD(unittest.TestCase):
    def setUp(self):
        self.vad = VAD(aggressiveness=2)

    def test_frame_size_is_correct(self):
        self.assertEqual(self.vad.frame_size, 320)

    def test_silence_is_not_speech(self):
        frame = b"\x00" * 640
        self.assertFalse(self.vad.is_speech_chunk(frame))

    def test_wrong_size_returns_false(self):
        frame = b"\x00" * 100
        self.assertFalse(self.vad.is_speech_chunk(frame))
