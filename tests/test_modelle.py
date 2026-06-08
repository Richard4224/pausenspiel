"""
tests/test_modelle.py – Unit Tests für modelle.py
==================================================
Getestet werden alle drei Klassen:
    Schiff    – Trefferzustand und versenkt-Property
    Spielfeld – Platzierungslogik, Schuss-Auswertung, Spielende
    KI        – Schuss-Koordinaten, keine Duplikate

Ausführen:
    pytest tests/
    pytest tests/ -v          # ausführliche Ausgabe
    pytest tests/ -v --tb=short
"""

import sys
import os

# Sicherstellen dass modelle.py gefunden wird (wenn pytest aus einem
# anderen Verzeichnis gestartet wird)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from modelle import Schiff, Spielfeld, KI, FLOTTE, SCHIFF_NAMEN


# ═══════════════════════════════════════════════════════════════
#  Hilfsfunktionen
# ═══════════════════════════════════════════════════════════════

def feld_mit_schiff(groesse=3, x=0, y=0, horizontal=True):
    """Erstellt ein Spielfeld mit einem einzelnen platzierten Schiff."""
    feld   = Spielfeld()
    schiff = Schiff(groesse)
    feld.platzieren(schiff, x, y, horizontal)
    return feld, schiff


# ═══════════════════════════════════════════════════════════════
#  Tests: Schiff
# ═══════════════════════════════════════════════════════════════

class TestSchiff:

    def test_initial_nicht_versenkt(self):
        """Neues Schiff ist nicht versenkt."""
        s = Schiff(3)
        assert s.versenkt is False

    def test_versenkt_nach_allen_treffern(self):
        """Schiff gilt als versenkt wenn alle Felder getroffen wurden."""
        s = Schiff(3)
        s.felder  = [(0, 0), (1, 0), (2, 0)]
        s.treffer = {(0, 0), (1, 0), (2, 0)}
        assert s.versenkt is True

    def test_nicht_versenkt_bei_teiltreffern(self):
        """Schiff mit nur teilweise getroffenen Feldern ist nicht versenkt."""
        s = Schiff(3)
        s.felder  = [(0, 0), (1, 0), (2, 0)]
        s.treffer = {(0, 0), (1, 0)}
        assert s.versenkt is False

    def test_versenkt_einzel_schiff(self):
        """Ein Schiff der Größe 1 ist nach einem Treffer versenkt."""
        s = Schiff(1)
        s.felder  = [(5, 5)]
        s.treffer = {(5, 5)}
        assert s.versenkt is True

    def test_groesse_gespeichert(self):
        """Schiff speichert die übergebene Größe korrekt."""
        for g in FLOTTE:
            assert Schiff(g).groesse == g

    def test_felder_initial_leer(self):
        """Felder-Liste ist direkt nach Erstellung leer."""
        assert Schiff(4).felder == []

    def test_treffer_initial_leer(self):
        """Treffer-Set ist direkt nach Erstellung leer."""
        assert len(Schiff(4).treffer) == 0


# ═══════════════════════════════════════════════════════════════
#  Tests: Spielfeld – Platzierung
# ═══════════════════════════════════════════════════════════════

class TestSpielfeld_Platzierung:

    def test_platzieren_horizontal_erfolgreich(self):
        """Horizontale Platzierung in gültigem Bereich gelingt."""
        feld, schiff = feld_mit_schiff(3, 0, 0, horizontal=True)
        assert schiff.felder == [(0, 0), (1, 0), (2, 0)]

    def test_platzieren_vertikal_erfolgreich(self):
        """Vertikale Platzierung in gültigem Bereich gelingt."""
        feld, schiff = feld_mit_schiff(3, 0, 0, horizontal=False)
        assert schiff.felder == [(0, 0), (0, 1), (0, 2)]

    def test_platzieren_setzt_raster_auf_1(self):
        """Nach Platzierung stehen die betroffenen Raster-Zellen auf 1."""
        feld, _ = feld_mit_schiff(3, 2, 4, horizontal=True)
        assert feld.raster[4][2] == 1
        assert feld.raster[4][3] == 1
        assert feld.raster[4][4] == 1

    def test_platzieren_gibt_true_zurueck(self):
        """platzieren() gibt True zurück wenn die Platzierung erfolgreich war."""
        feld   = Spielfeld()
        schiff = Schiff(3)
        assert feld.platzieren(schiff, 0, 0, True) is True

    def test_platzieren_gibt_false_bei_out_of_bounds(self):
        """Platzierung außerhalb des Rasters schlägt fehl (False)."""
        feld   = Spielfeld()
        schiff = Schiff(3)
        # Schiff der Größe 3 an x=8 horizontal → würde bei x=10 enden (außerhalb)
        assert feld.platzieren(schiff, 8, 0, True) is False

    def test_platzieren_gibt_false_bei_overlap(self):
        """Platzierung auf bereits besetzter Zelle schlägt fehl."""
        feld   = Spielfeld()
        s1     = Schiff(3)
        s2     = Schiff(3)
        feld.platzieren(s1, 0, 0, True)   # Belegt (0,0), (1,0), (2,0)
        assert feld.platzieren(s2, 2, 0, True) is False   # (2,0) ist schon belegt

    def test_platzieren_fuegt_schiff_zu_liste(self):
        """Erfolgreich platziertes Schiff erscheint in feld.schiffe."""
        feld, schiff = feld_mit_schiff(4)
        assert schiff in feld.schiffe

    def test_kann_platzieren_am_rand(self):
        """Schiff das exakt an den Rand passt ist erlaubt."""
        feld = Spielfeld()
        # Größe 5 an x=5 → belegt (5,0)…(9,0), also genau am rechten Rand
        assert feld.kann_platzieren(5, 5, 0, True) is True

    def test_kann_platzieren_zu_gross_fuer_rand(self):
        """Schiff das über den Rand hinausragen würde ist nicht erlaubt."""
        feld = Spielfeld()
        # Größe 5 an x=6 → würde (6,0)…(10,0) belegen → x=10 existiert nicht
        assert feld.kann_platzieren(5, 6, 0, True) is False

    def test_kann_platzieren_vertikal_am_unteren_rand(self):
        """Vertikales Schiff das exakt bis zur letzten Zeile passt ist erlaubt."""
        feld = Spielfeld()
        assert feld.kann_platzieren(3, 0, 7, False) is True   # belegt y=7,8,9

    def test_kann_platzieren_vertikal_zu_gross(self):
        """Vertikales Schiff das über den unteren Rand hinausgeht ist nicht erlaubt."""
        feld = Spielfeld()
        assert feld.kann_platzieren(3, 0, 8, False) is False   # würde y=8,9,10 brauchen

    def test_raster_initial_nullen(self):
        """Leeres Spielfeld besteht ausschließlich aus Nullen."""
        feld = Spielfeld()
        for zeile in feld.raster:
            assert all(z == 0 for z in zeile)

    def test_schiff_nicht_plaztiert_bei_fehler(self):
        """Bei fehlgeschlagener Platzierung bleibt das Raster unverändert."""
        feld   = Spielfeld()
        schiff = Schiff(3)
        feld.platzieren(schiff, 9, 0, True)   # schlägt fehl (out of bounds)
        assert schiff not in feld.schiffe
        assert all(feld.raster[y][x] == 0 for y in range(10) for x in range(10))


# ═══════════════════════════════════════════════════════════════
#  Tests: Spielfeld – Schießen
# ═══════════════════════════════════════════════════════════════

class TestSpielfeld_Schiessen:

    def test_schuss_ins_wasser(self):
        """Schuss auf leere Zelle ergibt 'wasser'."""
        feld, _ = feld_mit_schiff(3, 5, 5)
        assert feld.schiessen(0, 0) == "wasser"

    def test_wasser_setzt_raster_auf_2(self):
        """Fehlschuss markiert die Zelle im Raster mit 2."""
        feld, _ = feld_mit_schiff(3, 5, 5)
        feld.schiessen(0, 0)
        assert feld.raster[0][0] == 2

    def test_treffer(self):
        """Schuss auf Schiff ohne Versenkung ergibt 'treffer'."""
        feld, _ = feld_mit_schiff(3, 0, 0)   # belegt (0,0),(1,0),(2,0)
        assert feld.schiessen(0, 0) == "treffer"

    def test_treffer_setzt_raster_auf_3(self):
        """Treffer markiert die Zelle im Raster mit 3."""
        feld, _ = feld_mit_schiff(3, 0, 0)
        feld.schiessen(1, 0)
        assert feld.raster[0][1] == 3

    def test_versenkt(self):
        """Letzter Treffer auf ein Schiff ergibt 'versenkt'."""
        feld, _ = feld_mit_schiff(3, 0, 0)
        feld.schiessen(0, 0)
        feld.schiessen(1, 0)
        assert feld.schiessen(2, 0) == "versenkt"

    def test_doppelter_schuss_ergibt_none(self):
        """Zweimaliger Schuss auf dieselbe Zelle ergibt None."""
        feld, _ = feld_mit_schiff(3, 5, 5)
        feld.schiessen(0, 0)           # erster Schuss: wasser
        assert feld.schiessen(0, 0) is None   # doppelter Schuss

    def test_doppelter_treffer_ergibt_none(self):
        """Zweimaliger Schuss auf getroffene Schiff-Zelle ergibt None."""
        feld, _ = feld_mit_schiff(3, 0, 0)
        feld.schiessen(0, 0)           # treffer
        assert feld.schiessen(0, 0) is None   # nochmal

    def test_schiff_treffer_setzt_treffer_set(self):
        """Nach einem Treffer steht die Zelle im treffer-Set des Schiffs."""
        feld, schiff = feld_mit_schiff(3, 0, 0)
        feld.schiessen(1, 0)
        assert (1, 0) in schiff.treffer

    def test_versenkt_setzt_schiff_versenkt(self):
        """Nach vollständigem Versenken ist schiff.versenkt True."""
        feld, schiff = feld_mit_schiff(2, 0, 0)
        feld.schiessen(0, 0)
        feld.schiessen(1, 0)
        assert schiff.versenkt is True


# ═══════════════════════════════════════════════════════════════
#  Tests: Spielfeld – Spielende
# ═══════════════════════════════════════════════════════════════

class TestSpielfeld_Spielende:

    def test_alle_versenkt_false_bei_aktivem_spiel(self):
        """alle_versenkt() ist False solange noch Schiffe aktiv sind."""
        feld, _ = feld_mit_schiff(3, 0, 0)
        assert feld.alle_versenkt() is False

    def test_alle_versenkt_true_nach_versenkung(self):
        """alle_versenkt() ist True nachdem das einzige Schiff versenkt wurde."""
        feld, _ = feld_mit_schiff(2, 0, 0)
        feld.schiessen(0, 0)
        feld.schiessen(1, 0)
        assert feld.alle_versenkt() is True

    def test_alle_versenkt_mit_mehreren_schiffen(self):
        """alle_versenkt() bleibt False solange ein Schiff noch aktiv ist."""
        feld   = Spielfeld()
        s1     = Schiff(2)
        s2     = Schiff(2)
        feld.platzieren(s1, 0, 0, True)   # (0,0),(1,0)
        feld.platzieren(s2, 0, 2, True)   # (0,2),(1,2)

        feld.schiessen(0, 0)
        feld.schiessen(1, 0)              # s1 versenkt

        assert feld.alle_versenkt() is False   # s2 lebt noch

        feld.schiessen(0, 2)
        feld.schiessen(1, 2)              # s2 versenkt

        assert feld.alle_versenkt() is True

    def test_leeres_feld_alle_versenkt(self):
        """Feld ohne Schiffe: alle_versenkt() gibt True (all() über leere Liste)."""
        feld = Spielfeld()
        assert feld.alle_versenkt() is True   # Python: all([]) == True


# ═══════════════════════════════════════════════════════════════
#  Tests: Spielfeld – Zufällige Besetzung
# ═══════════════════════════════════════════════════════════════

class TestSpielfeld_ZufaelligBesetzen:

    def test_alle_flotten_schiffe_platziert(self):
        """zufaellig_besetzen() platziert die gesamte FLOTTE (5 Schiffe)."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        assert len(feld.schiffe) == len(FLOTTE)

    def test_schiffe_haben_richtige_groessen(self):
        """Jedes platzierte Schiff hat die korrekte Größe aus der FLOTTE."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        groessen = sorted(s.groesse for s in feld.schiffe)
        assert groessen == sorted(FLOTTE)

    def test_keine_ueberlappungen(self):
        """Kein Rasterfeld wird von mehr als einem Schiff belegt."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        alle_felder = []
        for schiff in feld.schiffe:
            alle_felder.extend(schiff.felder)
        # Wenn es Duplikate gibt, ist das Set kleiner als die Liste
        assert len(alle_felder) == len(set(alle_felder))

    def test_alle_felder_im_raster(self):
        """Alle platzierten Felder liegen innerhalb des 10×10-Rasters."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        for schiff in feld.schiffe:
            for x, y in schiff.felder:
                assert 0 <= x < 10
                assert 0 <= y < 10

    def test_raster_konsistent_mit_schifffeldern(self):
        """Rastereinträge stimmen mit den felder-Listen der Schiffe überein."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        for schiff in feld.schiffe:
            for x, y in schiff.felder:
                assert feld.raster[y][x] == 1   # Zelle muss als Schiff markiert sein

    def test_schiffe_haben_felder_befuellt(self):
        """Jedes Schiff hat schiff.felder mit der richtigen Anzahl Einträgen."""
        feld = Spielfeld()
        feld.zufaellig_besetzen()
        for schiff in feld.schiffe:
            assert len(schiff.felder) == schiff.groesse


# ═══════════════════════════════════════════════════════════════
#  Tests: KI
# ═══════════════════════════════════════════════════════════════

class TestKI:

    def test_ki_hat_100_kandidaten(self):
        """Eine neue KI hat genau 100 Schuss-Kandidaten (alle Felder)."""
        ki = KI()
        assert len(ki.kandidaten) == 100

    def test_alle_koordinaten_vorhanden(self):
        """Die Kandidaten-Liste enthält jede (x, y)-Kombination genau einmal."""
        ki      = KI()
        erwartet = {(x, y) for x in range(10) for y in range(10)}
        assert set(ki.kandidaten) == erwartet

    def test_naechster_schuss_gibt_koordinate(self):
        """naechster_schuss() gibt ein gültiges (x, y)-Tupel zurück."""
        ki   = KI()
        x, y = ki.naechster_schuss()
        assert 0 <= x < 10
        assert 0 <= y < 10

    def test_naechster_schuss_reduziert_kandidaten(self):
        """naechster_schuss() entfernt die Koordinate aus der Liste."""
        ki = KI()
        ki.naechster_schuss()
        assert len(ki.kandidaten) == 99

    def test_keine_doppelten_schuesse(self):
        """KI schießt nie zweimal auf dasselbe Feld."""
        ki       = KI()
        geschossen = set()
        for _ in range(100):
            koord = ki.naechster_schuss()
            assert koord not in geschossen
            geschossen.add(koord)

    def test_ki_deckt_alle_felder_ab(self):
        """KI schießt in 100 Zügen auf alle 100 Felder genau einmal."""
        ki       = KI()
        geschossen = set()
        for _ in range(100):
            geschossen.add(ki.naechster_schuss())
        erwartet = {(x, y) for x in range(10) for y in range(10)}
        assert geschossen == erwartet

    def test_ki_liste_leer_nach_100_schuessen(self):
        """Nach 100 Schüssen ist die Kandidaten-Liste leer."""
        ki = KI()
        for _ in range(100):
            ki.naechster_schuss()
        assert ki.kandidaten == []


# ═══════════════════════════════════════════════════════════════
#  Integrations-Tests: vollständiges Spiel simulieren
# ═══════════════════════════════════════════════════════════════

class TestIntegration:

    def test_ki_gewinnt_simulation(self):
        """
        Simuliert ein vollständiges PvE-Spiel bei dem die KI gewinnt.
        Alle KI-Schüsse werden sofort abgefeuert bis alle Spieler-Schiffe versenkt sind.
        """
        spieler_feld = Spielfeld()
        spieler_feld.zufaellig_besetzen()

        ki = KI()
        schuesse = 0

        while not spieler_feld.alle_versenkt():
            x, y = ki.naechster_schuss()
            ergebnis = spieler_feld.schiessen(x, y)
            assert ergebnis is not None   # KI schießt nie auf ein beschossenes Feld
            schuesse += 1

        # Ein vollständiges Spiel braucht mindestens 17 Schüsse (Summe der Schiffsgrößen)
        # und höchstens 100 Schüsse (alle Felder)
        assert 17 <= schuesse <= 100

    def test_spieler_gewinnt_simulation(self):
        """
        Simuliert ein vollständiges Spiel bei dem der Spieler alle KI-Schiffe versenkt.
        """
        ki_feld = Spielfeld()
        ki_feld.zufaellig_besetzen()

        # Spieler schießt auf alle Felder der Reihe nach
        schuesse = 0
        for y in range(10):
            for x in range(10):
                if ki_feld.alle_versenkt():
                    break
                ki_feld.schiessen(x, y)
                schuesse += 1

        assert ki_feld.alle_versenkt() is True

    def test_keine_doppelten_raster_schuss(self):
        """
        Stellt sicher, dass Doppelschüsse auf demselben Feld korrekt None zurückgeben.
        """
        feld, _ = feld_mit_schiff(3, 0, 0)
        feld.schiessen(5, 5)           # Fehlschuss
        feld.schiessen(5, 5)           # Doppelschuss → None
        assert feld.raster[5][5] == 2  # Zustand bleibt 2 (wasser), nicht überschrieben

    def test_treffer_dann_versenkt_dann_alle_versenkt(self):
        """
        Vollständiger Ablauf: Treffer → Treffer → Versenkt → alle_versenkt().
        """
        feld   = Spielfeld()
        schiff = Schiff(2)
        feld.platzieren(schiff, 3, 3, True)   # (3,3),(4,3)

        assert feld.schiessen(3, 3) == "treffer"
        assert feld.alle_versenkt() is False
        assert feld.schiessen(4, 3) == "versenkt"
        assert feld.alle_versenkt() is True
