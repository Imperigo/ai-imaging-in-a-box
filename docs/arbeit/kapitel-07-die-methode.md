# 7 · Die Methode: wie in dieser Arbeit entschieden wurde

> **Stand 19.09.2026 — Entwurf.** Erste geschriebene Fassung eines Kapitels dieser Arbeit.
> Was hier steht, ist aus 29 Sitzungsprotokollen, dem Lexikon und den Auftragsergebnissen
> zusammengetragen; jede genannte Zahl ist im Repo belegt und mit Datum auffindbar.
> **Noch nicht enthalten:** die Kürzung auf Abgabelänge. Je Regel ist ein Fall ausgeführt
> und die übrigen sind genannt — das ist die im Strukturblatt vorgesehene Form, aber sie
> ist noch nicht gegen ein Seitenmass gerechnet.

---

## 7.1 Warum ein Methodenkapitel, und warum dieses

Eine Vertiefungsarbeit, die Software hervorbringt, steht vor einer unangenehmen Frage:
**Was genau ist daran die wissenschaftliche Leistung?** Der Quelltext allein ist es nicht.
Er ist ein Erzeugnis, kein Argument. Und die Messwerte allein sind es auch nicht, denn sie
gelten nur, soweit das Verfahren gilt, das sie hervorgebracht hat.

Diese Arbeit nimmt einen dritten Gegenstand in den Blick: **den Umgang mit dem eigenen
Nichtwissen.** Ein Prototyp, der über Wochen entsteht, der von mehreren Stellen bearbeitet
wird und dessen Messungen auf fremder Hardware stattfinden, produziert fortlaufend
Aussagen, die *niemand geprüft hat*. Die entscheidende Frage ist nicht, ob solche Aussagen
entstehen — sie entstehen unvermeidlich —, sondern **ob sie als ungeprüft erkennbar
bleiben.**

Dafür sind im Verlauf dieser Arbeit fünf Regeln entstanden. Keine davon wurde vorab
aufgestellt. Jede entstand an einem konkreten Fehlschlag, und jede hat danach
**nachweislich eine Entscheidung verändert** — das ist das Auswahlkriterium für alles, was
in diesem Kapitel steht.

Der Nachweis ist möglich, weil das Repo ihn trägt: Jede Sitzung ist protokolliert, jede
Entscheidung mit Begründung, und die Protokolle wurden geschrieben, bevor bekannt war,
welche Regeln sich als tragend erweisen würden. *Ein Methodenkapitel, das nachträglich aus
dem Gedächtnis entsteht, beschreibt die Methode, die man gern gehabt hätte.*

---

## 7.2 Die erste Regel · Die dritte Antwort

> **Nicht messbar ist weder bestanden noch durchgefallen.**

Eine Prüfung kennt üblicherweise zwei Ausgänge. Diese Arbeit besteht auf einem dritten:
**nicht gemessen**. Er ist kein Zwischenwert und keine Unsicherheit, sondern eine Aussage
über die *Messung* statt über den *Gegenstand*.

Der Unterschied ist folgenreich. Ein Bild, dessen Geometrietreue nicht berechnet werden
konnte, ist nicht dasselbe wie ein Bild, das die Schwelle verfehlt hat. Das erste sagt
nichts über das Bild, das zweite alles. Wer beides als «nicht bestanden» ausliefert, hat
eine Information vernichtet, die niemand zurückholen kann.

### Der ausgeführte Fall: das Vertragsfeld, das drüben ankommt

Die erzeugten Bilder werden über eine Schnittstelle an eine fremde Oberfläche übergeben.
Deren Vertrag sieht für jede Kennzahl einen Zahlenwert vor. Die naheliegende Umsetzung —
bei fehlender Messung eine Null einzutragen — wurde verworfen, und zwar mit einer
Begründung, die sich in einem Satz sagen lässt: **Eine Null ist eine gemessene Null.** Sie
bedeutet «die Rangkorrelation beträgt exakt null», also «das Bild folgt der Geometrie
überhaupt nicht» — die schlechtestmögliche Aussage über ein Bild, das in Wahrheit gar
nicht beurteilt wurde.

Ausgeliefert wird darum `null` mit einem eigenen Statusfeld. Die Gegenseite hat das am
17.09.2026 unabhängig bestätigt: In ihrem Vertrag sind alle Zahlenmasse des
Qualitätsblocks als nullbar ausgewiesen, und ihr Statusfeld führt die drei Werte
*gemessen*, *nicht gemessen* und *nicht anwendbar*. **Die dritte Antwort stand auf beiden
Seiten der Schnittstelle, bevor die beiden Seiten voneinander wussten.**

*Weitere Fälle, hier nur genannt:* die Höhenlage einer Kamera, die ohne Geländehöhe nicht
bestimmbar ist; der Massstabsverdacht, der ausdrücklich ein Verdacht bleibt und keine
Umrechnung auslöst; die Gegenprobe gegen eine fremde Geometrie, die bei unvollständiger
Messung **nicht** als «hat getrennt» zählt.

---

## 7.3 Die zweite Regel · Die Mutationsprobe

> **Ein Wächter, der nicht fällt, bewacht nichts.**

Ein Test, der grün ist, beweist nichts. Er beweist erst dann etwas, wenn gezeigt ist, dass
er **rot wird, sobald der Fehler wieder da ist**, gegen den er geschrieben wurde. Das
Verfahren ist simpel: den behobenen Fehler absichtlich wiederherstellen, den Test laufen
lassen, die Änderung zurücknehmen. Bleibt der Test grün, bewacht er etwas anderes als das,
was in seinem Namen steht.

### Der ausgeführte Fall: der Wächter, der den halben Windows-Weg nie sah

Die Software wählt den Ablageort für Modellgewichte je nach Betriebssystem. Für Windows
liest sie eine Umgebungsvariable, und ein Test prüfte, dass sie die richtige nimmt — nicht
die ähnlich benannte, die auf ein synchronisiertes Netzlaufwerk zeigt.

Am 19.09.2026 wurde dieser Test einer Mutationsprobe unterzogen: In der Bibliothek wurde
die richtige Variable durch die falsche ersetzt. **Alle 131 Tests der Datei blieben grün.**

Die Ursache liegt tiefer als der Test. Ein Windows-Pfad gilt auf einem Linux-Rechner als
*unvollständig*; die Prüfung «ist dieser Pfad absolut?» verneinte ihn, der gelesene Wert
wurde verworfen, und was herauskam, war ein Ersatzwert. Der Test prüfte also nicht den
Windows-Zweig, sondern den Rückfall — und das Ergebnis war zufällig brauchbar. *Der
Fehlschlag sah wie ein Erfolg aus*, und genau deshalb fiel er zwei Tage lang nicht auf.

Nach der Berichtigung — die Frage «absolut?» wird nach den Regeln des *gemeinten* Systems
entschieden — fällt die Probe unter derselben Mutation, und zwar zweifach.

*Weitere Fälle, hier nur genannt:* ein Wächter gegen einen Ladeweg, der nur Aufrufargumente
absuchte und die Zuweisungsform übersah; eine Schwelle, die gegen den Grenzfall geprüft
war, aber nicht gegen die Gegenrichtung.

**Eine Falle des Verfahrens selbst** gehört dazu, weil sie zweimal zugeschlagen hat: Wird
die Mutation zurückgenommen und der Test sofort erneut gefahren, kann der Zwischenspeicher
des Interpreters noch die mutierte Fassung halten. Die Probe meldet dann einen Fehler, den
es im Quelltext nicht mehr gibt. Der Zwischenspeicher wird darum vor jeder Probe geleert —
*und dieser Satz stand am 19.09.2026 bereits im Lexikon dieser Arbeit, als der Fehler zum
zweiten Mal passierte.*

---

## 7.4 Die dritte Regel · Vorprüfung gegen tragende Messung

> **Eine Vorprüfung kann ein Mass widerlegen, aber nie tragen.**

Nicht jede Zahl ist gleich viel wert. Ein Mass, das an einem gerenderten Bild oder an
einem Nullanker berechnet wurde, kann zeigen, dass ein Vorschlag **nicht** funktioniert —
es kann nie zeigen, dass er funktioniert. Der Grund liegt in der Richtung der Aussage: Ein
Gegenbeispiel widerlegt, ein Beispiel bestätigt nicht.

### Der ausgeführte Fall: das Mass, das die Abwesenheit belohnt

Die ursprüngliche Geometrieprüfung verrechnete mehrere Kennzahlen zu einem Wert. Drei
Vorprüfungen an eigens konstruierten Fällen haben sie nacheinander widerlegt:

| Konstruierter Fall | Kennzahl | Gemessen | Was das bedeutet |
|---|---|---|---|
| Leeres Grundstück ohne Gebäude | Flächenüberschneidung | **0,9848** | besteht die Prüfung mit grossem Abstand |
| Das perfekte Bild derselben Szene | Flächenüberschneidung | 0,9703 | *schlechter als das leere Grundstück* |
| 2 m gegen 4 m Versatz | zusammengesetzter Wert | 0,1191 gegen 0,2301 | mehr Fehler, besserer Wert |
| Weisses Rauschen gegen 4 m Versatz | zusammengesetzter Wert | 0,7217 gegen 0,8911 | Rauschen liegt nah am groben Fehler |

**Die Kennzahl gehört in diese Tabelle, und ihr Fehlen wäre hier besonders peinlich
gewesen:** Die ersten zwei Zeilen messen die Flächenüberschneidung, die letzten zwei den
zusammengesetzten Wert. Beide in eine Spalte zu schreiben, weil beide «eine Zahl zwischen
null und eins» sind, wäre genau der Fehler, gegen den der vorige Abschnitt argumentiert.
*Der Entwurf dieses Kapitels hat ihn zuerst gemacht.*

Keine dieser Zahlen belegt ein besseres Mass. **Alle zusammen belegen, dass das vorhandene
nicht trägt** — und genau das war ihre Aufgabe. Die Suche nach dem Ersatz musste danach an
echten Läufen stattfinden, nicht an konstruierten Fällen.

*Weitere Fälle, hier nur genannt:* eine Schwelle, die an Bildern aus dem
Geometrieprogramm geeicht und auf erzeugte Bilder angewendet werden sollte — abgelehnt,
weil die Herkunft der Bilder die Zahlen trägt; ein Vorschlag für einen zweiten
Rahmungsriegel, der an einem konstruierten Fall funktionierte und an einem echten nicht.

---

## 7.5 Die vierte Regel · Eine Zahl gehört an ihre Bedingung

> **Eine Zahl ohne ihre Bedingung ist keine Auskunft, sondern eine Behauptung.**

Dieselbe Szene, bei zwei Auflösungen gerechnet, ergibt zwei verschiedene Werte. Dieselbe
Kennzahl, mit zwei Bildmodellen erzeugt, ebenso. Eine Zahl, die ohne Auflösung, ohne
Modell und ohne Schwelle ausgeliefert wird, ist darum nicht vergleichbar — und wer sie
trotzdem vergleicht, misst den Unterschied der Bedingungen statt den der Bilder.

### Der ausgeführte Fall: die Schwelle, die nur an einer Stelle gilt

Am 18.09.2026 wurde für eine neue Prüfung eine Schwelle gesetzt und im Quelltext
begründet: Sie liege in der Lücke zwischen dem Wertebereich unbrauchbarer Bilder
(−0,047 bis +0,055) und dem niedrigsten Wert eines brauchbaren (+0,144).

**Beide Zahlen stimmten. Die Begründung trug trotzdem nicht.** Sie war über zwei von drei
Messreihen desselben Laufs gerechnet; die mittlere war nicht ausgewertet. Dort liegt ein
Bild mit sauber sitzender Silhouette bei **−0,155** — unter dem gesamten Wertebereich der
unbrauchbaren Bilder.

Nachgerechnet, paarweise über dieselben Zellen:

| Vergleich | Ordnung erhalten |
|---|---|
| volle gegen keine Führung | **12 von 12** |
| volle gegen mittlere Führung | **7 von 12** |

An den Rändern ist die Ordnung sauber. **In der Mitte gibt es keine Ordnung, nur
Streuung** — und für eine Schwelle ist die Mitte genau der Bereich, der zählt.

Die Schwelle wurde nicht geändert; geändert wurde, was über sie behauptet wird. Sie gilt
als *gesetzt* und nicht als *kalibriert*, und die Stelle, an der sie im eigenen Datensatz
danebenliegt, steht seither neben ihr. Der Preis ist gezählt statt geschätzt: **Ein
brauchbares Bild von zwölf wird abgewiesen.** Das ist die verzeihliche Richtung — ein
Fehlalarm ist sichtbar, ein Durchlasser nicht —, aber es ist ein ungeklärter Fall.

*Weitere Fälle, hier nur genannt:* eine Stil-Schwelle, die aus Läufen eines Modells stammte
und auf ein anderes angewendet wurde; Zeitgrenzen, die auf einem schnellen Rechner gemessen
und als allgemeingültig geführt wurden.

---

## 7.6 Die fünfte Regel · Der Fehlschlag, der wie ein Erfolg aussieht

> **Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird geglaubt.**

Diese Regel wurde nicht aufgestellt, sondern **gefunden**: beim Zusammentragen der
Beispiele für die vier anderen. Sie erklärt mehr Fälle als jede von ihnen, und sie ist die
einzige, die eine Bauregel nach sich zieht.

Der gemeinsame Bauplan aller Fälle ist derselbe. Eine Prüfung liefert ein Ergebnis, das
*plausibel aussieht*. Sie liefert es aber aus einer Quelle, die den geprüften Gegenstand
gar nicht enthält — einem liegengebliebenen Bericht, einer Dateigrösse, einer Liste, einem
Ersatzwert. Weil das Ergebnis plausibel ist, sucht niemand weiter.

### Der ausgeführte Fall: fünf Testdateien und eine Datei, die es nie gab

Am 19.09.2026 wurde eine Prüfung eingebaut, die eine übergebene Modelldatei ansieht, bevor
gerechnet wird. Beim ersten Lauf wurden **57 Tests einer einzigen Datei rot**, dazu vier
weitere Dateien.

Sie hatten alle recht. Die Testattrappen dieser Dateien schrieben seit jeher acht Bytes:
die Kennung des Formats und eine Fassungsnummer, danach nichts. **Das ist keine gültige
Datei dieses Formats**; ihr fehlen die Längenangabe und der Inhaltsblock.

Fünf Testdateien prüften ihren Weg also an einem Gegenstand, den es so nie gegeben hätte.
Möglich war das nur, weil die geprüfte Stelle selbst nie hineinsah: Sie fragte, *ob* eine
Datei da ist, nicht *was* darin steht.

> **Eine Attrappe, die eine kaputte Sache nachbaut und dabei eine heile meint, prüft die
> falsche Sache — und zwar in einer Richtung, die nie rot wird.**

Daraus folgt die Bauregel, die diese Regel von den anderen unterscheidet: **Jede
Erfolgsmeldung muss an etwas hängen, das unabhängig vom Erzähler ist.** Eine Prüfung, die
ihr Urteil aus derselben Quelle zieht wie der geprüfte Vorgang, prüft nichts — sie
wiederholt.

*Weitere Fälle, hier nur genannt:* ein Bericht eines früheren Laufs, der einen
abgestürzten Lauf gesundmeldete; eine Dateigrösse als Beleg für einen Bildinhalt, der zu
null Prozent vorhanden war; ein Zähler, der Aufträge ohne Antwort zählte und darum nie
meldete, wenn eine Antwort längst dalag.

---

## 7.7 Der gemeinsame Nenner, und er ist schärfer als die fünfte Regel

> **Ein Riegel prüft, ob jedes Element der Wirklichkeit in seiner Liste steht — nicht, ob
> jedes Element seiner Liste in der Wirklichkeit vorkommt. Der zweite besteht immer.**

Dieser Satz stammt nicht aus dieser Arbeit. Er kam am 12.09.2026 von der Messmaschine, aus
einem fremden Projekt, und er fasst vier Fälle zusammen, die vorher als vier verschiedene
Befunde geführt wurden.

Eine Prüfung, die gegen eine **Liste** gebaut ist statt gegen die **Wirklichkeit**, fängt
keine Neuigkeit. Sie bestätigt, was sie kennt. Alle vier Fälle des Monats September haben
diesen Bauplan:

* Ein Zähler, der nur Aufträge *ohne* Antwort kannte, konnte einen Posten mit vorliegender
  Antwort nicht melden — **21 von 23 standen so.**
* Ein Wächter, der eine Diensteinheit als Datei verglich, sah die örtliche Ergänzung
  daneben nicht: Die Datei deckte sich, der Dienst lief anders.
* Ein Zeuge, der nur Wörterbucheinträge kannte, verneinte die Frage «ist das deutsch?» für
  ein Wort, das die Regeln übersetzt hätten.
* Eine Kennzahl lieferte für eine leere Wand und für einen strukturierten Raum dieselbe
  Zahl.

Und im weiteren Verlauf derselbe Bauplan noch einmal, nun auf das eigene Vorgehen
angewandt: **Drei Funde eines einzigen Tages hatten dieselbe Gestalt — etwas war gebaut,
und niemand sah hin.** Eine Reparatur lag dreissig Tage lang zwanzig Zeilen neben der
Stelle, die sie brauchte. Drei fertige Prüfbausteine hatten keinen einzigen Aufrufer. Und
fünf Testdateien prüften an einer Datei, die keine war.

> **Wo nichts hinsieht, kann alles stehenbleiben.**

Für diese Arbeit folgt daraus die schärfste Fassung ihrer eigenen Methode: *Aufgeschriebenes
Wissen wirkt nicht von allein.* Ein Kommentar ist kein Wächter, und ein Lexikoneintrag
auch nicht. Beides ist am 19.09.2026 am selben Tag belegt worden — zweimal, an der eigenen
Arbeit.

---

## 7.8 Die Stelle, an der eine Regel etwas gekostet hat

Eine Methodenbeschreibung ist wohlfeil, solange die Regeln nichts kosten. Ein Fall aus
dieser Arbeit zeigt den Preis.

Am 11.09.2026 bot die Messmaschine die Bildebenen eines laufenden Renderprojekts an — 121
Megabyte, darunter **genau der Tiefenanker mit belegtem Wertebereich, der dieser Arbeit
fehlt.** Er hätte eine offene Frage in Stunden geschlossen.

Abgelehnt. Die Daten stammen aus einem laufenden Wettbewerbsprojekt, und das Repo dieser
Arbeit ist öffentlich. Die dritte Regel des Projekts — keine echten Projektdaten — gilt
auch dann, wenn sie teuer ist.

*Die Stelle, an der eine Regel etwas kostet, ist die, an der sie gilt.* Für die Darstellung
der Randbedingungen in Kapitel 3 ist dies der beste verfügbare Beleg, dass sie nicht
nachträglich zurechtgelegt wurden.

---

## 7.9 Grenzen dieser Methode

Drei Einschränkungen gehören hierher und nicht in eine Fussnote.

**Erstens: Die Fälle sind selbst ausgewählt.** Das Kriterium ist benannt — der Fall muss
eine Entscheidung *gedreht* haben, und es muss sagbar sein, was sonst geschehen wäre —,
aber ausgewählt hat, wer auch entschieden hat. Ein unabhängiger Leser kann die Auswahl
anhand der Protokolle nachprüfen; er kann nicht nachprüfen, was **nicht** protokolliert
wurde.

**Zweitens: Die Regeln sind an einem einzigen Projekt entstanden.** Ob sie über dessen
Gegenstand hinaus tragen, ist nicht gezeigt. Die fünfte Regel hat ihre stärkste
Bestätigung ausgerechnet von aussen erhalten — aus einem fremden Projekt, das denselben
Bauplan unabhängig gefunden hat. Das ist ein Hinweis und kein Beleg.

**Drittens, und es ist die unangenehmste:** Die Regeln haben Fehler nicht verhindert. Sie
haben sie **auffindbar** gemacht. Jeder in diesem Kapitel ausgeführte Fall ist ein Fehler,
der zuerst passiert ist. Wer aus diesem Kapitel liest, dass die Arbeit fehlerarm
entstanden sei, liest es falsch — sie ist fehler**sichtbar** entstanden, und das ist
weniger, aber es ist nachprüfbar.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| 7.2 Die dritte Antwort | `src/aiimaging/kosmo_szene.py`, `docs/METHODE_2026-09-10.md` |
| 7.3 Die Mutationsprobe | `tests/test_render.py`, `docs/LEXIKON.md` (Stichwort *Stale Bytecode*) |
| 7.4 Vorprüfung | `docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`, `docs/EMPFINDLICHKEIT_2026-08-20.md` |
| 7.5 Zahl und Bedingung | `src/aiimaging/geometrie_qa.py` (Schwellenbegründungen), `docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md` |
| 7.6 Fünfte Regel | `docs/sitzungen/2026-09-19_sitzung-29.md`, `tests/test_bruecke.py` |
| 7.7 Gemeinsamer Nenner | `docs/sitzungen/2026-09-12_sitzung-25.md`, `docs/sitzungen/2026-09-19_sitzung-28.md` |
| 7.8 Der Preis einer Regel | `auftraege/offen/auf-20260911-106.json` |
