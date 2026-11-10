# Security and Permission Architecture

## Security Objectives
Because V.I.C.T.O.R. executes shell binaries, manipulates active windows, and queries system buses, strict boundary controls are established to protect user data and system stability.

---

## 1. Threat Mitigation Strategies

### Prompt Injection and Voice Spoofing
* **Strict Command Whitelisting**: System actuation commands (power off, reboot, lock screen, workspace shifts) are matched strictly against deterministic regex patterns. The language model cannot execute arbitrary shell syntax directly.
* **Structured Action Dispatch**: When an intent requires LLM reasoning, the model is instructed to output strictly `ACTION: <command>` matching a bounded grammatical schema, rather than executable shell pipelines.

### Destructive Action Confirmation
* Operations modifying system power state (`systemctl poweroff`, `systemctl reboot`) require explicit secondary confirmation.
* Example:
  * User: "Victor, shut down the laptop."
  * Victor: "Shall I shut down the workstation, sir?"
  * Victor sets a 10-second pending state requiring an explicit affirmative utterance before triggering `systemctl`.

### Credential and Token Isolation
* User tokens for third-party APIs (Todoist API keys, Spotify Client Secrets, Webhook URLs) are stored strictly in `~/.config/victor/config.toml` with `0600` POSIX file permissions.
* Configuration templates committed to git repositories (`config.example.toml`) contain empty placeholders.
* Sensitive values are masked from standard audit logs.

### Subprocess Execution Boundaries
* Subprocesses spawned by plugins are executed using `subprocess.Popen` or `subprocess.run` with discrete argument lists rather than `shell=True`.
* Timeouts are enforced across all external network calls and system commands (defaulting to 5-15 seconds) to prevent daemon deadlocks.
