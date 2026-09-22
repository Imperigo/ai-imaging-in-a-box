# Wie man eine Software von Grund auf baut

> Dieses Blatt erklärt die Grundgedanken, nach denen eine Software entsteht, für
> Leserinnen und Leser, die über ihren Bau entscheiden wollen, ohne selbst zu programmieren.
> Es ist Anhang B der Vertiefungsarbeit (Anhang A ist das Lexikon) und eine Unterlage, nicht
> der Text der Arbeit.

**Grundlage:** keine
**Stand:** 22.09.2026

---

## 0 · Vorweg: was dieses Blatt ist, und wie es zu lesen ist

Eine Software entsteht nicht dadurch, dass jemand lange genug Programmzeilen schreibt. Sie
entsteht aus Entscheidungen: was sie können soll, was sie nie tun darf, wie sie sich in
Teile gliedert, wem man welche Arbeit überlässt und woran man erkennt, dass etwas fertig
ist. Das Programmieren ist davon nur der sichtbarste Teil.

Dieses Blatt handelt von diesen Entscheidungen. Es ist für jemanden geschrieben, der
beurteilen will, **ob** und **wie** etwas gebaut wird, ohne selbst eine Zeile Code zu
schreiben. Es bleibt darum bei den Grundgedanken.

Jeder Grundgedanke wird an einem **echten Fall** erklärt, und zwar an **Visbox**, der
Software dieser Vertiefungsarbeit: Sie übernimmt ein Gebäudemodell, erzeugt daraus mit
einem KI-Bildmodell ein Bild und prüft danach, ob das Bild dem Modell treu geblieben ist
oder ob das Bildmodell etwas dazuerfunden hat. Alle Beispiele stehen mit Datum im Repo, dem
Ordner, in dem die Software samt ihrer ganzen Geschichte liegt (→ Lexikon: Repository
(kurz: Repo)). Viele stammen aus der Woche, in der dieses Blatt entstand, weil sich
Grundgedanken an frischen Fällen am deutlichsten zeigen.

**Wie lesen.** Die zehn Abschnitte bauen lose aufeinander auf, lassen sich aber einzeln
lesen. Ein Fachbegriff wird beim ersten Auftreten in einem Halbsatz erklärt und verweist auf
seinen Eintrag im Lexikon. Am Schluss steht je Abschnitt ein Satz zum Mitnehmen.

**Was dieses Blatt nicht ist.** Es ist Anhang B der Vertiefungsarbeit und ausdrücklich eine
**Unterlage**. Den Text der Arbeit schreibt ihr Verfasser selbst, im Projekt «der Owner»
genannt. Hier steht das Material dazu: was getan wurde, warum, und was offen blieb.

---

## 1 · Erst die Frage, dann der Bau

Bevor ein einziger Baustein entsteht, müssen drei Dinge feststehen. **Die Anforderung**:
was die Software können soll. **Die Randbedingung**: was sie nie tun darf oder immer
einhalten muss, gleichgültig, wie bequem ein anderer Weg wäre. **Das Erfolgskriterium**:
woran man erkennt, dass das Vorhaben gelungen ist, so formuliert, dass jemand anderes es
nachprüfen kann.

Diese drei gehören an den Anfang, weil eine Software am Anfang billig zu ändern ist und
später teuer. Was in der ersten Woche eine Frage ist, ist nach einem Monat eine
Umbauarbeit, weil inzwischen hundert andere Teile darauf aufbauen.

### Die vier Regeln als Randbedingungen

Für Visbox standen am 14.08.2026 vier Regeln fest, bevor eine Zeile Code geschrieben war.
Sie gelten seither als nicht verhandelbar:

1. Alles, was ins ausgelieferte Produkt eingeht, steht unter einer freizügigen Lizenz, also
   unter Bedingungen, die Nutzung und Weitergabe kaum einschränken (→ Lexikon: Permissive
   Lizenz). Modellgewichte, die gelernten Zahlen eines KI-Modells, zählen mit (→ Lexikon:
   Gewichte (Weights)).
2. Blender, ein freies 3D-Programm, mit dem Visbox die Bilder aus dem Modell rechnet, wird
   nur als eigenständiges Programm von aussen aufgerufen, nie in Visbox eingebaut.
3. Keine echten Projektdaten im Repo: keine Bürodaten, keine Kundenprojekte, keine Namen
   davon. Testdaten werden erzeugt, nicht abgelegt.
4. Der Kern ist eine Bibliothek und ohne Oberfläche aufrufbar.

Warum gerade diese vier, erklären die Abschnitte 2 und 4. Hier zählt etwas anderes: **Die
Regeln sind kein Rahmen, in den man hinterher einpasst, was man ohnehin bauen wollte.** Sie
haben die Gestalt der Software hervorgebracht. Ohne Regel 2 gäbe es keine Trennstelle
zwischen Visbox und Blender; ohne Regel 4 wäre die Oberfläche heute die Voraussetzung für
alles andere. Kapitel 3 der Arbeit fasst das in den Satz: Die Randbedingungen sind der
Entwurf.

Eine Randbedingung zeigt sich dort, wo sie etwas kostet. Am 11.09.2026 bot die Maschine, auf
der Visbox misst, die Bildebenen eines laufenden Wettbewerbsprojekts an, darunter genau die
Tiefeninformation, die der Arbeit damals fehlte. Sie hätte eine offene Frage in Stunden
geschlossen. Abgelehnt, weil das Repo öffentlich ist und Regel 3 keine echten Projektdaten
zulässt. *Die Stelle, an der eine Regel etwas kostet, ist die, an der sie gilt.*

### Die kleinste Fassung, die ein Erfolg wäre

Am 18.09.2026 wurde festgelegt, was Visbox mindestens können muss (Entscheid E4): sechs
Schritte, die zusammenhängen. Modell hinein, Kamera setzen, mit Blender rechnen, KI-Bild
erzeugen, ins Bild hineinzeichnen, neues Bild. Alles andere ist Zugabe.

Das Erfolgskriterium dazu lautet: **Eine fremde Person, die die Software zum ersten Mal
öffnet, kommt ohne Hilfe zu einem veränderten Bild.** Dieser Satz ist nachprüfbar. «Die
Software soll gute Bilder machen» wäre es nicht.

Die «kleinste Fassung» erzwingt eine Rangfolge: Was nicht zu den sechs Schritten gehört,
wartet. Und der Entscheid nennt ausdrücklich, **woran er kippen würde**: Bei weniger Zeit bis
zur Abgabe fällt der letzte Schritt zuerst. Jeder der zwanzig Entscheide vom 18.09.2026
trägt eine solche Kippstelle. Sie ist die Stelle, an der jemand widersprechen kann, ohne
alles lesen zu müssen.

Ein gutes Erfolgskriterium zeigt auch, was fehlt. Heute sind die ersten vier Schritte
gebaut, der fünfte zur Hälfte und der sechste nicht, und der Grund ist gemessen: Das
Bildmodell, das Visbox standardmässig verwendet, nimmt überhaupt kein Ausgangsbild an. Ohne
Ausgangsbild gibt es keine Skizze, die hineingereicht werden könnte. Ohne das Kriterium wäre
das eine Randnotiz; mit ihm ist es die wichtigste offene Frage des Projekts.

---

## 2 · Bibliothek und Oberfläche

Jede Software, die ein Mensch bedient, hat zwei Schichten, auch wenn man sie von aussen
nicht auseinanderhalten kann.

Die erste ist der **Kern**: das, was die Software kann. Bei Visbox heisst das, ein Modell
einzulesen, eine Kamera zu setzen, Bilder zu rechnen und sie zu prüfen. Ist dieser Kern so
gebaut, dass andere Programme seine Fähigkeiten aufrufen können, heisst er **Bibliothek**:
eine Sammlung fertiger Fähigkeiten, die man verwendet, ohne dass sie einem den Ablauf
vorschreibt (→ Lexikon: Bibliothek (Library)).

Die zweite ist die **Oberfläche**: das Fenster mit Knöpfen, Reglern und Bildern, über das
ein Mensch die Software bedient (→ Lexikon: GUI (Graphical User Interface)). Eine gute
Oberfläche kann selbst nichts. Sie übersetzt einen Klick in einen Aufruf der Bibliothek und
zeigt an, was zurückkommt.

### Warum die Trennung zählt

Regel 4 verlangt diese Trennung streng: Jede Fähigkeit muss aus einem Programm heraus
nutzbar sein, ohne dass eine Oberfläche läuft. Die Faustregel dazu lautet: **Was nur über
einen Klick erreichbar ist, existiert nicht.** Dafür gibt es drei praktische Gründe.

Erstens können **andere Programme** die Fähigkeiten nutzen. Visbox soll auch in KosmoOrbit
laufen, einer fremden Software, in der man Arbeitsschritte als Kästchen zu einem Ablauf
verbindet (→ Lexikon: KosmoOrbit). KosmoOrbit kann keine Knöpfe drücken; es kann nur
aufrufen, was die Bibliothek anbietet.

Zweitens lässt sich eine Bibliothek **ohne Menschen prüfen**. Ein Prüfprogramm kann jede
Fähigkeit tausendfach aufrufen, ohne dass jemand klickt (Abschnitt 6).

Drittens ändern sich Oberflächen schneller als Fähigkeiten, und oft gibt es mehrere. Liegt
das Können in der Oberfläche, muss es in jeder neuen noch einmal gebaut werden, und die
Fassungen laufen auseinander.

Ob die Trennung hält, wird nicht angenommen, sondern geprüft: Ein Prüfprogramm lädt den Kern
in einer frischen, leeren Umgebung. Kommt dabei irgendein Oberflächenwerkzeug mit, schlägt
die Prüfung an.

### Eine Bibliothek, drei Oberflächen

Am 21.09.2026 stand die Frage, ob die eigene Oberfläche von Visbox und die von KosmoOrbit
zusammenwachsen sollen. Der Owner entschied: getrennt bleiben (Entscheid E22). In KosmoOrbit
ist Visbox **ein Knoten unter vielen**, ein einzelnes Kästchen im Ablauf (→ Lexikon: Node
(Knoten)); in seiner eigenen Oberfläche ist Visbox **das Programm**. Eine Fläche kann nicht
beides zugleich sein.

Inzwischen liegen drei Oberflächen über derselben Bibliothek: eine Webseite, die auf dem
eigenen Rechner läuft (→ Lexikon: Die Oberfläche (von Visbox)); eine App für das iPad, die
gerade entsteht; und KosmoOrbit.

Mehrere Oberflächen haben einen Preis, und der Entscheid schreibt ihn auf: *Zwei Anzeigen
derselben Messung sind zwei Gelegenheiten, sie falsch anzuzeigen.* Die Gegenmassnahme ist
keine gemeinsame Oberfläche, sondern eine gemeinsame **Quelle**: Alle Oberflächen holen
Urteil und Vorbehalt aus der Bibliothek und formulieren keinen eigenen Satz dazu. Auch die
Felder, die man in der Webseite je Arbeitsschritt einstellen kann, stammen aus der
Bibliothek und nicht aus einer Liste in der Oberfläche. Kommt dort eine Einstellung dazu,
erscheint sie hier von selbst.

Die iPad-App treibt den Gedanken am weitesten: Das iPad rechnet **nie** selbst (Owner,
21.09.2026). Es zeichnet, zeigt an und schickt ab. Die Begründung steht in einem Satz: ein
Ort, ein Ergebnis, vergleichbar.

---

## 3 · Bausteine und Schnittstellen

Eine Software von einiger Grösse ist nicht ein Stück, sondern viele. Der kleinste Baustein
ist die **Funktion**: ein benannter Arbeitsschritt, der etwas entgegennimmt und etwas
zurückgibt (→ Lexikon: Funktion). Zusammengehörige Funktionen liegen in einem **Modul**,
einer einzelnen Datei (→ Lexikon: Modul), und mehrere Module bilden grössere Teile, etwa den,
der Bilder prüft, oder den, der mit KosmoOrbit spricht.

Wichtiger als die Bausteine sind die Stellen, an denen sie sich berühren: die
**Schnittstellen**. Eine Schnittstelle legt fest, was hineingeht und was herauskommt, so
dass jede Seite sich darauf verlassen kann, ohne die andere zu kennen. Ist diese Festlegung
schriftlich und verbindlich, heisst sie **Vertrag** (→ Lexikon: Contract (Vertrag)). Ein
Vertrag ist dort unverzichtbar, wo verschiedene Leute an den beiden Seiten bauen.

### Die Kette aus Knoten

Visbox gliedert seine Arbeit in eine **Kette** von Knoten. Vier bilden den Grundablauf: aus
der Gebäudedatei eine Geometrie machen; daraus mit Blender die Bildebenen rechnen, darunter
die Tiefenkarte, die für jeden Bildpunkt sagt, wie weit das Gebäude entfernt ist
(→ Lexikon: Depth-Pass / Tiefenkarte); aus Tiefenkarte und Beschreibung ein Bild erzeugen;
das Bild gegen die Geometrie prüfen. Seit dem 19.09.2026 bringen zwei weitere Knoten ein
vorhandenes, von Hand bearbeitetes Bild in die Rechnung.

Weil jeder Knoten seine Eingänge kennt, muss nicht neu gerechnet werden, was sich nicht
geändert hat. Ändert jemand nur die Beschreibung des Bildes, bleibt die Geometrie, wie sie
war, und Blender wird nicht noch einmal gestartet (→ Lexikon: Zwischenspeicher (Cache) einer
Rechenkette). *Die Frage ist nicht, wie schnell ein Bild entsteht, sondern wie schnell das
zweite.*

### Die Wege des Servers

Die Webseite spricht mit dem Programm auf dem Rechner über eine Handvoll fester Adressen,
eine je Tätigkeit: ein Projekt anlegen, eine Rechnung starten, den Fortschritt abfragen,
eine Skizze ablegen, Einstellungen lesen (→ Lexikon: REST / Endpoint). Jede Adresse ist eine
kleine Schnittstelle. Die Webseite muss nicht wissen, wie das Programm rechnet, nur, an
welche Adresse sie sich wendet und was sie dort abgeben darf.

### Der Vertrag mit KosmoOrbit

Zwischen Visbox und KosmoOrbit gibt es **keinen gemeinsamen Code**, sondern nur zwei Arten
von Dateien: eine Szenenbeschreibung, mit der KosmoOrbit ein Bild bestellt, und ein
Ergebnis, mit dem Visbox Bild und Prüfurteil zurückgibt. Die festgelegte Form dieser beiden
Dateien ist der Vertrag.

Daraus folgt eine unbequeme Regel: **Was im Vertrag kein Feld hat, kommt drüben nicht an,
gleichgültig wie fertig es hier ist** (→ Lexikon: Vertragsfeld). Eine Schnittstelle, die ein
unbekanntes Feld erhält, wirft es oft einfach weg, ohne sich zu beschweren (→ Lexikon:
Stilles Abstreifen (unbekannter Felder)), und wer das Feld geschickt hat, hält es für
angekommen.

### Eine Tatsache an einer Stelle

Aus Schnittstellen folgt eine Grundregel für den ganzen Bau: **Jede Tatsache steht an genau
einer Stelle.** Steht sie an zweien, wird sie irgendwann an einer geändert und an der
anderen vergessen.

Am 22.09.2026 fiel auf, dass die Form der Auftragskennungen von KosmoOrbit dreimal im Repo
stand. Hätte KosmoOrbit die Form geändert, wäre die Änderung an einer Stelle angekommen, und
an einer anderen wären Aufträge **still liegengeblieben**. Heute gibt es eine Quelle, und
alle anderen Stellen fragen sie.

---

## 4 · Fremde Bausteine und Lizenzen

Niemand baut eine Software ganz allein. Jede verwendet fremde Bausteine: zum Lesen von
Dateien, zum Rechnen mit Bildern, zum Betreiben eines KI-Modells. Ein solcher Baustein
heisst **Abhängigkeit**, weil das eigene Programm ohne ihn nicht läuft (→ Lexikon:
Abhängigkeit (Dependency)). Und jede Abhängigkeit bringt ihre **Lizenz** mit, die
Bedingungen, unter denen man sie benutzen darf.

### Freizügig oder ansteckend

Vereinfacht gibt es zwei Familien. **Freizügige Lizenzen** wie MIT, Apache-2.0 oder BSD
erlauben fast alles, auch den Verkauf; verlangt wird im Wesentlichen, dass man die Herkunft
nennt. Visbox selbst steht unter Apache-2.0.

**Ansteckende Lizenzen**, allen voran die GPL, verlangen mehr: Wer einen solchen Baustein in
sein Produkt **einbaut**, muss das ganze Produkt unter dieselben Bedingungen stellen
(→ Lexikon: Copyleft). Das ist kein Makel dieser Lizenzen, sondern ihr Zweck. Für eine
Software, die frei bleiben und zugleich von Büros kommerziell genutzt werden soll, wäre es
aber eine Umwidmung des ganzen Werks durch die Hintertür. Darum verbietet Regel 1 solche
Bausteine im Produkt.

### Warum Lizenzen den Entwurf bestimmen

Lizenzen sind keine Frage für den Schluss. In Visbox haben sie festgelegt, **wo die Grenzen
der Software verlaufen**.

Das deutlichste Beispiel ist Blender. Es steht unter der GPL und ist zugleich das beste
freie Programm, um aus einem Gebäudemodell Bildebenen zu rechnen. Der Ausweg liegt in der
Art der Verwendung: Visbox startet Blender als **eigenständiges Programm**, übergibt ihm eine
Datei und erhält Dateien zurück. Es entsteht kein gemeinsames Werk, sondern ein Nebeneinander
zweier Programme, die sich Dateien reichen. Diese Trennstelle heisst **Prozessgrenze** und
ist die folgenreichste Einzelentscheidung des Projekts (→ Lexikon: Prozessgrenze). Daher
Regel 2: Blender nur von aussen aufrufen, nie als Erweiterung einbauen (→ Lexikon: Add-on /
Plugin). Für das Lesen der IFC-Dateien, des gängigen Austauschformats für Gebäudemodelle
(→ Lexikon: IFC (Industry Foundation Classes)), gilt dasselbe.

Ein in der Bildbearbeitung mit KI weit verbreitetes Werkzeug fiel ganz weg, weil es unter der
GPL steht. Jede Bequemlichkeit, die es mitgebracht hätte, muss Visbox darum von Hand bauen.
Das ist der Preis der Regel, und er ist bezahlt worden.

### Auch Modelle haben Lizenzen

Die Gewichte eines KI-Modells tragen eigene Lizenzen (→ Lexikon: Modellgewichte-Lizenz).
Manche der besten Modelle sind nur für nicht-kommerzielle Zwecke freigegeben (→ Lexikon:
Non-Commercial (NC)). Sie dürfen in Visbox verwendet werden, um zu **messen** und zu
vergleichen, werden aber nie ausgeliefert.

Am 22.09.2026 fiel dazu ein Entscheid, der einen Monat offen gestanden hatte. Zwei weitere
Modelle tragen Lizenzen, die ihre Nutzung erlauben, aber Auflagen machen, die über eine
freizügige Lizenz hinausgehen. Das Programm meldete diese Spannung seit dem 18.08.2026, und
niemand löste sie auf. *Eine Spannung, die man meldet und nicht auflöst, wird nach einem
Monat nicht mehr gelesen.* Der Owner entschied: nur zum Messen, nie ausgeliefert. Eingebaut
wurde das an **beiden** Stellen, an denen ein Modell ins Produkt kommen könnte: wo das
Programm eine Lizenz beurteilt und wo es ein Modell auswählt. Stünde der Entscheid nur beim
Urteil, käme das Modell über die Auswahl trotzdem hinein.

### Deklarieren, nicht verstecken

Jeder fremde Baustein mit ansteckender Lizenz steht in einer eigenen Datei des Projekts
(→ Lexikon: NOTICE) und trägt dort eine **erklärte Auflösung**, etwa «über die
Prozessgrenze». Fehlt sie, schlägt eine Prüfung an. Einmal meldete eine Zweitquelle
freizügig, wo ansteckend steht; Lizenzen werden darum beim Urheber selbst geprüft
(→ Lexikon: Primärquelle / Sekundärquelle).

**Die Ausnahme für Schriften.** Die iPad-App soll ein Bild samt Prüfzeichen teilen. Die
Schrift dafür muss auf dem Gerät liegen, denn eine Schrift von einem fremden Server wäre
eine Netzverbindung, und zum Start darf keine nötig sein. Viele gute Schriften stehen aber
unter der Open Font License, einer Lizenz eigens für Schriften, die in der Liste von Regel 1
nicht vorkommt. Sie erlaubt, Schriften mit einer Software mitzuliefern, verbietet nur den
Verkauf der Schrift für sich allein und bindet Änderungen an der Schrift an dieselbe Lizenz.
Für Schriften hat der Owner darum am 22.09.2026 eine eigene, ausdrücklich benannte
Ausnahme entschieden und in den Regeln des Projekts festgehalten, statt die Regel
stillschweigend zu dehnen. *Eine Ausnahme, die aufgeschrieben ist, ist eine
Entscheidung; eine, die nicht aufgeschrieben ist, ein Versehen.*

---

## 5 · Das Gedächtnis

Eine Software entsteht über Monate, und wer daran arbeitet, vergisst. Sie braucht darum ein
Gedächtnis, das nicht in Köpfen liegt.

### Versionsverwaltung

Das Werkzeug dafür heisst **Versionsverwaltung**; das verbreitetste ist Git (→ Lexikon:
Git). Es hält jede Änderung als **Commit** fest: einen gespeicherten Stand mit Urheber,
Zeitpunkt und einer kurzen Nachricht (→ Lexikon: Commit). Man kann zu jedem früheren Stand
zurückkehren, sieht, wer was wann geändert hat, und kann benennen, auf welchem Stand eine
Messung gemacht wurde.

Gearbeitet wird auf **Zweigen**, Nebenlinien, auf denen eine Änderung entsteht, ohne den
Hauptstand zu stören (→ Lexikon: Branch (Zweig)). Erst wenn sie in sich schlüssig und
geprüft ist, wird sie in den Hauptstand zusammengeführt (→ Lexikon: main).

### Die Nachricht trägt das Warum

Die Hausregel lautet: **Commit-Messages tragen das Warum, nicht das Was** (→ Lexikon:
Commit-Message). Was sich geändert hat, steht ohnehin im Code. Warum, steht nirgends sonst.
Drei Nachrichten aus dieser Woche: «Ein null im fremden Auftrag riss den ganzen Durchgang
mit.» «Zwei Lizenzen, die erlaubt, aber nicht permissiv sind, gehen nicht ins Produkt.»
«Sechs Befunde, deren Fehler niemand sah, weil nichts kaputtging.» Wer in einem Jahr auf
eine dieser Änderungen stösst, erfährt, welcher Fehler dahinterstand.

### Was nicht in einer Datei steht, ist weg

Visbox wird zu einem grossen Teil von KI-Agenten gebaut, Sprachmodellen, die selbständig
Werkzeuge bedienen (→ Lexikon: Agent). Ein Agent arbeitet in einer **Sitzung**, und was er
darin weiss, verschwindet mit ihrem Ende (→ Lexikon: Session (Sitzung)). Für Menschen gilt
dasselbe, nur langsamer.

Darum gilt: **Was nicht in einer Datei steht, ist weg.** Jede Sitzung schreibt ein
Protokoll, bis heute sechsundsechzig. Hinein gehören die Entscheidungen **mit Begründung**,
die korrigierten Fehlannahmen, weil sie sonst wiederkehren, die geprüften Befunde samt dem
Prüfweg, die Fragen des Owners und was offen blieb. Kein wörtliches Gesprächsprotokoll,
sondern die Substanz.

Daneben stehen fortlaufende Blätter: ein Plan, in dem Erledigtes abgehakt und nicht
gelöscht wird; das Lexikon, das jeden neuen Fachbegriff in derselben Sitzung erklärt, in der
er auftaucht; Entscheidblätter, in denen jeder Entscheid seine Kippstelle nennt; und ein
Blatt mit dem Stand der Software, fortgeschrieben in derselben Sitzung, in der gebaut wird.
*Ein Standblatt, das nachgezogen wird, wenn Zeit ist, steht irgendwann auf einem alten
Stand, und ein alter Stand sieht genauso aus wie ein aktueller.*

Ein Gedächtnis hilft allerdings nur, wenn man hineinsieht. Am 22.09.2026 führte eine
Untersuchung eine Frage als «nicht geprüft», deren Antwort seit Langem gemessen im eigenen
Code stand. *Wer im eigenen Repo sucht, bevor er «nicht geprüft» schreibt, spart einen
Auftrag.*

---

## 6 · Prüfen

Eine Software wird nicht dadurch verlässlich, dass man sie sorgfältig schreibt, sondern
dadurch, dass laufend nachgewiesen wird, dass sie tut, was sie soll: automatisch, bei jeder
Änderung, ohne dass ein Mensch daran denken muss.

### Tests und Wächter

Das Mittel dafür ist der **Test**, ein kleines Programm, das ein anderes prüft: Es
beschreibt eine Erwartung und schlägt an, wenn sie verletzt ist (→ Lexikon: Test). Visbox
hat rund siebentausend davon, und alle laufen ohne Grafikkarte. Vor jedem Commit läuft die
ganze Sammlung, nicht nur der Teil, den man für betroffen hält. Am 22.09.2026 wurde das
einmal versäumt, und ein Test blieb rot liegen.

Eine besondere Art von Test heisst im Projekt **Wächter**: Er prüft keine Rechnung, sondern
hält eine **Aussage fest**, die sonst still veralten würde (→ Lexikon: Wächter). Jede der
vier Regeln hat seit dem 26.08.2026 einen. *Was nur im Text steht, veraltet, sobald jemand
eine Zeile schreibt, ohne den Text zu lesen.* Daraus folgt auch: Ein Kommentar im Code, der
eine Regel beschreibt, schützt nichts, denn er verlangt, dass ein Mensch ihn im richtigen
Moment liest (→ Lexikon: Ein Kommentar ist kein Wächter). *Ein Kommentar, der mehr behauptet, als sein
Wächter prüft, ist eine Zusage ohne Deckung.*

### Ein grüner Test beweist nichts

Ein Test, der besteht, sagt zunächst nur, dass er besteht. Ob er den Fehler, gegen den er
geschrieben wurde, überhaupt bemerken könnte, weiss man nicht.

Die Antwort ist die **Mutationsprobe** (→ Lexikon: Mutationsprobe): den behobenen Fehler
absichtlich wieder einbauen, die Tests laufen lassen, die Änderung zurücknehmen. Wird ein
Test rot, bewacht er etwas. Bleibt alles grün, bewacht er nichts, gleichgültig, was in
seinem Namen steht. In dieser Woche wurden so über hundert Proben gefahren. Am Ende fielen
alle; der Weg dorthin war lehrreicher als das Ergebnis.

**Die Attrappe.** Viele Tests können das Echte nicht verwenden: keine Grafikkarte, kein
Blender, keine fremde Software. Sie arbeiten mit einer **Attrappe**, einem Ersatzstück, das
vorhersehbar antwortet (→ Lexikon: Attrappe (Mock)). Das ist legitim, aber ein Baustein, der
nur gegen Attrappen geprüft ist, hat das Echte nie gesehen. Abschnitt 8 zeigt, was daraus
folgt.

### Wirkung statt Text

Tests lassen sich auf zwei Arten schreiben (→ Lexikon: Wirkungsprüfung gegen Textprüfung).
Eine **Textprüfung** liest das Programm wie einen Aufsatz und sucht ein Wort darin. Eine
**Wirkungsprüfung** lässt das Programm laufen und sieht nach, was herauskommt. Nur die
zweite merkt, wenn das Wort noch dasteht, aber nichts mehr tut.

**Die Tür.** Die Webseite von Visbox darf seit dem 21.09.2026 ins Heimnetz, damit das iPad
sie erreicht, aber nur mit Kennwort. Die Anmeldung heisst im Projekt «die Tür». Drei Wächter
sollten sie bewachen; sie lasen den Quelltext und suchten darin die richtigen Stellen. Ein
zweiter Agent wies bei der Durchsicht nach: **Man konnte die Tür aufsperren, und die Wächter
blieben grün.** Heute schicken sie wirkliche Anfragen durch die Tür. Dabei fiel eine zweite
Lücke auf: Die Gegenprobe prüfte nur das Lesen. Eine Tür, die angemeldete Leser durchlässt
und jeden Schreibversuch abweist, hätte alles bestanden, und die Oberfläche wäre unbenutzbar
gewesen.

**Der umbrochene Satz.** Ein Wächter sollte sicherstellen, dass ein Warnsatz nur an einer
Stelle im Code steht. Er zählte dafür eine Zeichenkette im Quelltext und war grün, weil der
Satz dort über zwei Zeilen umbrochen war und die gesuchte Kette gar nicht vorkam. Heute
vergleicht er, was das Programm wirklich ausgibt.

---

## 7 · Die dritte Antwort

Eine Prüfung hat üblicherweise zwei Ausgänge: bestanden oder nicht bestanden. Visbox
besteht auf einem dritten: **nicht gemessen** (→ Lexikon: Dreiwertiges Urteil (ja / nein /
nicht entscheidbar)). Wo nötig, kommt ein vierter dazu: **nicht zutreffend**, für eine
Frage, die sich im gegebenen Fall gar nicht stellt.

«Nicht gemessen» ist kein Zwischenwert, sondern eine Aussage über die **Messung** statt über
den Gegenstand. Ein Bild, dessen Treue zum Modell nicht berechnet werden konnte, ist etwas
anderes als ein Bild, das die Prüfung verfehlt hat. Das erste sagt nichts über das Bild, das
zweite alles.

Der Vertrag mit KosmoOrbit trägt diese Unterscheidung. Jede Kennzahl darf dort ausdrücklich
«nichts» sein (→ Lexikon: Nullbar (nullable)), und ein eigenes Feld sagt, ob gemessen, nicht
gemessen oder nicht zutreffend. Die fremde Seite hatte dieselben drei Werte in ihrem Vertrag,
bevor beide Seiten voneinander wussten. Der Grund ist derselbe: **Eine Null ist eine
gemessene Null.** Bei einer fehlenden Messung null einzutragen hiesse, über ein Bild, das gar
nicht beurteilt wurde, die schlechtestmögliche Aussage zu machen.

### Warum das ständig schiefgeht

In einer Software ist es sehr leicht, einen fehlenden Wert durch einen Ersatzwert zu
ersetzen: «Wenn nichts angegeben ist, nimm null.» Das ist bequem, verhindert jeden Absturz
und ist fast immer unsichtbar. Genau darin liegt die Gefahr: Aus «nicht gemessen» wird still
«in Ordnung», ohne dass jemand das entschieden hätte.

**Die fehlende Neigung wurde zu «lotrecht».** Visbox prüft, ob die Kamera geneigt ist, weil
eine geneigte Kamera stürzende Linien erzeugt. Fehlte die Neigung, setzte ein Baustein null
Grad ein, also die gemessene Aussage «die Kamera steht lotrecht». Auf dem gewöhnlichen Weg,
auf dem man den Standpunkt im Plan anklickt, geschah das **jedes Mal**. Heute bleibt fehlend
fehlend, und das Ergebnis trägt eine eigene Warnung: nicht gemessen.

**Ein «null» schaltete ein Sicherheitstor ab.** Aufträge an die Rechenmaschine tragen eine
Auflage: Gerechnet wird nur, wenn die Grafikkarte gerade frei ist (→ Lexikon:
Leerlauf-Torwächter). Das Programm las diese Auflage mit einem Ersatzwert für den Fall, dass
sie fehlt. Ein solcher Ersatzwert greift aber nur, wenn das Feld **ganz fehlt**. Steht es da
und enthält ausdrücklich «nichts», gewinnt das «nichts», und das Programm las daraus:
Auflage abgeschaltet. **Kein Absturz, keine Meldung**; die Rechnung durfte starten, obwohl
ein fremdes Modell auf der Karte lag. *Eine Sperre, die ein null aufhebt, ist keine Sperre.
Und sie fällt nicht auf, weil nichts kaputtgeht.* Aufgedeckt hat es eine Mutationsprobe.

Dieselbe Falle hatte am selben Tag eine lautere Folge. Die Rechenmaschine holt ihre Aufträge
in regelmässigen Durchgängen aus einer Warteschlange (→ Lexikon: Job / Queue (Auftrag /
Warteschlange)). Ein einziger fremder Auftrag mit einem «nichts» an der falschen Stelle
brachte den ganzen Durchgang zum Absturz, und weil er danach unverändert wartete, stolperte
jeder folgende wieder über ihn. Es war das vierte Mal in zwei Tagen, dass diese Falle
zuschlug. Die Lösung war darum keine vierte Einzelreparatur, sondern eine einzige Stelle je
Datei, die entscheidet: Ein ausdrückliches «nichts» zählt überall wie «nicht gesagt».
*Dreimal ist kein Ausrutscher, viermal ist eine Gewohnheit.*

### Auch Sätze können zu viel behaupten

Die dritte Antwort gilt nicht nur für Zahlen. In einem Fall setzte die Prüfung ihr Urteil
richtig auf «nicht gemessen», der Satz daneben meldete aber weiter einen Wert über der
Schwelle, der Grenze zum Bestehen (→ Lexikon: Schwelle (Grenzwert)). *Ein Satz, der nach
Bestehen klingt, neben einem Urteil, das keines ist, ist schlimmer als gar kein Satz.*

Und sie gilt in beide Richtungen. Die Prüfung meldete bei einem Bild «vorne und hinten
vertauscht». Gemessen war ein Zusammenhang nahe null, also gar keiner, und das ist etwas
anderes als ein umgekehrter. Heute heisst es in diesem Fall «kein messbarer Zusammenhang».

### Angabe und Messung

Verwandt damit ist der Unterschied zwischen einer **Messung**, die das Programm selbst
festgestellt hat, und einer **Angabe**, die ihm jemand mitgeteilt hat (→ Lexikon: Angabe
gegen Messung). Eine von Hand eingetippte Höhe des Geländes ist eine Angabe; an einer Stelle
der Software war sie zum «verlässlichen Bezug» geworden. Der Owner entschied am 22.09.2026:
Sie heisst auf allen Wegen «nicht geprüft» (→ Lexikon: Geländeangabe).

Die Haltung dahinter: Wo ein Zustand nicht feststellbar ist, wird angehalten oder
ausdrücklich gemeldet, nicht geraten. *Ein Fehlschlag, der wie ein Erfolg aussieht, wird
nicht gefunden, er wird geglaubt.*

---

## 8 · Gebaut ist nicht eingebaut

Am 26.08.2026 hat der Owner den Massstab des Projekts verschoben: *«Sorge dafür, dass andere
Worker immer alles einbauen in die Software, das ist Endziel.»* Worker heissen im Projekt die
mitarbeitenden Stellen ausserhalb dieses Repos (Abschnitt 9). Seither ist gebauter Code
**kein Ergebnis mehr, sondern eine Zwischenstufe.** Das Ergebnis ist Code, der dort läuft,
wo er laufen soll: auf dem echten Gerät, in der fremden Software, auf dem Weg, den ein
Mensch wirklich geht.

### Produktweg und direkter Aufruf

Eine Fähigkeit lässt sich auf zwei Arten erreichen. Beim **direkten Aufruf** ruft ein Test
oder ein Entwickler eine Funktion unmittelbar auf und reicht ihr von Hand alles hinein, was
sie braucht. Beim **Produktweg** geht die Anfrage den Weg eines Menschen: über die
Oberfläche, über das Projekt, über den Vertrag mit KosmoOrbit. Eine Fähigkeit kann auf dem
ersten Weg einwandfrei funktionieren und auf dem zweiten nie ankommen. Das ist kein seltener
Sonderfall, sondern der häufigste Fehler dieses Projekts.

### Der dritte Zustand

Für einen Posten, der eingebaut werden soll, gab es lange nur «erledigt» und «offen», und
beide sagen oft etwas Falsches. «Erledigt» behauptet eine Bestätigung, die niemand gegeben
hat; «offen» behauptet Arbeit, die längst getan ist. Darum gibt es einen dritten Zustand:
**gebaut, am Gerät unbestätigt**, hier fertig und dort noch nie ausprobiert (→ Lexikon:
Gebaut, am Gerät unbestätigt). Es ist die dritte Antwort aus Abschnitt 7, angewandt auf den
Einbau.

### Fünf Tage nur Namen

KosmoOrbit soll für jede Kamera ein eigenes Prüfurteil erhalten, und dafür gibt es im
Ergebnis ein Feld. Der Posten stand fünf Tage lang als **erledigt** im Stand des Einbaus,
belegt durch den Vergleich zweier Formen: Was Visbox schickt, passte zu dem, was KosmoOrbit
erwartet.

Am 22.09.2026 zeigte eine Prüfung auf dem Produktweg: Das Feld trug **nur die Namen der
Kameras**, keine Urteile. Das Programm fragte nach einer Angabe, die ein echtes
Kameraurteil nie trägt, und die Tests hatten genau diese Angabe von Hand gesetzt. Der Posten
wurde auf «gebaut, am Gerät unbestätigt» zurückgestuft. *Eine Form, die stimmt, ist kein
Feld, das ankommt.*

### Bestellbar, aber nicht lieferbar

Visbox kann auch Innenansichten rechnen. Am 22.09.2026 wurde das über die Oberfläche
bestellbar gemacht. Die Durchsicht fand, dass es so **nie** geliefert werden konnte: Räume
kennt die Software nur, wenn das Modell als IFC-Datei hereinkommt, und das Projekt rechnete
immer mit einer umgewandelten Datei ohne Räume. Jeder so bestellte Lauf endete mit einem
Fehler (→ Lexikon: Bestellbar, aber nicht lieferbar).

Der erste Test dazu hatte das verdeckt. Er reichte die Räume von Hand hinein, einen Zustand,
den der Produktweg nie herstellt, und sein Name sprach trotzdem vom Produktweg. Noch am
selben Tag wurde die Innenansicht lieferbar gemacht: Die Software liest die Räume jetzt
einmal beim Anlegen des Projekts.

### Angenommen ist nicht gewirkt

Diese Woche wurden Regler für den Sonnenstand und den Bildausschnitt über die Oberfläche
erreichbar. Eine Messung am echten Gerät ergab: Vier Läufe mit drei verschiedenen
Sonnenständen und zwei Bildausschnitten lieferten **dasselbe Bild**, Bildpunkt für
Bildpunkt.

Die Ursachen sind verschieden. Die Sonne wird angenommen und in Blender angewendet, aber das
Standard-Bildmodell sieht nur die Tiefenkarte, und eine Tiefenkarte trägt kein Licht. Das
ist Bauart, kein Fehler; die Oberfläche soll es künftig dazusagen. Der Bildausschnitt
dagegen wirkte nur auf einem von drei Wegen, eine Kamera zu setzen, und stand trotzdem in
jedem Bericht. Das war ein Fehler. Seither steht dort, wo er **wirkungslos** blieb, kein Wert
mehr, sondern der Vermerk samt Grund (→ Lexikon: Wirkungslos (im Bericht)).

Am selben 22.09.2026 lief der Produktweg zum ersten Mal **am echten Gerät ganz durch**, von
der Anmeldung über das Projekt bis zum fertigen, geprüften Bild. Die Prüfung wies dieses
erste Bild ab, und zwar zu Recht. Auch das ist ein Ergebnis: Sie hat auf dem echten Weg
gemeldet, wofür sie gebaut ist.

### Vier Pflichten

Aus dem Auftrag des Owners folgen vier Pflichten. **Verteilen**: Jeder offene Posten hat
einen Adressaten; «niemand» ist keine zulässige Angabe. **Nachhalten**: Der Rückstand wird
gezählt, nicht geschätzt (→ Lexikon: Rückstand gegen Einbau-Stand). **Einbauen
beauftragen**: Ein Messauftrag ist kein Einbauauftrag; der Auftrag muss sagen, was in die
Software kommt. **Bestätigen**: Gemeldet wird, was eingebaut ist, mit Beleg und Datum, und
nicht, was gebaut ist.

---

## 9 · Arbeitsteilung

Visbox wird von einem Menschen gebaut, der entscheidet, und von mehreren KI-Agenten, die
ausführen. Die Rollen sind festgelegt: **Der Owner ist der Visionär und Denker, der Agent
der Ausführer und Spezialist.** Der Owner muss nicht wissen, wie etwas gebaut ist, um zu
entscheiden, ob es gebaut wird.

### Drei Worker, die nicht dasselbe können

Ausserhalb dieses Repos arbeiten drei Stellen mit, die **Worker**, und sie haben
verschiedene Mittel:

* **local**, die Rechenmaschine zu Hause, im Projekt HomeStation genannt: Grafikkarte,
  Blender, echte Modellgewichte. Sie misst, rechnet und prüft.
* **cloud**, der Worker bei KosmoOrbit: Er hat unser Repo nicht, dafür den fremden Vertrag
  und die fremde Warteschlange.
* **ui**, der Worker für die Oberfläche von KosmoOrbit: Er hat unser Repo als Quelle und
  baut dort die ganze Bedienung.

Ein Messauftrag an den Cloud-Worker wäre unerfüllbar, ein Vertragsauftrag an die
HomeStation liefe ins Leere. Darum muss jeder Auftrag seinen Empfänger nennen, sonst wird
er gar nicht erst angelegt.

### Aufträge in Dateien, nicht im Gespräch

Ein Auftrag ist eine **Datei im Repo**, und das Ergebnis kommt als Datei zurück. Seit dem
22.08.2026 trägt der Auftrag seine Anweisung **vollständig in sich**: was zu tun ist, in
welcher Reihenfolge, was zurückkommen soll und was **nicht** getan werden soll. Kein «siehe
Dokument XY», sondern der Inhalt. *Ein Auftrag, der auf etwas verweist, das der Worker erst
suchen muss, ist ein halber Auftrag.* Im Gespräch mit dem Owner steht danach höchstens ein
Satz: dass der Auftrag liegt und was er fragt.

Was eine Grafikkarte oder die echten Gewichte braucht, wird ohne Rückfrage als Auftrag an die
HomeStation abgelegt. *Eine Messung, die hier nicht geht, ist keine offene Frage, sondern
ein unverschickter Auftrag.*

Eine Pflicht wird dabei leicht übersehen: Die HomeStation führt Werkzeuge **aus diesem
Repo** aus. Holt sie den neuen Stand ab, ändert sich dort, was gerechnet wird, ohne dass ein
Auftrag es sagt. Eine solche Änderung wird darum **angesagt, bevor sie ankommt**, sonst sieht
sie drüben aus wie ein Fehler (→ Lexikon: Ansage gegen Messauftrag). Am 22.09.2026 etwa
wurde vorweg angesagt, dass dort ab dem nächsten Abholen zwei Bildmodelle abgelehnt werden.

### Viele Agenten, klare Grenzen

Innerhalb des Repos arbeiten oft mehrere Agenten gleichzeitig. Einer verteilt die Arbeit und
führt die Ergebnisse zusammen (→ Lexikon: Orchestrator), die anderen bearbeiten je eine
abgegrenzte Teilaufgabe (→ Lexikon: Subagent). Damit das trägt, gelten Regeln, die alle aus
Fehlern dieser Woche stammen.

**Jeder nur seine eigenen Dateien.** Lexikon, Plan und Protokoll bleiben beim Verteilenden,
sonst schreiben sechs Agenten gleichzeitig in dieselbe Datei. Auch dieses Blatt ist so
entstanden: ein Agent, eine Datei.

**Erst nachprüfen, dann bauen.** Jeder bauende Agent muss den gemeldeten Befund zuerst selbst
mit einem Lauf nachprüfen und darf nur bauen, was stimmt. Am ersten Tag dieser Regel hat sie
sich zweimal ausgezahlt: Ein Befund stimmte nur zur Hälfte, ein anderer auf dem Produktweg
gar nicht.

**Jede Änderung liest ein Zweiter.** Nach dem Bau liest ein zweiter Agent die Änderung,
**ohne etwas anzufassen**, und urteilt: taugt oder taugt nicht. Am 22.09.2026 gingen sechs
Befunde an sechs bauende Agenten; die Durchsicht befand vier für tauglich und zwei nicht.
Die beiden abgelehnten hatten den Fehler richtig behoben, aber **mehr behauptet, als sie
bewachten**. Schon beim Finden gilt dasselbe: Zu jedem Fund prüft ein zweiter Agent mit dem
ausdrücklichen Auftrag, ihn zu **widerlegen**. Bei einer Suche am selben Tag hielten von
einundzwanzig Funden dreizehn stand. *Ein Befund ohne Gegenprobe ist eine Vermutung mit
Fundstelle.*

**Gegenproben an einer Stelle.** Mutationsproben werden **nicht** im gemeinsamen
Arbeitsstand gefahren, denn wer eine Datei kurz verbiegt, lässt die Tests aller anderen
falsch ausschlagen. Die bauenden Agenten **nennen** ihre Proben nur; gefahren werden sie am
Schluss von einer Stelle aus, eine nach der anderen, jede mit geleertem Zwischenspeicher
(→ Lexikon: Stale Bytecode nach einer Mutationsprobe).

---

## 10 · Erst zeichnen, dann bauen

Für alles, was ein Mensch sieht und bedient, gilt eine eigene Regel, die jüngste des
Projekts. Der Owner hat sie am 21.09.2026 festgelegt: Jede Arbeit an Bedienung und Aussehen
beginnt mit einer Zeichnung.

### Warum zuerst gezeichnet wird

Ein Bildschirm, über den entschieden werden soll, wird zuerst als **Entwurfsblatt**
gezeichnet: ein Bild des Bildschirms in der Grösse des Geräts, mit allem, was man dort sähe
(→ Lexikon: Entwurfsblatt (Artboard)). Das Blatt tut nichts; es zeigt nur.

Fragen zur Bedienung lassen sich an einem Bild stellen: Wo sitzt die Leiste, was geschieht
bei einem Doppeltipp, wie viele Varianten liegen nebeneinander. An einem fertigen Programm lassen sie sich nicht mehr stellen, weil jede
Antwort schon gebaut ist. *Wer erst baut und dann fragt, hat die Antwort schon gegeben.*

### Eine Fläche, nicht viele

Die Blätter liegen nebeneinander auf einer **Entwurfsfläche**, so dass man den ganzen Ablauf
auf einen Blick sieht (→ Lexikon: Entwurfsfläche). Für Visbox gibt es **eine** solche
Fläche, und neue Blätter kommen auf sie. Eine zweite hiesse zwei Stände, von denen einer
still veraltet. Es ist derselbe Gedanke wie in Abschnitt 3: eine Tatsache an einer Stelle.

### Was entschieden wird, kommt ins Repo

Die Fläche trägt das Bild, aber nicht das Gedächtnis. Am 21.09.2026 hat der Owner zwanzig
Fragen zum iPad-Entwurf beantwortet, und die Antworten stehen als eigenes Blatt im Repo.
*Ein Entscheid, der nur in einem Bild steht, ist beim nächsten Öffnen eine Vermutung.*

Einige der Antworten zeigen, dass Entscheide über Bedienung selten nur Bedienung betreffen.
Gezeichnet wird nur mit dem Stift; der Finger schiebt und zoomt. «Zurück» reicht zwanzig
Schritte weit. Jede Ebene einer Zeichnung ist eine Variante, und das zog eine Frage nach
sich, die niemand gestellt hatte: Was wird gerechnet? Festgelegt wurde: **gerechnet wird,
was sichtbar ist**, sonst rechnet das Gerät etwas anderes, als auf dem Schirm steht. Und weil
ein geteiltes Bild sein Prüfzeichen tragen soll, müssen die Schriften auf dem Gerät liegen;
daraus folgte die Lizenzfrage aus Abschnitt 4.

### Ehrlichkeit auch in der Bewegung

Der Owner wünschte sich, dass iPad und Rechner wie ein Werkzeug wirken: Eine abgeschickte
Skizze soll als Bewegung auf dem iPad beginnen und auf dem Rechner weitergehen. Die Regeln
dafür sind die Grundsätze dieses Blattes, angewandt auf eine Animation. **Bewegt sich etwas,
ist etwas unterwegs**; eine Bewegung, die weiterläuft, während nichts geschieht, ist ein
erfundener Fortschritt. **Gleichmässig heisst gezählt**; der Flug läuft nur dort gleichmässig,
wo übertragene Daten wirklich gezählt werden. Und **die Animation endet nicht vor der
Ankunft**, sondern rastet erst ein, wenn die Gegenseite bestätigt hat. *Eine Animation, die
vor der Ankunft endet, behauptet eine Ankunft.* Reisst die Verbindung, fällt die Skizze
zurück aufs iPad; sie verschwindet nie in der Mitte.

Auch das Entscheidblatt zum iPad schliesst mit dem, was noch offen ist, etwa wie gross eine
Skizze werden darf, bevor das Senden spürbar wird. Das lässt sich nur am Gerät beantworten
und ist darum, nach Abschnitt 9, keine offene Frage, sondern ein noch zu verschickender
Auftrag.

---

## 11 · Die zehn Sätze zum Mitnehmen

1. **Erst die Frage, dann der Bau.** Wer vor dem ersten Baustein festlegt, was die Software
   nie tun darf und woran ein Erfolg nachprüfbar zu erkennen wäre, hat den wichtigsten Teil
   des Entwurfs schon gemacht.
2. **Bibliothek und Oberfläche.** Der Kern ist eine Bibliothek, jede Oberfläche eine dünne
   Schicht darüber, und was nur über einen Klick erreichbar ist, existiert nicht.
3. **Bausteine und Schnittstellen.** Zwischen den Teilen stehen schriftliche Verträge, jede
   Tatsache steht an genau einer Stelle, und was im Vertrag kein Feld hat, kommt drüben
   nicht an.
4. **Fremde Bausteine und Lizenzen.** Die Lizenzen fremder Bausteine bestimmen, wo die
   Grenzen der eigenen Software verlaufen, und werden darum vor dem Bau beim Urheber
   geprüft, nicht danach.
5. **Das Gedächtnis.** Was nicht in einer Datei steht, ist weg, und eine Commit-Message
   trägt das Warum, weil das Was ohnehin im Code steht.
6. **Prüfen.** Ein Test, der nie rot werden kann, bewacht nichts; geprüft wird die Wirkung,
   nicht der Text, und die Mutationsprobe zeigt, ob ein Wächter überhaupt wacht.
7. **Die dritte Antwort.** «Nicht gemessen» ist eine eigene Antwort und darf nie still zu
   «in Ordnung» werden, weder als Ersatzwert noch als beruhigender Satz.
8. **Gebaut ist nicht eingebaut.** Fertig ist erst, was auf dem Weg, den ein Mensch
   wirklich geht, am echten Gerät wirkt; alles davor ist «gebaut, am Gerät unbestätigt».
9. **Arbeitsteilung.** Jede Aufgabe geht an den, der sie erfüllen kann, trägt ihre Anweisung
   vollständig in sich, und jedes Ergebnis wird von einem Zweiten gegengeprüft.
10. **Erst zeichnen, dann bauen.** Wer erst baut und dann fragt, hat die Antwort schon
    gegeben; darum wird gezeichnet, bevor gebaut wird, und entschieden wird im Repo.
