"""Lettura vocale opzionale con pyttsx3 (voce italiana di Windows).

Tutto gira in un thread separato: il gioco non si blocca mai.
Se pyttsx3 manca, non c'è una voce italiana o qualcosa va storto, lo stato
diventa "error" con un messaggio chiaro e l'opzione si disattiva da sola.
"""

import logging
import sys
import threading
import time

log = logging.getLogger("fuga")

OFF, STARTING, READY, ERROR = "off", "starting", "ready", "error"


def _is_italian(voice):
    langs = []
    for lang in getattr(voice, "languages", None) or []:
        if isinstance(lang, bytes):
            lang = lang.decode("ascii", "ignore")
        langs.append(str(lang).lower())
    text = " ".join(langs + [str(getattr(voice, "id", "")), str(getattr(voice, "name", ""))]).lower()
    return any(key in text for key in ("it-it", "it_it", "italian", "italiano")) or any(
        lang.startswith("it") for lang in langs
    )


class TTS:
    def __init__(self):
        self.status = OFF
        self.message = ""
        self.voice_name = ""
        self.enabled = False
        self._thread = None
        self._lock = threading.Lock()
        self._pending = None
        self._quit = False
        self._wake = threading.Event()

    # -------------------------------------------------------- API
    def enable(self):
        self.enabled = True
        if self.status == ERROR:
            return
        if self._thread is None:
            self.status = STARTING
            self.message = "Controllo la voce..."
            self._thread = threading.Thread(target=self._run, name="tts", daemon=True)
            self._thread.start()

    def disable(self):
        self.enabled = False
        self.stop()

    def say(self, text):
        if not self.enabled or self.status not in (STARTING, READY) or not text:
            return
        with self._lock:
            self._pending = str(text)
        self._wake.set()

    def stop(self):
        with self._lock:
            self._pending = ""
        self._wake.set()

    def shutdown(self):
        self._quit = True
        self.stop()

    # -------------------------------------------------------- thread
    def _fail(self, message, exc=None):
        self.status = ERROR
        self.enabled = False
        self.message = message
        if exc is not None:
            log.warning("Lettura vocale disattivata: %s (%r)", message, exc)
        else:
            log.info("Lettura vocale disattivata: %s", message)

    def _run(self):
        try:
            com_ok = False
            try:
                import pythoncom  # pywin32, necessario al driver sapi5
                pythoncom.CoInitialize()
                com_ok = True
            except Exception:
                pythoncom = None
            try:
                import pyttsx3
            except Exception as exc:
                self._fail("Lettura vocale non disponibile su questo computer.", exc)
                return
            try:
                engine = pyttsx3.init("sapi5") if sys.platform == "win32" else pyttsx3.init()
                voices = engine.getProperty("voices") or []
            except Exception as exc:
                self._fail("Lettura vocale non disponibile su questo computer.", exc)
                return
            italian = [v for v in voices if _is_italian(v)]
            if not italian:
                self._fail("Nessuna voce italiana trovata su questo computer.")
                return
            voice = italian[0]
            engine.setProperty("voice", voice.id)
            engine.setProperty("rate", 140)  # un po' più lenta, per i bambini
            engine.setProperty("volume", 1.0)
            self.voice_name = str(getattr(voice, "name", "voce italiana"))
            # Oggetto SAPI sottostante: permette di interrompere la frase precedente.
            sapi = getattr(getattr(getattr(engine, "proxy", None), "_driver", None), "_tts", None)
            self.status = READY
            self.message = "Voce pronta: " + self.voice_name.split(" - ")[0].replace("Microsoft ", "")
            log.info("Lettura vocale pronta (%s)", self.voice_name)
            self._loop(engine, sapi, pythoncom)
        except Exception as exc:
            self._fail("Lettura vocale non disponibile su questo computer.", exc)
        finally:
            try:
                if com_ok:
                    pythoncom.CoUninitialize()
            except Exception:
                pass

    def _loop(self, engine, sapi, pythoncom):
        while not self._quit:
            self._wake.wait(0.05)
            self._wake.clear()
            with self._lock:
                text, self._pending = self._pending, None
            if text is not None:
                if sapi is not None:
                    # 1 = asincrono, 2 = interrompi ciò che stava dicendo
                    sapi.Speak(text, 3)
                elif text:
                    engine.say(text)
                    engine.runAndWait()
            if pythoncom is not None:
                try:
                    pythoncom.PumpWaitingMessages()
                except Exception:
                    pass
            time.sleep(0.01)
        if sapi is not None:
            try:
                sapi.Speak("", 3)
            except Exception:
                pass
