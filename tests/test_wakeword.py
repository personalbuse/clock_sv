import unittest
from unittest.mock import patch
from src.audio.wakeword import WakeWordDetector


class TestWakeWord(unittest.TestCase):
    @patch("src.audio.wakeword.WhisperModel")
    def test_detection_above_threshold(self, mock_model):
        seg = type("Seg", (), {"text": "servidor"})()
        mock_model.return_value.transcribe.return_value = ([seg], None)
        detector = WakeWordDetector(word="servidor", threshold=80)
        chunk = b"\x00" * 640
        for i in range(100):
            result = detector.feed(chunk)
            if result:
                self.assertTrue(result)
                return
        self.fail("word not detected after 100 chunks")
