"""
main.py – pygame-Oberfläche für Schiffe Versenken
==================================================
Dieses Modul steuert alles was der Spieler sieht und mit ihm interagiert:
  - Fensterverwaltung (Größe, Vollbild, dynamisches Layout)
  - Spielzustand (State Machine mit 6 Zuständen)
  - Eingabeverarbeitung (Maus, Tastatur)
  - Rendering aller Screens

Ablauf:
    Beim Start liest pygame die Bildschirmgröße aus und öffnet ein Fenster
    mit 85% der nativen Auflösung. Alle Layout-Maße (Zellgröße, Ränder,
    Schriften) werden dynamisch berechnet und passen sich beim Größenändern
    automatisch an. F11 schaltet Vollbild um.

Spielzustände (State Machine):
    MENUE          → Startbildschirm, Moduswahl
    SCHIFFE_SETZEN → Spieler platziert seine Schiffe per Klick
    WECHSEL        → Übergangsscreen zwischen Spielern ("Bitte übernehmen")
    SPIELEN        → Aktiver Spieler schießt auf das Gegnergitter
    KI_DRAN        → KI-Zug mit animierter Verzögerung (nur PvE)
    GAME_OVER      → Spielende, Sieger wird angezeigt

Abhängigkeiten:
    modelle.py – Spielfeld, Schiff, KI (reine Logik, kein pygame)
"""

import pygame
import sys
from modelle import Spielfeld, Schiff, KI, FLOTTE, SCHIFF_NAMEN


# ═══════════════════════════════════════════════════════════════
#  Initialisierung
# ═══════════════════════════════════════════════════════════════

pygame.init()

# Native Bildschirmgröße auslesen – wird für Vollbild-Umschalten gebraucht
_info    = pygame.display.Info()
SCREEN_W = _info.current_w
SCREEN_H = _info.current_h

# Fenstermodus: 85% der nativen Auflösung, freie Größenänderung per Ziehen
vollbild = False
screen   = pygame.display.set_mode(
    (int(SCREEN_W * 0.85), int(SCREEN_H * 0.85)),
    pygame.RESIZABLE
)
pygame.display.set_caption("Schiffe Versenken")
clock = pygame.time.Clock()


# ═══════════════════════════════════════════════════════════════
#  Dynamisches Layout
# ═══════════════════════════════════════════════════════════════

# Diese globalen Variablen werden von layout_aktualisieren() gesetzt.
# Sie sind global, damit alle Zeichenfunktionen immer auf den
# aktuellen Stand zugreifen können ohne Parameter weiterzureichen.
ZELL   = 44    # Pixelgröße einer einzelnen Grid-Zelle (Quadrat)
RAND_L = 52    # Linker Rand: Abstand vom Fensterrand bis zum Grid
RAND_O = 52    # Oberer Rand: Abstand vom Fensterrand bis zum Grid
PANEL  = 245   # Breite des rechten Infopanels in Pixeln
BREITE = 0     # Aktuelle Fensterbreite (wird sofort durch layout_aktualisieren gesetzt)
HOEHE  = 0     # Aktuelle Fensterhöhe
font_L = None  # Großschrift (Titel, Gewinnermeldung)
font_M = None  # Mittelschrift (Panel-Text, Buttons)
font_S = None  # Kleinschrift (Achsenbeschriftungen A–J, 1–10)


def layout_aktualisieren():
    """
    Berechnet alle Layout-Größen neu, passend zur aktuellen Fenstergröße.

    Wird aufgerufen:
      - Einmal beim Start
      - Nach Vollbild-Umschalten
      - Jedes Frame wenn das Fenster gezogen/vergrößert wurde

    Fensteraufteilung:
        |<─── Spielfläche (links, ~75%) ───>|<─── Panel (rechts, ~25%) ───>|
        |   [Rand]  [  10×10 GRID  ]  [Rand] |  Info-Text                   |

    Das Grid wird in der Spielfläche horizontal UND vertikal zentriert,
    d.h. Rand links = Rand rechts und Rand oben = Rand unten.
    """
    global ZELL, RAND_L, RAND_O, PANEL, BREITE, HOEHE, font_L, font_M, font_S

    BREITE, HOEHE = screen.get_size()

    # Mindestrand: brauchen wir für Achsenbeschriftungen (A–J, 1–10)
    # und die Headerzeile über dem Grid im KI-Zug-Screen
    RAND_MIN = 48

    # ── Panel (rechte Seite) ──────────────────────────────────
    # ~25% der Fensterbreite, aber mindestens 200px damit Text lesbar bleibt
    PANEL = max(200, int(BREITE * 0.25))

    # ── Spielfläche (linke Seite) ─────────────────────────────
    spielflaeche_b = BREITE - PANEL

    # ── Zellgröße berechnen ───────────────────────────────────
    # Wir wollen das Grid so groß wie möglich machen, aber:
    #   - horizontal: muss in die Spielfläche passen (mit je RAND_MIN Abstand links und rechts)
    #   - vertikal:   muss ins Fenster passen (mit je RAND_MIN Abstand oben und unten)
    # min() stellt sicher, dass beide Bedingungen gleichzeitig erfüllt sind.
    zell_b = (spielflaeche_b - 2 * RAND_MIN) / 10
    zell_h = (HOEHE          - 2 * RAND_MIN) / 10
    ZELL = max(22, int(min(zell_b, zell_h)))   # mindestens 22px damit Cells sichtbar bleiben

    # ── Grid zentrieren ───────────────────────────────────────
    # Durch ganzzahlige Division ergibt sich auf beiden Seiten der gleiche Abstand.
    RAND_L = (spielflaeche_b - 10 * ZELL) // 2        # horizontal in Spielfläche
    RAND_O = max(RAND_MIN, (HOEHE - 10 * ZELL) // 2)  # vertikal im Fenster

    # ── Schriften ─────────────────────────────────────────────
    # Proportional zur Zellgröße, damit Text auf jedem Bildschirm gut lesbar ist.
    # skala=1.0 entspricht ZELL=44px (Referenz für ~1400×900 Fenster).
    # min/max-Grenzen verhindern zu kleine oder zu riesige Schriften.
    skala = ZELL / 44
    font_L = pygame.font.SysFont("monospace", int(max(18, min(42, 26 * skala))), bold=True)
    font_M = pygame.font.SysFont("monospace", int(max(13, min(28, 17 * skala))))
    font_S = pygame.font.SysFont("monospace", int(max(11, min(22, 14 * skala))))
  
    _textur_cache.clear()  # Cache leeren wenn Fenstergröße sich ändert


# Texturen laden
wasser_textur = pygame.image.load("Modelle,Texturen/Wasser.png").convert()

# Texturen der Schiffsklassen (Größe 2, 3, 4, 5)
schiff_texturen = {
    2: pygame.image.load("Modelle,Texturen/Patrol Boat.png").convert_alpha(),
    3: pygame.image.load("Modelle,Texturen/Destroyer.png").convert_alpha(),
    4: pygame.image.load("Modelle,Texturen/Cruiser.png").convert_alpha(),
    5: pygame.image.load("Modelle,Texturen/Battleship.png").convert_alpha(),
}
explosion_textur = pygame.image.load("Modelle,Texturen/Explosion.png").convert_alpha()
splash_textur    = pygame.image.load("Modelle,Texturen/Splash.png").convert_alpha()

_textur_cache = {}

def skalierte_textur(textur, breite, hoehe):
    # Skaliert eine Textur nur wenn nötig, sonst aus Cache. (Spart Rechenleistung)
    key = (id(textur), breite, hoehe)
    if key not in _textur_cache:
        _textur_cache[key] = pygame.transform.scale(textur, (breite, hoehe))
    return _textur_cache[key]



def toggle_vollbild():
    """
    Schaltet zwischen Vollbild und Fenstermodus um.
    Nach dem Umschalten wird das Layout neu berechnet.
    """
    global vollbild, screen
    vollbild = not vollbild
    if vollbild:
        # (0, 0) bedeutet: native Bildschirmauflösung verwenden
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        # Zurück zum 85%-Fenster mit freier Größenänderung
        screen = pygame.display.set_mode(
            (int(SCREEN_W * 0.85), int(SCREEN_H * 0.85)),
            pygame.RESIZABLE
        )
    layout_aktualisieren()


# Layout einmal beim Start berechnen
layout_aktualisieren()


# ═══════════════════════════════════════════════════════════════
#  Farben (RGB-Tupel)
# ═══════════════════════════════════════════════════════════════

BG        = (15,  25,  40)   # Hintergrunddunkelblau
PANEL_BG  = (22,  38,  58)   # Leicht helleres Blau für das Panel
WASSER_C  = (28,  95, 175)   # Blau – leere / unbekannte Zelle
SCHIFF_C  = (68,  72,  82)   # Dunkelgrau – eigenes Schiff (sichtbar beim Platzieren)
TREFFER_C = (210, 55,  50)   # Rot – Schiff wurde getroffen
MISS_C    = (148, 182, 208)  # Hellblau – Fehlschuss (Wasser)
GITTER_C  = (20,  62, 125)   # Dunkelblau – Gitterlinien und Trennlinien
WEISS     = (225, 235, 245)  # Fast-Weiß – normaler Text
GELB      = (248, 198,  48)  # Gelb – Überschriften, aktive Elemente
GRUEN     = (68,  158,  78)  # Grün – positive Anzeige (Schiffe noch aktiv)
ROT       = (198,  58,  52)  # Rot – negative Anzeige (versenkt, Alarm)
GRAU      = (100, 110, 120)  # Grau – deaktivierte / Hinweis-Texte
ORANGE    = (240, 140,  40)  # Orange – KI-Treffer-Hervorhebung


# ═══════════════════════════════════════════════════════════════
#  Spielzustände (State Machine)
# ═══════════════════════════════════════════════════════════════
# Das Spiel befindet sich immer in genau einem dieser Zustände.
# Jeder Zustand hat seine eigene Render-Funktion und seinen eigenen
# Input-Handler in der Hauptschleife.

MENUE          = "menue"           # Startscreen mit Moduswahl
SCHIFFE_SETZEN = "schiffe_setzen"  # Schiffe per Klick auf Grid platzieren
WECHSEL        = "wechsel"         # Übergangsscreen ("Spieler X übernehmen")
SPIELEN        = "spielen"         # Aktiver Spieler schießt
KI_DRAN        = "ki_dran"         # KI führt ihren Zug mit Verzögerung aus
GAME_OVER      = "game_over"       # Spielende, Sieger anzeigen

# Wartezeiten für den animierten KI-Zug (in Millisekunden)
KI_WARTE_MS = 800   # Pause bevor die KI schießt ("denkt nach")
KI_ZEIGE_MS = 700   # Pause nach dem Schuss bevor das Spiel weitergeht


# ═══════════════════════════════════════════════════════════════
#  Spiellogik (Zustandsverwaltung)
# ═══════════════════════════════════════════════════════════════

class Spiel:
    """
    Verwaltet den gesamten Spielzustand und die Übergänge zwischen Zuständen.

    Wichtigste Attribute:
        modus            – "pve" (gegen KI) oder "pvp" (zwei Spieler lokal)
        felder           – Liste mit zwei Spielfeld-Objekten: [Spieler1, Spieler2/KI]
        aktiver          – Index des aktuell schießenden Spielers (0 oder 1)
        zustand          – aktueller Spielzustand (eine der STATE-Konstanten)
        ki               – KI-Objekt (nur im PvE-Modus gesetzt)

    Zur State Machine:
        Zustandsübergänge passieren immer innerhalb dieser Klasse,
        nie direkt von außen. Die Render- und Input-Funktionen lesen
        nur den Zustand, ändern ihn aber nicht selbst.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Setzt alles auf den Ausgangszustand zurück.
        Wird beim Start und nach "Nochmal spielen" aufgerufen.
        """
        self.modus            = None              # Wird in starte() gesetzt
        self.felder           = [Spielfeld(), Spielfeld()]  # [Spieler1, Spieler2/KI]
        self.aktiver          = 0                 # Spieler 1 beginnt immer
        self.setup_spieler    = 0                 # Welcher Spieler gerade Schiffe setzt
        self.schiff_idx       = 0                 # Index in FLOTTE: welches Schiff kommt als nächstes
        self.horizontal       = True              # Ausrichtung beim Platzieren (R zum Drehen)
        self.ki               = None              # KI-Objekt, nur im PvE-Modus
        self.zustand          = MENUE
        self.wechsel_text     = ""                # Nachricht auf dem Wechsel-Screen
        self.wechsel_next     = ""                # Was nach Bestätigung passiert ("setup2", "zug", "start")
        self.letztes_ergebnis = ""                # "wasser" / "treffer" / "versenkt" / "KI: ..."
        self.gewinner         = None              # Index des Gewinners (0 oder 1)
        # KI-Zug Animation:
        self.ki_wartet        = True              # True = wartet auf Schuss, False = zeigt Ergebnis
        self.ki_naechste_zeit = 0                 # pygame-Tick ab dem der nächste Schritt passiert
        self.ki_schuss_xy     = None              # (x, y) des letzten KI-Schusses (für Highlight)
        self.ki_game_over     = False             # True wenn KI mit dem Schuss gewonnen hat

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def setup_feld(self):
        """Spielfeld des Spielers, der gerade Schiffe setzt."""
        return self.felder[self.setup_spieler]

    def angriffs_feld(self):
        """Spielfeld des Gegners – das Ziel beim Schießen."""
        return self.felder[1 - self.aktiver]

    def eigenes_feld(self):
        """Spielfeld des aktiven Spielers – die eigenen Schiffe."""
        return self.felder[self.aktiver]

    def spieler_name(self, idx=None):
        """
        Gibt den Anzeigenamen für Spieler idx zurück.
        Im PvE-Modus heißt Spieler 1 (idx=1) einfach "KI".
        Ohne Argument wird der aktive Spieler verwendet.
        """
        i = self.aktiver if idx is None else idx
        if self.modus == "pve" and i == 1:
            return "KI"
        return f"Spieler {i + 1}"

    # ── Setup-Phase ───────────────────────────────────────────────────────────

    def starte(self, modus):
        """
        Startet eine neue Partie im gewählten Modus.
        Wechselt direkt in den Schiffe-Setzen-Zustand für Spieler 1.
        """
        self.modus         = modus
        self.setup_spieler = 0
        self.schiff_idx    = 0
        self.horizontal    = True
        self.zustand       = SCHIFFE_SETZEN

    def platziere_schiff(self, x, y):
        """
        Versucht das nächste Schiff aus der FLOTTE auf (x, y) zu platzieren.
        Wird bei Mausklick auf das Grid aufgerufen.
        Bei Erfolg wird schiff_idx erhöht. Wenn alle Schiffe gesetzt sind,
        wird _setup_done() aufgerufen.
        """
        schiff = Schiff(FLOTTE[self.schiff_idx])
        if self.setup_feld().platzieren(schiff, x, y, self.horizontal):
            self.schiff_idx += 1
            if self.schiff_idx >= len(FLOTTE):
                self._setup_done()

    def _setup_done(self):
        """
        Alle Schiffe eines Spielers wurden platziert.

        PvP: Nach Spieler 1 kommt Spieler 2 (mit Wechsel-Screen dazwischen).
        PvE: Nur Spieler 1 setzt Schiffe, dann startet das Spiel direkt.
        """
        if self.modus == "pvp" and self.setup_spieler == 0:
            # Spieler 2 muss noch Schiffe setzen – zuerst Augen-zu-Screen
            self._zeige_wechsel(
                "Spieler 1 hat seine Schiffe gesetzt.\n\n"
                "Spieler 2, bitte übernehmen.\n\n"
                "[Enter] drücken",
                naechstes="setup2"
            )
        else:
            self._starte_spiel()

    def _starte_spiel(self):
        """
        Beide Spieler haben ihre Schiffe gesetzt – das Spiel beginnt.

        Im PvE-Modus: KI-Objekt erstellen und KI-Spielfeld zufällig besetzen.
        Im PvP-Modus: Wechsel-Screen für den ersten Zug anzeigen.
        """
        if self.modus == "pve":
            self.ki = KI()
            self.felder[1].zufaellig_besetzen()   # KI-Schiffe unsichtbar platzieren
        self.aktiver = 0
        self.letztes_ergebnis = ""
        if self.modus == "pvp":
            # Kurze Bestätigung damit Spieler 1 bereit ist
            self._zeige_wechsel(
                "Beide Spieler sind bereit.\n\n"
                "Spieler 1, du beginnst.\n\n"
                "[Enter] drücken",
                naechstes="start"
            )
        else:
            self.zustand = SPIELEN

    # ── Spielphase ────────────────────────────────────────────────────────────

    def schiesse(self, x, y):
        """
        Aktiver Spieler schießt auf Zelle (x, y) des Gegners.

        Spielregel: Bei Treffer darf nochmal geschossen werden.
        Bei Fehlschuss wird _wechseln() aufgerufen.
        Wenn alle gegnerischen Schiffe versenkt sind → GAME_OVER.
        """
        ergebnis = self.angriffs_feld().schiessen(x, y)
        if ergebnis is None:
            return  # Bereits beschossene Zelle → ignorieren

        self.letztes_ergebnis = ergebnis

        if self.angriffs_feld().alle_versenkt():
            self.gewinner = self.aktiver
            self.zustand  = GAME_OVER
            return

        if ergebnis == "wasser":
            self._wechseln()
        # Bei "treffer" oder "versenkt": gleicher Spieler darf nochmal schießen

    def _wechseln(self):
        """
        Spieler hat verfehlt → Wechsel zum Gegner.

        PvP: Zeigt Wechsel-Screen damit der andere Spieler übernehmen kann.
        PvE: Startet den animierten KI-Zug direkt.
        """
        if self.modus == "pvp":
            naechster = 1 - self.aktiver
            self._zeige_wechsel(
                f"{self.spieler_name(naechster)}, du bist dran.\n\n"
                "Bitte übernehmen.\n\n"
                "[Enter] drücken",
                naechstes="zug"
            )
        else:
            self._starte_ki_zug()

    def _starte_ki_zug(self):
        """
        Initiiert den KI-Zug und wechselt in den KI_DRAN-Zustand.
        Die eigentliche Logik läuft dann frame-basiert in ki_schritt().
        """
        self.ki_schuss_xy     = None
        self.ki_wartet        = True   # Phase 1: Wartezeit ("denkt nach")
        self.ki_game_over     = False
        self.ki_naechste_zeit = pygame.time.get_ticks() + KI_WARTE_MS
        self.zustand          = KI_DRAN

    def ki_schritt(self, jetzt):
        """
        Führt den KI-Zug schrittweise mit Verzögerung aus.
        Wird jeden Frame aufgerufen wenn zustand == KI_DRAN.

        Der KI-Zug hat zwei Phasen:
            Phase 1 (ki_wartet=True):
                KI "denkt nach" für KI_WARTE_MS Millisekunden.
                Danach: Schuss ausführen, Ergebnis speichern.

            Phase 2 (ki_wartet=False):
                Ergebnis für KI_ZEIGE_MS Millisekunden anzeigen.
                Danach je nach Ergebnis:
                  - Wasser  → Spieler ist wieder dran (zurück zu SPIELEN)
                  - Treffer → KI schießt nochmal (zurück zu Phase 1)
                  - Versenkt + alle weg → GAME_OVER
        """
        if jetzt < self.ki_naechste_zeit:
            return   # Noch nicht an der Reihe

        if self.ki_wartet:
            # ── Phase 1: Schuss ausführen ──────────────────────────────
            # Kandidaten-Liste hat alle noch nicht beschossenen Felder.
            # Schleife als Sicherheitsnetz falls schiessen() None zurückgibt.
            while self.ki.kandidaten:
                x, y     = self.ki.naechster_schuss()
                ergebnis = self.felder[0].schiessen(x, y)   # KI schießt auf Spieler-1-Feld
                if ergebnis is not None:
                    break
            else:
                return   # Keine Kandidaten mehr (Sicherheitsfall, sollte nie eintreten)

            self.ki_schuss_xy     = (x, y)
            self.letztes_ergebnis = f"KI: {ergebnis}"
            self.ki_wartet        = False                           # Wechsel zu Phase 2
            self.ki_naechste_zeit = jetzt + KI_ZEIGE_MS
            self.ki_game_over     = self.felder[0].alle_versenkt()  # Hat KI gewonnen?

        else:
            # ── Phase 2: Ergebnis auswerten, nächster Schritt ──────────
            if self.ki_game_over:
                self.gewinner = 1        # KI gewinnt (index 1 = KI)
                self.zustand  = GAME_OVER
            elif "wasser" in self.letztes_ergebnis:
                # KI hat verfehlt → Spieler 1 ist wieder dran
                self.ki_schuss_xy     = None
                self.letztes_ergebnis = ""
                self.zustand          = SPIELEN
            else:
                # KI hat getroffen → nochmal schießen (zurück zu Phase 1)
                self.ki_wartet        = True
                self.ki_schuss_xy     = None
                self.ki_naechste_zeit = jetzt + KI_WARTE_MS

    def _zeige_wechsel(self, text, naechstes):
        """
        Wechselt in den WECHSEL-Zustand und speichert den anzuzeigenden Text
        sowie was nach Drücken von Enter passiert.
        """
        self.wechsel_text = text
        self.wechsel_next = naechstes
        self.zustand      = WECHSEL

    def wechsel_confirm(self):
        """
        Spieler hat auf dem Wechsel-Screen Enter gedrückt.
        Führt je nach wechsel_next die passende Aktion aus:
            "setup2" → Spieler 2 setzt jetzt Schiffe
            "start"  → Spiel beginnt (nach beiden Setzen im PvP)
            "zug"    → Nächster Spieler ist dran (PvP-Runde)
        """
        if self.wechsel_next == "setup2":
            # Spieler 2 beginnt mit Schiffe setzen
            self.setup_spieler = 1
            self.schiff_idx    = 0
            self.horizontal    = True
            self.zustand       = SCHIFFE_SETZEN
        elif self.wechsel_next in ("start", "zug"):
            if self.wechsel_next == "zug":
                # Spielerwechsel: 0→1 oder 1→0
                self.aktiver = 1 - self.aktiver
            self.letztes_ergebnis = ""
            self.zustand = SPIELEN


# ═══════════════════════════════════════════════════════════════
#  Globales Spiel-Objekt
# ═══════════════════════════════════════════════════════════════

spiel = Spiel()


# ═══════════════════════════════════════════════════════════════
#  Hilfsfunktionen für das Rendering
# ═══════════════════════════════════════════════════════════════

def zelle_px(gx, gy):
    """
    Rechnet Grid-Koordinaten (gx, gy) in Pixel-Koordinaten um.
    Gibt die obere linke Ecke der Zelle zurück.
    """
    return RAND_L + gx * ZELL, RAND_O + gy * ZELL

def maus_zu_zelle(px, py):
    """
    Rechnet Pixel-Koordinaten in Grid-Koordinaten um.
    Gibt (gx, gy) zurück oder None wenn die Maus außerhalb des Grids ist.
    """
    gx = (px - RAND_L) // ZELL
    gy = (py - RAND_O) // ZELL
    if 0 <= gx < 10 and 0 <= gy < 10:
        return gx, gy
    return None

def koordinate(x, y):
    """Wandelt Grid-Koordinaten in lesbare Form um, z.B. (2, 4) → 'C5'."""
    return f"{'ABCDEFGHIJ'[x]}{y + 1}"


# ═══════════════════════════════════════════════════════════════
#  Kern-Zeichenfunktionen
# ═══════════════════════════════════════════════════════════════

def _zeichne_schiff(schiff):
    """
    Zeichnet ein Schiff als einzelnes Bild über alle seine Zellen.
    Erkennt Ausrichtung automatisch anhand der gespeicherten Felder.
    """
    if not schiff.felder:
        return

    textur = schiff_texturen.get(schiff.groesse)
    if textur is None:
        return

    # Erstes Feld = obere linke Ecke des Schiffs
    felder_sorted = sorted(schiff.felder)
    gx0, gy0 = felder_sorted[0]
    px, py   = zelle_px(gx0, gy0)

    # Ausrichtung: wenn x sich ändert → horizontal, sonst vertikal
    horizontal = len({f[0] for f in schiff.felder}) > 1

    if horizontal:
        breite = schiff.groesse * ZELL - 1
        hoehe  = ZELL - 1
        t = skalierte_textur(textur, breite, hoehe)
    else:
        # Textur drehen: original horizontal → 90° drehen für vertikal
        breite = ZELL - 1
        hoehe  = schiff.groesse * ZELL - 1
        basis  = skalierte_textur(textur, hoehe, breite)  # erst breit skalieren
        key    = (id(textur), breite, hoehe, "rot")
        if key not in _textur_cache:
            _textur_cache[key] = pygame.transform.rotate(basis, -90)
        t = _textur_cache[key]

    screen.blit(t, (px, py))



def zeichne_raster(feld, verdeckt=False, vorschau=None, vorschau_ok=True, highlight=None):

    grid_b = 10 * ZELL
    grid_h = 10 * ZELL

    # ── Wasser als Hintergrundbild (ganzes Grid) ────────────────
    wasser = skalierte_textur(wasser_textur, grid_b, grid_h)
    screen.blit(wasser, (RAND_L, RAND_O))

    # ── Schiffe zeichnen (pro Schiff, über mehrere Zellen) ──────
    if not verdeckt:
        for schiff in feld.schiffe:
            _zeichne_schiff(schiff)

    # ── Treffer und Fehlschuss-Overlays ─────────────────────────
    for gy in range(10):
        for gx in range(10):
            px, py = zelle_px(gx, gy)
            z = feld.raster[gy][gx]

            if z == 2:
                # Fehlschuss – Wasserplatscher overlay
                overlay = skalierte_textur(splash_textur, ZELL - 1, ZELL - 1)
                screen.blit(overlay, (px, py))
            elif z == 3:
                # Treffer – Explosion overlay
                overlay = skalierte_textur(explosion_textur, ZELL - 1, ZELL - 1)
                screen.blit(overlay, (px, py))

    # ── Versenkte Schiffe auf dem Angriffsgitter aufdecken ──────
    if verdeckt:
        for schiff in feld.schiffe:
            if schiff.versenkt:
                _zeichne_schiff(schiff)
                # Explosions-Overlay auf alle Felder des versenkten Schiffs
                for (gx, gy) in schiff.felder:
                    px, py = zelle_px(gx, gy)
                    overlay = skalierte_textur(explosion_textur, ZELL - 1, ZELL - 1)
                    screen.blit(overlay, (px, py))

    # ── Highlight: letzter KI-Schuss ────────────────────────────
    if highlight:
        gx, gy = highlight
        px, py = zelle_px(gx, gy)
        pygame.draw.rect(screen, ORANGE, (px - 2, py - 2, ZELL + 1, ZELL + 1), 3)

    # ── Platzierungsvorschau ─────────────────────────────────────
    if vorschau:
        alpha = (68, 158, 78, 130) if vorschau_ok else (198, 58, 52, 130)
        s = pygame.Surface((ZELL - 1, ZELL - 1), pygame.SRCALPHA)
        s.fill(alpha)
        for (gx, gy) in vorschau:
            if 0 <= gx < 10 and 0 <= gy < 10:
                screen.blit(s, zelle_px(gx, gy))

    # ── Gitterlinien ────────────────────────────────────────────
    for i in range(11):
        x = RAND_L + i * ZELL
        y = RAND_O + i * ZELL
        pygame.draw.line(screen, GITTER_C, (x, RAND_O), (x, RAND_O + 10 * ZELL))
        pygame.draw.line(screen, GITTER_C, (RAND_L, y), (RAND_L + 10 * ZELL, y))

    # ── Achsenbeschriftungen ─────────────────────────────────────
    for i, c in enumerate("ABCDEFGHIJ"):
        t  = font_S.render(c, True, WEISS)
        px = RAND_L + i * ZELL + ZELL // 2 - t.get_width() // 2
        py = RAND_O - t.get_height() - 4
        screen.blit(t, (px, py))
    for i in range(10):
        t  = font_S.render(str(i + 1), True, WEISS)
        px = RAND_L - t.get_width() - 6
        py = RAND_O + i * ZELL + ZELL // 2 - t.get_height() // 2
        screen.blit(t, (px, py))


def panel_x():
    """X-Position wo das Panel beginnt (= Breite minus Panel-Breite)."""
    return BREITE - PANEL

def zeichne_panel(zeilen):
    """
    Zeichnet das rechte Infopanel mit einer Liste von Textzeilen.

    Args:
        zeilen – Liste von (text, farbe)-Tupeln.
                 Sonderfall: text == "---" zeichnet eine horizontale Trennlinie.

    Das Panel füllt den Bereich von panel_x() bis zum rechten Fensterrand.
    """
    px = panel_x()

    # Panel-Hintergrund bis zum rechten Rand
    pygame.draw.rect(screen, PANEL_BG, (px - 6, 0, BREITE - px + 6, HOEHE))

    y = 16   # Startposition für die erste Zeile
    for text, farbe in zeilen:
        if text == "---":
            # Trennlinie quer durch das Panel
            pygame.draw.line(screen, GITTER_C, (px, y + 5), (BREITE - 10, y + 5))
            y += 16
        else:
            t = font_M.render(text, True, farbe)
            screen.blit(t, (px, y))
            y += font_M.get_height() + 6   # Zeilenhöhe dynamisch aus Schriftgröße


# ═══════════════════════════════════════════════════════════════
#  Screen-Funktionen (eine pro Spielzustand)
# ═══════════════════════════════════════════════════════════════

# menue_btns speichert die aktuellen Button-Positionen für die Klick-Erkennung.
# Muss global sein weil zeichne_menue() es befüllt und die Hauptschleife es liest.
menue_btns = []

def zeichne_menue():
    """
    Hauptmenü: Titel + zwei Buttons (PvE / PvP) + Hinweistext.
    Button-Positionen werden proportional zur Fenstergröße berechnet.
    """
    global menue_btns
    screen.fill(BG)

    # Titel mittig im oberen Fünftel des Fensters
    titel = font_L.render("SCHIFFE VERSENKEN", True, GELB)
    screen.blit(titel, (BREITE // 2 - titel.get_width() // 2, HOEHE // 5))

    # Button-Größe: skaliert mit ZELL damit es auf kleinen und großen Fenstern passt
    btn_h = max(40, ZELL)
    btn_w = max(280, ZELL * 7)
    abst  = btn_h + 16           # Abstand zwischen den Buttons

    cy1 = HOEHE * 2 // 5         # Erster Button bei 40% der Fensterhöhe
    cy2 = cy1 + abst             # Zweiter Button direkt darunter

    menue_btns = [
        ("PvE  –  Gegen KI",     BREITE // 2, cy1, "pve"),
        ("PvP  –  Zwei Spieler", BREITE // 2, cy2, "pvp"),
    ]

    # Hinweistext unten (Tastenkürzel)
    hinweis = font_S.render("F11 – Vollbild  |  Fenstergröße ziehbar", True, GRAU)
    screen.blit(hinweis, (BREITE // 2 - hinweis.get_width() // 2, HOEHE * 4 // 5))

    # Buttons zeichnen – bei Hover Farbe wechseln
    mouse = pygame.mouse.get_pos()
    for label, cx, cy, _ in menue_btns:
        bx, by = cx - btn_w // 2, cy - btn_h // 2
        hover  = bx <= mouse[0] <= bx + btn_w and by <= mouse[1] <= by + btn_h
        pygame.draw.rect(screen, GELB if hover else WEISS, (bx, by, btn_w, btn_h), border_radius=7)
        t = font_M.render(label, True, BG)
        screen.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


def zeichne_setup():
    """
    Schiffe-Setzen-Screen: Zeigt das eigene Spielfeld, das nächste zu platzierende
    Schiff und eine Vorschau an der Mausposition.

    Steuerung:
        Mausklick → Schiff platzieren (nur wenn grüne Vorschau)
        R         → Ausrichtung drehen (horizontal ↔ vertikal)
        Esc       → zurück zum Menü
    """
    screen.fill(BG)

    groesse  = FLOTTE[spiel.schiff_idx]      # Größe des nächsten Schiffs
    sp_name  = f"Spieler {spiel.setup_spieler + 1}"
    richtung = "Horizontal" if spiel.horizontal else "Vertikal"

    # ── Platzierungsvorschau berechnen ──────────────────────────
    # Die Vorschau zeigt die Zellen, die das Schiff bei Klick belegen würde.
    maus  = pygame.mouse.get_pos()
    zelle = maus_zu_zelle(*maus)
    vorschau, vorschau_ok = None, False

    if zelle:
        gx, gy      = zelle
        felder_prev = []
        ok          = True
        for i in range(groesse):
            fx = gx + (i if spiel.horizontal else 0)
            fy = gy + (0 if spiel.horizontal else i)
            felder_prev.append((fx, fy))
            if not (0 <= fx < 10 and 0 <= fy < 10):
                ok = False   # Außerhalb des Rasters
            elif spiel.setup_feld().raster[fy][fx] == 1:
                ok = False   # Überlappung mit bereits platziertem Schiff
        vorschau, vorschau_ok = felder_prev, ok

    # Grid des aktuellen Setup-Spielers rendern (eigene Schiffe sichtbar)
    zeichne_raster(spiel.setup_feld(), vorschau=vorschau, vorschau_ok=vorschau_ok)

    # ── Panel: Schiffsliste mit Status ──────────────────────────
    # Gesetzt = grün mit Haken, aktuell = gelb mit Pfeil, ausstehend = grau
    info = [
        (f"{sp_name} setzt Schiffe", GELB),
        ("---",                       WEISS),
        (f"Schiff: {SCHIFF_NAMEN[groesse]} ({groesse})", WEISS),
        (f"[R] Drehen: {richtung}",   WEISS),
        ("---",                       WEISS),
        ("Schiffe:",                  WEISS),
    ]
    for i, g in enumerate(FLOTTE):
        if i < spiel.schiff_idx:
            info.append((f" ✓ {SCHIFF_NAMEN[g]} ({g})", GRUEN))   # bereits gesetzt
        elif i == spiel.schiff_idx:
            info.append((f" → {SCHIFF_NAMEN[g]} ({g})", GELB))    # jetzt dran
        else:
            info.append((f"   {SCHIFF_NAMEN[g]} ({g})",      GRAU))   # noch ausstehend

    info += [("---", WEISS), ("[Esc] Menü", GRAU)]
    zeichne_panel(info)


def zeichne_wechsel():
    """
    Wechsel-Screen: Zeigt eine zentrierte Nachricht auf schwarzem Hintergrund.
    Der Spieler bestätigt mit Enter, dann geht es weiter.
    Dient dazu, dass der andere Spieler beim Übergeben nicht das Spielfeld sieht.
    """
    screen.fill(BG)
    lines   = spiel.wechsel_text.split("\n")
    zeilenH = font_M.get_height() + 10   # Dynamische Zeilenhöhe basierend auf Schriftgröße
    y       = HOEHE // 2 - len(lines) * zeilenH // 2   # Textblock vertikal zentrieren
    for line in lines:
        t = font_M.render(line, True, WEISS)
        screen.blit(t, (BREITE // 2 - t.get_width() // 2, y))   # Jede Zeile horizontal zentrieren
        y += zeilenH


def zeichne_spielen():
    """
    Spiel-Screen: Der aktive Spieler sieht das GEGNERGITTER und schießt.

    Das Gegnergitter wird verdeckt gerendert (Schiffe unsichtbar, nur
    Treffer und Fehlschüsse sichtbar). Im Panel stehen Flottenstatus
    und letztes Schussergebnis.
    """
    screen.fill(BG)

    # Angriffsgitter des Gegners – verdeckt=True versteckt ungetroffene Schiffe
    zeichne_raster(spiel.angriffs_feld(), verdeckt=True)

    sp    = spiel.spieler_name()           # Aktiver Spieler
    feind = spiel.spieler_name(1 - spiel.aktiver)   # Gegner

    # Eigene Flotte: wie viele Schiffe sind noch aktiv?
    eigene  = spiel.eigenes_feld().schiffe
    lebend  = sum(1 for s in eigene if not s.versenkt)
    gesamt  = len(eigene)

    # Gegnerverluste: wie viele Schiffe wurden bereits versenkt?
    feind_schiffe  = spiel.angriffs_feld().schiffe
    feind_versenkt = sum(1 for s in feind_schiffe if s.versenkt)
    feind_gesamt   = len(feind_schiffe)

    # Ergebnisfarbe für den letzten Schuss
    er = spiel.letztes_ergebnis
    if "versenkt" in er:   er_farbe = ROT
    elif "treffer" in er:  er_farbe = GELB
    elif "wasser" in er:   er_farbe = MISS_C
    else:                  er_farbe = WEISS

    info = [
        (f"{sp} greift an",              GELB),
        ("---",                           WEISS),
        ("Deine Flotte:",                 WEISS),
        (f"  {lebend}/{gesamt} aktiv",    GRUEN if lebend > 0 else ROT),
        ("---",                           WEISS),
        (f"{feind}s Verluste:",           WEISS),
        (f"  {feind_versenkt}/{feind_gesamt} versenkt", GELB),
        ("---",                           WEISS),
        ("Letzter Schuss:",               WEISS),
        (f"  {er.upper() if er else '-'}", er_farbe),
        ("---",                           WEISS),
        ("[Esc] Menü",                    GRAU),
    ]
    zeichne_panel(info)


def zeichne_ki_dran():
    """
    KI-Zug-Screen (nur PvE): Der Spieler sieht sein EIGENES Spielfeld
    und beobachtet wie die KI schießt.

    Ablauf sichtbar für den Spieler:
        1. "KI denkt nach..." (KI_WARTE_MS ms)
        2. Schuss landet auf eigenem Board, Ergebnis erscheint im Panel
        3. Bei Treffer: zurück zu Schritt 1 (KI schießt nochmal)
        4. Bei Fehlschuss: zurück zu zeichne_spielen()

    Der orangefarbene Rahmen markiert die zuletzt beschossene Zelle.
    """
    screen.fill(BG)

    # Eigenes Spielfeld anzeigen: Schiffe sichtbar + KI-Schüsse markiert
    zeichne_raster(spiel.felder[0], verdeckt=False, highlight=spiel.ki_schuss_xy)

    # ── Statuszeile im oberen Rand ──────────────────────────────
    if spiel.ki_wartet:
        header, h_farbe = "KI denkt nach...", GRAU
    else:
        er = spiel.letztes_ergebnis
        if "versenkt" in er:
            header, h_farbe = "KI versenkt dein Schiff!", ROT
        elif "treffer" in er:
            header, h_farbe = "KI: TREFFER!", ORANGE
        else:
            header, h_farbe = "KI: Fehlschuss!", MISS_C

    t = font_M.render(header, True, h_farbe)
    # In der oberen Hälfte des Randes platzieren, klar über den Achsenbuchstaben
    header_y = max(4, RAND_O // 2 - t.get_height() // 2)
    screen.blit(t, (RAND_L, header_y))

    # ── Panel-Inhalt ────────────────────────────────────────────
    eigene = spiel.felder[0].schiffe
    lebend = sum(1 for s in eigene if not s.versenkt)
    gesamt = len(eigene)

    er      = spiel.letztes_ergebnis
    er_rein = er.replace("KI: ", "").upper() if er else "..."
    if "versenkt" in er:   er_farbe = ROT
    elif "treffer" in er:  er_farbe = ORANGE
    elif "wasser" in er:   er_farbe = MISS_C
    else:                  er_farbe = GRAU

    info = [
        ("KI ist dran",                GELB),
        ("---",                         WEISS),
        ("Deine Flotte:",               WEISS),
        (f"  {lebend}/{gesamt} aktiv",  GRUEN if lebend > 0 else ROT),
        ("---",                         WEISS),
        ("KI schießt auf:",             WEISS),
    ]
    if spiel.ki_schuss_xy:
        # Koordinate des letzten KI-Schusses anzeigen (z.B. "C5")
        info += [
            (f"  {koordinate(*spiel.ki_schuss_xy)}", GELB),
            ("Ergebnis:",                             WEISS),
            (f"  {er_rein}",                          er_farbe),
        ]
    else:
        info.append(("  ...", GRAU))   # Noch kein Schuss in dieser Runde

    zeichne_panel(info)


def zeichne_game_over():
    """
    Spielende-Screen: Zeigt den Sieger und gibt Optionen zum Neustart oder Beenden.
    """
    screen.fill(BG)
    name    = spiel.spieler_name(spiel.gewinner)
    zeilenH = font_M.get_height() + 10

    t1 = font_L.render(f"{name} gewinnt!", True, GELB)
    t2 = font_M.render("[Enter]  Nochmal spielen", True, WEISS)
    t3 = font_M.render("[Esc]    Beenden",          True, WEISS)

    cx = BREITE // 2
    # Titel über der Mitte, Optionen darunter
    screen.blit(t1, (cx - t1.get_width() // 2, HOEHE // 2 - font_L.get_height() - zeilenH))
    screen.blit(t2, (cx - t2.get_width() // 2, HOEHE // 2 + zeilenH // 2))
    screen.blit(t3, (cx - t3.get_width() // 2, HOEHE // 2 + zeilenH // 2 + zeilenH))


# ═══════════════════════════════════════════════════════════════
#  Hauptschleife
# ═══════════════════════════════════════════════════════════════
# Läuft mit 60 FPS. Pro Frame:
#   1. Layout aktualisieren falls Fenstergröße geändert
#   2. KI-Schritt ausführen falls KI dran ist (zeitgesteuert)
#   3. Alle Events verarbeiten (Tastatur, Maus, Fenster schließen)
#   4. Aktuellen Zustand rendern
#   5. Frame anzeigen

while True:

    # ── Layout-Anpassung bei Fenstergrößenänderung ──────────────
    # screen.get_size() wird every frame gecheckt – bei Unterschied zu den
    # gespeicherten BREITE/HOEHE-Werten wird das Layout neu berechnet.
    # Dies passiert automatisch wenn der Nutzer das Fenster zieht.
    if screen.get_size() != (BREITE, HOEHE):
        layout_aktualisieren()

    jetzt = pygame.time.get_ticks()   # Millisekunden seit Programmstart

    # ── KI-Zug (zeitgesteuert, kein Tastendruck nötig) ──────────
    if spiel.zustand == KI_DRAN:
        spiel.ki_schritt(jetzt)

    # ── Event-Verarbeitung ───────────────────────────────────────
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # F11 funktioniert in jedem Spielzustand
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_vollbild()
            continue   # Dieses Event nicht an den State-Handler weitergeben

        # ── Zustandsspezifische Event-Handler ───────────────────

        if spiel.zustand == MENUE:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Klick-Erkennung für die Menü-Buttons
                btn_h = max(40, ZELL)
                btn_w = max(280, ZELL * 7)
                for _, cx, cy, aktion in menue_btns:
                    bx, by = cx - btn_w // 2, cy - btn_h // 2
                    if bx <= event.pos[0] <= bx + btn_w and by <= event.pos[1] <= by + btn_h:
                        spiel.starte(aktion)   # "pve" oder "pvp"

        elif spiel.zustand == SCHIFFE_SETZEN:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    spiel.horizontal = not spiel.horizontal   # Ausrichtung drehen
                elif event.key == pygame.K_ESCAPE:
                    spiel.reset()   # Zurück zum Menü
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                zelle = maus_zu_zelle(*event.pos)
                if zelle:
                    spiel.platziere_schiff(*zelle)

        elif spiel.zustand == WECHSEL:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                spiel.wechsel_confirm()

        elif spiel.zustand == SPIELEN:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                spiel.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                zelle = maus_zu_zelle(*event.pos)
                if zelle:
                    spiel.schiesse(*zelle)

        elif spiel.zustand == GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    spiel.reset()   # Neues Spiel starten
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    # ── Rendering ────────────────────────────────────────────────
    # Jeder Zustand hat seine eigene Zeichenfunktion.
    # screen.fill(BG) passiert jeweils am Anfang der Zeichenfunktion.
    if spiel.zustand == MENUE:
        zeichne_menue()
    elif spiel.zustand == SCHIFFE_SETZEN:
        zeichne_setup()
    elif spiel.zustand == WECHSEL:
        zeichne_wechsel()
    elif spiel.zustand == SPIELEN:
        zeichne_spielen()
    elif spiel.zustand == KI_DRAN:
        zeichne_ki_dran()
    elif spiel.zustand == GAME_OVER:
        zeichne_game_over()

    pygame.display.flip()   # Fertig gezeichneten Frame anzeigen
    clock.tick(60)          # Max. 60 FPS – verhindert unnötige CPU-Last
