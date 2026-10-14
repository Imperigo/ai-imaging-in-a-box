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

## Nie für Kunden, nie mitgeliefert

* **Nie über KosmoOrbit für Kunden.** Die EULA (§1.2 c/d) verbietet die Nutzung durch Dritte,
  Hosting und «service bureau». Die drei Variablen unten gehören **nur** in die Umgebung des
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
3. **Die Export-Parameterdatei anlegen** — ohne Oberfläche: den `ModelExport`-Abschnitt aus der
   `.rsinfo` eines Exports in eine leere `.xml` kopieren (Hilfe «Model Export»). Am Heim-PC
   gemessen (278 E1), **so muss sie stehen:**
   * PLY binär (`formatAndVersionUID` «ply 000», `exportBinary=1`), Ecken und Dreiecke an;
   * `exportVertexColors=0` (!) — mit 1 schreibt RealityScan nur die Netzfarbe (weiss);
   * `exportVertexColorSpace=1` (0 liefert linear, viel zu dunkel);
   * `settingsRotation` «90 0 0» — RealityScan vertauscht intern die Achsen; erst diese Drehung
     gibt die Koordinaten der Aufnahme unverändert zurück;
   * Massstab 1 1 1, Anker 0 0 0, `exportCoordinateSystemType=0`.
   *Visbox erfindet diese Datei nicht:* ihr Format ist nicht dokumentiert.
4. **Die drei Variablen für den Dienst setzen** — nicht in der eingecheckten Einheit
   (`betrieb/kosmo-abholer.service` wird gegen die installierte Fassung geprüft), sondern als
   Ergänzung: `systemctl --user edit kosmo-abholer.service` (ebenso für den Heim-Worker, wenn er
   Ketten mit Splat rechnet) und dort

       [Service]
       Environment=AIIMAGING_REALITYSCAN=<das wine des Pakets>
       Environment=AIIMAGING_REALITYSCAN_EXPORT_XML=%h/realityscan/export-ply-farben.xml
       # nur, wenn RealityScan.exe nicht am dokumentierten Ort liegt:
       # (mit Anführungszeichen, weil der Pfad Leerzeichen trägt)
       # Environment="AIIMAGING_REALITYSCAN_EXE=/opt/realityscan/support/realityscan/drive_c/Program Files/Epic Games/RealityScan/RealityScan.exe"

   **Der Starter ist das `wine` des Pakets**, nicht `realityscan-cli`: Das startet in 2.2 nicht
   («winewrapper: cannot execute RealityScan.exe», 278 F1). Beide nehmen `<exe> <befehle…>`.
   Abschalten heisst: die Variable `AIIMAGING_REALITYSCAN` entfernen.

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
* ruft `<wine> "<exe>" -headless -stdConsole -newScene -loadColmap <images.txt>
  -selectMaximalComponent -setReconstructionRegionAuto -calculateNormalModel -simplify 500000
  -calculateVertexColors -exportSelectedModel <export.ply> <export.xml> -quit` — alle Pfade als
  `Z:\…` (Wine bildet `Z:` auf `/` ab), als Liste ohne Shell, Frist 4 h, **in eigener
  Prozessgruppe**: Nach der Frist wird die ganze Gruppe beendet (erst freundlich, nach 10 s hart),
  sonst bliebe `RealityScan.exe` als Waise stehen (F9). Gemessen 278: kein `-addFolder` (Bilder
  doppelt), kein `-align` (eigene Komponenten), `-exportSelectedModel` statt `"Model 1"`
  (unvereinfacht), `-stdConsole` für die Fassung;
* **bereinigt** den Export: Farben von `float` auf `uchar` (Blender 5.2 macht `float` schwarz,
  F7), und der **Deckel** fällt weg — Dreiecke mit einer Kante über 5 % der Netzdiagonale, mit
  denen RealityScan Bereiche ohne Fotos schliesst (am Heim-PC 59 % der Fläche);
* prüft den Export: PLY mit Flächen (`element face`) **und** Farbe je Ecke — sonst Fehler mit Grund;
* prüft die **Lage**: Liegt das Netz bei den COLMAP-Punkten der Aufnahme (mindestens die Hälfte
  hat eine Ecke in der Nähe, Zelle 1 % der Diagonale; Diagonale höchstens zweimal grösser oder
  kleiner) und bei den dichten Punkten des Splats? Sonst wird es **nicht** benutzt (Grund `lage`)
  — RealityScan könnte neu gelagert oder skaliert haben;
* legt das Netz ab nach dem **Inhalt** von Aufnahme, Fotos (Namen und Grössen) und
  Export-Parameterdatei. Ein zweiter Auftrag mit derselben Aufnahme rechnet nicht neu. Ein
  gescheiterter Lauf wird nicht abgelegt (der nächste Auftrag versucht es wieder), ein Export ohne
  Farbe schon (er hängt an der Exportdatei — eine neue ergibt einen neuen Lauf);
* schreibt einen Bericht **ohne Pfade**: Zeiten, Ecken, Dreiecke, Hüllbox, Fassung des Programms
  (wenn die Ausgabe sie nennt), die letzten 2000 Zeichen der Ausgabe mit ersetzten Pfaden.

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

**Zur Hand für die Prüfung:** `python3 -c "from aiimaging import realityscan as r; print(r.einrichtung())"`
sagt, ob alles gefunden ist; `r.realityscan_zu_netz("<lauf>/sparse/0")` rechnet einmal direkt
und gibt den Bericht zurück (ohne Pfade, bis auf `netz_ply`).
