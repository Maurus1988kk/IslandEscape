"""Salvataggio: un file rovinato non deve mai far crashare il gioco."""

import json

import pytest

from game import save
from game.state import GameState, Options


def test_roundtrip(data_dir):
    st = GameState(team_name="Delfini")
    st.prepare_stage(3)
    st.last_completed = 3
    st.add_item("tronchi")
    st.elapsed = 123.4
    assert save.save_game(st)
    loaded = save.load_game()
    assert loaded is not None
    assert loaded.team_name == "Delfini"
    assert loaded.last_completed == 3
    assert loaded.stage == 4                      # si riprende dalla tappa successiva
    assert loaded.inventory == ["rosa", "corda", "tronchi"]
    assert loaded.elapsed == pytest.approx(123.4)
    assert save.has_save()
    save.delete_game()
    assert save.load_game() is None


@pytest.mark.parametrize("content", [
    b"\x00\xff\xfe garbage",
    b"{ non e' json",
    b"",
    b"[]",
    b"null",
    b'{"last_completed": "tre"}',
    b'{"last_completed": 99}',
    b'{"last_completed": 0}',
    b'{"last_completed": 6}',
    b'{"last_completed": true}',
    b'{"last_completed": 2, "team_name": 5, "elapsed": "x", "errors": [1,2]}',
])
def test_corrupt_save_is_ignored(data_dir, content):
    (data_dir / save.SAVE_FILE).write_bytes(content)
    st = save.load_game()
    if content.startswith(b'{"last_completed": 2'):
        assert st is not None and st.team_name == "" and st.elapsed == 0.0
    else:
        assert st is None


def test_corrupt_options_give_defaults(data_dir):
    (data_dir / save.OPTIONS_FILE).write_bytes(b"\xde\xad\xbe\xef")
    opts = save.load_options()
    assert opts == Options()
    (data_dir / save.OPTIONS_FILE).write_text(json.dumps({"timer_minutes": 17, "sound": "si", "tts": True}))
    opts = save.load_options()
    assert opts.timer_minutes == 0 and opts.sound is True and opts.tts is True


def test_options_roundtrip(data_dir):
    opts = Options(timer_minutes=45, sound=False, tts=True, uppercase=True)
    assert save.save_options(opts)
    assert save.load_options() == opts


def test_continue_from_corrupt_save_goes_to_menu(app, data_dir):
    (data_dir / save.SAVE_FILE).write_text("{rotto")
    from game.scenes.menu import MenuScene
    app.go_menu()
    assert isinstance(app.scene, MenuScene)
    assert not app.scene.has_save
    app.continue_game()
    assert isinstance(app.scene, MenuScene)
