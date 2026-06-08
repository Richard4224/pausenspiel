# 🚢 Schiffe Versenken

Das klassische Battleship-Spiel als lokales Python-Spiel mit grafischer Oberfläche – spielbar alleine gegen eine KI oder zu zweit am selben Bildschirm.

---

## Voraussetzungen

- Python 3.8 oder neuer
- pip

---

## Installation & Starten

```bash
# 1. Repository klonen
git clone https://github.com/Richard4224/pausenspiel/tree/main

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Spiel starten
python3 main.py
```

Das Spielfenster öffnet sich mit einer festen Größe von 920×700 Pixeln.

---

## Modi

### PvE – Spieler gegen KI
Du spielst gegen einen eingebauten Algorithmus. Die KI schießt zufällig auf noch nicht beschossene Felder. Du siehst nach deinem Zug wie die KI ihren Zug macht – inklusive kurzer Wartezeit und sichtbarem Schussergebnis auf deinem Spielfeld.

### PvP – Zwei Spieler lokal
Beide Spieler spielen abwechselnd am selben Bildschirm. Zwischen jedem Zug erscheint ein Übergabe-Screen, damit der andere Spieler das Spielfeld nicht sieht. Erst nach Drücken von `Enter` wird das Board des nächsten Spielers angezeigt.

---

## Spielablauf

### 1. Schiffe setzen
Jeder Spieler platziert seine Flotte auf einem 10×10-Raster.

| Aktion | Steuerung |
|---|---|
| Schiff platzieren | Linksklick auf das Raster |
| Ausrichtung drehen (horizontal ↔ vertikal) | `R` |
| Zurück ins Menü | `Esc` |

Eine farbige Vorschau zeigt an, ob die gewählte Position gültig ist:
- 🟢 **Grün** – Position ist frei, Klick platziert das Schiff
- 🔴 **Rot** – Position ist belegt oder außerhalb des Rasters

Die Schiffe werden in dieser Reihenfolge gesetzt:

| Schiff | Größe |
|---|---|
| Schlachtschiff | 5 Felder |
| Kreuzer | 4 Felder |
| Zerstörer | 3 Felder |
| Zerstörer | 3 Felder |
| U-Boot | 2 Felder |

Im PvP-Modus setzt zuerst Spieler 1, dann erscheint ein Übergabe-Screen, dann setzt Spieler 2.  
Im PvE-Modus setzt nur der menschliche Spieler Schiffe – die KI belegt ihr Feld automatisch zufällig.

### 2. Spielrunden

Du schießt, indem du auf eine Zelle im Gegnergitter klickst. Das Gitter zeigt dabei nur Treffer und Fehlschüsse – die gegnerischen Schiffe sind verdeckt.

| Zellfarbe | Bedeutung |
|---|---|
| 🔵 Blau | Wasser – noch nicht beschossen |
| 🔴 Rot | Treffer – Schiff getroffen |
| 🩵 Hellblau | Fehlschuss – Wasser getroffen |
| 🟫 Dunkelrot | Versenkt – Schiff vollständig versenkt und aufgedeckt |

**Spielregel:** Bei einem Treffer darf der aktive Spieler sofort nochmal schießen. Erst bei einem Fehlschuss wechselt der Zug.

### 3. KI-Zug (nur PvE)

Nach deinem Fehlschuss übernimmt die KI automatisch:

1. „KI denkt nach…" – kurze Pause (~1,5 Sekunden)
2. Der KI-Schuss landet sichtbar auf deinem Spielfeld (orangefarbener Rahmen)
3. Bei Treffer schießt die KI sofort nochmal, bei Fehlschuss bist du wieder dran

### 4. Spielende

Das Spiel endet wenn alle Schiffe eines Spielers versenkt wurden. Der Sieger wird angezeigt.

| Taste | Aktion |
|---|---|
| `Enter` | Nochmal spielen |
| `Esc` | Spiel beenden |

---

## Spielfeld-Koordinaten

Das Raster hat Spalten **A–J** (horizontal) und Zeilen **1–10** (vertikal).  
Beispiel: `C5` = dritte Spalte, fünfte Zeile.

```
   A  B  C  D  E  F  G  H  I  J
1  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~
2  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~
3  ~  ~  ▪  ▪  ▪  ~  ~  ~  ~  ~
4  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~
...
```

---

## Projektstruktur

```
pausenspiel/
├── main.py          – Spielfenster, Rendering, Eingaben (pygame)
├── modelle.py       – Spiellogik: Schiff, Spielfeld, KI (kein pygame)
├── tests/
│   └── test_modelle.py  – Unit Tests für die Spiellogik
├── requirements.txt
└── README.md
```

---

## Unit Tests ausführen

Die Tests prüfen die gesamte Spiellogik in `modelle.py` – unabhängig von pygame, also ohne Fenster.

```bash
# pytest installieren (einmalig)
pip install pytest

# Alle Tests ausführen
python3 -m pytest tests/

# Mit ausführlicher Ausgabe
python3 -m pytest tests/ -v
```

Erwartete Ausgabe:
```
collected 50 items

tests/test_modelle.py::TestSchiff::test_initial_nicht_versenkt         PASSED
tests/test_modelle.py::TestSchiff::test_versenkt_nach_allen_treffern   PASSED
...
50 passed in 0.04s
```

### Was getestet wird

| Gruppe | Anzahl Tests | Inhalt |
|---|---|---|
| `Schiff` | 7 | `versenkt`-Property, Teiltreffer, Initialisierung |
| `Spielfeld – Platzierung` | 13 | Horizontal/vertikal, Out-of-bounds, Überlappung, Raster-Update |
| `Spielfeld – Schießen` | 9 | Wasser, Treffer, Versenkt, Doppelschuss |
| `Spielfeld – Spielende` | 4 | `alle_versenkt()` mit einem und mehreren Schiffen |
| `Spielfeld – Zufällig` | 6 | Flotte vollständig, keine Überlappungen, Raster-Konsistenz |
| `KI` | 7 | 100 Kandidaten, keine Duplikate, alle Felder abgedeckt |
| `Integration` | 4 | Vollständige Spielsimulationen |

---

## Technologie

| Was | Womit |
|---|---|
| Sprache | Python 3 |
| Grafik | [pygame](https://www.pygame.org/) |
| Tests | [pytest](https://pytest.org/) |
| Spiellogik | reines Python, kein pygame |
