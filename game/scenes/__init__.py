"""Registro delle tappe: per aggiungerne una basta creare la classe e metterla qui."""


def stage_classes():
    from .tappa1_spiaggia import Tappa1
    from .tappa2_alba import Tappa2
    from .tappa3_mezzogiorno import Tappa3
    from .tappa4_tramonto import Tappa4
    from .tappa5_notte import Tappa5
    from .tappa6_zattera import Tappa6
    return {1: Tappa1, 2: Tappa2, 3: Tappa3, 4: Tappa4, 5: Tappa5, 6: Tappa6}


def make_stage(app, n):
    return stage_classes()[int(n)](app)
