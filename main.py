import pygame
import sys
from modelle import Spielfeld, Schiff, KI, FLOTTE, SCHIFF_NAMEN

# ── Fenster & Schriften ───────────────────────────────────────────────────────

pygame.init()

BREITE = 920
HOEHE  = 700
ZELL   = 58      # Größe einer Spielfeldzelle in Pixeln
RAND_L = 58      # Abstand des Spielfelds vom linken Rand
RAND_O = 58      # Abstand des Spielfelds vom oberen Rand

screen = pygame.display.set_mode((BREITE, HOEHE))
clock  = pygame.time.Clock()
pygame.display.set_caption("Schiffe Versenken")

font_gross  = pygame.font.SysFont("Arial", 36, bold=True)
font_mittel = pygame.font.SysFont("Arial", 22)
font_klein  = pygame.font.SysFont("Arial", 16)

# ── Texturen ─────────────────────────────────────────────

wasser_textur = pygame.image.load(
    "Modelle,Texturen/Wasser.png"
).convert()

schiff_texturen = {
    2: pygame.image.load(
        "Modelle,Texturen/Patrol Boat.png"
    ).convert_alpha(),

    3: pygame.image.load(
        "Modelle,Texturen/Destroyer.png"
    ).convert_alpha(),

    4: pygame.image.load(
        "Modelle,Texturen/Cruiser.png"
    ).convert_alpha(),

    5: pygame.image.load(
        "Modelle,Texturen/Battleship.png"
    ).convert_alpha(),
}

explosion_textur = pygame.image.load(
    "Modelle,Texturen/Explosion.png"
).convert_alpha()

splash_textur = pygame.image.load(
    "Modelle,Texturen/Splash.png"
).convert_alpha()

_textur_cache = {}

# ── Farben ────────────────────────────────────────────────────────────────────

BG        = (15,  25,  40)
WASSER_C  = (28,  95, 175)
SCHIFF_C  = (68,  72,  82)
TREFFER_C = (210, 55,  50)
MISS_C    = (148, 182, 208)
GITTER_C  = (20,  62, 125)
PANEL_BG  = (22,  38,  58)
WEISS     = (225, 235, 245)
GELB      = (248, 198,  48)
GRUEN     = (68,  158,  78)
ROT       = (198,  58,  52)
GRAU      = (100, 110, 120)
ORANGE    = (240, 140,  40)

# ── Spielzustände ─────────────────────────────────────────────────────────────
# Das Spiel ist immer in genau einem dieser Zustände (State Machine).
# Jeder Zustand bestimmt welcher Screen gezeichnet wird und welche Events
# verarbeitet werden. Übergänge finden nur in den Spiellogik-Funktionen statt.

MENUE          = "menue"
SCHIFFE_SETZEN = "schiffe_setzen"
WECHSEL        = "wechsel"    # Übergabe-Screen: verhindert dass Spieler 2 das Feld von Spieler 1 sieht
SPIELEN        = "spielen"
KI_DRAN        = "ki_dran"   # Eigener Zustand damit die KI-Animation nicht den Spieler blockiert
GAME_OVER      = "game_over"

KI_WARTE_MS = 1500   # Millisekunden bevor die KI schießt
KI_ZEIGE_MS = 700    # Millisekunden das Ergebnis anzeigen bevor weitergegangen wird

# ── Spielzustand ──────────────────────────────────────────────────────────────
# Alles was sich während des Spiels ändert steckt in diesem Dictionary.

# Zentrales Spielzustand-Dictionary: alle veränderlichen Spielvariablen an einem Ort.
# Kein globaler Zustand ist über mehrere Variablen verteilt – alles steckt hier drin.
# Das erleichtert Reset (spiel_neu()) und macht Abhängigkeiten zwischen Variablen sichtbar.
spiel = {}   # wird von spiel_neu() befüllt


def spiel_neu():
    """Alle Spielvariablen auf den Anfangszustand setzen."""
    global spiel
    spiel = {
        "zustand":          MENUE,
        "modus":            None,                    # "pve" oder "pvp"
        "felder":           [Spielfeld(), Spielfeld()],  # [Spieler1, Spieler2/KI]
        "aktiver":          0,                       # Wer schießt? 0=Spieler1, 1=Spieler2/KI
        "setup_spieler":    0,                       # Wer setzt gerade Schiffe?
        "schiff_idx":       0,                       # Index des nächsten Schiffs in FLOTTE
        "horizontal":       True,                    # Schiff waagerecht (True) oder senkrecht?
        "ki":               None,                    # KI-Objekt, nur im PvE-Modus
        "wechsel_text":     "",                      # Text auf dem Übergabe-Screen
        "wechsel_next":     "",                      # Was passiert nach Enter? ("setup2", "start", "zug")
        "letztes_ergebnis": "",                      # "wasser", "treffer" oder "versenkt"
        "gewinner":         None,                    # Index des Gewinners (0 oder 1)
        "ki_wartet":        True,                    # KI: wartet (True) oder zeigt Ergebnis (False)
        "ki_naechste_zeit": 0,                       # Zeitstempel (ms) wann der nächste KI-Schritt fällig ist
        "ki_schuss_xy":     None,                    # Position des letzten KI-Schusses für den orangenen Rahmen
    }


# ── Spiellogik ────────────────────────────────────────────────────────────────

def spieler_name(idx=None):
    """Gibt 'Spieler 1', 'Spieler 2' oder 'KI' zurück."""
    # Ohne Argument: Name des aktuell aktiven Spielers. Mit Argument: beliebiger Index.
    i = spiel["aktiver"] if idx is None else idx
    if spiel["modus"] == "pve" and i == 1:
        return "KI"
    return f"Spieler {i + 1}"


def spiel_starten(modus):
    """Spiel im gewählten Modus starten und Schiffe-Setzen beginnen."""
    spiel["modus"]         = modus
    spiel["setup_spieler"] = 0
    spiel["schiff_idx"]    = 0
    spiel["horizontal"]    = True
    spiel["zustand"]       = SCHIFFE_SETZEN


def schiff_platzieren(gx, gy):
    """Nächstes Schiff auf Gitter-Position (gx, gy) setzen."""
    schiff = Schiff(FLOTTE[spiel["schiff_idx"]])
    feld   = spiel["felder"][spiel["setup_spieler"]]

    if feld.platzieren(schiff, gx, gy, spiel["horizontal"]):
        spiel["schiff_idx"] += 1

        if spiel["schiff_idx"] >= len(FLOTTE):
            alle_schiffe_gesetzt()


def alle_schiffe_gesetzt():
    """Wird aufgerufen wenn ein Spieler alle Schiffe platziert hat."""
    if spiel["modus"] == "pvp" and spiel["setup_spieler"] == 0:
        # PvP: Spieler 2 muss noch Schiffe setzen
        zeige_wechsel(
            "Spieler 1 ist fertig.\n\nSpieler 2, bitte übernehmen.\n\n[Enter] drücken",
            naechstes="setup2"
        )
    else:
        spiel_beginnen()


def spiel_beginnen():
    """Alle Schiffe sind gesetzt – das Spiel startet."""
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
    """Aktiver Spieler schießt auf Gitter-Position (gx, gy) des Gegners."""
    # "1 - aktiver" ist das elegante Muster um zwischen Index 0 und 1 zu wechseln
    gegner_feld = spiel["felder"][1 - spiel["aktiver"]]
    ergebnis    = gegner_feld.schiessen(gx, gy)

    if ergebnis is None:
        return   # Bereits beschossen – ignorieren (modelle.py gibt None zurück)

    spiel["letztes_ergebnis"] = ergebnis

    if gegner_feld.alle_versenkt():
        spiel["gewinner"] = spiel["aktiver"]
        spiel["zustand"]  = GAME_OVER
        return

    if ergebnis == "wasser":
        spieler_wechseln()
    # Bei Treffer: Zustand bleibt SPIELEN → gleicher Spieler darf nochmal schießen


def spieler_wechseln():
    """Fehlschuss → zum nächsten Spieler wechseln."""
    if spiel["modus"] == "pvp":
        naechster = 1 - spiel["aktiver"]
        zeige_wechsel(
            f"{spieler_name(naechster)}, du bist dran!\n\nBitte übernehmen.\n\n[Enter] drücken",
            naechstes="zug"
        )
    else:
        ki_zug_starten()


def ki_zug_starten():
    """KI-Zug einleiten – wechselt in den KI_DRAN-Zustand."""
    # Durch den eigenen Zustand KI_DRAN kann die Hauptschleife weiter mit 60 FPS laufen
    # während die KI zeitgesteuert (nicht mit sleep()) auf ihren Zug wartet.
    spiel["ki_schuss_xy"]     = None
    spiel["ki_wartet"]        = True
    spiel["ki_naechste_zeit"] = pygame.time.get_ticks() + KI_WARTE_MS
    spiel["zustand"]          = KI_DRAN


def ki_schritt(jetzt):
    """
    KI-Zug animiert ausführen. Wird jeden Frame aufgerufen wenn KI dran ist.

    Phase 1 (ki_wartet=True):  KI wartet kurz, dann schießt sie.
    Phase 2 (ki_wartet=False): Ergebnis kurz anzeigen, dann weiter.

    Zwei Phasen statt einer: der Spieler soll erst die Denkpause sehen (Phase 1),
    dann das Ergebnis lesen können (Phase 2), bevor das Spiel weitergeht.
    """
    if jetzt < spiel["ki_naechste_zeit"]:
        return   # Timer läuft noch – nichts tun, nächster Frame übernimmt

    if spiel["ki_wartet"]:
        # Phase 1: KI schießt – while-Schleife überspringt bereits beschossene Felder
        # (kann passieren wenn die KI-Liste durch einen Bug doppelte Einträge hätte)
        while spiel["ki"].kandidaten:
            x, y     = spiel["ki"].naechster_schuss()
            ergebnis = spiel["felder"][0].schiessen(x, y)
            if ergebnis is not None:
                break
        else:
            return   # Keine Felder mehr übrig (sollte nie passieren)

        spiel["ki_schuss_xy"]     = (x, y)
        spiel["letztes_ergebnis"] = f"KI: {ergebnis}"
        spiel["ki_wartet"]        = False
        spiel["ki_naechste_zeit"] = jetzt + KI_ZEIGE_MS

    else:
        # Phase 2: Ergebnis auswerten
        er = spiel["letztes_ergebnis"]

        if spiel["felder"][0].alle_versenkt():
            spiel["gewinner"] = 1
            spiel["zustand"]  = GAME_OVER
        elif "wasser" in er:
            # KI hat verfehlt → Spieler ist wieder dran
            spiel["ki_schuss_xy"]     = None
            spiel["letztes_ergebnis"] = ""
            spiel["zustand"]          = SPIELEN
        else:
            # KI hat getroffen → nochmal schießen
            spiel["ki_wartet"]        = True
            spiel["ki_schuss_xy"]     = None
            spiel["ki_naechste_zeit"] = jetzt + KI_WARTE_MS


def zeige_wechsel(text, naechstes):
    """Wechsel-Screen aktivieren: Text anzeigen, auf Enter warten."""
    spiel["wechsel_text"] = text
    spiel["wechsel_next"] = naechstes
    spiel["zustand"]      = WECHSEL


def wechsel_bestaetigt():
    """Enter auf dem Wechsel-Screen wurde gedrückt."""
    if spiel["wechsel_next"] == "setup2":
        # Spieler 2 setzt jetzt Schiffe
        spiel["setup_spieler"] = 1
        spiel["schiff_idx"]    = 0
        spiel["horizontal"]    = True
        spiel["zustand"]       = SCHIFFE_SETZEN
    elif spiel["wechsel_next"] in ("start", "zug"):
        if spiel["wechsel_next"] == "zug":
            spiel["aktiver"] = 1 - spiel["aktiver"]   # Spieler wechseln
        spiel["letztes_ergebnis"] = ""
        spiel["zustand"]          = SPIELEN


# ── Zeichenhilfsfunktionen ────────────────────────────────────────────────────

def gitter_zu_pixel(gx, gy):
    """Gitter-Koordinate (0-9) → Pixel-Koordinate (obere linke Ecke der Zelle)."""
    return RAND_L + gx * ZELL, RAND_O + gy * ZELL


def maus_zu_gitter(px, py):
    """Mausposition in Pixeln → Gitter-Koordinate, oder None wenn außerhalb."""
    # Umkehrung von gitter_zu_pixel: Offset abziehen, dann durch Zellgröße teilen
    gx = (px - RAND_L) // ZELL
    gy = (py - RAND_O) // ZELL
    if 0 <= gx < 10 and 0 <= gy < 10:
        return gx, gy
    return None   # Maus ist außerhalb des Spielfelds → kein gültiger Klick


def text_zentriert(text, font, y, farbe=WEISS):
    """Text horizontal zentriert auf Höhe y zeichnen."""
    surf = font.render(text, True, farbe)
    screen.blit(surf, (BREITE // 2 - surf.get_width() // 2, y))


def skalierte_textur(textur, breite, hoehe):
    """
    Textur nur einmal skalieren und anschließend aus Cache laden.
    """
    key = (id(textur), breite, hoehe)

    if key not in _textur_cache:
        _textur_cache[key] = pygame.transform.scale(
            textur,
            (breite, hoehe)
        )

    return _textur_cache[key]


# ── Zeichenfunktionen ─────────────────────────────────────────────────────────

def zeichne_schiff_modell(schiff):
    """
    Zeichnet ein Schiff als zusammenhängendes Modell.
    """

    if not schiff.felder:
        return

    textur = schiff_texturen.get(schiff.groesse)

    if textur is None:
        return

    felder_sortiert = sorted(schiff.felder)

    gx0, gy0 = felder_sortiert[0]
    px, py   = gitter_zu_pixel(gx0, gy0)

    horizontal = len({x for x, y in schiff.felder}) > 1

    if horizontal:

        breite = schiff.groesse * ZELL - 1
        hoehe  = ZELL - 1

        bild = skalierte_textur(
            textur,
            breite,
            hoehe
        )

    else:

        breite = ZELL - 1
        hoehe  = schiff.groesse * ZELL - 1

        basis = skalierte_textur(
            textur,
            hoehe,
            breite
        )

        key = (id(textur), breite, hoehe, "rot")

        if key not in _textur_cache:
            _textur_cache[key] = pygame.transform.rotate(
                basis,
                -90
            )

        bild = _textur_cache[key]

    screen.blit(bild, (px, py))



def zeichne_spielfeld(feld, verdeckt=False, vorschau=None, vorschau_ok=True, highlight=None):
    """
    10x10 Spielfeld zeichnen.

    feld       – das Spielfeld-Objekt
    verdeckt   – True = Schiffe verstecken (Angriffsmodus, d.h. Spieler schaut auf Gegnergitter)
    vorschau   – Liste von Zellen die als Platzierungsvorschau eingefärbt werden
    vorschau_ok– True = grüne Vorschau (Platzierung möglich), False = rote (ungültig)
    highlight  – Zelle die orange eingerahmt wird (letzter KI-Schuss)
    """
    # Zellen zeichnen
    grid_b = 10 * ZELL
    grid_h = 10 * ZELL

    wasser = skalierte_textur(
        wasser_textur,
        grid_b,
        grid_h
    )

    screen.blit(
        wasser,
        (RAND_L, RAND_O)
    )
    

    if not verdeckt:
        for schiff in feld.schiffe:
            zeichne_schiff_modell(schiff)
        
    
    # Treffer/Fehlschuss-Texturen auf jede Zelle zeichnen
    for gy in range(10):
        for gx in range(10):
            px, py = gitter_zu_pixel(gx, gy)
            wert   = feld.raster[gy][gx]

            if wert == 2:   # Fehlschuss → Splash-Textur
                overlay = skalierte_textur(splash_textur, ZELL - 1, ZELL - 1)
                screen.blit(overlay, (px, py))
            elif wert == 3:  # Treffer → Explosions-Textur
                overlay = skalierte_textur(explosion_textur, ZELL - 1, ZELL - 1)
                screen.blit(overlay, (px, py))

    # Versenkte Schiffe auch im Angriffsmodus aufdecken – Spielregel: versenktes Schiff wird sichtbar
    if verdeckt:
        for schiff in feld.schiffe:

            if schiff.versenkt:

                zeichne_schiff_modell(schiff)

                for gx, gy in schiff.felder:

                    px, py = gitter_zu_pixel(gx, gy)

                    overlay = skalierte_textur(
                        explosion_textur,
                        ZELL - 1,
                        ZELL - 1
                    )

                    screen.blit(
                        overlay,
                        (px, py)
                    )

    # Letzter KI-Schuss orange einrahmen damit der Spieler sieht wohin die KI geschossen hat
    if highlight:
        gx, gy = highlight
        px, py = gitter_zu_pixel(gx, gy)
        pygame.draw.rect(screen, ORANGE, (px - 2, py - 2, ZELL + 1, ZELL + 1), 3)

    # Platzierungsvorschau mit Transparenz: SRCALPHA-Surface ermöglicht Alpha-Kanal (130 von 255)
    if vorschau:
        alpha = (68, 158, 78, 130) if vorschau_ok else (198, 58, 52, 130)
        s = pygame.Surface((ZELL - 1, ZELL - 1), pygame.SRCALPHA)
        s.fill(alpha)
        for gx, gy in vorschau:
            if 0 <= gx < 10 and 0 <= gy < 10:   # Vorschau-Zellen außerhalb des Rasters ignorieren
                screen.blit(s, gitter_zu_pixel(gx, gy))

    # Gitternetz
    for i in range(11):
        x = RAND_L + i * ZELL
        y = RAND_O + i * ZELL
        pygame.draw.line(screen, GITTER_C, (x, RAND_O), (x, RAND_O + 10 * ZELL))
        pygame.draw.line(screen, GITTER_C, (RAND_L, y), (RAND_L + 10 * ZELL, y))

    # Achsenbeschriftung: A-J oben, 1-10 links
    for i, buchstabe in enumerate("ABCDEFGHIJ"):
        t  = font_klein.render(buchstabe, True, WEISS)
        px = RAND_L + i * ZELL + ZELL // 2 - t.get_width() // 2
        screen.blit(t, (px, RAND_O - t.get_height() - 4))
    for i in range(10):
        t  = font_klein.render(str(i + 1), True, WEISS)
        py = RAND_O + i * ZELL + ZELL // 2 - t.get_height() // 2
        screen.blit(t, (RAND_L - t.get_width() - 6, py))


def zeichne_panel(zeilen):
    """
    Rechtes Infopanel zeichnen.
    zeilen = Liste von (text, farbe). Text "---" zeichnet eine Trennlinie.

    Das Panel wird von den Screen-Funktionen befüllt – jede baut ihre eigene
    Zeilen-Liste und übergibt sie hier. Dadurch liegt das Layout-Wissen in
    den Screen-Funktionen, nicht hier.
    """
    panel_x = BREITE - 210
    # Hintergrund des Panels als gefülltes Rechteck – überdeckt alles was darunter liegt
    pygame.draw.rect(screen, PANEL_BG, (panel_x - 8, 0, BREITE - panel_x + 8, HOEHE))

    y = 20
    for text, farbe in zeilen:
        if text == "---":
            pygame.draw.line(screen, GITTER_C, (panel_x, y + 5), (BREITE - 10, y + 5))
            y += 18
        else:
            t = font_mittel.render(text, True, farbe)
            screen.blit(t, (panel_x, y))
            y += t.get_height() + 6


# ── Screen-Funktionen ─────────────────────────────────────────────────────────

# Button-Positionen werden pro Frame in zeichne_menue() berechnet und hier gespeichert,
# damit die Event-Verarbeitung (Mausklick) auf dieselben Koordinaten zugreifen kann.
menue_btns = []


def zeichne_menue():
    """Hauptmenü zeichnen: Titel + zwei Buttons."""
    global menue_btns
    screen.fill(BG)

    text_zentriert("SCHIFFE VERSENKEN", font_gross, HOEHE // 5, GELB)

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
    for label, bx, by, _ in menue_btns:
        hover = bx <= maus[0] <= bx + btn_b and by <= maus[1] <= by + btn_h
        pygame.draw.rect(screen, GELB if hover else WEISS, (bx, by, btn_b, btn_h), border_radius=6)
        t = font_mittel.render(label, True, BG)
        screen.blit(t, (bx + btn_b // 2 - t.get_width() // 2, by + btn_h // 2 - t.get_height() // 2))


def zeichne_schiffe_setzen():
    """Schiffe-Setzen-Screen: Spielfeld mit Vorschau + Panel mit Schiffsliste."""
    screen.fill(BG)

    groesse  = FLOTTE[spiel["schiff_idx"]]
    sp_name  = f"Spieler {spiel['setup_spieler'] + 1}"
    richtung = "Horizontal" if spiel["horizontal"] else "Vertikal"

    # Vorschau berechnen: welche Zellen würde das Schiff an der aktuellen Mausposition belegen?
    # ok=False wenn eine Zelle außerhalb des Rasters oder bereits belegt ist → rote Vorschau
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
            if not (0 <= fx < 10 and 0 <= fy < 10):
                ok = False
            elif spiel["felder"][spiel["setup_spieler"]].raster[fy][fx] == 1:
                ok = False

    zeichne_spielfeld(spiel["felder"][spiel["setup_spieler"]], vorschau=vorschau, vorschau_ok=ok)

    info = [
        (f"{sp_name} setzt Schiffe", GELB),
        ("---", WEISS),
        (f"Schiff: {SCHIFF_NAMEN[groesse]} ({groesse})", WEISS),
        (f"[R] Drehen: {richtung}", WEISS),
        ("---", WEISS),
        ("Flotte:", WEISS),
    ]
    for i, g in enumerate(FLOTTE):
        if i < spiel["schiff_idx"]:
            info.append((f" ✓ {SCHIFF_NAMEN[g]} ({g})", GRUEN))
        elif i == spiel["schiff_idx"]:
            info.append((f" → {SCHIFF_NAMEN[g]} ({g})", GELB))
        else:
            info.append((f"   {SCHIFF_NAMEN[g]} ({g})", GRAU))
    info += [("---", WEISS), ("[Esc] Menü", GRAU)]
    zeichne_panel(info)


def zeichne_wechsel_screen():
    """Übergabe-Screen: zentrierter Text, wartet auf Enter."""
    screen.fill(BG)
    zeilen = spiel["wechsel_text"].split("\n")
    zeil_h = font_mittel.get_height() + 10
    y      = HOEHE // 2 - len(zeilen) * zeil_h // 2
    for zeile in zeilen:
        text_zentriert(zeile, font_mittel, y)
        y += zeil_h


def zeichne_spielen():
    """Spielscreen: Angriffsgitter des Gegners – Spieler schießt hier drauf."""
    screen.fill(BG)
    zeichne_spielfeld(spiel["felder"][1 - spiel["aktiver"]], verdeckt=True)

    eigene_schiffe = spiel["felder"][spiel["aktiver"]].schiffe
    gegner_schiffe = spiel["felder"][1 - spiel["aktiver"]].schiffe
    lebend         = sum(1 for s in eigene_schiffe if not s.versenkt)
    versenkt       = sum(1 for s in gegner_schiffe if s.versenkt)

    er = spiel["letztes_ergebnis"]
    if "versenkt" in er:  er_farbe = ROT
    elif "treffer" in er: er_farbe = GELB
    elif "wasser" in er:  er_farbe = MISS_C
    else:                 er_farbe = WEISS

    info = [
        (f"{spieler_name()} greift an", GELB),
        ("---", WEISS),
        (f"Deine Flotte: {lebend}/{len(eigene_schiffe)}", GRUEN if lebend > 0 else ROT),
        (f"Gegner versenkt: {versenkt}/{len(gegner_schiffe)}", GELB),
        ("---", WEISS),
        ("Letzter Schuss:", WEISS),
        (f"  {er.upper() if er else '-'}", er_farbe),
        ("---", WEISS),
        ("[Esc] Menü", GRAU),
    ]
    zeichne_panel(info)


def zeichne_ki_dran():
    """KI-Zug-Screen: eigenes Spielfeld, Spieler sieht wie KI schießt."""
    screen.fill(BG)
    zeichne_spielfeld(spiel["felder"][0], verdeckt=False, highlight=spiel["ki_schuss_xy"])

    # Statuszeile über dem Spielfeld
    if spiel["ki_wartet"]:
        header, h_farbe = "KI denkt nach...", GRAU
    else:
        er = spiel["letztes_ergebnis"]
        if "versenkt" in er:  header, h_farbe = "KI versenkt dein Schiff!", ROT
        elif "treffer" in er: header, h_farbe = "KI: TREFFER!", ORANGE
        else:                 header, h_farbe = "KI: Fehlschuss!", MISS_C

    t = font_mittel.render(header, True, h_farbe)
    screen.blit(t, (RAND_L, max(4, RAND_O // 2 - t.get_height() // 2)))

    eigene = spiel["felder"][0].schiffe
    lebend = sum(1 for s in eigene if not s.versenkt)
    er     = spiel["letztes_ergebnis"]
    er_text= er.replace("KI: ", "").upper() if er else "..."

    if "versenkt" in er:  er_farbe = ROT
    elif "treffer" in er: er_farbe = ORANGE
    elif "wasser" in er:  er_farbe = MISS_C
    else:                 er_farbe = GRAU

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
    """Spielende-Screen: Gewinner anzeigen, Optionen zum Neustart."""
    screen.fill(BG)
    name = spieler_name(spiel["gewinner"])
    text_zentriert(f"{name} gewinnt!", font_gross, HOEHE // 2 - 80, GELB)
    text_zentriert("[Enter]  Nochmal spielen", font_mittel, HOEHE // 2 + 20)
    text_zentriert("[Esc]    Beenden",          font_mittel, HOEHE // 2 + 60)


# ── Hauptschleife ─────────────────────────────────────────────────────────────
# Das Spiel läuft als Endlosschleife mit 60 Frames pro Sekunde.
# Reihenfolge pro Frame: KI-Logik → Events → Zeichnen → flip()
# flip() tauscht den fertigen Frame in den sichtbaren Puffer (double buffering).

spiel_neu()   # Spiel direkt im MENUE-Zustand starten

while True:

    jetzt = pygame.time.get_ticks()   # Millisekunden seit Programmstart (für KI-Timer)

    # KI-Schritt VOR den Events ausführen: so reagiert die KI sofort wenn ihr Timer abläuft,
    # unabhängig davon ob der Spieler gerade eine Taste drückt.
    if spiel["zustand"] == KI_DRAN:
        ki_schritt(jetzt)

    # pygame sammelt alle Eingaben seit dem letzten Frame in einer Event-Queue.
    # get() leert die Queue und gibt eine Liste zurück – wir gehen jeden Event durch.
    for event in pygame.event.get():

        # QUIT tritt auf wenn der Nutzer das Fenster schließt (X-Button)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # KEYDOWN = eine Taste wurde gedrückt (nicht gehalten).
        # pygame.K_r, pygame.K_RETURN usw. sind Konstanten für einzelne Tasten –
        # K_RETURN ist die Enter-Taste, K_ESCAPE ist Esc, K_r ist die Taste "R".
        elif event.type == pygame.KEYDOWN:

            if spiel["zustand"] == SCHIFFE_SETZEN:
                if event.key == pygame.K_r:         # R → Ausrichtung umschalten
                    spiel["horizontal"] = not spiel["horizontal"]
                elif event.key == pygame.K_ESCAPE:  # Esc → zurück ins Menü
                    spiel_neu()

            elif spiel["zustand"] == WECHSEL:
                if event.key == pygame.K_RETURN:    # Enter → Übergabe bestätigen
                    wechsel_bestaetigt()

            elif spiel["zustand"] == SPIELEN:
                if event.key == pygame.K_ESCAPE:    # Esc → Spiel abbrechen
                    spiel_neu()

            elif spiel["zustand"] == GAME_OVER:
                if event.key == pygame.K_RETURN:    # Enter → nochmal spielen
                    spiel_neu()
                elif event.key == pygame.K_ESCAPE:  # Esc → Programm beenden
                    pygame.quit()
                    sys.exit()

        # MOUSEBUTTONDOWN = Maustaste gedrückt. event.button == 1 heißt: linke Maustaste.
        # (2 = mittlere, 3 = rechte Maustaste – die ignorieren wir hier)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if spiel["zustand"] == MENUE:
                btn_b, btn_h = 280, 50   # Breite und Höhe der Buttons (gleich wie in zeichne_menue)

                # menue_btns ist eine Liste mit einem Eintrag pro Button.
                # Jeder Eintrag hat 4 Werte: (label, bx, by, aktion)
                #   label  = Beschriftung (wird hier nicht gebraucht, nur zum Entpacken)
                #   bx, by = Pixel-Position der oberen linken Ecke des Buttons
                #   aktion = "pve" oder "pvp" – wird an spiel_starten() übergeben
                for label, bx, by, aktion in menue_btns:
                    # Prüfen ob der Klick (event.pos[0]=x, event.pos[1]=y) innerhalb des Buttons liegt
                    if bx <= event.pos[0] <= bx + btn_b and by <= event.pos[1] <= by + btn_h:
                        spiel_starten(aktion)

            elif spiel["zustand"] == SCHIFFE_SETZEN:
                # *event.pos entpackt das Tupel (x, y) als zwei einzelne Argumente –
                # dasselbe wie: maus_zu_gitter(event.pos[0], event.pos[1])
                zelle = maus_zu_gitter(*event.pos)
                if zelle:   # None wenn außerhalb des Spielfelds geklickt
                    schiff_platzieren(*zelle)

            elif spiel["zustand"] == SPIELEN:
                zelle = maus_zu_gitter(*event.pos)
                if zelle:
                    schiessen(*zelle)

    # Aktuellen Screen zeichnen
    if spiel["zustand"] == MENUE:
        zeichne_menue()
    elif spiel["zustand"] == SCHIFFE_SETZEN:
        zeichne_schiffe_setzen()
    elif spiel["zustand"] == WECHSEL:
        zeichne_wechsel_screen()
    elif spiel["zustand"] == SPIELEN:
        zeichne_spielen()
    elif spiel["zustand"] == KI_DRAN:
        zeichne_ki_dran()
    elif spiel["zustand"] == GAME_OVER:
        zeichne_game_over()

    pygame.display.flip()   # fertigen Frame in den sichtbaren Puffer tauschen
    clock.tick(60)          # max. 60 FPS – verhindert 100% CPU-Auslastung
