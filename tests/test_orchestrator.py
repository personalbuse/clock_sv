import unittest
from unittest.mock import MagicMock, patch
from src.core.orchestrator import Orchestrator, State


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.config = {
            "audio": {"sample_rate": 16000, "device": "default"},
            "vad": {"aggressiveness": 2},
            "wake_word": {"word": "servidor", "threshold": 80},
            "stt": {"model": "test"},
            "llm": {"model": "test"},
            "tts": {"model": "test", "voice": "test"},
        }
        self.status = MagicMock()
        self.orch = Orchestrator(self.config, self.status)

    def test_initial_state(self):
        self.assertEqual(self.orch.state, State.IDLE)

    def test_ptt_starts_listening(self):
        self.orch.press_ptt()
        self.assertEqual(self.orch.state, State.LISTENING)

    def test_ptt_release_goes_to_transcribing(self):
        self.orch.press_ptt()
        self.orch._audio_buffer = [b"\x00" * 320]
        self.orch.release_ptt()
        self.assertEqual(self.orch.state, State.TRANSCRIBING)
