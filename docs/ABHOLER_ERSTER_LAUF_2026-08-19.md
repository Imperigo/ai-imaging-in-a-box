# Der erste Auftrag, der wirklich durchlief — und das Minuszeichen, das ihn elf Stunden aufhielt

**HomeStation, 19.08.2026, Abend**

---

## Was passiert ist

In `/tmp/kosmo-jobs/` lagen zwei vollständige Aufträge der fremden Brücke, einer seit
09:04, beide auf `queued`. Die Oberfläche meldete *«wartet auf GPU-Leerlauf»* — bei 0 %
Last und 15,5 W. Sie wartete nicht auf die Karte. Sie wartete auf jemanden, der abholt.

:mod:`aiimaging.abholer` konnte das bereits vollständig. **Nur rief es niemand.**

Dieser Abend hat drei Dinge getan: den Betriebs-Einstieg gebaut, den Fehler gefunden, der
dann zutage trat, und den ersten Auftrag bis `done` gebracht.

---

## 1 · `tools/abholen.py` — der fehlende Aufruf

Bewusst dünn. Er trifft **keine** Entscheidung, die der Abholer schon trifft, sondern nur
die zwei, die eine Bibliothek nicht treffen darf:

**Gilt die fremde Freigabe?** Die Brücke prägt ihren `approval_token` selbst. Ob er gilt,
entscheidet der Betreiber — darum `--fremde-freigabe` als ausdrückliches Flag,
voreingestellt **aus**. Ohne es bleibt der Auftrag liegen, und der Bericht sagt warum.

**Ist die Karte frei?** Die Auskunft kommt aus `nvidia-smi`. Fehlt es, schweigt es oder
liefert Unlesbares, lautet die Antwort **nein** — nicht «vermutlich schon». Zusätzlich
gilt die Karte als belegt, wenn mehr als 4 GiB gehalten werden: Der Desktop allein braucht
rund 1 GiB, ein geladenes Sprachmodell mehr als 15.

---

## 2 · Der Fehler: ein Minuszeichen

Der erste Lauf brach ab:

    SeamError: Blender endete mit Code 2
    usage: blender [-h] --glb GLB --out OUT …

Kamera 0 «Eingang» lief. Kamera 1 «Übersicht» lief. **Kamera 2 «Innenraum» nicht.**
Ihr Standort: `auge = [-6.854, 1.6, 6.854]`.

Die vollständige Meldung, freigelegt durch einen Einzelaufruf:

    blender: error: argument --auge: expected one argument

`argparse` liest jedes Wort mit führendem Minus als Option. `--auge` stand damit ohne Wert
da. Die Gleichheitszeichen-Form `--auge=-6.854,…` ist der Weg daran vorbei: Was hinter dem
`=` steht, wird nie mehr als Option gelesen.

**Warum es so lange gutging, und das ist die eigentliche Lehre:** Jede bis dahin gemessene
Kamera stand **vor** dem Bauwerk, also im positiven Bereich. Eine Innenraumkamera steht im
Gebäude — und dort ist fast immer mindestens eine Koordinate negativ. Der Fehler war nicht
selten. Er war **unerreichbar, solange niemand nach innen schaute**. Dieselbe Sorte wie
die randberührende Bodenfläche in `auf-15`: Eine Regel gilt so weit, wie gemessen wurde.

**Behoben** in `seams._multipass_argumente` für alle Zahlenwerte, nicht nur `--auge`:
`--blick-auf`, `--brennweite`, `--gelaende-z` und `--kamera-huellbox` tragen dasselbe
Minus. Zwei Regressionstests dazu; drei bestehende Tests prüften die alte Zwei-Wort-Form
und sind auf die neue gehoben — der geprüfte **Inhalt** ist derselbe geblieben.
Suite: **2484 grün.**

---

## 3 · Der erste Auftrag bis `done`

Frischer Auftrag über die Oberfläche ausgelöst, dann abgeholt:

    gesehen 1 · verarbeitet 1 · fehler 0 · liegengelassen 0
    vis-…-27f51f: 3 Bild(er) geschrieben
    status: done

`render-result.json` nach `kosmovis.render-result/v2`, drei Bilder (Eingang, Übersicht,
Innenraum), Zeiten je Kamera 92.6 / 92.0 / 107.7 s, gesamt 292.2 s.

**Damit ist die Kette zum ersten Mal geschlossen:** Oberfläche → Graph → Auftrag → Brücke
→ Abholer → Blender-Multipass → Bildmodell → Geometrie-QA → Ergebnis → `done`.

---

## 4 · Und das Bild ist schlecht — aus einem Grund, den wir schon gemessen haben

Die Geometrie-QA meldet:

    geometry_fidelity: null · passed: false · reason: "Geometrie None gegen 0.65"

**Ungemessen, nicht bestanden.** Kein erfundenes grünes Abzeichen. Das Bild zeigt
schwebende Drahtgitter und einen Stapel schwarzer Platten vor bewölktem Himmel; ein
Gebäude ist nicht zu erkennen.

Der Grund steht im Auftragsvertrag: `"vis": {"backbone": "qwen", …}`. Der Vertrag
`packages/kosmo-contracts/src/render-scene.ts` führt `qwen` als Vorgabe — und
`auf-20260818-09` hat am Gerät belegt, dass `qwen-image-edit-2511` über
`QwenImageEditPlusPipeline` **kein ControlNet ist**: kein `control_image`, kein
`controlnet_conditioning_scale`, kein `strength`. Die Tiefenkarte wird dort als `image`
übergeben und **bearbeitet** statt zu konditionieren.

Das ist genau der Befund, den ich heute Abend an den Cloud-Worker gemeldet habe
(`HOMESTATION-2026-08-19-PUBLISH-UND-KOSMO.md`, Befund 12). **Er ist jetzt nicht mehr
Papier, sondern ein Bild.** Sobald `z-image-turbo` in der Aufzählung des Vertrags steht,
ist derselbe Lauf eine echte Probe — die Naht dieses Backbones trägt, `auf-20260820-22`
hat es gemessen.

---

*Ein Fehler gefunden, behoben, mit Test gesichert; ein Betriebs-Einstieg gebaut; ein
Auftrag bis `done` gebracht. Die zwei alten Aufträge stehen auf `error` mit
festgehaltener Begründung — so, wie der Abholer es vorsieht: Ein Fehler ist ein Ergebnis.*
