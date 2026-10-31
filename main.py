"""Avvio di "Fuga dall'Isola Sperduta".

    python main.py              schermo intero (F11 per la finestra)
    python main.py --finestra   avvio in finestra
    python main.py --selftest   prova automatica (usata per verificare l'eseguibile)
"""

import logging
import logging.handlers
import os
import sys
import traceback


def setup_logging():
    from game import save
    path = save.log_path()
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=400_000, backupCount=1, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger("fuga")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    return path


def show_message(title, text):
    """Finestra di messaggio di Windows (funziona anche senza console)."""
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, title, 0x40)
            return
    except Exception:
        pass
    print(f"{title}: {text}", file=sys.stderr)


def selftest():
    """Apre ogni scena per qualche fotogramma, prova audio e voce, scrive l'esito e chiude."""
    import time
    import pygame
    from game import save
    from game.app import App
    from game.scenes import stage_classes
    from game.scenes.intro import IntroScene
    from game.scenes.mappa import MapScene
    from game.scenes.menu import MenuScene, TeamScene
    from game.scenes.opzioni import OptionsScene
    from game.scenes.pausa import PauseOverlay, TimerOverlay
    from game.scenes.vittoria import VictoryScene
    from game.ui import fonts

    report = []
    ok = True
    app = App(fullscreen=False)
    report.append(f"display driver: {pygame.display.get_driver()}")
    report.append(f"font accenti: {fonts.get(30).metrics('àèéìòù') is not None}")
    factories = [lambda: MenuScene(app), lambda: TeamScene(app), lambda: OptionsScene(app),
                 lambda: IntroScene(app), lambda: MapScene(app, 3)]
    factories += [(lambda c=c: c(app)) for c in stage_classes().values()]
    factories.append(lambda: VictoryScene(app))
    worst = 0.0
    for size in ((1280, 720), (1920, 1080)):
        try:
            pygame.display.set_mode(size, pygame.RESIZABLE)
        except pygame.error:
            continue
        for make in factories:
            try:
                app.state.prepare_stage(6)
                scene = make()
                app.change_scene(scene)
                app.frame(1 / 60)
                t0 = time.perf_counter()
                for _ in range(20):
                    app.frame(1 / 60)
                ms = (time.perf_counter() - t0) / 20 * 1000
                worst = max(worst, ms)
                report.append(f"scena {type(scene).__name__} a {size[0]}x{size[1]}: ok, {ms:.1f} ms per fotogramma")
            except Exception:
                ok = False
                report.append(f"scena: ERRORE\n{traceback.format_exc()}")
    report.append(f"fotogramma più lento: {worst:.1f} ms (60 FPS = 16.7 ms)")
    for ov in (PauseOverlay, TimerOverlay):
        try:
            app.overlay = ov(app)
            for _ in range(5):
                app.frame(1 / 60)
            app.overlay = None
            report.append(f"finestra {ov.__name__}: ok")
        except Exception:
            ok = False
            report.append(f"finestra {ov.__name__}: ERRORE\n{traceback.format_exc()}")
    app.audio.wait_ready()
    report.append(f"audio: {'ok, ' + str(len(app.audio.sounds)) + ' suoni' if app.audio.ok else 'non disponibile'}")
    app.tts.enable()
    end = time.time() + 15
    while app.tts.status == "starting" and time.time() < end:
        time.sleep(0.05)
    report.append(f"voce: {app.tts.status} - {app.tts.message}")
    if app.tts.status == "ready":
        app.tts.say("Prova della voce.")
        time.sleep(1.0)
    app.shutdown()
    report.append("ESITO: " + ("OK" if ok else "ERRORI"))
    out = save.data_dir() / "selftest.txt"
    out.write_text("\n".join(report), encoding="utf-8")
    return 0 if ok else 1


def main():
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        log_path = setup_logging()
    except Exception:
        log_path = None
    log = logging.getLogger("fuga")
    log.info("Avvio del gioco (python %s)", sys.version.split()[0])
    args = [a.lower() for a in sys.argv[1:]]
    if "--selftest" in args:
        try:
            return selftest()
        except Exception:
            log.exception("Autotest fallito")
            return 2
    try:
        from game.app import App
        app = App(fullscreen=not ("--finestra" in args or "--window" in args))
        app.run()
        if app.fatal_message:
            show_message("Fuga dall'Isola Sperduta", app.fatal_message)
            return 1
    except Exception:
        log.exception("Errore all'avvio")
        show_message("Fuga dall'Isola Sperduta",
                     "Il gioco non è riuscito a partire.\n"
                     f"I dettagli sono nel file:\n{log_path or 'log.txt'}")
        return 1
    log.info("Chiusura normale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
