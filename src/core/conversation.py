from datetime import datetime


class Conversation:
    def __init__(self, id: int):
        self.id = id
        self.messages: list[dict] = []
        self.created = datetime.now()

    def add(self, role: str, text: str) -> None:
        self.messages.append({
            "role": role,
            "text": text,
            "timestamp": datetime.now(),
        })

    @property
    def summary(self) -> str:
        if not self.messages:
            return "nueva"
        last = self.messages[-1]
        text = last["text"]
        if len(text) > 40:
            text = text[:37] + "..."
        return f"{last['role']}: {text}"

    @property
    def llm_messages(self) -> list[dict]:
        result = []
        for m in self.messages:
            role = "user" if m["role"] == "user" else "assistant"
            result.append({"role": role, "content": m["text"]})
        return result

    def __repr__(self) -> str:
        return f"Conv#{self.id} ({len(self.messages)} msgs): {self.summary}"


class ConversationManager:
    def __init__(self, max_tokens: int = 2048):
        self._conversations: list[Conversation] = []
        self._current_id: int | None = None
        self._next_id = 1
        self.max_tokens = max_tokens

    @property
    def current(self) -> Conversation | None:
        if self._current_id is None:
            return None
        for c in self._conversations:
            if c.id == self._current_id:
                return c
        return None

    def new(self) -> Conversation:
        c = Conversation(self._next_id)
        self._next_id += 1
        self._conversations.append(c)
        self._current_id = c.id
        return c

    def switch_to(self, conv_id: int) -> bool:
        for c in self._conversations:
            if c.id == conv_id:
                self._current_id = c.id
                return True
        return False

    def add_message(self, role: str, text: str) -> None:
        c = self.current
        if c is None:
            c = self.new()
        c.add(role, text)

    @property
    def conversations(self) -> list[Conversation]:
        return list(self._conversations)

    def get_llm_context(self, system_prompt: str) -> list[dict]:
        c = self.current
        if c is None or not c.messages:
            return [{"role": "system", "content": system_prompt}]
        msgs = [{"role": "system", "content": system_prompt}]
        for m in c.messages[-20:]:
            role = "user" if m["role"] == "user" else "assistant"
            msgs.append({"role": role, "content": m["text"]})
        return msgs
