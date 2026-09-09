"""Rechnerische Sichtpruefung: Rendern geht in dieser Umgebung nicht (LibreOffice
Impress ist nicht installiert), also wird geprueft, was sich aus dem XML rechnen
laesst — Rand, Ueberlauf, Ueberlappung."""
import math, re, sys, zipfile
from xml.etree import ElementTree as ET

EMU = 914400.0
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
BREITE, HOEHE = 13.333, 7.5
RAND_MIN = 0.5
# Mittlere Zeichenbreite als Anteil der Schriftgroesse (Calibri/Cambria ~0.48,
# Courier New ist dicksten: 0.60).
BREIT = {"Courier New": 0.60, "Cambria": 0.50, "Calibri": 0.47}

def zoll(v): return float(v) / EMU

def texte(sl):
    for sp in sl.iter("{%s}sp" % NS["p"]):
        xfrm = sp.find(".//a:xfrm", NS)
        if xfrm is None:
            continue
        off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
        if off is None or ext is None:
            continue
        kasten = (zoll(off.get("x")), zoll(off.get("y")),
                  zoll(ext.get("cx")), zoll(ext.get("cy")))
        absaetze = []
        for para in sp.iter("{%s}p" % NS["a"]):
            stuecke, groesse, schrift, zeilen_abstand = [], 18.0, "Calibri", None
            pPr = para.find("a:pPr", NS)
            if pPr is not None:
                ln = pPr.find("a:lnSpc/a:spcPts", NS)
                if ln is not None:
                    zeilen_abstand = int(ln.get("val")) / 100.0
            for r in para.findall("a:r", NS):
                t = r.find("a:t", NS)
                rPr = r.find("a:rPr", NS)
                if rPr is not None and rPr.get("sz"):
                    groesse = int(rPr.get("sz")) / 100.0
                if rPr is not None:
                    lat = rPr.find("a:latin", NS)
                    if lat is not None:
                        schrift = lat.get("typeface", schrift)
                if t is not None and t.text:
                    stuecke.append(t.text)
            if stuecke:
                absaetze.append(("".join(stuecke), groesse, schrift, zeilen_abstand))
        if absaetze:
            yield kasten, absaetze

def hoehe_geschaetzt(text, groesse, schrift, breite_zoll, zeilen_abstand):
    zeichenbreite = BREIT.get(schrift, 0.48) * groesse / 72.0
    je_zeile = max(1, int(breite_zoll / zeichenbreite))
    zeilen = 0
    for stueck in text.split("\n"):
        zeilen += max(1, math.ceil(len(stueck) / je_zeile))
    hoehe_zeile = (zeilen_abstand or groesse * 1.22) / 72.0
    return zeilen * hoehe_zeile, zeilen

def rahmen(sl):
    """Alle Rahmen (auch Bilder), fuer die Ueberlappungspruefung."""
    aus = []
    for tag in ("sp", "pic"):
        for el in sl.iter("{%s}%s" % (NS["p"], tag)):
            xfrm = el.find(".//a:xfrm", NS)
            if xfrm is None:
                continue
            off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
            if off is None or ext is None:
                continue
            aus.append((tag, zoll(off.get("x")), zoll(off.get("y")),
                        zoll(ext.get("cx")), zoll(ext.get("cy"))))
    return aus

datei = sys.argv[1]
z = zipfile.ZipFile(datei)
namen = sorted((n for n in z.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
               key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
maengel = 0
for nr, name in enumerate(namen, 1):
    sl = ET.fromstring(z.read(name))
    for (x, y, b, h), absaetze in texte(sl):
        noetig = sum(hoehe_geschaetzt(t, g, s, b - 0.02, la)[0] for t, g, s, la in absaetze)
        erster = absaetze[0][0][:44].replace("\n", " ")
        if noetig > h + 0.02:
            print(f"Folie {nr:2d}  UEBERLAUF  brauchte {noetig:.2f}\" von {h:.2f}\"  "
                  f"({b:.2f}\" breit)  «{erster}…»")
            maengel += 1
        if x < RAND_MIN - 0.01 or y < RAND_MIN - 0.01 \
           or x + b > BREITE - RAND_MIN + 0.01 or y + h > HOEHE - RAND_MIN + 0.01:
            print(f"Folie {nr:2d}  RAND       x={x:.2f} y={y:.2f} b={b:.2f} h={h:.2f}  «{erster}…»")
            maengel += 1
        if x < -0.01 or y < -0.01 or x + b > BREITE + 0.01 or y + h > HOEHE + 0.01:
            print(f"Folie {nr:2d}  AUSSERHALB DER FOLIE  «{erster}…»")
            maengel += 1
    # Bilder ausserhalb
    for tag, x, y, b, h in rahmen(sl):
        if tag == "pic" and (x < -0.01 or y < -0.01 or x + b > BREITE + 0.01 or y + h > HOEHE + 0.01):
            print(f"Folie {nr:2d}  BILD AUSSERHALB  x={x:.2f} y={y:.2f} b={b:.2f} h={h:.2f}")
            maengel += 1
print(f"\n{len(namen)} Folien geprueft, {maengel} Beanstandungen")
