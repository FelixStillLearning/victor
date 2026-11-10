# V.I.C.T.O.R. System Architecture Document

## Overview
V.I.C.T.O.R. (Voice Intelligence for Contextual Tasks & OS Reasoning) is designed as a layered, asynchronous daemon system. It maintains low idle resource utilization on Linux workstations while delivering sub-second voice command parsing and active desktop awareness.

---

## 1. C4 Architecture Specification

### 1.1 Level 1: System Context Diagram

```mermaid
graph TD
    User([Workstation Operator]) -->|Microphone Audio Stream| Victor[V.I.C.T.O.R. Core System]
    Victor -->|Speaker Synthesized Audio| User
    Victor -->|Visual Overlays & HUD State| Quickshell[Quickshell Dynamic Island]
    
    Victor -->|Window & Workspace Commands| Hyprland[Hyprland Wayland Compositor]
    Victor -->|Semantic Desktop Inspection| ATSPI[Linux Accessibility Bus / AT-SPI]
    Victor -->|Peripheral & Battery Queries| KernelSystemd[Linux Kernel /sys & systemd D-Bus]
    Victor -->|Telephony Tracking| KDEConnect[KDE Connect Daemon]
    Victor -->|Task & Media Lookups| CloudAPIs[External Services: Spotify, Todoist]
    Victor -->|Reasoning Fallback| LocalCloudLLM[Inference Engines: Ollama / Claude]
```

### 1.2 Level 2: Container Diagram

```mermaid
graph TD
    subgraph Audio Subsystem [Audio & Acoustic Processing]
        MicStream[/PulseAudio / PipeWire Capture/] --> VAD[Voice Activity Detector]
        VAD --> WakeWord[openWakeWord Engine]
        WakeWord --> STT[Faster-Whisper Transcriber]
        TTS[Piper Neural TTS Engine] --> DSP[FFmpeg Audio Filter Graph]
        DSP --> SpeakerOut[/PipeWire Playback Sink/]
    end

    subgraph Runtime Core [Victor Python Core Daemon]
        STT --> IntentRouter[Core Intent Router]
        IntentRouter -->|Deterministic Action Match| PluginRegistry[Plugin Execution Registry]
        IntentRouter -->|Undetermined Semantic Intent| LLMAdapter[Pluggable LLM Adapter]
        LLMAdapter -->|Structured Command Action| PluginRegistry
        
        SystemWatcher[Proactive Hardware Watcher] -->|Status Broadcasts| TTS
    end

    subgraph Plugin Containers [Modular Extensions]
        PluginRegistry --> P_Hypr[Hyprland Window Dispatcher]
        PluginRegistry --> P_Media[MPRIS & Spotify Controller]
        PluginRegistry --> P_Vision[AT-SPI & Vision Capture]
        PluginRegistry --> P_Tasks[Todoist Task Synchronizer]
        PluginRegistry --> P_Notes[Obsidian Note Sink]
        PluginRegistry --> P_History[Command Audit Storage]
    end
```

### 1.3 Level 3: Component Diagram (Core Layer)

```mermaid
classDiagram
    class ConfigManager {
        +dict config_data
        +load(path: Path)
        +get(key: str, default: Any)
    }

    class IntentRouter {
        +list registered_handlers
        +route(transcription: str) CommandResult
        +fallback_to_llm(transcription: str) str
    }

    class VictorPlugin {
        <<abstract>>
        +str name
        +list keywords
        +setup(config: dict) bool
        +handle(intent: str, context: dict) Optional[str]
        +teardown() void
    }

    class PluginRegistry {
        +dict loaded_plugins
        +discover_and_load(directory: Path)
        +dispatch(intent: str, context: dict) Optional[str]
    }

    class SystemWatcher {
        +poll_hardware()
        +evaluate_battery()
        +evaluate_thermal()
        +evaluate_peripherals()
    }

    IntentRouter --> PluginRegistry
    PluginRegistry o-- VictorPlugin
    SystemWatcher --> ConfigManager
```

---

## 2. Interaction Sequence: Voice Command Execution

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant PipeWire as PipeWire / Mic
    participant VAD as Wake & VAD Engine
    participant STT as Whisper STT Engine
    participant Router as Intent Router
    participant Plugin as Hyprland Plugin
    participant Quickshell as Dynamic Island
    participant TTS as Piper TTS

    User->>PipeWire: "Victor, workspace 3"
    PipeWire->>VAD: Audio PCM Frames
    VAD->>VAD: Wake word detected ("Victor")
    VAD->>Quickshell: IPC "hear" state
    VAD->>STT: Audio segment buffer
    STT->>Router: Transcribed Text: "workspace 3"
    Router->>Plugin: handle("workspace 3")
    Plugin->>Plugin: Dispatch Hyprctl workspace command
    Plugin-->>Router: Result text: "Workspace 3, sir."
    Router->>TTS: Synthesize("Workspace 3, sir.")
    TTS->>Quickshell: IPC "speak" + Envelope
    TTS->>PipeWire: Stream PCM to Default Audio Sink
```

---

## 3. Extensibility and Plugin Isolation Rules
* Plugins inherit from `victor.plugins.base.VictorPlugin`.
* Plugins are sandboxed against crashing the main loop: any unhandled exception inside a plugin's `handle()` method is captured, logged, and isolated.
* Plugins declare dependencies and trigger keywords in a declarative `PLUGIN.toml`.
