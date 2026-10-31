"""Tutti i testi del gioco, in un unico posto per poterli modificare facilmente.

Regola: frasi brevi (massimo 15-20 parole), italiano semplice.
"""

# ---------------------------------------------------------------- generali
STAGE_TITLES = {
    1: "La spiaggia del naufragio",
    2: "L'alba sulla scogliera",
    3: "Il bastone di mezzogiorno",
    4: "Il tramonto e la mappa del tesoro",
    5: "La notte stellata",
    6: "La zattera e il viaggio verso casa",
}

# Frase-regola mostrata a fine tappa (e riassunta nel diploma).
STAGE_RULES = {
    1: "Sulle mappe il Nord è in alto. In senso orario: Nord, Est, Sud, Ovest!",
    2: "Il sole sorge a EST! Braccio destro verso il sole: davanti c'è il Nord.",
    3: "A mezzogiorno l'ombra è la più corta e indica il NORD!",
    4: "Il sole tramonta a OVEST!",
    5: "Il Grande Carro ci porta alla Stella Polare. Lei indica il NORD!",
}

DIPLOMA_RULES = [
    "Il Nord è in alto. In senso orario: Nord, Est, Sud, Ovest.",
    "Il sole sorge a Est: braccio destro al sole, davanti c'è il Nord.",
    "A mezzogiorno l'ombra è cortissima e indica il Nord.",
    "Il sole tramonta a Ovest.",
    "Il Grande Carro ci porta alla Stella Polare: lei indica il Nord.",
    "Con i punti cardinali troviamo sempre la strada di casa!",
]

WRONG_DEFAULT = "Quasi! Riprova."
RIGHT_DEFAULT = ["Bravi!", "Giusto!", "Bravissimi!", "Esatto!", "Ottimo!"]
STAGE_DONE = "Tappa superata!"
TIMER_EXPIRED = "Il tempo è finito, ma i veri esploratori non si arrendono! Continuiamo?"
HINT_TITLE = "Indizio"
HINT_EXPLICIT_TITLE = "Indizio speciale"

# ---------------------------------------------------------------- intro
def intro_lines(team_name):
    hello = "Ciao esploratori!"
    if team_name:
        hello = f"Ciao, squadra {team_name}!"
    return [
        f"{hello} Sono Bussolino, il pappagallo esploratore.",
        "Stavamo navigando in canoa verso Sud. Ma una grande tempesta ha rotto le nostre canoe!",
        "Siamo finiti su un'isola sperduta!",
        "Casa nostra è a NORD, sulla terraferma.",
        "Per tornarci dobbiamo imparare a orientarci e costruire una zattera. Siete pronti?",
    ]

INTRO_READY = "Siamo pronti!"

# ---------------------------------------------------------------- mappa
MAP_NEXT = "Prossima tappa:"
MAP_START = "Ecco la nostra isola. Partiamo dalla spiaggia!"
MAP_HOME = "Ultima tappa: costruiamo la zattera e torniamo a casa!"

# ---------------------------------------------------------------- tappa 1
T1_INTRO = [
    "Ecco la spiaggia del naufragio. Guardate le nostre canoe rotte!",
    "La rosa dei venti della canoa è andata in pezzi.",
    "Rimettiamola a posto! Ricordate: sulle mappe il Nord è in alto.",
]
T1_TASK = "Trascinate le lettere N, E, S, O nelle caselle giuste."
T1_HINT = "Il Nord è in alto e il Sud in basso. L'Est è a destra."
T1_HINT2 = "N va in alto, S in basso, E a destra e O a sinistra."
T1_DONE = "Bravissimi! La rosa dei venti è di nuovo intera!"
T1_ORDER_INTRO = "Ora un gioco veloce. Giriamo come le lancette dell'orologio!"
T1_ORDER_Q = [
    ("Partendo dal Nord e girando come le lancette dell'orologio, quale viene dopo?", "E"),
    ("E dopo l'Est, quale viene?", "S"),
    ("E dopo il Sud?", "O"),
]
T1_ORDER_HINT = "Seguite la freccia che gira come le lancette: dall'alto va verso destra."
T1_ORDER_HINT2 = {
    "E": "Dopo il Nord viene l'Est!",
    "S": "Dopo l'Est viene il Sud!",
    "O": "Dopo il Sud viene l'Ovest!",
}
T1_ORDER_DONE = "Perfetto! Nord, Est, Sud, Ovest. E poi si torna al Nord!"

# ---------------------------------------------------------------- tappa 2
T2_INTRO = [
    "Che notte! Siamo sulla scogliera. Ora vediamo la radura dall'alto.",
    "Attenzione: qui non sappiamo dov'è il Nord. Ci aiuterà il sole!",
]
T2_SUNRISE = "Guardate! Il sole sta sorgendo..."
T2_Q1 = "Il sole sta sorgendo. Da che parte sorge il sole?"
T2_Q1_HINT = "Pensate alla rosa dei venti: il sole sorge dalla parte che inizia con la E."
T2_Q1_HINT2 = "Il sole sorge sempre a Est!"
T2_Q1_OK = "Giusto! Il sole sorge a Est. Metto la E dalla parte del sole."
T2_Q2 = "Ora trascinate N, S e O nei posti giusti intorno all'esploratore."
T2_Q2_HINT = "Braccio destro verso il sole che sorge: davanti a te c'è il Nord!"
T2_Q2_HINT2 = "Davanti c'è il Nord, dietro il Sud, a sinistra l'Ovest. Guardate le lettere chiare!"
T2_DONE = "Bravissimi! Il Nord non è sempre in alto: dipende da come sei girato!"

# ---------------------------------------------------------------- tappa 3
T3_INTRO = [
    "Ci servono dei tronchi. Ma prima, un trucco da veri esploratori!",
    "Questo è un bastone piantato nella sabbia. Lo guardiamo dall'alto.",
    "Qui il Nord è in alto. Muovete il sole e guardate l'ombra!",
]
T3_TASK_SHORT = "Muovete il sole fino a quando l'ombra diventa la più corta di tutte!"
T3_SHORT_WRONG = "Quasi! L'ombra può diventare ancora più corta."
T3_SHORT_HINT = "L'ombra è più corta quando il sole è più alto nel cielo."
T3_SHORT_HINT2 = "Portate il sole a metà strada, sul segno giallo: è mezzogiorno!"
T3_SHORT_OK = "Bravi! È mezzogiorno: il sole è a Sud ed è altissimo."
T3_TASK_TIP = "A mezzogiorno l'ombra indica il Nord. Toccate la punta dell'ombra!"
T3_TIP_WRONG = "Quasi! Toccate dove finisce l'ombra."
T3_TIP_HINT = "L'ombra parte dal bastone. Toccate il punto dove finisce!"
T3_TIP_HINT2 = "Toccate il cerchio giallo, sulla punta dell'ombra!"
T3_TIP_OK = "Esatto! L'ombra di mezzogiorno indica il Nord."
T3_BONUS = "E la mattina, l'ombra verso dove punta? Provate col sole!"
T3_BONUS_HINT = "Spostate il sole verso la mattina e guardate l'ombra. La rosa vi aiuta!"
T3_BONUS_HINT2 = "La mattina il sole è a Est, quindi l'ombra va dalla parte opposta: Ovest!"
T3_BONUS_OK = "Giusto! La mattina l'ombra punta a Ovest. La sera punta a Est."
T3_GRID_INTRO = [
    "Ora cerchiamo i tronchi per la zattera!",
    "Seguite le mie indicazioni con i pulsanti N, E, S, O. Un passo alla volta!",
]
T3_GRID_WRONG = "Quasi! Qui non ci sono tronchi. Premete Ricomincia percorso."
T3_GRID_ROCK = "C'è una roccia! Di lì non si passa."
T3_GRID_SEA = "Lì c'è il mare! Restiamo sull'isola."
T3_GRID_HINT = "Contate i passi uno alla volta. Il Nord è in alto, l'Est è a destra."
T3_GRID_HINT2 = "Seguite i puntini gialli sulla mappa!"
T3_GRID_FOUND = "Trovati i tronchi!"
T3_RESTART = "Ricomincia percorso"

# ---------------------------------------------------------------- tappa 4
T4_INTRO = [
    "Che bella giornata! Ora il sole sta scendendo verso il mare.",
]
T4_Q1 = "Il sole sta tramontando. Da che parte tramonta?"
T4_Q1_HINT = "Il sole sorge a Est e tramonta dalla parte opposta."
T4_Q1_HINT2 = "Il sole tramonta a Ovest!"
T4_Q1_OK = "Giusto! Il sole tramonta a Ovest."
T4_MAP_INTRO = [
    "Ecco la mappa dell'isola. Il Nord è in alto, come sempre sulle mappe.",
    "Per la vela servono tre cose. Risolvete i miei indovinelli e toccate il posto giusto!",
]
T4_WRONG = "Quasi! Riprova."
T4_DONE_PIECE = ["Trovata la corda!", "Trovata la tela!", "Trovato l'albero!"]

# ---------------------------------------------------------------- tappa 5
T5_INTRO = [
    "È notte. Il cielo è pieno di stelle!",
    "Le stelle possono aiutarci a trovare il Nord. Proviamo!",
]
T5_FIND = "Trovate il Grande Carro! Sembra un carretto con un manico lungo."
T5_FIND_WRONG = "Quasi! Cercate sette stelle più luminose."
T5_FIND_HINT = "Cercate sette stelle grandi: quattro fanno il carretto, tre fanno il manico."
T5_FIND_HINT2 = "Toccate una delle stelle che lampeggiano!"
T5_FIND_OK = "Bravi! Ecco il Grande Carro. Fa parte della costellazione dell'Orsa Maggiore."
T5_POINTERS = "Ora toccate le due stelle in fondo al carro, dalla parte opposta al manico."
T5_POINTERS_WRONG = "Quasi! Cercate le due stelle lontane dal manico."
T5_POINTERS_HINT = "Il manico è da una parte. Le due stelle sono all'altra estremità del carro."
T5_POINTERS_HINT2 = "Toccate le due stelle che lampeggiano!"
T5_POINTERS_ONE = "Bene! Ora toccate l'altra."
T5_POINTERS_OK = "Esatto! Queste due stelle ci indicano la strada."
T5_LINE = "Prolunghiamo la linea circa 5 volte: lì c'è una stella da sola, la Stella Polare. Toccatela!"
T5_LINE_WRONG = "Quasi! Seguite la linea tratteggiata."
T5_LINE_HINT = "Misurate la distanza tra le due stelle e riportatela 5 volte, come col righello."
T5_LINE_HINT2 = "Il righello arriva alla Stella Polare: toccate la stella che lampeggia!"
T5_LINE_OK = "Trovata! È la Stella Polare."
T5_NORTH = "La Stella Polare indica sempre il Nord! Trascinate la N sull'orizzonte, proprio sotto di lei."
T5_NORTH_WRONG = "Quasi! La N va proprio sotto la Stella Polare."
T5_NORTH_HINT = "Guardate la Stella Polare e scendete dritti fino all'orizzonte."
T5_NORTH_HINT2 = "Portate la N nel cerchio giallo!"
T5_NORTH_OK = "Perfetto! Sotto la Stella Polare c'è il Nord."

# ---------------------------------------------------------------- tappa 6
T6_INTRO = [
    "Eccoci sulla spiaggia a Nord dell'isola. Costruiamo la zattera!",
]
T6_BUILD = "Trascinate i pezzi sulla zattera, nell'ordine giusto."
T6_BUILD_WRONG = {
    "corda": "Quasi! Prima ci vuole la base della zattera.",
    "vela": "Quasi! La vela va messa per ultima.",
    "tronchi": "Quasi! Riprova.",
}
T6_BUILD_WRONG_LATE = "Quasi! Prima legate i tronchi con la corda."
T6_BUILD_HINT = "Prima si fa la base, poi si legano i pezzi, poi si mette la vela."
T6_BUILD_HINT2 = "Prima i Tronchi, poi la Corda, infine la Vela!"
T6_BUILD_OK = ["Ecco la base!", "Tronchi legati!", "Vela montata!"]
T6_SAIL_INTRO = [
    "La zattera è pronta! Ora navighiamo verso Nord, verso casa.",
    "Usate i pulsanti N, E, S, O. Attenti agli scogli e ai mulinelli!",
]
T6_NAV = "Portate la zattera verso Nord, fino alla terraferma!"
T6_ROCK = "Attenti, uno scoglio! Torniamo indietro di un passo."
T6_WHIRL = "Un mulinello! La zattera gira e torna indietro."
T6_ISLAND = "Lì c'è l'isola! Dobbiamo andare verso Nord."
T6_EDGE = "Non andiamo troppo lontano! Casa è a Nord."
T6_NAV_HINT = "Evitate scogli e mulinelli: cercate il mare libero verso l'alto."
T6_NAV_HINT2 = "Seguite i puntini gialli!"
T6_DAY_Q = "È mattina e stiamo andando verso Nord. Il sole ce l'abbiamo a destra o a sinistra?"
T6_DAY_HINT = "Di mattina il sole è a Est. Dov'è l'Est quando guardiamo verso Nord?"
T6_DAY_HINT2 = "Guardando verso Nord, l'Est è a destra. Quindi il sole è a destra!"
T6_DAY_OK = "Giusto! Il sole è a Est: alla nostra destra."
T6_DAY_RIGHT = "A destra"
T6_DAY_LEFT = "A sinistra"
T6_NIGHT_INTRO = "Si è fatta notte! Il cielo si riempie di stelle."
T6_NIGHT_Q = "Per andare a Nord, quale stella dobbiamo avere davanti? Toccatela!"
T6_NIGHT_HINT = "È la stella che abbiamo trovato col Grande Carro!"
T6_NIGHT_HINT2 = "È la Stella Polare, quella indicata dal Grande Carro!"
T6_NIGHT_OK = "Esatto! Teniamo la Stella Polare davanti a noi."
T6_STARS = [("Sirio", False), ("Stella Polare", True), ("Vega", False)]
T6_LAND = "Terra! Siamo arrivati a casa!"

# ---------------------------------------------------------------- vittoria
VICTORY_TITLE = "Ce l'avete fatta! Siete tornati a casa!"
DIPLOMA_TITLE = "Diploma di Esploratore dell'Orientamento"
VICTORY_AGAIN = "Gioca ancora"
VICTORY_MENU = "Menu"
