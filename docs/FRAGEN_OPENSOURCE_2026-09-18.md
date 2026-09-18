# Was ich wissen muss, bevor gebaut wird — 62 Fragen

**Grundlage:** keine
**Nachgesehen bis:** f7cd8f2
**Codestand:** `f7cd8f2`

> **Owner-Auftrag 18.09.2026:** Aus KosmoOrbit wird eine eigenständige Open-Source-Software
> für die Vertiefungsarbeit herausgelöst. ETH D-ARCH ITA, Lehrstuhl Gramazio Kohler.
> Vorrang bis ca. Februar 2027, danach wieder geschlossen. Zweispurig: was hier entsteht,
> wandert auch nach KosmoOrbit — und umgekehrt.

---

## Wie dieses Blatt zu lesen ist

Jede Frage nennt **warum** sie gestellt wird und **die Wege mit ihren Kosten**. Sie ist so
gebaut, dass ein Satz als Antwort genügt.

| Marke | heisst |
|---|---|
| 🔴 | **Blockiert.** Ohne Antwort kann ich an dieser Stelle nicht anfangen. |
| 🟠 | Vor dem Bau des jeweiligen Teils nötig, nicht sofort. |
| 🔵 | Später, aber besser jetzt entschieden als später umgebaut. |

**Wo ich eine Empfehlung habe, steht sie dabei.** Sie sind laut Ihrem Auftrag automatisch
freigegeben — wenn Sie zu einer Frage nichts sagen, nehme ich meine Empfehlung und schreibe
auf, dass sie von mir stammt.

---

## Was ich vorher selbst nachgesehen habe

Damit die Fragen nicht Dinge erfragen, die dastehen:

| | KosmoOrbit | AI Imaging in a Box |
|---|---|---|
| Sprache | TypeScript / React | Python |
| Umfang | ~78 000 Zeilen, 7 Pakete | 40 757 Zeilen, 50 Module |
| Auslieferung | **Tauri 2** (Desktop), PWA | Bibliothek, `pip` |
| Knoten | **`NodeCanvas.tsx`, 2992 Zeilen**, Typen `modell szene material prompt stimmung kombinierer zahl render` | `graph.py` — Rechenkern mit Zwischenspeicher, **ohne Oberfläche** |
| KI | Anthropic · **Ollama** · OpenAI · claude-cli | — |
| Skizze | `SketchModus.tsx`, iPad über Yjs-Sync | — |
| Blender | über HomeStation-Brücke | Unterprozess, 30 Beweise |
| Bildmodelle | — | Registry mit Lizenzampel, **keine Gewichte** |

**Der wichtigste Einzelbefund:** Die beiden Bestände sind **komplementär, nicht doppelt.**
KosmoOrbit hat die Oberfläche und die Knotentypen; wir haben den Rechenkern mit
Inhalts-Hashing, Herkunftsnachweis und Qualitätsprüfung. Das ist eine gute Ausgangslage —
es heisst aber auch, dass die Naht zwischen TypeScript und Python die zentrale
Bauentscheidung ist (Frage 12).

---

# 1 · Der Name

**🔴 F1 — Wie soll die Software heissen?**
Das ist die erste Entscheidung, weil alles andere daran hängt: Repo, Paketname, Fenstertitel,
Titelblatt der Arbeit, und ob sie zur Kosmo-Familie gehört oder nicht.

Meine vier Vorschläge, in Rangfolge:

| | Name | dafür | dagegen |
|---|---|---|---|
| 1 | **Baukasten** | Bauhaus-Resonanz, an einer Architekturschule sofort verstanden. Trifft „in a Box" wörtlich: Kasten = Box. Kurz, sprechbar. | Deutsch; international braucht es einen Untertitel. Häufiges Wort — Markenlage zu prüfen. |
| 2 | **AI Imaging in a Box** (bleibt) | Sagt genau, was es ist. Ist schon der Repo-Name, also null Reibung. Die Verheissung *ein Download, alles drin* steckt im Namen. | Lang, generisch, nicht schützbar, klingt nach Werkzeug statt nach Werk. |
| 3 | **Rissbild** | „Riss" ist der Fachbegriff für die Zeichnung (Grundriss, Aufriss), „Bild" das Ergebnis — der Bogen der Software in einem Wort. Distinktiv. | Für Englischsprachige weder lesbar noch sprechbar. „Riss" heisst auch Sprung/Bruch. |
| 4 | **KosmoBox** | Bleibt in der Familie, macht die Herkunft sichtbar, erleichtert das Zurückführen im Februar. | Bindet die offene Arbeit an ein geschlossenes Produkt — genau das, was eine ETH-Arbeit nicht will. |

**Meine Empfehlung: Baukasten**, mit dem englischen Untertitel *an AI imaging workbench for
architects*. Der Repo-Name kann bleiben.

**🟠 F2 — Soll der Name in die Kosmo-Familie gehören oder sich absetzen?**
Das ist eine andere Frage als F1 und wird oft mit ihr verwechselt. *Dafür:* Herkunft
sichtbar, Zurückführen einfacher. *Dagegen:* Eine ETH-Arbeit, die den Produktnamen der
eigenen Firma trägt, lädt die Frage nach der Unabhängigkeit ein — und die wollen Sie in
einer Vertiefungsarbeit nicht führen müssen.

**🔵 F3 — Wer ist Urheber im Sinne der Lizenz?**
Sie persönlich, eine Firma, die ETH? Das steht in jedem Dateikopf und im `NOTICE`, und es
im Nachhinein zu ändern heisst, jede Datei anzufassen.

**🔵 F4 — Wie soll die ETH genannt werden?**
Lehrstuhl, Institut, Betreuung Gonzalo Casas — was darf in Readme, Titel und Paketdaten
stehen? Gibt es dafür eine Vorgabe der ETH, die ich kennen muss?

---

# 2 · Abgrenzung — was ist drin, was bleibt draussen

**🔴 F5 — Welche der zwölf KosmoOrbit-Module kommen mit?**
Vorhanden sind: `asset data design dev doc kxp paket prepare publish spez train vis`.
Der Entwurfsablauf braucht nach meinem Verständnis `vis` (Bilder), `design` (Skizze),
`asset` (Modelle) und `spez` (KI). *Meine Empfehlung: diese vier, alles andere bleibt
drüben.* Widersprechen Sie, wo ich falsch liege — besonders bei `prepare` und `publish`.

**🔴 F6 — Kommt der BIM-Kern mit?**
KosmoOrbit kann modellieren (Wände, Treppen, Dächer, SIA-Pläne). Die neue Software soll
ein **Modell importieren**, nicht eines bauen. *Meine Empfehlung: nein* — das ist der
grösste einzelne Brocken, und er gehört nicht zum Entwurfsablauf, den Sie beschrieben
haben. Aber es ist Ihre Software, und vielleicht sehen Sie das anders.

**🟠 F7 — Was ist ausdrücklich ein Nicht-Ziel?**
Eine Arbeit wird nicht dadurch gut, dass sie alles kann. Was darf die Software
**ausdrücklich nicht** können, damit sie im Februar fertig ist? Mein Vorschlag:
kein Modellieren, kein Plansatz, keine Mehrbenutzer-Bearbeitung, keine Wolke.

**🟠 F8 — Gibt es in KosmoOrbit Code, der nicht offengelegt werden darf?**
Gekauftes, Fremdbeiträge, Kundenbezogenes, Marken. Ich prüfe das systematisch, aber Sie
wissen es schneller als jede Suche.

---

# 3 · Der Entwurfsablauf

**🔴 F9 — Was ist die kleinste Fassung, die für Sie ein Erfolg wäre?**
Wenn im Februar nur **eines** läuft — welches? Meine Lesart Ihres Auftrags:
*Modell rein → Kamera → Blender-Render → ein KI-Bild daraus → hineinskizzieren → neues
Bild.* Alles andere wäre Zugabe. Stimmt das?

**🟠 F10 — In welcher Reihenfolge baue ich die sechs Schritte?**
*Meine Empfehlung:* Import → Node-Tree → Render → KI-Bild → Skizze → Photoshop-Ersatz.
Begründung: Jeder Schritt erzeugt die Eingabe des nächsten, also ist die Reihenfolge des
Ablaufs auch die des Bauens, und nach jedem Schritt gibt es etwas Vorzeigbares.

**🟠 F11 — Wie viele Schritte muss eine Nutzerin tun, bis sie ihr erstes Bild sieht?**
Das ist die Zahl, an der ein Werkzeug gemessen wird. *Mein Vorschlag als Ziel: drei* —
Modell hineinziehen, Knopf drücken, warten. Zu niedrig gegriffen?

---

# 4 · Die Naht zwischen den zwei Sprachen

**🔴 F12 — Wie kommen TypeScript-Oberfläche und Python-Kern zusammen?**
Das ist die **folgenreichste technische Entscheidung des ganzen Vorhabens.**

| Weg | wie | Kosten |
|---|---|---|
| **A · Python als Unterprozess** | Tauri startet Python, Austausch über Dateien/JSON | Einfach, robust, die Prozessgrenze hilft auch bei Lizenzen. Aber: Python muss mitgeliefert werden (~80 MB), und der Start ist träge. |
| **B · Python als lokaler Dienst** | Python läuft als HTTP-Dienst, die Oberfläche spricht mit ihm | Flüssiger, gut für Fortschrittsanzeige. Aber: ein Dienst, der abstürzen, hängen und Ports blockieren kann. |
| **C · Alles nach TypeScript** | Den Python-Kern neu schreiben | Ein Programm statt zwei. Aber: 40 757 Zeilen geprüfter Code wegwerfen, und die Bildmodelle leben nun einmal in Python. |
| **D · Alles nach Python** | Oberfläche neu, z. B. Qt | Ein Programm. Aber: 2992 Zeilen NodeCanvas und die ganze Tauri-Auslieferung wegwerfen. |

*Meine Empfehlung: **B**, mit **A** als Rückfallebene.* Grund: Die Bildmodelle sind Python,
die Oberfläche ist gebaut, und ein lokaler Dienst ist das Einzige, was eine Fortschritts-
anzeige über einen 13-Minuten-Lauf trägt. **Sagen Sie mir, wenn Sie das anders sehen — ein
Wechsel dieser Entscheidung im Dezember kostet Wochen.**

**🟠 F13 — Darf die neue Software Code aus KosmoOrbit kopieren oder muss sie teilen?**
Kopieren ist schnell und läuft auseinander. Teilen ist sauber und koppelt zwei Vorhaben mit
verschiedenen Fristen. *Meine Empfehlung: kopieren, aber mit einer Probe, die anschlägt,
wenn die Fassungen auseinanderlaufen* — siehe Abschnitt 13.

---

# 5 · Der Importer

**🔴 F14 — Welche Formate muss er am Abgabetag können?**
Heute belegt: IFC und glTF/GLB. *Mein Vorschlag:* IFC, glTF/GLB und OBJ als Pflicht.
**Die eigentliche Frage:** Rhino `.3dm` und SketchUp `.skp` — das sind die Formate, die
Architekturstudierende wirklich haben. Ohne sie ist die Software für viele nicht benutzbar;
mit ihnen kommen zwei fremde Bibliotheken samt Lizenzfragen hinzu.

**🟠 F15 — Was passiert mit einem Modell, das 2 GB gross ist?**
Studierendenmodelle sind oft unaufgeräumt. Ablehnen? Vereinfachen? Rechnen lassen und
warten? *Meine Empfehlung: messen, warnen, rechnen lassen* — mit einer ehrlichen
Zeitschätzung vorher.

**🟠 F16 — Wie wird mit Einheiten und Hochachse umgegangen?**
Wir haben dafür eine Herkunftstabelle mit vier Sicherheitsgraden. Soll die Software raten
(bequem, manchmal falsch), fragen (sicher, nervt) oder beides (raten und die Vermutung
sichtbar machen)? *Meine Empfehlung: das Dritte.*

**🟠 F17 — Materialien und Texturen: mitnehmen oder wegwerfen?**
Für ein KI-Bild sind Materialien halb entbehrlich — das Bildmodell erfindet ohnehin
Oberflächen. Für ein Blender-Render sind sie es nicht.

**🔵 F18 — Soll es Beispielmodelle geben?**
Eine Software, die beim ersten Start etwas zu zeigen hat, wird ausprobiert. *Empfehlung:
ja, synthetisch erzeugt* — Regel 3 verbietet echte Projektdaten, und ein im Repo
erzeugbares Beispiel ist ohnehin besser.

---

# 6 · Der Node-Tree

**🔴 F19 — Was genau an Figma Weave ist das Vorbild?**
Ich konnte Weave nicht ansehen — mein Zugang ist nicht verknüpft. Ist es *das Aussehen*
(Kacheln, Kanten, Zoom), *das Verhalten* (Vorschau je Knoten, Ausführung auf Knopfdruck),
oder *das Modell* (welche Knoten es gibt und wie sie zusammenpassen)? Jede Antwort führt zu
einer anderen Arbeit. **Am hilfreichsten wären zwei, drei Bildschirmfotos.**

**🔴 F20 — Welche Knoten soll es geben?**
Heute in KosmoOrbit: `modell szene material prompt stimmung kombinierer zahl render`.
Nach Ihrem Ablauf fehlen mindestens: **Import**, **Kamera**, **Tiefe/ControlNet**,
**Skizze**, **Maske/Auswahl**, **Variante**, **Vergleich**, **Export**. *Meine Empfehlung:
diese acht ergänzen.* Welche fehlen Ihnen noch, und welche der vorhandenen sind Ballast?

**🟠 F21 — Wie streng sind die Verbindungen?**
Typgeprüft (man kann nichts Falsches stecken, aber es fühlt sich eng an) oder frei (alles
geht, Fehler zeigen sich erst beim Rechnen)? *Meine Empfehlung: typgeprüft, mit einer
lesbaren Begründung an der abgelehnten Kante* — „Tiefe passt nicht in Prompt" statt eines
roten Kreuzes.

**🟠 F22 — Was sieht man am Knoten selbst?**
Nur den Namen, ein kleines Vorschaubild, oder die Messwerte? *Meine Empfehlung: Vorschau
plus die eine Zahl, die zählt* — bei einem QA-Knoten also das Urteil, nicht sechs Werte.

**🟠 F23 — Wer rechnet wann?**
Alles sofort bei jeder Änderung (lebendig, aber ein Laptop glüht), oder auf Knopfdruck
(ruhig, aber man wartet)? *Meine Empfehlung: billige Knoten sofort, teure auf Knopfdruck*,
und die Software sagt, welcher welcher ist.

**🔵 F24 — Kann man einen Ablauf speichern und weitergeben?**
Ein Knotenbaum, den man teilt, ist die Art, wie sich so eine Software unter Studierenden
verbreitet. *Empfehlung: ja, als lesbare Datei im Repo-Format.*

**🔵 F25 — Gibt es Untergraphen?**
Also: mehrere Knoten zu einem zusammenfassen. Mächtig, aber ein eigenes Vorhaben.
*Empfehlung: nein, bis Februar.*

---

# 7 · Kosmo — die KI in der Software

**🔴 F26 — Was darf die KI tun?**
*Fragen beantworten* („was macht dieser Knoten?"), *vorschlagen* („so kämst du zum Ziel"),
oder *selbst bauen* (Knoten anlegen und verbinden)? Jede Stufe ist deutlich mehr Arbeit als
die vorige. *Meine Empfehlung: die ersten zwei bis Februar, die dritte als Zugabe.*

**🔴 F27 — Muss sie ohne Konto laufen?**
Das ist die Frage, die über die Brauchbarkeit für Studierende entscheidet. Mit Anthropic-
Schlüssel ist sie besser, kostet aber Geld und schliesst aus. Mit Ollama lokal ist sie
schlechter, aber frei. *Meine Empfehlung: **Ollama als Vorgabe**, ein eigener Schlüssel
optional* — und die Software sagt ehrlich, was der Unterschied ist.

**🟠 F28 — Welches lokale Modell, und wie gross darf es sein?**
Auf einem M1 Max mit 32 GB ist bei etwa 7–14 Milliarden Parametern (4–9 GB) Schluss, wenn
daneben noch ein Bildmodell laufen soll. *Vorschlag: eines um 8 GB, beim ersten Start
geladen, nicht mitgeliefert.*

**🟠 F29 — Wie viel von Kosmo darf mitkommen?**
`kosmo-ai` sind 12 570 Zeilen mit Personas, Gedächtnis, Staffelung. *Empfehlung: nur die
Werkzeugschicht und der Gesprächsfaden* — der Rest ist KosmoOrbit-Eigenart.

**🔵 F30 — Auf Deutsch oder Englisch?**
Die Software ist deutsch geschrieben. An der ETH liest man englisch.

---

# 8 · KosmoSketch und das iPad

**🔴 F31 — Ist das iPad Pflicht bis Februar?**
Das ist der grösste einzelne Umfangsposten in Ihrer Aufzählung. *Meine ehrliche
Einschätzung:* Skizzieren im Desktop-Fenster ist in Wochen machbar; eine iPad-Fassung ist
ein eigenes Vorhaben mit eigener Auslieferung. **Wenn eines von beidem gestrichen werden
muss, empfehle ich, das iPad auf nach Februar zu legen** — und im Desktop so zu bauen, dass
es später dazukommt.

**🟠 F32 — Was soll das Skizzieren bewirken?**
*Maske* („hier etwas anderes"), *Führung* („ungefähr diese Form"), oder *Geometrie*
(„daraus wird eine Wand")? Das Dritte kann KosmoOrbit schon, die ersten zwei sind für den
Bildweg die wichtigeren. *Empfehlung: Maske und Führung.*

**🟠 F33 — Skizziert man in das Rendering oder in das KI-Bild?**
Das ist ein Unterschied im Ablauf: in das Rendering heisst *nochmal rechnen*, in das KI-Bild
heisst *nachbessern*.

**🔵 F34 — Braucht es Druckempfindlichkeit und Neigung?**
Für Masken nein, für Entwurfsskizzen sehr wohl.

---

# 9 · Bilderzeugung und Photoshop-Ersatz

**🔴 F35 — Welches Bildmodell ist das Standardmodell?**
FLUX.1-dev und FLUX.2-dev sind **Non-Commercial und damit ausgeschlossen** — sie dürfen
nicht mitgeliefert und nicht empfohlen werden. Was bleibt, ist deutlich schwächer. *Meine
Empfehlung: SDXL-Familie unter offener Lizenz*, mit dem klaren Hinweis, dass ein
Nutzer selbst ein anderes einsetzen darf. **Das ist ein Qualitätsverlust, und die Arbeit
sollte ihn benennen statt ihn zu verstecken.**

**🔴 F36 — Werden Gewichte mitgeliefert?**
Mitliefern heisst ein Download von 7–20 GB und Lizenzfragen bei jeder Weitergabe. Nachladen
heisst, der erste Start braucht Netz und Geduld. *Empfehlung: nachladen, mit einer ehrlichen
Anzeige, was gleich passiert.*

**🟠 F37 — Wie lange darf ein Bild dauern?**
Auf einem M1 Max sind bei SDXL realistisch 30–90 Sekunden je Bild. Ab wann ist es zu lang,
um noch ein Entwurfswerkzeug zu sein?

**🟠 F38 — Was heisst „Photoshop-Ersatz" genau?**
*Bereich auswählen und neu erzeugen* (Inpainting), *Bild erweitern* (Outpainting),
*Gegenstand entfernen*, *Stil ändern*? **Meine Empfehlung: Inpainting mit Maske aus der
Skizze** — es trifft Ihren Ablauf am genauesten und baut auf dem auf, was schon da ist.

**🟠 F39 — Wie viele Varianten auf einmal?**
Vier parallel sprengen den Speicher eines Laptops. Vier nacheinander dauern sechs Minuten.

**🔵 F40 — Sollen eigene LoRAs trainierbar sein?**
Wir haben ein `lora`-Modul. Auf einem Laptop trainieren ist grenzwertig. *Empfehlung:
verwenden ja, trainieren nein.*

---

# 10 · Blender und das Rendern

**🔴 F41 — Wird Blender mitgeliefert, nachgeladen oder vorausgesetzt?**
Blender ist **GPL**. Mitliefern ist rechtlich heikel und macht das Paket um ~300 MB
schwerer. *Meine Empfehlung: voraussetzen und beim ersten Start prüfen*, mit einer klaren
Anleitung, wenn es fehlt. Das hält die Prozessgrenze sauber, die unsere Regel 2 verlangt.

**🟠 F42 — Welche Blender-Fassung ist verbindlich?**
Heute 4.2 LTS. Eine LTS-Fassung festzuschreiben erspart viel Ärger.

**🟠 F43 — Was, wenn kein Blender da ist?**
Gar nichts geht? Oder gibt es einen einfacheren Renderweg als Rückfall? *Empfehlung:
ehrlich abbrechen mit Anleitung* — ein zweiter Renderweg wäre eine zweite Wahrheit.

**🟠 F44 — Wie lange darf ein Render dauern, und was sieht man solange?**
Wir haben eine Fortschrittswache. Wichtiger als die Dauer ist, dass die Software nicht
stumm dasteht.

---

# 11 · Hardware und der Speicherdeckel

**🔴 F45 — Welche Maschine ist die Messlatte?**
Sie nennen M1 Max. *Ich schlage als verbindliche Untergrenze vor: Apple Silicon ab M1 Pro
mit **16 GB**, empfohlen 32 GB.* Alles darunter kann die Software ablehnen, statt eine
Stunde zu rechnen und dann abzustürzen.

**🔴 F46 — Wie hoch ist der Speicherdeckel?**
*Mein Vorschlag: 60 % des vereinten Speichers*, also 19 GB bei 32 GB. Darüber wird abgebrochen
mit einer Erklärung, statt das ganze System einfrieren zu lassen. Zu streng?

**🟠 F47 — Windows und Linux auch?**
Jede zusätzliche Plattform kostet Bauzeit, Prüfzeit und Fehlersuche auf Geräten, die ich
nicht habe. *Empfehlung: macOS zuerst und vollständig, Windows als Zugabe, Linux nur als
Quelltext.*

**🟠 F48 — Darf etwas in die Wolke ausweichen?**
Wenn ein Laptop nicht reicht — abbrechen, oder anbieten, es woanders rechnen zu lassen?
*Empfehlung: nein, bis Februar* — es macht aus einer lokalen Software eine mit Konto.

**🔵 F49 — Gibt es eine Maschine zum Prüfen?**
Ich habe hier weder GPU noch Apple Silicon. **Ohne eine Messung auf einem echten M1 Max
sind alle Zahlen oben geschätzt** — und ich möchte in der Arbeit nicht schätzen.

---

# 12 · Auslieferung

**🔴 F50 — Ein Download, und was ist drin?**
*Mein Vorschlag:* die Software plus Python, **ohne** Modellgewichte und **ohne** Blender,
also ~150 MB statt ~8 GB — und beim ersten Start holt sie, was fehlt, und sagt vorher, wie
viel.

**🟠 F51 — Signieren und beglaubigen?**
Ohne Apple-Beglaubigung erscheint beim Öffnen eine Warnung, die Laien abschreckt. Mit kostet
es ein Entwicklerkonto (99 USD/Jahr) und einen Bauschritt.

**🟠 F52 — Selbstaktualisierung?**
Tauri kann das. Aber eine Software, die sich selbst aktualisiert, braucht einen Server und
jemanden, der ihn betreibt — über Februar hinaus.

**🔵 F53 — Wo liegt der Download?**
GitHub-Releases ist das Einfachste und kostet nichts.

---

# 13 · Zweispurigkeit

**🔴 F54 — Was ist die Quelle der Wahrheit, wenn beide dasselbe ändern?**
*Mein Vorschlag:* **Der Vertrag** (die Feldnamen, die beide lesen) hat genau eine Quelle,
und zwar drüben in `kosmo-contracts`, weil der Cloud-Worker daran hängt. Alles andere darf
kopiert sein — mit einer Probe, die anschlägt, wenn eine Kopie altert.

**🟠 F55 — Wie oft wird abgeglichen?**
Bei jeder Änderung (viel Arbeit, nie überraschend), wöchentlich (pragmatisch), oder nach
Bedarf (läuft auseinander)? *Empfehlung: wöchentlich, mit einem Werkzeug, das die Abweichung
zählt statt sie zu schätzen.*

**🟠 F56 — Wer trägt den Abgleich?**
Ich, wenn ich beide Repos sehe. Heute habe ich beide — bleibt das so?

**🔵 F57 — Was passiert im Februar 2027?**
Beim Zurückschliessen muss entflochten werden, was dann verwoben ist. **Was ich jetzt anders
baue, spart dort Wochen.** *Mein Vorschlag: alles Offene in klar getrennten Dateien halten,
die man als Ganzes verschieben kann.*

---

# 14 · Die Vertiefungsarbeit

**🔴 F58 — Wie lautet die Forschungsfrage?**
Eine Software zu bauen ist keine Forschungsfrage. Was soll die Arbeit **zeigen**, das man
ohne sie nicht wüsste? *Mein Vorschlag, aus dem, was wir schon gemessen haben:* ob sich
Architekturbilder so erzeugen lassen, dass **die Geometrie nachweislich erhalten bleibt** —
das haben wir mit `geometrie_qa` bereits als messbare Grösse. Passt das zu Ihrer Absicht?

**🔴 F59 — Wann ist Abgabe, und in welcher Form?**
Text, Umfang, Bilder, Software als Anhang? Ohne Datum kann ich nicht rückwärts planen, und
alles Weitere in diesem Blatt hängt daran.

**🟠 F60 — Wie viel Zeit geht in die Arbeit statt in die Software?**
Das ist die Falle dieses Vorhabens. *Meine Empfehlung: ab Dezember jede Woche einen festen
Anteil ins Schreiben*, sonst steht im Februar eine gute Software ohne Arbeit daneben.

**🟠 F61 — Wer liest mit, und wann?**
Betreuung durch Gonzalo Casas — gibt es Zwischentermine, auf die ich hin planen soll?

**🔵 F62 — Soll die Arbeit selbst im Repo entstehen?**
*Empfehlung: ja.* Sie wächst dann mit dem Code, statt am Ende aus Protokollen
zusammengesucht zu werden.

---

## Und eine Bitte zum Antworten

**Sie müssen nicht alle 62 beantworten.** Die **🔴 zwanzig** genügen, um anzufangen; bei
allen anderen nehme ich meine Empfehlung und schreibe dazu, dass sie von mir stammt.

Ein Satz je Frage reicht. **„Weiss ich noch nicht" ist eine vollständige Antwort** — dann
steht die Frage als offen da, statt dass ich sie mir still selbst beantworte.
