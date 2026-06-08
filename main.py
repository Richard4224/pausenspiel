import pygame
import sys
from modelle import Spielfeld, Schiff, KI, FLOTTE, SCHIFF_NAMEN


# ═══════════════════════════════════════════════════════════════
#  Initialisierung
# ═══════════════════════════════════════════════════════════════

pygame.init()

BREITE = 920
HOEHE  = 700
ZELLE   = 58      # Größe einer Spielfeldzelle in Pixeln (Breite = Höhe, da quadratisch)
RAND_L = 58      # Abstand des Spielfelds vom linken Fensterrand
RAND_O = 58      # Abstand des Spielfelds vom oberen Fensterrand

Fenster = pygame.display.set_mode((BREITE, HOEHE))
clock  = pygame.time.Clock()
pygame.display.set_caption("Schiffe Versenken")

Schrift_gross  = pygame.font.SysFont("Arial", 36, bold=True)
Schrift_mittel = pygame.font.SysFont("Arial", 22)
Schrift_klein  = pygame.font.SysFont("Arial", 16)

Hintergrund = pygame.image.load(
    "Modelle,Texturen/Hintergrund.png"
).convert()

Hintergrund = pygame.transform.scale(
    Hintergrund,
    (BREITE, HOEHE)
)


# ═══════════════════════════════════════════════════════════════
#  Texturen
# ═══════════════════════════════════════════════════════════════
# Alle Bilder werden einmalig beim Start geladen.
# .convert()       – optimiert das Pixelformat für schnelles Zeichnen (kein Alpha)
# .convert_alpha() – wie convert(), aber behält den Alpha-Kanal für Transparenz

TEXTUR_PFAD = "Modelle,Texturen/"

def lade_textur(dateiname, alpha=False):
    """
    Lädt eine Bilddatei aus dem Texturordner und konvertiert sie.
    alpha=True → convert_alpha() für Bilder mit Transparenz (PNG mit Alpha-Kanal)
    alpha=False → convert() für Bilder ohne Transparenz (z.B. Hintergrundbild)
    """
    text_flaeche = pygame.image.load(TEXTUR_PFAD + dateiname)
    return text_flaeche.convert_alpha() if alpha else text_flaeche.convert()

# Hintergrundbild – wird als einziges Bild auf das gesamte 10×10-Grid gestreckt
wasser_textur = lade_textur("Wasser.png")

# Pro Schiffsklasse ein eigenes Modell – Schlüssel ist die Schiffsgröße (Anzahl Zellen)
schiff_texturen = {
    2: lade_textur("Patrol Boat.png",  alpha=True),
    3: lade_textur("Destroyer.png",    alpha=True),
    4: lade_textur("Cruiser.png",      alpha=True),
    5: lade_textur("Battleship.png",   alpha=True),
}

# Overlays – werden transparent über Wasser oder Schiffe gelegt
explosion_textur = lade_textur("Explosion.png", alpha=True)  # Treffer
splash_textur    = lade_textur("Splash.png",    alpha=True)  # Fehlschuss

# Cache für skalierte/gedrehte Texturen (siehe skalierte_textur())
_textur_cache = {}


# ═══════════════════════════════════════════════════════════════
#  Farben (RGB)
# ═══════════════════════════════════════════════════════════════

BG        = (15,  25,  40)   # Dunkelblauer Hintergrund
WASSER_C  = (28,  95, 175)   # Fallback-Farbe falls Wassertextur fehlt
SCHIFF_C  = (68,  72,  82)   # Fallback-Farbe für Schiffe
TREFFER_C = (210, 55,  50)   # Rot – getroffene Zelle
MISS_C    = (148, 182, 208)  # Hellblau – Fehlschuss
GITTER_C  = (20,  62, 125)   # Dunkelblau – Gitterlinien
PANEL_BG  = (22,  38,  58)   # Etwas helleres Blau für das Infopanel
WEISS     = (225, 235, 245)  # Fast-Weiß für normalen Text
GELB      = (248, 198,  48)  # Gelb für Überschriften und aktive Elemente
GRUEN     = (68,  158,  78)  # Grün für positive Anzeigen
ROT       = (198,  58,  52)  # Rot für Warnungen
GRAU      = (100, 110, 120)  # Grau für deaktivierte Elemente
ORANGE    = (240, 140,  40)  # Orange für den letzten KI-Schuss


# ═══════════════════════════════════════════════════════════════
#  Spielzustände (State Machine)
# ═══════════════════════════════════════════════════════════════
# Das Spiel ist zu jedem Zeitpunkt in genau einem dieser Zustände.
# Der Zustand bestimmt welcher Screen gezeichnet wird und welche
# Eingaben verarbeitet werden. Übergänge passieren nur in den
# Spiellogik-Funktionen, nie direkt in der Hauptschleife.

MENUE          = "menue"           # Startmenü mit Moduswahl
SCHIFFE_SETZEN = "schiffe_setzen"  # Spieler platziert Schiffe per Klick
WECHSEL        = "wechsel"         # Schwarzer Übergangsscreen zwischen den Spielern
SPIELEN        = "spielen"         # Aktiver Spieler schießt auf Gegnergitter
KI_ZUG         = "ki_zug"          # KI-Zug mit animierter Wartezeit
GAME_OVER      = "game_over"       # Spielende, Sieger wird angezeigt

# Wartezeiten für den KI-Zug (in Millisekunden).
# Ohne diese Pausen würde die KI sofort schießen – das wäre kaum zu verfolgen.
KI_WARTE_MS = 1500   # Denkpause bevor die KI schießt
KI_ZEIGE_MS = 700    # Anzeigezeit des Ergebnisses nach dem KI-Schuss


# ═══════════════════════════════════════════════════════════════
#  Spielzustand-Dictionary
# ═══════════════════════════════════════════════════════════════
# Alle veränderlichen Spielvariablen stecken in einem einzigen Dictionary.
# Das hat zwei Vorteile:
#   1. Reset ist trivial: spiel_neu() ersetzt einfach das ganze Dictionary.
#   2. Alle Abhängigkeiten sind an einem Ort sichtbar.

spiel = {}   # wird von spiel_neu() befüllt


def spiel_neu():
    """Setzt alle Spielvariablen auf den Anfangszustand zurück."""
    global spiel
    spiel = {
        "zustand":          MENUE,
        "modus":            None,                        # "pve" oder "pvp", wird in spiel_starten() gesetzt
        "felder":           [Spielfeld(), Spielfeld()],  # Index 0 = Spieler 1, Index 1 = Spieler 2 / KI
        "aktiver":          0,                           # Wer schießt gerade? 0 oder 1
        "setup_spieler":    0,                           # Wer setzt gerade Schiffe? 0 oder 1
        "schiff_idx":       0,                           # Welches Schiff aus FLOTTE kommt als nächstes?
        "horizontal":       True,                        # Ausrichtung beim Platzieren (R zum Umschalten)
        "ki":               None,                        # KI-Objekt, nur im PvE-Modus vorhanden
        "wechsel_text":     "",                          # Nachricht auf dem Übergabe-Screen
        "wechsel_next":     "",                          # Aktion nach Enter: "setup2", "start" oder "zug"
        "letztes_ergebnis": "",                          # "wasser", "treffer" oder "versenkt"
        "gewinner":         None,                        # Index des Gewinners (0 oder 1)
        "ki_wartet":        True,                        # True = Denkpause, False = Ergebnis anzeigen
        "ki_naechste_zeit": 0,                           # pygame-Tick ab dem der nächste KI-Schritt startet
        "ki_schuss_xy":     None,                        # (x,y) des letzten KI-Schusses für orangen Rahmen
    }


# ═══════════════════════════════════════════════════════════════
#  Spiellogik
# ═══════════════════════════════════════════════════════════════

def spieler_name(idx=None):
    """
    Gibt den Anzeigenamen für einen Spieler zurück.
    Ohne Argument: Name des aktuell aktiven Spielers.
    Im PvE-Modus heißt Spieler 1 (idx=1) einfach 'KI'.
    """
    i = spiel["aktiver"] if idx is None else idx
    if spiel["modus"] == "pve" and i == 1:
        return "KI"
    return f"Spieler {i + 1}"


def spiel_starten(modus):
    """Startet eine neue Partie im gewählten Modus und beginnt die Setup-Phase."""
    spiel["modus"]         = modus
    spiel["setup_spieler"] = 0
    spiel["schiff_idx"]    = 0
    spiel["horizontal"]    = True
    spiel["zustand"]       = SCHIFFE_SETZEN


def schiff_platzieren(gx, gy):
    """
    Versucht das nächste Schiff aus FLOTTE auf Position (gx, gy) zu setzen.
    Bei Erfolg: schiff_idx erhöhen. Wenn alle Schiffe gesetzt: alle_schiffe_gesetzt() aufrufen.
    """
    schiff = Schiff(FLOTTE[spiel["schiff_idx"]])
    feld   = spiel["felder"][spiel["setup_spieler"]]

    if feld.platzieren(schiff, gx, gy, spiel["horizontal"]):
        spiel["schiff_idx"] += 1
        if spiel["schiff_idx"] >= len(FLOTTE):
            alle_schiffe_gesetzt()


def alle_schiffe_gesetzt():
    """
    Wird aufgerufen wenn ein Spieler alle seine Schiffe platziert hat.
    PvP: Spieler 2 muss noch Schiffe setzen → Wechsel-Screen.
    PvE: Nur Spieler 1 setzt Schiffe → Spiel beginnt direkt.
    """
    if spiel["modus"] == "pvp" and spiel["setup_spieler"] == 0:
        zeige_wechsel(
            "Spieler 1 ist fertig.\n\nSpieler 2, bitte übernehmen.\n\n[Enter] drücken",
            naechstes="setup2"
        )
    else:
        spiel_beginnen()


def spiel_beginnen():
    """
    Alle Schiffe sind gesetzt – das Spiel startet.
    Im PvE-Modus: KI-Objekt erstellen, KI-Feld zufällig besetzen.
    Im PvP-Modus: kurzen Startscreen zeigen.
    """
    if spiel["modus"] == "pve":
        spiel["ki"] = KI()
        spiel["felder"][1].zufaellig_besetzen()   # KI-Schiffe unsichtbar platzieren

    spiel["aktiver"]          = 0
    spiel["letztes_ergebnis"] = ""

    if spiel["modus"] == "pvp":
        zeige_wechsel(
            "Beide Spieler sind bereit!\n\nSpieler 1, du beginnst.\n\n[Enter] drücken",
            naechstes="start"
        )
    else:
        spiel["zustand"] = SPIELEN


def schiessen(gx, gy):
    """
    Aktiver Spieler schießt auf (gx, gy) des Gegners.
    Bei Treffer: gleicher Spieler darf nochmal.
    Bei Fehlschuss: spieler_wechseln() aufrufen.
    Bei letztem Schiff versenkt: GAME_OVER.
    """
    # "1 - aktiver" wechselt elegant zwischen Index 0 und 1
    gegner_feld = spiel["felder"][1 - spiel["aktiver"]]
    ergebnis    = gegner_feld.schiessen(gx, gy)

    if ergebnis is None:
        return   # Bereits beschossene Zelle – ignorieren

    spiel["letztes_ergebnis"] = ergebnis

    if gegner_feld.alle_versenkt():
        spiel["gewinner"] = spiel["aktiver"]
        spiel["zustand"]  = GAME_OVER
        return

    if ergebnis == "wasser":
        spieler_wechseln()
    # "treffer" oder "versenkt": Zustand bleibt SPIELEN → nochmal schießen


def spieler_wechseln():
    """
    Fehlschuss: zum nächsten Spieler wechseln.
    PvP → Wechsel-Screen damit der andere Spieler das Spielfeld nicht sieht.
    PvE → KI-Zug direkt starten.
    """
    if spiel["modus"] == "pvp":
        naechster = 1 - spiel["aktiver"]
        zeige_wechsel(
            f"{spieler_name(naechster)}, du bist dran!\n\nBitte übernehmen.\n\n[Enter] drücken",
            naechstes="zug"
        )
    else:
        ki_zug_starten()


def ki_zug_starten():
    """
    KI-Zug vorbereiten und in den KI_ZUG-Zustand wechseln.
    Der eigentliche Zug läuft dann zeitgesteuert über ki_schritt().
    """
    spiel["ki_schuss_xy"]     = None
    spiel["ki_wartet"]        = True
    spiel["ki_naechste_zeit"] = pygame.time.get_ticks() + KI_WARTE_MS
    spiel["zustand"]          = KI_ZUG


def ki_schritt(jetzt):
    """
    KI-Zug animiert ausführen. Wird jeden Frame aufgerufen wenn KI_ZUG aktiv ist.

    Zweiphasiger Ablauf damit der Spieler etwas sieht:
      Phase 1 (ki_wartet=True):  Denkpause (KI_WARTE_MS ms), dann Schuss ausführen.
      Phase 2 (ki_wartet=False): Ergebnis anzeigen (KI_ZEIGE_MS ms), dann weiter.
    """
    if jetzt < spiel["ki_naechste_zeit"]:
        return   # Timer läuft noch – auf nächsten Frame warten

    if spiel["ki_wartet"]:
        # ── Phase 1: KI schießt ──────────────────────────────────
        # while-Schleife als Sicherheitsnetz für bereits beschossene Felder
        while spiel["ki"].kandidaten:
            x, y     = spiel["ki"].naechster_schuss()
            ergebnis = spiel["felder"][0].schiessen(x, y)
            if ergebnis is not None:
                break
        else:
            return   # Keine Kandidaten mehr (Sicherheitsfall)

        spiel["ki_schuss_xy"]     = (x, y)
        spiel["letztes_ergebnis"] = f"KI: {ergebnis}"
        spiel["ki_wartet"]        = False                  # → Phase 2
        spiel["ki_naechste_zeit"] = jetzt + KI_ZEIGE_MS

    else:
        # ── Phase 2: Ergebnis auswerten ──────────────────────────
        ergebniss = spiel["letztes_ergebnis"]

        if spiel["felder"][0].alle_versenkt():
            spiel["gewinner"] = 1
            spiel["zustand"]  = GAME_OVER
        elif "wasser" in ergebniss:
            # Fehlschuss → Spieler ist wieder dran
            spiel["ki_schuss_xy"]     = None
            spiel["letztes_ergebnis"] = ""
            spiel["zustand"]          = SPIELEN
        else:
            # Treffer → KI schießt nochmal (zurück zu Phase 1)
            spiel["ki_wartet"]        = True
            spiel["ki_schuss_xy"]     = None
            spiel["ki_naechste_zeit"] = jetzt + KI_WARTE_MS


def zeige_wechsel(text, naechstes):
    """Wechselt in den WECHSEL-Zustand und speichert Text und Folgeaktion."""
    spiel["wechsel_text"] = text
    spiel["wechsel_next"] = naechstes
    spiel["zustand"]      = WECHSEL


def wechsel_bestaetigt():
    """
    Spieler hat auf dem Wechsel-Screen Enter gedrückt.
    "setup2" → Spieler 2 setzt Schiffe
    "start"  → Spiel beginnt (nach PvP-Setup)
    "zug"    → Nächster Spieler ist dran
    """
    if spiel["wechsel_next"] == "setup2":
        spiel["setup_spieler"] = 1
        spiel["schiff_idx"]    = 0
        spiel["horizontal"]    = True
        spiel["zustand"]       = SCHIFFE_SETZEN
    elif spiel["wechsel_next"] in ("start", "zug"):
        if spiel["wechsel_next"] == "zug":
            spiel["aktiver"] = 1 - spiel["aktiver"]   # 0→1 oder 1→0
        spiel["letztes_ergebnis"] = ""
        spiel["zustand"]          = SPIELEN


# ═══════════════════════════════════════════════════════════════
#  Textur-Hilfsfunktion
# ═══════════════════════════════════════════════════════════════

def skalierte_textur(textur, breite, hoehe, winkel=0):
    """
    Gibt eine skalierte (und optional gedrehte) Textur zurück.
    Das Ergebnis wird gecacht – pygame.transform.scale/rotate ist rechenintensiv
    und würde bei 60 FPS sonst jedes Frame neu ausgeführt werden.

    textur – Original-pygame.Surface
    breite – Zielbreite in Pixeln
    hoehe  – Zielhöhe in Pixeln
    winkel – Drehung in Grad (0 = keine Drehung, -90 = 90° im Uhrzeigersinn)

    Der Cache-Schlüssel kombiniert alle Parameter eindeutig, sodass z.B.
    dieselbe Textur in zwei Größen oder Winkeln separat gecacht wird.
    """
    key = (id(textur), breite, hoehe, winkel)
    if key not in _textur_cache:
        skaliert = pygame.transform.scale(textur, (breite, hoehe))
        # Nur drehen wenn nötig – rotate(surf, 0) wäre sinnlose Arbeit
        _textur_cache[key] = pygame.transform.rotate(skaliert, winkel) if winkel else skaliert
    return _textur_cache[key]


# ═══════════════════════════════════════════════════════════════
#  Zeichenhilfsfunktionen
# ═══════════════════════════════════════════════════════════════

def gitter_zu_pixel(gx, gy):
    """Wandelt Gitterkoordinaten (0–9) in die Pixelposition der Zelle um (obere linke Ecke)."""
    return RAND_L + gx * ZELLE, RAND_O + gy * ZELLE


def maus_zu_gitter(px, py):
    """
    Wandelt eine Mausposition in Pixeln in Gitterkoordinaten um.
    Gibt (gx, gy) zurück – oder None wenn die Maus außerhalb des Grids ist.
    """
    gx = (px - RAND_L) // ZELLE
    gy = (py - RAND_O) // ZELLE
    if 0 <= gx < 10 and 0 <= gy < 10:
        return gx, gy
    return None


def text_zentriert(text, font, y, farbe=WEISS):
    """Rendert einen Text horizontal zentriert auf der angegebenen y-Position."""
    surf = font.render(text, True, farbe)
    Fenster.blit(surf, (BREITE // 2 - surf.get_width() // 2, y))


# ═══════════════════════════════════════════════════════════════
#  Schiff-Zeichenfunktion
# ═══════════════════════════════════════════════════════════════

def zeichne_schiff_modell(schiff):
    """
    Zeichnet ein Schiff als zusammenhängendes Modellbild über alle seine Zellen.

    Alle Schiffstexturen liegen im Querformat vor (horizontal).
    Für vertikale Schiffe wird die Textur zuerst auf die horizontale Zielgröße
    skaliert und dann um -90° gedreht → pygame tauscht dabei automatisch
    Breite und Höhe, das Ergebnis passt also exakt ins Grid.

    Beispiel für ein 3er-Schiff bei ZELL=58:
      horizontal: skalieren auf (3*58-1, 58-1) = (173, 57)
      vertikal:   skalieren auf (173, 57), dann -90° drehen → (57, 173)
    """
    if not schiff.felder:
        return

    textur = schiff_texturen.get(schiff.groesse)
    if textur is None:
        return   # Kein Modell für diese Schiffsgröße – still überspringen

    # Obere linke Ecke des Schiffs (nach Sortierung ist das immer felder[0])
    gx0, gy0 = sorted(schiff.felder)[0]
    px, py   = gitter_zu_pixel(gx0, gy0)

    # Ausrichtung bestimmen: wenn sich der x-Wert zwischen den Feldern ändert → horizontal
    horizontal = len({x for x, y in schiff.felder}) > 1

    # Zielgröße berechnen: Schiffslänge × Zellgröße, minus 1px für die Gitterlinie
    schiff_lang = schiff.groesse * ZELLE - 1
    zell_kurz   = ZELLE - 1

    if horizontal:
        # Textur direkt auf (Länge × ZELLE, ZELLE) strecken
        bild = skalierte_textur(textur, schiff_lang, zell_kurz)
    else:
        # Textur horizontal skalieren, dann um 90° drehen → wird automatisch hochkant
        bild = skalierte_textur(textur, schiff_lang, zell_kurz, winkel=-90)

    Fenster.blit(bild, (px, py))


# ═══════════════════════════════════════════════════════════════
#  Spielfeld-Zeichenfunktion
# ═══════════════════════════════════════════════════════════════

def zeichne_spielfeld(feld, verdeckt=False, vorschau=None, vorschau_ok=True, highlight=None):
    """
    Zeichnet das komplette 10×10 Spielfeld in dieser Reihenfolge:
      1. Wasser-Hintergrundbild (ganzes Grid auf einmal)
      2. Schiffsmodelle (außer im Angriffsmodus)
      3. Treffer- und Fehlschuss-Overlays
      4. Versenkte Schiffe aufdecken (nur im Angriffsmodus)
      5. Highlight für letzten KI-Schuss
      6. Platzierungsvorschau (transparent)
      7. Gitternetz
      8. Achsenbeschriftung (A–J, 1–10)

    feld       – Spielfeld-Objekt
    verdeckt   – True im Angriffsmodus: Schiffe verstecken, nur Treffer/Fehlschuss sichtbar
    vorschau   – Liste von (gx,gy)-Zellen die als Platzierungsvorschau eingefärbt werden
    vorschau_ok– True = grüne Vorschau (gültige Position), False = rote (ungültig)
    highlight  – (gx,gy)-Zelle mit orangem Rahmen (letzter KI-Schuss)
    """

    # ── 1. Wasser-Hintergrundbild ────────────────────────────────
    # Ein einziges Bild wird auf das gesamte Grid gestreckt (10×ZELL × 10×ZELL).
    grid_pixel = 10 * ZELLE
    Fenster.blit(skalierte_textur(wasser_textur, grid_pixel, grid_pixel), (RAND_L, RAND_O))

    # ── 2. Schiffsmodelle ────────────────────────────────────────
    # Im Angriffsmodus (verdeckt=True) sind Schiffe unsichtbar – klassische Spielregel.
    if not verdeckt:
        for schiff in feld.schiffe:
            zeichne_schiff_modell(schiff)

    # ── 3. Treffer- und Fehlschuss-Overlays ──────────────────────
    # Die Overlays liegen transparent über Wasser bzw. Schiff.
    # raster[gy][gx]: 0 = Wasser, 1 = Schiff, 2 = Fehlschuss, 3 = Treffer
    for gy in range(10):
        for gx in range(10):
            px, py = gitter_zu_pixel(gx, gy)
            wert   = feld.raster[gy][gx]

            if wert == 2:
                Fenster.blit(skalierte_textur(splash_textur, ZELLE - 1, ZELLE - 1), (px, py))
            elif wert == 3:
                Fenster.blit(skalierte_textur(explosion_textur, ZELLE - 1, ZELLE - 1), (px, py))

    # ── 4. Versenkte Schiffe aufdecken ───────────────────────────
    # Spielregel: Ein versenktes Schiff wird auf dem Angriffsgitter sichtbar.
    if verdeckt:
        for schiff in feld.schiffe:
            if schiff.versenkt:
                zeichne_schiff_modell(schiff)
                # Alle Felder des versenkten Schiffs mit Explosion überlagern
                for gx, gy in schiff.felder:
                    px, py = gitter_zu_pixel(gx, gy)
                    Fenster.blit(skalierte_textur(explosion_textur, ZELLE - 1, ZELLE - 1), (px, py))

    # ── 5. Highlight: letzter KI-Schuss ─────────────────────────
    # Orangefarbener Rahmen damit der Spieler sieht wohin die KI gerade geschossen hat.
    if highlight:
        gx, gy = highlight
        px, py = gitter_zu_pixel(gx, gy)
        pygame.draw.rect(Fenster, ORANGE, (px - 2, py - 2, ZELLE + 1, ZELLE + 1), 3)

    # ── 6. Platzierungsvorschau ──────────────────────────────────
    # SRCALPHA-Surface ermöglicht den Alpha-Kanal (130 von 255 = halbtransparent).
    # Grün = gültige Position, Rot = ungültig (außerhalb oder Überlappung).
    if vorschau:
        alpha = (68, 158, 78, 130) if vorschau_ok else (198, 58, 52, 130)
        overlay = pygame.Surface((ZELLE - 1, ZELLE - 1), pygame.SRCALPHA)
        overlay.fill(alpha)
        for gx, gy in vorschau:
            if 0 <= gx < 10 and 0 <= gy < 10:
                Fenster.blit(overlay, gitter_zu_pixel(gx, gy))

    # ── 7. Gitternetz ────────────────────────────────────────────
    # 11 Linien ergeben 10 Spalten/Zeilen (je eine am Anfang und Ende des Grids).
    for i in range(11):
        x = RAND_L + i * ZELLE
        y = RAND_O + i * ZELLE
        pygame.draw.line(Fenster, GITTER_C, (x, RAND_O), (x, RAND_O + 10 * ZELLE))
        pygame.draw.line(Fenster, GITTER_C, (RAND_L, y), (RAND_L + 10 * ZELLE, y))

    # ── 8. Achsenbeschriftung ────────────────────────────────────
    # Buchstaben A–J über den Spalten, Zahlen 1–10 links der Zeilen.
    for i, buchstabe in enumerate("ABCDEFGHIJ"):
        text_flaeche = Schrift_klein.render(buchstabe, True, WEISS)
        px = RAND_L + i * ZELLE + ZELLE // 2 - text_flaeche.get_width() // 2   # in Spaltenmitte
        Fenster.blit(text_flaeche, (px, RAND_O - text_flaeche.get_height() - 4))
    for i in range(10):
        text_flaeche = Schrift_klein.render(str(i + 1), True, WEISS)
        py = RAND_O + i * ZELLE + ZELLE // 2 - text_flaeche.get_height() // 2  # in Zeilenmitte
        Fenster.blit(text_flaeche, (RAND_L - text_flaeche.get_width() - 6, py))


# ═══════════════════════════════════════════════════════════════
#  Panel-Zeichenfunktion
# ═══════════════════════════════════════════════════════════════

def zeichne_panel(zeilen):
    """
    Zeichnet das rechte Infopanel mit einer Liste von Textzeilen.
    zeilen = Liste von (text, farbe)-Tupeln.
    Sonderfall: text == "---" zeichnet eine horizontale Trennlinie.
    """
    panel_x = BREITE - 210
    pygame.draw.rect(Fenster, PANEL_BG, (panel_x - 8, 0, BREITE - panel_x + 8, HOEHE))

    y = 20
    for text, farbe in zeilen:
        if text == "---":
            pygame.draw.line(Fenster, GITTER_C, (panel_x, y + 5), (BREITE - 10, y + 5))
            y += 18
        else:
            text_flaeche = Schrift_mittel.render(text, True, farbe)
            Fenster.blit(text_flaeche, (panel_x, y))
            y += text_flaeche.get_height() + 6


# ═══════════════════════════════════════════════════════════════
#  Screen-Funktionen (eine pro Spielzustand)
# ═══════════════════════════════════════════════════════════════

# Button-Positionen werden in zeichne_menue() berechnet und hier gespeichert,
# damit die Klick-Erkennung in der Hauptschleife auf dieselben Koordinaten zugreift.
menue_btns = []


def zeichne_menue():
    """Hauptmenü: Titel + zwei Modus-Buttons."""
    global menue_btns
    Fenster.blit(Hintergrund, (0, 0))

    btn_b = 280
    btn_h = 50
    bx    = BREITE // 2 - btn_b // 2
    y1    = HOEHE * 2 // 5
    y2    = y1 + 70

    menue_btns = [
        ("PvE  –  Gegen KI",     bx, y1, "pve"),
        ("PvP  –  Zwei Spieler", bx, y2, "pvp"),
    ]

    maus = pygame.mouse.get_pos()
    for Beschriftung, bx, by, _ in menue_btns:
        # Hover-Effekt: Button wird gelb wenn die Maus drüber ist
        hover = bx <= maus[0] <= bx + btn_b and by <= maus[1] <= by + btn_h
        pygame.draw.rect(Fenster, GELB if hover else WEISS, (bx, by, btn_b, btn_h), border_radius=6)
        text_flaeche = Schrift_mittel.render(Beschriftung, True, BG)
        Fenster.blit(text_flaeche, (bx + btn_b // 2 - text_flaeche.get_width() // 2, by + btn_h // 2 - text_flaeche.get_height() // 2))


def zeichne_schiffe_setzen():
    """Schiffe-Setzen-Screen: Spielfeld mit Vorschau + Panel mit Schiffsliste."""
    Fenster.fill(BG)

    groesse  = FLOTTE[spiel["schiff_idx"]]
    sp_name  = f"Spieler {spiel['setup_spieler'] + 1}"
    richtung = "Horizontal" if spiel["horizontal"] else "Vertikal"

    # Vorschau berechnen: welche Zellen würde das Schiff an der Mausposition belegen?
    maus     = pygame.mouse.get_pos()
    zelle    = maus_zu_gitter(*maus)
    vorschau = None
    ok       = False

    if zelle:
        gx, gy   = zelle
        vorschau = []
        ok       = True
        for i in range(groesse):
            fx = gx + (i if spiel["horizontal"] else 0)
            fy = gy + (0 if spiel["horizontal"] else i)
            vorschau.append((fx, fy))
            # Vorschau ist ungültig wenn eine Zelle außerhalb des Grids liegt...
            if not (0 <= fx < 10 and 0 <= fy < 10):
                ok = False
            # ...oder bereits ein anderes Schiff dort steht
            elif spiel["felder"][spiel["setup_spieler"]].raster[fy][fx] == 1:
                ok = False

    zeichne_spielfeld(spiel["felder"][spiel["setup_spieler"]], vorschau=vorschau, vorschau_ok=ok)

    # Panel: Status jedes Schiffs in der Flotte (gesetzt ✓, aktuell →, ausstehend grau)
    info = [
        (f"{sp_name} setzt Schiffe", GELB),
        ("---", WEISS),
        (f"Schiff: {SCHIFF_NAMEN[groesse]} ({groesse})", WEISS),
        (f"[R] Drehen: {richtung}", WEISS),
        ("---", WEISS),
        ("Flotte:", WEISS),
    ]
    for i, groesse in enumerate(FLOTTE):
        if i < spiel["schiff_idx"]:
            info.append((f" ✓ {SCHIFF_NAMEN[groesse]} ({groesse})", GRUEN))
        elif i == spiel["schiff_idx"]:
            info.append((f" → {SCHIFF_NAMEN[groesse]} ({groesse})", GELB))
        else:
            info.append((f"   {SCHIFF_NAMEN[groesse]} ({groesse})", GRAU))
    info += [("---", WEISS), ("[Esc] Menü", GRAU)]
    zeichne_panel(info)


def zeichne_wechsel_screen():
    """Übergabe-Screen: zentrierter Text auf dunklem Hintergrund, wartet auf Enter."""
    Fenster.fill(BG)
    zeilen = spiel["wechsel_text"].split("\n")
    zeil_h = Schrift_mittel.get_height() + 10
    y      = HOEHE // 2 - len(zeilen) * zeil_h // 2
    for zeile in zeilen:
        text_zentriert(zeile, Schrift_mittel, y)
        y += zeil_h


def zeichne_spielen():
    """Spielscreen: Angriffsgitter des Gegners – verdeckt, nur Treffer/Fehlschuss sichtbar."""
    Fenster.fill(BG)
    zeichne_spielfeld(spiel["felder"][1 - spiel["aktiver"]], verdeckt=True)

    eigene_schiffe = spiel["felder"][spiel["aktiver"]].schiffe
    gegner_schiffe = spiel["felder"][1 - spiel["aktiver"]].schiffe
    lebend         = sum(1 for overlay in eigene_schiffe if not overlay.versenkt)
    versenkt       = sum(1 for overlay in gegner_schiffe if overlay.versenkt)

    # Farbe des letzten Schussergebnisses im Panel
    ergebniss = spiel["letztes_ergebnis"]
    if "versenkt" in ergebniss:  er_farbe = ROT
    elif "treffer" in ergebniss: er_farbe = GELB
    elif "wasser" in ergebniss:  er_farbe = MISS_C
    else:                         er_farbe = WEISS

    info = [
        (f"{spieler_name()} greift an", GELB),
        ("---", WEISS),
        (f"Deine Flotte: {lebend}/{len(eigene_schiffe)}", GRUEN if lebend > 0 else ROT),
        (f"Gegner versenkt: {versenkt}/{len(gegner_schiffe)}", GELB),
        ("---", WEISS),
        ("Letzter Schuss:", WEISS),
        (f"  {ergebniss.upper() if ergebniss else '-'}", er_farbe),
        ("---", WEISS),
        ("[Esc] Menü", GRAU),
    ]
    zeichne_panel(info)


def zeichne_ki_zug():
    """KI-Zug-Screen: eigenes Spielfeld, Spieler beobachtet den KI-Zug."""
    Fenster.fill(BG)
    # Eigenes Spielfeld mit Schiffsmodellen + orangem Rahmen um letzten KI-Schuss
    zeichne_spielfeld(spiel["felder"][0], verdeckt=False, highlight=spiel["ki_schuss_xy"])

    # Statuszeile über dem Grid – zeigt ob KI denkt oder das Ergebnis sichtbar ist
    if spiel["ki_wartet"]:
        header, h_farbe = "KI denkt nach...", GRAU
    else:
        ergebniss = spiel["letztes_ergebnis"]
        if "versenkt" in ergebniss:  header, h_farbe = "KI versenkt dein Schiff!", ROT
        elif "treffer" in ergebniss: header, h_farbe = "KI: TREFFER!", ORANGE
        else:                 header, h_farbe = "KI: Fehlschuss!", MISS_C

    text_flaeche = Schrift_mittel.render(header, True, h_farbe)
    Fenster.blit(text_flaeche, (RAND_L, max(4, RAND_O // 2 - text_flaeche.get_height() // 2)))

    eigene = spiel["felder"][0].schiffe
    lebend = sum(1 for overlay in eigene if not overlay.versenkt)
    ergebniss = spiel["letztes_ergebnis"]
    er_text = ergebniss.replace("KI: ", "").upper() if ergebniss else "..."

    if "versenkt" in ergebniss:  er_farbe = ROT
    elif "treffer" in ergebniss: er_farbe = ORANGE
    elif "wasser" in ergebniss:  er_farbe = MISS_C
    else:                         er_farbe = GRAU

    info = [
        ("KI ist dran", GELB),
        ("---", WEISS),
        (f"Deine Flotte: {lebend}/{len(eigene)}", GRUEN if lebend > 0 else ROT),
        ("---", WEISS),
        ("KI schießt auf:", WEISS),
    ]
    if spiel["ki_schuss_xy"]:
        gx, gy = spiel["ki_schuss_xy"]
        koord  = f"{'ABCDEFGHIJ'[gx]}{gy + 1}"
        info  += [(f"  {koord}", GELB), ("Ergebnis:", WEISS), (f"  {er_text}", er_farbe)]
    else:
        info.append(("  ...", GRAU))
    zeichne_panel(info)


def zeichne_game_over():
    """Spielende-Screen: Sieger anzeigen + Optionen."""
    Fenster.fill(BG)
    text_zentriert(f"{spieler_name(spiel['gewinner'])} gewinnt!", Schrift_gross, HOEHE // 2 - 80, GELB)
    text_zentriert("[Enter]  Nochmal spielen", Schrift_mittel, HOEHE // 2 + 20)
    text_zentriert("[Esc]    Beenden",          Schrift_mittel, HOEHE // 2 + 60)


# ═══════════════════════════════════════════════════════════════
#  Hauptschleife
# ═══════════════════════════════════════════════════════════════
# Läuft mit 60 FPS. Pro Frame:
#   1. KI-Schritt ausführen (zeitgesteuert, kein Tastendruck nötig)
#   2. Event-Queue verarbeiten (Tastatur, Maus, Fenster schließen)
#   3. Aktuellen Zustand rendern
#   4. Fertigen Frame anzeigen (double buffering via flip())

spiel_neu()   # Spiel im MENUE-Zustand starten

while True:

    jetzt = pygame.time.get_ticks()   # Millisekunden seit Programmstart

    # KI-Schritt VOR den Events – so reagiert die KI sofort wenn ihr Timer abläuft
    if spiel["zustand"] == KI_ZUG:
        ki_schritt(jetzt)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:

            if spiel["zustand"] == SCHIFFE_SETZEN:
                if event.key == pygame.K_r:
                    spiel["horizontal"] = not spiel["horizontal"]   # Ausrichtung umschalten
                elif event.key == pygame.K_ESCAPE:
                    spiel_neu()   # Zurück ins Menü

            elif spiel["zustand"] == WECHSEL:
                if event.key == pygame.K_RETURN:
                    wechsel_bestaetigt()

            elif spiel["zustand"] == SPIELEN:
                if event.key == pygame.K_ESCAPE:
                    spiel_neu()

            elif spiel["zustand"] == GAME_OVER:
                if event.key == pygame.K_RETURN:
                    spiel_neu()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if spiel["zustand"] == MENUE:
                btn_b, btn_h = 280, 50
                for Beschriftung, bx, by, aktion in menue_btns:
                    if bx <= event.pos[0] <= bx + btn_b and by <= event.pos[1] <= by + btn_h:
                        spiel_starten(aktion)

            elif spiel["zustand"] == SCHIFFE_SETZEN:
                zelle = maus_zu_gitter(*event.pos)
                if zelle:
                    schiff_platzieren(*zelle)

            elif spiel["zustand"] == SPIELEN:
                zelle = maus_zu_gitter(*event.pos)
                if zelle:
                    schiessen(*zelle)

    # Aktuellen Screen zeichnen
    if spiel["zustand"] == MENUE:           zeichne_menue()
    elif spiel["zustand"] == SCHIFFE_SETZEN: zeichne_schiffe_setzen()
    elif spiel["zustand"] == WECHSEL:        zeichne_wechsel_screen()
    elif spiel["zustand"] == SPIELEN:        zeichne_spielen()
    elif spiel["zustand"] == KI_ZUG:        zeichne_ki_zug()
    elif spiel["zustand"] == GAME_OVER:      zeichne_game_over()

    pygame.display.flip()   # Fertigen Frame in den sichtbaren Puffer tauschen
    clock.tick(60)          # Max. 60 FPS – verhindert unnötige CPU-Last
