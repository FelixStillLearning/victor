"""Wake-word engines package."""

from victor.engines.wakeword.base import WakeWordEngine
from victor.engines.wakeword.openwakeword import OpenWakeWordEngine

__all__ = ["WakeWordEngine", "OpenWakeWordEngine"]
