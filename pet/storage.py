import json
from pathlib import Path

from .state import PetState

STATE_FILE = Path.home() / ".pet_state.json"


def save(state: PetState) -> None:
    STATE_FILE.write_text(json.dumps(state.to_dict(), indent=2))


def load() -> PetState:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            return PetState.from_dict(data)
        except Exception:
            pass
    return PetState()
