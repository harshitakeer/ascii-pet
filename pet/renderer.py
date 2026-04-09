from rich.console import Group
from rich.text import Text

from .state import PetState

# ASCII art frames per behavior
FRAMES: dict[str, list[str]] = {
    "idle": [
        "(=^.^=)",
        "(=^-^=)",
    ],
    "walking_right": [
        "(=^.^=)~",
        "(=^o^=)>",
    ],
    "walking_left": [
        "~(=^.^=)",
        "<(=^o^=)",
    ],
    "sleeping": [
        "(= -.- =)  z",
        "(= -.- =)   z",
        "(= -.- =)    Z",
        "(= -.- =)   z",
    ],
    "sad": [
        "(=;.;=)",
        "(=T.T=)",
    ],
    "hungry": [
        "(=°.°=)",
        "(=°o°=)",
    ],
    "playful": [
        "(=^w^=)/",
        "(=^v^=)~",
        "(=^w^=)*",
    ],
}

BEHAVIOR_STYLE: dict[str, str] = {
    "idle": "white",
    "walking_right": "bright_white",
    "walking_left": "bright_white",
    "sleeping": "blue",
    "sad": "magenta",
    "hungry": "red",
    "playful": "bright_yellow",
}

MOOD_LABEL: dict[str, str] = {
    "idle": "relaxing",
    "walking_right": "exploring",
    "walking_left": "exploring",
    "sleeping": "sleeping  zzZ",
    "sad": "feeling sad",
    "hungry": "SO HUNGRY",
    "playful": "being playful!",
}


def _stat_bar(value: float, width: int = 12) -> tuple[str, str]:
    """Return (bar_string, style) for a 0-100 value."""
    filled = round(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    if value > 60:
        style = "green"
    elif value > 30:
        style = "yellow"
    else:
        style = "red"
    return bar, style


class Renderer:
    def __init__(self) -> None:
        self._frame_idx = 0
        self._tick = 0
        self._ticks_per_frame = 3  # change frame every N ticks

    def get_renderable(self, state: PetState, terminal_width: int) -> Group:
        self._tick += 1
        if self._tick % self._ticks_per_frame == 0:
            self._frame_idx += 1

        frames = FRAMES.get(state.behavior, FRAMES["idle"])
        frame = frames[self._frame_idx % len(frames)]
        pet_style = BEHAVIOR_STYLE.get(state.behavior, "white")
        mood = MOOD_LABEL.get(state.behavior, state.behavior)

        # ── Status bar ──────────────────────────────────────────────
        status = Text()
        status.append(f" {state.name}", style="bold cyan")
        status.append(f"  [{mood}]", style="dim italic")

        fullness = 100.0 - state.hunger
        for label, val in (("food", fullness), ("happy", state.happiness), ("energy", state.energy)):
            bar, bar_style = _stat_bar(val)
            status.append(f"  {label} ", style="dim")
            status.append(bar, style=bar_style)

        # ── Pet line ─────────────────────────────────────────────────
        x = max(0, int(state.position))
        pet_text = Text()
        pet_text.append(" " * x)
        pet_text.append(frame, style=f"bold {pet_style}")

        # ── Ground ───────────────────────────────────────────────────
        ground = Text("─" * terminal_width, style="dim")

        return Group(status, Text(""), pet_text, ground, Text(""))
