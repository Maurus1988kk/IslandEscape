# Fuga dall'Isola Sperduta

**Italiano** | [English](README.en.md)

Escape room didattica di geografia sull'orientamento per la scuola primaria (7-9 anni),
pensata per la LIM (lavagna interattiva multimediale) e per il gioco a squadre.

Una classe di piccoli esploratori naufraga su un'isola sperduta. Casa è a **Nord**.
Con l'aiuto di Bussolino, un pappagallo esploratore, i bambini imparano a orientarsi,
superano sei tappe, raccolgono i pezzi di una zattera e tornano a casa.

## Le sei tappe

| Tappa | Cosa si impara | Premio |
|---|---|---|
| 1. La spiaggia del naufragio | i quattro punti cardinali e il loro ordine in senso orario (N, E, S, O) | Rosa dei venti |
| 2. L'alba sulla scogliera | il sole sorge a Est; il Nord non è sempre "in alto"; il trucco delle braccia | Corda |
| 3. Il bastone di mezzogiorno | l'ombra di un bastone durante il giorno: a mezzogiorno è la più corta e indica il Nord; seguire indicazioni come "2 passi a Nord" | Tronchi |
| 4. Il tramonto e la mappa del tesoro | il sole tramonta a Ovest; leggere una mappa con "a Nord di", "a Ovest di"... | Vela |
| 5. La notte stellata | trovare il Grande Carro e, prolungando le sue due stelle, la Stella Polare | Stella Polare |
| 6. La zattera e il viaggio verso casa | costruire la zattera e navigare verso Nord tra scogli e mulinelli | Diploma |

Caratteristiche principali:

- **non si perde mai**: gli errori ricevono un "Quasi! Riprova", dopo 2 errori compare un indizio
  e dopo 4 l'indizio diventa più esplicito;
- timer da escape room facoltativo (30, 45 o 60 minuti), che allo scadere non fa perdere;
- lettura vocale dei fumetti con la voce italiana di Windows e opzione TUTTO MAIUSCOLO;
- solo tocco o mouse, pulsanti grandi, salvataggio automatico alla fine di ogni tappa;
- grafica e suoni interamente generati via codice, contenuti scientificamente corretti
  (le stelle del Grande Carro sono nelle loro posizioni reali);
- diploma finale di "Esploratore dell'Orientamento" con le sei regole imparate.

Il gioco è in italiano. La guida per le insegnanti (durate, uso alla LIM, soluzioni,
attività in classe e in cortile) è in [`GUIDA_MAESTRE.txt`](GUIDA_MAESTRE.txt).

## Scaricare il gioco

L'eseguibile pronto si scarica dalla pagina
[Releases](https://github.com/Maurus1988kk/IslandEscape/releases/latest):
file `FugaDallIsola.exe` (insieme alla guida `GUIDA_MAESTRE.txt`).
Si avvia con un doppio clic, senza installare niente (Windows 10 o 11 a 64 bit).
Al primo avvio Windows SmartScreen può mostrare un avviso: "Ulteriori informazioni" → "Esegui comunque".

---

## Avvio da sorgente

Serve Python 3.11 o superiore (64 bit).

```bat
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py              :: schermo intero (F11 per la finestra)
.venv\Scripts\python.exe main.py --finestra   :: avvio in finestra
.venv\Scripts\python.exe main.py --selftest   :: autotest: apre tutte le scene, prova audio e voce
```

L'autotest scrive l'esito in `selftest.txt` nella cartella dei dati (vedi sotto) ed esce
con codice 0 se tutto è andato bene.

## Test

```bat
.venv\Scripts\python.exe -m pytest -q
```

I test usano SDL in modalità `dummy` (nessuna finestra, nessun audio) e una cartella dati
temporanea, quindi non toccano `%APPDATA%`. Ci sono 96 test:

| File | Cosa verifica |
|---|---|
| `tests/test_logic.py` | rosa dei venti ruotata (tutti e 4 gli orientamenti), modello del sole e dell'ombra, unicità delle risposte degli indovinelli, risolvibilità dei percorsi (tappa 3) e della mappa del mare (tappa 6), proiezione delle stelle (Polare a circa 5 volte la distanza Merak-Dubhe e sul loro prolungamento) |
| `tests/test_save.py` | salvataggio e opzioni, file rovinati o con dati sbagliati ignorati senza crash |
| `tests/test_smoke.py` | ogni scena si apre, si aggiorna e si disegna; 160 tocchi e trascinamenti casuali per scena senza errori; lettere accentate; suoni generati; audio assente; scala della finestra e conversione delle coordinate |
| `tests/test_playthrough.py` | partite simulate: ogni tappa viene giocata dall'inizio alla fine (con errori, indizi, "Ricomincia percorso", scogli), più menu, Continua, pausa, timer scaduto, scorciatoie della maestra, schermata di errore con log |

## Build dell'eseguibile

```bat
build.bat            :: installa le dipendenze, esegue i test, crea e prova l'exe
build.bat --no-test  :: come sopra ma senza pytest
```

Cosa fa `build.bat`:
1. cerca Python 3.11+ (`py -3.11`, poi `py -3`, poi `python`);
2. crea l'ambiente virtuale `.venv` (se manca) e installa `requirements.txt`;
3. genera i moduli `comtypes` della voce di Windows (SAPI) così vengono inclusi nell'exe,
   e l'icona `tools\icona.ico` (disegnata con pygame, salvata con Pillow);
4. esegue i test;
5. lancia PyInstaller con `--onefile --windowed --name FugaDallIsola` e gli hidden import
   per pyttsx3/comtypes/pywin32;
6. avvia `dist\FugaDallIsola.exe --selftest` e mostra l'esito.

## Struttura del codice

```
main.py                 avvio, log, messaggio di errore, autotest
game/
  config.py             costanti: risoluzione, layout, colori, oggetti
  testi.py              TUTTI i testi del gioco (dialoghi, domande, indizi, regole, diploma)
  state.py              stato della partita (squadra, tappa, inventario, errori, tempo) e opzioni
  save.py               salvataggio JSON in %APPDATA%\FugaIsola\, cartella dati, log
  audio.py              suoni generati con il modulo array (niente numpy)
  tts.py                lettura vocale con pyttsx3 in un thread separato
  app.py                finestra, scala con bande nere, eventi, scene, scorciatoie, errori
  logic/                logica pura, senza pygame (testata da pytest)
    rose.py             rosa dei venti e rotazione (tappe 1 e 2)
    sun.py              sole e ombra del bastone (tappa 3)
    grid.py             griglia dei tronchi (tappa 3) e mappa del mare (tappa 6)
    places.py           luoghi e indovinelli della mappa del tesoro (tappa 4)
    stars.py            Grande Carro, Stella Polare e proiezione polare (tappa 5)
  scenes/
    base.py             Scene e StageScene (fumetti, domande, errori, indizi, fine tappa)
    menu.py             menu principale e nome della squadra
    opzioni.py intro.py mappa.py pausa.py errore.py vittoria.py
    tappa1_spiaggia.py ... tappa6_zattera.py
    __init__.py         registro delle tappe (make_stage)
  ui/
    widgets.py          Button, Draggable, DragGroup, DropSlot, Slider, SpeechBubble,
                        Toast, HintCard, CompleteCard, InventoryBar
    parrot.py           Bussolino animato
    fonts.py            font, a capo automatico, opzione TUTTO MAIUSCOLO
  gfx/draw.py           tutte le funzioni di disegno (mare, isola, palme, sole, stelle,
                        rosa dei venti, zattera, luoghi della mappa, icone...)
tests/                  pytest
tools/make_icon.py      crea l'icona dell'exe
tools/screenshots.py    salva screenshot delle scene (utile per controllare la grafica)
```

### Come funziona una tappa

Ogni tappa è una sottoclasse di `StageScene` (in `scenes/base.py`) che offre:

- `say(righe, poi)`: fumetti di Bussolino con il pulsante "Avanti";
- `task(testo, indizio, indizio_esplicito, disegno=None, choices=None, on_choice=None)`:
  una domanda o un compito; con `choices` compaiono i pulsanti di risposta;
- `wrong(msg)` / `right(msg)`: feedback gentile con forma (spunta/croce) e colore;
  dopo 2 errori compare "Indizio", dopo 4 l'indizio diventa esplicito e la tappa
  riceve `on_hint(2)` per mostrare aiuti nella scena (lettere chiare, frecce, puntini...);
- `after(secondi, funzione)`: azioni ritardate (mai `sleep`: il ciclo non si blocca);
- `complete()`: schermata "Tappa superata!", oggetto che vola nell'inventario,
  salvataggio automatico, mappa dell'isola.

### Aggiungere o modificare tappe e testi

- **Testi**: si cambiano tutti in `game/testi.py` (frasi brevi, massimo 15-20 parole).
- **Percorsi della tappa 3**: `GRID3_ROUTES` e `GRID3_ROCKS` in `game/logic/grid.py`.
- **Mappa del mare della tappa 6**: `SEA_MAP` in `game/logic/grid.py`
  (`L` terraferma, `I` isola, `R` scoglio, `W` mulinello, `.` mare).
- **Luoghi e indovinelli della tappa 4**: `PLACES` e `RIDDLES` in `game/logic/places.py`.
- I test controllano automaticamente che percorsi e mappa siano risolvibili e che ogni
  indovinello abbia una sola risposta: dopo una modifica eseguire `pytest`.
- **Nuova tappa**: creare `game/scenes/tappaN_nome.py` con una classe che estende
  `StageScene` (impostare `stage = N`, scrivere `start()`, `on_event()`, `draw_background()`,
  `draw_play()`), registrarla in `game/scenes/__init__.py` e aggiornare `STAGE_COUNT`,
  `STAGE_ITEM` (config), `STAGE_TITLES`, `STAGE_RULES` e `DIPLOMA_RULES` (testi) e i
  segnaposto della mappa (`MARKERS` in `scenes/mappa.py`).

## Scelte fatte (dove il testo lasciava libertà)

- **pygame-ce invece di pygame**: è mantenuto attivamente, ha wheel pronte per le versioni
  recenti di Python, è compatibile con l'API di pygame e funziona con gli hook di
  PyInstaller (si importa sempre come `pygame`). Ha anche `smoothscale` ottimizzato,
  utile per scalare 1280x720 a schermo intero.
- **Font**: Verdana (presente in tutti i Windows, molto leggibile) con ripiego su
  Tahoma/Arial e infine sul font interno di pygame. All'avvio si verifica che le lettere
  accentate esistano. Nessuna emoji: spunte, croci e frecce sono disegnate.
- **Pulsanti che scattano alla pressione** (non al rilascio): più affidabile con il tocco
  della LIM. Un intervallo di sicurezza di 0,28 s evita i doppi tocchi; gli eventi doppi
  dello stesso tocco (entro 70 ms e 30 px) vengono scartati.
- **Tocco**: si usano gli eventi mouse che SDL genera dal tocco (gli eventi FINGER sono
  ignorati per non contare due volte). Se il rilascio di un trascinamento si perde, dopo
  0,6 s senza pulsante premuto l'etichetta viene rilasciata; se la finestra perde il
  focus i trascinamenti vengono annullati. Si accettano anche tasto destro e centrale
  (alcune LIM mandano il destro con la pressione prolungata).
- **Schermo intero "desktop"** (nessun cambio di risoluzione, più sicuro con i proiettori),
  processo marcato DPI-aware, il gioco non si riduce a icona se si cambia finestra.
- **Cartella dati**: `%APPDATA%\FugaIsola\` (`salvataggio.json`, `opzioni.json`,
  `log.txt`); se non è scrivibile si usa `~\FugaIsola`, poi la cartella temporanea.
  La variabile `FUGAISOLA_DATA_DIR` permette di cambiarla (usata da test e build).
- **Salvataggio**: scritto a fine tappa (file temporaneo + `os.replace`, quindi mai a metà).
  "Continua" riparte dalla mappa che porta alla tappa successiva. A fine gioco il
  salvataggio viene cancellato, così "Continua" sparisce.
- **Timer**: conta solo durante il gioco (intro, mappa e tappe), non nei menu e in pausa.
  Alla scadenza compare il messaggio di Bussolino e il tempo continua come "+mm:ss".
  Nel diploma c'è il tempo totale se il timer era attivo.
- **Lettura vocale**: pyttsx3 sceglie la voce italiana SAPI5 (es. "Microsoft Elsa"), poi le
  frasi vengono pronunciate con l'oggetto SAPI sottostante in modalità asincrona con
  "interrompi la frase precedente" (flag 3): così la voce non resta indietro quando si
  preme "Avanti". Se l'oggetto interno non fosse disponibile si usa `say()/runAndWait()`.
  Tutto avviene in un thread; errori o voce mancante disattivano l'opzione con un messaggio.
- **Audio**: suoni sintetizzati in un thread all'avvio (onde leggere in sottofondo nelle
  scene di mare). Se il mixer non parte, il gioco resta muto senza errori.
- **Tappa 2**: il lato dell'alba è scelto a caso a ogni partita (e a ogni "Ricomincia tappa").
- **Tappa 3**: lo slider va confermato con "Fatto!"; la punta dell'ombra si accetta entro
  42 px (e più vicino alla punta che al bastone). Sulla griglia il movimento è libero:
  quando i passi sono finiti, se l'esploratore non è sui tronchi si deve premere
  "Ricomincia percorso". Rocce e bordo non contano come errore.
- **Tappa 4**: "X è a Nord di Y" = stessa colonna, più in alto (Est/Ovest = stessa riga).
  La griglia della mappa è tratteggiata per rendere visibili righe e colonne.
- **Tappa 5**: rotazione −155° e scala 9,6: il Grande Carro è in alto a destra sopra la
  Polare, che sta a circa il 41% dell'altezza tra orizzonte e bordo alto. Per il primo
  passo basta toccare una stella del carro (tolleranza 36 px).
- **Tappa 6**: scogli e mulinelli contano come "errore gentile" (servono per far comparire
  l'indizio, che mostra una strada libera). L'evento del mattino scatta alla riga 6, quello
  della notte alla riga 3. Le tre stelle della domanda notturna sono Sirio, Vega e Polare.
- **Errori imprevisti**: vengono scritti nel log e compare una schermata "Ops!" con
  "Torna al menu"; dopo 3 errori in 15 secondi il gioco si chiude con un messaggio di Windows
  che indica dove si trova il log.
- **`.venv` nella cartella del progetto**: è la scelta più semplice. Se la cartella è dentro
  OneDrive, conviene escludere `.venv`, `build` e `dist` dalla sincronizzazione.
- **Nessuna tastiera a schermo** per il nome della squadra (è facoltativo e si può saltare).

## Limiti noti

- Il modello del sole è quello dell'equinozio (alba esattamente a Est, tramonto a Ovest,
  altezza massima 65°): è una semplificazione voluta, spiegata nella guida per le maestre.
- Su Windows non in italiano la voce italiana SAPI5 potrebbe mancare: in quel caso
  l'opzione si disattiva da sola con un messaggio.
- L'eseguibile non è firmato: Windows SmartScreen mostra un avviso al primo avvio
  (procedura nella guida). Alcuni antivirus possono essere sospettosi verso gli exe
  creati con PyInstaller `--onefile`.
- L'exe `--onefile` si scompatta in una cartella temporanea a ogni avvio: la prima
  apertura richiede qualche secondo.
