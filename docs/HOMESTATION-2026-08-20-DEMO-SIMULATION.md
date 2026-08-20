# Demo-Simulation, zweiter Durchgang — 20.08.2026

**Gefahren wie ein Nutzer, mit echten Mausereignissen, auf `v0.9.41`.** Vergleich zum
ersten Durchgang vom 19.08. Während des Laufs wurde **nichts repariert**.

---

## Die Antwort in drei Sätzen

**Die Kette läuft zum ersten Mal von der Oberfläche bis zum fertigen Bild durch.** Knopf
gedrückt → Auftrag angelegt → vom Dienst abgeholt → Blender-Multipass mit drei Nullproben
→ Bildmodell → Ergebnis zurück in die Brücke: **72 Sekunden**, ein Bild von 1600 × 992.

**Sie bleibt an der letzten Handbreit stehen.** Die Oberfläche fragt alle 2,5 Sekunden
nach, bekommt `status: "done"` samt vollständigem Ergebnisblock — und zeigt nach
**237 Abfragen und 8½ Minuten** immer noch «RENDERT · rendert im GPU-Leerlauf …».

**Das Urteil widerspricht sich selbst.** Drei Nullproben liegen gerendert im
Ausgabeordner, und das Urteil sagt «Geometrie-Schwelle NICHT kalibriert (keine
Nullprobe)». Die Geometriezahl kam gar nicht zustande: `spearman: null`, `geom_iou: 0.0`.

---

## 1 · Die acht Schritte, 19.08. gegen 20.08.

| # | Vision | 19.08. | 20.08. | Was sich geändert hat |
|---|---|---|---|---|
| 1 | Modell laden | GEHT | **GEHT** | «Demohaus Kubus» aktiv, 3 Bauteile, 3D+Plan nebeneinander |
| 2 | Übersetzen | TEIL | **TEIL** | unverändert geprüft |
| 3 | KosmoVis öffnen | GEHT | **GEHT** | Kanon-Hierarchie jetzt oben: KosmoData · KosmoDesign · KosmoSpez · KosmoOffice |
| 4 | Preset (Kameras, Stimmung) | TEIL | **TEIL** | Auto-Kamera-Knoten schlägt «Eingang» und «Übersicht» vor |
| 5 | Node-Oberfläche | GEHT | **GEHT+** | öffnet **vorverdrahtet**: Modell → Auto-Kamera → Prompt → Render |
| 6 | Knoten | GEHT | **GEHT** | Render-Knoten mit Formular (Fassade, Szene, Jahreszeit, Personen, Freitext) |
| 7 | Output (n Bilder) | TEIL | **TEIL+** | **Ein Bild entsteht wirklich** — kommt aber nicht in der Oberfläche an |
| 8 | An den Publisher | TEIL | TEIL | nicht erreicht, weil 7 hängt |

---

## 2 · Was neu durchläuft — und das ist der Fortschritt des Tages

Am 19.08. blieb es an zwei Stellen stehen. **Beide sind weg:**

**«Ausführen» erreicht den Knopf.** Am 19.08. lag der Vergrössern-Knopf über der linken
oberen Ecke; mein Klick kam nie an. Diesmal vor dem Klick nachgemessen:

    Knopf 84 × 32 bei 590,554 · disabled: false · elementFromPoint trifft: true

**Der Auftrag wird abgeholt.** Am 19.08. blieb er auf «wartet auf GPU-Leerlauf» liegen —
es lief schlicht kein Abholer. Seit heute ist er ein Dienst mit 30-Sekunden-Takt:

    15s  queued
    30s  running
    75s  done      1 Bild geschrieben

Und die Oberfläche sagt inzwischen die **Wahrheit über das Warten**: statt des falschen
«wartet auf GPU-Leerlauf» steht dort «wartet — nicht abgeholt (Grund unbekannt). Läuft
auf der HomeStation ein Render-Abholer?»

**Was gerendert wurde:** Kamera `sSE` (eine der zwölf Himmelsrichtungen aus `kameras.py` —
das Kameramodul, das der Demoplan als Stufe 1 forderte, **existiert inzwischen**),
1600 × 992 aus angeforderten 1600 × 1000 (16er-Raster, gemeldet), 3 Meshes, Hüllbox
6,36 × 6,18 × 3,0 m, 40,7 s reine Renderzeit.

---

## 3 · Wo es stehen bleibt, auf die Naht genau

Nicht geraten, sondern durchgemessen:

| Prüfung | Ergebnis |
|---|---|
| Fragt die Oberfläche nach? | **Ja** — 237 Abfragen an `:8600/jobs/<id>`, alle 2,5 s, bis zuletzt |
| Antwortet die Brücke? | **Ja** — HTTP 200 mit `status: "done"` und vollem `result` |
| Ist es CORS? | **Nein** — `access-control-allow-origin` ist gesetzt, Vorflug beantwortet |
| Ist es der Zwischenspeicher? | **Nein** — dieselbe Anfrage aus der Seite heraus, mit und ohne `cache: no-store`, liefert beide Male `done` |

**Also: die Oberfläche bekommt das `done` und handelt nicht darauf.** Das ist der einzige
fehlende Griff zwischen «Knopf drücken» und «Bild ansehen».

Ein Detail für die Fehlersuche: die Brücke sendet **keine einzige Cache-Kopfzeile**
(kein `Cache-Control`, kein `ETag`). Das war hier nicht die Ursache, ist aber eine
Zeitbombe für jede Umgebung mit einem Zwischenspeicher davor.

---

## 4 · Der zweite Befund: das Urteil widerspricht dem Ausgabeordner

    out/sSE/nullprobe_grau.png
    out/sSE/nullprobe_rauschen.png
    out/sSE/nullprobe_verlauf.png

    "verdict": { "passed": false,
                 "reason": "Geometrie None gegen 0.65; Geometrie-Schwelle NICHT
                            kalibriert (keine Nullprobe, siehe hinweise)" }
    "geometry": { "spearman": null, "geom_iou": 0.0, "passed": false }

Die Anker sind **gerendert**, das Urteil hält sie für **abwesend**, und die Geometriezahl
ist gar nicht erst zustande gekommen (`spearman: null`, `geom_iou: 0.0` — nicht «schlecht»,
sondern **nicht gerechnet**). Das liegt in unserer Lane und ist noch nicht angefasst; der
Lauf war zum Messen da, nicht zum Reparieren.

---

## 5 · Das Bild, ehrlich angesehen

Ein Sichtbeton-Quader auf gepflastertem Grund unter **blauem** Himmel — der Prompt
verlangte «bedeckter Himmel». Der Prompt kommt also entweder nicht an oder wird
überstimmt; **ungemessen**, welches von beidem.

**Eine Korrektur an meinem ersten Eindruck:** Ich hielt den geschlossenen Quader für eine
Erfindung des Bildmodells, weil das Demohaus ein offenes U aus drei Wänden ist. Der
Blender-Pass zeigt aus derselben Richtung **selbst einen geschlossenen Körper** — von
Südost verdecken die zwei Aussenflächen das Innere, und die Wandoberkanten lesen sich als
Deckel. Das Bildmodell erfindet hier kein Dach, es setzt fort, was die Kamera sah.

Erfunden ist der **Kontext**: Pflaster, niedrige Mauern, Bäume am Horizont. Bei einem
Modell ohne Gelände ist das erwartbar und nicht dasselbe wie eine erfundene Geometrie.

---

## 6 · Was ungemessen blieb

* **Warum der Prompt nicht durchkommt** (blauer statt bedeckter Himmel) — nicht verfolgt.
* **Die zwei Kamera-Standpunkte der Oberfläche** («Eingang», «Übersicht») erreichen den
  Render nicht: gesendet wird `cameras: "auto"`, und `auto` heisst bei uns bewusst
  **eine** Richtung (`AUTO_RICHTUNGEN = ("sSE",)`, «zwölf Standpunkte sind zwölf
  GPU-Läufe»). Vertragsgemäss, aber die Oberfläche verspricht mehr, als sie bestellt.
* **Schritt 8** (Übergabe an den Publisher) — nicht erreicht.
* **Ob die Oberfläche bei einem zweiten Auftrag anders reagiert** — nur ein Lauf.
* **Der `hinweise`-Block**, auf den das Urteil verweist, steht im Ergebnisvertrag weiterhin
  nicht — derselbe offene Punkt wie am 19.08.

---

## 7 · Was der Cloud-Worker daraus braucht

**Ein Griff, und die Demo läuft durch:** Der Render-Knoten muss auf `status: "done"`
reagieren und `result.images[0]` anzeigen. Alles davor ist gemessen in Ordnung — die
Brücke antwortet, CORS steht, kein Zwischenspeicher dazwischen.

Dazu zwei kleinere: `Cache-Control: no-store` auf die Auftragsabfrage, und der
Auto-Kamera-Knoten sollte entweder die Standpunkte wirklich bestellen oder nicht zwei
Namen anzeigen, wenn er `auto` sendet.
