import random

from .state import PetState

TICK_RATE = 0.12  # seconds per tick (~8 FPS)

# Stat drift rates per second
HUNGER_RATE = 0.4     # hunger climbs
HAPPY_RATE = 0.25     # happiness falls
ENERGY_RATE = 0.15    # energy drains (when awake)
SLEEP_RECOVERY = 2.5  # energy recovered per second while sleeping


def update_stats(state: PetState, dt: float) -> None:
    state.hunger = min(100.0, state.hunger + HUNGER_RATE * dt)
    state.happiness = max(0.0, state.happiness - HAPPY_RATE * dt)

    if state.behavior == "sleeping":
        state.energy = min(100.0, state.energy + SLEEP_RECOVERY * dt)
    else:
        state.energy = max(0.0, state.energy - ENERGY_RATE * dt)


def choose_behavior(state: PetState) -> str:
    # Forced overrides (highest priority first)
    if state.energy < 15:
        return "sleeping"
    if state.hunger > 88:
        return "hungry"
    if state.happiness < 18:
        return "sad"
    if state.happiness > 85:
        return "playful"

    # Soft random walk
    if state.behavior in ("walking_left", "walking_right"):
        # 10% chance to pause, otherwise keep going
        return "idle" if random.random() < 0.10 else state.behavior
    else:
        # idle or other — pick a new movement
        r = random.random()
        if r < 0.35:
            return "walking_right"
        elif r < 0.70:
            return "walking_left"
        return "idle"


def update_position(state: PetState, terminal_width: int, dt: float) -> None:
    speed = 7.0  # columns per second
    margin = 12  # keep pet away from the right edge

    if state.behavior == "walking_right":
        state.position = min(terminal_width - margin, state.position + speed * dt)
        if state.position >= terminal_width - margin:
            state.behavior = "walking_left"
    elif state.behavior == "walking_left":
        state.position = max(0.0, state.position - speed * dt)
        if state.position <= 0.0:
            state.behavior = "walking_right"
