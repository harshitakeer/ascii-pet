import sys
from io import StringIO

from rich.console import Console
from rich.text import Text

from .state import PetState

# ASCII art frames per pet type, per behavior.
# Cat   — pointy ears:  (=^.^=)
# Dog   — side ears:    {^.^}
# Bunny — tall ears:    ('^.^')
ALL_FRAMES: dict[str, dict[str, list[str]]] = {
    "cat": {
        "idle":          ["(=^.^=)", "(=^-^=)"],
        "walking_right": ["(=^.^=)~", "(=^o^=)>"],
        "walking_left":  ["~(=^.^=)", "<(=^o^=)"],
        "sleeping":      ["(= -.- =)  z", "(= -.- =)   z", "(= -.- =)    Z", "(= -.- =)   z"],
        "sad":           ["(=;.;=)", "(=T.T=)"],
        "hungry":        ["(=o.o=)", "(=O.O=)"],
        "playful":       ["(=^w^=)/", "(=^v^=)~", "(=^w^=)*"],
    },
    "dog": {
        "idle":          ["{^.^}", "{^-^}"],
        "walking_right": ["{^.^}~", "{^o^}>"],
        "walking_left":  ["~{^.^}", "<{^o^}"],
        "sleeping":      ["{- .- }  z", "{- .- }   z", "{- .- }    Z", "{- .- }   z"],
        "sad":           ["{;.;}", "{T.T}"],
        "hungry":        ["{o.o}", "{O.O}"],
        "playful":       ["{^w^}/", "{^v^}~", "{^w^}*"],
    },
    "bunny": {
        "idle":          ["(\\.^.^./)", "(\\.^-^./)"],
        "walking_right": ["(\\.^.^./)~", "(\\.^o^./)>"],
        "walking_left":  ["~(\\.^.^./)", "<(\\.^o^./)"],
        "sleeping":      ["(\\.- .- ./)  z", "(\\.- .- ./)   z", "(\\.- .- ./)    Z", "(\\.- .- ./)   z"],
        "sad":           ["(\\. ;.; ./)", "(\\. T.T ./)"],
        "hungry":        ["(\\.o.o./)", "(\\.O.O./)"],
        "playful":       ["(\\.^w^./)/", "(\\.^v^./)~", "(\\.^w^./)*"],
    },
}

PET_TYPES = list(ALL_FRAMES.keys())

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
    "sleeping": "sleeping zzZ",
    "sad": "feeling sad",
    "hungry": "SO HUNGRY",
    "playful": "being playful!",
}

# Number of lines we write each frame — must stay constant to erase correctly.
RENDER_LINES = 5


def _bar(value: float, width: int = 10) -> tuple[str, str]:
    filled = round(value / 100 * width)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
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
        self._started = False

    def render(self, state: PetState, terminal_width: int) -> None:
        self._tick += 1
        if self._tick % 3 == 0:
            self._frame_idx += 1

        pet_frames = ALL_FRAMES.get(state.pet_type, ALL_FRAMES["cat"])
        frames = pet_frames.get(state.behavior, pet_frames["idle"])
        frame = frames[self._frame_idx % len(frames)]
        pet_style = BEHAVIOR_STYLE.get(state.behavior, "white")
        mood = MOOD_LABEL.get(state.behavior, state.behavior)

        # ── Status bar (kept short to avoid wrapping) ────────────────
        fullness = 100.0 - state.hunger
        food_bar, food_style   = _bar(fullness)
        happy_bar, happy_style = _bar(state.happiness)
        nrg_bar, nrg_style     = _bar(state.energy)

        status = Text(overflow="crop", no_wrap=True)
        status.append(f" {state.name}", style="bold cyan")
        status.append(f" {mood}", style="dim italic")
        status.append("  food ", style="dim")
        status.append(food_bar, style=food_style)
        status.append("  happy ", style="dim")
        status.append(happy_bar, style=happy_style)
        status.append("  energy ", style="dim")
        status.append(nrg_bar, style=nrg_style)

        # ── Pet ───────────────────────────────────────────────────────
        x = max(0, int(state.position))
        pet_text = Text(overflow="crop", no_wrap=True)
        pet_text.append(" " * x)
        pet_text.append(frame, style=f"bold {pet_style}")

        # ── Ground ───────────────────────────────────────────────────
        ground = Text("\u2500" * terminal_width, style="dim", overflow="crop", no_wrap=True)

        lines = [status, Text(""), pet_text, ground, Text("")]

        # Render to buffer so we can write atomically with cursor control
        buf = StringIO()
        c = Console(file=buf, width=terminal_width, highlight=False,
                    force_terminal=True, no_color=False)
        for line in lines:
            c.print(line, end="\n", no_wrap=True, overflow="crop")

        output = buf.getvalue()

        # Move cursor up to overwrite previous frame, then write
        if self._started:
            sys.stdout.write(f"\033[{RENDER_LINES}A\033[1G")
        sys.stdout.write(output)
        sys.stdout.flush()
        self._started = True
