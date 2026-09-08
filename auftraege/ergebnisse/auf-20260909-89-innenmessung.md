# auf-20260909-89 — Traegt eine frontale Innenansicht ein Geometrie-Urteil?

**Stand:** 2026-09-08 (Geraetedatum) · **Karte:** RTX 5090, Leistungsgrenze 400 W,
Spitze im Lauf **307 W / 26.0 GB** · **Blender** 5.2.1 LTS · **torch** 2.11.0+cu128 ·
**Schaetzer** depth-anything-v2-small · **Backbone** z-image-turbo

---

## Kurzantwort

**Ja, rho trennt frontal von ueber Eck — und zwar sauber. Aber der frontale Wert ist
keine Messung.**

Ueber **30 Renderlaeufe** — fuenf frontale und funf ueber-Eck-Standpunkte, je drei
Startwerte — gilt ohne eine einzige Ausnahme:

| | rho ueber der Maske | Spanne ueber 3 Startwerte | unter dem Rauschanker |
|---|---|---|---|
| **ueber Eck** (15 Laeufe) | +0.9695 … +0.9998 | 0.0006 … 0.0250 | **0 von 15** |
| **frontal** (15 Laeufe) | −0.0351 … +0.9384 | 0.0400 … 0.9393 | **6 von 15** |

Die beiden Bereiche **ueberschneiden sich nicht**: der kleinste Ueber-Eck-Wert (+0.9695)
liegt ueber dem groessten frontalen (+0.9384).

Der entscheidende Teil steht in der dritten Spalte. Ueber Eck steht rho fest — dieselbe
Geometrie, drei Bilder, Unterschied in der vierten Nachkommastelle. Frontal wandert rho
mit dem Startwert um bis zu **0.9393** und faellt in **6 von 15** Laeufen **unter den
Nullanker aus weissem Rauschen derselben Maskenlage**. Eine Zahl, die vom Startwert um
0.94 abhaengt und die ein Rauschbild ebenso gut erreicht, misst nicht die Geometrie.

*Zu «beherrscht von einer Flaeche» heisst «rho misst dort nichts»: Ja — aber nicht, weil
rho niedrig waere, sondern weil es nicht reproduzierbar ist.*

---

## Wie gemessen wurde

Geometrie aus dem Repo, keine Projektdaten:

```
.venv-ifc/bin/python tools/make_test_ifc.py build/innen/raeume.ifc IFC4 --raeume
AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \
    .venv-render/bin/python tools/studie_innenmessung.py build/innen
AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \
    .venv-render/bin/python tools/studie_innenmessung.py build/innen800 --breite=800 --hoehe=496
```

`tools/studie_innenmessung.py` ist neu und liegt im Arbeitsbaum (nicht eingecheckt).
Der Ablauf je Fall ist woertlich der des Produktpfads `tools/homeworker._render_und_qa`:
Multipass → `maske.maske_aus_bericht(gelaende_erwartet=True)` → Soll-Karte aus der EXR
(`bildlesen.tiefen_aus_report`) → `render.rendere` je Startwert →
`tiefenschaetzer.qa_gegen_soll(..., maske=…)`. Dazu je Fall `abholer._nullprobe` ueber
derselben Maskenlage.

**Gegenprobe gegen den Produktpfad.** Fall A, Startwert 0, ueber
`homeworker.fuehre_aus()` mit einer In-Memory-Kopie des Auftrags (params `auge`,
`blick_auf`, `brennweite`, `aufloesung`, `samples`, `seed`, `schritte`, `prompt`,
`out_dir`; die Auftragsdatei wurde **nicht** veraendert):

```
rho_maske    0.5448032913998685   (Studie: 0.5448032913998685)
score        0.5739281678494094   (Studie: 0.5739281678494094)
kantenanteil 0.0                  (Studie: 0.0)
```

Stellengleich. Die Studie misst denselben Weg.

Prompt (in `params` des Auftrags stand keiner; der uebliche Standardprompt beschreibt
eine **Aussen**ansicht und passt hier nicht):

> photorealistic architectural interior view of a simple modern room, plain plastered
> walls, matte concrete floor, soft indirect daylight, no furniture, no people,
> eye-level interior view

Aufloesung 512 x 512 (Vorgabe des Produktpfads), 32 Samples, 20 Schritte,
controlnet_staerke 0.8, denoise 0.6, Beauty-Pass als Anker. Zusaetzlich derselbe Satz
bei 800 x 496, eurem Format aus der Vorpruefung. Rechenzeit: Multipass 4.2–4.3 s,
Render 3.5–3.7 s je Bild.

---

## V1 · rho ueber der Maske, alle drei Startwerte einzeln

### 512 x 512 — die Vorgabe des Produktpfads

| Fall | Blick | seed 0 | seed 1 | seed 2 | Spanne | Nullanker (Rauschen) | Abstand zum Anker |
|---|---|---|---|---|---|---|---|
| A Raum-Nord | frontal | **+0.5448** | +0.8573 | **+0.6202** | **0.3125** | +0.8167 | −0.2719 … +0.0406 |
| B Raum-Nord | ueber Eck | +0.9993 | +0.9989 | +0.9941 | 0.0051 | +0.8760 | +0.1182 … +0.1233 |
| C Raum-Sued | frontal | +0.8732 | +0.8916 | +0.9131 | 0.0400 | +0.7205 | +0.1527 … +0.1927 |
| D Raum-Sued | ueber Eck | +0.9994 | +0.9998 | +0.9989 | 0.0008 | +0.8052 | +0.1938 … +0.1946 |

### 800 x 496 — euer Format aus der Vorpruefung

| Fall | Blick | seed 0 | seed 1 | seed 2 | Spanne | Nullanker (Rauschen) | Abstand zum Anker |
|---|---|---|---|---|---|---|---|
| A Raum-Nord | frontal | +0.9037 | +0.8045 | **+0.5571** | **0.3466** | +0.5800 | −0.0229 … +0.3237 |
| B Raum-Nord | ueber Eck | +0.9976 | +0.9981 | +0.9978 | 0.0006 | +0.6881 | +0.3095 … +0.3100 |
| C Raum-Sued | frontal | **−0.0351** | +0.8184 | +0.9042 | **0.9393** | +0.3471 | −0.3822 … +0.5571 |
| D Raum-Sued | ueber Eck | +0.9944 | +0.9886 | +0.9979 | 0.0093 | +0.6735 | +0.3152 … +0.3245 |

Fett: Laeufe unter dem eigenen Rauschanker bzw. die Spanne, um die es geht.

**Das Niveau trennt.** Alle 12 Ueber-Eck-Laeufe liegen ueber +0.9886; von den 12
frontalen erreicht keiner +0.92.

**Die Reproduzierbarkeit trennt schaerfer.** Ueber Eck ist die Spanne ueber drei
Startwerte hoechstens 0.0093 — bei zwei Faellen sogar unter 0.001, also praktisch
dieselbe Zahl aus drei verschiedenen Bildern. Frontal reicht sie von 0.0400 bis 0.9393.
Der frontale Fall C bei 800 x 496 liefert aus drei Bildern derselben Geometrie **−0.04,
+0.82 und +0.90**. Das ist kein Messwert mit Streuung, das ist Wuerfeln.

**Eure Startwertstreuung von 0,2269 ist hier deutlich uebertroffen** — frontal, nicht
ueber Eck. Die Ansage im Auftrag («ohne drei Startwerte ist ein Unterschied nicht von
Rauschen zu trennen») war richtig und hat den ganzen Befund erst sichtbar gemacht: mit
nur seed 0 haette Fall A bei 800 x 496 mit +0.9037 wie ein gutes Ergebnis ausgesehen.

---

## V2 · Kantenanteil an der Maskengrenze, je Startwert

Zwei Masse, nicht verrechnet — wie verlangt.

| Fall | Blick | Format | seed 0 | seed 1 | seed 2 | n_grenze | ueber Zufall? |
|---|---|---|---|---|---|---|---|
| A | frontal | 512 | 0.0000 | 0.0000 | **0.1863** | 510 | nur seed 2 |
| B | ueber Eck | 512 | 0.0000 | 0.0000 | 0.0000 | 510 | nein |
| C | frontal | 512 | 0.0000 | 0.0000 | 0.0000 | 481 | nein |
| D | ueber Eck | 512 | 0.0000 | 0.0000 | 0.0000 | 510 | nein |
| A | frontal | 800 | 0.0000 | 0.0000 | 0.0000 | 798 | nein |
| B | ueber Eck | 800 | 0.0000 | 0.0000 | 0.0000 | 735 | nein |
| C | frontal | 800 | 0.0000 | 0.0000 | 0.0000 | 601 | nein |
| D | ueber Eck | 800 | 0.0000 | 0.0000 | 0.0000 | 709 | nein |

Die zugehoerige Kantenstaerke (`kante.gerichtet`, Median innen minus Median aussen) liegt
in allen 24 Laeufen zwischen −0.0044 und +0.0119, gegen eine Schwelle von 0.05.

**Das zweite Bein traegt innen ueberhaupt nicht — und zwar in beiden Blickarten.**
`paarurteil.bestanden` ist in **allen 24 Laeufen `false`**, jedesmal getragen von
`anteil` (Schwelle 0.20), nie von rho. Ueber Eck faellt das Paarurteil also durch,
obwohl rho mit +0.999 so gut ist, wie diese Kette es je gemessen hat.

Der Grund steht in den Zahlen daneben: `himmel.anteil` ist in allen 24 Laeufen **1.000**.
Die Maskengrenze der Testgeometrie ist der **offene Deckenrand** — die Testgeometrie hat
keine Decke, und der Blick nach oben trifft Himmel. Die 481–798 Grenzpunkte sind kein
Bauwerksumriss, sondern die Kante zum fehlenden Dach. Was dort gemessen wird,
beantwortet die Existenzfrage nicht.

---

## V3 · Nullanker aus derselben Nullprobe

Je Fall drei Kontrollbilder ohne jede Geometrie (`bildschreiben.KONTROLLARTEN`),
gemessen ueber **derselben Maskenlage**. Angegeben ist rho; die Kante der Nullprobe liegt
durchweg zwischen −0.0053 und −0.0002.

| Fall | Blick | Format | Rauschen | Grau | Verlauf |
|---|---|---|---|---|---|
| A | frontal | 512 | **+0.8167** | +0.6839 | +0.4418 |
| B | ueber Eck | 512 | +0.8760 | +0.8796 | +0.8174 |
| C | frontal | 512 | +0.7205 | +0.6267 | +0.3963 |
| D | ueber Eck | 512 | +0.8052 | +0.8500 | +0.5954 |
| A | frontal | 800 | +0.5800 | +0.2636 | +0.0981 |
| B | ueber Eck | 800 | +0.6881 | +0.7016 | +0.8376 |
| C | frontal | 800 | +0.3471 | +0.0915 | −0.1042 |
| D | ueber Eck | 800 | +0.6735 | +0.6074 | +0.3394 |

**Warum der Anker je Fall gemessen gehoert und nicht nachgeschlagen:** er schwankt hier
zwischen −0.10 und +0.88. Eine feste Zahl haette den Befund zerstoert.

**Der harte Punkt:** Bei Fall A / 512 liegt der Mittelwert der drei gerenderten Bilder
(+0.6741) **unter** dem weissen Rauschen (+0.8167). Ein Bild aus reinem Zufall ordnet die
Tiefe dieser Maske besser als das konditionierte Render. Bei Fall B derselben Karte liegt
das Render 0.12 ueber dem Anker, und zwar in allen drei Startwerten gleich weit.

---

## V4 · Welche Brennweite ist angekommen?

**24.0 mm.** In allen zehn Multipass-Berichten der Messreihe steht

```
kamera.brennweite_mm = 24.0
kamera.weg           = "vorgegeben"
kamera.begruendung   = "Standort und Blickziel kamen als Zahlen herein; hier wurde nur gestellt."
```

Euer Durchgriff ist also angekommen, und `auge`/`blick_auf` sind in `_KAMERA_PARAMS`
(`tools/homeworker.py`, Zeile 281). Kein Auftrag musste von Hand geflickt werden.

**Gegenprobe, damit die Zahl etwas aussagen kann:** derselbe Standpunkt ohne
`brennweite` in den Params —

```
OHNE brennweite -> kamera.brennweite_mm = 50.0 | weg = "vorgegeben"
```

Der Rueckfall auf 50 mm existiert hier also unveraendert und wird **nur** dadurch
vermieden, dass der Auftrag die Brennweite mitbestellt. Euer Befund 2 gilt auf dieser
Seite genauso.

**Nebenbefund zu V4, und er betrifft eure Frage direkt:** Der Produktpfad
`homeworker._render_und_qa` traegt den Kamerablock **nicht** in seine `messwerte` — der
Multipass-Zweig tut es (`"kamera": _nur_dateinamen(blender_bericht.get("kamera"))`,
Zeile 446), der Render-Zweig nicht. Aus einem gewoehnlichen `art: "render"`-Ergebnis
waere V4 **gar nicht zu beantworten** gewesen. Wir haben die Zahl aus dem
Blender-Bericht selbst gelesen. Wer die Brennweite kuenftig aus einem Renderauftrag
belegen will, braucht die Zeile dort.

---

## V5 · Gegenprobe der Standpunkte — ja, dieselben Zahlen

`kette._raeume_lesen()` → `raumkamera.standpunkte()` ueber derselben erzeugten
Geometrie, ohne Renderlauf:

| | euer Wert | unser Wert |
|---|---|---|
| A Raum-Nord frontal | auge [4.000, 0.600, 1.35] · blick_auf [4.000, 4.700, 1.35] | auge [4.000000, 0.600000, 1.350000] · blick_auf [4.000000, 4.700000, 1.350000] |
| B Raum-Nord ueber Eck | auge [0.604, 0.604, 1.35] · blick_auf [4.394, 4.394, 1.35] | auge [0.604056, 0.604056, 1.350000] · blick_auf [4.394148, 4.394148, 1.350000] |
| C Raum-Sued frontal | auge [6.350, 0.610, 1.30] · blick_auf [6.350, 2.500, 1.30] | auge [6.350000, 0.610000, 1.300000] · blick_auf [6.350000, 2.500000, 1.300000] |
| D Raum-Sued ueber Eck | auge [7.396, 0.604, 1.30] · blick_auf [5.805, 2.195, 1.30] | auge [7.395944, 0.604056, 1.300000] · blick_auf [5.804954, 2.195046, 1.300000] |

**Identisch auf allen von euch angegebenen Stellen.** Auch die Hoehen stimmen mit eurer
Regel: Raum-Nord z_unten 0.0 + 2.7/2 = 1.35, Raum-Sued z_unten 0.1 + 2.4/2 = 1.30, und
`auge[2] == blick_auf[2]` in allen vier Faellen. `sichtfeld.brennweite_mm` ist ueberall
24.0.

(Der einzige Zahlenwert, der bei uns anders aussieht, ist ein Rechenrest:
`auge[1] = 0.6000000000000432` statt 0.6. Auf eure drei Stellen gerundet dasselbe.)

---

## V6 · Eine eigene Datei MIT Raeumen UND Decke — und zwei Ueberraschungen

**Wir haben eine.** Genauer: sechs Kandidaten mit Raeumen liegen hier. Die erste
Ueberraschung ist, dass die Innenkette auf **keinem einzigen** von ihnen laeuft — dazu
unten und in V7.

Gemessen wurde an einer Pilotdatei aus dem eigenen Oekosystem (IFC4, Millimeter,
13 `IfcSpace` auf drei Geschossen, 82 Elemente, 1016 Dreiecke, Huellbox
61.0 x 29.5 x 15.2 m). Kein Projekt-, Buero- oder Kundenname, keine Raumnamen — die
Raeume tragen dort nur GUIDs. Gewaehlt: der groesste EG-Raum, 47.5 m², Raumhoehe 3.0 m,
mit zwei Geschossen darueber, also **mit Decke**. Standpunkte wieder aus
`raumkamera.standpunkte`, nicht von Hand:

- **E frontal**: auge [135.500, 16.800, 1.500] · blick_auf [135.500, 21.500, 1.500]
- **F ueber Eck**: auge [132.804, 16.804, 1.500] · blick_auf [137.195, 21.195, 1.500]

512 x 512, sonst alles wie oben.

| Fall | Blick | seed 0 | seed 1 | seed 2 | Spanne | Anker Rauschen | Anker Grau | Anker Verlauf |
|---|---|---|---|---|---|---|---|---|
| **E** | frontal | **+0.3389** | +0.9384 | **+0.7641** | **0.5995** | +0.7927 | +0.8981 | +0.7303 |
| **F** | ueber Eck | +0.9945 | +0.9931 | +0.9695 | 0.0250 | +0.8338 | +0.9059 | +0.8098 |

Soll-Karte: E groesste Ebene 41.6 %, Spanne 2.758 m, 206 Stufen · F groesste Ebene
0.59 %, Spanne 7.082 m, 607 Stufen. Kantenanteil: **nicht messbar**, in allen sechs
Laeufen.

### Befund 1 · Die Decke rettet die frontale Ansicht nicht — sie macht sie schlechter

Gegen euer Gegenargument im Plan: Boden, Decke und anschneidende Seitenwaende sind hier
**alle** im Bild, und die Ansicht ist trotzdem der schlechteste frontale Fall der ganzen
Messreihe. Spanne ueber drei Startwerte **0.5995**; der Mittelwert (+0.6805) liegt
**unter** dem Rauschanker (+0.7927), gegen den Grau-Anker (+0.8981) liegen **alle drei**
Startwerte darunter. Ueber Eck derselben Datei: Spanne 0.0250, alle drei ueber jedem der
drei Anker.

Die Decke fuegt Tiefe hinzu (Spanne 2.758 m statt 2.296 m in der Testgeometrie, 206
statt 138 Stufen) — und aendert am Urteil nichts.

### Befund 2 · Mit Decke ist das zweite Bein nicht nur schwach, es existiert nicht

`anteil_bauwerk = 1.0`. Die Bauwerksmaske fuellt das **ganze Bild**, `n_grenze = 0`, und
damit sind `kante` und `kantenanteil` **nicht gemessen — weder 0 noch 1**. Die Kette sagt
das von sich aus und richtig:

> «Die Maske hat keine Grenze: 0 Randpunkte innen, 0 aussen. Eine leere Maske und eine,
> die das ganze Bild fuellt, haben beide keinen Rand.»

Und `paarurteil` erklaert sich fuer **nicht zustaendig** (`zustaendig: false`,
`bestanden: null`), weil hinter dem Umriss 0.0 % Himmel steht statt der verlangten 10 %.
Das ist gutes Verhalten und kein Fehler — aber die Folge ist hart:

**In einer geschlossenen Innenansicht bleibt vom Maskenweg genau ein Bein uebrig: rho.
Und rho ist das Bein, das die frontale Ansicht nicht tragen kann.**

Ohne Decke (Testgeometrie) faellt das Paarurteil in allen 24 Laeufen durch, weil der
Kantenanteil unter 0.20 liegt; mit Decke faellt es gar nicht erst an. Beide Male gibt es
innen **kein** vollstaendiges Paarurteil — aus zwei verschiedenen Gruenden.

---

## V7 · Die Zeile, die ihr nicht erfragt habt

**Ausserhalb eurer Testgeometrie liefert `raumkamera` auf dieser Maschine null
Standpunkte: sechs echte Dateien, 972 `IfcSpace`, kein einziger Grundriss — 941 davon an
genau einer Ursache, `IfcIndexedPolyCurve`, die der Raumleser als Profilkurve nicht
liest.**

Gemessen (`kette._raeume_lesen`, unveraendert):

| Datei (neutral) | MB | IfcSpace | mit Standpunkt | Ursache |
|---|---|---|---|---|
| Bestandsaufnahme | 65.89 | 358 | 0 | 355 × `IfcIndexedPolyCurve`, 3 × kein Extrusionskoerper |
| Werkzeugausgabe A | 5.35 | 375 | 0 | 375 × `IfcIndexedPolyCurve` |
| Werkzeugausgabe B | 33.68 | 198 | 0 | 198 × `IfcIndexedPolyCurve` |
| Pilotdatei (V6) | 0.19 | 13 | 0 | 13 × `IfcIndexedPolyCurve` |
| Wohnbau-Beispiel A | 0.12 | 14 | 0 | 14 × `keine_repraesentation` (Zonen ohne Koerper) |
| Wohnbau-Beispiel B | 0.12 | 14 | 0 | 14 × `keine_repraesentation` |
| **Summe** | | **972** | **0** | **941 × `IfcIndexedPolyCurve`**, 28 × ohne Koerper, 3 × ohne Extrusionskoerper |

Die Stelle ist `src/aiimaging/runners/ifc_raeume_runner.py`, Zeile 302:
`if not kurve.is_a("IfcPolyline")` → `PROFILKURVE_NICHT_UNTERSTUETZT`. Die Begruendung
dort («alles andere wuerde geraten statt gelesen») ist fuer Boegen richtig, fuer
`IfcIndexedPolyCurve` mit reinen `IfcLineIndex`-Segmenten aber nicht: das ist eine
Polylinie, nur anders geschrieben.

Damit V6 ueberhaupt eine Zahl bekommt, haben wir eine **Kopie** des Runners unter
`build/` um genau diesen Fall erweitert (Geradensegmente ja, Boegen weiterhin abgelehnt).
Ergebnis an der Pilotdatei: **13 von 13** Raeumen mit Grundriss, Flaechen 7.5–47.5 m²,
Hoehen 3.0 m, Geschosse EG/1.OG/2.OG. **Der Produktleser wurde nicht angefasst** — das
ist eine Messhilfe, kein Fix, und die Entscheidung darueber gehoert euch.

*Solange das so steht, ist die ganze Innenkette auf dieser Maschine nur auf
`make_test_ifc.py --raeume` fahrbar.*

---

## Abweichungen von dem, was im Auftrag steht

**1. Unsere Vorpruefungszahlen weichen ab — bis wir euer Bildformat einstellen.**
Der Produktpfad rendert 512 x 512 (Vorgabe `homeworker`), eure Studie 800 x 496. An
derselben Geometrie, denselben Standpunkten, 24 mm:

| Fall | Groesse | Geometrieanteil | Spanne m | Stufen | groesste Ebene |
|---|---|---|---|---|---|
| A frontal | 512 x 512 | 76.8 % | 2.296 | 138 | **48.8 %** |
| A frontal | 800 x 496 | 93.3 % | 1.191 | 73 | **78.8 %** |
| C frontal | 512 x 512 | 82.0 % | 2.353 | 187 | **35.3 %** |
| C frontal | 800 x 496 | 96.2 % | 2.288 | 207 | **56.9 %** |

Bei 800 x 496 kommt **eure Tabelle stellengleich heraus** — 93.3 / 1.191 / 73 / 78.8 ·
84.2 / 4.998 / 489 / 0.6 · 96.2 / 2.288 / 207 / 56.9 · 85.1 / 5.106 / 497 / 0.5.
Nachgerechnet mit unserem eigenen Weg (`seams.glb_zu_tiefenkarte` +
`bildlesen.tiefen_aus_report`), nicht mit eurem Skript.

Die Ursache ist das Seitenverhaeltnis: `sensor_fit` ist HORIZONTAL, ein quadratisches
Bild sieht also **mehr Boden und mehr offenen Deckenrand** und weniger von der Stirnwand.
Damit sinkt die groesste Ebene um rund 20 Prozentpunkte und der Geometrieanteil um 14–16.

**Das ist keine Entwarnung, sondern ein zweiter Hebel:** die Herrschaft einer Flaeche ist
kein Merkmal des Standpunkts allein, sondern des Standpunkts **und des Bildformats**. Bei
demselben Standpunkt und einer um 30 Punkte geringeren Flaechenherrschaft blieb der
frontale Befund derselbe (Spanne 0.3125 statt 0.3466). Wer das Format aendert, um die
frontale Ansicht zu retten, rettet sie nicht.

**2. `bestanden` ist frontal nicht durchweg `false`.** Von den 15 frontalen Laeufen
bestehen **12** das Geometrie-Tor ueber das ganze Bild (Schwelle 0.65) — Fall A / 800 /
seed 0 sogar mit score 0.9171, Fall E / seed 1 mit 0.9687. Das Tor ueber das ganze Bild sieht die Sache also gar nicht. Nur
der Maskenweg und der Nullanker zeigen sie. Das ist genau der Fall, vor dem eure eigene
Notiz warnt: gruen und leer.

**3. Zaehlung:** A/C/E frontal und B/D/F ueber Eck, wobei A–D je zweimal gefahren sind
(512 x 512 und 800 x 496) und E/F einmal. Macht 10 Multipass-Laeufe, 30 Renderlaeufe,
30 Schaetzerlaeufe und 30 Nullprobenbilder.

---

## Was NICHT getan wurde

- Keine Schwelle geaendert, kein Riegel scharfgestellt. `geometrie_qa.SCHWELLE_GEOMETRIE`
  und die Paarschwellen stehen unveraendert.
- Nichts committet, nichts gepusht.
- Die Auftragsdatei wurde nicht veraendert.
- Der Produktleser `ifc_raeume_runner.py` wurde **nicht** angefasst; die V6-Erweiterung
  ist eine Kopie unter `build/`.
- Bei Fall A wurde nicht abgebrochen, obwohl rho dort unbrauchbar aussah.

## Rohdaten

`build/innen/roh.json`, `build/innen800/roh.json`, `build/v6_512/roh.json` — bleiben auf
dem Geraet (Regel 3), je Fall mit allen Startwerten, Nullankern, Maskenbefunden und dem
vollstaendigen Kamerablock des Multipass-Berichts.
