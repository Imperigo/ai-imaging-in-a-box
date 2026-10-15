# RealityScan-Brücke — die Umgebung als Netz aus den Fotos

**Warum das hier liegt.** Der offene Splat-Weg (gsplat + Open3D, `betrieb/SPLAT_BRUECKE.md`)
deckt am echten Splat nur rund 10 % der Umgebung (`auf-20261013-276`/`-277`). Owner-Entscheid 81
(13.10.2026): Die Umgebung kommt als echtes Netz aus den **Fotos** der Aufnahme, über **Epic
RealityScan 2.1**. RealityScan ist ein **Fremdprogramm, vom Nutzer installiert** (CLAUDE.md,
Entscheid 79): Visbox ruft es nur auf, wenn der Owner es auf seinem eigenen Rechner selbst
installiert, lizenziert und eingeschaltet hat.

**Ohne Einrichtung ändert sich nichts.** Dann läuft der offene Weg wie bisher, und der Vermerk
sagt es: `kontext.weg` steht auf `"netz"` oder `"kugeln"`, `kontext.realityscan_grund` auf
«RealityScan nicht eingeschaltet …». Mit RealityScan steht `kontext.weg` auf `"realityscan"`, und
jedes Ergebnis trägt in `verdict.hinweise` den Satz «UMGEBUNG aus den Fotos (RealityScan, vom
Nutzer installiert) — nicht im Produkt ausgeliefert.»

**Fassung 3 (14.10.2026): Textur statt Eckfarben.** Die HomeStation hat am echten Auftrag gemessen:
Ein **texturiertes** Netz ist im Bild so scharf wie der Splat oder schärfer (Schärfe
Splat/Textur/Eckfarben 4.1/7.4/6.3, 4.9/7.8/7.3, 4.8/7.0/3.4, an einer Fensterwand 3.2/4.1/1.9); mit
**Eckfarben** (eine Farbe je Ecke) sind Fensterwände unlesbar. Seither wickelt die Brücke das Netz ab,
rechnet die Textur und lädt in Blender ein **OBJ mit PNG-Bildern** — sofern die **Abwicklungsdatei**
eingerichtet ist (unten, Schritt 3). Ohne sie bleibt alles wie in Fassung 2 (PLY mit Eckfarben), und
der Bericht sagt es (`hinweise`: «Eckfarben statt Textur …»).

## Nie für Kunden, nie mitgeliefert

* **Nie über KosmoOrbit für Kunden.** Die EULA (§1.2 c/d) verbietet die Nutzung durch Dritte,
  Hosting und «service bureau». Die Variablen unten gehören **nur** in die Umgebung des
  Dienstes auf dem Rechner des Lizenznehmers, für seine eigenen Aufträge — nie in eine
  Einrichtung, die Aufträge anderer rechnet.
* **Nie mitgeliefert.** Kein Binary, kein Installer, kein Download durch Visbox. Visbox sucht
  RealityScan auch **nicht** von selbst (kein Durchsuchen von `/opt`, kein `PATH`): Eingeschaltet
  ist es nur, wenn die Variable gesetzt ist — eine bewusste Einrichtung, kein Zufallsfund.
* **Nie Voraussetzung.** Fehlt etwas oder scheitert der Lauf, nimmt Visbox den offenen Weg und
  sagt den Grund (ohne Pfad) in `kontext.realityscan_grund`.

## Was der Owner selbst tut

1. **Paket laden und installieren** — das `.deb` (oder `.rpm`) von realityscan.com/linux, mit dem
   eigenen Epic-Konto. Es installiert nach `/opt/realityscan` und bringt sein eigenes Wine mit.
2. **Lizenz aktivieren.** RealityScan ist gratis unter 1 Mio. USD Umsatz in 12 Monaten, sonst
   1250 USD je Platz und Jahr (Owner bestätigt 14.10.2026: gratis gilt). Einmal mit Oberfläche
   anmelden; danach läuft `-headless` ohne Anmeldung und ohne Bildschirm (`auf-20261013-278` F2).
3. **Die zwei Einstellungsdateien an einen eigenen Ort kopieren** (Fassung 3) — die Vorlagen liegen im
   Repo unter `betrieb/realityscan/`, ohne Pfade und ohne Namen; die Brücke liest sie nur über die
   Variablen unten und erfindet keine:

       mkdir -p ~/realityscan
       cp betrieb/realityscan/export-obj-textur.xml betrieb/realityscan/unwrap-optimal.xml ~/realityscan/

   * `export-obj-textur.xml` — Export als **OBJ** mit **PNG**-Textur, ohne Eckfarben, gedreht um
     90° um X (`settingsRotation` «90 0 0», wie in Fassung 2: so kommen die Koordinaten der Aufnahme
     zurück). **Wichtig:** `Layer0 type="1"` ist die Farbtextur; `type="5"` liefert nur ein
     Schachbrett — die Brücke weist eine solche Datei ab («nicht eingerichtet»).
   * `unwrap-optimal.xml` — die **Abwicklung**: kleinste Texelgrösse «optimal», grösste Typ 4,
     Kacheln fest 8192, grosse Dreiecke ab Schwelle 10 entfernt, Fuge 2 Bildpunkte. **Wichtig:** Die
     Schalter `-set unwrap…` wirken in der Befehlszeile **nicht**; erst diese Datei, als Argument an
     `-unwrap` übergeben, wirkt. Mit den Vorgaben von RealityScan: 1 Textur zu 8K bei 7.6 mm je
     Texel; mit dieser Datei 3–4 Texturen zu 8K bei etwa 3 mm.

   **Nur Fassung 2 (Eckfarben, ohne Abwicklungsdatei):** die PLY-Exportdatei, wie bisher — den
   `ModelExport`-Abschnitt aus der `.rsinfo` eines Exports in eine leere `.xml` kopieren (Hilfe
   «Model Export»). Am Heim-PC gemessen (278 E1), **so muss sie stehen:**
   * PLY binär (`formatAndVersionUID` «ply 000», `exportBinary=1`), Ecken und Dreiecke an;
   * `exportVertexColors=0` (!) — mit 1 schreibt RealityScan nur die Netzfarbe (weiss);
   * `exportVertexColorSpace=1` (0 liefert linear, viel zu dunkel);
   * `settingsRotation` «90 0 0» — RealityScan vertauscht intern die Achsen; erst diese Drehung
     gibt die Koordinaten der Aufnahme unverändert zurück;
   * Massstab 1 1 1, Anker 0 0 0, `exportCoordinateSystemType=0`.
   *Visbox erfindet diese Datei nicht:* ihr Format ist nicht dokumentiert.

   **Widersprüche weist die Brücke ab** (Grund ohne Pfad, Ursache `einrichtung`, dann der offene
   Weg): Abwicklungsdatei gesetzt, aber die Exportdatei wählt PLY — oder die Exportdatei wählt OBJ,
   aber die Abwicklungsdatei fehlt (ein OBJ ohne Textur wäre grau).
4. **Die Variablen für den Dienst setzen** — nicht in der eingecheckten Einheit
   (`betrieb/kosmo-abholer.service` wird gegen die installierte Fassung geprüft), sondern als
   Ergänzung: `systemctl --user edit kosmo-abholer.service` (ebenso für den Heim-Worker, wenn er
   Ketten mit Splat rechnet) und dort

       [Service]
       Environment=AIIMAGING_REALITYSCAN=<das wine des Pakets>
       Environment=AIIMAGING_REALITYSCAN_EXPORT_XML=%h/realityscan/export-obj-textur.xml
       Environment=AIIMAGING_REALITYSCAN_UNWRAP_XML=%h/realityscan/unwrap-optimal.xml
       # Der EIGENE Bildschirm (15.10.2026): ein Xvfb nur für RealityScan, nie der des Owners.
       Environment=AIIMAGING_REALITYSCAN_DISPLAY=:87
       # Fassung 2 (Eckfarben) stattdessen: die PLY-Exportdatei und KEINE Abwicklungsdatei
       # Environment=AIIMAGING_REALITYSCAN_EXPORT_XML=%h/realityscan/export-ply-farben.xml
       # nur, wenn RealityScan.exe nicht am dokumentierten Ort liegt:
       # (mit Anführungszeichen, weil der Pfad Leerzeichen trägt)
       # Environment="AIIMAGING_REALITYSCAN_EXE=/opt/realityscan/support/realityscan/drive_c/Program Files/Epic Games/RealityScan/RealityScan.exe"

   **Der Starter ist das `wine` des Pakets**, nicht `realityscan-cli`: Das startet in 2.2 nicht
   («winewrapper: cannot execute RealityScan.exe», 278 F1). Beide nehmen `<exe> <befehle…>`.
   Abschalten heisst: die Variable `AIIMAGING_REALITYSCAN` entfernen.

**Der eigene Bildschirm (Pflicht für neue Läufe, 15.10.2026).** RealityScan 2.2 startet unter dem
`wine` des Pakets nur mit erreichbarem X-Server — **auch mit `-headless`** (ohne Bildschirm
`0x887a0001`, mit totem `0x887a0004`; berichtigt 278 F2). Am Heim-PC läuft dafür ein eigenes Xvfb
(`kosmo-xvfb87.service`, `:87`, 1920×1080×24), der Abholer hängt daran (`Requires`/`After`).
Die Brücke nimmt **nur** `AIIMAGING_REALITYSCAN_DISPLAY` und nie das geerbte `DISPLAY`: Ein
Dienst mit der Umgebung des angemeldeten Owners hätte RealityScan sonst auf dessen Bildschirm
gestartet. Sie entfernt dazu `WAYLAND_DISPLAY` und `XAUTHORITY` aus der Umgebung des Laufs.
Fehlt der Bildschirm, sagt es `einrichtung()` (`display_grund`), ein Netz aus dem Speicher geht
weiter, und ein **neuer** Lauf bricht mit diesem Satz ab — die Splat-Brücke übernimmt **mit Grund**.

Optional: `AIIMAGING_REALITYSCAN_SPEICHER` — wo die Netze abgelegt werden (sonst
`~/.cache/aiimaging/realityscan-netz`).

## Was Visbox dann tut

`seams.kontext_vorbereiten` (Abholer und Kette, dieselbe Entscheidung) nimmt für einen Splat:

1. **RealityScan**, wenn eingeschaltet und eingerichtet, eine COLMAP-Aufnahme zum Splat gefunden
   ist (wie beim offenen Weg: Parameter, `AIIMAGING_SPLAT_AUFNAHME`, neben dem Splat) **und** alle
   Fotos da sind — nach der Konvention `<sparse/0>/../../images`, also
   `<lauf>/images/{front,back,left,right}/NNNN.jpg`, die Namen wie in der Aufnahme;
2. sonst den **offenen Weg** (gsplat + Open3D);
3. sonst die **Kugeln**.

Der Lauf (`realityscan.realityscan_zu_netz`):

* schreibt die Aufnahme als COLMAP-3-Text (`cameras.txt`, `images.txt`, `points3D.txt`; je Bild
  seine eigene Pose, das Rig fällt weg) in einen Arbeitsordner;
  Die **Bildnamen zeigen relativ zum Textordner** auf die Fotos (`../../…/images/back/0031.jpg`):
  RealityScan löst sie gegen den Ordner der `images.txt` auf und wartet trotz `-headless` auf einen
  Dialog, wenn eines fehlt (278 F3). Ohne 3D-Punkte startet nichts — daran hinge es ebenso (F4);
* ruft, **mit Textur** (Fassung 3):
  `<wine> "<exe>" -headless -stdConsole -newScene -loadColmap <images.txt>
  -selectMaximalComponent -setReconstructionRegionAuto -calculateNormalModel -simplify 1000000
  -set MvsGeometryTexturingDoHdr=false -set txtImageDownscaleTexture=1
  -unwrap <unwrap-optimal.xml> -calculateTexture
  -exportSelectedModel <export/netz.obj> <export-obj-textur.xml> -quit` —
  `-simplify` wählt das neue Modell, `-unwrap` und `-calculateTexture` arbeiten am gewählten (im
  Handversuch der HomeStation war es `-selectModel`; Reihenfolge je Modell: wählen → `-unwrap
  <datei>` → `-calculateTexture` → `-exportSelectedModel <obj> <datei>`). **1 Mio. Dreiecke**,
  gemessen: 500 000 bis 1 Mio. tragen die Textur, 3 Mio. bringen nichts. Zeiten der HomeStation (RTX
  5090, Netz 1 Mio.): vereinfachen 25–41 s, texturieren ~100 s, schreiben ~52 s, GPU höchstens 2.1 GB
  — rund 2.5 min mehr als mit Eckfarben. Die Bereinigung (reines Python) brauchte hier für ein
  synthetisches OBJ mit 1 Mio. Dreiecken ~22 s und ~270 MB.

  **Ohne Abwicklungsdatei** (Fassung 2, Eckfarben): `<wine> "<exe>" -headless -stdConsole -newScene
  -loadColmap <images.txt> -selectMaximalComponent -setReconstructionRegionAuto
  -calculateNormalModel -simplify 500000 -calculateVertexColors -exportSelectedModel <export.ply>
  <export.xml> -quit`.

  In beiden Fällen alle Pfade als
  `Z:\…` (Wine bildet `Z:` auf `/` ab), als Liste ohne Shell, Frist 4 h, **in eigener
  Prozessgruppe**: Nach der Frist wird die ganze Gruppe beendet (erst freundlich, nach 10 s hart),
  sonst bliebe `RealityScan.exe` als Waise stehen (F9). Gemessen 278: kein `-addFolder` (Bilder
  doppelt), kein `-align` (eigene Komponenten), `-exportSelectedModel` statt `"Model 1"`
  (unvereinfacht), `-stdConsole` für die Fassung;
* **bereinigt** den Export: Der **Deckel** fällt weg — Dreiecke mit einer Kante über 2.5 % der
  Netzdiagonale (gemessen in M3, `auf-20261014-280`), mit denen RealityScan Bereiche ohne Fotos
  schliesst (am Heim-PC 59 % der Fläche). Beim **OBJ** werden danach Ecken und Texturkoordinaten neu
  nummeriert (jede Fläche zeigt auf dieselben Ecken **und** dieselbe Stelle der Textur wie vorher),
  MTL und Bilder heissen `netz.mtl` und `netz_textur_<k>.png`, jeder Bildverweis ist ein Dateiname
  ohne Pfad, Kommentare fallen weg (Regel 3), und die Prüfsumme der Bilder steht als Kommentar im
  OBJ (so hängt auch der Speicher des Multipass an der Textur). Bei der **PLY**: Farben von `float`
  auf `uchar` (Blender 5.2 macht `float` schwarz, F7);
* prüft den Export: OBJ mit Flächen, Texturkoordinaten, MTL und lesbaren PNG — bzw. PLY mit Flächen
  (`element face`) **und** Farbe je Ecke — sonst Fehler mit Grund;
* prüft die **Lage**: Liegt das Netz bei den COLMAP-Punkten der Aufnahme (mindestens die Hälfte
  hat eine Ecke in der Nähe, Zelle 1 % der Diagonale; Diagonale höchstens zweimal grösser oder
  kleiner) und bei den dichten Punkten des Splats? Sonst wird es **nicht** benutzt (Grund `lage`)
  — RealityScan könnte neu gelagert oder skaliert haben;
* legt das Netz ab nach dem **Inhalt** von Aufnahme, Fotos (Namen und Grössen), Export- und
  Abwicklungsdatei sowie Fassung, Art (Textur/Eckfarben) und Dreieckszahl — beim OBJ **alle** Dateien
  in einem Ordner; ein Treffer verlangt jede unverändert. Ein zweiter Auftrag mit derselben Aufnahme
  rechnet nicht neu. Ein
  gescheiterter Lauf wird nicht abgelegt (der nächste Auftrag versucht es wieder), ein Export ohne
  Farbe schon (er hängt an der Exportdatei — eine neue ergibt einen neuen Lauf);
* schreibt einen Bericht **ohne Pfade**: Zeiten, Ecken, Dreiecke, Hüllbox, Art, je Datei Name, Grösse
  und sha256 (`netz.dateien`, `netz.sha256_alle`), die Texturen mit Breite und Höhe, Fassung des
  Programms (wenn die Ausgabe sie nennt), die letzten 2000 Zeichen der Ausgabe mit ersetzten Pfaden.

**In Blender** (`runners/blender_depth_stage._kontext_netz_laden`) wird das OBJ mit `wm.obj_import`
geladen (ein Objekt, Achsen als Einheit wie die PLY; in die Welt legt es die Matrix des Splats) und je
Material **Emission mit der Stärke 1 aus der Bildtextur** geschattet — wie schon die Eckfarben: Die
Farbe der Fotos ist das Licht der Aufnahme; beleuchtet (etwa ein Teil Selbstleuchten plus Sonne) sähe
sie doppelt belichtet aus. Im Material-ID-Pass trägt die ganze Umgebung weiter **eine** Kennung, und
`n_materialien` zählt nur die des Modells. Beauty, Tiefe und Maske des Bauwerks rechnen wie vorher.

## Was der Heim-PC geprüft hat, und was offen bleibt

Die zehn Fragen von Fassung 1 hat `auf-20261013-278` (14.10.2026) beantwortet; Fassung 2 der
Brücke setzt die Antworten um (Protokoll 74 §100). Vergleich mit demselben Mass wie 277:
RealityScan 2.2, 960 Bilder, **324 s, 93 % Deckung**, Lage Median 3.7 cm; der offene Weg 9.9 %;
COLMAP-dicht (Poisson) 49–87 % in über einer Stunde für ein Drittel der Bilder. Owner-Entscheid
(14.10.2026): RealityScan ist der Weg fürs Umgebungsnetz, der offene Weg bleibt Rückfall.

Offen (dieselbe Liste in `realityscan.OFFENE_FRAGEN`):

1. Besteht das Bild mit der Umgebung aus RealityScan die QA (Hallenauftrag, M2)?
2. Wie verhält sich `-headless` ohne vorherige Anmeldung im Wine-Profil?
3. Wie viel GPU bleibt mit geladenem Kosmo-Modell (RealityScan belegt rund 25 GB)?
4. Fassung 3: Läuft die ganze Folge in **einem** Aufruf (`-newScene … -simplify -set -unwrap <datei>
   -calculateTexture -exportSelectedModel <obj> <xml> -quit`), und wirken `-set` und `-unwrap` so
   wie im Handversuch nach `-load` eines gespeicherten Projekts?
5. Fassung 3: Schreibt der OBJ-Export trotz `exportMaterials="0"` eine MTL mit `map_Kd`, als Text-OBJ
   (trotz `exportBinary="1"`), mit welchen Dateinamen für MTL und PNG, und mit Verweisen ohne Pfad?
6. Fassung 3: Lädt die Blender-Stufe das bereinigte OBJ in der Lage der PLY von Fassung 2
   (Lageprüfung bestanden, Material-ID-Bild wie vorher), und ist die Textur mit Emission 1 so scharf
   wie im Handversuch?
7. Fassung 3: Wie lange brauchen Bereinigung (~1 Mio. Dreiecke, reines Python) und Blender-Import mit
   3–4 Texturen zu 8K, und wie viel Speicher?

**Zur Hand für die Prüfung:** `python3 -c "from aiimaging import realityscan as r; print(r.einrichtung())"`
sagt, ob alles gefunden ist; `r.realityscan_zu_netz("<lauf>/sparse/0")` rechnet einmal direkt
und gibt den Bericht zurück (ohne Pfade, bis auf `netz_datei` und — derselbe Pfad, der alte Name —
`netz_ply`).
