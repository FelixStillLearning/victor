# V.I.C.T.O.R.

**Voice Intelligence for Contextual Tasks & OS Reasoning**

V.I.C.T.O.R. is an extensible, privacy-focused voice assistant engineered natively for Linux and modern Wayland compositors. It combines local neural speech synthesis, offline acoustic transcription, active workspace context awareness via AT-SPI, and pluggable language reasoning engines.

---

## Architectural Principles

* **Native Compositor Integration**: Built from the ground up for Wayland environments (Hyprland), featuring inter-process communication with overlay panels (Dynamic Island via Quickshell).
* **Deterministic Tool Routing**: Prioritizes instant, zero-latency local regex and intent matching before delegating complex requests to language models.
* **Semantic Screen Context**: Queries the Linux AT-SPI accessibility bus directly to extract structured application context, preserving context windows without requiring token-heavy screenshot loops.
* **Proactive Watchdogs**: Continuously monitors power topology, thermal metrics, external displays, audio sinks, and Bluetooth devices.
* **Pluggable Architecture**: Modular plugin interface allowing extensions to register custom voice triggers, background hooks, and IPC handlers independently.

---

## System Requirements

* **Operating System**: Linux (Arch Linux, Fedora, Ubuntu 24.04+)
* **Compositor**: Wayland (Hyprland recommended) or X11
* **Audio Server**: PipeWire with `wireplumber` and `pactl` compatibility
* **Python Runtime**: Python 3.11 or newer
* **Optional System Dependencies**:
  * `piper-tts` or precompiled Piper ONNX runtime
  * `faster-whisper` with CTranslate2 runtime
  * `openwakeword` for local acoustic wake detection
  * `at-spi2-core` for accessibility context extraction
  * `kdeconnect` for mobile phone integration

---

## Quick Start

### Installation via Installer Script

```bash
git clone https://github.com/felixdev/victor.git
cd victor
./install.sh
```

### Manual Development Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,vision]"

# Initialize user configuration
mkdir -p ~/.config/victor
cp config/config.example.toml ~/.config/victor/config.toml
```

---

## Command Line Interface

```bash
# Speech and interaction
victor say "All systems are operational, sir."
victor greet                      # Execute morning login greeting and briefings
victor brief                      # Report current time, weather, battery, and media
victor listen                     # Start continuous wake-word and voice recognition daemon
victor ask                        # Trigger single-shot listening without wake word
victor toggle                     # Toggle wake-word listening on or off

# Background monitoring
victor watch                      # Launch hardware, power, and notification monitor daemon
victor done 0 1234 "make build"   # Terminal completion notification handler

# Plugin management
victor plugin list                # Display status of all bundled and installed plugins
victor plugin enable <name>       # Enable a specific plugin
victor plugin disable <name>      # Disable a specific plugin
```

---

## Core Plugin Architecture

V.I.C.T.O.R. isolates functional capabilities into modular plugins located in `src/victor/plugins/`:

| Plugin | Responsibility | Triggers / Function |
| :--- | :--- | :--- |
| `hyprland` | Window management, workspace switching, dynamic island IPC | "workspace 3", "close window" |
| `media` | MPRIS media controller and Spotify catalog lookups | "play Bohemian Rhapsody", "pause" |
| `tasks` | Task orchestration with Todoist API synchronization | "add task finish dissertation tomorrow" |
| `notes` | Rapid daily note appending for Obsidian vaults | "note investigate attention mechanisms" |
| `phone` | KDE Connect device tracking and remote telephony alert | "find my phone", incoming call hooks |
| `vision` | Semantic accessibility tree extraction and bounded screenshots | "read this screen", "summarize open document" |
| `clipboard` | Wayland clipboard text transformations | "format clipboard as markdown" |
| `history` | Command audit logging and contextual query retrieval | "what did I ask earlier?" |

Refer to [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) and [docs/architecture/plugin-specification.md](docs/architecture/plugin-specification.md) for detailed architectural blueprints.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.
