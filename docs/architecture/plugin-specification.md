# Plugin Architecture Specification

## Overview
V.I.C.T.O.R. employs a decoupled plugin system. All capabilities outside the core audio loop and system watcher are implemented as self-contained plugins.

---

## 1. Plugin Interface Contract

Every plugin must inherit from `VictorPlugin` defined in `victor.plugins.base`:

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class VictorPlugin(ABC):
    name: str = ""
    description: str = ""
    keywords: List[str] = []

    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin state, verify prerequisites, and validate configuration."""
        pass

    @abstractmethod
    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate user intent.
        Returns spoken response string if handled, or None if intent does not match.
        """
        pass

    def teardown(self) -> None:
        """Release open file descriptors, network connections, or threads on shutdown."""
        pass
```

---

## 2. Declarative Metadata (`PLUGIN.toml`)

Each plugin directory must contain a `PLUGIN.toml` file:

```toml
[plugin]
name = "vision"
version = "0.1.0"
description = "Semantic active window inspection via AT-SPI"
author = "Felix Angga Resky"
entry_point = "plugin:VisionPlugin"

[dependencies]
system_packages = ["at-spi2-core", "grim"]
python_packages = ["pyatspi", "pillow"]

[triggers]
keywords = [
    "read screen",
    "baca layar",
    "what is on my screen",
    "summarize this document",
    "jelaskan error di layar",
]
```

---

## 3. Plugin Lifecycle Management

1. **Discovery**: At daemon launch, `PluginRegistry` scans `src/victor/plugins/` and optional user paths (`~/.config/victor/plugins/`).
2. **Configuration Binding**: The registry matches section `[plugins.<name>]` from `config.toml` and passes it to `setup()`.
3. **Execution Routing**: Incoming transcribed text passes sequentially through loaded plugins. The first plugin returning a non-null string terminates the routing chain.
4. **Error Boundary**: Exceptions raised inside `handle()` are logged to `~/.local/state/victor/plugins.log` without terminating the daemon.
