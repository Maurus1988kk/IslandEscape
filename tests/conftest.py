import os
import sys

import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Ogni test usa una cartella dati temporanea (mai %APPDATA%)."""
    from game import save
    monkeypatch.setenv("FUGAISOLA_DATA_DIR", str(tmp_path))
    save.reset_data_dir_cache()
    yield tmp_path
    save.reset_data_dir_cache()


@pytest.fixture
def app():
    from game.app import App
    a = App(fullscreen=False)
    yield a
    a.shutdown()
