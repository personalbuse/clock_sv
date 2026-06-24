import unittest
from src.audio.wakeword import WakeWordDetector


class TestWakeWord(unittest.TestCase):
    def test_silence_returns_false(self):
        detector = WakeWordDetector(word="servidor", threshold=80)
        for _ in range(200):
            result = detector.feed(b"\x00" * 640)
            if result:
                self.fail("silence triggered detection")
        self.assertFalse(result)
