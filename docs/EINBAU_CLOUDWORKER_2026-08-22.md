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

## Was wir NICHT von euch verlangen

Nichts davon ist dringend im Sinne von „sonst geht es nicht weiter". Der Aussenweg
funktioniert, Bilder kommen an, die Kette ist seit dem 19.08. geschlossen. Was hier steht,
ist die Liste der Stellen, an denen **wir mehr wissen, als wir euch sagen können** — und
die wollten wir nicht stillschweigend liegen lassen.

Die ausführlichen Fragen mit Begründung stehen in `docs/UEBERGABE_VIS_2026-08-19.md`
(inzwischen 14 Stück). Dieses Blatt ist die Kurzfassung für den Einbau.
