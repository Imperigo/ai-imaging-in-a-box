# erg-20260908-93 — `auf-20260909-93` (U10/U11): rho steht in dieser Oberflaeche gar nicht als Zahl, und der Wandanteil kommt nie an

**Stand 08.09.2026:** offen — woran gemessen: beide Befunde sind hier an der echten
Oberflaeche und am echten Kern nachgefahren (Beweis 15 reproduziert, U11 ohne GPU
nachgerechnet, beide Zahlenpaare des Blattes bestaetigt aufs Tausendstel), die Antwort
in System A liegt fertig und ist im Trockenlauf durch `tools/antwort.py` gegangen —
**abgelegt ist sie nicht**, und V3/V4 sind Entscheide des `ui`-Workers, die hier
ausdruecklich nicht getroffen wurden. Offen bleibt genau das: absenden und entscheiden.

**Fremder Auftrag.** `auf-20260909-93` ist an `worker: ui` gerichtet und liegt im Repo
des KosmoVis (`auftraege/offen/` im Repo). Am Blatt wurde nichts geaendert,
keine Stand-Zeile eingetragen, nichts committet, nichts gepusht. Was hier steht, ist
gemessen — nicht entschieden.

**Arbeitsstand:** `Architektur-Cosmos` HEAD `515ec80d`, `ai-imaging-in-a-box` HEAD
`aa54e5d5`, Uhr dieser Maschine `2026-09-08T16:07:46Z`.

---

## 1 · Was hier gemessen wurde

### 1.1 Die zwei rho-Zahlen — nachgefahren, nicht abgeschrieben

```
cd <euer Klon von ai-imaging-in-a-box>
python3 tools/beweis/15_qa_maske.py <ziel>        # EXITCODE 0, 16 Bilder
```

Das Skript schreibt seine Messwerte in die Dateinamen. Wortlaut aus dem Lauf:

| Fall | rho ueber das ganze Bild | rho ueber die Maske | geom_iou Maske |
|---|---|---|---|
| treu | 1.000 | 1.000 | 1.000 |
| umgekehrt (Bauwerk in der Tiefe gespiegelt) | **0.962** | **−1.000** | 1.000 |
| rampe | 0.960 | −0.134 | 1.000 |
| Versatz 0/2/4/8/16 px | 1.000 / 0.999 / 0.998 / 0.997 / **0.993** | 1.000 / 0.740 / 0.498 / 0.064 / **−0.607** | 1.000 / 0.954 / 0.907 / 0.815 / 0.630 |

**Keine Abweichung zum Blatt.** 0,962 gegen −1,000 und 0,993 gegen −0,607 stimmen exakt.
Das Blatt ist an dieser Stelle belegt, und zwar auf dieser Maschine, nicht auf Zuruf.

### 1.2 Der Wandanteil — ohne Blender und ohne GPU nachgerechnet

Die Auflage des Blattes lautet «keine Messung, kein Lauf, keine GPU». Der gerechnete Teil
von Beweis 22 laeuft trotzdem: dieselbe Testgeometrie, derselbe Standpunkt, nur ohne
Cycles. Abstand und Sensorhoehe stammen aus denselben Funktionen wie im Beweis
(`raumkamera.frontaler_standpunkt`, Sensorbreite 36 mm auf 800x496).

```
Raumhoehe 2,700 m · Abstand 4,100 m · Sensorhoehe 22,320 mm · Gleichgewicht 1,350 m
h=0,68 m  boden=0,323  decke=0,000  wand=0,677  roh_decke=−0,031  decken_kante=False
h=1,35 m  boden=0,146  decke=0,146  wand=0,708  beide Kanten True
h=2,02 m  boden=0,000  decke=0,323  wand=0,677  roh_boden=−0,031  boden_kante=False
```

Alle neun Zahlen des Blattes bestaetigt. **Und ein Zusatz, den das Blatt nicht zeigt:**
`1 − roh_boden − roh_decke` ist in allen drei Zeilen **0,708** — die Invariante steckt
exakt in den Rohwerten, und die stehen bereits im Rueckgabewert von
`komposition.bildanteile`.

Daraus folgt eine Praezisierung, die fuer eine Beschriftung zaehlt: Der begrenzte
Wandanteil 0,677 **beschreibt das Bild weiterhin richtig** — bei 0,68 m ist die
Restflaeche tatsaechlich Wand, die Summe der drei Anteile ist 1,000. Was seine
Gueltigkeit verliert, ist nicht die Zahl, sondern die **Aussage** «der Wandanteil haengt
nicht von der Kamerahoehe ab». Das ist ein anderer Satz als «diese Zahl koennte falsch
sein», und er fuehrt zu einer anderen Beschriftung.

### 1.3 Eine Spalte im Blatt hat keinen gezaehlten Gegenwert

Die Ueberschrift im Blatt lautet «gegen den ECHTEN gerenderten Bildinhalt gezaehlt
(Abweichung 0,001)», und darunter steht eine Wandanteil-Spalte. Gelesen in
`tools/beweis/22_innenraum_bildgleichgewicht.py`:

* `_anteile_aus_material_id` zaehlt **nur die Bodenfarbe** und den Hintergrund.
* Der Deckenanteil ist nach dem eigenen Kopftext des Skripts mangels Deckenkoerper
  «nicht messbar» — im Material-ID-Pass steht dort ein schwarzes Band.
* `abw = [abs(g - m) …]` wird ausschliesslich ueber den **Bodenanteil** gebildet.
* `zeilen.append((h, g, m, anteile.get("wandanteil"), …))` nimmt den Wandanteil aus der
  **Rechnung**; ein gezaehlter Wandanteil existiert nirgends.

Die 0,001 gehoeren also dem Bodenanteil. Die Zahl, um die es in U11 geht, ist im Beweis
gerechnet und nicht gezaehlt. Das entwertet U11 nicht — die Rechnung ist ja bestaetigt —
aber die Ueberschrift deckt sie nicht.

### 1.4 Was die Oberflaeche mit rho tatsaechlich macht

Gemessen an den Produktivfunktionen selbst (`varianteMerkmale`, `varianteDiff`,
`bewertungsLage` aus `apps/kosmo-orbit/src/modules/vis/varianten-diff.ts`), gefahren
unter `npx vitest run` in `kosmo-orbit/apps/kosmo-orbit`. Die Sonde wurde nach der
Messung geloescht (`git status` sauber bis auf drei fremde, vorbestehende Eintraege).

**Eingabe A** — beide Zahlen zugleich, `spearman: 0.962`, `rho_maske: -1.000`,
`geom_iou: 1.0`, `status: 'measured'`:

```
Geometrie-Status       | gemessen
Tiefenstaffelung       | verfehlt
Nullprobe (rho_maske)  | —
Bauwerk vorhanden      | —
Enthaelt die Tabelle "-1.00" oder "0.96"?   false   false
```

**Keine der beiden Zahlen erscheint.** `rho_maske` wird gegen `RHO_MASKE_SCHWELLE = 0.8`
(varianten-diff.ts:191) verglichen und zu **einem Wort**. `spearman` — rho ueber das
ganze Bild — hat im Vertrag ein Feld (`render-result.ts:213`), aber in der ganzen
Oberflaeche **null Anzeigestellen**.

**Eingabe B** — nur rho ueber das ganze Bild, `spearman: 0.962`, `geom_iou: 1.0`,
`geometry_fidelity: 0.95`, `passed: true`, kein Maskenweg:

```
bewertungsLage:  "widerrufen"
sterneAusQa:     0
Tiefenstaffelung | —
```

Der Nutzer liest dann woertlich: *«Bewertung zurueckgezogen — die Grundlage dieser Zahlen
ist widerlegt. Die Bildseite liefert die tragfaehigen Werte nach.»*
(`KuratierInspektor.tsx:158-162`). Das ist genau die Antwort, die U10 verlangt — gebaut
am 22.08.2026 aus einem anderen Anlass (die widerrufenen `geom_iou`/`spearman`-Masse).

**Gegenprobe, damit die Null widersprechen kann:** mit `nullprobe: { rho_maske: -0.02 }`
erscheint sehr wohl eine Zahl — `Nullprobe (rho_maske) | -0.02`. Die Oberflaeche kann
also rho drucken; sie tut es nur fuer den Anker, nicht fuer den Hauptwert.

**Was bleibt** — kleiner als der Befund des Blattes, aber es steht da: Das Wort
«Tiefenstaffelung» sagt nicht, worueber gerechnet wurde. Zwei Stellen:
`KuratierInspektor.tsx:72` und `varianten-diff.ts:297`. Und die beiden Sichten sind nicht
deckungsgleich — der Inspektor zeigt nur `Tiefenstaffelung` und `Bauwerk vorhanden`, die
A/B-Tabelle zusaetzlich `Geometrie-Status` und `Nullprobe (rho_maske)`.

### 1.5 Bildaufteilung in der Oberflaeche: null, und die Null kann widersprechen

Gezaehlt ueber `apps/kosmo-orbit/src` und `packages/*/src`:

| Name | Dateien |
|---|---|
| `wandanteil`, `bodenanteil`, `deckenanteil`, `bildanteile`, `boden_kante_im_bild`, `decken_kante_im_bild`, `horizontanteil` | je **0** |
| Gegenprobe `rho_maske` | 4 |
| Gegenprobe `horizontlinie` | 4 |
| Gegenprobe `kante_an_maskengrenze` | 3 |

Und der Grund liegt **vor** der Anzeige: `grep -c 'wandanteil\|bildanteile\|bodenanteil\|komposition'`
ueber `packages/kosmo-contracts/src/render-result.ts` → **0**. Der Ergebnisvertrag hat
kein Feld fuer eine Bildaufteilung. Innenansichten werden sehr wohl bestellt
(`interior.rooms`, `render-scene.ts:118`), zurueck kommt darueber nichts.

### 1.6 Die Gegenrichtung: drei bestellte Zahlen, die niemand liest

`RenderScene` traegt seit dem Owner-Befund K20/A10 ein Objekt `komposition` mit
`seitenverhaeltnis`, `brennweiteMm` und `horizontlinie` (`render-scene.ts:324`), und jedes
Cycles-Preset fuellt es (`render-presets.ts:50/61/72`). Gemessen im Repo des KosmoVis:

```
grep -rIn 'horizontlinie' .            → EXITCODE 1 (kein einziger Treffer, ganzes Repo)
grep -rIln 'seitenverhaeltnis' .       → Treffer (Gegenprobe: der Suchweg funktioniert)
```

Und an der Leseseite selbst, mit einer Bestellung, die `komposition` traegt:

```
lies_szene(...)  → 21 Schluessel, 'komposition' ist keiner davon
warnungen: ()    maengel: ()
stehengebliebene_felder(szene) → 0 Eintraege
GEGENPROBE mit vis.upscale=true → 1 Eintrag ('hochskalieren')
```

Das Feld faellt also still auf den Boden — und `STEHENGEBLIEBEN` (die Liste, die genau
solche Faelle melden soll, U1 aus ihrem eigenen Befundblatt) kennt es nicht. Drei Zahlen,
die eine Bildkomposition beschreiben, werden bestellt und nie gelesen. Das ist derselbe
Fehlertyp wie U10, nur in die andere Richtung: eine Zahl ohne ihre Bedingung, hier ohne
die Bedingung «wird ueberhaupt beachtet».

### 1.7 Die Kennungen U10 und U11 sind schon vergeben

`kosmo-orbit/docs/auftraege-kosmovis/auf-20260827-62.md` fuehrt bereits:

```
Zeile 53  U9  · EIN GRUENES HAEKCHEN DARF DIESEN LAUF NICHT WIE JEDEN ANDEREN ZEIGEN.
Zeile 64  U10 · DER SATZ IST DA ODER NICHT DA — NICHT IMMER.
Zeile 70  U11 · DER VORBEHALT GEHOERT ZUR ZAHL, NICHT AUF EINE ANDERE SEITE.
```

Genau so stehen sie heute im Quelltext der Oberflaeche (`KuratierInspektor.tsx:61-63`,
`NodeCanvas.tsx:435` und `:448`, `varianten-diff.ts:286`). In `docs/UI_BEFUNDE.md`
dagegen heisst U9 etwas anderes («Ein wartender Auftrag hat einen Grund»), und U10/U11
kommen dort ueberhaupt nicht vor (`grep -n 'U10\|U11' docs/UI_BEFUNDE.md` → 0 Treffer).
Es laufen also zwei Zaehlungen mit denselben Nummern, und die neue Nachricht faellt in
die Ueberschneidung.

**Und das Interessante daran:** das alte U11 — «der Vorbehalt gehoert zur Zahl» — ist
gebaut. Die Zeile `QA-Vorbehalt` steht ungekuerzt in derselben Tabelle direkt neben dem
Verdikt und erscheint nur, wenn `qa.verdict.reason` gesetzt ist. Der Mechanismus, den
beide neuen Vorschlaege verlangen, existiert bereits; er traegt heute nur keinen
rho-Bezug und keine Kanten-Bedingung.

### 1.8 Zwei kleinere Beobachtungen

* **Zustellung:** `auf-20260909-93` liegt nicht in `kosmo-orbit/docs/auftraege-kosmovis/`
  (letztes Blatt dort: `auf-20260907-84.md`, 20 Dateien insgesamt — der Weg funktioniert
  also). Der `ui`-Worker hat auf diesem Rechner keine Kopie des Blattes.
* **Datierung:** das Blatt traegt `erstellt: 2026-09-10T00:30:00Z`, die Uhr dieser
  Maschine steht auf `2026-09-08T16:07:46Z`, beide Repos haben ihren letzten Commit vom
  08.09. Zwei Tage Vorlauf. Aendert an den Zahlen nichts.

---

## 2 · Die Antwort in System A

`tools/antwort.py` geht durch `auftrag.baue_ergebnis`, und dort greift eine Grenze, die
im Block an den `ui`-Worker nicht erwaehnt ist: **`_wehre_bilddaten_ab` weist jede
Zeichenkette ueber 2048 Zeichen ab** (`src/aiimaging/auftrag.py:685`). Der erste Anlauf
mit 7443 Zeichen ist daran gescheitert, der zweite mit 2345 und der dritte mit 2170
ebenfalls. Erst diese Fassung geht durch:

```
python3 tools/antwort.py auf-20260909-93 --datei <antwort.txt> --status ok --trocken
WUERDE SCHREIBEN: auftraege/ergebnisse/auf-20260909-93.json (status=ok, 2030 Zeichen)
EXITCODE 0
```

Statuswort **`ok`** — und nicht `abgelehnt`: `antwort.py` weist `abgelehnt` bei einer
`art: frage` selbst zurueck, weil ein begruendetes Nein die vollstaendige Antwort ist.
**Geschrieben wurde nichts** (`--trocken`); das Ablegen ist die Sache des Adressaten.

Der Antworttext (2030 Zeichen), wortgleich wie geprueft:

```text
ABSENDER: HomeStation-Agent, nicht der ui-Worker. V1/V2/V5 gemessen; V3/V4 sind seine Entscheide, offen. Volltext: erg-20260908-93 (Architektur-Cosmos).

V1: Die Oberflaeche druckt rho NICHT als Zahl. Mit spearman 0.962 UND rho_maske -1.000 gibt varianteDiff nur: Tiefenstaffelung «verfehlt», Nullprobe «—». rho_maske wird gegen 0.80 (varianten-diff.ts:191) zu EINEM Wort; spearman hat ein Vertragsfeld, aber 0 Anzeigestellen. U10 tritt so nicht auf. Kommt rho ganz allein an, sagt sie seit 22.08.: «Bewertung zurueckgezogen — die Grundlage dieser Zahlen ist widerlegt» (bewertungsLage=widerrufen, 0 Sterne). Rest: «Tiefenstaffelung» nennt den Bezug nicht (2 Stellen).

V2: tritt nicht auf. wandanteil, bodenanteil, deckenanteil, bildanteile, beide *_kante_im_bild, horizontanteil: je 0 Dateien in src (Gegenprobe rho_maske 4). render-result/v2 hat kein Feld dafuer; interior.rooms wird bestellt, zurueck kommt nichts.

V3/V4: nicht entschieden. Umfang: U10 = 2 Beschriftungsstellen ohne Vertragsaenderung; U11 = 0 Stellen, dafuer erst ein Vertragsfeld.

V5: (a) U9/U10/U11 sind in auf-20260827-62 vergeben und stehen so im UI-Code; UI_BEFUNDE.md kennt U10/U11 nicht (0 Treffer), U9 dort anders belegt. (b) Euer U11-Weg ist gebaut: qa.verdict.reason erscheint ungekuerzt als Zeile «QA-Vorbehalt» neben dem Verdikt — die Kanten-Bedingung dort hineinzulegen kostet 0 Zeilen UI-Code. (c) KosmoOrbit bestellt komposition{seitenverhaeltnis,brennweiteMm,horizontlinie}; horizontlinie: 0 Treffer bei euch, lies_szene liefert 21 Schluessel ohne komposition, STEHENGEBLIEBEN kennt es nicht (0 gegen 1 bei vis.upscale).

BERICHTIGUNG: Abweichung 0,001 gehoert dem Bodenanteil; der Wandanteil ist gerechnet — Beweis 22 zaehlt nur die Bodenfarbe.

NACHGEMESSEN: Beweis 15 reproduziert (0.962/-1.000, 0.993/-0.607). U11 ohne GPU: 0,323/0,146/0,000 und 0,677/0,708/0,677 — identisch. Dazu: 1-roh_boden-roh_decke = 0,708 in allen drei Zeilen; der begrenzte Wandanteil beschreibt das Bild richtig, es faellt die AUSSAGE der Hoehenunabhaengigkeit.
```

---

## 3 · Was beim KosmoVis bleibt

Fuenf Posten. Keiner davon ist hier entschieden worden.

1. **Die Antwort ablegen oder nicht.** Der Text oben ist geprueft und geht durch
   `tools/antwort.py --status ok`. Wer ihn absetzt, entscheidet ihr mit dem Owner — er
   kommt von dieser Maschine, nicht vom `ui`-Worker, und der Absenderhinweis steht in der
   ersten Zeile. Der Befehl ohne `--trocken` schreibt
   `auftraege/ergebnisse/auf-20260909-93.json`.
2. **Die 2048-Zeichen-Grenze gehoert in den Block.** Euer Block
   `auftraege/bloecke/2026-09-10_ui.md` nennt den Rueckweg
   («`auftraege/ergebnisse/<kennung>.json`, committen, pushen»), aber nicht, dass
   `baue_ergebnis` jede Zeichenkette ueber 2048 Zeichen abweist. Die erste ausfuehrliche
   Antwort laeuft dagegen. Ob ihr die Grenze nennt, den Volltext-Weg beschreibt
   (`ANTWORT-<kennung>-volltext.md` neben der JSON, so wie ihr es selbst macht) oder die
   Grenze anhebt — euer Entscheid.
3. **U10 und U11 sind doppelt vergeben.** In `auf-20260827-62` heissen sie bereits etwas
   anderes, und der UI-Code fuehrt diese Bedeutung. In `docs/UI_BEFUNDE.md` stehen die
   neuen Befunde ueberhaupt nicht (0 Treffer) — euer eigenes Blatt verlangt, dass jeder
   Befund entweder weitergegeben oder ausdruecklich als «noch nicht» gefuehrt wird, und
   `tests/test_ui_befunde.py` erzwingt es. Ob ihr umnummeriert oder die Doppelung mit
   einem Praefix aufloest, entscheidet ihr.
4. **Die Ueberschrift ueber eurer U11-Tabelle.** «Gegen den echten gerenderten Bildinhalt
   gezaehlt (Abweichung 0,001)» deckt die Bodenanteil-Spalte, nicht die
   Wandanteil-Spalte. Ob ihr die Spalte als «gerechnet» kennzeichnet, den Beweis um einen
   gezaehlten Wandanteil erweitert (Deckenkoerper in `make_test_ifc.py --raeume`) oder es
   so stehen lasst: eure Sache. Der Befund selbst haelt — er haengt nicht an dieser
   Spalte.
5. **`komposition` aus `RenderScene`.** Drei bestellte Zahlen ohne Leser, und
   `STEHENGEBLIEBEN` meldet sie nicht. Drei Wege stehen euch offen — Eintrag in
   `STEHENGEBLIEBEN` (dann meldet der Abholer «bestellt und nicht ausgefuehrt»),
   tatsaechlich lesen, oder dem `ui`-Worker sagen, dass er es nicht mehr schicken soll.
   Welcher, entscheidet ihr; die Messung liegt in 1.6.

---

## 4 · Was beim `ui`-Worker bleibt (nicht entschieden)

Der Vollstaendigkeit halber getrennt, weil es ihm gehoert und nicht dem KosmoVis:

* **V3** — welcher der beiden Punkte billiger ist. Gemessen ist nur der Umfang: U10 sind
  zwei Beschriftungsstellen ohne Vertragsaenderung, U11 sind null Stellen und ein
  fehlendes Vertragsfeld.
* **V4** — ob er ein neues Feld bestellt und welches. Ohne Feld im
  `render-result`-Vertrag kann eine Bildaufteilung nicht ankommen (1.5).
* Ob «Tiefenstaffelung» einen Bezug bekommt, und ob er im Wort, in einer Klammer oder in
  einem Titel steht.
* Ob er den bereits gebauten Weg ueber `qa.verdict.reason` nutzt oder eigene Zeilen
  vorzieht.

---

## 5 · Was hier nicht messbar war

* **Der gezaehlte Teil von Beweis 22.** Er braucht Blender/Cycles; die Auflage des
  Blattes sagt «keine GPU», und sie wurde eingehalten. Bestaetigt ist der gerechnete
  Teil — was in 1.3 steht, ist am Quelltext des Skripts gelesen, nicht am Bild.
* **Die Oberflaeche im Browser.** Gemessen wurde an den Produktivfunktionen, die die
  Zeilen erzeugen, nicht an einem Bildschirmfoto. Fuer Beschriftungstexte ist das
  dieselbe Quelle; fuer Anordnung und Sichtbarkeit waere es nicht dasselbe. Es wurde
  keine Vorschau gestartet, `:5183` und `:5199` blieben unberuehrt.
* **Ob der `ui`-Worker das Blatt je gesehen hat.** Gemessen ist nur, dass es in seinem
  Zustellordner nicht liegt (1.8).
