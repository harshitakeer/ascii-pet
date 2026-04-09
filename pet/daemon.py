"""
Pet daemon — run this in a dedicated terminal pane.
Usage: python -m pet.daemon
"""

import asyncio
import os
import random
import shutil
import signal
import sys
import time

from .behavior import TICK_RATE, choose_behavior, update_position, update_stats
from .ipc import IPCServer, SOCKET_PATH
from .renderer import Renderer
from .state import PetState
from .storage import load, save

PID_FILE = "/tmp/pet_daemon.pid"

# How often (seconds) to reconsider the pet's behavior
_MIN_BEHAVIOR_INTERVAL = 2.0
_MAX_BEHAVIOR_INTERVAL = 6.0


class PetDaemon:
    def __init__(self, pet_type: str | None = None) -> None:
        self.state: PetState = load()
        if pet_type is not None:
            self.state.pet_type = pet_type
        self.renderer = Renderer()
        self._last_tick = time.monotonic()
        self._last_save = time.monotonic()
        self._behavior_timer = 0.0
        self._behavior_interval = random.uniform(_MIN_BEHAVIOR_INTERVAL, _MAX_BEHAVIOR_INTERVAL)
        self._ipc = IPCServer(self._handle_command)

    # ── Main loop ────────────────────────────────────────────────────

    async def run(self) -> None:
        asyncio.create_task(self._ipc.start())

        while True:
            now = time.monotonic()
            dt = now - self._last_tick
            self._last_tick = now

            terminal_size = shutil.get_terminal_size((80, 24))
            w = terminal_size.columns

            update_stats(self.state, dt)
            self._maybe_change_behavior(dt)
            update_position(self.state, w, dt)

            self.renderer.render(self.state, w)

            # Periodic save
            if now - self._last_save > 30:
                save(self.state)
                self._last_save = now

            await asyncio.sleep(TICK_RATE)

    def _maybe_change_behavior(self, dt: float) -> None:
        self._behavior_timer += dt
        if self._behavior_timer >= self._behavior_interval:
            self._behavior_timer = 0.0
            self._behavior_interval = random.uniform(_MIN_BEHAVIOR_INTERVAL, _MAX_BEHAVIOR_INTERVAL)
            self.state.behavior = choose_behavior(self.state)

        # Forced overrides always win
        if self.state.energy < 15:
            self.state.behavior = "sleeping"
        elif self.state.hunger > 88:
            self.state.behavior = "hungry"
        elif self.state.happiness < 18:
            self.state.behavior = "sad"

    # ── IPC command handler ──────────────────────────────────────────

    async def _handle_command(self, msg: dict) -> dict:
        action = msg.get("action", "")

        if action == "feed":
            self.state.hunger = max(0.0, self.state.hunger - 40.0)
            self.state.happiness = min(100.0, self.state.happiness + 8.0)
            return {"ok": True, "message": f"{self.state.name} eats happily! Nom nom."}

        if action == "play":
            if self.state.energy < 20:
                return {"ok": False, "message": f"{self.state.name} is too tired to play..."}
            self.state.happiness = min(100.0, self.state.happiness + 30.0)
            self.state.energy = max(0.0, self.state.energy - 15.0)
            self.state.behavior = "playful"
            self._behavior_timer = 0.0
            self._behavior_interval = 5.0
            return {"ok": True, "message": f"{self.state.name} plays joyfully!"}

        if action == "sleep":
            self.state.behavior = "sleeping"
            self._behavior_timer = 0.0
            self._behavior_interval = 10.0
            return {"ok": True, "message": f"{self.state.name} curls up for a nap..."}

        if action == "status":
            return {
                "ok": True,
                "name": self.state.name,
                "pet_type": self.state.pet_type,
                "hunger": round(self.state.hunger, 1),
                "happiness": round(self.state.happiness, 1),
                "energy": round(self.state.energy, 1),
                "behavior": self.state.behavior,
            }

        if action == "stop":
            save(self.state)
            _cleanup()
            os.kill(os.getpid(), signal.SIGTERM)
            return {"ok": True}

        return {"error": f"Unknown action: {action!r}"}


# ── Helpers ──────────────────────────────────────────────────────────

def _cleanup() -> None:
    for path in (SOCKET_PATH, PID_FILE):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _write_pid() -> None:
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", dest="pet_type", default=None,
                        help="Pet type to use (cat, dog, bunny)")
    args = parser.parse_args()

    _write_pid()
    daemon = PetDaemon(pet_type=args.pet_type)
    try:
        asyncio.run(daemon.run())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        save(daemon.state)
        _cleanup()


if __name__ == "__main__":
    main()
