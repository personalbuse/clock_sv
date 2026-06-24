import email
import email.policy
import imaplib
import logging
import threading
import time
from email.utils import parsedate_to_datetime

EMAIL_SYSTEM_PROMPT = (
    "Eres un asistente que evalúa si un correo electrónico es importante "
    "para el usuario. Responde ÚNICAMENTE con una línea con el siguiente formato:\n"
    "IMPORTANTE:|<resumen máximo 15 palabras>\n"
    "o si no es importante:\n"
    "NO_IMPORTANTE\n\n"
    "Correo:\n"
)


class EmailMonitor:
    def __init__(self, config: dict, on_alert):
        ec = config.get("email", {})
        self._enabled = ec.get("enabled", False)
        self._server = ec.get("imap_server", "imap.gmail.com")
        self._port = ec.get("imap_port", 993)
        self._username = ec.get("username", "")
        self._password = ec.get("password", "")
        self._interval = ec.get("check_interval_seconds", 30)
        self._max_body = ec.get("max_body_chars", 500)
        self._max_per_cycle = ec.get("max_emails_per_check", 5)
        self._on_alert = on_alert

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._announced_ids: set[str] = set()

        llm_cfg = config.get("llm", {})
        self._llm_provider = llm_cfg.get("provider", "ollama")
        self._groq_api_key = config.get("groq_api_key", "")
        self._groq_model = llm_cfg.get("groq", {}).get("model", "llama-3.1-8b-instant")
        self._ollama_endpoint = llm_cfg.get("ollama", {}).get("endpoint", "http://localhost:11434")
        self._ollama_model = llm_cfg.get("ollama", {}).get("model", "qwen2.5:3b")

    def start(self) -> None:
        if not self._enabled or not self._username or not self._password:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._check_email()
            except Exception as e:
                logging.error("email_monitor: %s", e)
            self._stop.wait(self._interval)

    def _check_email(self) -> None:
        mail = imaplib.IMAP4_SSL(self._server, self._port)
        mail.login(self._username, self._password)
        mail.select("INBOX")
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            mail.logout()
            return

        num_ids = data[0].split()
        checked = 0
        for raw_id in num_ids:
            if checked >= self._max_per_cycle:
                break
            msg_id = raw_id.decode()
            if msg_id in self._announced_ids:
                continue
            checked += 1

            result2, data2 = mail.fetch(raw_id, "(BODY.PEEK[])")
            if result2 != "OK":
                continue

            raw_email = data2[0][1]
            msg = email.message_from_bytes(raw_email, policy=email.policy.default)
            sender = msg.get("From", "desconocido")
            subject = msg.get("Subject", "sin asunto")
            body = self._get_body_preview(msg)

            importance, summary = self._evaluate(sender, subject, body)
            if importance:
                self._announced_ids.add(msg_id)
                self._on_alert(sender, summary)

        mail.logout()

    @staticmethod
    def _get_body_preview(msg: email.message.Message, max_chars: int = 500) -> str:
        parts: list[str] = []
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_content()
                    if isinstance(payload, str):
                        parts.append(payload)
                except Exception:
                    continue
        full = "\n".join(parts).strip()
        return full[:max_chars]

    def _evaluate(self, sender: str, subject: str, body: str) -> tuple[bool, str]:
        text = (
            f"De: {sender}\n"
            f"Asunto: {subject}\n"
            f"Contenido: {body[:300]}"
        )
        try:
            if self._llm_provider == "groq":
                return self._evaluate_groq(text)
            return self._evaluate_ollama(text)
        except Exception as e:
            logging.error("email_monitor LLM eval failed: %s", e)
            return False, ""

    def _evaluate_groq(self, text: str) -> tuple[bool, str]:
        from groq import Groq
        client = Groq(api_key=self._groq_api_key)
        response = client.chat.completions.create(
            model=self._groq_model,
            messages=[
                {"role": "system", "content": EMAIL_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=80,
            timeout=15,
        )
        result = (response.choices[0].message.content or "").strip()
        return self._parse_evaluation(result)

    def _evaluate_ollama(self, text: str) -> tuple[bool, str]:
        import requests
        resp = requests.post(
            f"{self._ollama_endpoint}/api/chat",
            json={
                "model": self._ollama_model,
                "messages": [
                    {"role": "system", "content": EMAIL_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 80},
            },
            timeout=30,
        )
        resp.raise_for_status()
        result = (resp.json()["message"].get("content") or "").strip()
        return self._parse_evaluation(result)

    @staticmethod
    def _parse_evaluation(result: str) -> tuple[bool, str]:
        if result.startswith("IMPORTANTE"):
            _, _, summary = result.partition("|")
            summary = summary.strip().strip(".").strip()
            if not summary:
                summary = "correo importante"
            return True, summary
        return False, ""
