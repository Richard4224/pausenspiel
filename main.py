import pygame
import sys

BREITE  = 800
HOEHE   = 800
FPS     = 30
TITEL   = "Schiffe Versenken"

# Farben (Platzhalter – später anpassen)
FARBE_HINTERGRUND = (15, 25, 50)
FARBE_TEXT        = (255, 255, 255)
FARBE_BUTTON      = (30, 80, 160)
FARBE_BUTTON_HOV  = (50, 120, 220)
FARBE_BUTTON_TEXT = (255, 255, 255)
FARBE_HINWEIS     = (160, 180, 210)


# ─────────────────────────────────────────────
#  SPIELZUSTÄNDE
# ─────────────────────────────────────────────
# Das Spiel befindet sich immer in genau einem dieser Zustände.
# Der Zustand bestimmt welcher Screen angezeigt wird und was
# als nächstes passiert.

ZUSTAND_HAUPTMENU      = "hauptmenu"
ZUSTAND_SCHIFFE_SETZEN = "schiffe_setzen"
ZUSTAND_SPIELERWECHSEL = "spielerwechsel"
ZUSTAND_AM_ZUG         = "am_zug"
ZUSTAND_SPIELENDE      = "spielende"


# ─────────────────────────────────────────────
#  INITIALISIERUNG
# ─────────────────────────────────────────────
def init():
    """Pygame initialisieren und Fenster erstellen."""
    pygame.init()
    screen = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption(TITEL)
    clock = pygame.time.Clock()
    return screen, clock


# ─────────────────────────────────────────────
#  HILFSFUNKTIONEN
# ─────────────────────────────────────────────
def lade_schriften():
    """Alle Schriftarten laden und zurückgeben."""
    return {
        "titel":  pygame.font.SysFont("Arial", 64, bold=True),
        "button": pygame.font.SysFont("Arial", 32),
        "mittel": pygame.font.SysFont("Arial", 28),
        "klein":  pygame.font.SysFont("Arial", 20),
    }


def zeichne_button(screen, schriften, text, rect, maus_pos):
    """
    Einen einzelnen Button zeichnen.
    Gibt True zurück, wenn die Maus darüber ist (Hover-State).
    """
    hover = rect.collidepoint(maus_pos)
    farbe = FARBE_BUTTON_HOV if hover else FARBE_BUTTON
    pygame.draw.rect(screen, farbe, rect, border_radius=8)

    label = schriften["button"].render(text, True, FARBE_BUTTON_TEXT)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

    return hover


def zeichne_text_zentriert(screen, schriften, text, groesse, y, farbe=None):
    """
    Text horizontal zentriert auf einer bestimmten Y-Position zeichnen.
    groesse: "titel" | "mittel" | "button" | "klein"
    """
    if farbe is None:
        farbe = FARBE_TEXT
    surf = schriften[groesse].render(text, True, farbe)
    rect = surf.get_rect(center=(BREITE // 2, y))
    screen.blit(surf, rect)


def verarbeite_events():
    """
    Globale Events verarbeiten (Fenster schließen).
    Gibt eine Liste aller Events zurück, damit jeder Screen
    selbst entscheiden kann was er damit macht.
    """
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    return events


# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────

def zeige_hauptmenu(screen, clock, schriften):
    """
    Hauptmenü anzeigen und auf Benutzereingabe warten.
    Gibt den gewählten Modus zurück: 'einzelspieler' | 'mehrspieler'
    """
    btn_breite, btn_hoehe = 280, 55
    btn_x = BREITE // 2 - btn_breite // 2

    buttons = {
        "einzelspieler": pygame.Rect(btn_x, 280, btn_breite, btn_hoehe),
        "mehrspieler":   pygame.Rect(btn_x, 360, btn_breite, btn_hoehe),
        "beenden":       pygame.Rect(btn_x, 440, btn_breite, btn_hoehe),
    }

    while True:
        maus_pos = pygame.mouse.get_pos()
        events   = verarbeite_events()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for aktion, rect in buttons.items():
                    if rect.collidepoint(maus_pos):
                        if aktion == "beenden":
                            pygame.quit()
                            sys.exit()
                        return aktion

        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
        zeichne_text_zentriert(screen, schriften, TITEL, "titel", 140)

        zeichne_button(screen, schriften, "Einzelspieler", buttons["einzelspieler"], maus_pos)
        zeichne_button(screen, schriften, "Mehrspieler",   buttons["mehrspieler"],   maus_pos)
        zeichne_button(screen, schriften, "Beenden",       buttons["beenden"],       maus_pos)

        pygame.display.flip()
        clock.tick(FPS)


def zeige_schiffe_setzen(screen, clock, schriften, spieler_nr):
    """
    Platzhalter-Screen: Spieler setzt seine Schiffe.

    Dieser Screen wird später vom Feature 'Schiffsplatzierung' befüllt.
    Im Moment zeigt er nur einen Hinweis und wartet auf Enter.

    Args:
        spieler_nr – 1 oder 2, wird im Titel angezeigt
    """
    while True:
        events = verarbeite_events()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return  # Platzierung abgeschlossen → zurück zum Controller

        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
        zeichne_text_zentriert(screen, schriften, f"Spieler {spieler_nr}: Schiffe setzen", "titel", 180)

        # Platzhalter-Hinweis
        zeichne_text_zentriert(screen, schriften, "[ Hier kommt das Spielfeld ]", "mittel", 340, FARBE_HINWEIS)
        zeichne_text_zentriert(screen, schriften, "Enter → weiter", "klein", 420, FARBE_HINWEIS)

        pygame.display.flip()
        clock.tick(FPS)


def zeige_spielerwechsel(screen, clock, schriften, naechster_spieler):
    """
    Übergabe-Screen: Verhindert dass ein Spieler das Brett des anderen sieht.

    Zeigt eine Aufforderung an den nächsten Spieler zu übernehmen.
    Erst nach Enter wird weitergegangen.

    Args:
        naechster_spieler – 1 oder 2
    """
    while True:
        events = verarbeite_events()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return  # Spieler hat bestätigt

        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
        zeichne_text_zentriert(screen, schriften, f"Spieler {naechster_spieler}", "titel", 240)
        zeichne_text_zentriert(screen, schriften, "bitte übernehmen!", "button", 320)
        zeichne_text_zentriert(screen, schriften, "Enter → weiter", "klein", 420, FARBE_HINWEIS)

        pygame.display.flip()
        clock.tick(FPS)


def zeige_am_zug(screen, clock, schriften, spieler_nr, modus):
    """
    Platzhalter-Screen: Aktiver Spieler macht seinen Zug (schießt).

    Dieser Screen wird später vom Feature 'Spielfeld & Schuss-Logik' befüllt.
    Im Moment gibt er immer 'wasser' zurück damit der Spielfluss getestet
    werden kann.

    Args:
        spieler_nr – 1 oder 2 (bzw. 'KI' im Einzelspieler-Modus)
        modus      – 'einzelspieler' | 'mehrspieler'

    Returns:
        ergebnis   – 'wasser' | 'treffer' | 'versenkt' | 'alle_versenkt'
    """
    name = "KI" if (modus == "einzelspieler" and spieler_nr == 2) else f"Spieler {spieler_nr}"

    while True:
        events = verarbeite_events()

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Platzhalter-Steuerung zum Testen des Spielflusses:
                # T → Treffer simulieren
                # V → Versenkt simulieren
                # A → Alle versenkt (Spielende) simulieren
                # Enter / Leertaste → Fehlschuss (Wasser)
                if event.key == pygame.K_t:
                    return "treffer"
                if event.key == pygame.K_v:
                    return "versenkt"
                if event.key == pygame.K_a:
                    return "alle_versenkt"
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "wasser"

        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
        zeichne_text_zentriert(screen, schriften, f"{name} ist am Zug", "titel", 180)

        zeichne_text_zentriert(screen, schriften, "[ Hier kommt das Spielfeld ]", "mittel", 340, FARBE_HINWEIS)

        # Hinweis zu den Platzhalter-Tasten
        zeichne_text_zentriert(screen, schriften, "Enter → Fehlschuss  |  T → Treffer", "klein", 430, FARBE_HINWEIS)
        zeichne_text_zentriert(screen, schriften, "V → Versenkt  |  A → Alle versenkt", "klein", 460, FARBE_HINWEIS)

        pygame.display.flip()
        clock.tick(FPS)


def zeige_spielende(screen, clock, schriften, gewinner_name):
    """
    Spielende-Screen: Zeigt den Gewinner und gibt Optionen zum Neustart.

    Returns:
        'neustart' | 'hauptmenu'
    """
    btn_breite, btn_hoehe = 260, 50
    btn_x = BREITE // 2 - btn_breite // 2

    buttons = {
        "neustart":   pygame.Rect(btn_x, 420, btn_breite, btn_hoehe),
        "hauptmenu":  pygame.Rect(btn_x, 490, btn_breite, btn_hoehe),
    }

    while True:
        maus_pos = pygame.mouse.get_pos()
        events   = verarbeite_events()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for aktion, rect in buttons.items():
                    if rect.collidepoint(maus_pos):
                        return aktion

        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
        zeichne_text_zentriert(screen, schriften, "Spiel beendet!", "titel",  200)
        zeichne_text_zentriert(screen, schriften, f"{gewinner_name} gewinnt!", "button", 290)

        zeichne_button(screen, schriften, "Nochmal spielen", buttons["neustart"],  maus_pos)
        zeichne_button(screen, schriften, "Hauptmenü",       buttons["hauptmenu"], maus_pos)

        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────
#  RUNDENLOGIK & SPIELFLUSS-CONTROLLER
# ─────────────────────────────────────────────

def runden_controller(screen, clock, schriften, modus):
    """
    Steuert den kompletten Ablauf einer Partie vom ersten Schiff-Setzen
    bis zum Spielende.

    Spielablauf:
        1. Spieler 1 setzt Schiffe
        2. (PvP) Übergabe-Screen → Spieler 2 setzt Schiffe
        3. (PvP) Übergabe-Screen → Spieler 1 beginnt
        4. Rundenloop:
              - Aktiver Spieler macht Zug
              - Treffer → gleicher Spieler nochmal
              - Fehlschuss → (PvP) Übergabe-Screen → Gegner dran
              - Alle Schiffe versenkt → Spielende

    Args:
        modus – 'einzelspieler' | 'mehrspieler'

    Returns:
        'neustart'   – direkt neues Spiel im selben Modus starten
        'hauptmenu'  – zurück ins Hauptmenü
    """

    # ── Phase 1: Schiffe setzen ────────────────────────────────
    zeige_schiffe_setzen(screen, clock, schriften, spieler_nr=1)

    if modus == "mehrspieler":
        # Spieler 1 darf nicht sehen was Spieler 2 platziert
        zeige_spielerwechsel(screen, clock, schriften, naechster_spieler=2)
        zeige_schiffe_setzen(screen, clock, schriften, spieler_nr=2)
        # Kurze Übergabe bevor das Spiel startet
        zeige_spielerwechsel(screen, clock, schriften, naechster_spieler=1)

    # Im Einzelspieler-Modus setzt die KI ihre Schiffe automatisch (kein Screen nötig).
    # Das wird später hier aufgerufen: ki.schiffe_zufaellig_setzen()

    # ── Phase 2: Rundenloop ────────────────────────────────────
    # aktiver_spieler: 1 = Spieler 1 (oder Mensch im PvE)
    #                  2 = Spieler 2 (oder KI im PvE)
    aktiver_spieler = 1

    while True:
        ergebnis = zeige_am_zug(screen, clock, schriften, aktiver_spieler, modus)

        if ergebnis == "alle_versenkt":
            # Aktiver Spieler hat gewonnen – alle gegnerischen Schiffe sind versenkt
            if modus == "einzelspieler" and aktiver_spieler == 2:
                gewinner_name = "KI"
            else:
                gewinner_name = f"Spieler {aktiver_spieler}"

            aktion = zeige_spielende(screen, clock, schriften, gewinner_name)
            return aktion  # 'neustart' oder 'hauptmenu'

        elif ergebnis in ("treffer", "versenkt"):
            # Treffer → gleicher Spieler darf nochmal schießen, kein Wechsel
            pass

        else:
            # Fehlschuss (wasser) → Spieler wechseln
            aktiver_spieler = 2 if aktiver_spieler == 1 else 1

            if modus == "mehrspieler":
                # Übergabe-Screen damit der andere Spieler das Brett nicht sieht
                zeige_spielerwechsel(screen, clock, schriften, aktiver_spieler)

            # Im Einzelspieler-Modus: wenn jetzt die KI dran ist, läuft sie
            # direkt durch (kein Übergabe-Screen nötig, kein Klick nötig).
            # Später wird hier ki.naechster_schuss() aufgerufen.


# ─────────────────────────────────────────────
#  HAUPT-ZUSTANDSMASCHINE
# ─────────────────────────────────────────────

def spiel_loop(screen, clock, schriften):
    """
    Äußere Zustandsmaschine: wechselt zwischen Hauptmenü und Spielen.
    Startet das Spiel neu wenn der Spieler 'Nochmal spielen' wählt.
    """
    zustand = ZUSTAND_HAUPTMENU
    modus   = None

    while True:
        if zustand == ZUSTAND_HAUPTMENU:
            modus   = zeige_hauptmenu(screen, clock, schriften)
            zustand = ZUSTAND_SCHIFFE_SETZEN

        elif zustand == ZUSTAND_SCHIFFE_SETZEN:
            # Komplette Partie spielen (Rundenlogik übernimmt ab hier)
            aktion = runden_controller(screen, clock, schriften, modus)

            if aktion == "neustart":
                # Direkt nochmal spielen im gleichen Modus
                zustand = ZUSTAND_SCHIFFE_SETZEN
            else:
                # Zurück ins Hauptmenü
                zustand = ZUSTAND_HAUPTMENU


# ─────────────────────────────────────────────
#  EINSTIEGSPUNKT
# ─────────────────────────────────────────────

def main():
    screen, clock = init()
    schriften = lade_schriften()
    spiel_loop(screen, clock, schriften)


if __name__ == "__main__":
    main()
