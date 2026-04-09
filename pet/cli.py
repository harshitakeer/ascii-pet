"""
Pet CLI — lightweight client that talks to the running daemon.
Usage: python -m pet.cli <command>
"""

import asyncio
import os
import subprocess
import sys
import time

from .ipc import send_command

PID_FILE = "/tmp/pet_daemon.pid"

USAGE = """\
Usage: pet <command> [options]

Commands:
  start [--type <type>]  Start the pet daemon (cat, dog, bunny)
  stop                   Stop the pet daemon and save state
  status                 Show pet's current stats
  feed                   Feed your pet
  play                   Play with your pet
  sleep                  Put your pet to sleep
  types                  List available pet types
"""


# ── Commands ─────────────────────────────────────────────────────────

def cmd_start(pet_type: str | None = None) -> None:
    from .renderer import PET_TYPES
    if pet_type and pet_type not in PET_TYPES:
        print(f"Unknown type {pet_type!r}. Available: {', '.join(PET_TYPES)}")
        sys.exit(1)

    if _daemon_alive():
        pid = _read_pid()
        print(f"Pet is already running (PID {pid}). Stop it first to change type.")
        return

    daemon_mod = "pet.daemon"
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extra = ["--type", pet_type] if pet_type else []

    if os.environ.get("TMUX"):
        type_flag = f" --type {pet_type}" if pet_type else ""
        subprocess.Popen(
            ["tmux", "split-window", "-v", "-l", "8",
             f"cd {pkg_dir} && {sys.executable} -m {daemon_mod}{type_flag}"],
        )
        time.sleep(0.4)
        label = pet_type or "cat"
        print(f"Pet ({label}) started in a new tmux pane below!")
    else:
        proc = subprocess.Popen(
            [sys.executable, "-m", daemon_mod] + extra,
            cwd=pkg_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)
        label = pet_type or "cat"
        print(f"Pet ({label}) started (PID {proc.pid}).")
        print("Tip: run inside a tmux session to see the pet in a split pane.")


def cmd_stop() -> None:
    _send_and_print("stop", on_ok=lambda r: print("Goodbye! Pet state saved."))


def cmd_status() -> None:
    result = asyncio.run(send_command({"action": "status"}))
    if "error" in result:
        print(result["error"])
        return

    name = result["name"]
    fullness = 100.0 - result["hunger"]

    print(f"\n  {name}'s status  [{result.get('pet_type', 'cat')}]\n")
    _print_stat("Food   ", fullness)
    _print_stat("Happy  ", result["happiness"])
    _print_stat("Energy ", result["energy"])
    print(f"\n  Mood: {result['behavior']}\n")


def cmd_types() -> None:
    from .renderer import PET_TYPES, ALL_FRAMES
    print("\n  Available pet types:\n")
    previews = {"cat": "(=^.^=)", "dog": "{^.^}", "bunny": "(\\.^.^./)"}
    for t in PET_TYPES:
        print(f"    {t:<8}  {previews.get(t, '')}")
    print(f"\n  Usage: pet start --type <type>\n")


def cmd_feed() -> None:
    _send_and_print("feed")


def cmd_play() -> None:
    _send_and_print("play")


def cmd_sleep() -> None:
    _send_and_print("sleep")


# ── Helpers ──────────────────────────────────────────────────────────

def _send_and_print(action: str, on_ok=None) -> None:
    result = asyncio.run(send_command({"action": action}))
    if "error" in result:
        print(result["error"])
    elif not result.get("ok"):
        print(result.get("message", "Action failed."))
    else:
        if on_ok:
            on_ok(result)
        elif "message" in result:
            print(result["message"])


def _print_stat(label: str, value: float, width: int = 20) -> None:
    filled = round(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    if value > 60:
        colour = "\033[32m"  # green
    elif value > 30:
        colour = "\033[33m"  # yellow
    else:
        colour = "\033[31m"  # red
    reset = "\033[0m"
    print(f"  {label} {colour}{bar}{reset}  {value:.0f}%")


def _read_pid() -> int | None:
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _daemon_alive() -> bool:
    pid = _read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


# ── Entry point ───────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        return

    cmd = sys.argv[1]

    if cmd == "start":
        pet_type = None
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                pet_type = sys.argv[idx + 1]
        cmd_start(pet_type=pet_type)
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "feed":
        cmd_feed()
    elif cmd == "play":
        cmd_play()
    elif cmd == "sleep":
        cmd_sleep()
    elif cmd == "types":
        cmd_types()
    else:
        print(f"Unknown command: {cmd!r}\n")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
