# Escape from the Lost Island (Fuga dall'Isola Sperduta)

[Italiano](README.md) | **English**

An educational geography escape room about orientation for primary school children (ages 7-9),
designed for interactive whiteboards and team play.

A class of young explorers is shipwrecked on a lost island. Home is to the **North**.
With the help of Bussolino, an explorer parrot, the children learn how to find their way,
complete six stages, collect the pieces of a raft and sail back home.

> The game itself is in Italian (it was made for Italian primary schools).
> In-game words are quoted below in Italian, with a translation in brackets.

## The six stages

| Stage | What children learn | Reward |
|---|---|---|
| 1. The shipwreck beach | the four cardinal points and their clockwise order (N, E, S, W) | Compass rose |
| 2. Dawn on the cliffs | the sun rises in the East; North is not always "up"; the arms trick | Rope |
| 3. The noon stick | a stick's shadow during the day: at noon it is shortest and points North; following directions such as "2 steps North" | Logs |
| 4. Sunset and the treasure map | the sun sets in the West; reading a map with "north of", "west of"... | Sail |
| 5. The starry night | finding the Big Dipper and, by extending its two pointer stars, the North Star (Polaris) | North Star |
| 6. The raft and the journey home | building the raft and sailing North between rocks and whirlpools | Diploma |

Main features:

- **nobody ever loses**: mistakes get a gentle "Quasi! Riprova" ("Almost! Try again"), a hint
  button appears after 2 mistakes and the hint becomes more explicit after 4;
- optional escape-room timer (30, 45 or 60 minutes) that never makes you lose;
- optional read-aloud of the speech bubbles with the Italian Windows voice, and an
  ALL CAPS option for younger readers;
- touch or mouse only, large buttons, automatic save at the end of each stage;
- all graphics and sounds generated in code; scientifically correct content
  (the Big Dipper stars are drawn in their real positions);
- a final "Orientation Explorer Diploma" listing the six rules learned.

The teachers' guide (durations, whiteboard use, solutions, classroom and outdoor activities)
is in [`GUIDA_MAESTRE.txt`](GUIDA_MAESTRE.txt) (in Italian).

## Download

The ready-to-use executable is on the
[Releases](https://github.com/Maurus1988kk/IslandEscape/releases/latest) page:
`FugaDallIsola.exe` (together with the guide `GUIDA_MAESTRE.txt`).
Double-click to start, nothing to install (Windows 10 or 11, 64-bit).
On first launch Windows SmartScreen may show a warning: "More info" → "Run anyway"
(on Italian Windows: "Ulteriori informazioni" → "Esegui comunque").

---

## Running from source

Requires Python 3.11 or newer (64-bit).

```bat
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py              :: full screen (F11 toggles window mode)
.venv\Scripts\python.exe main.py --finestra   :: start in a window
.venv\Scripts\python.exe main.py --selftest   :: self-test: opens every scene, tests audio and voice
```

The self-test writes its report to `selftest.txt` in the data folder (see below) and exits
with code 0 when everything is fine.

## Tests

```bat
.venv\Scripts\python.exe -m pytest -q
```

The tests run SDL in `dummy` mode (no window, no audio) and use a temporary data folder,
so they never touch `%APPDATA%`. There are 96 tests:

| File | What it checks |
|---|---|
| `tests/test_logic.py` | rotated compass rose (all 4 orientations), sun and shadow model, each treasure-map riddle has exactly one answer, the stage 3 paths and the stage 6 sea map can be solved, star projection (Polaris at about 5 times the Merak-Dubhe distance and on their extension) |
| `tests/test_save.py` | saves and options; corrupted or invalid files are ignored without crashing |
| `tests/test_smoke.py` | every scene opens, updates and draws; 160 random taps and drags per scene without errors; accented letters; generated sounds; missing audio device; window scaling and coordinate conversion |
| `tests/test_playthrough.py` | simulated games: every stage is played from start to finish (with mistakes, hints, "restart path", rocks), plus menu, Continue, pause, timer expiry, teacher shortcuts, error screen with log |

## Building the executable

```bat
build.bat            :: installs dependencies, runs the tests, builds and checks the exe
build.bat --no-test  :: same, without pytest
```

What `build.bat` does:
1. finds Python 3.11+ (`py -3.11`, then `py -3`, then `python`);
2. creates the `.venv` virtual environment (if missing) and installs `requirements.txt`;
3. generates the `comtypes` modules for the Windows voice (SAPI) so they are bundled in the exe,
   and the icon `tools\icona.ico` (drawn with pygame, saved with Pillow);
4. runs the tests;
5. runs PyInstaller with `--onefile --windowed --name FugaDallIsola` and the hidden imports
   for pyttsx3/comtypes/pywin32;
6. starts `dist\FugaDallIsola.exe --selftest` and prints the report.

## Code structure

```
main.py                 startup, logging, error message box, self-test
game/
  config.py             constants: resolution, layout, colours, items
  testi.py              ALL in-game texts (dialogues, questions, hints, rules, diploma)
  state.py              game state (team, stage, inventory, mistakes, time) and options
  save.py               JSON saves in %APPDATA%\FugaIsola\, data folder, log
  audio.py              sounds synthesised with the array module (no numpy)
  tts.py                read-aloud with pyttsx3 in a separate thread
  app.py                window, letterboxed scaling, events, scenes, shortcuts, errors
  logic/                pure logic, no pygame (covered by pytest)
    rose.py             compass rose and rotation (stages 1 and 2)
    sun.py              sun and stick shadow (stage 3)
    grid.py             log-hunt grid (stage 3) and sea map (stage 6)
    places.py           treasure-map places and riddles (stage 4)
    stars.py            Big Dipper, North Star and polar projection (stage 5)
  scenes/
    base.py             Scene and StageScene (speech bubbles, questions, mistakes, hints, stage end)
    menu.py             main menu and team name
    opzioni.py intro.py mappa.py pausa.py errore.py vittoria.py
                        (options, intro, progress map, pause, error screen, victory)
    tappa1_spiaggia.py ... tappa6_zattera.py   (stages 1-6)
    __init__.py         stage registry (make_stage)
  ui/
    widgets.py          Button, Draggable, DragGroup, DropSlot, Slider, SpeechBubble,
                        Toast, HintCard, CompleteCard, InventoryBar
    parrot.py           animated Bussolino
    fonts.py            fonts, word wrapping, ALL CAPS option
  gfx/draw.py           all drawing functions (sea, island, palms, sun, stars,
                        compass rose, raft, map places, icons...)
tests/                  pytest
tools/make_icon.py      creates the exe icon
tools/screenshots.py    saves scene screenshots (handy for checking the graphics)
```

### How a stage works

Each stage is a subclass of `StageScene` (in `scenes/base.py`), which provides:

- `say(lines, then)`: Bussolino's speech bubbles with the "Avanti" (Next) button;
- `task(text, hint, explicit_hint, drawer=None, choices=None, on_choice=None)`:
  a question or a task; with `choices`, answer buttons appear;
- `wrong(msg)` / `right(msg)`: gentle feedback using both shape (tick/cross) and colour;
  after 2 mistakes the "Indizio" (Hint) button appears, after 4 the hint becomes explicit
  and the stage receives `on_hint(2)` to show on-screen help (faded letters, arrows, dots...);
- `after(seconds, function)`: delayed actions (never `sleep`: the loop never blocks);
- `complete()`: "Tappa superata!" (Stage complete!) screen, item flying into the inventory,
  automatic save, island map.

### Adding or changing stages and texts

- **Texts**: all of them are in `game/testi.py` (short sentences, 15-20 words at most).
- **Stage 3 paths**: `GRID3_ROUTES` and `GRID3_ROCKS` in `game/logic/grid.py`.
- **Stage 6 sea map**: `SEA_MAP` in `game/logic/grid.py`
  (`L` mainland, `I` island, `R` rock, `W` whirlpool, `.` open sea).
- **Stage 4 places and riddles**: `PLACES` and `RIDDLES` in `game/logic/places.py`.
- The tests automatically check that paths and the sea map can be solved and that every
  riddle has exactly one answer: run `pytest` after any change.
- **New stage**: create `game/scenes/tappaN_name.py` with a class extending `StageScene`
  (set `stage = N`, implement `start()`, `on_event()`, `draw_background()`, `draw_play()`),
  register it in `game/scenes/__init__.py` and update `STAGE_COUNT`, `STAGE_ITEM` (config),
  `STAGE_TITLES`, `STAGE_RULES` and `DIPLOMA_RULES` (texts) and the map markers
  (`MARKERS` in `scenes/mappa.py`).

## Design choices (where the specification left room)

- **pygame-ce instead of pygame**: actively maintained, ships wheels quickly for new Python
  versions, API-compatible with pygame and works with the PyInstaller hooks (it is still
  imported as `pygame`). Its optimised `smoothscale` helps when scaling 1280x720 to full screen.
- **Font**: Verdana (present on every Windows, very readable) with Tahoma/Arial and finally
  pygame's built-in font as fallbacks. Accented letters are checked at startup.
  No emoji: ticks, crosses and arrows are drawn.
- **Buttons fire on press** (not on release): more reliable with whiteboard touch.
  A 0.28 s safety interval prevents double taps; duplicate events from the same touch
  (within 70 ms and 30 px) are discarded.
- **Touch**: the game uses the mouse events SDL generates from touch (FINGER events are
  ignored to avoid counting twice). If the release of a drag gets lost, the label is dropped
  after 0.6 s without a pressed button; drags are cancelled when the window loses focus.
  Right and middle buttons are accepted too (some whiteboards send a right click on long press).
- **"Desktop" full screen** (no resolution change, safer with projectors), DPI-aware process,
  the game does not minimise when switching to another window.
- **Data folder**: `%APPDATA%\FugaIsola\` (`salvataggio.json` save, `opzioni.json` options,
  `log.txt`); if not writable, `~\FugaIsola`, then the temp folder.
  The `FUGAISOLA_DATA_DIR` variable overrides it (used by tests and the build).
- **Saving**: written at the end of each stage (temporary file + `os.replace`, so never
  half-written). "Continua" (Continue) restarts from the map leading to the next stage.
  The save is deleted when the game is won, so "Continua" disappears.
- **Timer**: counts only during play (intro, map and stages), not in menus or while paused.
  When it runs out Bussolino shows his message and time keeps counting as "+mm:ss".
  The diploma shows the total time if the timer was on.
- **Read-aloud**: pyttsx3 picks the Italian SAPI5 voice (e.g. "Microsoft Elsa"); sentences
  are then spoken through the underlying SAPI object, asynchronously and with "purge before
  speak" (flag 3), so the voice never lags behind when "Avanti" is pressed. If that internal
  object is not available, `say()/runAndWait()` is used. Everything runs in a thread;
  errors or a missing voice switch the option off with a message.
- **Audio**: sounds are synthesised in a thread at startup (soft waves in the background of
  sea scenes). If the mixer fails, the game simply stays silent.
- **Stage 2**: the side where the sun rises is random for every game (and every stage restart).
- **Stage 3**: the slider must be confirmed with "Fatto!" (Done!); the shadow tip is accepted
  within 42 px (and closer to the tip than to the stick). On the grid movement is free: when
  all steps are used and the explorer is not on the logs, "Ricomincia percorso" (Restart path)
  must be pressed. Rocks and the edge do not count as mistakes.
- **Stage 4**: "X is north of Y" means same column, higher up (east/west: same row).
  The map grid is dashed so rows and columns are visible.
- **Stage 5**: rotation −155° and scale 9.6: the Big Dipper is above and to the right of
  Polaris, which sits at about 41% of the height between horizon and top edge. For the first
  step, tapping any Dipper star is enough (36 px tolerance).
- **Stage 6**: rocks and whirlpools count as a "gentle mistake" (so the hint, which shows a
  free route, can appear). The morning event triggers at row 6, the night event at row 3.
  The three stars in the night question are Sirius, Vega and Polaris.
- **Unexpected errors**: written to the log and an "Ops!" screen with "Torna al menu"
  (Back to menu) appears; after 3 errors within 15 seconds the game closes with a Windows
  message box saying where the log is.
- **`.venv` inside the project folder**: the simplest option. If the folder is inside
  OneDrive, exclude `.venv`, `build` and `dist` from syncing.
- **No on-screen keyboard** for the team name (it is optional and can be skipped).

## Known limitations

- The sun model is the equinox one (sunrise exactly East, sunset exactly West, maximum
  height 65°): a deliberate simplification, explained in the teachers' guide.
- On non-Italian Windows the Italian SAPI5 voice may be missing: the option then switches
  itself off with a message.
- The executable is not signed: Windows SmartScreen shows a warning on first launch
  (steps in the guide). Some antivirus tools may be suspicious of PyInstaller `--onefile` exes.
- A `--onefile` exe unpacks to a temporary folder on every launch, so it takes a few seconds
  to open.
