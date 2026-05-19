import pygame
import sys
 
# ─────────────────────────────────────────────
#  KONSTANTEN
# ─────────────────────────────────────────────
BREITE  = 800
HOEHE   = 600
FPS     = 60
TITEL   = "Schiffe Versenken"
 
# Farben (Platzhalter – später anpassen)
FARBE_HINTERGRUND = (15, 25, 50)
FARBE_TEXT        = (255, 255, 255)
FARBE_BUTTON      = (30, 80, 160)
FARBE_BUTTON_HOV  = (50, 120, 220)
FARBE_BUTTON_TEXT = (255, 255, 255)
 
 
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
 
 
def verarbeite_events():
    """
    Globale Events verarbeiten (Fenster schließen, Tastatur).
    Gibt eine Liste aller Events zurück.
    """
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
    return events
 
 
# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def zeige_hauptmenu(screen, clock, schriften):
    """
    Hauptmenü anzeigen und auf Benutzereingabe warten.
    Gibt den gewählten Zustand als String zurück:
      'einzelspieler' | 'mehrspieler' | 'beenden'
    """
    # Button-Positionen definieren
    btn_breite, btn_hoehe = 280, 55
    btn_x = BREITE // 2 - btn_breite // 2
 
    buttons = {
        "einzelspieler": pygame.Rect(btn_x, 250, btn_breite, btn_hoehe),
        "mehrspieler":   pygame.Rect(btn_x, 330, btn_breite, btn_hoehe),
        "beenden":       pygame.Rect(btn_x, 410, btn_breite, btn_hoehe),
    }
 
    while True:
        maus_pos = pygame.mouse.get_pos()
        events   = verarbeite_events()
 
        # Klick-Auswertung
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for aktion, rect in buttons.items():
                    if rect.collidepoint(maus_pos):
                        return aktion  # Zustand zurückgeben
 
        # ── Zeichnen ──────────────────────────
        screen.fill(FARBE_HINTERGRUND)
 
        # Titel
        titel_surf = schriften["titel"].render(TITEL, True, FARBE_TEXT)
        titel_rect = titel_surf.get_rect(center=(BREITE // 2, 130))
        screen.blit(titel_surf, titel_rect)
 
        # Buttons
        zeichne_button(screen, schriften, "Einzelspieler", buttons["einzelspieler"], maus_pos)
        zeichne_button(screen, schriften, "Mehrspieler",   buttons["mehrspieler"],   maus_pos)
        zeichne_button(screen, schriften, "Beenden",       buttons["beenden"],       maus_pos)
 
        pygame.display.flip()
        clock.tick(FPS)
 
 
# ─────────────────────────────────────────────
#  SPIELZUSTANDS-VERWALTUNG
# ─────────────────────────────────────────────
def starte_spiel(screen, clock, schriften, modus):
    """Platzhalter – wird später durch echte Spiellogik ersetzt."""
    print(f"[DEBUG] Spielmodus gewählt: {modus}")
    # Hier kommt später: zeige_schiffsplatzierung(...) usw.
 
 
def spiel_loop(screen, clock, schriften):
    """
    Haupt-Zustandsmaschine des Spiels.
    Steuert den Wechsel zwischen den verschiedenen Screens.
    """
    zustand = "hauptmenu"
 
    while True:
        if zustand == "hauptmenu":
            auswahl = zeige_hauptmenu(screen, clock, schriften)
 
            if auswahl == "einzelspieler":
                zustand = "spiel"
                starte_spiel(screen, clock, schriften, modus="einzelspieler")
                zustand = "hauptmenu"  # nach Spielende zurück
 
            elif auswahl == "mehrspieler":
                zustand = "spiel"
                starte_spiel(screen, clock, schriften, modus="mehrspieler")
                zustand = "hauptmenu"
 
            elif auswahl == "beenden":
                pygame.quit()
                sys.exit()
 
 
# ─────────────────────────────────────────────
#  EINSTIEGSPUNKT
# ─────────────────────────────────────────────
def main():
    screen, clock = init()
    schriften = lade_schriften()
    spiel_loop(screen, clock, schriften)

    # Spiellogik inplementieren
    pass

    #Todo: Auswahl des Spielsmodus (PvP oder PvE)

    #Todo: Spielfeld erstellen

    #Todo: Setzen der Schiffe

    #Todo: Zug für Zug Schießen
        # Spiellogik checkt ob ein schuss erfolgreich war

    # Wenn alle Schiffe zerstört sind, sagen welcher Spieler gewonnen hat
 
 
if __name__ == "__main__":
    main()
