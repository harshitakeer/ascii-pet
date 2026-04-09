import time
from dataclasses import dataclass, field


@dataclass
class PetState:
    name: str = "Bit"
    pet_type: str = "cat"     # cat | dog | bunny
    hunger: float = 30.0      # 0 = full, 100 = starving
    happiness: float = 70.0   # 0 = sad,  100 = happy
    energy: float = 80.0      # 0 = exhausted, 100 = energized
    position: float = 0.0     # current x position in terminal columns
    behavior: str = "idle"    # current behavior
    last_saved: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "pet_type": self.pet_type,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "position": self.position,
            "behavior": self.behavior,
            "last_saved": self.last_saved,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PetState":
        return cls(
            name=d.get("name", "Bit"),
            pet_type=d.get("pet_type", "cat"),
            hunger=d.get("hunger", 30.0),
            happiness=d.get("happiness", 70.0),
            energy=d.get("energy", 80.0),
            position=d.get("position", 0.0),
            behavior=d.get("behavior", "idle"),
            last_saved=d.get("last_saved", time.time()),
        )
