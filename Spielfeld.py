
# 0 — leer / wasser
# 1 — schiff
# 2 — fehlschuss
# 3 — treffer
# 4 — versenkt

class schiff:
    def __init__(self, groesse):
        self.groesse = groesse
        self.start = None
        self.richtung = "horizontal"
        self.treffer = []
        self.leben = True


class feld:
    def __init__(self):
        self.spielfelder = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    def set_schiff(self, x, y):
        self.spielfelder[y][x] = 1

    def set_fehlschuss(self, x, y):
        self.spielfelder[y][x] = 2

    def set_treffer(self, x, y):
        self.spielfelder[y][x] = 3

    def set_versenkt(self, x, y):
        self.spielfelder[y][x] = 4



