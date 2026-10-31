"""Stato della partita e opzioni."""

from dataclasses import dataclass, field

from . import config


@dataclass
class Options:
    timer_minutes: int = 0
    sound: bool = True
    tts: bool = False
    uppercase: bool = False

    def to_dict(self):
        return {
            "timer_minutes": self.timer_minutes,
            "sound": self.sound,
            "tts": self.tts,
            "uppercase": self.uppercase,
        }

    @classmethod
    def from_dict(cls, data):
        opts = cls()
        if not isinstance(data, dict):
            return opts
        tm = data.get("timer_minutes")
        if isinstance(tm, int) and not isinstance(tm, bool) and tm in config.TIMER_CHOICES:
            opts.timer_minutes = tm
        for key in ("sound", "tts", "uppercase"):
            val = data.get(key)
            if isinstance(val, bool):
                setattr(opts, key, val)
        return opts


@dataclass
class GameState:
    team_name: str = ""
    stage: int = 1               # tappa in corso
    last_completed: int = 0      # ultima tappa superata
    inventory: list = field(default_factory=list)
    errors: dict = field(default_factory=dict)
    elapsed: float = 0.0         # secondi di gioco
    timer_expired_ack: bool = False

    def items_before(self, stage):
        return [config.STAGE_ITEM[s] for s in range(1, stage) if config.STAGE_ITEM.get(s)]

    def prepare_stage(self, stage):
        """Imposta lo stato all'inizio di una tappa (inventario delle tappe precedenti)."""
        self.stage = stage
        self.last_completed = max(0, stage - 1)
        self.inventory = self.items_before(stage)

    def add_item(self, item):
        if item and item not in self.inventory:
            self.inventory.append(item)
            self.inventory.sort(key=config.ITEMS.index)

    def add_error(self, stage):
        self.errors[stage] = self.errors.get(stage, 0) + 1

    def to_dict(self):
        return {
            "version": 1,
            "team_name": self.team_name,
            "last_completed": self.last_completed,
            "inventory": list(self.inventory),
            "elapsed": round(self.elapsed, 1),
            "timer_expired_ack": self.timer_expired_ack,
            "errors": {str(k): v for k, v in self.errors.items()},
        }

    @classmethod
    def from_dict(cls, data):
        """Ricostruisce lo stato da un dizionario. Solleva ValueError se non è valido."""
        if not isinstance(data, dict):
            raise ValueError("salvataggio non valido")
        last = data.get("last_completed")
        if not isinstance(last, int) or isinstance(last, bool) or not 1 <= last < config.STAGE_COUNT:
            raise ValueError("tappa non valida")
        name = data.get("team_name", "")
        if not isinstance(name, str):
            name = ""
        elapsed = data.get("elapsed", 0.0)
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
            elapsed = 0.0
        st = cls()
        st.team_name = clean_team_name(name)
        st.prepare_stage(last + 1)
        st.elapsed = float(min(elapsed, 24 * 3600))
        st.timer_expired_ack = bool(data.get("timer_expired_ack", False))
        errs = data.get("errors", {})
        if isinstance(errs, dict):
            for k, v in errs.items():
                try:
                    st.errors[int(k)] = int(v)
                except (TypeError, ValueError):
                    pass
        return st


MAX_TEAM_NAME = 18


def clean_team_name(name):
    allowed = []
    for ch in str(name):
        if ch.isprintable() and (ch.isalnum() or ch in " '-.!"):
            allowed.append(ch)
    return "".join(allowed).strip()[:MAX_TEAM_NAME]
