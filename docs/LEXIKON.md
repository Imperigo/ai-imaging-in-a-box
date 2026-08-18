# Lexikon

Begriffe aus Softwareentwicklung, Lizenzrecht, KI und der Arbeit mit Sprachmodellen —
erklärt für Leser:innen mit Architektur-, nicht Informatikhintergrund.

**Zweck:** Nachschlagewerk während der Entwicklung und Anhang der Vertiefungsarbeit.
**Pflege:** wächst mit dem Projekt. Jeder neue Fachbegriff, der in Code, Commit oder
Gespräch auftaucht, wird hier nachgetragen — siehe `CLAUDE.md`.

> **Lesehinweis:** thematisch gruppiert, weil die Begriffe sich gegenseitig erklären.
> Für alphabetisches Nachschlagen die Suchfunktion benutzen (`Strg+F` / `Cmd+F`).

---

## 1 · Versionsverwaltung und Zusammenarbeit

Werkzeuge, die festhalten, wer wann was geändert hat — vergleichbar mit einem
Planarchiv, das jeden Zwischenstand aufbewahrt statt ihn zu überschreiben.

**Git** — Das Programm, das jede Änderung an den Projektdateien aufzeichnet. Es
speichert nicht nur den aktuellen Stand, sondern die vollständige Geschichte. Jeder
frühere Zustand ist wiederherstellbar.

**Repository (kurz: Repo)** — Der Projektordner samt seiner gesamten Geschichte. Ein
Repo liegt lokal auf dem Rechner und meist zusätzlich auf einem Server (siehe *GitHub*).

**GitHub** — Ein Dienst, der Git-Repositories im Internet hostet. Zusätzlich zur reinen
Ablage bietet er Oberflächen für Diskussion, Überprüfung und Zusammenarbeit.

**Commit** — Ein festgeschriebener Zwischenstand, vergleichbar mit einem datierten
Planstand. Ein Commit umfasst die geänderten Dateien, Zeitpunkt, Urheber:in und eine
Nachricht, die erklärt *warum* geändert wurde. Er ist unveränderlich und wird durch eine
Prüfsumme identifiziert (z. B. `ae2cfa7`).

**Commit-Message** — Die Begründung zu einem Commit. Konvention: die erste Zeile fasst
in einem Satz zusammen, was sich ändert; der Rumpf erklärt die Gründe. Das *Was* steht
ohnehin im Code — die Message trägt das *Warum*.

**Branch (Zweig)** — Ein Entwicklungsstrang, der vom Hauptstand abzweigt. Erlaubt
Arbeit an einer Sache, ohne den funktionierenden Hauptstand anzutasten. Analogie: eine
Variantenstudie auf Transparentpapier über dem Hauptplan.

**main** — Der Hauptzweig, üblicher Name für den massgeblichen Stand. (Früher `master`.)

**Merge (Zusammenführen)** — Das Zurückführen eines Zweigs in einen anderen. Git
verbindet beide Änderungsgeschichten zu einer.

**Merge-Konflikt** — Tritt auf, wenn zwei Zweige *dieselbe Zeile* unterschiedlich
geändert haben. Git kann nicht entscheiden, welche Fassung gilt, und fragt nach.

**Pull Request (PR)** — Der Vorschlag, einen Zweig in einen anderen zu übernehmen. Auf
GitHub eine Seite mit allen Änderungen, Zeile für Zeile, plus Kommentarfunktion. In
Teams der Ort der gegenseitigen Überprüfung. Bei Alleinarbeit oft entbehrlich —
Zusammenführen geht auch direkt.

**Diff** — Die Gegenüberstellung zweier Stände: welche Zeilen kamen hinzu (grün),
welche fielen weg (rot).

**Clone** — Eine vollständige lokale Kopie eines Repositories inklusive Geschichte.

**Push / Pull** — Hochladen der lokalen Commits auf den Server / Herunterladen der
Änderungen anderer.

**Fetch** — Wie *Pull*, aber holt die Änderungen nur ab, ohne sie einzuarbeiten.

**Remote** — Ein Server-Repository, mit dem das lokale abgeglichen wird. Der Standard
heisst `origin`.

**HEAD** — Zeiger auf den gerade ausgecheckten Stand: „wo ich mich in der Geschichte
gerade befinde".

**Checkout** — Wechsel des Arbeitsstands auf einen anderen Zweig oder Commit.

**`.gitignore`** — Liste von Dateien, die Git bewusst *nicht* aufzeichnen soll:
Modellgewichte, Renderausgaben, Passwörter, temporäre Dateien. In diesem Projekt
zusätzlich Schutzmechanismus für Regel 3 (keine echten Projektdaten im Repo).

**Fork** — Eine eigenständige Kopie eines fremden Repositories unter eigenem Konto.

**Issue** — Ein Eintrag in der Aufgaben-/Fehlerliste eines Repositories.

---

## 2 · Lizenzen und Recht

Der für dieses Projekt heikelste Bereich. Softwarelizenzen bestimmen, was mit fremdem
Code gebaut und ob das Ergebnis verkauft werden darf. Sie sind nicht Formsache, sondern
Entwurfsbeschränkung: Sie schliessen Bausteine aus, bevor die Technik überhaupt zur
Sprache kommt.

**Open Source** — Software, deren Quelltext einsehbar und nutzbar ist. Sagt für sich
genommen **nichts** über kommerzielle Verwertbarkeit — dafür sind die konkreten
Bedingungen entscheidend.

**Permissive Lizenz** — Erlaubt praktisch alles, verlangt im Wesentlichen nur
Namensnennung. Der Code darf in geschlossene, verkaufte Produkte einfliessen. Beispiele:
MIT, Apache-2.0, BSD.

**MIT-Lizenz** — Die kürzeste verbreitete permissive Lizenz. Bedingung: Copyright-Hinweis
beibehalten.

**Apache-2.0** — Permissive Lizenz, ausführlicher als MIT. *In diesem Projekt die Lizenz
des eigenen Codes.*

**Was sie erlaubt** — praktisch alles: benutzen, verändern, weitergeben, verkaufen, in
geschlossene Produkte einbauen. Ohne Rückfrage, ohne Gebühr, ohne Pflicht, eigene
Änderungen offenzulegen. Auch kommerziell.

**Was sie verlangt** — vier Dinge, wenn der Code weitergegeben wird:

1. Eine Kopie der Lizenz beilegen.
2. Copyright-Hinweise stehen lassen.
3. Veränderte Dateien als verändert kennzeichnen.
4. Eine vorhandene `NOTICE`-Datei mitgeben.

**Die Patentklausel** — der eigentliche Unterschied zu MIT. Wer zu Apache-2.0-Code
beiträgt, erteilt allen Nutzern zugleich eine Lizenz an seinen einschlägigen Patenten.
Bei MIT ist das ungeregelt: Man erhält das Urheberrecht am Code, aber niemand sichert
zu, dass an dessen Verfahren keine Patente hängen.

**Die Verteidigungsklausel** — die Kehrseite: Wer jemanden wegen eines Patents an diesem
Werk verklagt, verliert damit die eigene Patentlizenz daran. Eine Selbstentschärfung, die
Apache-2.0 im professionellen Umfeld zur bevorzugten permissiven Lizenz gemacht hat.

**Was sie nicht gewährt** — Namensrechte. Der Code darf verwendet werden, der
Projektname nicht als eigener.

**Verträglichkeit** — Apache-2.0-Code darf in GPL-3.0-Projekte einfliessen, aber **nicht**
in GPL-2.0-only-Projekte; die Patentklausel verträgt sich mit deren Bedingungen nicht.
Diese Einschränkung wirkt nur in diese eine Richtung: Apache-lizenzierter Code *benutzt*
werden — etwa GPL-Programme als Subprozess aufrufen — ist davon nicht berührt.

**BSD-Lizenz** — Permissiv, MIT sehr ähnlich, in mehreren Varianten (2-Clause, 3-Clause).

**Copyleft** — Das Gegenprinzip zu permissiv: Wer den Code nutzt, muss das Ergebnis
unter denselben Bedingungen weitergeben. Der Zweck ist, dass freie Software frei bleibt.
Umgangssprachlich „ansteckend".

**GPL (GNU General Public License)** — Starkes Copyleft. Wird GPL-Code Teil eines
Produkts, muss das **gesamte** Produkt GPL werden: Quelltext offen, Weitergabe frei.
*In diesem Projekt ausgeschlossen (Regel 1) — betrifft unter anderem ComfyUI und Blender.*

**AGPL (GNU Affero GPL)** — GPL mit zusätzlicher Netzwerkklausel. Bei GPL greift das
Copyleft erst beim Ausliefern von Software. Die AGPL erweitert das auf den *Betrieb als
Dienst*: Wer AGPL-Code hinter einer Weboberfläche laufen lässt, muss den Quelltext
offenlegen, obwohl er nichts verteilt hat. Für Pipelines besonders heikel.

**LGPL (GNU Lesser GPL)** — Abgeschwächtes Copyleft. Steckt nicht an, solange die
Bibliothek nur *benutzt* und nicht *verändert* wird. Zentrale Auflage: Nutzer müssen die
Bibliothek durch eine eigene Fassung ersetzen können. Wird die Bibliothek selbst geändert,
sind diese Änderungen offenzulegen — der übrige eigene Code bleibt unberührt.
*In diesem Projekt: der Grenzfall bei IfcOpenShell.*

**MPL-2.0 (Mozilla Public License)** — Copyleft auf **Dateiebene**. Nur veränderte
Dateien der Bibliothek müssen offen bleiben; der eigene Code in eigenen Dateien nicht.
Ein Mittelweg, mit permissiven Projekten gut verträglich.

**Dual License** — Dasselbe Werk unter zwei Lizenzen. Typisches Muster: kostenlos unter
Copyleft, gegen Geld unter kommerzieller Lizenz. *Beispiel: CGAL.*

**OpenRAIL++-M** — Lizenz von Stable Diffusion XL. Erlaubt kommerzielle Nutzung, knüpft
sie aber an Nutzungsauflagen: bestimmte Anwendungen sind untersagt, und die Auflagen sind
weiterzugeben. Nicht permissiv im Sinn von Regel 1, aber auch kein Copyleft.

**Stability Community License** — Lizenz von SD3.5. Frei nutzbar unterhalb einer
Umsatzschwelle (1 Mio USD), darüber kostenpflichtig. Kommerziell nutzbar, aber nicht
bedingungslos — eine Einschränkung, die man beim Wachsen bemerkt.

**Non-Commercial (NC)** — Nutzung nur ohne Erwerbszweck. Trotz offenem Zugang **kein**
Open Source im Sinne der OSI. *Beispiel: FLUX.1-dev.*

**OSI (Open Source Initiative)** — Organisation, die anerkannte Open-Source-Lizenzen
führt. „Nicht OSI-konform" heisst: offen zugänglich, aber mit Auflagen, die echte
Weiterverwendung einschränken.

**Derivative Work (abgeleitetes Werk)** — Ein Werk, das fremden Code so einbindet, dass
beide ein Ganzes bilden. Löst das Copyleft aus. Die entscheidende Frage jeder
Lizenzdiskussion.

**Aggregation (Lizenzrecht)** — Das Gegenteil: zwei eigenständige Programme, die
lediglich nebeneinander liegen oder sich Daten reichen. Löst **kein** Copyleft aus.
*Nicht zu verwechseln mit* **Aggregation (Messwerte)** *in Abschnitt 6 — gleiches Wort,
anderer Sachverhalt.*

**Linking (Binden)** — Das technische Verbinden von Programmteilen zu einer Einheit.
*Statisch* = fest einkompiliert; *dynamisch* = zur Laufzeit hinzugeladen. Der
Unterschied ist lizenzrechtlich erheblich: Statisches Binden gilt als abgeleitetes Werk,
dynamisches ist umstritten.

**Prozessgrenze** — Die in diesem Projekt tragende Konstruktion. Läuft fremder Code als
**eigenständiges Programm**, das man von aussen aufruft und mit dem man nur Dateien
austauscht, entsteht kein gemeinsames Werk, sondern eine Aggregation. Deshalb darf
Blender (GPL) benutzt, aber nicht eingebaut werden.
*Bauliche Analogie: der Unterschied zwischen einem Anbau, der Fundament und Wände des
Bestands mitbenutzt und deshalb unter dessen Baubewilligung fällt, und einem
Nebengebäude, das über einen Weg erschlossen ist und für sich steht.*

**NOTICE** — Datei im Repo, die alle fremden Bestandteile mit ihrer Lizenz aufführt.
Bei Apache-2.0 vorgesehen und die übliche Form, GPL-Beigaben sauber zu deklarieren.

**Modellgewichte-Lizenz** — Die Lizenz *trainierter Modelle* ist unabhängig von der des
Codes. Ein Apache-lizenziertes Programm kann Gewichte laden, deren Lizenz kommerzielle
Nutzung untersagt. Beide sind getrennt zu prüfen.

---

## 3 · Programmieren, allgemein

**Quelltext / Code** — Der lesbare Text, aus dem ein Programm besteht.

**Skript** — Ein kurzes Programm für eine bestimmte Aufgabe, meist ohne Oberfläche und
von oben nach unten ausgeführt.

**Bibliothek (Library)** — Eine Sammlung fertiger Funktionen, die man in eigenen
Programmen verwendet. Man ruft sie auf — sie gibt den Ablauf nicht vor.
*In diesem Projekt: der Kern soll eine Bibliothek sein (Regel 4).*

**Framework** — Wie eine Bibliothek, aber mit umgekehrtem Verhältnis: Das Framework gibt
die Struktur vor und ruft den eigenen Code auf. Mehr Vorleistung, weniger Freiheit.

**API (Application Programming Interface)** — Die vereinbarte Schnittstelle, über die
Programme miteinander sprechen: welche Aufrufe es gibt, welche Angaben sie erwarten,
was zurückkommt. Nicht die Umsetzung, sondern der Vertrag darüber.

**CLI (Command Line Interface)** — Bedienung über eingetippte Befehle im Terminal statt
über Fenster und Knöpfe. Für Automatisierung unverzichtbar, weil ein Befehl
wiederholbar und skriptbar ist.

**GUI (Graphical User Interface)** — Die grafische Oberfläche.

**Headless** — Ein Programm ohne grafische Oberfläche betreiben. *In diesem Projekt:
`blender --background` rendert, ohne dass ein Fenster aufgeht.*

**Funktion** — Ein benannter, wiederverwendbarer Arbeitsschritt: nimmt Werte entgegen,
liefert ein Ergebnis.

**Parameter / Argument** — Die Angaben, die eine Funktion entgegennimmt (*Parameter* =
die vorgesehene Stelle, *Argument* = der konkret übergebene Wert).

**Rückgabewert** — Das Ergebnis, das eine Funktion zurückliefert.

**Klasse / Objekt** — Bauplan und daraus erzeugtes Einzelstück. Eine Klasse `Kamera`
beschreibt, was jede Kamera hat; ein Objekt ist eine konkrete Kamera mit konkreten Werten.

**Modul** — Eine einzelne Quelltextdatei, die andere einbinden können.

**Paket (Package)** — Eine Sammlung von Modulen, als Einheit installierbar.

**Import** — Das Einbinden eines Moduls in den eigenen Code.

**pyproject.toml** — Die zentrale Beschreibungsdatei eines Python-Projekts: Name,
Version, Lizenz, Abhängigkeiten, Werkzeugeinstellungen. Ersetzt die früher üblichen
`setup.py`/`setup.cfg`.

**src-Layout** — Konvention, den eigenen Code unter `src/` abzulegen statt direkt im
Projektwurzelverzeichnis. Vorteil: Tests laufen zwangsläufig gegen das *installierte*
Paket und nicht versehentlich gegen die Dateien daneben — Verpackungsfehler fallen so
sofort auf statt beim Nutzer.

**Optionale Abhängigkeitsgruppe** — Zusätzliche Pakete, die nur für bestimmte Zwecke
installiert werden, etwa `dev` für Testwerkzeuge. Sie gehören nicht zur Laufzeit des
Produkts. *In diesem Projekt hat der Kern **null** Laufzeitabhängigkeiten — alles
Schwere liegt jenseits der Prozessgrenze in eigenen Environments.*

**SPDX** — Ein standardisiertes Kürzelverzeichnis für Lizenzen (`Apache-2.0`, `MIT`,
`GPL-3.0-or-later`). Erlaubt es, Lizenzen maschinenlesbar anzugeben, statt sie in Prosa
zu umschreiben.

**Abhängigkeit (Dependency)** — Fremde Software, die das eigene Programm zum Laufen
braucht. Jede Abhängigkeit bringt ihre Lizenz mit — deshalb ist die Abhängigkeitsliste
zugleich eine Lizenzliste.

**pip** — Das Installationswerkzeug für Python-Pakete.

**PyPI (Python Package Index)** — Das zentrale Verzeichnis, aus dem `pip` lädt.

**Wheel** — Ein vorkompiliertes Python-Paket. Praktisch, weil nichts übersetzt werden
muss — aber undurchsichtig, weil fertige Binärteile mitgeliefert werden, deren Herkunft
man nicht sieht. *Genau daraus entstand die CGAL-Frage in diesem Projekt.*

**venv (virtuelle Umgebung)** — Ein abgeschotteter Ordner mit eigener Python-Installation
und eigenen Paketen. Verhindert, dass Projekte sich gegenseitig stören.
*In diesem Projekt zusätzlich als Lizenzgrenze eingesetzt: LGPL-/GPL-behaftete
Bibliotheken bekommen ein eigenes venv und werden nur als Subprozess aufgerufen.*

**Prozess** — Ein laufendes Programm mit eigenem Speicher. Zwei Prozesse können sich
nicht in die Quere kommen — die Grundlage der Prozessgrenze.

**Subprozess** — Ein Programm, das ein anderes Programm startet und dessen Ergebnis
abwartet. Praktisch dasselbe, als würde man den Befehl selbst ins Terminal tippen —
nur tut es das eigene Programm. *In diesem Projekt die Form, in der Blender und
IfcOpenShell aufgerufen werden.*

**IPC (Interprozesskommunikation)** — Oberbegriff für alle Arten, wie getrennte Programme
Daten austauschen: über Dateien, über die Standardausgabe, über Netzwerkverbindungen.
Die einfachste Form — eine Datei schreiben, die das andere Programm liest — genügt für
dieses Projekt und ist deshalb die gewählte.

**stdout / stderr (Standardausgabe / Standardfehler)** — Die beiden Textkanäle, über die
ein Programm im Terminal ausgibt. Getrennt, damit sich Ergebnisse und Fehlermeldungen
nicht vermischen und einzeln weiterverarbeiten lassen.

**Exit-Code** — Die Zahl, mit der sich ein Programm verabschiedet. `0` heisst „hat
geklappt", alles andere signalisiert einen Fehler. So erfährt das aufrufende Programm,
ob der Subprozess erfolgreich war.

**stdio (Standard-Ein-/Ausgabe)** — Der einfachste Weg, wie zwei Programme sprechen: Das
eine schreibt in seine Ausgabe, das andere liest sie als Eingabe. Ohne Netzwerk, ohne
Port. *MCP-Server im ArchitekturKosmos laufen über stdio — Kosmo startet sie und
kommuniziert über diese beiden Kanäle.*

**Pfad-Sandbox** — Beschränkung, in welche Verzeichnisse ein Programm schreiben darf.
*Im ArchitekturKosmos müssen Schreibziele unter `$HOME` oder `/tmp` liegen; ein Werkzeug
kann so nicht versehentlich oder böswillig ins System schreiben.*

**write-gated** — Gegenstück zu read-only: Ein Werkzeug, das schreibt, und darum eine
ausdrückliche Freigabe braucht. *`kosmodraw_export_ifc` ist write-gated, die lesenden
Werkzeuge derselben Lane nicht.*

**Runner** — Ein kleines eigenständiges Skript, das genau eine Aufgabe in einem eigenen
venv erledigt und über Dateien antwortet. Die praktische Bauform der Prozessgrenze.
*Beispiele: `glb_export_runner.py`, `export_ifc_runner.py`.*

**Protokoll** — Eine Vereinbarung darüber, in welcher Form zwei Programme miteinander
sprechen: welche Nachrichten es gibt, in welcher Reihenfolge, in welchem Format. Nötig,
wenn die Gegenseite nicht im Voraus weiss, was sie erwartet — überflüssig, wenn ein
schlichter Aufruf genügt. *MCP ist ein Protokoll, ein Subprozessaufruf braucht keines.*

**Umgebungsvariable** — Eine Einstellung, die dem Programm von aussen mitgegeben wird —
üblicher Ort für Pfade und Geheimnisse, die nicht in den Code gehören.

**JSON** — Ein schlichtes Textformat für strukturierte Daten. Für Mensch und Maschine
lesbar, deshalb das übliche Austauschformat zwischen Prozessen.

**Schema** — Die formale Beschreibung, wie eine Datenstruktur auszusehen hat: welche
Felder verpflichtend sind, welchen Typ sie haben. Macht Verträge zwischen Programmteilen
prüfbar.

**Parsing** — Das Zerlegen einer Datei in eine für das Programm nutzbare Struktur.

**Serialisierung** — Die Gegenrichtung: eine Datenstruktur in eine speicherbare Form
bringen.

**Pfad** — Die Adresse einer Datei im Dateisystem. *Absolut* = ab Wurzel,
*relativ* = ausgehend vom aktuellen Ordner.

**Terminal / Shell** — Das Fenster, in dem Befehle eingetippt werden, und das Programm,
das sie ausführt.

**Frontend-Framework (React, Vue, Svelte)** — Baukästen für Bedienoberflächen im Browser.
*KosmoOrbit verwendet React.*

**TypeScript** — JavaScript mit Typangaben. Der Übersetzer prüft vor dem Ausführen, ob
Datentypen zusammenpassen — Fehler fallen beim Bauen auf statt beim Benutzen.

**Tauri** — Baukasten für Desktop-Anwendungen, deren Oberfläche aus Web-Technik besteht,
deren Rahmen aber ein kompaktes Rust-Programm ist. Schlanker als die Alternative Electron.
*KosmoOrbit ist eine Tauri-Anwendung.*

**REST / Endpoint** — Verbreitete Art, Web-Schnittstellen zu bauen: Jede Fähigkeit hat
eine eigene Adresse (den *Endpoint*), die per HTTP angesprochen wird.

**SSE (Server-Sent Events)** — Technik, mit der ein Server fortlaufend Daten an den
Client nachliefert, ohne dass dieser wiederholt nachfragt. *Grundlage dafür, dass
Kosmo-Antworten wortweise erscheinen statt am Stück.*

**Sidecar** — Ein Hilfsprogramm, das mit der Hauptanwendung ausgeliefert wird und
daneben läuft. Die übliche Form, ein Python-Programm in eine Desktop-Anwendung
einzubinden, ohne es in sie hineinzubauen.


---

## 4 · Qualität und Absicherung

**Test** — Code, der anderen Code überprüft. Ein Test beschreibt eine Erwartung und
schlägt Alarm, wenn sie verletzt wird.

**Unit-Test** — Prüft einen einzelnen, kleinen Baustein isoliert.

**Integrationstest** — Prüft das Zusammenspiel mehrerer Bausteine.

**Regressionstest** — Ein Test, der einen bereits behobenen Fehler festhält, damit er
nicht unbemerkt zurückkehrt. Das eigentliche Sicherheitsnetz eines wachsenden Projekts.

**Testabdeckung (Coverage)** — Wieviel Prozent des Codes von Tests durchlaufen wird.
Ein grober Anhaltspunkt, keine Qualitätsgarantie.

**CI (Continuous Integration)** — Automatischer Durchlauf aller Tests bei jeder Änderung,
auf einem Server statt auf dem eigenen Rechner.

**Linter** — Ein Programm, das Code auf Stil- und Flüchtigkeitsfehler prüft, ohne ihn
auszuführen.

**Debugging** — Die Suche nach der Ursache eines Fehlverhaltens.

**Log** — Fortlaufende Aufzeichnung dessen, was ein Programm während des Laufs tut.
Bei langen Renderläufen oft die einzige Möglichkeit nachzuvollziehen, was geschah.

**Exception (Ausnahme)** — Ein Fehler, der das Programm an der betreffenden Stelle
abbricht — falls er nicht abgefangen wird.

**Attrappe (Mock)** — Ein Ersatzstück, das im Test die Stelle eines echten Bausteins
einnimmt und vorhersehbar antwortet. *Erlaubt, den Stil-Score zu prüfen, obwohl das
Einbettungsmodell hier gar nicht vorhanden ist.*

**Vakuöser Test** — Ein Test, der besteht, weil die geprüfte Lage nie eintritt — etwa die
Prüfung „FLUX erscheint nicht in der Auswahl", wenn FLUX gar nicht in der Registry steht.
Er sieht grün aus und bewacht nichts. Abhilfe ist eine Gegenprobe, die belegt, dass der
Fall überhaupt vorkommen könnte.

**Registry** — Ein zentrales Verzeichnis, in dem gleichartige Dinge mit ihren Eigenschaften
eingetragen sind. *Hier die Bildmodelle samt Lizenz — dadurch steht die Lizenz im Code und
nicht nur in der Doku.*

**Dataclass / unveränderlich (frozen)** — Eine Python-Klasse, die im Wesentlichen nur Daten
hält. `frozen` heisst: nach dem Anlegen nicht mehr änderbar. *Wichtig überall dort, wo
etwas gehasht oder als Vertrag weitergereicht wird — es soll sich nicht unbemerkt ändern.*

**Stub** — Ein Platzhalter, der die richtige Form hat, aber noch nichts leistet.

**Refactoring** — Umbau des Codes, ohne sein Verhalten zu ändern — nur zugunsten der
Lesbarkeit oder Struktur.

**Technische Schuld** — Metapher für Abkürzungen, die kurzfristig Zeit sparen und
langfristig Zinsen kosten. Nicht per se schlecht, aber buchführungspflichtig.

**Fail-closed** — Entwurfshaltung: Im Zweifel oder bei Störung *nicht* handeln. Für
teure, nicht rückholbare Vorgänge wie GPU-Renderläufe die richtige Grundeinstellung.

**Idempotenz** — Eigenschaft eines Vorgangs, der mehrfach ausgeführt dasselbe Ergebnis
liefert wie einmal ausgeführt. Macht Wiederholung nach Abbruch gefahrlos.

**Race Condition (Wettlaufsituation)** — Fehler, der davon abhängt, welcher von zwei
gleichzeitigen Vorgängen zuerst fertig wird. Schwer zu finden, weil unregelmässig.

---

## 5 · Geometrie, Daten und Rendering

**IFC (Industry Foundation Classes)** — Offenes Austauschformat für Gebäudemodelle.
Enthält nicht nur Geometrie, sondern auch Bedeutung: Dieses Volumen *ist* eine Wand, sie
gehört zu diesem Geschoss, sie besteht aus diesem Material.

**BIM (Building Information Modeling)** — Die Arbeitsweise, für die IFC das
Austauschformat ist.

**Mesh (Netz)** — Geometriedarstellung aus Dreiecken. Was Renderer und Grafikkarten
tatsächlich verarbeiten.

**NURBS** — Mathematisch exakte Kurven- und Flächenbeschreibung, wie sie CAD-Programme
(z. B. Rhino) verwenden. Muss zum Rendern erst in ein Mesh überführt werden
(*Tesselierung*).

**glTF / glb** — Ein schlankes Übertragungsformat für 3D-Geometrie. `glb` ist die
gepackte Einzeldatei-Variante. *In diesem Projekt das Zwischenformat zwischen IFC und
Blender.*

**Bounding Box** — Der kleinste achsparallele Quader, der ein Objekt umschliesst.
Nützlich für schnelle Grössen- und Lageabschätzungen, etwa zur automatischen
Kamerasetzung.

**Up-Achse** — Vereinbarung darüber, welche Achse „oben" bedeutet. IFC und Blender
verwenden Z, glTF verwendet Y. Wird die Umrechnung vergessen, liegt das Gebäude auf der
Seite.

**Georeferenzierung** — Verortung eines Modells in einem Landeskoordinatensystem
(z. B. LV95). Führt zu sehr grossen Zahlenwerten und damit zu Genauigkeitsproblemen —
siehe *Float*.

**Float (Fliesskommazahl)** — Computerdarstellung für Kommazahlen, mit begrenzter
Stellenzahl. `float32` hat rund sieben signifikante Stellen. Bei Koordinaten in
Millionenhöhe bleibt dadurch nur noch Dezimeter-Auflösung — sichtbar als zitternde oder
aufreissende Geometrie.

**STEP / ISO-10303-21** — Das Textformat, in dem eine IFC-Datei tatsächlich vorliegt.
Jede Zeile ist eine nummerierte Entität, die auf andere verweist (`#42= IFCWALL(...)`).
Lesbar, aber weitschweifig — eine kleine IFC hat schnell Hunderte Zeilen.
*In diesem Projekt schreibt `tools/make_test_ifc.py` STEP direkt, ohne Bibliothek — so
braucht das Erzeugen von Testdaten kein GPL-behaftetes Environment.*

**Extrusion / SweptSolid** — Die häufigste Art, wie IFC Geometrie beschreibt: ein
zweidimensionales Profil, entlang einer Richtung in die Höhe gezogen. Eine Wand ist ein
Rechteck, drei Meter hochgezogen. Deshalb steht in einer IFC kein fertiges 3D-Modell,
sondern eine Bauanweisung — jemand muss daraus erst Dreiecke rechnen.

**GUID (Globally Unique Identifier)** — Eine Kennung, die ein Objekt weltweit eindeutig
bezeichnet. IFC schreibt jedem Bauteil eine vor, in einer eigenen 22-Zeichen-Schreibweise.
*In diesem Projekt werden sie für Testdaten bewusst **deterministisch** erzeugt.*

**Determinismus** — Eigenschaft eines Vorgangs, der bei gleicher Eingabe immer exakt
dasselbe Ergebnis liefert. Für Testdaten unverzichtbar: Wären die Kennungen zufällig,
erzeugte jeder Lauf eine andere Datei, und kein Test wäre wiederholbar.

**Testfixture** — Ein fester, bekannter Datensatz, gegen den geprüft wird. *Hier: das
synthetische Gebäude aus vier Wänden und einer Platte, absichtlich asymmetrisch
(8 × 5 × 3 m), damit eine verdrehte Up-Achse auffällt statt zufällig gleich auszusehen.*

**Renderer** — Programm, das aus 3D-Geometrie ein Bild berechnet.

**Cycles** — Der physikalisch basierte Renderer in Blender.

**Raytracing** — Renderverfahren, das Lichtstrahlen einzeln verfolgt. Realistisch, aber
rechenintensiv.

**Pass** — Ein einzelner Bildkanal aus dem Renderer. Neben dem fertigen Bild
(*Beauty-Pass*) etwa Tiefe, Materialzuordnung oder Normalen.

**Rangkorrelation (Spearman)** — Misst, ob zwei Messreihen dieselbe *Reihenfolge* haben,
nicht dieselben Werte. Wert zwischen −1 und 1. *Hier zentral: Eine aus einem Bild
zurückgerechnete Tiefenkarte hat einen anderen Massstab und Nullpunkt als echte Meter —
vergleichbar ist nur die Reihenfolge „was ist näher".*

**Bindung (Tie)** — Gleiche Werte in einer Messreihe. Bei Rangkorrelation bekommen sie
den mittleren Rang. *In Tiefenkarten der Normalfall: Eine Wand parallel zur Bildebene
liefert lauter gleiche Werte. Die verbreitete Kurzformel für Spearman rechnet dort
systematisch falsch.*

**Silhouette** — Die Menge der Bildpunkte, die überhaupt Geometrie tragen (im Unterschied
zum Hintergrund). *Der Teil der Geometrie-QA, der die Halluzination fängt.*

**IoU (Intersection over Union)** — Überlappungsmass zweier Flächen: gemeinsame Fläche
geteilt durch Gesamtfläche. 1 heisst deckungsgleich, 0 heisst keine Überlappung.

**Geometrisches Mittel** — Die Wurzel aus dem Produkt zweier Werte, statt ihres
Durchschnitts. *Hier bewusst gewählt: Es verlangt, dass **beide** Anteile gut sind. Beim
belegten Halluzinationsfall ergibt der Durchschnitt 0,52 — fast bestanden —, das
geometrische Mittel 0,20.*

**Disparität / invertierte Tiefe** — Manche Verfahren geben statt der Entfernung ihren
Kehrwert aus: gross heisst nah statt fern. Wer das nicht beachtet, misst die Tiefe genau
verkehrt herum.

**Beauty-Pass** — Das gewöhnliche gerenderte Bild, im Unterschied zu den Hilfskanälen
(Tiefe, Material-ID). Was man sieht, wenn man „das Rendering" meint.

**Emissions-Shader** — Ein Material, das selbst leuchtet, statt Licht zu empfangen.
*Für den Material-ID-Pass gebraucht: Die Farben sollen die Bauteile bezeichnen, nicht die
Beleuchtung wiedergeben.*

**View-Transform (AgX, Standard)** — Die Umrechnung von berechneten Lichtwerten in
Bildwerte. `AgX` bildet filmisch ab und ist für Ansichtsbilder schöner; `Standard` rechnet
unverfälscht und ist nötig, wenn aus dem Bild wieder Zahlen werden sollen.

**Dithering** — Absichtliches feines Rauschen, das Farbstufen weicher wirken lässt. *Im
Material-ID-Pass schädlich: Es zerfaserte jede Kennfarbe um ±1, aus 5 Farben wurden 19.*

**Denoiser (Entrauscher)** — Nachbearbeitung, die das Bildrauschen eines Raytracers
glättet. Für Ansichtsbilder erwünscht, für Kennfarben schädlich.

**Bittiefe** — Wie viele Abstufungen ein Bildkanal unterscheidet. 8 Bit ergibt 256
Stufen, 16 Bit rund 65 000. *Die normalisierte Tiefenkarte braucht 16 Bit — mit 8 wären
Tiefenunterschiede grob gerastert.*

**Depth-Pass / Tiefenkarte** — Graustufenbild, in dem die Helligkeit die Entfernung zur
Kamera kodiert. *In diesem Projekt der zentrale Baustein: Die Tiefenkarte ist es, die
das KI-Modell an die echte Gebäudeform bindet.*

**Material-ID-Pass** — Bild, in dem jedes Material eine eigene Farbfläche bekommt.
Erlaubt der KI, Bereiche zu unterscheiden.

**Goldener Winkel** — Ein Verteilungstrick: Nimmt man bei jedem Schritt rund 137,5°
(bzw. den Anteil 0,618 eines vollen Kreises), liegen aufeinanderfolgende Werte immer
weit auseinander, egal wie viele es werden. *Wird hier benutzt, um jedem Bauteil im
Material-ID-Pass eine gut unterscheidbare Farbe zu geben — auch beim zwanzigsten.*
In der Natur dasselbe Prinzip wie bei der Blattstellung am Trieb.

**Normalisierung** — Messwerte auf einen festen Bereich umrechnen, meist 0 bis 1.
*Die Tiefenkarte trägt echte Meter; das Bildmodell erwartet Graustufen. Die
Rückrechnungsformel wird darum mitgeliefert, sonst wären die Meter verloren.*

**EXR** — Bildformat mit hoher Genauigkeit, das Werte ausserhalb von 0–255 speichern
kann. Notwendig für Tiefendaten, weil dort echte Meterwerte stehen.

**Compositor** — Nachbearbeitungsstufe im Renderer, in der einzelne Passes verrechnet
und ausgegeben werden.

**Sample** — Ein einzelner Rechenschritt pro Bildpunkt beim Raytracing. Mehr Samples
bedeuten weniger Bildrauschen und längere Rechenzeit.

**Add-on / Plugin** — Eine Erweiterung, die *innerhalb* eines Wirtsprogramms läuft und
dessen Innenleben mitbenutzt. Technisch bequem, lizenzrechtlich heikel: Ein Add-on ist
kein eigenständiges Programm.
*In diesem Projekt ausgeschlossen (Regel 2).*

**bpy** — Blenders Python-Schnittstelle. `import bpy` funktioniert nur *innerhalb* von
Blender und macht den eigenen Code zum Teil von Blender.

---

## 6 · KI-Bildmodelle

**Modell** — Ein trainiertes System, das aus Eingaben Ausgaben erzeugt. Umgangssprachlich
sowohl die Bauform als auch die konkreten trainierten Zahlen.

**Gewichte (Weights)** — Die im Training gelernten Zahlen. Sie *sind* das Können des
Modells. Dateigrössen von mehreren Gigabyte sind üblich.

**Checkpoint** — Eine gespeicherte Fassung der Gewichte.

**`.safetensors`** — Das heute übliche Dateiformat für Gewichte. Sicherer als das
ältere Pickle-Format, weil es keinen ausführbaren Code enthalten kann.

**Parameter (bei Modellen)** — Anzahl der Gewichte, meist in Milliarden („20B"). Grobe
Grössenangabe, kein Qualitätsmass.

**Inferenz** — Die *Benutzung* eines fertigen Modells. Zu unterscheiden vom Training.

**Training** — Das Erzeugen der Gewichte aus Daten. Um Grössenordnungen aufwendiger als
Inferenz.

**Fine-Tuning** — Nachtraining eines fertigen Modells auf eigene Daten.

**Diffusionsmodell** — Die heute vorherrschende Bauform für Bild-KI. Sie lernt, aus
reinem Rauschen schrittweise ein Bild herauszuarbeiten.

**Denoising (Entrauschen)** — Der einzelne Schritt dieses Prozesses.

**Steps (Schritte)** — Anzahl der Entrauschungsschritte. Mehr Schritte bedeuten mehr
Detail und mehr Zeit.

**Latent Space (latenter Raum)** — Eine komprimierte interne Darstellung, in der das
Modell rechnet. Deutlich kleiner als das fertige Bild — der Grund, warum
Bildgenerierung überhaupt auf Endgeräten läuft.

**VAE (Variational Autoencoder)** — Der Übersetzer zwischen latentem Raum und sichtbarem
Bild.

**Text-Encoder** — Wandelt den Prompt in eine für das Modell verständliche Form.

**Prompt** — Die Textbeschreibung des gewünschten Bildes.

**Negativer Prompt** — Beschreibung dessen, was *nicht* erscheinen soll.

**CFG (Classifier-Free Guidance)** — Regelt, wie streng sich das Modell an den Prompt
hält. Zu niedrig heisst beliebig, zu hoch heisst überzeichnet.

**Seed** — Startwert des Zufallsgenerators. Gleicher Seed und gleiche Einstellungen
liefern dasselbe Bild — die Grundlage reproduzierbarer Versuche.

**img2img** — Bilderzeugung ausgehend von einem vorhandenen Bild statt von Rauschen.

**Denoise-Stärke** — Wie stark das Ausgangsbild bei img2img überschrieben wird. Niedrig
heisst nah am Original, hoch heisst freier.

**Inpainting** — Gezieltes Neuerzeugen nur eines maskierten Bildbereichs.

**ControlNet** — Ein Zusatzmodell, das die Bilderzeugung an eine Vorgabe bindet — etwa
an eine Tiefenkarte oder Kantenzeichnung. *Der entscheidende Baustein dieses Projekts:
Er ist der Grund, warum die KI die echte Kubatur übernimmt statt eine zu erfinden.*

**Conditioning (Konditionierung)** — Oberbegriff für alles, was die Erzeugung lenkt:
Prompt, Tiefenkarte, Referenzbild.

**LoRA (Low-Rank Adaptation)** — Ein sparsames Nachtrainingsverfahren. Statt das ganze
Modell zu verändern, wird eine kleine Zusatzschicht gelernt — typischerweise wenige
Dutzend Megabyte statt vieler Gigabyte. Übliches Mittel, einem Modell einen bestimmten
Stil beizubringen.

**IP-Adapter** — Verfahren, das einen Stil aus einem Referenzbild überträgt, **ohne**
Training. Schnell, aber weniger verbindlich als eine LoRA.

**Depth-ControlNet-Naht** — Der Vertrag, über den in diesem Projekt Bildmodelle
austauschbar bleiben: Jeder Backbone wird über dieselbe Tiefenkarten-Konditionierung
angesprochen. Ein Modellwechsel ist dann ein Registry-Eintrag statt eines Umbaus. Modelle,
die dieses Paradigma verlassen (FLUX.2, HiDream), brauchen je eine eigene Adapterschicht.

**Multi-Reference-Editing** — Neuerer Ansatz, bei dem ein Modell mehrere Referenzbilder
direkt entgegennimmt, statt über ein ControlNet konditioniert zu werden. Mächtiger, aber
nicht mit der obigen Naht verträglich.

**Referenzset** — Die kuratierten Bilder, gegen die der Stil gemessen wird. *Hier: eigene
Renders des Büros — sie bleiben lokal und kommen nie ins Repo (Regel 3).*

**Stil-Score** — Wie nah ein Render am Referenzset liegt, gemessen als
Kosinus-Ähnlichkeit der Embeddings. Schwelle 0,30.

**Aggregation (Messwerte)** — Wie mehrere Einzelwerte zu einem zusammengefasst werden.
*Beim Stil-Score: `max` fragt „wie nah ist die **nächste** Referenz?", `mittel` fragt „wie
nah ist das Set **insgesamt**?". Bei einem bewusst vielfältigen Referenzset urteilen die
beiden verschieden — `max` ist Vorgabe, weil ein Treffer auf einen der Bürostile genügt.*
*Nicht zu verwechseln mit* **Aggregation (Lizenzrecht)** *in Abschnitt 2.*

**Embedding** — Die Übersetzung von Inhalten (Text, Bild) in eine Zahlenreihe, in der
Ähnlichkeit als Nähe messbar wird.

**Kosinus-Ähnlichkeit** — Das übliche Ähnlichkeitsmass zwischen zwei Embeddings.
Wertebereich −1 bis 1. *In diesem Projekt Grundlage des Stil-Scores.*

**Halluzination** — Wenn ein Modell etwas Plausibles, aber Falsches erzeugt. *Im
Architekturkontext der entscheidende Mangel: ein schönes Gebäude, das nicht das
entworfene ist.*

**Backbone** — Das Hauptmodell einer Pipeline, im Unterschied zu den Hilfsmodellen.

**Quantisierung** — Verkleinerung der Gewichte durch gröbere Zahlendarstellung. Spart
Speicher, kostet etwas Qualität.

**fp16 / fp8** — Zahlenformate der Gewichte (16 bzw. 8 Bit). Je kleiner, desto
sparsamer und ungenauer.

**GGUF** — Ein quantisiertes Dateiformat, verbreitet für den Betrieb auf schwacher
Hardware.

**VRAM** — Der Speicher auf der Grafikkarte. Die harte Obergrenze dafür, welche Modelle
überhaupt laufen.

**Upscaling** — Nachträgliches Vergrössern eines Bildes unter Hinzuerfindung von Details.

**Gated Model** — Modell, dessen Gewichte erst nach Zustimmung zu Nutzungsbedingungen
heruntergeladen werden können.

---

## 7 · Sprachmodelle und Agenten

**LLM (Large Language Model)** — Ein Modell, das Text fortsetzt. Grundlage von Claude,
GPT, Qwen, Llama.

**Token** — Die Recheneinheit, in der Sprachmodelle Text zerlegen — meist Wortteile.
Grobe Faustregel: ein Token entspricht etwa vier Zeichen.

**Kontextfenster** — Wieviel Text ein Modell gleichzeitig überblicken kann. Alles
darüber hinaus muss zusammengefasst oder weggelassen werden.

**Systemprompt** — Die einleitende Anweisung, die Rolle und Regeln festlegt, bevor das
Gespräch beginnt.

**Prompting** — Die Praxis, Anweisungen so zu formulieren, dass ein brauchbares Ergebnis
entsteht.

**Few-Shot Prompting** — Der Anweisung einige Beispiele beigeben, statt sie nur zu
beschreiben.

**Chain-of-Thought** — Das Modell zum schrittweisen Denken anhalten, statt sofort zu
antworten. Verbessert Ergebnisse bei mehrstufigen Aufgaben.

**Temperature** — Regelt die Zufälligkeit der Antworten. Niedrig heisst berechenbar,
hoch heisst vielfältig.

**RAG (Retrieval-Augmented Generation)** — Verfahren, bei dem vor der Antwort passende
Dokumente herausgesucht und mitgegeben werden. Der übliche Weg, ein Modell auf eigenem
Material antworten zu lassen, ohne es nachzutrainieren.

**Agent** — Ein Sprachmodell, das nicht nur antwortet, sondern Werkzeuge bedienen und
mehrschrittig arbeiten kann.

**Tool Use / Function Calling** — Die Fähigkeit, statt einer Textantwort einen
Werkzeugaufruf zu erzeugen — etwa eine Datei zu lesen oder einen Befehl auszuführen.

**MCP (Model Context Protocol)** — Ein offener Standard dafür, wie Sprachmodelle
Werkzeuge und Datenquellen ansprechen. Statt für jedes Modell eine eigene Anbindung zu
schreiben, spricht man ein gemeinsames Protokoll.

MCP löst ein Problem, das es **nur bei Sprachmodellen** gibt: Das Modell weiss vorab
nicht, welche Werkzeuge existieren. Es braucht sie beschrieben — Name, Zweck, erwartete
Angaben —, bevor es eines auswählen kann. Ruft dagegen ein Programm ein anderes auf,
steht der Aufruf bereits im Code; dort ist ein Protokoll überflüssiger Aufwand.

*Abgrenzung: MCP ist **nicht** die allgemeine Form, in der Programme miteinander reden,
und **nicht** das Mittel, mit dem in diesem Projekt die Lizenz-Prozessgrenze gezogen
wird. Dafür genügt der Subprozessaufruf. MCP kommt an genau einer Stelle vor — ganz
oben, wo ein Sprachmodell die Pipeline bedienen soll.*

**MCP-Server** — Ein Programm, das über dieses Protokoll Werkzeuge bereitstellt.
*In diesem Projekt der geplante Weg, über den ein lokales Sprachmodell Renderaufträge
einstellen darf — einstellen, nicht ausführen. Der Server spricht mit der eigenen
Bibliothek, nie direkt mit Blender oder IfcOpenShell.*

**Lokales Modell** — Ein Modell, das auf eigener Hardware läuft. Kein Datenabfluss,
keine laufenden Kosten, dafür begrenzt durch die eigene Grafikkarte.

**llama.cpp / Ollama / vLLM** — Programme zum Betrieb lokaler Sprachmodelle.

**Guardrail** — Eine technische Schranke, die verhindert, dass ein Modell etwas
Unerwünschtes auslöst. *In diesem Projekt: Freigabe-Token und GPU-Leerlaufprüfung vor
jedem Render.*

---

## 8 · Systemarchitektur

**Architektur (Software)** — Der Aufbau eines Systems: welche Teile es gibt, wer wovon
abhängt, wo die Grenzen verlaufen. Der Begriff meint dasselbe wie im Bauwesen, nur ist
das Material Code.

**Node (Knoten)** — Ein einzelner Arbeitsschritt in einer Verarbeitungskette, mit
Eingängen und Ausgängen.

**Graph** — Ein Netz aus Knoten und Verbindungen.

**DAG (Directed Acyclic Graph)** — Ein gerichteter Graph ohne Kreise: Die Verbindungen
haben eine Richtung, und kein Weg führt zum Ausgangspunkt zurück. Dadurch ist immer eine
gültige Reihenfolge bestimmbar. Die übliche Grundform von Bildketten.

**Skip-on-Error** — Wenn ein Knoten in einer Kette scheitert, werden alle von ihm
abhängigen Knoten übersprungen statt mit unvollständigen Eingaben gerechnet. Ein Ergebnis
aus halben Daten ist schlimmer als gar keines — es sieht gültig aus.

**Pipeline** — Eine feste Abfolge von Verarbeitungsschritten.

**Frontend / Backend** — Die sichtbare Oberfläche gegenüber dem rechnenden Unterbau.
*In diesem Projekt muss das Backend allein lauffähig sein (Regel 4).*

**Job / Queue (Auftrag / Warteschlange)** — Ein Auftrag wird eingestellt statt sofort
ausgeführt und wartet, bis Kapazität da ist. Entkoppelt Auslösen und Ausführen — die
Grundlage dafür, dass ein Sprachmodell etwas anstossen darf, ohne die Grafikkarte zu
blockieren.

**Scheduler** — Das Programm, das entscheidet, wann ein Auftrag ausgeführt wird.

**Freigabe-Token** — Eine Zeichenfolge, die eine Befugnis belegt: Erst mit ihr darf ein
teurer Vorgang starten. *Hier `CONFIRMED_RENDER_*`. Es wird bewusst **nie** in die
Auftragsdatei geschrieben — läge es darin, wäre die Befugnis mit der Datei weiterreichbar,
und jeder, der das Verzeichnis lesen kann, hätte sie.*

**Pfad-Trickserei (Path Traversal)** — Ein Angriff, bei dem in einem Namen `..` oder `/`
steckt, um aus dem vorgesehenen Verzeichnis auszubrechen — etwa `../../etc/passwd`. Abwehr:
Namen prüfen, bevor sie zu Pfaden werden.

**Positivliste / Verbotsliste** — Zwei Arten zu prüfen: erlauben, was ausdrücklich zulässig
ist (Positivliste), oder ablehnen, was ausdrücklich schädlich ist (Verbotsliste). *Bei
Sicherheitsfragen ist die Positivliste die richtige — eine Verbotsliste übersieht immer
etwas.*

**fsync** — Betriebssystem-Befehl, der erzwingt, dass Geschriebenes tatsächlich auf dem
Datenträger liegt und nicht nur in einem Zwischenspeicher. Nötig, wenn ein Stromausfall
zwischen „geschrieben" und „wirklich da" nicht zu Datenverlust führen darf.

**Atomares Schreiben** — Eine Datei so schreiben, dass sie für Leser entweder ganz alt
oder ganz neu ist, nie halb. Üblich: erst in eine Nebendatei schreiben, dann in einem
einzigen Schritt umbenennen. *Nötig, weil ein abgebrochener Schreibvorgang sonst einen
halben Auftrag hinterlässt, den ein Scheduler später für gültig hält.*

**Zustandsautomat** — Ein Ding mit festgelegten Zuständen und festgelegten Übergängen
dazwischen. Alles, was nicht ausdrücklich erlaubt ist, ist verboten. *Ein Auftrag geht
von `awaiting_approval` über `queued` und `running` nach `done` — aber nie rückwärts, und
nie an der Freigabe vorbei.*

**Endzustand** — Ein Zustand, aus dem es keinen Weg hinaus gibt. *`done`, `error` und
`cancelled`: Ein abgeschlossener Auftrag lässt sich nicht wieder starten.*

**Content-Hashing** — Einen Zwischenspeicher nicht über Dateinamen oder Änderungsdatum
adressieren, sondern über eine Prüfsumme des **Inhalts**. Identischer Inhalt ergibt
denselben Schlüssel, auch unter anderem Namen — und geänderter Inhalt einen anderen, auch
bei gleichem Namen.

**Mutationsprobe** — Eine Gegenprüfung für Tests: Man baut absichtlich einen Fehler ein
und schaut, ob die Tests ihn bemerken. Tun sie es nicht, bewachen sie nichts. *Ohne das
kann eine grüne Testreihe blosse Beruhigung sein.*

**Cache** — Zwischenspeicher für teuer berechnete Ergebnisse, damit sie nicht doppelt
berechnet werden.

**Hash / Prüfsumme** — Eine kurze Zeichenfolge, die aus einem Inhalt berechnet wird.
Gleicher Inhalt ergibt gleichen Hash. Dient dazu, Gleichheit festzustellen und
Zwischenergebnisse wiederzufinden.

**Contract (Vertrag)** — Die verbindliche Festlegung, welche Daten zwischen zwei Teilen
fliessen. Meist als Schema notiert.

**Adapter** — Zwischenschicht, die eine fremde Schnittstelle auf die eigene übersetzt.
*In diesem Projekt der Mechanismus, der Bildmodelle austauschbar macht.*

**Seam (Naht)** — Eine bewusst gesetzte Trennstelle im System, an der später etwas
ausgetauscht oder geprüft werden kann.

**Gate (Tor)** — Eine Prüfung, die bestanden sein muss, bevor es weitergeht.
*In diesem Projekt: Ein Render gilt nur als bestanden, wenn er sowohl das Stil- als auch
das Geometrie-Tor passiert.*

**Wrapper** — Eine dünne Hülle um fremden Code, die dessen Bedienung vereinheitlicht.

**Topologische Sortierung** — Verfahren, das aus einem DAG eine gültige Reihenfolge
ableitet: Jeder Knoten kommt erst dran, wenn alle seine Vorgänger fertig sind. Entdeckt
zugleich Kreise, denn bei einem Kreis bleibt eine gültige Reihenfolge unmöglich.
*In diesem Projekt: die Art, wie KosmoOrbit seine Knotenketten ausführt.*

**JSON-Schema** — Eine formale Beschreibung, wie eine JSON-Struktur auszusehen hat:
welche Felder es gibt, welchen Typ sie haben, welche verpflichtend sind. Macht
Schnittstellen maschinell prüfbar statt nur dokumentiert.

**Validierung** — Die Prüfung tatsächlicher Daten gegen ihr Schema. Schlägt sie fehl,
stimmt die Wirklichkeit nicht mit dem Vertrag überein.

**inputSchema / outputSchema** — Die beiden Schemas eines MCP-Werkzeugs: was es erwartet,
was es zurückgibt. *In diesem Projekt Pflicht — ohne sie kann KosmoOrbit unsere Werkzeuge
nicht verdrahten.*

**structuredContent** — Das Feld, in dem ein MCP-Werkzeug sein maschinenlesbares Ergebnis
zurückgibt, im Unterschied zum Freitext für Menschen.

**Cockpit-Prinzip** — Entwurfshaltung des ArchitekturKosmos: Die Oberfläche *konsumiert*
Werkzeugverträge, statt deren Logik nachzubauen. Die Fähigkeit lebt im Werkzeug, nicht in
der Ansicht. Deckungsgleich mit Regel 4, nur aus Sicht der Oberfläche formuliert.

**Read-only-Gate** — Schranke, die nur lesende und rechnende Aufrufe durchlässt.
Schreibende Vorgänge brauchen einen eigenen, ausdrücklich freigegebenen Weg.

**Lane (Bahn)** — Im ArchitekturKosmos ein Fachbereich mit eigenem Werkzeugsatz
(KosmoDraw, KosmoPublish, KosmoVis). Eine Kette läuft über mehrere Lanes hinweg.

**Local-first** — Entwurfshaltung, bei der alles ohne Internet funktioniert. Cloud ist
Ergänzung, nicht Voraussetzung.

---

## 9 · Arbeit mit Claude Code

**Claude** — Das Sprachmodell von Anthropic.

**Claude Code** — Die Fassung von Claude, die in einer Entwicklungsumgebung arbeitet:
Dateien lesen und schreiben, Befehle ausführen, mit Git umgehen.

**Session (Sitzung)** — Ein zusammenhängender Arbeitsverlauf mit gemeinsamem Gedächtnis.
Mit dem Ende der Sitzung geht dieses Gedächtnis verloren — was bleiben soll, muss in
Dateien stehen.

**Kontext** — Alles, was Claude gerade „vor Augen" hat: Gespräch, gelesene Dateien,
Werkzeugausgaben. Begrenzt (siehe *Kontextfenster*).

**Kompaktierung** — Automatisches Zusammenfassen, wenn der Kontext voll wird. Details
gehen dabei verloren — ein weiterer Grund, Beschlüsse schriftlich festzuhalten.

**`CLAUDE.md`** — Die Datei im Projektwurzelverzeichnis, die Claude zu Beginn jeder
Sitzung liest. Der Ort für dauerhafte Projektregeln.
*In diesem Projekt: die vier nicht verhandelbaren Regeln.*

**Subagent** — Eine eigenständige Nebensitzung für eine abgegrenzte Teilaufgabe, mit
eigenem Kontext.


**Orchestrator** — Bei mehreren gleichzeitig arbeitenden Modellen die Instanz, die die
Arbeit aufteilt, verteilt und die Ergebnisse zusammenführt, statt selbst alles zu tun.
Sinnvoll nur dort, wo Teilaufgaben wirklich unabhängig sind — sonst kostet das Aufteilen
mehr, als es einbringt.

**Skill** — Eine hinterlegte Arbeitsanweisung für wiederkehrende Aufgaben, die bei Bedarf
geladen wird.

**Slash-Befehl** — Ein mit `/` eingeleiteter Kurzbefehl.

**Sandbox** — Eine abgeschottete Umgebung, in der Befehle ohne Risiko für das übrige
System laufen.

**Permission Mode** — Die Einstellung, welche Aktionen ohne Rückfrage erlaubt sind.

---

## Änderungsverzeichnis

| Datum | Änderung |
|---|---|
| 2026-08-14 | Erstfassung: 9 Themengruppen, ~200 Begriffe |
| 2026-08-14 | Ergaenzt: IPC, stdout/stderr, Exit-Code, Protokoll, Subprozess praezisiert |
| 2026-08-18 | Ergaenzt aus dem Multipass-Ausbau: Beauty-Pass, Emissions-Shader, View-Transform, Dithering, Denoiser, Bittiefe |
| 2026-08-18 | Ergaenzt aus Backbone/Stil-QA: Registry, Dataclass/frozen, Depth-ControlNet-Naht, Multi-Reference-Editing, Referenzset, Stil-Score, Attrappe, vakuoeser Test, OpenRAIL++-M, Stability Community License. **Aggregation** in zwei Bedeutungen getrennt (Lizenzrecht / Messwerte) |
| 2026-08-18 | Ergaenzt aus dem Multipass: Goldener Winkel, Normalisierung |
| 2026-08-18 | Ergaenzt aus der Geometrie-QA: Rangkorrelation, Bindung, Silhouette, IoU, geometrisches Mittel, Disparitaet |
| 2026-08-18 | Ergaenzt aus Phase 3: Leistungsgrenze, Rauchprobe, fail-closed praezisiert |
| 2026-08-18 | Ergaenzt aus Phase 2: Skip-on-Error, Freigabe-Token, Pfad-Trickserei, Positivliste, fsync, atomares Schreiben, Zustandsautomat, Endzustand, Content-Hashing, Mutationsprobe |
| 2026-08-18 | Ergaenzt aus der Paketierung: pyproject.toml, src-Layout, optionale Abhaengigkeitsgruppe, SPDX |
| 2026-08-18 | Ergaenzt aus Phase 1: STEP/ISO-10303-21, Extrusion/SweptSolid, GUID, Determinismus, Testfixture, Orchestrator |
| 2026-08-14 | Ergaenzt aus Phase 0: stdio, Pfad-Sandbox, write-gated, Runner |
| 2026-08-14 | Ergaenzt aus der KosmoOrbit-Einbindung: Tauri, TypeScript, React, REST/Endpoint, SSE, Sidecar, topologische Sortierung, JSON-Schema, Validierung, inputSchema/outputSchema, structuredContent, Cockpit-Prinzip, Read-only-Gate, Lane |
| 2026-08-14 | Ausgebaut: Apache-2.0 (Auflagen, Patent- und Verteidigungsklausel), MCP (Abgrenzung zum Subprozessaufruf) |
