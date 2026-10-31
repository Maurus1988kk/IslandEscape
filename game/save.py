"""Salvataggio automatico su JSON e cartella dei dati.

Cartella: %APPDATA%\\FugaIsola\\ (se non si può, la cartella utente ~/FugaIsola).
La variabile d'ambiente FUGAISOLA_DATA_DIR permette di sceglierne un'altra (usata nei test).
Un file rovinato non fa mai crashare il gioco: viene semplicemente ignorato.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

from . import config
from .state import GameState, Options

log = logging.getLogger("fuga")

SAVE_FILE = "salvataggio.json"
OPTIONS_FILE = "opzioni.json"
LOG_FILE = "log.txt"

_data_dir = None


def _candidate_dirs():
    env = os.environ.get("FUGAISOLA_DATA_DIR")
    if env:
        yield Path(env)
    appdata = os.environ.get("APPDATA")
    if appdata:
        yield Path(appdata) / config.APP_DIR_NAME
    yield Path.home() / config.APP_DIR_NAME
    yield Path(tempfile.gettempdir()) / config.APP_DIR_NAME


def data_dir():
    """Cartella scrivibile per salvataggi, opzioni e log."""
    global _data_dir
    if _data_dir is not None:
        return _data_dir
    for cand in _candidate_dirs():
        try:
            cand.mkdir(parents=True, exist_ok=True)
            probe = cand / ".scrivibile"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            _data_dir = cand
            return cand
        except OSError:
            continue
    _data_dir = Path(".")
    return _data_dir


def reset_data_dir_cache():
    global _data_dir
    _data_dir = None


def log_path():
    return data_dir() / LOG_FILE


def _write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        log.warning("File ignorato perché illeggibile (%s): %s", path.name, exc)
        return None


# ------------------------------------------------------------ partita
def save_game(state):
    try:
        _write_json(data_dir() / SAVE_FILE, state.to_dict())
        return True
    except (OSError, TypeError, ValueError) as exc:
        log.warning("Salvataggio non riuscito: %s", exc)
        return False


def load_game():
    """GameState pronto per riprendere, oppure None se non c'è o è rovinato."""
    data = _read_json(data_dir() / SAVE_FILE)
    if data is None:
        return None
    try:
        return GameState.from_dict(data)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        log.warning("Salvataggio ignorato: %s", exc)
        return None


def has_save():
    return load_game() is not None


def delete_game():
    try:
        (data_dir() / SAVE_FILE).unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        log.warning("Impossibile cancellare il salvataggio: %s", exc)


# ------------------------------------------------------------ opzioni
def save_options(options):
    try:
        _write_json(data_dir() / OPTIONS_FILE, options.to_dict())
        return True
    except (OSError, TypeError, ValueError) as exc:
        log.warning("Opzioni non salvate: %s", exc)
        return False


def load_options():
    return Options.from_dict(_read_json(data_dir() / OPTIONS_FILE))
