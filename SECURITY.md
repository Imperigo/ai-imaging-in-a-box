# Sicherheit

## Was hier überhaupt eine Sicherheitslücke ist

Visbox ist kein Dienst im Netz. Es läuft lokal auf dem Rechner der Anwenderin, ohne
offenen Port und ohne Anmeldedaten. Die Frage „was kann ein Angreifer erreichen?" hat
hier darum eine andere Form als bei einer Webanwendung — und drei ernsthafte Antworten.

**Die kurze Fassung: Alles, was Visbox gefährlich machen kann, kommt von aussen herein —
als Datei, als Gewicht oder als Pfad.**

### 1 · Wir starten fremde Programme

Die Prozessgrenze, die dieses Projekt aus Lizenzgründen zieht (Blender und die
IFC-Umgebung laufen als eigene Programme, nie als Import), ist zugleich die grösste
Angriffsfläche. Gestartet wird:

* **Blender**, adressiert über `AIIMAGING_BLENDER`, mit `--background --python <skript>`.
* **Der Python-Interpreter der IFC-Umgebung**, adressiert über `AIIMAGING_IFC_PYTHON`.
* **Die LoRA-Trainerumgebung**, über `AIIMAGING_LORA_PYTHON` und `AIIMAGING_LORA_TRAINER`.

Daraus folgen echte Fragen, und eine Antwort darauf gehört in einen Bericht:

* **Wer diese Umgebungsvariablen setzen kann, kann beliebigen Code ausführen** — mit den
  Rechten der Anwenderin. Dasselbe gilt für jeden, der in die Verzeichnisse schreiben
  kann, auf die sie zeigen. Ein verwundbarer Fall ist ein Ort, den *andere Benutzer
  desselben Rechners* beschreiben können.
* **Der Skriptpfad, den Blender ausführt, ist ein Einfallstor.** Jede Stelle, an der ein
  solcher Pfad aus einer Eingabe entsteht statt aus dem Paket, ist ein Fund.
* **Argument-Schmuggel:** Ein Dateiname, der mit `-` beginnt, kann als Schalter eines
  aufgerufenen Programms gelesen werden statt als Datei.
* **Pfadauswanderung in die Gegenrichtung:** Namen aus einer Fremddatei werden hier
  weiterverwendet — seit dem 26.08.2026 trägt ein Knotenname den Namen aus der
  IFC-Datei. Wo ein solcher Name in einen Ausgabepfad gerät, kann `../` darin
  hinausführen.

### 2 · Wir laden Modellgewichte aus dem Netz

Gewichte landen in der Ablage, auf die `AIIMAGING_MODELLE` zeigt, und werden danach
geladen. Das ist kein Datenformat wie ein Bild, sondern ein Format, das bei manchen
Varianten **Code ausführt**:

* **Ein `.bin`-, `.ckpt`- oder `.pt`-Gewicht ist eine Python-Pickle-Datei.** Sie zu
  laden heisst, den darin abgelegten Code auszuführen. `.safetensors` tut das nicht —
  das ist der Grund, warum es dieses Format gibt. Jede Stelle im Code, die ein
  Pickle-Format lädt, ohne dass es dafür einen ausdrücklichen Grund und eine
  Herkunftsprüfung gibt, ist ein Fund.
* **Ein Bezug auf ein Modell ohne festgenagelte Fassung** (ohne Revision oder Prüfsumme)
  heisst: Was heute geladen wird, muss nicht sein, was morgen geladen wird. Bei einem
  fremden Konto, das umbenannt oder übernommen wird, ist das der ganze Angriff.
* **Eine Modellablage, in die andere schreiben können**, macht jede Prüfung wertlos, die
  vor dem Laden stattfand.
* **Kein Zertifikatsfehler wird unterdrückt.** Wenn Sie eine Stelle finden, an der die
  Prüfung abgeschaltet oder ein Fehler verschluckt wird, melden Sie sie.

### 3 · Wir lesen fremde Dateien mit fremden Parsern

IFC, glTF und glb, dazu Bilder und Tiefenkarten. Diese Dateien kommen von aussen — aus
einem CAD-Programm, von einer Kollegin, aus einem Download. Sie werden von Bibliotheken
in C und C++ gelesen (IfcOpenShell samt CGAL, trimesh, Pillow, OpenEXR), und die sind
nicht speichersicher.

* **Ein Absturz beim Einlesen einer präparierten Datei ist ein Bericht wert**, auch wenn
  es „nur" ein Absturz ist.
* **Eine glTF-Datei kann auf externe Puffer verweisen** (`uri`). Ein solcher Verweis
  kann auf eine beliebige Datei des Rechners zeigen oder eine Netzverbindung auslösen,
  die die Anwenderin nicht erwartet hat.
* **Grössenbomben:** Eine kleine Datei, die beim Entpacken oder Auffalten den Speicher
  füllt (eingebettete Puffer, riesige Bildmasse). Der Schaden ist ein stehender Rechner,
  und das zählt.
* **Der eine Trost:** Die IFC-Seite läuft schon aus Lizenzgründen in einem eigenen
  Prozess. Ein Fehler dort ist damit nicht automatisch ein Fehler im Hauptprozess — aber
  er läuft mit denselben Benutzerrechten, und das ist kein Sandkasten.

### 4 · Die Auftragsbrücke und die Anbindung an ein Cockpit

Aufträge werden als Dateien übergeben, nicht über einen Dienst. Ein Verzeichnis unter
`/tmp` ist auf einem gemeinsam genutzten Rechner aber von **jedem lokalen Benutzer**
beschreibbar: Wer dort eine Auftragsdatei ablegt, lässt sie von der Abholung ausführen.
Dazu kommen die üblichen `/tmp`-Fragen — Verweise (Symlinks), die woanders hinzeigen,
und Namen, die vor dem Schreiben schon von jemand anderem angelegt wurden.

Die MCP-Schicht ist ein optionaler Zusatz und Teil dieser Fläche: Sie nimmt Aufträge von
aussen entgegen. Wer sie startet, öffnet eine Tür, die der Kern nicht braucht.

---

## Was hier **keine** Sicherheitslücke ist

Damit Sie Ihre Zeit nicht an der falschen Stelle einsetzen:

* **Ein Bild besteht die Geometrieprüfung, obwohl es nicht zum Modell passt.** Das ist
  ein Messfehler und für dieses Projekt ein wichtiger Befund — aber er gehört in ein
  öffentliches Issue, nicht in eine vertrauliche Meldung. Genau diese Art Befund hat am
  18.09.2026 die ganze Prüfung umgestellt.
* **Eine Schwelle ist zu mild oder zu streng.** Issue.
* **Ein Wächter ist umgehbar, indem man den Quelltext ändert.** Wer den Quelltext ändern
  kann, hat den Rechner. Die Wächter dieses Projekts schützen vor Versehen, nicht vor
  dem Eigentümer.

**Ein Grenzfall, und wir nehmen ihn ernst:** Wenn Sie in diesem Repo einen echten Namen
finden — eines Menschen, eines Büros, eines Projekts — oder einen absoluten Pfad, in dem
ein Benutzername steht, dann melden Sie das bitte **vertraulich** und nicht als Issue.
Das ist keine Lücke im Programm, aber es sind Daten, die niemand veröffentlichen wollte.
Es ist hier schon passiert: Der Name kam nicht durch Nachlässigkeit herein, sondern über
Fehlertexte, die den vollen Skriptpfad mitbrachten.

---

## Melden

**Nicht als öffentliches Issue, nicht als Pull Request.**

Der bevorzugte Weg ist die private Meldung über GitHub: Reiter **Security** →
**Report a vulnerability**. Sie erzeugt einen vertraulichen Kanal, ohne dass jemand eine
Adresse veröffentlichen muss.

> **Alternative Kontaktstelle:** *(noch einzutragen — diese Zeile füllt der Owner aus.)*

Hilfreich in einer Meldung:

* Welche der Flächen oben betroffen ist, oder welche vierte Sie gefunden haben.
* Was ein Angreifer erreicht, und **was er dafür schon können muss** (Datei
  unterschieben? Umgebungsvariable setzen? auf demselben Rechner angemeldet sein?).
* Ein möglichst kleiner Weg zur Wiederholung. Eine präparierte Datei nur als
  Beschreibung oder Erzeugungsskript — **schicken Sie keine echten Projektdateien**,
  das ist Regel 3 dieses Projekts und gilt auch für Sicherheitsmeldungen.
* Fassung, Betriebssystem, Python-Version, Blender-Version.

---

## Was Sie an Reaktion erwarten dürfen

Ehrlich statt nach Vorlage: **Visbox ist die Vertiefungsarbeit einer einzelnen Person,
kein Produkt mit Bereitschaftsdienst.** Eine Meldung wird gelesen und beantwortet, aber
es gibt keine zugesicherte Frist und keinen zweiten Menschen, der einspringt. In der
Zeit um die Abgabe Ende Februar 2027 kann eine Antwort länger dauern als sonst.

Wir bitten um eine Gelegenheit zur Behebung, bevor Sie eine Lücke veröffentlichen. Eine
feste Frist verlangen wir nicht; verlangen Sie umgekehrt bitte keine Zusage, die dieses
Projekt nicht halten kann.

## Unterstützte Fassungen

Es gibt noch keine Veröffentlichung (Stand: `0.0.1`, in Arbeit). Behoben wird
ausschliesslich im Hauptzweig. Ältere Stände werden nicht nachgepflegt.
