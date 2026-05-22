
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
        self.felder = [None for x in range(self.groesse)]
        self.richtung = "horizontal"
        self.treffer = []
        self.versenkt = False


class Spielfeld:
    def __init__(self):
        self.raster = [[0]*10 for x in range(10)]


    def feldzustand_setzen(self, x, y, zustand):
        nummer = pruefzahl(zustand, 4)
        self.raster[y][x] = nummer




