import unittest
from unittest.mock import patch
from src.services.stt_groq import transcribe
from src.services.llm_groq import ask
from src.services.tts_gemini import synthesize


class TestSTTMock(unittest.TestCase):
    @patch("src.services.stt_groq.Groq")
    def test_transcribe_success(self, mock_groq):
        mock_groq.return_value.audio.transcriptions.create.return_value = "hola"
        result = transcribe(b"audio", api_key="test")
        self.assertEqual(result, "hola")


class TestLLMMock(unittest.TestCase):
    @patch("src.services.llm_groq.Groq")
    def test_ask_success(self, mock_groq):
        mock_response = type("Resp", (), {
            "choices": [type("Ch", (), {
                "message": type("M", (), {"content": "Hola Mundo"})()
            })()]
        })()
        mock_groq.return_value.chat.completions.create.return_value = mock_response
        result = ask("test", api_key="test")
        self.assertEqual(result, "Hola Mundo")


class TestTTSMock(unittest.TestCase):
    @patch("src.services.tts_gemini.genai")
    def test_synthesize_success(self, mock_genai):
        mock_part = type("Part", (), {
            "inline_data": type("D", (), {"data": b"audio_data"})()
        })()
        mock_candidate = type("Cand", (), {
            "content": type("C", (), {"parts": [mock_part]})()
        })()
        mock_genai.Client.return_value.models.generate_content.return_value = type(
            "Resp", (), {"candidates": [mock_candidate]})()

        result = synthesize("test", api_key="test")
        self.assertEqual(result, b"audio_data")
