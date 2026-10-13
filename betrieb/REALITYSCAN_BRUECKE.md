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
   1250 USD je Platz und Jahr. **Wie die Aktivierung ohne Oberfläche geht, ist offen** (Frage 2
   unten) — vermutlich einmal das Programm mit Oberfläche starten und anmelden.
3. **Die Export-Parameterdatei anlegen** — einmal im Programm (auch unter Wine): ein Netz
   exportieren als **PLY**, mit **Farben je Ecke** (red/green/blue), **Koordinaten unverändert**
   (kein Verschieben, kein Massstab, keine Achsendrehung), und die Einstellungen als XML speichern.
   Laut Doku steht derselbe Inhalt auch im `ModelExport`-Abschnitt einer `.rsinfo`. *Visbox
   erfindet diese Datei nicht:* ihr Format ist nicht dokumentiert.
4. **Die drei Variablen für den Dienst setzen** — nicht in der eingecheckten Einheit
   (`betrieb/kosmo-abholer.service` wird gegen die installierte Fassung geprüft), sondern als
   Ergänzung: `systemctl --user edit kosmo-abholer.service` (ebenso für den Heim-Worker, wenn er
   Ketten mit Splat rechnet) und dort

       [Service]
       Environment=AIIMAGING_REALITYSCAN=/opt/realityscan/bin/realityscan-cli
       Environment=AIIMAGING_REALITYSCAN_EXPORT_XML=%h/realityscan/export-ply-farben.xml
       # nur, wenn RealityScan.exe nicht am dokumentierten Ort liegt:
       # (mit Anführungszeichen, weil der Pfad Leerzeichen trägt)
       # Environment="AIIMAGING_REALITYSCAN_EXE=/opt/realityscan/support/realityscan/drive_c/Program Files/Epic Games/RealityScan/RealityScan.exe"

   Der Pfad zu `realityscan-cli` ist der, den die Installation wirklich angelegt hat (Frage 1).
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
* ruft `realityscan-cli "<exe>" -headless -newScene -set appIncSubdirs=true -addFolder <images>
  -importColmap <images.txt> -align -selectMaximalComponent -setReconstructionRegionAuto
  -calculateNormalModel -simplify 500000 -calculateVertexColors -exportModel "Model 1" <netz.ply>
  <export.xml> -quit` — alle Pfade als `Z:\…` (Wine bildet `Z:` auf `/` ab), als Liste ohne
  Shell, Frist 4 h (gesetzt);
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

## Was der Heim-PC prüft (offene Fragen)

Jede dieser Fragen ist **nicht** aus der Doku zu beantworten; die Brücke ist darum gesetzt, nicht
gemessen. Dieselbe Liste steht in `realityscan.OFFENE_FRAGEN`.

1. Wo liegt `realityscan-cli` nach der Installation (z. B. `/opt/realityscan/bin/realityscan-cli`
   oder im `PATH`), und reicht es die Argumente einzeln an Wine weiter (Pfade mit Leerzeichen,
   ohne Shell)?
2. Wie wird die Epic-Lizenz headless aktiviert? Läuft `-headless` ohne angemeldete Sitzung, oder
   verlangt der erste Start eine Anmeldung in der Oberfläche?
3. Lädt `-importColmap` die Bilder selbst, oder braucht es vorher `-addFolder <images>` mit
   `appIncSubdirs=true` (heute gesetzt)? Passen die Bildnamen mit Unterordner (`back/0031.jpg`)
   zu den geladenen Bildern, und gegen welchen Ordner löst RealityScan sie auf (Ordner der
   `images.txt` oder der Bilder)? Zum Vergleich: `realityscan_zu_netz(…, bilder_weg="importColmap")`.
4. Welche der drei Textdateien erwartet `-importColmap` (heute `images.txt`), und braucht es
   `points3D.txt` mit Spuren (heute ja) oder genügt sie leer (`mit_punkten=False`)?
5. Behält RealityScan nach `-importColmap` und `-align` Lage und Massstab der Aufnahme, oder
   lagert es neu? (Die Lageprüfung fängt es ab; dann bleibt der offene Weg.) Gibt es eine
   Einstellung, die die importierten Posen festhält?
6. Legt `-simplify` ein neues Modell an? Wenn ja: Wie heisst es («Model 2»?), und exportiert
   `-exportModel "Model 1"` dann das unvereinfachte Netz (Bericht `netz.vereinfacht`)?
7. Welche Einstellungen braucht die Export-Parameterdatei für PLY mit Eckpunktfarben und
   unveränderten Koordinaten? Schreibt der Export binär oder als Text (beides wird gelesen)?
8. Welche Fassung meldet das Programm in seiner Ausgabe (Zeile mit «RealityScan x.y»)?
9. Wie lange dauert der Lauf mit 960 Bildern, und reicht die Frist von 4 h?
10. Format von `-exportRegistration`: Liesse sich daraus eine Ausrichtung (Umeyama-Verfahren) zur
    Aufnahme rechnen, falls RealityScan neu lagert? **Nicht gebaut**, solange das Format
    unbekannt ist.

**Zur Hand für die Prüfung:** `python3 -c "from aiimaging import realityscan as r; print(r.einrichtung())"`
sagt, ob alles gefunden ist; `r.realityscan_zu_netz("<lauf>/sparse/0")` rechnet einmal direkt
und gibt den Bericht zurück (ohne Pfade, bis auf `netz_ply`).
