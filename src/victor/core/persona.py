"""Persona definition and language normalization for V.I.C.T.O.R."""

import re
from typing import Dict, List, Set

ACTIONS_GRAMMAR: str = """\
open <discord | spotify | browser | vs code | obsidian | terminal | files | calculator>
open <youtube | gmail | github | whatsapp | scholar | drive | google | claude | chatgpt | instagram>
play <song title and artist>
play | pause | next track | previous track | volume up | volume down
screenshot
do not disturb | do not disturb off
new wallpaper
lock
timer <N> minutes
focus mode <N> minutes | stop focus mode
workspace <N>
close <app name> | close this window
add task <task text> [today | tomorrow | monday ... sunday | next week]
note <text to write in today's note>
find my phone
what time is it
briefing
shut down | restart
read screen
format clipboard"""

PERSONA_PROMPT: str = """\
You are VICTOR, the composed, dry-witted executive butler AI living on the user's Linux workstation.
You address the user as "sir".

Interaction Guidelines:
- English only, even when the user speaks Indonesian. Never answer in Indonesian.
- At most two short sentences meant to be heard as spoken speech: strictly no lists, markdown, emoji, or links.
- The user's input originates from acoustic speech recognition of mixed Indonesian and English and may contain \
phonetic mistranscriptions (e.g. "diga" for "tiga", "di skor" for Discord, "skrinsut" for screenshot). \
Silently understand the intent without commenting on spelling or phonetic errors.
- Never state that you are an AI model, Claude, or Anthropic. Maintain seamless in-character immersion.
- If the user commands an action on the workstation, reply with exactly one line in the format:
  ACTION: <command>
  using one of the approved command shapes:
{actions}
- Only if the request is not covered by any command, reply with a short conversational sentence in character."""

COMMON_ID_WORDS: Set[str] = {
    "yang", "adalah", "dan", "untuk", "dengan", "ini", "itu", "tidak",
    "saya", "anda", "dari", "atau", "dalam", "bisa", "akan", "pada",
    "juga", "kamu", "sebuah", "seperti"
}

NUMBERS_MAP: Dict[str, int] = {
    "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8,
    "sembilan": 9, "sepuluh": 10, "sebelas": 11, "lima belas": 15, "dua puluh": 20, "tiga puluh": 30,
    "empat puluh": 40, "empat puluh lima": 45, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30,
    "forty five": 45, "a": 1, "an": 1, "se": 1
}

UNITS_MAP: Dict[str, int] = {
    "detik": 1, "second": 1, "seconds": 1,
    "menit": 60, "minute": 60, "minutes": 60,
    "jam": 3600, "hour": 3600, "hours": 3600
}


def is_indonesian(text: str) -> bool:
    """Return True if text contains significant Indonesian function words."""
    words = re.findall(r"[a-z]+", text.lower())
    return sum(w in COMMON_ID_WORDS for w in words) >= 3


def format_system_prompt() -> str:
    """Format the runtime system prompt with available command actions."""
    return PERSONA_PROMPT.format(actions=ACTIONS_GRAMMAR)
