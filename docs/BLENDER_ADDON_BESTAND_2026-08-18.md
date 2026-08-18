# Bestandsaufnahme: der ältere Blender-Add-on-Code

**Datum:** 2026-08-18 · **Anlass:** Der Owner erinnert sich an viel älteren Code, der als
Blender-Add-on geschrieben wurde und automatische Kameraplatzierung enthält.
**Auftrag:** Finden, verstehen, einstufen. **Nicht** kopieren.

> **Diese Datei beschreibt fremden Code, sie enthält ihn nicht.** Es wurde keine Zeile aus
> den untersuchten Repos in dieses Repo übernommen. Verfahren sind in Prosa und Formeln
> wiedergegeben, damit ein Nachbau möglich ist, ohne dass eine Herkunftsfrage entsteht.
>
> **Regel 3 wurde beim Schreiben angewandt:** Die untersuchten Repos sind privat und
> enthalten reale Projekt-, Orts- und Personennamen sowie persönliche Dateipfade. Nichts
> davon steht hier. Wo ein realer Bezug für das Verständnis nötig wäre, steht eine
> Umschreibung („ein reales Wettbewerbsprojekt", „ein hartcodierter persönlicher
> Cloud-Pfad").

---

## 0 · Kurzfassung für Eilige

Ja, der Code existiert, und er ist erheblich umfangreicher als vermutet. Das ursprüngliche
KosmoVis-Add-on umfasst **83 Python-Module mit rund 37 000 Zeilen** und einen vollständigen
**eigenen Blender-Node-Tree** mit 17 aktiven Knoten.

Die **automatische Kameraplatzierung existiert und ist das Beste, was gefunden wurde.** Sie
löst die schwierige Frage — passt das Gebäude ins Bild? — auf drei Wegen: analytisch aus dem
Bildwinkel, iterativ über einen Frustum-Test aller acht Hüllbox-Ecken, und mit einem
Raycast-Test gegen Verdeckung durch Nachbargebäude. Der grösste Teil davon ist **reine
Rechnung** und damit bpy-frei nachbaubar.

Eine Einschränkung vorweg, die den Fund erst brauchbar macht: **Der Code lag nicht dort, wo
gesucht werden sollte.**

---

## 1 · Was durchsucht wurde — und was nicht

### 1.1 Durchsucht

Die sieben bereits geklonten Ökosystem-Repos im Scratchpad:
`KosmoPrepare`, `KosmoVis`, `KosmoPublish`, `KosmoDesign`, `ArchitekturKosmos-Codex`,
`architekturkosmos-control-hub`, `Architektur-Cosmos`.

Suchmuster: `bl_info`, `register(`, `bpy.ops.object.camera_add`, `bpy.data.cameras`,
`track_to` / `TRACK_TO`, `lens`, `sensor_width`, `sensor_fit`, `ortho_scale`, `look_at`,
`augenhoehe` / `augenhöhe` / `eye_height` / `eye_level`, `1.7`, `camera_presets`,
`camera_to_view_selected`, `fit_camera`, `frame_all`, `atan` / `fov` / `angle_x`,
`NodeTree` / `NodeSocket` / `bl_idname`, `links.new`, `GPL` / `AGPL`.

### 1.2 Der Fund, der den Auftrag gerettet hat

Der Klon von `KosmoVis` im Scratchpad war **unvollständig ausgecheckt**. Der Arbeitsbaum
enthielt fünf Dateien; `git ls-tree -r HEAD` meldete 314, davon 124 Python-Dateien. Ursache:
ein partieller Klon (`partialclonefilter = blob:none`), bei dem sämtliche Dateien im Index
als gelöscht standen. `git reset --hard HEAD` hat den Baum wiederhergestellt — die Blobs
waren über den Promisor nachladbar.

**Ohne diesen Schritt wäre der Bericht auf „es gibt kaum etwas" hinausgelaufen.** Der
gesuchte Add-on-Code liegt vollständig in `KosmoVis/01_workflow/`. Wer dieselbe Suche
wiederholt, sollte zuerst prüfen, ob der Arbeitsbaum vollständig ist:

```
git -C <repo> ls-tree -r HEAD --name-only | wc -l    # gegen
find <repo> -not -path "*/.git/*" -type f | wc -l    # abgleichen
```

Die Spur dorthin kam aus `KosmoVis/01_workflow/_pilot/run_kosmovis_stage.py`: Dieses Skript
importiert Module namens `archviz_pipeline_v6_camera_math`, `archviz_custom_cameras`,
`archviz_multipass_render`, die im Arbeitsbaum nicht existierten. Ein Skript, das auf
Module zeigt, die es nicht gibt, ist ein Hinweis auf einen unvollständigen Klon — nicht auf
verlorenen Code.

### 1.3 Nicht durchsucht

- **`KosmoDraw-Privat`** — auftragsgemäss nicht angefasst („Privat" im Namen, Regel 3).
- **`KosmoOrbit`** — im Repo-Verzeichnis der Sitzung vorhanden, aber nicht ausgewertet. Die
  Oberfläche gehört ohnehin KosmoOrbit; für den Kamerabestand war es nicht nötig. **Offen.**
- **`KosmoDraw`, `kosmo-backend`** — nicht geklont, kein Anhaltspunkt für Kameracode.
- **`legacy_archive/`** — im Autoloader referenziert (`archviz_pipeline_v2` bis `_v5_smart`,
  dazu ein archiviertes Verzeichnis vom 21.05.2026). Diese Dateien sind **nicht** im Repo.
  Es sind die Vorgängerfassungen der hier beschriebenen Verfahren; sie zu suchen lohnt nur,
  wenn eine Entwurfsgeschichte gebraucht wird.
- **Die `.blend`-Dateien selbst.** Der Node-Tree wird in `.blend`-Dateien gespeichert; die
  liegen nicht im Repo. Was hier über den Tree steht, stammt aus dem Code, der ihn *aufbaut*,
  nicht aus einem Tree-Abzug.

---

# TEIL A · Kameras

Das ist der wichtigste Teil und der einzige, der vollständig ausgewertet wurde.

## A.1 · `KosmoVis/01_workflow/archviz_pipeline_v6_camera_math.py` — die Hauptfundstelle

283 Zeilen. Der Kopfkommentar nennt sie „Raycast + Frustum + 2/3-Komposition". Sie enthält
vier Funktionen und beantwortet als einzige Fundstelle alle vier Fragen des Auftrags.

### Wie der Abstand bestimmt wird

Analytisch aus dem Bildwinkel, nicht als fester Faktor. Der Kern:

1. Aus Brennweite und Sensormass wird der Öffnungswinkel gebildet — horizontal aus 36 mm,
   vertikal aus 27 mm Sensorhöhe, jeweils `2·atan(sensor / (2·lens))`. Vorgabe 28 mm.
2. Als horizontale Ausdehnung wird der **grösste** der drei Werte genommen: Breite, Tiefe,
   und die **Grundriss-Diagonale** `√(x² + y²)`. Die Diagonale ist der schlimmste Fall, der
   bei einer Diagonalansicht sichtbar wird — das ist der Grund, warum die Rechnung auch für
   Eckansichten trägt.
3. Zwei Kandidatenabstände werden gebildet:
   `dist_h = (h_extent/2) / tan(hfov/2) / coverage` und
   `dist_v = (size.z/2) / tan(vfov/2) / coverage`. Der grössere gewinnt.
4. `coverage` (Vorgabe 0.55) ist der **Anteil des Bildes, den das Gebäude füllen soll**.
   Ein Wert unter 1 schiebt die Kamera weiter weg und lässt Luft — das ist die
   „2/3-Komposition" aus dem Modulnamen, als Zahl ausgedrückt.
5. Zum Schluss eine Untergrenze: mindestens die halbe kleinere Grundrissseite plus 10 m
   Wandabstand. Dann noch mal `distance_factor` (Vorgabe 1.0) als Regler von Hand.

Das ist **deutlich sauberer als alles andere im Ökosystem** und der eigentliche Fund.

### Wie die Höhe bestimmt wird

`eye_z = 1.7` als Vorgabewert, **absolut** — nicht relativ zum Gebäudefuss. Das Blickziel
liegt nicht auf Augenhöhe, sondern angehoben: `target.z = eye_z + size.z · 0.2`, also ein
Fünftel der Gebäudehöhe über der Augenhöhe. Damit kippt die Kamera leicht nach oben und das
Gebäude sitzt tiefer im Bild — der übliche Architekturfotografie-Griff.

Beim iterativen Nachschieben bleibt die Augenhöhe **konstant** (`cur.z = eye_z` nach jedem
Schritt). Die Kamera weicht nur horizontal aus, nie nach oben. Das ist eine bewusste
Entscheidung und der Grund, warum das Verfahren Augenhöhen-Perspektiven liefert statt
Drohnenbildern.

### Wie die Richtungen bestimmt werden

Zwölf Richtungen, nicht gleichmässig verteilt, sondern nach Fassaden gedacht:

- **4 frontal** — `n`, `e`, `s`, `w`, exakt senkrecht auf eine Fassade. Dazu ein kleiner
  seitlicher Versatz (`lateral = size.x · 0.10`), damit das Bild nicht symmetrisch-tot wird.
- **8 diagonal** — `nNE`, `nNW`, `sSE`, `sSW`, `eEN`, `eES`, `wWN`, `wWS`. Gelesen als:
  Primärrichtung, dann um `bias_deg` in einen Quadranten gedreht.

`bias_deg` ist der interessante Parameter. Der Code dokumentiert ihn als Regler für das
Verhältnis der beiden sichtbaren Fassaden: 30° = primäre Fassade dominant (2/3 zu 1/3),
45° = echter Eckblick (50/50), 35° = ausgewogen (60/40) und Vorgabewert. Das ist eine
**architektonische Bildregel als Zahl** — genau die Art Wissen, die man nicht neu erfindet.

Im Code steht ein kommentierter Vorzeichenfehler: für `n` und `s` waren die Drehrichtungen
invertiert und wurden korrigiert. Wer nachbaut, sollte die vier N/S-Diagonalen gegen eine
Skizze prüfen; es ist erwiesenermassen eine Stelle, an der man sich vertut.

### Wie sichergestellt wird, dass das Gebäude ins Bild passt

Das war die schwierigste Frage, und hier steht die beste Antwort des ganzen Bestands:
`ensure_bbox_in_frustum`.

Das Verfahren prüft nicht die Hüllbox als Ganzes, sondern **alle acht Ecken einzeln**:

1. Aus Brennweite und Sensormassen werden `tan(hfov/2)` und `tan(vfov/2)` gebildet und mit
   einem `frame_margin` (Vorgabe 0.92) multipliziert — 8 % Sicherheitsrand.
2. Ein Kamerakoordinatensystem wird aus der tatsächlichen Blickrichtung aufgebaut
   (vorwärts, rechts, oben — über Kreuzprodukte, Welt-Z als Referenz-Oben).
3. Für jede Ecke: Tiefe = Skalarprodukt mit „vorwärts". Ecken mit Tiefe unter 0.5 gelten als
   hinter der Kamera und sind sofort ein Fehlschlag. Sonst werden die seitlichen Anteile
   durch die Tiefe geteilt — das ist die perspektivische Division — und gegen die
   Tangenswerte verglichen.
4. Das grösste Überstehen über alle Ecken (`max_overflow`) steuert, **wie weit** die Kamera
   zurückgeschoben wird: `push = (max_overflow − 1) · aktueller_abstand · 0.6 + 3.0`. Der
   Schub folgt nur der horizontalen Richtung; die Augenhöhe bleibt.
5. Höchstens 20 Durchläufe. Danach wird gewarnt und die letzte Position zurückgegeben —
   das Verfahren **verweigert nicht, es liefert eine erklärt-unvollkommene Antwort**.

Das ist die richtige Bauart: analytisch grob (`compute_camera_for_2_3`), dann iterativ genau
(`ensure_bbox_in_frustum`). Die analytische Rechnung allein reicht nicht, weil sie mit einer
Ersatzausdehnung arbeitet; der Eckentest prüft die Wirklichkeit.

### Und der Teil, der wirklich Blender braucht: Verdeckung

`cast_clear_path` und `pull_camera_until_clear` behandeln ein Problem, an das reine Geometrie
nicht herankommt: **stehen Nachbargebäude im Weg?**

Ein Strahl wird von der Kamera zum Ziel geschossen. Treffer auf Objekte des Gebäudes selbst
sowie auf Hilfs- und Geländeobjekte werden übersprungen — der Strahl wird ab dem Trefferpunkt
plus 5 cm neu gestartet, bis zu 20 Mal. Trifft er etwas Fremdes, gilt die Sicht als verstellt.

Dann wird die Kamera **näher herangezogen** (nicht weiter weg), in Schritten von 12 % der
Restdistanz, höchstens acht Mal. Abbruch, wenn die Sicht frei ist, wenn der Abstand unter 6 m
fällt, oder wenn der nächste Schritt in die um einen Sicherheitsabstand von 3 m erweiterte
Hüllbox eintreten würde. Die Augenhöhe bleibt auch hier konstant.

Bemerkenswert: Die beiden Verfahren ziehen **gegeneinander** — der Frustum-Test schiebt weg,
der Verdeckungstest zieht heran. Im Code laufen sie nacheinander, nicht in einer gemeinsamen
Schleife. Ob das in der Praxis stabil ist, geht aus dem Code nicht hervor.

### Einstufung

| Funktion | Einstufung | Begründung |
|---|---|---|
| `compute_camera_for_2_3` | **reine Rechnung** | Nur Winkelfunktionen und Vektorarithmetik. Nutzt `mathutils.Vector`, das ist aber reine Bequemlichkeit — mit einem eigenen Vektortyp oder numpy identisch nachbaubar. |
| `ensure_bbox_in_frustum` | **reine Rechnung** | Ebenso. Kreuzprodukte und Skalarprodukte, keine Szene. Die `print`-Aufrufe müssten in eine Protokollierung wandern. |
| `cast_clear_path` | **braucht bpy** | `bpy.context.scene.ray_cast` gegen den Depsgraph. Gehört in den Runner. |
| `pull_camera_until_clear` | **braucht bpy** | Nur wegen `cast_clear_path`. Die Schrittlogik selbst ist rein — die Verdeckungsprüfung liesse sich als übergebene Funktion herausziehen, dann wäre auch dieser Teil testbar. |
| Modulkopf | **Hindernis** | `import bpy` steht auf Modulebene, obwohl zwei der vier Funktionen es nicht brauchen. Beim Nachbau trennen. |

**Kein `bl_info`, kein `register()`.** Das Modul ist ausdrücklich als Helfer angelegt — die
letzte Zeile sagt es wörtlich. Das ist die am wenigsten add-on-verseuchte Fundstelle im
ganzen Bestand.

### Reifegrad

**Erprobt im Betrieb, aber ohne Testnetz.** Es gibt keine Unit-Tests für dieses Modul.
Belege dafür, dass es gelaufen ist:

- `run_kosmovis_stage.py` ruft die zwölf Richtungen über `_human_direction_apply` auf und ist
  als Pilot-Stufe eines Orchestrators eingebunden.
- Der Stress-Test-Bericht vom 23.05.2026 führt den zugehörigen Knoten (`CameraCombined`) als
  eine von 17 Knoten mit Status „✓".
- Die kommentierten Fehlerkorrekturen (Vorzeichen der N/S-Diagonalen) sind Belege dafür, dass
  jemand die Ergebnisse angeschaut und für falsch befunden hat. Das ist ein stärkerer
  Beleg als ein Test.

Gegenbeleg: `run_kosmovis_stage.py` erklärt selbst, dass das tatsächliche Render-Ergebnis
**nicht** ohne echten Blender-Lauf verifiziert wurde.

---

## A.2 · `KosmoVis/01_workflow/archviz_camera.py` — der analytische Vorläufer

345 Zeilen, mit `bl_info` — ein eigenständiges Add-on. Kopfkommentar: „Positioniert eine
Kamera auf Augenhöhe so, dass das komplette Gebäude im Frame zu sehen ist."

Interessant ist `fit_camera_to_bbox`, weil es dasselbe Problem **ohne Iteration** löst:

- Zwei Abstände werden gebildet — einer, damit die Breite passt (`half_w / tan(hfov/2)`), einer
  für die Höhe. Der grössere gewinnt, mal `padding` (1.15), plus die halbe Gebäudetiefe.
- Der vertikale Bildwinkel wird **aus dem Seitenverhältnis abgeleitet**:
  `2·atan((sensor_w / aspect) / (2·lens))`. Das ist der Punkt, an dem die Bildproportion in
  die Rechnung eingeht — in `camera_math` steckt sie fest in der 27-mm-Sensorhöhe.
- Der vertikale Bedarf wird **von der Augenhöhe aus** gemessen, nach oben und nach unten
  getrennt (`extra_up = maxs.z − (mins.z + eye_height)`, `extra_down = eye_height`), und der
  grössere der beiden zählt. Das ist sauberer als eine halbe Gebäudehöhe, weil die Kamera auf
  1,7 m eben **nicht** in der Mitte der Fassade sitzt.
- Die Ausrichtung entsteht über `to_track_quat('-Z', 'Y')` — die Standardumrechnung von einer
  Blickrichtung in eine Blender-Rotation.

`EYE_HEIGHT = 1.7`, `DEFAULT_LENS = 35`, Seitenverhältnis 4:3, 2048 px Breite.

**Einstufung:** Die Abstandsrechnung ist **reine Rechnung**. Das Setzen von
`cam_obj.location` und `rotation_euler` und `to_track_quat` **braucht bpy**. Der Rest der
Datei — `bl_info`, zwei Operatoren mit `bpy.props`-Feldern, N-Panel-Verortung — ist
**Add-on/UI und nicht übernehmbar**.

**Reifegrad:** Vorgänger. Vom V6-Verfahren überholt (kein Verdeckungstest, keine Diagonalen,
keine Eckenprüfung), aber die Aspekt-Ableitung und die asymmetrische Höhenrechnung sind
**besser** als in V6. Beim Nachbau beide Fundstellen zusammenlegen.

---

## A.3 · `KosmoPublish/nodes/axonometry.py` — das sauberste Vorbild im ganzen Bestand

241 Zeilen. Orthografische Kamera für Axonometrien. Hier ist der Fund nicht in erster Linie
das Verfahren, sondern **die Bauart**: Die Datei ist mit zwei Überschriften geteilt,
`# ---------- Pure Math ----------` und `# ---------- Blender-Wrapper ----------`.

- `compute_axonometry_camera(obb_min, obb_max, params) -> AxoCameraConfig` — rechnet, importiert
  nichts von Blender, gibt ein `NamedTuple` zurück.
- `setup_axonometry_camera(scene, ...)` — importiert `bpy` **innerhalb der Funktion**, ruft die
  reine Rechnung und setzt das Ergebnis.

**Das ist genau die Trennung, die unser Auftrag verlangt, bereits im Ökosystem vorgelebt.**
Wer bei uns die Kameraschicht baut, sollte diese Datei als Formvorbild nehmen, unabhängig
vom Inhalt.

### Das Verfahren

Die Kamera sitzt auf einer Kugel um den Hüllbox-Mittelpunkt, Abstand = Raumdiagonale mal
`distance_factor` (3.0). Bei einer orthografischen Kamera ist der Abstand für das Bild
belanglos — er steuert nur das Abschneiden vorn und hinten (`clip_start = dist − diagonale`,
`clip_end = dist + diagonale`).

Was das Bild bestimmt, ist `ortho_scale`, und **hier steckt die eigentliche Einsicht**. Die
sichtbare Ausdehnung wird auf die Bildebene projiziert:

- horizontal: `|breite·cos(az)| + |tiefe·sin(az)|` — vom Kippwinkel unabhängig.
- vertikal: der Grundrissanteil `(|breite·sin(az)| + |tiefe·cos(az)|)` **mal `sin(elev)`**,
  plus die Gebäudehöhe **mal `cos(elev)`**.

Die Verkürzung ist an den Randwinkeln eindeutig: Senkrecht von oben (90°) trägt die Höhe
nichts zum Bild bei, weil sie auf der Blickachse liegt. Am Horizont (0°) steht der Grundriss
kantig und trägt vertikal nichts bei. Der grössere der beiden Werte mal `(1 + padding)`
(0.20) ergibt den Rahmen.

Vorgabewerte: 60° Kippung, 45° Drehung — im Kommentar als Schweizer Wettbewerbsstandard
bezeichnet, neben isometrisch (54.736°) und dimetrisch.

**Einstufung:** `compute_axonometry_camera` ist **reine Rechnung**, ohne Vorbehalt — es
importiert nur `math`. `setup_axonometry_camera` und `render_axonometry` **brauchen bpy**.
Kein `bl_info`, kein `register()` in dieser Datei.

**Reifegrad: erprobt, mit dem besten Beleg im ganzen Bestand.**
`KosmoPublish/tests/test_axonometry.py` ist ein Regressionsnetz, das die Verkürzungsphysik an
den Randwinkeln festnagelt. Sein Kopfkommentar dokumentiert einen **echten, gefundenen und
behobenen Fehler**: `sin(elev)` und `cos(elev)` waren vertauscht, wodurch ein senkrecht von
oben betrachteter Turm auf seine unsichtbare Höhe statt auf seinen Grundriss gerahmt wurde —
und ein gewöhnliches viergeschossiges Gebäude im 60°-Standardwinkel vertikal knapp
beschnitten wurde.

**Das ist der Beleg, den der Auftrag verlangt hat.** Ein Verfahren, das einen Fehler hatte,
bei dem der Fehler bemerkt wurde, weil ein Ergebnis falsch aussah, und für den anschliessend
ein Netz gespannt wurde. Es ist auch die Warnung: Diese Art Vorzeichenfehler ist genau die,
die man beim Nachbau wieder macht.

### Geschwisterdateien mit gleicher Bauart

`KosmoPublish/nodes/elevation.py`, `section.py`, `floor_plan.py` folgen demselben Muster
(`# ---------- Pure Math ----------`, `NamedTuple`-Rückgabe, `compute_*`-Funktion).

- **`elevation.py`** — vier Himmelsrichtungsansichten. Kamera ausserhalb der Hüllbox mit
  festem Versatz (20 m), Z mittig. Rotationen als feste Euler-Werte pro Richtung, sauber
  kommentiert. Enthält Doctests.
- **`section.py`** — Vertikalschnitte. Kamera **an** der Schnittebene, Vorderes über
  `clip_start` weggeschnitten, `show_in_front` (5 cm) lässt Anschlusslinien stehen. Enthält
  Doctests.
- **`floor_plan.py`** — Grundrisse über Kamera-Clipping statt boolescher Schnitte. Schnitthöhe
  1.10 m über Fertigboden. Die Begründung im Kopfkommentar (nicht zerstörend, schnell bei
  vielen Objekten, umkehrbar, parametrisch) ist ein Argument, das wir übernehmen sollten,
  falls wir je Grundrisse brauchen.

Alle drei: **reine Rechnung** in den `compute_*`-Funktionen, **braucht bpy** in den
Setup- und Render-Funktionen. Tests vorhanden (`test_elevation_and_axo.py`,
`test_section.py`, `test_floor_plan.py`).

---

## A.4 · `KosmoPrepare/nodes/kosmodraw_bridge.py` — der Kameravertrag, den niemand liest

Die Funktion `_build_camera_presets(target_bbox, eye_height_m)` erzeugt die acht
Standardkameras, die `docs/OEKOSYSTEM_2026-08-18.md` §7.4 als Vertrag führt.

### Das Verfahren — und warum es das schwächste ist

- Abstand: `radius = max(breite, tiefe) · 1.5`. **Ein fester Faktor, kein Bildwinkel.** Der
  Kommentar nennt es „2/3-Verhältnis", aber die Brennweite (35 mm, fest) geht in die Rechnung
  **nicht ein**. Ändert jemand die Brennweite, ändert sich der Bildausschnitt und der Abstand
  bleibt gleich.
- Höhe: `cz = zmin + eye_height`, also relativ zum Gebäudefuss (anders als V6, wo 1,7 m
  absolut gemeint ist). Bei den vier Diagonalen wird um feste 5 m angehoben, „für besseren
  Überblick".
- Richtungen: vier frontal (0°, 90°, 180°, 270°), vier diagonal (45°, 135°, 225°, 315°) —
  gleichmässig verteilt, ohne Bias-Regler.
- **Ob das Gebäude ins Bild passt, wird nicht geprüft.** Es gibt keinen Frustum-Test, keine
  Höhenberücksichtigung. Ein hohes, schmales Gebäude fällt oben aus dem Bild.

### Der Vertrag

Geschrieben wird `{name, location, look_at, lens_mm, type}` — deckungsgleich mit dem, was
`docs/OEKOSYSTEM_2026-08-18.md` §7.4 führt. Bestätigt.

**Aber: nichts liest ihn.** Eine Suche über alle sieben Repos nach `camera_presets`,
`AB_Preset` und `load_handoff` findet ausserhalb der schreibenden Datei nur **eine einzige
Erwähnung, und zwar in einem Tutorial-Text**. Kein Code konsumiert diese Datei. Der Vertrag
ist einseitig — er wurde geschrieben in der Erwartung, dass ein anderes Repo ihn aufgreift,
und das ist nie geschehen.

### Der zweite, unvereinbare Kameravertrag

`KosmoVis/01_workflow/archviz_custom_cameras.py` persistiert Kameras ebenfalls, aber anders:

```
{name, location, rotation_euler, lens_mm, type, ortho_scale, clip_start, clip_end, saved_at}
```

**Der Unterschied ist nicht kosmetisch.** Der eine Vertrag führt `look_at`, der andere
`rotation_euler`. Von `look_at` nach `rotation_euler` zu rechnen ist eindeutig; zurück nicht,
weil ein Blickvektor keine Zielentfernung kennt. Dazu führt der KosmoVis-Vertrag die
Ortho-Felder und die Clipping-Grenzen, die der andere nicht hat.

**Das ist die teuerste Sorte Fehler, die der Auftrag benennt: zwei Feldnamensätze für
dieselbe Sache.** Wenn wir einen Kameravertrag anbieten, muss er sich entscheiden — oder
beides führen und die Umrechnungsrichtung festschreiben.

**Einstufung `_build_camera_presets`:** **reine Rechnung** (nur `math`), aber eingebettet in
eine Datei, die `bpy` auf Modulebene importiert, `bl_info`-Nachbarn hat und über
Operator-Eigenschaften gesteuert wird. `_bbox_of_collections` in derselben Datei **braucht
bpy**.

**Reifegrad: Entwurf.** Keine Tests. Kein Konsument. Der Auftrag warnt zu Recht — eine
Funktion ist kein Beleg für ein Verfahren.

---

## A.5 · Weitere Kamerafundstellen, kürzer

**`KosmoPublish/nodes/render_specs.py`** (231 Z.) — fünf feste Renderrezepte als
Dataclasses (`CameraSpec`, `LightingSpec`, `RenderSpec`). Position und Blickziel werden aus
Gebäudemittelpunkt und -höhe über **feste Vielfache** gebildet: die Aussenperspektive steht
bei `höhe · 1.5` in X und Y auf 1.65 m; das Titelbild bei `höhe · 1.2` und `höhe · 1.8` auf
`höhe · 0.8`; die Vogelperspektive fest bei 40 m Versatz und 60 m Höhe. **Kein Bildwinkel,
keine Prüfung.** Augenhöhe hier **1.65 m**, nicht 1.70 m — ein dritter Wert im Bestand.

Wert für uns liegt nicht in der Rechnung, sondern in der **Feldstruktur**: Brennweite und
Sensorbreite getrennt, Sonnenstand als Azimut/Elevation, Auflösung, Samples,
Farbmanagement, dazu ein Freitextfeld pro Bild. Das ist eine brauchbare Vorlage für einen
Renderauftrag.

Einstufung: **reine Rechnung**, sogar bpy-frei importierbar — aber die Zahlen sind auf ein
reales Projekt zugeschnitten (Raummittelpunkte, Eingangslage), nicht allgemein.
Reifegrad: erprobt als Datenstruktur (`test_render_specs.py` prüft die Vorgabewerte), **nicht
erprobt als Platzierungsverfahren** — die Tests prüfen, dass 1.65 dort steht, wo 1.65 stehen
soll, nicht dass das Ergebnis ein brauchbares Bild ist.

**`KosmoPublish/nodes/render_executor.py`** (127 Z.) — führt eine `RenderSpec` aus. Die
Ausrichtung läuft über ein **Hilfsobjekt mit TRACK_TO-Constraint** statt über eine berechnete
Rotation. Das ist in Blender robust, erzeugt aber ein zusätzliches Objekt in der Szene.
Erwähnenswert, weil es die dritte Ausrichtungsmethode im Bestand ist (neben `to_track_quat`
und festen Euler-Werten). **Braucht bpy**, vollständig. Reifegrad: Entwurf — das Modul sagt
selbst, es laufe nur aus dem Blender-Skripteditor, und nennt einen Aufruf von Hand.

**`KosmoPrepare/core/multiview_texture.py`** (54 Z.) — kein Platzierungsverfahren, aber
bemerkenswert: **reines numpy, ausdrücklich Blender-frei testbar**. Wählt für jede Fläche die
beste Kamera über `facing / (1 + k·dist²)`, gültig nur wenn die Fläche zur Kamera zeigt und
im Blickfeld liegt. Wenn wir je fragen „welche unserer Kameras sieht diese Fassade am
besten?", steht das Verfahren hier. **Reine Rechnung**, vorbildlich.

**`KosmoPrepare/tools/render_*.py`** (6 Dateien) — Blender-Skripte für Massenstudien. Die
Kameraplatzierung ist durchweg **handgesetzt** (`ortho_scale = w · 1.3`, Kamera bei
`ccy − 0.95·w` auf `0.9·w`). Keine Rechnung, keine Ableitung. Eine dieser Dateien enthält
einen **hartcodierten persönlichen Cloud-Pfad** und ruft `addon_utils.enable(...)` — sie
setzt ein installiertes Add-on voraus. **Nicht übernehmbar**, weder rechtlich noch praktisch.
Als Beleg taugen sie: die Skripte sind gelaufen, sonst gäbe es die Bildausgaben nicht, auf
die sie sich beziehen.

**`KosmoPrepare/core/camera_path.py`** — wie in der Vorsichtung vermutet: Kamera-**Export**
nach COLMAP/Nerfstudio, keine Platzierung. Für uns nur als Vertragsvorbild interessant, falls
wir je Kameras an eine Rekonstruktionspipeline übergeben.

---

# TEIL B · Der Node-Tree

Ausgewertet, aber weniger tief als Teil A.

## B.1 · Was es ist

`KosmoVis/01_workflow/archviz_pipeline_nodes.py` definiert einen **eigenen Blender-Node-Tree**:

- **Tree:** `bl_idname = "ArchVizPipelineTree"`, `bl_label = "KosmoVis"`.
- **Vier eigene Sockeltypen:** `ArchVizSocketCamera` („Camera Config"), `ArchVizSocketImage`
  („Image"), `ArchVizSocketLayer` („Render-Layer"), `ArchVizSocketVariant` („Variant"). Jeder
  mit fester Farbe.
- Ein gemeinsames Mixin für das Aussehen aller Knoten.

**Diese vier Sockeltypen sind die eigentliche Auskunft.** Sie sagen, welche vier Datenarten
zwischen den Stufen fliessen sollen: eine Kamerakonfiguration, ein Bild, ein Renderlayer, eine
Variante. Wenn unsere MCP-Schicht Verträge anbietet, sind das die vier Kandidaten.

## B.2 · Die Knotenliste

`archviz_auto_setup.py` baut den Tree in **fünf Rängen** auf (Kommentar: „Logischer
User-Workflow von links nach rechts"):

| Rang | Zweck | Knoten |
|---|---|---|
| 1 | Grundlagen | PlanReference · BuildingAnalyzer · **CameraCombined** · AssetRecommendation |
| 2 | Assets + Material | AutoScatter · MaterialCatalog · MaterialPreview · ReferenzDB |
| 3 | Stil + Render + KI | StyleSkill · TexturePlus · **AIPipelineV2** · RenderQueue |
| 4 | Korrektur | CompareAB · SketchEdit · AssetInserter · ImageAnnotator |
| 5 | Export + Alternativen | ArchiCADExport · CustomCameras · Marble |

Dazu eine **Altlast-Reihe** in `archviz_pipeline_nodes_legacy.py`, ab 27.05.2026 ausgelagert
und für Neuanlagen abgeraten, die der Demo-Vision **noch näher** kommt:

`Camera → MaterialPass → LayerFilter → Compositor → AIVariant → Output`

Das ist fast eins zu eins die Kette aus der Demo-Vision des Owners. Die neuere Fassung hat
diese Kette in breitere Werkzeugknoten aufgelöst.

## B.3 · Die unbequeme Wahrheit über die Verdrahtung

**Der Tree ist kein Datenflussgraph.** Beim Aufbau wird `tree.links.clear()` gerufen; die
Ränge werden als farbige Rahmen nebeneinandergelegt, **ohne Verbindungen**. Eine Suche nach
`links.new` über alle 83 Module findet Treffer nur in *Material*- und *Compositor*-Bäumen von
Blender selbst — nicht im Pipeline-Tree.

Es gibt ein Modul `archviz_pipeline_wiring.py`, das genau das nachrüsten will („Auto-Wire:
erstellt alle fehlenden Soll-Verbindungen mit einem Klick", „listet isolierte Nodes"). Dass es
existiert, ist der Beleg dafür, dass die Knoten **normalerweise unverbunden** dastehen.

Die Knoten reden stattdessen über **Szenen-Eigenschaften als Seitenkanal** — etwa
`scene["archviz_building_min"]` / `["archviz_building_max"]`, die die Gebäudeerkennung setzt
und die Kamerarechnung liest. Der Kommentar in `archviz_style_skills.py` sagt es offen: der
Stil wird „via Scene-Properties als Bridge" in den nächsten KI-Lauf gereicht.

**Für uns heisst das:** Der Tree ist eine **Werkzeugpalette mit Ablaufreihenfolge**, kein
Graph. Die Reihenfolge (Rang 1 bis 5) und die Feldnamen sind übernehmbar. Eine
Verdrahtungslogik gibt es nicht zu übernehmen — sie müsste bei uns erst entstehen, und
unsere `graph.py`/`kette.py` sind dafür vermutlich schon weiter als das Vorbild.

## B.4 · Feldnamen des Kameraknotens

`ARCHVIZ_NODE_CameraCombined` (`bl_idname = "ArchVizNodeCameraCombined"`) führt zwei
Abschnitte. Die Feldnamen, weil sie laut Auftrag die teuerste Sorte Fehler sind:

**Automatik:** `distance_factor` (1.0; 0.3–5.0) · `bias_deg` (35.0; 15–60) ·
`last_direction` · `last_detected_main` · `last_detected_count` · `last_detected_size` ·
`node_status` (pending/ready/done/error) · `last_render_path`

**Von Hand:** `anchor_x/y/z` · `bbox_size_x/y/z` · `eye_height` (1.7) · `distance` (25.0) ·
`azimuth_deg` (180.0) · `elevation_deg` (0.0) · `offset_x/y/z` · `lens_mm` (28.0) ·
`pixel_width` (2048) · `aspect_ratio` (4:3 / 3:4 / 16:9 / 1:1) · `live_update`

Das ist ein **vollständiger Kameravertrag mit Automatik- und Handbetrieb** und damit die
dritte Feldnamensfassung im Bestand — neben `camera_presets.json` und dem
`_capture_camera_state`-Format aus A.4. Auch hier: `eye_height` heisst überall gleich,
`lens_mm` auch; aber die Richtungsangabe ist mal `look_at`, mal `rotation_euler`, mal
`azimuth_deg`/`elevation_deg`.

**Einstufung:** Der Knoten ist **Add-on/UI, nicht übernehmbar** — `bpy.props`-Felder,
`update`-Rückrufe, die `bpy.ops` auslösen, `poll` gegen den Tree-Typ. Die **Feldnamen und
Vorgabewerte** sind Auskunft und übernehmbar.

## B.5 · Add-on-Verpackung im Bestand

`bl_info` gefunden in: `KosmoVis/01_workflow/archviz_camera.py`,
`archviz_pipeline_nodes.py`, `archviz_pipeline_wiring.py` (und weiteren KosmoVis-Modulen),
sowie `KosmoPrepare/__init__.py`, `KosmoPublish/__init__.py`,
`KosmoPublish/blender_addon/__init__.py`, `KosmoPublish/nodes/final_export.py`.

`register()`/`unregister()` in rund 100 Dateien über alle Repos.

Dazu `archviz_autoloader.py`: ein Modul, das in Blenders Startverzeichnis kopiert wird und
über einen `load_post`-Handler bei jedem Dateiöffnen **alle** Module registriert. Es enthält
einen **hartcodierten persönlichen Cloud-Pfad** und einen Dateinamensfilter auf ein reales
Projektkürzel.

**Alles davon fällt unter Regel 2 und ist nicht übernehmbar.** Der Autoloader ist zusätzlich
unter Regel 3 belastet.

---

# TEIL C · Kompositor, Material, Presets, Stile

Ab hier ist die Auswertung eine Übersicht, keine Tiefenprüfung. Ich habe hier aufgehört, weil
Teil A gründlich wichtiger war als Teil C vollständig.

## C.1 · Kompositor und Passes — mit einer wichtigen Warnung

`archviz_multipass_render.py` (784 Z.) erzeugt Beauty plus Zusatzpasses. Der Kopfkommentar
enthält den wertvollsten Satz des ganzen Bestands für unsere Renderstufe:

> Blender 5.1's `compositing_node_group` und `OutputFile`-Nodes werden beim Render **nicht
> zuverlässig ausgeführt** (API-Regression). Wir umgehen das mit View-Layer-Material-Override.

**Das ist eine bezahlte Erfahrung, die wir sonst selbst machen.** Wer bei uns Passes über
Blenders Kompositor herausschreiben will, sollte das zuerst gegen die eingesetzte
Blender-Fassung prüfen.

Der Tiefenpass hat **drei Wege mit Rückfall**, im Code benannt als `compositor_z` (echter
`use_pass_z`-Pass), `foreach_z` (Pixel direkt auslesen) und `emission_fallback`. Der gewählte
Weg wird im Ergebnis mitgeschrieben — die Ausgabe sagt, wie sie zustande kam. **Das ist eine
Bauart, die wir übernehmen sollten**, unabhängig vom Code: ein Verfahren mit Rückfallebenen,
das protokolliert, welche Ebene gegriffen hat.

Ein Material-ID-Pass wird über `mat.pass_index` erzeugt, mit Sicherung und Wiederherstellung
der vorherigen Werte.

Passes nach Qualitätsstufe: Test/schnell nur Beauty; Standard/hoch zusätzlich Material-Farbe.
Tiefe, Normalen und Linien kommen ausdrücklich **nicht** aus Blender, sondern aus den
Vorverarbeitern der KI-Stufe.

**Einstufung:** durchweg **braucht bpy**. Die Rückfall-Bauart ist eine Idee, kein Code.
**Reifegrad:** erprobt genug, dass die Umwege dokumentiert sind — das ist ein starkes
Zeichen. `test_depth_wiring.py` und zwei Smoke-Skripte für den Tiefenpass existieren.

## C.2 · Material und Farblayer

`archviz_material_catalog.py` (1171 Z.). Vergabe der Material-IDs: **deterministisch über den
goldenen Schnitt.** `hue = (index · 0.61803398875) mod 1`, dann HSV nach RGB bei voller
Sättigung und Helligkeit. Das erzeugt für beliebig viele Materialien gut unterscheidbare
Farben, ohne eine Palette zu pflegen.

**Das ist reine Rechnung, in drei Zeilen nachbaubar, und genau das, was ein Material-ID-Pass
braucht.** Die einzige Zutat, die unser Produkt hier wirklich übernehmen sollte.

Pro Material werden ausserdem geführt: ein eigener Prompt, eine Referenztextur oder ein
KI-Platzhalter, und vier Regler (Skalierung, Drehung, UV-Ausrichtung, KI-Stärke). Die
Texturbeschaffung läuft dreistufig: Treffer in einer lokalen PBR-Bibliothek, sonst Erzeugung
über ComfyUI, sonst Cache. Der Pfad zur Bibliothek ist ein **hartcodierter persönlicher
Cloud-Pfad**.

`archviz_materials.py` baut Blender-Materialgruppen mit benannten Eingängen (Base Color,
Roughness, Metallic, IOR, Coat Weight, Transmission, Sheen Weight, UV Scale, Normal Strength,
Bump Strength, Use Triplanar). **Braucht bpy**, aber die Feldliste ist eine brauchbare
Materialvertragsvorlage.

## C.3 · Presets — HDRI, Licht, Renderstile

Vorhanden, aber dünner als der Rest:

- `archviz_prompt_library.py` (194 Z.) — modulare Prompt-Bausteine in JSON, **sieben
  Kategorien**: `vegetation`, `people`, `atmosphere`, `light_time`, `sky`, `material_detail`,
  `composition`. Saubere API (`load_library`, `list_categories`, `list_options`, `get_prompt`,
  `compose`). **Reine Rechnung**, bpy-frei, sofort verständlich. Die JSON-Datei selbst liegt
  unter `_DEV/prompts/library.json` und ist **nicht im Repo** — die Kategorien sind belegt,
  die Inhalte nicht.
- `archviz_style_skills.py` (296 Z.) — Architekturstile als auswählbare „Skills" mit
  `slug`/`display_name`/`description`, aus einer Registry `archviz_styles`. Diese Registry ist
  **ebenfalls nicht im Repo**.
- `archviz_light_sweep.py` (587 Z.) und `archviz_material_sweep.py` (807 Z.) — Reihenversuche
  über Lichtstimmungen bzw. Materialien. Nicht ausgewertet.
- `archviz_cycles_quality.py` (715 Z.) — Qualitätsstufen samt Nachbearbeitung (Glare,
  Linsenverzerrung) über Blenders Kompositor. Nicht ausgewertet.

**Zur Frage „Renderstile — Code oder Wunsch?":** Es ist **beides, mit dem Gerüst auf der
Codeseite und dem Inhalt auf der Wunschseite.** Die Auswahlmechanik, die Kategorien und die
Weiterreichung in den KI-Lauf sind gebaut. Die eigentlichen Stildefinitionen — was
„skizzenhaft" konkret bedeutet — liegen in Dateien, die nicht im Repo sind. Wer den Bestand
übernimmt, erbt die Form, nicht den Inhalt.

## C.4 · Nicht ausgewertet

`archviz_comfyui_workflow.py` (1706 Z.) und `archviz_ai_pipeline_v2.py` (1450 Z.) sind die
beiden grössten Module des Bestands und betreffen die KI-Stufe. Beide **nicht geöffnet**.
Wenn unsere ComfyUI-Anbindung ansteht, ist das die erste Adresse.

Ebenfalls nicht ausgewertet: `archviz_archicad_export.py`, `archviz_marble_bridge.py`,
`archviz_trellis_bridge.py`, `archviz_gemini_omni_bridge.py`, `archviz_speech_input.py`,
`archviz_asset_recommendation.py`, `archviz_auto_scatter.py`, `archviz_variant_scorer.py`,
`archviz_qa_gate.py`, `archviz_cost_tracker.py`.

---

# TEIL D · Der Vertrag, der schon zu uns passt

`KosmoVis/docs/RENDER_SCENE_CONTRACT.md` (Stand 2026-06-16, „v1") ist unabhängig vom
Add-on-Code entstanden und beschreibt, **was die Vis-Stufe als Prozess entgegennimmt und
liefert** — genau die Schnittstelle, die wir brauchen.

Eingang `render-scene.json`: `schema`, `project`, `geometry{path,format}`, `cameras`
(`"auto"` | `"saved"` | Liste von Richtungskürzeln), `render{resolution, samples, faithful,
sun{lat,lon,datetime,presets}}`, `style{mode,refs,lora,prompt}`,
`vis{skip,backbone,upscale}`, `out`.

Ausgang `render-scene-result.json`: je Kamera ein `passes`-Block (`beauty`, `depth`,
`depth_method`, `material`, `material_id`), dazu `ai_variant`, `qa{ok,notes}`, sowie
`engine`, `cost{gpu_peak_w, wall_s, cloud_chf}` und `status` (`ok|partial|failed`).

Drei Dinge daran verdienen Aufmerksamkeit:

1. **`faithful`** — ein Regler von 1.0 (Cycles-treu) bis 0.0 (KI-frei), im Kommentar als
   ControlNet-Stärke ausgewiesen. Das ist die „KI-Einstellung" der Demo-Vision, als eine
   einzige Zahl. Ein guter Entwurf.
2. **`depth_method`** wandert in die Ausgabe. Die Ausgabe sagt, wie sie entstanden ist.
3. **`cameras: "auto"`** verweist auf genau die zwölf Richtungen aus A.1 — hier schliesst
   sich der Kreis zwischen Vertrag und Rechnung.

**Einstufung:** ein Dokument, kein Code — vollständig übernehmbar, ohne Regel-2-Frage.
**Reifegrad:** als Vertrag durchdacht (Versionierung, defensives Lesen, Abstufung bei
fehlenden Abschnitten). Ob er je vollständig bedient wurde, geht daraus nicht hervor;
`run_kosmovis_stage.py` erfüllt ihn teilweise.

---

# TEIL E · Was ich übernehmen würde und was nicht

Das ist der Teil, der zählt.

## E.1 · Übernehmen, als bpy-freies Modul des Produkts

**1 · Die Abstandsrechnung aus dem Bildwinkel** (A.1, ergänzt um A.2).

Aus Brennweite, Sensormass, Hüllbox und einem Deckungsgrad einen Abstand rechnen. Mit den
Verbesserungen aus `archviz_camera.py`: den vertikalen Bildwinkel aus dem **Seitenverhältnis**
ableiten statt aus einer festen Sensorhöhe, und den vertikalen Bedarf **von der Augenhöhe aus
asymmetrisch** messen. Beides ist in V6 schlechter gelöst als im Vorläufer.

*Warum:* Das ist der Kern und er ist reine Trigonometrie. Ohne Blender testbar, mit von Hand
nachrechenbaren Erwartungswerten.

**2 · Den Frustum-Test über alle acht Ecken** (A.1, `ensure_bbox_in_frustum`).

Kamerabasis aus der Blickrichtung, perspektivische Division je Ecke, Vergleich gegen die
Tangenswerte mit Sicherheitsrand, Rückschub proportional zum Überstehen, Augenhöhe konstant,
Iterationsdeckel mit ehrlicher Rückgabe.

*Warum:* Das ist die Antwort auf die schwierigste Frage des Auftrags, und sie ist reine
Rechnung. Der Deckel mit „liefert eine als unvollkommen gekennzeichnete Antwort" statt einer
Ausnahme passt zu unserer Bauart.

**3 · Die Verkürzungsrechnung für orthografische Rahmen** (A.3).

Grundrissanteil mal `sin(elev)`, Höhe mal `cos(elev)`, der grössere gewinnt, plus Rand.

*Warum:* Sobald wir Axonometrien oder Ansichten anfassen, brauchen wir das. **Und es ist die
einzige Fundstelle mit einem Regressionsnetz, das einen echten Vorzeichenfehler festhält.**
Diesen Test würde ich sinngemäss mit nachbauen — die Randwinkel 0° und 90° sind physikalisch
eindeutig und damit ideale Prüfpunkte.

**4 · Die zwölf Richtungen samt Bias-Regler** (A.1).

Vier frontal mit seitlichem Versatz, acht diagonal mit `bias_deg` als Regler für das
Fassadenverhältnis (30° = 2/3 zu 1/3, 45° = Eckblick, 35° = ausgewogen).

*Warum:* Das ist **architektonisches Bildwissen, keine Programmierung.** Die Zuordnung von
Winkel zu Bildwirkung erfindet man nicht neu, man erbt sie. Beim Nachbau die vier
N/S-Diagonalen gegen eine Skizze prüfen — dort steckte nachweislich ein Vorzeichenfehler.

**5 · Die Material-ID-Farbvergabe über den goldenen Schnitt** (C.2).

*Warum:* Drei Zeilen, deterministisch, beliebig erweiterbar, löst ein Problem, das wir sonst
mit einer gepflegten Palette lösen würden.

**6 · Die Beste-Kamera-je-Fläche-Bewertung** (A.5, `multiview_texture.py`).

*Warum:* Bereits bpy-frei und in numpy geschrieben. Falls wir je fragen, welche unserer
Kameras eine Fassade am besten sieht, ist die Frage beantwortet.

## E.2 · Übernehmen, aber in den Runner

**7 · Den Verdeckungstest per Raycast** (A.1).

*Warum:* Braucht die Szene, punkt. Aber mit einem Schnitt, den der Bestand nicht macht: die
**Schrittlogik** von `pull_camera_until_clear` (12 %-Schritte, Untergrenze 6 m, Stopp am
erweiterten Hüllbox-Rand, Augenhöhe konstant) ist reine Rechnung. Wenn die Verdeckungsprüfung
als übergebene Funktion hineingereicht wird, ist die Schrittlogik ohne Blender testbar und
nur der Strahlenschuss selbst bleibt im Runner. **Das ist die Trennung, die der Auftrag
verlangt, an der Stelle, wo sie am meisten bringt.**

**8 · Die Rückfall-Bauart des Tiefenpasses** (C.1).

Nicht der Code — die Bauart: mehrere Wege, geordnet, und **die Ausgabe schreibt mit, welcher
Weg gegriffen hat**.

**9 · Die Warnung zum Blender-Kompositor** (C.1).

Kein Code, eine Erfahrung: `OutputFile`-Knoten liefen in Blender 5.1 beim Render nicht
zuverlässig. Vor dem Bau unserer Passes prüfen.

## E.3 · Übernehmen als Vertrag, nicht als Code

**10 · `RENDER_SCENE_CONTRACT.md`** (Teil D) — als Vorbild für unseren Renderauftrag,
besonders `faithful` als eine Zahl und `depth_method` in der Ausgabe.

**11 · Die vier Sockeltypen** (B.1) — Camera Config, Image, Render-Layer, Variant. Als
Antwort auf die Frage, welche Datenarten unsere MCP-Schicht zwischen den Stufen führen muss.

**12 · Die Ablaufreihenfolge der fünf Ränge** (B.2) — als Auskunft darüber, in welcher
Reihenfolge der Owner die Arbeitsschritte denkt.

## E.4 · Nicht übernehmen

**Alles mit `bl_info`, `register()`, `bpy.props`, `Operator`, `Panel`, `Node`.** Regel 2, ohne
Ermessen. Das betrifft `archviz_camera.py` als Ganzes, sämtliche Knotenklassen, alle
N-Panel-Module, `archviz_autoloader.py`.

**Den Autoloader ganz besonders.** Er kopiert sich in Blenders Startverzeichnis, hängt sich an
einen `load_post`-Handler und registriert bei jedem Dateiöffnen 60 Module. Das ist die
Bauart, die Regel 2 verhindern soll — und er enthält zusätzlich einen persönlichen Cloud-Pfad
und ein reales Projektkürzel (Regel 3).

**Die Platzierung aus `kosmodraw_bridge.py`** (A.4). Fester Faktor 1.5, Brennweite geht nicht
ein, keine Prüfung ob das Gebäude passt. Wir haben mit A.1 etwas Besseres. **Den Vertrag**
(`name`, `location`, `look_at`, `lens_mm`, `type`) würde ich behalten, das Verfahren dahinter
ersetzen.

**Die festen Renderrezepte aus `render_specs.py`** (A.5). Die Zahlen sind auf ein reales
Projekt zugeschnitten. Die **Feldstruktur** ja, die Werte nein.

**Die `render_*.py`-Skripte aus KosmoPrepare.** Handgesetzte Kameras, persönliche Pfade,
`addon_utils.enable`.

**Die „Verdrahtungslogik" des Node-Trees** — weil es sie nicht gibt (B.3). Der Tree ist eine
Palette, die Knoten reden über Szenen-Eigenschaften. Hier gibt es nichts zu erben; unsere
`graph.py`/`kette.py` sind vermutlich schon weiter.

## E.5 · Die Entscheidung, die vor dem Nachbau fallen muss

**Es gibt drei unvereinbare Kameraverträge und drei Augenhöhen.**

| Herkunft | Richtungsangabe | Augenhöhe | Bezug |
|---|---|---|---|
| `camera_presets.json` (A.4) | `look_at` | 1.7 (Parameter) | relativ zu `zmin` |
| `_capture_camera_state` (A.4) | `rotation_euler` | — | — |
| `CameraCombined` (B.4) | `azimuth_deg`/`elevation_deg` | 1.7 | absolut |
| `render_specs.py` (A.5) | `look_at_xyz` | **1.65** | absolut |

`look_at` nach `rotation_euler` ist eindeutig; zurück nicht, weil ein Blickvektor keine
Zielentfernung kennt. Und 1.65 gegen 1.70 ist keine Rundung, sondern eine andere Annahme über
den Menschen im Bild.

**Empfehlung:** `look_at` als führende Form (sie ist erklärbar und stabil gegenüber
Rotationskonventionen), `rotation_euler` als abgeleitete Zusatzangabe für Blender, Augenhöhe
**absolut** und **1.70 m** — weil die Mehrheit des Bestands und das ausgereifteste Verfahren
(A.1) es so halten. Das gehört entschieden, bevor die erste Zeile entsteht, nicht danach.

---

# TEIL F · Lizenz und Herkunft (Regel 1)

**Kein GPL- oder AGPL-Fund im übernehmbaren Material.** Zwei Punkte zur Kenntnis:

1. **Zwei Verweise auf eine fremde Quelle.** `archviz_style_skills.py` und
   `archviz_qa_gate.py` tragen den Vermerk, ein Muster sei aus einem fremden
   GitHub-Projekt („image-blaster") übernommen. Es geht erkennbar um ein *Muster*, nicht um
   kopierten Code — aber die Lizenz jenes Projekts ist **ungeprüft**. Da wir von diesen beiden
   Modulen ohnehin nichts übernehmen, ist das folgenlos. **Sollte sich das ändern, zuerst die
   Lizenz klären.**

2. **Eine GPL-Erwähnung in einer Analyse-Notiz.** Ein Vergleichsdokument im Bestand führt ein
   fremdes Blender/ComfyUI-Projekt und markiert es ausdrücklich als GPL. Es wurde als
   *lehrreich* eingestuft, nicht eingebunden. Ich habe keinen Hinweis darauf gefunden, dass
   Code daraus übernommen wurde. **Trotzdem gemeldet, weil Regel 1 das so will.**

3. Ein Modul verweist im Kommentar auf ein Beispielskript aus dem ComfyUI-Projekt. Nur ein
   Verweis in einer Fehlermeldung, kein Code.

Die untersuchten Repos sind privat und tragen keine Lizenzdatei, die eine Weiterverwendung
regeln würde. **Alles, was wir übernehmen, ist Eigentum des Owners** — das ist der Grund,
warum Herkunft hier keine Schranke ist, sondern nur Sorgfalt verlangt.

Zum Blender-Binary selbst ändert dieser Bericht nichts: Es bleibt eine GPL-Komponente, die
als eigenständiges Programm aufgerufen und im `NOTICE` deklariert wird.

---

# TEIL G · Was offen blieb

1. **`KosmoOrbit` wurde nicht ausgewertet.** Die Oberfläche der Demo-Vision gehört dorthin.
   Falls dort ein zweiter Knotenentwurf liegt, wäre er mit B.2 abzugleichen.
2. **`legacy_archive/` fehlt im Repo.** Die Vorgängerfassungen `archviz_pipeline_v2` bis
   `_v5_smart` sind im Autoloader gelistet, aber nicht vorhanden. Vermutlich unwichtig.
3. **Die Stil- und Prompt-Inhalte fehlen** — `archviz_styles/` und `_DEV/prompts/library.json`
   sind nicht im Repo. Die Kategorien sind belegt (C.3), die Inhalte nicht. **Wenn die
   Renderstile aus der Demo-Vision aus diesem Bestand kommen sollen, muss der Owner sagen, wo
   diese Dateien liegen.**
4. **Die beiden grössten KI-Module sind ungeöffnet** (C.4, zusammen über 3100 Zeilen).
5. **Ziehen Frustum-Test und Verdeckungstest gegeneinander?** Der eine schiebt weg, der andere
   heran; im Code laufen sie nacheinander. Ob das schwingt, wäre bei einem Nachbau zu prüfen.
6. **Die `.blend`-Dateien wurden nicht angesehen** — der gespeicherte Tree liegt dort, nicht
   im Code. Was hier über den Tree steht, stammt aus dem Aufbaucode.
7. **Kein Beleg für einen vollständigen Zwölf-Kamera-Lauf.** Der Stress-Test-Bericht bestätigt,
   dass der Knoten registriert und fehlerfrei ist; `run_kosmovis_stage.py` sagt selbst, das
   Render-Ergebnis sei ohne echten Blender-Lauf nicht verifiziert. **Dass die Kameras
   registriert sind, ist kein Beleg dafür, dass die zwölf Bilder je gut aussahen.**
8. **Das Lexikon wurde nicht nachgeführt.** Dieser Auftrag war auf eine Datei beschränkt. Neue
   Begriffe, die nachzutragen wären: *Frustum*, *Bildwinkel*, *Raycast*, *Hüllbox/Bounding
   Box*, *Ortho-Scale*, *Axonometrie*, *Node-Tree*, *Socket*, *Pass/Multipass*, *Material-ID*,
   *Depsgraph*, *Add-on*, *Perspektivische Division*, *ControlNet-Stärke*. **Das ist eine
   offene Pflicht aus `CLAUDE.md`.**

---

## Anhang · Fundstellenverzeichnis

Alle Pfade relativ zum jeweiligen Ökosystem-Repo. Einstufung: **R** = reine Rechnung,
**B** = braucht bpy, **A** = Add-on/UI.

| Datei | Was | Einst. | Reife |
|---|---|---|---|
| `KosmoVis/01_workflow/archviz_pipeline_v6_camera_math.py` | 12 Richtungen, Bildwinkel-Abstand, Frustum-Test, Verdeckung | R + B | erprobt, ohne Test |
| `KosmoVis/01_workflow/archviz_camera.py` | analytischer Frame-Fit, Aspekt-Ableitung | R + B + A | Vorläufer |
| `KosmoVis/01_workflow/archviz_pipeline_v6_combined.py` | Kameraknoten, Feldnamen | A | erprobt |
| `KosmoVis/01_workflow/archviz_custom_cameras.py` | Kamerazustand speichern/anwenden | B + A | erprobt |
| `KosmoVis/01_workflow/archviz_camera_check.py` | Kamera-im-Mesh-Prüfung, 6 Strahlen | B | Entwurf |
| `KosmoVis/01_workflow/archviz_pipeline_nodes.py` | Tree + 4 Sockeltypen | A | erprobt |
| `KosmoVis/01_workflow/archviz_pipeline_nodes_legacy.py` | alte 6er-Kette | A | Altlast |
| `KosmoVis/01_workflow/archviz_auto_setup.py` | 5-Rang-Layout, Knotenliste | A | erprobt |
| `KosmoVis/01_workflow/archviz_autoloader.py` | Autostart-Registrierung | A | **nicht übernehmbar** |
| `KosmoVis/01_workflow/archviz_multipass_render.py` | Passes, 3 Tiefenwege | B | erprobt |
| `KosmoVis/01_workflow/archviz_material_catalog.py` | Material-IDs golden ratio | R + B | erprobt |
| `KosmoVis/01_workflow/archviz_prompt_library.py` | 7 Prompt-Kategorien | R | Gerüst ohne Inhalt |
| `KosmoVis/docs/RENDER_SCENE_CONTRACT.md` | Vertrag Ein-/Ausgang | Dokument | durchdacht |
| `KosmoVis/01_workflow/_pilot/run_kosmovis_stage.py` | headless Runner, 12 Richtungen | B | teilverifiziert |
| `KosmoPublish/nodes/axonometry.py` | Ortho-Verkürzung, Pure-Math-Trennung | R + B | **erprobt, mit Test** |
| `KosmoPublish/nodes/elevation.py` | 4 Ansichten | R + B | Test vorhanden |
| `KosmoPublish/nodes/section.py` | Schnitte über Clipping | R + B | Test vorhanden |
| `KosmoPublish/nodes/floor_plan.py` | Grundrisse über Clipping | R + B | Test vorhanden |
| `KosmoPublish/nodes/render_specs.py` | 5 feste Rezepte, Feldstruktur | R | Struktur ja, Verfahren nein |
| `KosmoPublish/nodes/render_executor.py` | TRACK_TO-Ausrichtung | B | Entwurf |
| `KosmoPrepare/nodes/kosmodraw_bridge.py` | 8 Presets, `camera_presets.json` | R + B | **Entwurf, kein Konsument** |
| `KosmoPrepare/core/multiview_texture.py` | beste Kamera je Fläche | R | bpy-frei, vorbildlich |
| `KosmoPrepare/core/camera_path.py` | Export COLMAP/Nerfstudio | R | kein Platzierungsverfahren |
| `KosmoPrepare/tools/render_*.py` | 6 Skripte, Kameras von Hand | B | **nicht übernehmbar** |
