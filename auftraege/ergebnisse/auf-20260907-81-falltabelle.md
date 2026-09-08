# Die Falltabelle der Paarmasse mit ECHTEM Tiefenschaetzer — `auf-20260907-81`

**08.09.2026 · HomeStation · `depth-anything-v2-small`, gemessene Polaritaet −1 · 176 Zeilen**

---

## Die Karte

Vor jedem Lauf gemessen mit
`nvidia-smi --query-gpu=power.draw,memory.used --format=csv,noheader`:

| Zeitpunkt | Leistung | belegt | Leerlauf? |
|---|---|---|---|
| vor Lauf 1 | 46.85 W | 735 MiB (0.72 GB) | ja (unter 120 W, unter 8 GB) |
| vor Lauf 2 | 45.73 W | 729 MiB (0.71 GB) | ja |
| waehrend Lauf 1 | 72.97 W | 1777 MiB | — |
| nach allen Laeufen | 44.77 W | 739 MiB | Karte freigegeben |

Leistungsgrenze gemessen: `power.limit 400.00 W` von `power.max_limit 600.00 W` —
**nicht angehoben**. Immer nur ein Lauf, nie zwei parallel. Geladen wurde nur der
Tiefenschaetzer (99 MB Gewichte); der Hoechststand von 1.78 GB liegt weit unter der
Schwelle. Kein Modell blieb geladen.

**V4 entfaellt.** Die Karte war frei, der Auftrag musste nicht zurueckgestellt werden.

---

## Was geaendert wurde — genau eines

Die Studie vom 01.09. (`docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`) baut die Ist-Karten
aus der Soll-Karte. Hier kommt die Ist-Karte aus dem **Beauty-Bild**, geschaetzt mit
`depth-anything-v2-small`. Sonst ist nichts anders: dieselben vier Szenen, dieselben vier
Richtungen (`s`, `w` frontal; `sSE`, `nNE` diagonal), 192 Punkte, 6 Samples, dieselbe
Saat 20260901 je Richtung zurueckgesetzt, dieselben elf Faelle mit denselben von Hand
vergebenen Etiketten — `studie_paarmasse.faelle` ist unveraendert importiert, nicht
nachgebaut.

Die Polaritaet wechselt mit und ist keine zweite Aenderung, sondern die Folge der ersten:
gebaute Karten waren Tiefen in Metern (+1), die Schaetzung ist Disparitaet. Es gilt das
**gemessene** Vorzeichen des Paares aus Schaetzer und unserer Soll-Konvention,
`geometrie_qa.GEMESSENE_POLARITAET` = **−1** (24 Laeufe, `auf-20260820-23`) — nicht
geraten und nicht aus den Daten geschlossen.

Werkzeug: `tools/studie_echtschaetzer.py`. Rohdaten: `auf-20260907-81-falltabelle.json`
(V1, 176 Zeilen). Sie liegt **neben dieser Datei und nicht in `build/`** — bei `auf-61`
waren genau diese Zwischendateien weg, und die Tabelle liess sich darum nicht mehr
rekonstruieren.

---

## 0 · Die Gegenprobe zuerst — und sie hat widersprochen

Bevor eine einzige neue Zahl etwas heissen darf: Rechnet derselbe Aufbau auf **denselben
Renders** den alten Weg nach, kommt dann die publizierte Tabelle heraus?

`auf-20260907-81-gegenprobe-gebaut.json`, gerechnet mit `studie_ersatzkalibrierung.sammle`
auf den Renders dieses Laufs:

| Gruppe | hoechster schlechter | niedrigster guter | publiziert 01.09. |
|---|---|---|---|
| frontal | **0.2568** | **0.3790** | 0.2568 / 0.3790 — **auf vier Stellen gleich** |
| diagonal | 0.5826 | 0.9223 | 0.5311 / 0.9065 — **weicht ab** |

Die fuenf frontal gesperrten guten Faelle sind Zeile fuer Zeile dieselben. Der Aufbau ist
damit belegt — und die diagonale Abweichung ist ein **Befund und kein Fehler**, wie die
Auflage es verlangt.

**Woran sie liegt, gemessen und nicht vermutet.** Der Geometrieanteil der diagonalen
Ansichten stimmt nicht mehr mit der publizierten Tabelle ueberein:

| Szene | `s` | `w` | `sSE` | `nNE` |
|---|---|---|---|---|
| heute | 0.1981 | 0.1529 | **0.1698** | **0.1698** |
| 01.09. | 0.1981 | 0.1529 | **0.1108** | **0.1108** |

Frontal identisch, diagonal um Faktor 1.53 in der Flaeche groesser — die diagonale Kamera
steht heute naeher. Der Blender-Bericht nennt den Grund selbst: bei `s` entscheidet
`kamera.massgebend = "breite"`, bei `sSE` **`"untergrenze"`**. Diese Untergrenze kam am
01.09. in `kameras.py` dazu (`e99caba`, *«Eine Probe, die immer 0.700 meldete»*), also am
Tag der Studie oder danach. Die Geometrie ist unveraendert — `bbox_bauwerk` ist in beiden
Richtungen dieselbe.

**Damit gilt: das publizierte diagonale Fenster `(0.5311, 0.9065]` ist auf diesem
Repostand nicht mehr reproduzierbar.** Auf heutigen Renders liefert derselbe Weg
`(0.5826, 0.9223]`. Das aendert nichts an der Kernaussage jener Studie (beide Fenster
ueberschneiden sich weiterhin nicht), aber die vier Zahlen sind nicht mehr dieselben.

---

## 1 · Was der Schaetzer allein kostet — `treu` ist nicht mehr 1.0000

Mit gebauten Karten ist `treu` per Konstruktion 1.0000, auf allen sechzehn Ansichten.
Geschaetzt ist es das nicht mehr, und **das ist die Zahl, die es bisher nicht gab**:

| Szene | `s` | `w` | `sSE` | `nNE` |
|---|---|---|---|---|
| `quader` | 0.9963 | 0.9980 | 0.9709 | 0.9806 |
| `hochbau` | 0.9043 | **0.6559** | 0.9748 | 0.9579 |
| `gelaende` | 0.9366 | **0.2115** | 0.9877 | 0.9798 |
| `raeume` | 0.9963 | 0.9980 | 0.9709 | 0.9806 |

*(ρ der reinen Schaetzung gegen das Soll ueber der Maske, gerichtet.)*

**Diagonal kostet der Schaetzer wenig (0.9579 bis 0.9877), frontal bis zu 0.7885.** Der
Verlust ist nicht gleichmaessig verteilt, sondern trifft die frontalen Ansichten der
beiden Szenen, deren Fassade eine kleine Tiefenspanne hat.

**Und daraus folgt sofort der schaerfste Einzelsatz dieser Messung:**

> `PAAR_RHO_SCHWELLE = 0.80` sperrt auf **zwei von acht** frontalen Ansichten das
> **perfekte Blender-Bild selbst** — `hochbau-w` bei 0.6559 und `gelaende-w` bei 0.2115.
> Diagonal auf keiner von acht.

Ein Bild, an dem nichts falsch ist, faellt durch — nicht wegen des Bildes, sondern wegen
des Schaetzers. Mit gebauten Karten war das unsichtbar, weil `treu` dort immer 1.0000 war.

---

## 2 · V2 · Die fehlerfreien Fenster je Richtungsgruppe

Gerechnet aus V1 und aus sonst nichts:

| Gruppe | hoechster schlechter | niedrigster guter | Fenster |
|---|---|---|---|
| **frontal** | **0.9957** | **0.1426** | **keines — UEBERLAPPEND** |
| **diagonal** | 0.5906 | 0.9468 | **0.5906 < t ≤ 0.9468** |

Zum Vergleich, dieselben vier Zahlen mit gebauten Karten (Gegenprobe oben):

| Gruppe | gebaut | geschaetzt |
|---|---|---|
| frontal | 0.2568 / 0.3790 — trennt sauber | 0.9957 / 0.1426 — **trennt nicht** |
| diagonal | 0.5826 / 0.9223 — trennt sauber | 0.5906 / 0.9468 — trennt sauber |

**Der Befund vom 01.09. haelt fuer diagonal und faellt fuer frontal.** Die Studie vom
01.09. sagte voraus, ein echter Schaetzer koenne die Luecke zwischen den Gruppen «nur
vergroessern». Gemessen ist es schlimmer als das: **auf frontalen Richtungen gibt es
ueberhaupt kein fehlerfreies Fenster mehr.** Guter und schlechter Bereich liegen
ineinander — 0.1426 bis 0.9957 gegen 0.1426 bis 0.9980.

Entdoppelt aendert sich daran nichts: frontal bleibt ueberlappend, diagonal behaelt
dasselbe Fenster auf allen Stellen. Die Randfaelle sind keine Dubletten.

Alle acht Kurven melden weiterhin `genuegt_als_kalibrierung: false`, mit zwei
Vorbehalten je Kurve: dem mitgegebenen Herkunftsvorbehalt (das Bild kommt aus Blender,
nicht aus dem Bildmodell — der Fehler der Bilderzeugung steht nicht drin) und den nicht
messbaren `flach`-Faellen. Der **Umfangsvorbehalt ist diesmal weg**: entdoppelt bleiben
je Gruppe 30 gute und 29 schlechte Zeilen, ueber allen Mindestmassen. Der Grund ist der
Schaetzer selbst — er loest die analytischen Fixpunkte `treu` und `skala` auf, die vorher
ueber alle Szenen denselben Wert hatten. Dubletten: **58 von 176** statt 87.

---

## 3 · Der eine Fall, der das frontale Fenster zerbricht — der Mechanismus ist gemessen

Ein einzelner schlechter Fall steht bei ρ = **+0.9957**: `quader-w-versatz_20px`
(und seine Kopie `raeume-w-versatz_20px`). Mit gebauten Karten liegt derselbe Fall bei
**−0.0282**. Eine Differenz von **+1.0239** an derselben Ansicht, derselben Stoerung,
demselben Render.

Nicht erzaehlt, sondern nachgemessen an `quader-w`:

```
Maske: 5635 Punkte, x 53..145, y 66..126
Maskenpunkte, deren Quelle (x−20) AUSSERHALB der Maske liegt: 1220 (21.7 %)

Punktmenge                            gebaut     geschaetzt
ganze Maske                          −0.0282       +0.9957
nur Quelle INNERHALB der Maske       +1.0000       +0.9974   (n=4415)
nur Quelle AUSSERHALB der Maske         None       +0.9873   (n=1220)

An den fremden Quellen: SOLL ist 1220/1220 mal die Hintergrundmarke 1e10
SCHAETZUNG dort: 3.395..3.682     in der Maske: 2.281..3.465     -> Bereiche UEBERLAPPEN
```

**Der Sprung an der Silhouette ist der ganze Unterschied.** In der gebauten Karte steht
hinter dem Umriss die Hintergrundmarke — eine Konstante ohne Rangfolge. Rutscht das Bild
20 Punkte zur Seite, wandern 21.7 % der gewerteten Punkte auf diese Konstante, ρ ueber sie
allein ist nicht einmal definiert, und die Gesamtzahl faellt von 1.0000 auf −0.0282.

Der Schaetzer kennt diese Marke nicht. Er gibt dem Himmel neben der Fassade ganz
gewoehnliche Werte, und die liegen **im selben Bereich wie die Fassade selbst**
(3.395–3.682 gegen 2.281–3.465). Der verrutschte Streifen korreliert deshalb weiter mit
dem Soll — allein ueber diese 1220 Punkte mit **+0.9873**. Ein um 20 Punkte versetztes
Bauwerk sieht fuer ρ fast so aus wie ein richtiges.

> **Was die perfekte Karte an einer unendlichen Kante faengt, glaettet der Schaetzer weg.**
> Das ist genau die Fehlerklasse, die eine Obergrenze mit gebauten Karten nicht sehen
> kann — und der Grund, warum diese Messung noetig war.

Das passt zum eigenen Befund `auf-vis-20260824-10`: 95.75 % der Varianz auf einem leeren
Bild stammen aus einem festen Ortsfeld. Ein Feld, das vor allem vom Bildort abhaengt,
ueberlebt eine seitliche Verschiebung.

---

## 4 · V3 · Was `0.80` heute kostet — die Zahl, die niemand kannte

| Gruppe | gute Zeilen | **falsch gesperrt** | schlechte Zeilen (messbar) | **falsch bestanden** |
|---|---|---|---|---|
| **frontal** | 40 | **11** | 48 (40) | **2** |
| **diagonal** | 40 | **0** | 48 (40) | **0** |

**Elf, nicht fuenf.** Mit gebauten Karten sperrt `0.80` fuenf gute frontale Faelle; mit
echtem Schaetzer sind es elf von vierzig:

| Fall | ρ |
|---|---|
| `gelaende-w-rausch_leicht` | 0.1426 |
| `gelaende-w-versatz_1px` | 0.1738 |
| `gelaende-w-glatt_leicht` | 0.2022 |
| `gelaende-w-treu` | **0.2115** |
| `gelaende-w-skala` | **0.2115** |
| `hochbau-w-versatz_1px` | 0.6201 |
| `hochbau-w-glatt_leicht` | 0.6362 |
| `hochbau-w-rausch_leicht` | 0.6453 |
| `hochbau-w-treu` | **0.6559** |
| `hochbau-w-skala` | **0.6559** |
| `gelaende-s-rausch_leicht` | 0.7154 |

Es sind nicht elf verschiedene Konstellationen, sondern **zwei Ansichten mit je fuenf
Faellen plus eine**: `gelaende-w` und `hochbau-w` fallen vollstaendig durch, samt ihrem
perfekten Bild. Die Sperre haengt nicht an der Stoerung, sondern an der **Ansicht**.

**Und die andere Spalte ist neu und schwerer.** Mit gebauten Karten liess `0.80` in beiden
Gruppen **null** schlechte Faelle durch — das war die tragende Rechtfertigung der Zahl.
Mit echtem Schaetzer kommen **zwei** durch:

| Fall | ρ |
|---|---|
| `quader-w-versatz_20px` | 0.9957 |
| `raeume-w-versatz_20px` | 0.9957 |

Da `raeume` eine Kopie von `quader` ist (siehe unten), ist es **eine** Konstellation, an
zwei Stellen gezaehlt. Sie geht nicht knapp durch: **28 der 40 guten frontalen Zeilen
liegen unter ihr**, nur 12 darueber. Ein um 20 Punkte verschobenes Bauwerk erreicht ein
besseres ρ als sieben Achtel der richtigen Bilder derselben Gruppe.

**Der Satz, den die Studie vom 01.09. traegt — «kein einziger schlechter Fall kommt
durch, in keiner Richtung» — gilt unter Schaetzerrauschen nicht mehr.**

Keine Empfehlung. Welcher der beiden Fehler schwerer wiegt, ist ein Entscheid und keine
Messung, und er gehoert dem Owner.

---

## 5 · Der Kantenanteil trennt weiterhin in keiner Gruppe

| Gruppe | hoechster schlechter | niedrigster guter | Trennung |
|---|---|---|---|
| frontal | 1.0000 | 0.3113 | **ueberlappend** |
| diagonal | 1.0000 | 0.4969 | **ueberlappend** |

Unveraendert im Befund: Der beste schlechte Fall erreicht in beiden Gruppen den
Hoechstwert. Es ist `innen_vertauscht` — vollkommener Umriss, gespiegelte Tiefen, ρ
zwischen −0.9980 und −0.2115. Es gibt keine Schwelle, die ihn sperrt, ohne jeden guten
mitzusperren. Der niedrigste gute Wert sinkt gegenueber der gebauten Fassung — in der
Gegenprobe auf denselben Renders gemessen, nicht zitiert: frontal 0.4967 → **0.3113**,
diagonal 0.5184 → **0.4969**. Die Aussage bleibt dieselbe.

Bei `PAAR_KANTENANTEIL_SCHWELLE = 0.20` sperrt er weiterhin **null** gute Faelle und laesst
den grossen Teil der schlechten durch. Das ist kein Argument, ihn zu entfernen — beide
Masse versagen weiter in entgegengesetzte Richtungen —, aber es ist auch kein Argument
fuer die 0.20.

---

## 6 · Was mitgemessen wurde, damit niemand raten muss

**Die Hintergrundmarke hat die Messung nicht beruehrt.** `faelle()` fuellt bei `versatz_*`
und `gedreht_90` die leergeschobenen Spalten mit 1e10. Auf einer Disparitaetskarte ist das
sinnverkehrt — «weit» waere dort ein *kleiner* Wert. Darum fuehrt jede Zeile
`n_marke_in_maske` mit: die Zahl der **gewerteten** Punkte, die diese Marke wirklich
tragen. Sie ist in **allen 176 Zeilen null**. Der Einwand ist damit gemessen und nicht
weggeredet: Die Maske liegt bei x ≥ 53, die Fuellspalten bei x < 20.

**`bauwerk_weg` ist jetzt ueberall messbar — und faellt ueberall durch.** Mit gebauten
Karten war ρ auf den drei Szenen ohne Gelaende `None`, weil hinter dem Bauwerk nur die
Hintergrundmarke stand. Die Schaetzung kennt keine Marke und liefert auch fuer den Himmel
eine gewoehnliche Zahl; damit findet der Ersatz immer einen Wert. Gemessen:

| Gruppe | Spanne von `bauwerk_weg` |
|---|---|
| frontal | −0.0647 .. +0.0153 |
| diagonal | −0.0635 .. +0.1270 |

Alle sechzehn Zeilen liegen dicht bei null. **Ein verschwundenes Bauwerk faellt bei ρ auch
mit echtem Schaetzer klar durch** — das ist die Antwort auf die alte Frage V3 aus
`auf-61`, jetzt gemessen statt zitiert, und sie ist ein Gewinn: der Fall ist nicht mehr
«nicht beurteilbar», sondern beurteilt.

**Nicht messbar bleiben 16 Zeilen**, je eine Ansicht: `flach`. Eine konstante Karte hat
keine Rangfolge, ρ und Kantenanteil sind `None`. Sie sind gezaehlt und benannt, nicht
weggelassen.

**Die vierte Szene ist weiterhin keine.** `raeume` liefert in **44 von 44** Zeilen exakt
dieselben Zahlen wie `quader` — die beiden innenliegenden `IfcSpace` sind von aussen nicht
zu sehen, und der Schaetzer sieht sie so wenig wie die gebaute Karte. `gelaende` ist
dagegen eine echte vierte Sicht: nur 8 von 44 Zeilen sind mit `quader` identisch.
Gemessen sind drei Szenen, nicht vier.

---

## 7 · Was diese Messung nicht traegt

* **Keine Empfehlung.** Weder fuer eine richtungsabhaengige Schwelle noch fuer eine andere
  Zahl. Die Tabelle ist die Vorlage, der Entscheid ist es nicht.
* **Keine Kalibrierung.** Alle acht Kurven melden `genuegt_als_kalibrierung: false`. Der
  Grund ist diesmal nicht der Umfang, sondern die Herkunft: Das Bild kommt aus Blender und
  nicht aus dem Bildmodell. Der Fehler des **Schaetzers** steht in diesen Zahlen, der
  Fehler der **Bilderzeugung** nicht.
* **Die elf Stoerungen sind auf die geschaetzte Karte gerechnet, nicht auf das Bild.** Das
  ist die bewusste Wahl fuer Vergleichbarkeit — eine Aenderung je Lauf. Eine Studie, die
  das *Bild* stoert und danach neu schaetzt, waere die naechste und eine andere; drei der
  elf Faelle (`flach`, `rauschen`, `innen_vertauscht`) liessen sich darin gar nicht
  ausdruecken.
* **Ein Fehler im eigenen Werkzeug, gefunden und behoben.** Die Spalte `rho_roh` las den
  Schluessel `spearman`; `rho_ueber_maske` liefert das rohe Spearman aber unter `rho`. Die
  Spalte war im ersten Lauf in allen 176 Zeilen still `None`. Behoben, neu gerechnet, und
  der Grund steht als Kommentar an der Stelle. Die abgelegte Tabelle ist die korrigierte
  (160 von 176 Zeilen gefuellt; die 16 `flach` bleiben `None`, richtigerweise).

---

## Anhang · Wo die Zahlen herkommen

```
nvidia-smi --query-gpu=power.draw,memory.used --format=csv,noheader   # vor jedem Lauf
AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \
  .venv-render/bin/python tools/studie_echtschaetzer.py build/echt
```

16 Multipass-Laeufe (4 Szenen × 4 Richtungen, 192 px, 6 Samples), 16 Schaetzungen,
daraus 176 Zeilen und acht Trennkurven. Rechenzeit ohne Render 8.5 s.

* **V1** — `auf-20260907-81-falltabelle.json`, 176 Zeilen. Je Zeile `szene`, `kamera`,
  **`gruppe`** (frontal/diagonal, in **jeder** Zeile), `art`, `gut`, `rho` (gerichtet),
  `rho_roh`, `kantenanteil`, `paarurteil_bestanden` / `_gemessen` / `_zustaendig` /
  `_traeger`, `geometrieanteil`, `bodenanteil`, `n_marke_in_maske`.
* **Gegenprobe** — `auf-20260907-81-gegenprobe-gebaut.json`, dieselben 176 Zeilen auf
  denselben Renders, aber mit gebauten Ist-Karten.
* Werkzeug: `tools/studie_echtschaetzer.py`. Es importiert `_bericht`, `dubletten`,
  `gruppe` und die Konstanten aus `tools/studie_ersatzkalibrierung.py` und die elf Faelle
  aus `tools/studie_paarmasse.py` unveraendert — nachgebaut ist nichts.

**Nichts in dieser Auswertung ist aus der publizierten Markdown-Tabelle
zurueckuebersetzt.** Die Vergleichszahlen mit gebauten Karten sind in dieser Sitzung neu
gerechnet; wo sie von der Veroeffentlichung abweichen, steht die Abweichung in Kapitel 0.
