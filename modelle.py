"""
modelle.py – Spiellogik für Schiffe Versenken
==============================================
Dieses Modul enthält ausschließlich die Datenstrukturen und Spielregeln.
Kein pygame, kein Rendering – nur reine Logik.

Klassen:
    Schiff      – ein einzelnes Schiff mit Positionen und Trefferzustand
    Spielfeld   – das 10×10-Raster eines Spielers mit allen Methoden
    KI          – einfacher Random-Shooter-Algorithmus

Konstanten:
    FLOTTE        – Größen der Schiffe in der klassischen Battleship-Flotte
    SCHIFF_NAMEN  – Anzeigename je Schiffsgröße
"""

import random

# Klassische Battleship-Flotte: 1× Größe 5, 1× Größe 4, 2× Größe 3, 1× Größe 2
FLOTTE = [5, 4, 3, 3, 2]

# Anzeigenamen für die Schiffsgrößen (wird im UI verwendet)
SCHIFF_NAMEN = {5: "Schlachtschiff", 4: "Kreuzer", 3: "Zerstörer", 2: "U-Boot"}


# ─────────────────────────────────────────────────────────────────────────────

class Schiff:
    """
    Repräsentiert ein einzelnes Schiff auf dem Spielfeld.

    Attribute:
        groesse  – Anzahl der Felder, die das Schiff belegt
        felder   – Liste der belegten Zellen als (x, y)-Tupel,
                   wird beim Platzieren befüllt
        treffer  – Set der bereits getroffenen Zellen als (x, y)-Tupel
    """

    def __init__(self, groesse):
        self.groesse = groesse
        self.felder  = []       # Wird in Spielfeld.platzieren() befüllt
        self.treffer = set()    # Set statt Liste → schnelles Membership-Check

    @property
    def versenkt(self):
        """True wenn alle Felder des Schiffs getroffen wurden."""
        return len(self.treffer) == self.groesse


# ─────────────────────────────────────────────────────────────────────────────

class Spielfeld:
    """
    Das 10×10-Spielfeld eines Spielers.

    Das Raster speichert für jede Zelle einen Zahlenwert:
        0 = Wasser (unberührt)
        1 = Schiff (platziert, noch nicht beschossen)
        2 = Fehlschuss (Wasser getroffen)
        3 = Treffer (Schiff getroffen)

    Attribute:
        raster   – 2D-Liste [y][x] mit den Zellzuständen (0–3)
        schiffe  – Liste aller auf diesem Feld platzierten Schiff-Objekte
    """

    def __init__(self):
        # Outer list = Zeilen (y), Inner list = Spalten (x)
        # Zugriff: self.raster[y][x]
        self.raster  = [[0] * 10 for _ in range(10)]
        self.schiffe = []

    def kann_platzieren(self, groesse, x, y, horizontal):
        """
        Prüft ob ein Schiff der gegebenen Größe an Position (x,y) platzierbar ist,
        ohne das Raster zu verlassen oder ein anderes Schiff zu überlappen.

        Args:
            groesse     – Anzahl der Felder des Schiffs
            x, y        – Startposition (obere-linke Ecke des Schiffs)
            horizontal  – True = waagerecht, False = senkrecht

        Returns:
            True wenn die Platzierung gültig wäre, sonst False
        """
        for i in range(groesse):
            # Je nach Ausrichtung entweder x oder y erhöhen
            fx = x + (i if horizontal else 0)
            fy = y + (0 if horizontal else i)

            # Außerhalb des Rasters?
            if not (0 <= fx < 10 and 0 <= fy < 10):
                return False

            # Bereits von einem anderen Schiff belegt?
            if self.raster[fy][fx] == 1:
                return False

        return True

    def platzieren(self, schiff, x, y, horizontal):
        """
        Platziert ein Schiff auf dem Raster, falls die Position gültig ist.

        Schreibt in das Raster (Wert 1) und befüllt schiff.felder
        mit den Koordinaten der belegten Zellen.

        Returns:
            True bei Erfolg, False wenn die Position ungültig war
        """
        if not self.kann_platzieren(schiff.groesse, x, y, horizontal):
            return False

        for i in range(schiff.groesse):
            fx = x + (i if horizontal else 0)
            fy = y + (0 if horizontal else i)
            schiff.felder.append((fx, fy))
            self.raster[fy][fx] = 1     # Zelle als "Schiff" markieren

        self.schiffe.append(schiff)
        return True

    def schiessen(self, x, y):
        """
        Verarbeitet einen Schuss auf die Zelle (x, y).

        Returns:
            None       – diese Zelle wurde schon beschossen (ungültiger Zug)
            "wasser"   – kein Schiff getroffen
            "treffer"  – Schiff getroffen, aber noch nicht versenkt
            "versenkt" – Schiff getroffen und vollständig versenkt
        """
        # Doppelter Schuss auf dieselbe Zelle wird ignoriert
        if self.raster[y][x] in (2, 3):
            return None

        # Prüfen ob eine der Schiffskoordinaten getroffen wurde
        for schiff in self.schiffe:
            if (x, y) in schiff.felder:
                schiff.treffer.add((x, y))
                self.raster[y][x] = 3   # Treffer im Raster markieren
                return "versenkt" if schiff.versenkt else "treffer"

        # Kein Schiff getroffen → Fehlschuss
        self.raster[y][x] = 2
        return "wasser"

    def alle_versenkt(self):
        """True wenn alle Schiffe auf diesem Feld versenkt wurden (= Spielende)."""
        return all(s.versenkt for s in self.schiffe)

    def zufaellig_besetzen(self):
        """
        Platziert die gesamte FLOTTE zufällig auf dem Raster.
        Wird für die KI verwendet, damit man nicht manuell Schiffe setzen muss.
        Versucht immer wieder zufällige Positionen bis eine passt.
        """
        for groesse in FLOTTE:
            while True:
                schiff     = Schiff(groesse)
                x          = random.randint(0, 9)
                y          = random.randint(0, 9)
                horizontal = random.choice([True, False])
                if self.platzieren(schiff, x, y, horizontal):
                    break   # Platzierung erfolgreich → nächstes Schiff


# ─────────────────────────────────────────────────────────────────────────────

class KI:
    """
    Einfacher KI-Algorithmus (Stufe 1: Random Shooter).

    Schießt auf alle 100 Felder des Rasters in zufälliger Reihenfolge,
    ohne ein Feld doppelt zu beschießen.

    Funktionsweise:
        Beim Erstellen wird eine Liste aller (x,y)-Koordinaten gemischt.
        naechster_schuss() gibt immer die nächste Koordinate zurück (pop von hinten).

    Hinweis für Erweiterungen:
        Für einen schlaueren Algorithmus (Hunt & Target, Wahrscheinlichkeitskarte)
        würde man hier die Logik ergänzen, z.B. nach einem Treffer die
        Nachbarfelder bevorzugen.
    """

    def __init__(self):
        alle = [(x, y) for x in range(10) for y in range(10)]
        random.shuffle(alle)
        self.kandidaten = alle  # Noch nicht beschossene Felder (gemischt)

    def naechster_schuss(self):
        """Gibt die nächste Zielkoordinate zurück und entfernt sie aus der Liste."""
        return self.kandidaten.pop()
