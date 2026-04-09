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
Usage: pet <command>

Commands:
  start   Start the pet daemon (uses tmux split if inside tmux)
  stop    Stop the pet daemon and save state
  status  Show pet's current stats
  feed    Feed your pet
  play    Play with your pet
  sleep   Put your pet to sleep
"""


# ── Commands ─────────────────────────────────────────────────────────

def cmd_start() -> None:
    if _daemon_alive():
        pid = _read_pid()
        print(f"Pet is already running (PID {pid}).")
        return

    daemon_mod = "pet.daemon"
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if os.environ.get("TMUX"):
        # Split a new pane inside the current tmux window
        subprocess.Popen(
            ["tmux", "split-window", "-v", "-l", "8",
             f"cd {pkg_dir} && {sys.executable} -m {daemon_mod}"],
        )
        time.sleep(0.4)
        print("Pet started in a new tmux pane below!")
    else:
        proc = subprocess.Popen(
            [sys.executable, "-m", daemon_mod],
            cwd=pkg_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)
        print(f"Pet started (PID {proc.pid}).")
        print("Tip: run 'pet start' inside a tmux session to see the pet in a split pane.")


def cmd_stop() -> None:
    _send_and_print("stop", on_ok=lambda r: print("Goodbye! Pet state saved."))


def cmd_status() -> None:
    result = asyncio.run(send_command({"action": "status"}))
    if "error" in result:
        print(result["error"])
        return

    name = result["name"]
    fullness = 100.0 - result["hunger"]

    print(f"\n  {name}'s status\n")
    _print_stat("Food   ", fullness)
    _print_stat("Happy  ", result["happiness"])
    _print_stat("Energy ", result["energy"])
    print(f"\n  Mood: {result['behavior']}\n")


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

_COMMANDS = {
    "start": cmd_start,
    "stop": cmd_stop,
    "status": cmd_status,
    "feed": cmd_feed,
    "play": cmd_play,
    "sleep": cmd_sleep,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        return

    cmd = sys.argv[1]
    fn = _COMMANDS.get(cmd)
    if fn is None:
        print(f"Unknown command: {cmd!r}\n")
        print(USAGE)
        sys.exit(1)

    fn()


if __name__ == "__main__":
    main()
