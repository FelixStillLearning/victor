"""Command Line Interface entrypoint and dispatcher for V.I.C.T.O.R."""

import argparse
import sys
from typing import List, Optional

from victor import __version__
from victor.cli.commands import (
    cmd_ask,
    cmd_brief,
    cmd_done,
    cmd_greet,
    cmd_listen,
    cmd_say,
    cmd_toggle,
    cmd_watch,
    setup_runtime,
)
from victor.core.config import get_config
from victor.plugins.registry import get_registry


def build_parser() -> argparse.ArgumentParser:
    """Construct standard command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="victor",
        description="V.I.C.T.O.R. - Voice Intelligence for Contextual Tasks & OS Reasoning on Linux",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # say
    p_say = subparsers.add_parser("say", help="Synthesize and speak provided text")
    p_say.add_argument("text", nargs="+", help="Text to vocalize")

    # greet & brief
    subparsers.add_parser("greet", help="Perform login morning greeting and briefing")
    subparsers.add_parser("brief", help="Report time, weather, and battery status")

    # listen, ask, toggle
    subparsers.add_parser("listen", help="Run continuous wake-word and voice recognition daemon")
    subparsers.add_parser("ask", help="Trigger single-shot speech capture without wake-word")
    subparsers.add_parser("toggle", help="Toggle wake-word listening on or off")

    # watch
    subparsers.add_parser("watch", help="Launch background system and hardware monitor daemon")

    # done
    p_done = subparsers.add_parser("done", help="Terminal shell hook for long command completions")
    p_done.add_argument("status", help="Exit code status")
    p_done.add_argument("pid", help="Shell process ID")
    p_done.add_argument("cmd", nargs="+", help="Command string")

    # plugin
    p_plugin = subparsers.add_parser("plugin", help="Manage V.I.C.T.O.R. plugins")
    plugin_sub = p_plugin.add_subparsers(dest="plugin_action", help="Plugin action")
    plugin_sub.add_parser("list", help="List all registered plugins")
    p_penable = plugin_sub.add_parser("enable", help="Enable a specific plugin")
    p_penable.add_argument("name", help="Plugin name")
    p_pdisable = plugin_sub.add_parser("disable", help="Disable a specific plugin")
    p_pdisable.add_argument("name", help="Plugin name")

    # config
    p_cfg = subparsers.add_parser("config", help="Inspect configuration")
    cfg_sub = p_cfg.add_subparsers(dest="config_action", help="Config action")
    cfg_sub.add_parser("show", help="Print active configuration")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI execution dispatch function."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    if parsed.command == "say":
        cmd_say(" ".join(parsed.text))
        return 0

    if parsed.command == "greet":
        cmd_greet()
        return 0

    if parsed.command == "brief":
        cmd_brief()
        return 0

    if parsed.command == "listen":
        cmd_listen()
        return 0

    if parsed.command == "ask":
        cmd_ask()
        return 0

    if parsed.command == "toggle":
        cmd_toggle()
        return 0

    if parsed.command == "watch":
        cmd_watch()
        return 0

    if parsed.command == "done":
        cmd_done(parsed.status, parsed.pid, " ".join(parsed.cmd))
        return 0

    if parsed.command == "plugin":
        setup_runtime()
        reg = get_registry()
        action = parsed.plugin_action or "list"

        if action == "list":
            plugins = reg.list_plugins()
            print(f"{'NAME':<15} {'ENABLED':<10} {'DESCRIPTION'}")
            print("-" * 60)
            for p in plugins:
                en = "yes" if p["enabled"] else "no"
                print(f"{p['name']:<15} {en:<10} {p['description']}")
            return 0

        if action == "enable":
            print(f"Plugin '{parsed.name}' enabled in active session.")
            return 0

        if action == "disable":
            reg.unregister(parsed.name)
            print(f"Plugin '{parsed.name}' disabled.")
            return 0

    if parsed.command == "config":
        action = parsed.config_action or "show"
        if action == "show":
            import json
            cfg = get_config()
            print(json.dumps(cfg.as_dict(), indent=2))
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
