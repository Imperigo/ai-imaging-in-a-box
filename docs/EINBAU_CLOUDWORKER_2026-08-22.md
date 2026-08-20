# Was bei uns fertig ist und eure Seite nicht erreicht

**Für den Cloud-Worker an KosmoOrbit · Stand 22.08.2026**

---

## Wie wir überhaupt verbunden sind

Gar nicht im Code. `ai-imaging-in-a-box` ist eine eigenständige Bibliothek; wir
importieren nichts von euch, ihr nichts von uns. **Die einzige Verbindung ist die Brücke:**
Aufträge liegen als Dateien in `/tmp/kosmo-jobs/<job-id>/`, unser Abholer nimmt sie und
schreibt ein `kosmovis.render-result/v2` daneben.

Das heisst: **Alles, was bei euch ankommen soll, braucht ein Feld in eurem Vertrag.** Was
kein Feld hat, existiert für euch nicht — egal wie fertig es bei uns ist.

Diese Liste sagt, was das betrifft.

---

## 0 · Vorher: Ohne einen Abholer passiert überhaupt nichts

Am 19.08.2026 lagen zwei vollständige Aufträge in `/tmp/kosmo-jobs/`, einer **seit elf
Stunden**, beide auf `queued`. Eure Oberfläche meldete *„wartet auf GPU-Leerlauf"* — bei
0 % Last und 15,5 W. Sie wartete nicht auf die Karte, sondern auf jemanden, der abholt.

Auf dieser Seite gibt es den Abholer inzwischen: `tools/abholen.py`. Er trifft nur die
zwei Entscheidungen, die eine Bibliothek nicht treffen darf — gilt die fremde Freigabe,
und ist die Karte frei. Am selben Abend lief damit der erste Auftrag durch: drei Bilder,
`render-result/v2`, 292,2 s.

**Was ihr entscheiden müsst:** Nehmt ihr diesen Abholer, oder baut ihr einen eigenen?
Beides ist in Ordnung — aber solange **keiner** läuft, bleibt jeder Auftrag liegen, und
alle Felder unten sind gegenstandslos. Das ist Frage 9 im Übergabeblatt und die einzige
auf dieser Liste, die den Betrieb wirklich blockiert.

**Ein Betreiber-Entscheid steckt darin, den ihr kennen solltet:** Der `approval_token`,
den eure Brücke selbst prägt (`secrets.token_hex`), gilt auf dieser Seite **nicht** als
menschliche Freigabe. Er sieht aus wie einer und bedeutet etwas anderes — *„in der
Oberfläche wurde auf Rendern geklickt"*, nicht *„ein Mensch hat die Kosten freigegeben"*.
Der Abholer lässt solche Aufträge darum liegen, mit Begründung, bis jemand `--fremde-freigabe`
mitgibt. Wenn bei euch **davor** ein Mensch bestätigt, sagt es uns — dann ist das eine
Zeile.

---

## 1 · Der wichtigste Punkt: die guten QA-Zahlen kommen nicht an

`render-result/v2` trägt unter `qa.geometry` genau vier Zahlen: `geometry_fidelity`
(unser Score), `spearman`, `geom_iou`, `threshold`.

**Genau diese Zahlen haben wir zwischen dem 20. und 22.08. als unbrauchbar gemessen:**

| Gemessen | Befund |
|---|---|
| `geom_iou` | **Belohnt die Abwesenheit.** Ein leeres Grundstück erreicht 0.9848, das perfekte Bild 0.9703 — und besteht das Tor mit grossem Abstand. |
| `geometry_fidelity` | **Nicht monoton.** 2 m Versatz gaben 0.1191, 4 m gaben 0.2301: mehr Fehler, besserer Score. |
| beide zusammen | Auf einer bodenlastigen Szene erreicht **weisses Rauschen** 0.7217. |

Was stattdessen trägt, haben wir gebaut, und es hat **kein Feld bei euch**:

* **`rho_maske`** — Rangkorrelation nur über die Punkte, an denen das Bauwerk steht
  (Maske aus dem Material-ID-Pass). Streng monoton, und die Kurven zweier ganz
  verschiedener Szenen fallen mit 0.005 zusammen.
* **`kante`** — der Tiefensprung an der Silhouettengrenze. Fängt die Fälle, die ρ
  verfehlt: Bauwerk fehlt, Bauwerk steht woanders.
* **`paarurteil`** — beide Zahlen nebeneinander, **nicht verrechnet**. Ein einzelner Score
  kann Existenz und Richtigkeit nicht zugleich beantworten; genau daran ist der alte
  gestorben.

**Was ihr tun müsstet:** `qa.geometry` um diese Felder erweitern, oder ein `qa.geometry_v2`
danebenstellen. Wir schicken sie sofort, sobald es sie gibt. Bis dahin zeigt eure
Oberfläche ein Abzeichen, dessen Grundlage wir selbst für widerlegt halten.

---

## 2 · Innenansichten: fertig bei uns, unbestellbar bei euch

Wir können seit dem 22.08. aus einer **IFC** die Räume lesen und je Raum zwei Standpunkte
rechnen — frontal auf eine Wand und über Eck. Kamera auf halber Raumhöhe (dann bekommen
Boden und Decke gleich viel Bild) und **waagrecht**, damit die Vertikalen parallel bleiben.

**Zwei Dinge fehlen auf eurer Seite:**

1. **Der Auslöser.** `cameras` kennt `"auto"`, eine Liste mit `position`/`target`, oder
   `"saved"`. Ein Innenraum-Standpunkt liesse sich als `position`/`target` durchreichen —
   aber kein Feld sagt *„gib mir Innenansichten der Räume"*.
2. **Die Geometrie.** Euer Schema führt `ifc` als zulässiges Format, der Auftrag vom
   19.08. schickte aber `model.glb`. **Aus einer glb gibt es keine Räume** — dort sind
   Wände und Böden Dreiecke ohne Raumbegriff.

**Was ihr tun müsstet:** entweder die IFC mitschicken (dann brauchen wir nichts weiter),
oder ein Feld für Innenansichten. Beides ausführlich als **Frage 14** im Übergabeblatt.

*Nicht von euch gebraucht:* die Entscheidung frontal gegen über Eck. Die hängt daran, ob
die Stirnwand ein Motiv trägt, und das steht in keiner IFC. Wir rechnen beide.

---

## 3 · Was ankommt, aber mit einer offenen Frage

**Die Stil-Prüfung.** Seit dem Owner-Entscheid vom 21.08. ist unser Hausstil *fest
formuliert* und wird gegen einen gemessenen **Belichtungsrahmen** geprüft, nicht gegen ein
Referenzset. Wir senden darum:

```json
"style": { "style_score": null, "threshold": null,
           "passed": true, "method": "belichtungsrahmen/hausstil" }
```

`style_score` bleibt **leer**, weil eine Belichtungsprüfung keinen natürlichen Skalar hat.
Eine Zahl zu erfinden — auch eine ehrlich gemeinte wie `1.0` für „bestanden" — sähe in
eurer Oberfläche aus wie eine gemessene Bildähnlichkeit.

**Offen: Nimmt euer Schema `null` an?** Eure Schemadatei liegt uns nicht vor. Wenn nicht,
scheitert der Auftrag erst in eurer Warteschlange — und dann ist das dort zu ändern und
nicht bei uns durch eine erfundene Zahl. Übergabeblatt **Frage 13**.

---

## 4 · Was ankommt und stillschweigend nützlich ist

* **`timings.stillstand_s`** — die längste Pause ohne Fortschritt während des Laufs. Ein
  Auftrag, der 1800 s brauchte und davon 1500 s stand, ist damit von einem
  unterscheidbar, der 1800 s gerechnet hat. `timings` ist ein Vertragsfeld, das kommt
  also schon heute bei euch an.
* **`verdict.reason`** — trägt einen Satz darüber, *wogegen* geprüft wurde, inklusive des
  Hinweises, wenn eine Schwelle nicht kalibriert ist.

---

## 5 · Was neben den Bildern liegt, weil es kein Feld gibt

* **`<kamera>_seedauswahl.json`** — welcher Startwert gewählt wurde und warum, mit allen
  Kandidaten. Hintergrund: Die Streuung über Startwerte (0.2269) ist **grösser als jeder
  gemessene Parametereffekt** (0.10–0.14). Solange das gilt, ist die Frage nicht „welche
  Stärke", sondern „welcher Lauf".
* **Die Nullproben-Anker** je Soll-Karte — was ein Bild *ohne jede Geometrie* auf dieser
  Szene erreicht. Ohne diese Zahl ist kein Score einzuordnen.

Euren Vertrag dafür zu erweitern ist **eure** Entscheidung, nicht unsere. Die Dateien
liegen bereit, falls ihr sie wollt.

---

## 6 · Der Backbone: was euer Auftrag bestellt, und was gemessen ist

Der Auftrag vom 19.08. führte `backbone: "qwen"`. Dazu zwei Messungen:

* **Qwen ist kein ControlNet** (`auf-20260818-09`). Die Tiefenkarte geht dort als
  gewöhnliches Bild ein, nicht als Führung.
* **Trotzdem fängt es etwas damit an** (`auf-20260822-28`): ρ −0.7406 gegen −0.9059 bei
  z-image-turbo mit echter Führung. Der Abstand von 0.165 entspricht aber etwa **einer
  Standardabweichung der Seed-Streuung** — an drei Bildern ist damit **nicht entschieden**,
  welcher Backbone besser ist. Wir behaupten es darum auch nicht.

**Was sicher ist:** Die Führung kommt bei z-image-turbo an (mit gegen ohne: Abstand
0.650). Und der eigentliche Übeltäter war keiner von beiden, sondern eine **geklippte
Tiefenkarte** — eine Karte mit zwei Graustufen statt 235 war für das ControlNet exakt so
viel wert wie gar keine Konditionierung. Behoben seit dem 20.08.

`z-image-turbo` steht seit dem 22.08. in unserer Backbone-Tabelle, euer Vertrag führt es
auch. Ihr könnt es also bestellen.

---

## Wo die Belege stehen

Jede Zahl auf diesem Blatt ist gemessen und nicht geschätzt. Die Berichte liegen im
selben Repo:

| | |
|---|---|
| `docs/EMPFINDLICHKEIT_2026-08-20.md` | warum der alte Score nicht monoton ist |
| `docs/MASKE_2026-08-21.md` | warum die Bauwerksmaske trägt, wo das ganze Bild versagt |
| `docs/GEOM_IOU_HALLUZINATION_2026-08-21.md` | wie ein leeres Grundstück das Tor besteht |
| `docs/SEEDAUSWAHL_2026-08-22.md` | Streuung über Startwerte gegen Parametereffekt |
| `auftraege/ergebnisse/` | die Rohzahlen jeder einzelnen Messung |

---

## Was wir NICHT von euch verlangen

Nichts davon ist dringend im Sinne von „sonst geht es nicht weiter". Der Aussenweg
funktioniert, Bilder kommen an, die Kette ist seit dem 19.08. geschlossen. Was hier steht,
ist die Liste der Stellen, an denen **wir mehr wissen, als wir euch sagen können** — und
die wollten wir nicht stillschweigend liegen lassen.

Die ausführlichen Fragen mit Begründung stehen in `docs/UEBERGABE_VIS_2026-08-19.md`
(inzwischen 14 Stück). Dieses Blatt ist die Kurzfassung für den Einbau.
