"""Core Intent Router and conversational coordinator."""

import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from victor.core.persona import format_system_prompt, is_indonesian
from victor.engines.llm.base import LLMEngine
from victor.plugins.registry import PluginRegistry, get_registry

YES_PATTERNS = re.compile(r"\b(ya|iya|iyah|yes|yeah|yep|oke|okay|ok|lanjut|betul|benar|boleh|sure|do it|go ahead)\b", re.I)


class IntentRouter:
    """Evaluates transcription text, dispatches to plugins, or invokes LLM fallback."""

    def __init__(self, registry: Optional[PluginRegistry] = None, llm: Optional[LLMEngine] = None) -> None:
        self.registry = registry or get_registry()
        self.llm = llm
        self.pending_confirmation: Optional[Tuple[str, Callable[[], None]]] = None
        self.conversation_history: List[Tuple[str, str]] = []
        self.system_prompt = format_system_prompt()

    def route(self, transcription: str) -> str:
        """Process incoming transcribed speech and return verbal response."""
        t = transcription.strip()
        cleaned = re.sub(r"^(hey|hai|halo)?\s*(victor|jarvis)[,.]?\s*", "", t, flags=re.I).strip(" .!?")

        # 1. Evaluate pending confirmation (e.g., shutdown, reboot)
        if self.pending_confirmation:
            msg, action = self.pending_confirmation
            self.pending_confirmation = None
            if YES_PATTERNS.search(cleaned) and not re.search(r"\b(no|nggak|gak|ga|tidak|jangan)\b", cleaned, re.I):
                threading.Timer(2.0, action).start()
                return msg
            return "Very well, sir. Action cancelled."

        if not cleaned:
            return "Yes, sir?"

        if re.search(r"\b(never ?mind|cancel|batal|(nggak|gak|ga|tidak) jadi)\b", cleaned, re.I):
            return "Very well, sir."

        # 2. Check for destructive system power commands requiring confirmation
        if re.search(r"\b(shut ?down|power off|matikan (laptop|komputer|pc)|matiin (laptop|komputer|pc))\b", cleaned, re.I):
            import subprocess
            self.pending_confirmation = ("Shutting down, sir.", lambda: subprocess.run(["systemctl", "poweroff"]))
            return "Shall I shut down the workstation, sir?"

        if re.search(r"\b(restart|reboot|mulai ulang)\b", cleaned, re.I):
            import subprocess
            self.pending_confirmation = ("Restarting, sir.", lambda: subprocess.run(["systemctl", "reboot"]))
            return "Shall I restart the workstation, sir?"

        # 3. Time query
        if re.search(r"\b(what time|the time|jam berapa)\b", cleaned, re.I):
            now = time.localtime()
            hour = now.tm_hour % 12 or 12
            ampm = "AM" if now.tm_hour < 12 else "PM"
            time_str = f"{hour} {now.tm_min:02d} {ampm}" if now.tm_min else f"{hour} {ampm}"
            return f"It is {time_str}, sir."

        # 4. Dispatch through registered plugins
        context: Dict[str, Any] = {"raw_input": transcription, "cleaned_input": cleaned}
        plugin_response = self.registry.dispatch(cleaned, context)
        if plugin_response is not None:
            self._record_history(t, plugin_response)
            return plugin_response

        # 5. Fallback to Language Model Reasoning
        if self.llm is not None:
            llm_response = self._fallback_llm(cleaned)
            self._record_history(t, llm_response)
            return llm_response

        return "I am afraid that is not within my reach yet, sir."

    def _fallback_llm(self, query: str) -> str:
        """Submit query to language model and parse structured action or verbal response."""
        convo = "".join(f"User: {u}\nVICTOR: {a}\n" for u, a in self.conversation_history[-6:])
        prompt = (
            f"Conversation History:\n{convo}User: {query}\n\n"
            "Reply as VICTOR: either one ACTION: <command> line, or at most two short spoken sentences in English only.\nVICTOR:"
        )

        out = self.llm.query(prompt, self.system_prompt)
        m = re.search(r"ACTION:\s*`?([^`\n]+)", out)
        if m:
            action_intent = m.group(1).strip()
            # Re-dispatch action through plugins
            res = self.registry.dispatch(action_intent, {})
            return res if res is not None else "I am afraid that is not within my reach yet, sir."

        if out and is_indonesian(out):
            trans_prompt = f"Translate into natural spoken English, keeping the executive butler tone and 'sir':\n{out}"
            translated = self.llm.query(trans_prompt, self.system_prompt)
            return translated or out

        return out or "I am afraid my connection failed, sir."

    def _record_history(self, user_text: str, reply: str) -> None:
        """Store conversational context for multi-turn continuity."""
        self.conversation_history.append((user_text, reply))
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
