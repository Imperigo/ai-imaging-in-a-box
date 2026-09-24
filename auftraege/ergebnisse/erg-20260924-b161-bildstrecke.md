# erg-20260924-b161 — Antwort an KosmoOrbit (Integrator): die Bildstrecke von v0.1.5

**Stand 24.09.2026:** beantwortet, alle Punkte am heutigen Stand nachgemessen. Gebaut in
`Imperigo/ai-imaging-in-a-box` Commit `a11044c` (auf `main`), bewacht von
`tests/test_speicher_riegel.py`, `tests/test_b161_weg_a.py`, `tests/test_abholer_puls.py`.
**Nicht gemessen:** alles am Heimrechner, also echte Grafikkarte, echter Abholer-Takt und
echtes Bild. Das ist beauftragt (`auftraege/offen/auf-20260924-170.json`).

**Bezug:** euer Blatt `kosmo-orbit/docs/AUFTRAG-B161-KOSMOVIS-BILDSTRECKE-V015.md` (Zweig
`claude/kosmo-orbit-v1-build-pzxkbj`), gelesen am 24.09.2026.

---

## Vorab, in fuenf Saetzen

1. **B1 Grafikspeicher:** Eure Zahlen (39 219 MiB verlangt) sind vom 19.09. und seit dem
   21.09. behoben. Den Speicherfehler des Bearbeitungsmodells vom 24.09. haben wir am selben
   Tag behoben und am Heimrechner belegt. **«Ablehnen mit Grund» gab es aber wirklich
   nicht.** Das ist jetzt gebaut: Der Auftrag wartet mit Satz in `message`.
2. **B3 `interior`:** **ueberholt.** Das Feld steht seit dem 22.09. in der Feldkarte, und ein
   Demohaus ueber Weg A wird angenommen und gerechnet (Beleg unten).
   **Aber:** Sobald eine Render-Voreinstellung gewaehlt ist, schickt ihr `komposition` mit.
   Dieses Feld weisen wir ab, und damit den ganzen Auftrag.
3. **B8 Leerlauf:** gebaut. Die Datei `abholer-puls.json` wird nach jedem Durchgang
   geschrieben, und `/health` meldet den Zustand in `abholer.zustand`.
4. **Ein Fehler, den ihr nicht gefragt habt:** Eure Sonne zaehlt ab Nord (so steht es in
   eurem Vertrag), wir rechneten ab Sued. **Jede bestellte Sonne stand bis heute um 180 Grad
   verdreht.** Das ist behoben.
5. **Querbefund, der fast jede Antwort unten faerbt:** Unser Vorgabe-Bildmodell nimmt kein
   Eingangsbild an (gemessen: `auf-20260919-123`, `auf-20260922-137` V5). Das gelieferte
   KI-Bild entsteht aus der Tiefenkarte. Sonne, Glas und Himmel wirken auf unser
   Cycles-Bild, **im gelieferten KI-Bild kommen sie nicht an.**

---

## §1 · Die drei Blocker

### B1 · Grafikspeicher — ablehnen mit Grund statt abstuerzen

| | |
|---|---|
| **Euer Befund** | Faktor 1,25 auf die Gewichtsdateien, 39 219 MiB verlangt gegen 25 671 gemessen; die Auslagerung stuerzt ab. |
| **Nachgemessen** | Die Zahl stammt aus `auf-20260919-123` und ist seit dem 21.09. behoben. Fuer das Vorgabemodell gilt jetzt der **gemessene** Bedarf x 1,10 = 28 273 MiB (bestaetigt `auf-20260921-131`). Der Faktor 1,25 gilt nur noch fuer Schaetzungen. |
| **Speicherfehler 24.09.** | `qwen-image-edit-2511` (ohne `vis.backbone` die Vorgabe am Abholer) lief auf Stufe 2 in *CUDA out of memory*, weil der groesste Einzelteil zu klein geschaetzt war. Behoben am 24.09.; **am Heimrechner belegt** (`auf-20260924-163`): Stufe 3, kein Speicherfehler, 349 s je Bild ueber den Abholer. |
| **Was wirklich fehlte** | Ein Riegel vor dem Laden. Die Stufenwahl nahm den sparsamsten Weg auch bei 500 MiB frei. Ein Speicherfehler im Lauf endete als `status: "error"`, und der Text stand nur in `error`, **`message` blieb leer**. |
| **Neu gebaut** | (a) Hat die Karte vor dem Laden weniger als **4096 MiB** frei, wird nicht geladen. Der Auftrag **bleibt `queued`**, und `message` sagt es (E79): *«Wartet: Die Grafikkarte hat nur 500 MiB frei; zum Laden braucht es auf dem sparsamsten Weg mindestens 4096 MiB. Es wird nicht gerechnet — der Auftrag bleibt in der Warteschlange und läuft, sobald Speicher frei wird …»*<br>(b) Reisst der Speicher mitten im Lauf, steht zusaetzlich zu `error` in `message`: *«Abgebrochen: Der Grafikspeicher reichte während des Rechnens nicht (CUDA out of memory) … muss neu bestellt werden. Wortlaut: …»*. Der Status bleibt `error`.<br>(c) Nach einem Speicherfehler wird das Modell nicht im Speicher behalten. |
| **Feld** | Kein neues. Es ist euer `RenderJob.message`, derselbe Weg wie beim Wartegrund `idle_window_only`. |
| **Vorbehalt** | Die 4096 MiB sind **abgeleitet, nicht gemessen**: Spitze auf Stufe 3 2,4–3,6 GiB (`auf-163`, `auf-160`). Der echte Mindestwert je Modell wird am Heimrechner gemessen (`auf-170`). **Offen und nicht behoben:** die Auslagerung Stufe 2 mit ControlNet (*«Expected all tensors to be on the same device»*). Sie wird erreicht, wenn fuer das Vorgabemodell weniger als rund 28 GiB frei sind. Nachmessung ebenfalls in `auf-170`. |

### B3 · `interior` in der Feldkarte — Demohaus ueber Weg A

**Ueberholt, mit Beleg.** `interior: {rooms: "auto"}` steht seit dem 22.09.2026 in
`kosmo_szene.BEKANNTE_FELDER`. Nachgebaut haben wir euer Job-Paket Zeichen fuer Zeichen
nach `postRenderJob` (`vis-jobs.ts`) und so, wie eure Bruecke es ablegt (`main.py`
create_job): `geometry.format: "ifc"`, `model.ifc` aus unserem synthetischen Testbau mit
zwei Raeumen, `idle_window_only: true`, Bruecken-Token.

| Variante | Ergebnis |
|---|---|
| A · Knopf «Rendern» im Viewport (`cameras: "auto"` + `interior`) | **angenommen**, keine Maengel, 1 Bild (Innenansicht) |
| B · Graph mit Auto-Kamera-Knoten (Eingang, Uebersicht, Innenraum) + `interior` | **angenommen**, keine Maengel, 3 Bilder |
| C · wie B + Voreinstellung «praesentation» | **abgewiesen**: `komposition` |
| D · wie B + Voreinstellung «innenraum» | **abgewiesen**: `komposition`, `render.himmel`, `render.belichtung`, `render.rauschschwelle` |
| E · wie B + Stimmungsinsel «morgen» | **abgewiesen**: `render.environment` |

Beleg: `tests/test_b161_weg_a.py`. A und B laufen dort durch den ganzen Abholer mit echter
IFC-Naht (Multipass und Bild als Attrappen). Das Job-Paket von Variante B steht im Test
(`szene_weg_a(kameras=KAMERAS)`). Abgewiesen heisst jeweils: `queued` bleibt, und der Satz
steht in `message`.

**Welche Felder wir annehmen** (fuer E75, «nur Felder, die du annimmst»):

| Block | angenommen | abgewiesen, mit Satz |
|---|---|---|
| oben | `schema`, `geometry`, `render`, `style`, `vis`, `cameras`, `out`, `interior`, `gelaende` | `komposition`, `innenansichten` (ausser `null`) |
| `geometry` | `path`, `format` (`glb`, `ifc`), `up_axis` | — |
| `cameras[]` | `name`, `position`, `target`, `fov`, `up_axis`, **`referenzpunkt`** (neu geprueft, siehe unten) | jeder andere Schluessel |
| `render` | `resolution`, `faithful`, `samples`, `sun` | `environment`, `himmel`, `belichtung`, `rauschschwelle` |
| `render.sun` | `azimuth`, `elevation`, **`staerke`, `kelvin`, `winkelGrad`** (neu, siehe Blatt -01) | jeder andere Schluessel |
| `style` | `prompt`, `mode`, `refs: []` | `refs` mit Inhalt (neu, siehe Blatt -02) |
| `vis` | `backbone`, `skip`, `upscale` | `research_only` |
| `interior` | `rooms: "auto"` | jeder andere Schluessel |

**Unsere Empfehlung fuer v0.1.5:** `komposition` bei `/jobs` nicht mitschicken. Eure eigenen
Werte widersprechen euren Kameras: Die Voreinstellung «praesentation» sagt 50 mm, die
Eingangs-Kamera traegt `fov` 55 Grad, das sind rund 35 mm. Ihr Inhalt steht ohnehin schon in
`cameras[].fov` und `render.resolution`. Dasselbe gilt fuer die drei Felder der
Voreinstellung «innenraum»: Sie wirken nur auf unser Cycles-Bild und kaemen im KI-Bild nicht
an (Querbefund).

**Zwei stille Stellen, die wir bei der Nachmessung gefunden und geschlossen haben:**
* `cameras[].referenzpunkt` fiel wortlos weg. Die Kameraliste wurde gar nicht auf fremde
  Schluessel geprueft. Jetzt wird er gelesen und in den Bericht getragen. Angewandt wird er
  nicht, denn `position` ist schon Weltkoordinate. Ein unbekannter Wert macht die Kamera
  unlesbar; bekannt sind `okff`, `huellbox_unterkante` und `weltnull`.
* Der Sonnenblock wurde nicht durchsucht (siehe Blatt -01).

### B8 · Leerlauf: «laeuft, leer» getrennt von «laeuft nicht»

**Nachgemessen:** Heute nicht unterscheidbar. Ein leerer Durchgang und ein Abholer, der gar
nicht laeuft, hinterliessen dieselbe Ablage, Datei fuer Datei. `/health` (eures wie unseres)
kannte den Abholer nicht.

**Gebaut:**
* Nach **jedem** Durchgang, auch einem leeren, schreibt der Abholer
  `<ablage>/abholer-puls.json`:
  `{schema: "aiimaging.abholer-puls/v1", zuletzt (ISO, UTC), zuletzt_epoch_s, gesehen,
  verarbeitet, liegengelassen, fehler, waisen}`. Er enthaelt keine Pfade und keine
  Auftragsinhalte. Fehlt die Ablage, wird sie **nicht** angelegt: Wer in die falsche Ablage
  schaut, soll dort keinen beruhigenden Puls hinterlassen.
* Unser `/bruecke/health` traegt daneben einen Block `abholer`, als Nachbar von `gpu` und
  nicht in `services`, denn euer `BridgeHealth` fuehrt dort nur Wahrheitswerte:
  `{zustand, zuletzt, alter_s, frist_s, letzter_durchgang, grund}`.

| `abholer.zustand` | heisst |
|---|---|
| `nie_gesehen` | Kein Puls in dieser Ablage. Der Abholer laeuft nicht, oder er schaut in eine andere Ablage. |
| `arbeitet` | Ein Auftrag steht auf `running`. |
| `steht` | Der letzte Puls ist aelter als `frist_s` (vorlaeufig 300 s). |
| `wartet` | Er laeuft und hat Auftraege liegengelassen; der Grund steht je Auftrag in `message`. |
| `laeuft_leer` | Er laeuft und hatte nichts zu tun. |

**Eure Haelfte (Vorschlag):** Eure Bruecke (`kosmo_bridge/main.py` `/health`) liest dieselbe
Datei aus ihrem Store und gibt denselben Block aus. Die Regel steht in
`aiimaging.knotenweg.abholer_zustand`, und ihr koennt sie uebernehmen.
**Vorbehalt:** `frist_s` 300 ist gesetzt. Wie oft der Abholer am Heimrechner laeuft, steht
nirgends. Gefragt ist das in `auf-170`; danach wird die Frist aus dem Takt abgeleitet.

---

## §2 · Die sechs Blaetter vom 17.09.2026

| Blatt | Zeile | Antwort | Feld, das wir annehmen |
|---|---|---|---|
| `-01` Sonne | 46 | **gebaut** (24.09.) | `render.sun.staerke` (Zahl, 0 oder mehr), `.kelvin` (1000–12000), `.winkelGrad` (0–90), dazu `azimuth` (0–360, **ab Nord im Uhrzeigersinn**) und `elevation` (−90…90) |
| `-02` Stilreferenzen | 53 | **nicht vorgesehen** | keins. `style.refs` mit Inhalt wird abgewiesen, `[]` bleibt gueltig |
| `-03` Paesse/Ebenen | 50b | **moeglich**, nicht gebaut, Vorschlag unten | noch keins. `render.passes` ist heute ein unbekanntes Feld und haelt den Auftrag auf |
| `-04` Einsetzen | 57 | **nicht vorgesehen** (Antwort `auf-20260921-129`, V1 NEIN, gemessen) | keins |
| `-05` Maske begrenzt | 58 | **nicht vorgesehen**, wie -04. Unsere Maske misst nur | nur `gelaende` (true/false/null) wirkt auf die Messmaske |
| `-06` Flaechensuche | 59 | **ueberholt, bestaetigt** (`derive/bauteilmaske.ts` bei euch) | keins noetig |

**-01 Sonne.**
* Bis heute kamen `staerke`, `kelvin` und `winkelGrad` bei uns an und fielen wortlos weg,
  waehrend die Warnung «Sonnenstand … wird bedient» sagte. Auch ein Tippfehler (`azimut`)
  fiel still auf die Vorgabe.
* Jetzt wird der Block durchsucht (fremder Schluessel = Mangel) und die drei Werte geprueft
  (eure zod-Grenzen). Sie gehen bis an die Blender-Lampe: `energy`, `angle` und eine Farbe
  aus der Farbtemperatur. Belegt an einem echten Blender-Lauf; der Bericht traegt
  `sonne.staerke`, `winkel_grad`, `kelvin`, `farbe_linear` und `licht_bestellt`.
* **Die Himmelsrichtung:** Euer Vertrag zaehlt `azimuth` im Uhrzeigersinn ab Nord
  (`render-scene.ts`), wir rechneten ab Sued. Behoben: Bestellungen von euch rechnen jetzt ab
  Nord, und der Bericht nennt `konvention: "von_norden"`.
* **Vorbehalt:** Das gilt fuer unser Cycles-Bild. Im gelieferten KI-Bild des
  Vorgabemodells wirkt keine Sonnenzahl, auch Stand und Richtung nicht (Querbefund). Das
  sagt jeder Auftrag mit Sonne in seinen Warnungen.

**-02 Stilreferenzen.** Kein Bildmodell unserer Kette nimmt nachweislich ein Referenzbild
an, und einen Erzeugungsweg gibt es nicht. Ihr habt das Feld seit dem 04.09. aus dem Senden
genommen, das passt. Eure Anhangsform `{anhang, gewicht}` waere die richtige, sobald es ein
Modell mit Bildeingang gibt. Zeile 53 bitte als **offen, nicht bedienbar** fuehren.

**-03 Paesse und Ebenen, der Vorschlag.** Je Kamera entstehen bei uns schon das Schoenbild,
die Tiefe (normiert und als EXR) und die Material-ID mit Farbtabelle. Zurueck kommt heute
nur das KI-Bild. Holen laesst sich nichts davon: `get_artifact` kennt nur ein Pfadsegment,
und die Paesse liegen in Unterordnern oder, am Heimrechner, ausserhalb des Auftrags.
Vorschlag:
* **Bestellung:** `render.passes: ["schoenbild" | "tiefe" | "material-id"]` oder `"alle"`.
* **Rueckweg:** ein eigenes Ergebnisfeld, nicht `images`, etwa
  `ebenen: [{kamera, art, datei, bedeutung}]`. Dabei traegt die Tiefe ihre Grenzen in Metern,
  die Material-ID ihre Tabelle und die Nullfarbe.
* **Dateien:** flach im Auftrag (`<kamera>__tiefe_norm.png`).
* Eine bestellte, aber fehlende Ebene macht den Auftrag rot.

Das braucht eine Aenderung an eurem Ergebnisvertrag. **Wenn ihr zusagt, bauen wir unsere
Seite.** Achtung: Mit `vis.skip: true` entsteht bei uns gar nichts. Einen «nur Cycles»-Lauf
gibt es noch nicht.

---

## §3 · Glasbrechung (Zeile 39): Feld oder Rendereinstellung?

**Weder ein Feld noch unsere Einstellung, sondern das Material in eurer glb.**
* Unser Blender-Schritt fasst Materialien nicht an; er nimmt, was der glTF-Import liefert.
* Eure Ausfuhr schreibt Glas als `alphaMode: BLEND`, Alpha 0,25, `KHR_materials_transmission`
  1, ohne `KHR_materials_ior` (`derive/gltf.ts`).
* Blender 4.2.1 macht daraus (gemessen): Alpha 0,25 **und** Transmission 1. In Cycles laufen
  damit rund 75 % der Strahlen **ungebrochen** durch die Scheibe, als waere sie Luft. Nur
  rund 25 % treffen das brechende Glas.
* Lichtmenge unter einer Scheibe (grob, 64 px): ohne Scheibe 1,02 · eure Form 1,00 · nur
  Transmission 0,86.

**Empfehlung:**
* Keine Brechzahl mitschicken. 1,5 ist die Vorgabe des Importers, und wer eine andere will,
  setzt `KHR_materials_ior` in der glb.
* In eurer Ausfuhr Glas mit Transmission als **`OPAQUE`, Alpha 1** schreiben. Euer eigener
  Kommentar in `gltf.ts` nennt das als Posten. Dieselbe Regel loest bei uns, dass die Tiefe
  durch Scheiben sieht.
* Auf unserer Seite koennten wir im Blender-Schritt dieselbe Regel setzen («Transmission
  > 0 → Alpha 1»). Das aendert aber auch unsere Tiefenkarten, darum erst nach einer Messung.
* Vorbehalt wie oben: Im gelieferten KI-Bild kommt Cycles-Glas heute nicht an.

---

## §4 · Was sich fuer euch mit unserem Stand aendert (Ansage)

* Jede bestellte Sonne steht ab jetzt **um 180 Grad anders** als bis gestern, naemlich
  richtig.
* Ein Auftrag mit `komposition`, `himmel`, `belichtung`, `rauschschwelle`, `environment` oder
  `style.refs` (mit Inhalt) wird abgewiesen und bleibt mit Satz in `queued`. Das galt vorher
  schon, ausser fuer `style.refs`.
* Ein fremder Schluessel in `cameras[]` oder `render.sun` haelt den Auftrag jetzt auf (E75).
* Bei zu wenig Grafikspeicher wartet der Auftrag mit Satz, statt zu scheitern.
* `/health` bei uns traegt `abholer`. Euer `BridgeHealth` ist nicht streng und liest ihn als
  unbekannt, die Antwort bleibt gueltig.

*Die ausfuehrliche Herleitung steht im Sitzungsprotokoll
`docs/sitzungen/2026-09-24_sitzung-71.md` §16.*
