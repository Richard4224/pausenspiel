
# 0 — leer / wasser
# 1 — schiff
# 2 — fehlschuss
# 3 — treffer
# 4 — versenkt

def pruefzahl(zahl, letzte, erste = 0 ):
    if erste > letzte:
        erste, letzte = letzte, erste
    try:
        a = int(zahl)
    except ValueError:
        print ("Value Error")
        return None
    if a > letzte or a < erste:
        print(f"Das Argument muss zwischen {erste} und {letzte} liegen.")
        return None
    return a


class Schiff:
    def __init__(self, groesse):
        self.groesse = groesse
        self.start = None
        self.felder = []
        self.richtung = "horizontal"
        self.treffer = []
        self.versenkt = False

    def felder_berechnen(self, x, y, richtung):
        self.start = (x, y)
        self.richtung = richtung
        self.felder = []

        for i in range(self.groesse):
            if richtung == "horizontal":
                self.felder.append((x + i, y))
            elif richtung == "vertikal":
                self.felder.append((x, y + i))
            else:
                print("Falsche Richtung")
                return None

        return self.felder


class Spielfeld:
    def __init__(self):
        self.raster = [[0]*10 for x in range(10)]


    def feldzustand_setzen(self, x, y, zustand):
        nummer = pruefzahl(zustand, 4)
        self.raster[y][x] = nummer

    def ist_im_feld(self, x, y):
        return 0 <= x < 10 and 0 <= y < 10

    def kann_schiff_platzieren(self, schiff):
        for x, y in schiff.felder:
            if not self.ist_im_feld(x, y):
                return False

            if self.raster[y][x] != 0:
                return False

        return True

    def schiff_platzieren(self, schiff, x, y, richtung):
        schiff.felder_berechnen(x, y, richtung)

        if not self.kann_schiff_platzieren(schiff):
            print("Schiff kann hier nicht platziert werden.")
            return False

        for x, y in schiff.felder:
            self.raster[y][x] = 1

        return True




