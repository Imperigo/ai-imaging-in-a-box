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

*Permissiv heisst **nicht** dasselbe wie „kommerziell erlaubt", und diese Verwechslung ist
in diesem Projekt die folgenreichste. „Kommerziell erlaubt" heisst nur: Geldverdienen ist
nicht untersagt. „Permissiv" heisst darüber hinaus, dass keine weiteren Auflagen mitlaufen
— keine Liste untersagter Anwendungen, keine Umsatzschwelle, keine Schranke für die
Weitergabe. Die Lizenz von Juggernaut XL v9 und die Stability Community License erlauben
kommerzielle Nutzung und sind trotzdem nicht permissiv. Regel 1 verlangt permissiv, nicht
bloss erlaubt. Damit dieselbe Liste nicht in drei Verzeichnissen dreimal verschieden
aufgeschrieben wird, stehen die vier zulässigen Familien an genau einer Stelle im Code
(`PERMISSIVE_LIZENZEN` in `src/aiimaging/lizenzquelle.py`). Was aus dieser Unterscheidung
im Vollzug geworden ist, steht unter* **Regel-1-Spannung** *am Ende dieses Abschnitts.*

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
*In diesem Projekt lange nur an IfcOpenShell festgemacht. Die Prüfung der Binärpakete vom
18.08.2026 hat gezeigt, dass es mehrere sind: **GEOS** reist im Paket `shapely` mit,
**libquadmath** in `numpy`, **Open CASCADE** in IfcOpenShell — und keines dieser Pakete
nennt die LGPL in seiner kurzen Lizenzangabe
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §4.2 und §4.7). Die drei Auflagen aus
`CLAUDE.md` — hinter einer Prozessgrenze, unverändert, austauschbar und deklariert — waren
dabei zweimal ohne Zutun erfüllt; geschuldet war allein die Deklaration im `NOTICE`.*

**Ausnahmeklausel (Lizenzausnahme)** — Ein Zusatz, mit dem ein Urheber sein eigenes
Copyleft für einen bestimmten Fall selbst zurücknimmt. Die Lizenz bleibt formal GPL, aber
der genannte Fall löst die Ansteckung nicht aus. Wer nur den Lizenznamen liest, sieht
„GPL" und erschrickt; wer den Zusatz mitliest, sieht, dass er nicht gemeint ist.

**GCC Runtime Library Exception** — Die wichtigste dieser Ausnahmen. Der weit verbreitete
Übersetzer GCC legt in jedes Programm, das er übersetzt, ein paar kleine
Hilfsbibliotheken hinein — etwa `libgomp`, damit ein Programm mehrere Rechenkerne nutzen
kann. Diese Hilfsbibliotheken stehen unter der GPL. Ohne Ausnahme wäre also jedes mit GCC
übersetzte Programm GPL, was niemand will und auch nie gemeint war. Die Ausnahme sagt
darum: Wer sie bloss mitliefert, weil sein Übersetzer sie hineingelegt hat, darf sein
Programm unter Bedingungen seiner Wahl weitergeben.
*In diesem Projekt betrifft das `libgomp` und `libgfortran`, die in den Wheels von `torch`
und `numpy` mitreisen, ohne dass deren Lizenzangabe sie erwähnt. Sie stehen als GPL-Zeile
im `NOTICE` — mit der Ausnahme daneben, damit ein späterer Prüfer den Fund findet **und**
seine Entwarnung. `libquadmath` aus demselben numpy-Wheel hat diese Ausnahme dagegen
**nicht**: Es steht unter der LGPL, und dort gelten die drei Auflagen aus `CLAUDE.md`
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §4.2).*

**MPL-2.0 (Mozilla Public License)** — Copyleft auf **Dateiebene**. Nur veränderte
Dateien der Bibliothek müssen offen bleiben; der eigene Code in eigenen Dateien nicht.
Ein Mittelweg, mit permissiven Projekten gut verträglich.

**CDDL (Common Development and Distribution License)** — Ebenfalls Copyleft auf
Dateiebene und der MPL im Aufbau sehr ähnlich: Veränderte Dateien der Bibliothek bleiben
offen, eigener Code in eigenen Dateien nicht. Ursprünglich von Sun Microsystems für
Solaris geschrieben, heute vor allem im Java- und .NET-Umfeld anzutreffen.
*In diesem Projekt die Lizenz des xbim Toolkit, einer .NET-Bibliothek für IFC. Die
Prüfung vom 18.08.2026 bestätigt „CDDL" wörtlich — der Lizenztext nennt aber **keine
Versionsnummer**, die verbreitete Angabe „CDDL-1.0" ist also plausibel und unbelegt
(`docs/LIZENZPRUEFUNG_2026-08-18.md`, §3.8).*

**Dual License (Doppellizenz) / Lizenzwahl** — Dasselbe Werk unter zwei Lizenzen. Das
bekannte Muster ist das kaufmännische: kostenlos unter Copyleft, gegen Geld unter einer
kommerziellen Lizenz. *Beispiel: CGAL.*

Es gibt aber auch die Doppellizenz **zwischen zwei offenen Lizenzen**, und die verlangt
eine Entscheidung des Benutzers. **FreeType**, die Schriftbibliothek in jedem
Pillow-Paket, liegt unter der FreeType License **oder** der GPL-2.0-or-later, und ihr
eigener Text sagt wörtlich, man müsse eine von beiden wählen. Wer nicht wählt, hat nicht
beide, sondern nichts Bestimmtes — und müsste im Streitfall erst erklären, unter welcher
er das Werk benutzt hat. *Für dieses Projekt ist die Wahl leicht, weil die GPL unter
Regel 1 ausscheidet; sie bleibt aber eine Wahl, und die FreeType License bringt eine
Nennungsauflage mit — das Projekt muss in der Produktdokumentation erwähnt werden
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §4.3).*

**Contributor License Agreement (CLA)** — Eine Vereinbarung, die Beitragende
unterschreiben, bevor ihr Code angenommen wird: Sie räumen dem Projekt das Recht ein,
ihren Beitrag auch unter anderen Bedingungen weiterzugeben. Ohne ein solches Abkommen
gehört jedem Beitragenden ein Stück des Werks, und niemand könnte es später neu
lizenzieren — deshalb hängt ein CLA meist an einer Doppellizenzierung.
*In diesem Projekt gestreift bei Open WebUI, das eines verlangt
(`docs/LIZENZPRUEFUNG_2026-08-18.md`, §3.6).*

**OpenRAIL++-M** — Lizenz von Stable Diffusion XL. Erlaubt kommerzielle Nutzung, knüpft
sie aber an Nutzungsauflagen: bestimmte Anwendungen sind untersagt, und die Auflagen sind
weiterzugeben. Nicht permissiv im Sinn von Regel 1, aber auch kein Copyleft.

**CreativeML OpenRAIL-M** — Die ältere Schwester der vorigen Lizenz, aus der
Stable-Diffusion-1.x-Linie. Gleiches Prinzip — kommerzielle Nutzung erlaubt, bestimmte
Anwendungen untersagt —, aber ein anderer, älterer Text. Die beiden Namen unterscheiden
sich nur durch zwei Pluszeichen und werden deshalb verwechselt.
*Belegt am 18.08.2026: Die Registry der Bildmodelle (`src/aiimaging/backbone.py`)
führte für den Rückfall-Backbone „OpenRAIL++-M"; die Modellkarte von Juggernaut XL v9 sagt
`creativeml-openrail-m`, also die ältere Variante
(`docs/LIZENZPRUEFUNG_2026-08-18.md`, §3.1). An Regel 1 ändert das nichts — beide sind
nutzungsbeschränkt und keine der vier permissiven Lizenzen —, aber ein falscher Name in
der `NOTICE`-Datei ist eine falsche Angabe. Dieselbe Karte trägt ausserdem eine
Zusatzschranke des Anbieters **oberhalb** der Lizenz: kein Betrieb hinter einem
kostenpflichtigen Dienst. Sie steht nur im Fliesstext und in keinem Lizenzbezeichner.*

**Stability Community License** — Lizenz von SD3.5. Frei nutzbar unterhalb einer
Umsatzschwelle (1 Mio USD), darüber kostenpflichtig. Kommerziell nutzbar, aber nicht
bedingungslos — eine Einschränkung, die man beim Wachsen bemerkt.

**Non-Commercial (NC)** — Nutzung nur ohne Erwerbszweck. Trotz offenem Zugang **kein**
Open Source im Sinne der OSI. *Beispiel: FLUX.1-dev.*

**OSI (Open Source Initiative)** — Organisation, die anerkannte Open-Source-Lizenzen
führt. „Nicht OSI-konform" heisst: offen zugänglich, aber mit Auflagen, die echte
Weiterverwendung einschränken.

**Proprietär** — Der dritte Fall neben permissiv und copyleft: Software, deren Quelltext
nicht offenliegt und deren Benutzung ein Vertrag regelt, den allein der Hersteller
schreibt. Nicht dasselbe wie „kostenpflichtig" — die NVIDIA-Bibliotheken sind gratis zu
haben und trotzdem proprietär. Für eine Lizenzprüfung ist das die unbequemste Kategorie,
weil sie durch jedes Raster fällt, das nur permissiv und copyleft kennt: Es gibt kein
Kürzel, das man nachschlagen könnte, sondern nur einen Vertragstext, den man lesen muss.

**EULA (Endnutzer-Lizenzvertrag)** — Genau dieser Vertragstext: ausformulierte Prosa statt
eines Kurzbezeichners wie „MIT", oft dutzende Seiten lang, mit Auflagen, die eine
Open-Source-Lizenz gar nicht kennt.
*In diesem Projekt am 18.08.2026 gelesen statt vermutet: Jedes `nvidia-*`-Paket bringt
einen NVIDIA-Vertrag von 59 200 Zeichen mit. Drei seiner Auflagen betreffen ein
öffentliches Repo unmittelbar — die Bibliotheken dürfen nicht für sich weitergegeben
werden, sondern nur eingebettet in eine eigene Anwendung; Zurückübersetzen ist untersagt;
und eine eigene Klausel verbietet, die Software so zu benutzen, dass sie **unter eine
Open-Source-Lizenz fiele**. Letzteres ist ein sehr konkretes Verbot, CUDA und eine
GPL-Komponente in dasselbe Programm zu legen — und die Prozessgrenze, die dieses Projekt
aus ganz anderen Gründen gezogen hat, erfüllt es von selbst. Das ist ein nachträgliches
Argument für eine früher getroffene Entscheidung, und es gehört festgehalten
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §4.4).*
*Der Umfang, damit niemand das für eine Randnotiz hält: Ein `pip install torch` zieht auf
Linux **zwingend** rund anderthalb Gigabyte solcher Dateien nach — kein Zusatz, keine
Option.*

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

**Gebündeltes Binary (mitgelieferte Fremdbibliothek)** — Ein fertiges Paket, das nicht nur
den eigenen Code enthält, sondern fremde Bibliotheken gleich mit — als übersetzte Datei,
nicht als lesbaren Quelltext. Zwei Formen: **statisch eingebunden** heisst, die fremde
Bibliothek steckt unsichtbar in einer grossen Datei des Pakets; **mitgeliefert** heisst,
sie liegt als eigene Datei daneben. In beiden Fällen kommt sie mit ihrer eigenen Lizenz —
und in beiden Fällen schweigt die Lizenzangabe des Pakets darüber oft.

*Deshalb sagt die Lizenzangabe eines Pakets nichts über seinen Inhalt, und das ist keine
Vermutung, sondern das Ergebnis der Prüfung vom 18.08.2026: `numpy` gibt sich als BSD und
liefert zwei GNU-Bibliotheken mit, eine unter GPL mit Ausnahme, eine unter LGPL;
`shapely` gibt sich als BSD und liefert GEOS unter LGPL mit; `triton` gibt sich als MIT
und liefert rund 90 Megabyte an proprietären NVIDIA-Werkzeugen mit; `ifcopenshell` gibt sich als
LGPL und hat CGAL unter GPL-3.0 statisch eingebaut. In fünf von fünf geprüften Paketen mit
nennenswertem Binäranteil wich die Kurzangabe von dem ab, was wirklich drin lag. Die
Merkregel des Berichts: **Die Kurzangabe eines Pakets ist ein Hinweis, sein
Lizenzverzeichnis eine Aussage, und der Ordner mit den mitgelieferten Bibliotheken die
Wahrheit** (`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §2 und §7).*

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

**Primärquelle / Sekundärquelle** — Die **Primärquelle** ist das Original: bei einer
Lizenz die `LICENSE`-Datei des Projekts selbst oder der vom Lizenzgeber veröffentlichte
Vertragstext. Eine **Sekundärquelle** ist jede Angabe *über* das Original — ein
Blogeintrag, eine Übersichtstabelle, die Antwort einer Suchmaschine, auch die eigene
Notiz von letzter Woche. Sekundärquellen sind bequem und meistens richtig; genau das ist
ihre Gefahr.

**Ein Fehler in dieser Kette fällt nie von selbst auf.** Er hat zwei Richtungen, und sie
sind verschieden teuer: Wird etwas Freizügiges strenger geführt als es ist, kostet das
einen ungenutzten Baustein. Wird umgekehrt etwas Copyleft-Behaftetes als permissiv
geführt, verhält sich alles unauffällig — bis das Produkt ausgeliefert ist. Nichts im
Betrieb widerspricht einer falschen Lizenzangabe; kein Test schlägt an, kein Programm
stürzt ab.
*Belegter Fall vom 18.08.2026: Die Lagebeurteilung führte Krita AI Diffusion als „MIT".
Die `LICENSE`-Datei des Projekts ist der vollständige Text der GPL-3.0 — die
Sekundärquelle lag nicht ungenau, sondern glatt falsch, und in die gefährliche Richtung.
Von 35 prüfbaren Positionen stimmten 30; dieser eine Fehltreffer wiegt schwerer als die
Quote (`docs/LIZENZPRUEFUNG_2026-08-18.md`, §3.2 und Kap. 6). Seither gilt im Projekt:
Lizenz vor Technik, und zwar gegen die Datei des Herausgebers, nicht gegen eine
Suchmaschine.*

**Regel-1-Spannung** — Der Name, den dieses Projekt einem Widerspruch gegeben hat, der
nicht in einer Lizenz steckt, sondern in ihrer **Anwendung**: Zwei Verzeichnisse desselben
Projekts messen dieselbe Art von Lizenz verschieden streng.

*Der Fall, ausgeschrieben (18.08.2026):* `src/aiimaging/einbetter.py` schliesst das Modell
**DINOv3** aus, wörtlich mit der Begründung „Regel 1 verlangt permissiv, nicht bloss
erlaubt". `src/aiimaging/backbone.py` lässt **sdxl-juggernaut** und **sd35-large** zu.
Alle drei erlauben kommerzielle Nutzung, keines der drei ist permissiv — gleiche Lage,
entgegengesetztes Urteil.

Das ist **keine Auslegungsfrage einer Lizenz, sondern eine Uneinheitlichkeit im Vollzug**:
Nicht der Vertragstext ist unklar, sondern die eigene Praxis. Der Unterschied ist deshalb
wichtig, weil er sagt, wer die Sache lösen kann — eine unklare Lizenz braucht eine
Auskunft, ein uneinheitlicher Vollzug einen Entscheid. Hier ist es ein Owner-Entscheid,
denn ein Ausschluss nähme dem Projekt sein Rückfallmodell, und das ist keine
Aufräumarbeit.

*Bis dahin wird der Widerspruch nicht verschwiegen, sondern ausgesprochen: Die Funktion
`regel_1_spannung` (`src/aiimaging/lizenzquelle.py`) hängt ihn an **jede** einzelne
Lizenzauskunft an, statt ihn in einem Bericht abzulegen, den später niemand mehr liest.
Das ist die allgemeine Lehre dieses Eintrags — ein bekannter, aber unaufgelöster
Widerspruch gehört dorthin, wo gearbeitet wird, nicht in die Ablage.*

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

**Standardbibliothek (stdlib)** — Die Sammlung von Bausteinen, die schon mit Python
mitkommt: Dateizugriff, Zahlenformate, Packen, Prüfsummen. Sie muss nicht installiert
werden und bringt keine fremde Lizenz mit. *In diesem Projekt eine Entwurfsvorgabe und
nicht nur Bequemlichkeit: `src/aiimaging/bildlesen.py` und `src/aiimaging/bildschreiben.py`
lesen und schreiben EXR und PNG allein damit — jede zusätzliche Fremdbibliothek wäre eine
neue Lizenzfrage.*

**Heuristik** — Eine Faustregel, die schnell eine brauchbare Antwort liefert, ohne alle
Möglichkeiten durchzurechnen und ohne zu versprechen, dass die Antwort die beste ist. Man
nimmt sie, wenn die genaue Lösung unverhältnismässig teuer wäre und ein guter
Näherungswert genügt.

**API (Application Programming Interface)** — Die vereinbarte Schnittstelle, über die
Programme miteinander sprechen: welche Aufrufe es gibt, welche Angaben sie erwarten,
was zurückkommt. Nicht die Umsetzung, sondern der Vertrag darüber.

**Nullbares Feld (nullable)** — Ein Feld einer Schnittstelle, das ausdrücklich auch
*leer* sein darf — im Vertrag als „Text **oder** nichts" geschrieben statt nur als „Text".
Das ist keine Nachlässigkeit, sondern eine Aussage: Es gibt einen ehrlichen Fall, in dem
es diesen Wert nicht gibt. *In diesem Projekt:* `job_id` und `status` der Werkzeugnaht
sind nullbar, weil ein Auftrag, der gar nicht erst angelegt wurde — abgewiesen vom
Torwächter, fehlende Geometriequelle —, weder Kennung noch Zustand hat; der Grund steht
dann in `error`. Wer das Feld als nicht-nullbar zusagt, erzeugt beim Empfänger einen
Schemafehler *anstelle* der Ursache, die die Antwort eigentlich mitbringt — genau das war
bis zum 18.08.2026 der Fall.

**CLI (Command Line Interface)** — Bedienung über eingetippte Befehle im Terminal statt
über Fenster und Knöpfe. Für Automatisierung unverzichtbar, weil ein Befehl
wiederholbar und skriptbar ist.

**GUI (Graphical User Interface)** — Die grafische Oberfläche.

**Headless** — Ein Programm ohne grafische Oberfläche betreiben. *In diesem Projekt:
`blender --background` rendert, ohne dass ein Fenster aufgeht.*

**Fabrikfunktion** — Eine Funktion, die keine Antwort liefert, sondern eine **andere
Funktion** — vorkonfiguriert mit Dingen, die man ihr nicht bei jedem Aufruf mitgeben will.
*Hier nötig, weil ein geladenes Modell nicht in die Knotenparameter passt: Die werden
gehasht und müssen dafür als Text darstellbar sein.*

**Closure** — Eine Funktion, die sich Werte aus ihrer Entstehungsumgebung merkt. Das ist
der Mechanismus hinter der Fabrikfunktion: Die zurückgegebene Funktion „weiss" noch,
welches Modell ihr mitgegeben wurde, ohne es als Parameter zu führen.

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
installiert werden. Sie gehören nicht zur Laufzeit des Produkts. *In diesem Projekt zwei:
`dev` für die Testwerkzeuge und `mcp` für die Anbindung an KosmoOrbit (`pyproject.toml`).
Der Kern selbst hat **null** Laufzeitabhängigkeiten — er ist reine Standardbibliothek.*

*Berichtigt am 18.08.2026: Hier stand bisher, „alles Schwere" liege jenseits der
Prozessgrenze in eigenen Environments. Das stimmt nicht, und die Prüfung der Binärpakete
hat es gemessen. Jenseits der Prozessgrenze liegt, was **copyleft** ist — Blender und
IfcOpenShell. `torch`, `diffusers`, `transformers` und `Pillow` werden im
Produkt-Environment importiert, wenn auch erst innerhalb der Ladefunktion
(`src/aiimaging/render.py`), und mit ihnen kommt über ein Gigabyte NVIDIA-Dateien ins
selbe Environment. Die Grenze trennt nach Lizenz, nicht nach Gewicht
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §1).*

**SPDX** — Ein standardisiertes Kürzelverzeichnis für Lizenzen (`Apache-2.0`, `MIT`,
`GPL-3.0-or-later`). Erlaubt es, Lizenzen maschinenlesbar anzugeben, statt sie in Prosa
zu umschreiben.

**Abhängigkeit (Dependency)** — Fremde Software, die das eigene Programm zum Laufen
braucht. Jede Abhängigkeit bringt ihre Lizenz mit — deshalb ist die Abhängigkeitsliste
zugleich eine Lizenzliste.

**Transitive Abhängigkeit** — Die Abhängigkeit einer Abhängigkeit: nichts, was man selbst
ausgesucht hat, aber alles, was mitkommt. Für die Lizenzprüfung zählt sie genauso, denn
installiert wird sie ebenso. *In diesem Projekt der Grund, warum die MCP-Anbindung
optional bleibt: Das MCP-Paket selbst ist MIT, zieht aber 19 weitere Pakete nach, die
nicht einzeln geprüft sind (`pyproject.toml`). Und der Grund, warum ein
`pip install torch` auf Linux über ein Gigabyte proprietärer Dateien installiert, ohne
dass irgendwo „NVIDIA" getippt worden wäre.*

**pip** — Das Installationswerkzeug für Python-Pakete.

**PyPI (Python Package Index)** — Das zentrale Verzeichnis, aus dem `pip` lädt. Wer dort
etwas veröffentlicht, gibt Name, Fassungsnummer und Lizenz selbst an; niemand prüft nach.

**Platzhalterpaket** — Ein Paket, das auf PyPI existiert, aber nichts enthält: Es belegt
nur einen Namen, damit ihn kein anderer bekommt. Wenige Kilobyte, meist in der Fassung
`0.0.1`, mit einer beliebig eingetragenen Lizenz — geprüft hat die niemand, weil es nichts
zu prüfen gibt.
*Der Fund vom 18.08.2026, und er ist lehrreich: Unter dem Namen `nvidia-cublas-cu13` liegt
ein **1371 Byte** grosser Platzhalter, der `Apache-2.0` deklariert. Die Bibliothek cuBLAS
selbst heisst `nvidia-cublas`, ist 410 Megabyte gross und NVIDIA-proprietär. Wer eine
Lizenzliste aus Paketnamen oder aus den PyPI-Angaben erzeugt — die übliche, bequeme
Methode —, liest für cuBLAS „Apache-2.0" und übersieht den Endnutzervertrag vollständig.
Es ist derselbe Fehler wie bei Krita AI Diffusion und in dieselbe Richtung: permissiv
gemeldet, wo es nicht permissiv ist. Nur diesmal ohne fremdes Zutun — es genügt, dass zwei
Pakete beinahe gleich heissen.*

**Metapaket** — Ein Paket ohne eigenen Inhalt, dessen einziger Zweck es ist, andere Pakete
nachzuziehen. Beim Installieren bequem, beim Prüfen unangenehm: Es trägt oft gar keine
Lizenzangabe, und was es hereinholt, sieht man erst, wenn man seine Abhängigkeitsliste
liest. *In diesem Projekt `cuda-toolkit`, über das `torch` elf einzelne NVIDIA-Pakete
nachzieht.*

**Wheel** — Ein vorkompiliertes Python-Paket. Praktisch, weil nichts übersetzt werden
muss — aber undurchsichtig, weil fertige Binärteile mitgeliefert werden, deren Herkunft
man nicht sieht. *Genau daraus entstand die CGAL-Frage in diesem Projekt.* Technisch ist
ein Wheel nichts weiter als ein ZIP-Archiv: Man kann hineinsehen, ohne es zu installieren
— und man muss es, denn was drinliegt, deckt sich nicht zwangsläufig mit dem, was
draufsteht (siehe *gebündeltes Binary* in Abschnitt 2).

**`dist-info` (Metadatenverzeichnis)** — Der Ordner, den `pip` beim Installieren neben dem
Paket anlegt und der alles über das Paket sagt, was nicht Code ist: Name, Fassung,
Lizenzangabe, Abhängigkeitsliste und im Unterordner `licenses/` die beigelegten
Lizenztexte. Er ist die erste Adresse für die Frage, unter welcher Lizenz etwas steht.

Darin sind drei Angaben zu unterscheiden, und sie sind verschieden viel wert: der
**Klassifikator** (ein Eintrag aus einer festen Auswahlliste, etwa „License :: OSI
Approved :: MIT License" — grob, und oft das Einzige, was da ist), die **Lizenzangabe** in
der Datei `METADATA` (ein Kurzbezeichner wie `MIT`, siehe *SPDX*) und die **beigelegten
Lizenzdateien**, also die Verträge selbst. *In der Prüfung vom 18.08.2026 fehlte bei
`tokenizers` sogar die eigene Lizenzdatei im Paket, und bei `numpy` nannte keine der drei
Angaben die zwei GNU-Bibliotheken, die `pip` tatsächlich mitinstalliert.*

**Symbol / Symbolverweis** — In einer übersetzten Programmdatei stehen die Namen der
Funktionen und Datenstücke, die sie enthält oder von anderswo braucht; ein solcher Name
heisst **Symbol**. Sie überleben das Übersetzen, weil die Teile eines Programms sich
darüber wiederfinden müssen — und werden dadurch zum Nachweismittel: Wer in einer Datei
von 155 Megabyte 249-mal den Namen `Nef_polyhedron_3` findet, weiss, dass die
CGAL-Komponente dieses Namens darin steckt, auch wenn keine Lizenzdatei sie erwähnt.
*So ist der GPL-Fund in IfcOpenShell belegt worden — am 14.08.2026 am Paket, am 18.08.2026
an der installierten Datei nachgemessen, mit denselben Zahlen; sie stehen im `NOTICE`.
Was ein Symbolverweis belegt, ist allerdings nur, dass etwas **da** ist — nicht, in
welchem Umfang es benutzt wird.*

**Versionen festschreiben („pinnen")** — In der Abhängigkeitsliste nicht „irgendeine
Fassung von torch" verlangen, sondern genau eine (`torch==2.13.0`). Ohne Festschreibung
installiert jeder Rechner und jeder Tag etwas anderes.
*Für dieses Projekt ist das keine Ordnungsfrage, sondern die Haltbarkeitsfrage jeder
Lizenzprüfung: Geprüft wurde, was ein **bestimmtes** Paket enthält. Die nächste Fassung
desselben Pakets kann eine andere Bibliothek bündeln, **ohne dass sich die deklarierte
Lizenz ändert** — genau das ist ja der Befund. Eine Lizenzprüfung ohne festgeschriebene
Version ist deshalb eine Momentaufnahme mit Verfallsdatum
(`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, §7). Im Projekt ist bisher nichts
festgeschrieben, weil `pyproject.toml` keine Laufzeitabhängigkeiten führt — die Frage ist
damit nicht beantwortet, sondern nur auf den Tag verschoben, an dem sie eingetragen
werden.*

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

**Timeout (Zeitgrenze)** — Eine Frist, nach der ein Aufrufer aufgibt und den Vorgang für
gescheitert erklärt. Sie ist nötig, weil ein Programm, das nicht antwortet, sonst ewig
Wartezeit bindet. *In diesem Projekt: `subprocess.run(..., timeout=…)` in `seams.py`.*

**Gesamt-Timeout gegen Fortschrittsfrist** — Zwei verschiedene Fristen mit sehr
verschiedenem Nutzen. Der **Gesamt-Timeout** begrenzt die ganze Dauer („nach 30 Minuten
ist Schluss"). Die **Fortschrittsfrist** begrenzt die Zeit *ohne erkennbares Vorankommen*
(„wenn sich fünf Minuten lang nichts rührt, stimmt etwas nicht"). Die zweite meldet
dieselbe Auskunft viel früher — aber nur, wenn es etwas gibt, woran sich Vorankommen
ablesen lässt. *`src/aiimaging/fortschritt.py`.*

**Stillstand (Stall / Hänger)** — Ein Vorgang, der weder fertig wird noch abstürzt: Der
Prozess lebt, die Grafikkarte ist belegt, und es geschieht nichts mehr. Der unangenehmste
Fehlerfall, weil er sich von aussen genau wie *sehr langsam* anfühlt. *Ein Absturz meldet
sich; ein Stillstand nicht.*

**Behauptetes gegen belegtes Fortschrittszeichen** — In diesem Projekt die Unterscheidung,
an der die Stillstandserkennung hängt. Ein **behauptetes** Zeichen ist ein Statuswort:
„läuft" sagt nur, dass jemand das behauptet. Ein **belegtes** Zeichen kommt aus etwas, das
sich unabhängig davon bewegt — ein Schrittzähler, der zählt, eine Datei, die wächst, eine
neue Datei im Ausgabeordner. Aus einem unveränderten Statuswort lässt sich *langsam* nicht
von *hängend* trennen; aus einer Datei, die seit fünf Minuten nicht mehr wächst, schon.
*Darum darf ein bloss behaupteter Stillstand höchstens warnen und nie einen Fehler melden
— dieselbe Regel wie beim* **Belichtungsrahmen** *in Abschnitt 5.*

**GIL (Global Interpreter Lock)** — Eine Sperre im Python-Kern, die dafür sorgt, dass
immer nur **ein** Faden zugleich Python-Anweisungen ausführt. Wer rechenintensiven
Python-Code in mehrere Fäden verteilt, gewinnt darum nichts. Eine in C oder C++
geschriebene Bibliothek darf die Sperre aber **freigeben**, solange sie rechnet — dann
laufen andere Python-Fäden weiter.
*Am 20.08.2026 gemessen und entscheidend: Cycles gibt die Sperre während des Renderns
frei. Ein gewöhnlicher Faden läuft darum weiter, während `bpy.ops.render.render()` den
Hauptfaden blockiert — 61 Schläge in 118 Sekunden, während die beiden dokumentierten
Blender-Haken (`render_stats`, `bpy.app.timers`) **null** Mal feuerten.*

**Rückruf (Callback)** — Eine Funktion, die man einer fremden Bibliothek *übergibt*,
damit sie sie zum passenden Zeitpunkt selbst aufruft. Man sagt also nicht „gib mir
Bescheid, wenn du fertig bist", sondern „ruf das hier bei jedem Schritt".
*In diesem Projekt: `callback_on_step_end` von `diffusers` — der einzige Weg, während
eines Bildlaufs zu erfahren, wie weit er ist. Nicht jede Pipeline kennt ihn; welche, wird
an ihrer Signatur abgelesen und im Ergebnis **gemeldet**, denn ein Rückruf, der nie
gerufen wird, sieht von aussen genauso aus wie ein hängender Lauf.*

**Diffusionsschritt** — Ein Rechenschritt bei der Bilderzeugung: Aus einem verrauschten
Bild wird schrittweise das Rauschen entfernt, bis das Motiv übrig bleibt. Mehr Schritte
heissen mehr Rechenzeit und meist mehr Detail.
*Wichtig und leicht zu übersehen: Im **Bildbearbeitungs**modus rechnen viele Pipelines
nur `schritte × denoise` — bei 20 bestellten Schritten und einem `denoise` von 0,6 also
zwölf. Der Auftrag nennt die bestellte Zahl; wer zwei Läufe über die Schrittzahl
vergleicht, vergleicht unter Umständen etwas anderes als gedacht. `schritte_gerechnet`
im Ergebnis nennt darum die wirklich gelaufene Zahl — und `None`, wenn sie ungemessen ist.*

**Lebenszeichen gegen Fortschrittszeichen** — Zwei Dinge, die leicht verwechselt werden
und sehr verschieden viel behaupten. Ein **Lebenszeichen** belegt, dass ein Vorgang noch
*da* ist: Der Prozess lebt, etwas rührt sich. Ein **Fortschrittszeichen** belegt, dass er
*vorankommt*.
*In diesem Projekt schreibt der Blender-Runner ein Lebenszeichen (`herzschlag.txt`) und
ausdrücklich kein Fortschrittszeichen: Ein festgefahrener Renderkern, der den Prozess
nicht mitnimmt, schlägt weiter. Der Umkehrschluss trägt aber — ein **ausbleibender**
Herzschlag heisst zuverlässig, dass der Prozess tot oder eingefroren ist —, und nur auf
ihn schlägt die Wache an.*

**Monotone Uhr (monotonic clock)** — Eine Uhr, die nur vorwärts läuft und nie springt, im
Gegensatz zur *Wanduhr*, die durch Zeitumstellung oder Zeitabgleich rückwärts gehen kann.
Für Zeitmessungen („wie lange läuft das schon") ist die monotone Uhr die richtige — eine
rückwärts gestellte Wanduhr ergäbe negative Laufzeiten. *`time.monotonic()`; in
`fortschritt.py` ist sie zusätzlich austauschbar, damit sich eine Frist von fünf Minuten
prüfen lässt, ohne fünf Minuten zu warten.*

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
*Die eigenen liegen unter `src/aiimaging/runners/`: `ifc_to_glb_runner.py` ruft
IfcOpenShell im `.venv-ifc` auf, `blender_depth_stage.py` und `blender_exr_lesen.py`
laufen in Blender. Die früher hier genannten `glb_export_runner.py` und
`export_ifc_runner.py` gehören **nicht** zu diesem Projekt, sondern zu KosmoDraw — sie
sind das Vorbild, nicht der Bestand (`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`).*

**Protokoll** — Eine Vereinbarung darüber, in welcher Form zwei Programme miteinander
sprechen: welche Nachrichten es gibt, in welcher Reihenfolge, in welchem Format. Nötig,
wenn die Gegenseite nicht im Voraus weiss, was sie erwartet — überflüssig, wenn ein
schlichter Aufruf genügt. *MCP ist ein Protokoll, ein Subprozessaufruf braucht keines.*

**Umgebungsvariable** — Eine Einstellung, die dem Programm von aussen mitgegeben wird —
üblicher Ort für Pfade und Geheimnisse, die nicht in den Code gehören.

**JSON** — Ein schlichtes Textformat für strukturierte Daten. Für Mensch und Maschine
lesbar, deshalb das übliche Austauschformat zwischen Prozessen.

**Markdown** — Eine Schreibweise, mit der sich eine gewöhnliche Textdatei gliedern lässt,
ohne Textverarbeitung: `#` macht eine Überschrift, `*` eine Aufzählung, Sternchen ringsum
eine Hervorhebung. Die Datei bleibt im Editor lesbar und wird von Werkzeugen zugleich als
formatierter Text angezeigt. *Sämtliche Dokumente dieses Projekts — dieses Lexikon
eingeschlossen — sind Markdown-Dateien (`.md`). Deshalb liegen sie in derselben
Versionsverwaltung wie der Code und lassen sich Zeile für Zeile vergleichen.*

**Front-Matter (Kopfblock)** — Ein Block am Anfang einer Markdown-Datei, oben und unten
durch eine Zeile aus drei Bindestrichen abgetrennt, der Angaben **über** die Datei
enthält statt Text für den Leser: Titel, Sprache, Urheber — oder eben die Lizenz.
Programme lesen ihn maschinell aus; beim Anzeigen wird er meist ausgeblendet, weshalb man
ihn leicht übersieht. *In diesem Projekt die Stelle, an der die Lizenz eines Modells
steht: Die Zeile `license: apache-2.0` im Front-Matter einer Modellkarte ist die Angabe,
die Hugging Face auswertet und anzeigt. Sie kann dem Fliesstext derselben Karte
widersprechen — bei Juggernaut XL v9 tut sie es —, und bei einem gesperrten Modell ist
sie das Einzige, was ohne Anmeldung lesbar bleibt (`docs/LIZENZPRUEFUNG_2026-08-18.md`;
siehe* **Modellkarte** *und* **Gated Model / Gated Repository** *in Abschnitt 6).*

**Schema** — Die formale Beschreibung, wie eine Datenstruktur auszusehen hat: welche
Felder verpflichtend sind, welchen Typ sie haben. Macht Verträge zwischen Programmteilen
prüfbar.

**Parsing** — Das Zerlegen einer Datei in eine für das Programm nutzbare Struktur.

**Lesefenster** — Von einer grossen Datei absichtlich nur den Anfang lesen, statt sie ganz
in den Speicher zu holen. Das lohnt sich, wenn das Gesuchte vorne steht: In einer
IFC-Datei stehen Kopf und Einheitenzuweisung am Anfang, weil alles Weitere darauf
verweist. Eine solche Datei kann hunderte Megabyte haben; gelesen werden zwei
(`LESEFENSTER_BYTE` in `src/aiimaging/herkunft.py`).

Der Preis ist eine Zweideutigkeit, und sie muss ausgesprochen werden: **„im gelesenen
Anfang nicht gefunden" ist nicht dasselbe wie „nicht vorhanden".** Das eine ist eine
Aussage über die eigene Suche, das andere eine über die fremde Datei. Wer beides gleich
meldet, macht aus einer Grenze des eigenen Verfahrens einen Befund über fremde Daten —
dieselbe Verwechslung wie zwischen „nicht lesbar" und „gibt es nicht" bei den
*HTTP-Statuscodes* weiter unten. *`lies_ifc_kopf` gibt darum das Feld
`vollstaendig_gelesen` mit zurück und hängt an eine abgeschnittene Lektüre eine
ausdrückliche Warnung an, die genau diesen Satz enthält.*

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

**HTTP-Statuscode** — Die dreistellige Zahl, mit der ein Webserver jede Anfrage
beantwortet, noch bevor er Inhalt liefert. `200` heisst „hier ist es", `404` „gibt es
nicht", `401` „du bist nicht angemeldet", `403` „angemeldet oder nicht — du darfst
nicht". *Die Unterscheidung entschied in der Lizenzprüfung vom 18.08.2026 über die
Aussage: `401` bei einem Modell heisst, dass die Lizenzdatei existiert und eine
Zustimmung fehlt; kein Treffer in der Suche heisst, dass es sie gar nicht gibt — so
geschehen bei Depth-Anything-V2-Giant, dessen Gewichte öffentlich schlicht nicht
vorliegen. Beides sieht von aussen nach „nicht lesbar" aus und ist doch etwas ganz
anderes (`docs/LIZENZPRUEFUNG_2026-08-18.md`, Kap. 0 und §3.5).*

**Range-Abruf (HTTP Range)** — Von einer Datei im Netz nur einen benannten Bereich
anfordern statt der ganzen Datei — das *Lesefenster* über die Leitung.
*In diesem Projekt das Mittel, mit dem die Binärprüfung vom 18.08.2026 in Pakete von
mehreren hundert Megabyte hineinsehen konnte, ohne sie herunterzuladen oder zu
installieren: Ein Wheel ist ein ZIP-Archiv, und ein ZIP trägt sein Inhaltsverzeichnis am
Ende. Man holt also erst das Ende, liest dort, an welcher Stelle die Lizenzdateien liegen,
und holt dann nur diese. Das ist die härteste erreichbare Quelle — nicht eine Angabe
**über** das Artefakt, sondern das Artefakt selbst.*

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

**Charakterisierungstest** — Ein Test, der festhält, wie sich etwas **heute** verhält,
ohne zu behaupten, dass dieses Verhalten richtig ist. Der Unterschied zum gewöhnlichen
Test steckt im Anspruch: Der gewöhnliche prüft eine Zusage und hat recht, wenn er bricht;
der Charakterisierungstest schreibt einen Ist-Zustand auf, damit dessen Änderung
überhaupt auffällt — und damit die Grenze eines Verfahrens in einer Zahl steht statt in
einem Nebensatz. *In diesem Projekt etwa
`test_glaettung_ist_ein_stumpfes_instrument` (`tests/test_schwellenstudie.py`): Er hält
fest, dass acht Mittelungsdurchgänge über der Testszene den Geometrie-Score um weniger
als ein Hundertstel bewegen. Sein Docstring beginnt mit den Worten „Befund, nicht Zusage"
— genau das macht ihn zum Charakterisierungstest. Niemand behauptet, dass es so sein
soll; festgehalten ist, dass es so ist, und wer die Kurven der Schwellenstudie deutet,
muss es wissen.*

**Rückwärtskompatibilität** — Die Zusage, dass Neues mit Altem weiter zusammenarbeitet:
Eine neue Programmfassung liest, was die alte geschrieben hat, und versteht die bisherigen
Aufrufe. Wird sie aufgegeben, muss man es merken können — siehe den nächsten Eintrag.

**Stiller Bruch** — Ein Kompatibilitätsbruch, der sich *nicht* als Fehlermeldung zeigt,
sondern als falsches Ergebnis. Das Programm läuft weiter und liefert Unsinn, und niemand
wird gewarnt. *Belegter Fall in diesem Projekt: Blender 5.2 lädt eine mehrschichtige EXR
als Bild von 0 × 0 Bildpunkten mit 0 Kanälen, statt den Ladevorgang scheitern zu lassen —
obwohl es dieselbe Datei kurz zuvor selbst geschrieben hat. Wer nur auf einen Abbruch
wartet, bemerkt nichts; die Tiefenkarte wäre still leer geblieben. Beschrieben im
Kopf von `src/aiimaging/runners/blender_depth_stage.py`.*

**Referenzimplementierung** — Diejenige Umsetzung eines Verfahrens, die im Streitfall
recht hat: Weichen zwei Programme voneinander ab, gilt ihr Ergebnis als das richtige, und
das andere muss sich erklären. *In diesem Projekt seit dem 18.08.2026
`src/aiimaging/bildschreiben.py` für die Normalisierung der Tiefenkarte — vorher war es
Blender. Der Wechsel ist bewusst: Die Blender-Zahlen exakt nachzubauen hiesse, die
Reihenfolge fremder Rechenschritte nachzuahmen, die niemand zusichert — das wäre
vorgetäuschte statt echter Genauigkeit.*

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

**Traceback** — Die Liste der Aufrufe, die zu einem Abbruch geführt haben; das, was
Python beim Absturz ins Terminal schreibt. Beim Suchen nützlich, aber flüchtig: Er steht
nicht in der Ergebnisdatei und ist nach dem Lauf verloren.

**Attrappe (Mock)** — Ein Ersatzstück, das im Test die Stelle eines echten Bausteins
einnimmt und vorhersehbar antwortet. *Erlaubt, den Stil-Score zu prüfen, obwohl das
Einbettungsmodell hier gar nicht vorhanden ist.*

**Vakuöser Test** — Ein Test, der besteht, weil die geprüfte Lage nie eintritt — etwa die
Prüfung „FLUX erscheint nicht in der Auswahl", wenn FLUX gar nicht in der Registry steht.
Er sieht grün aus und bewacht nichts. Abhilfe ist eine Gegenprobe, die belegt, dass der
Fall überhaupt vorkommen könnte.

*Die zweite Bauart desselben Fehlers, gefunden am 18.08.2026: Ein Test suchte das Wort
„geprüft" in einer Liste von Auflagen und war zufrieden, als er es fand — nur stand es in
einem Eintrag, der mit der geprüften Sache nichts zu tun hatte. Der Test bestand also aus
dem falschen Grund, und er hätte auch bestanden, wenn die Auflage, um die es ging, ganz
gefehlt hätte. Abhilfe war hier keine Gegenprobe, sondern ein eindeutiges Merkmal: Die
betroffenen Hinweise beginnen jetzt alle mit einer festgelegten Vorsilbe
(`HERKUNFT_HINWEIS_PRAEFIX` in `src/aiimaging/lizenzquelle.py`), damit ein Test sie
erkennen kann, ohne auf ein Wort zu setzen, das anderswo ebenfalls vorkommt. Merksatz: Ein
grüner Test beweist nur, dass die Bedingung erfüllt war, die dort steht — nicht, dass es
die gemeinte war.*

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

**Fail-open** — Das Gegenstück: Bei einer Störung wird weitergemacht statt angehalten.
Vertretbar nur dort, wo das Hauptergebnis auch ohne den gestörten Teilschritt gültig
bleibt — sonst entsteht genau das halbe Ergebnis, das gültig aussieht (siehe
*Skip-on-Error*).

**Laufzettel** — Die kleine Datei, die neben einem Auftrag liegt und seinen **Zustand**
führt: Wer ihn gestellt hat, ob er wartet, läuft, fertig ist oder gescheitert.
Beim Ökosystem heisst sie `job.json`. Sie ist nicht der Auftrag selbst — der steht
daneben in `render-scene.json` — sondern der Zettel, auf dem der Bearbeitungsstand
mitgeschrieben wird. *Wer ihn liest, weiss, was zu tun ist; wer ihn fortschreibt, sagt
allen anderen, dass er es tut.*

**Waise (verwaister Auftrag)** — Ein Auftrag, der auf „läuft" steht, den aber niemand
mehr bearbeitet: Der Rechner ging mitten im Lauf aus, und der Laufzettel blieb stehen,
wo er war. Von aussen sieht das genau aus wie ein sehr langer Lauf.
*Erkannt an der Änderungszeit des Laufzettels und nicht an einem Feld darin — ein Feld
müsste jemand fortschreiben, und genau dieser Jemand ist im Waisenfall gestorben. In
diesem Projekt werden Waisen **gemeldet und nicht neu eingereiht**: Ein zweiter Lauf
kostet eine GPU-Stunde und kann ein zweites Bild unter derselben Kennung erzeugen.*

**Befund als Feld statt Absturz** — Die Form, in der dieses Projekt fail-open umsetzt:
Ein gescheiterter Teilschritt bricht den Lauf nicht ab, sondern schreibt seinen Grund in
ein eigenes Feld des Ergebnisberichts. *`_tiefe_nachbearbeiten` in
`src/aiimaging/seams.py` legt bei einem Fehler `depth_png_fehler` an und lässt den
Blender-Lauf gelten: Die EXR mit den echten Metern ist das massgebliche Ergebnis, das PNG
nur ihre Ableitung für das Bildmodell. Der Unterschied zum Verschweigen ist, dass der
Grund in einer Datei steht und nicht bloss in einem Traceback im Terminal.*

**Rauchprobe (Smoke Test)** — Die kürzeste Prüfung, die feststellt, ob etwas
*überhaupt* läuft — nicht, ob es richtig rechnet. Der Name kommt aus der Elektronik: Man
schaltet ein Gerät zum ersten Mal ein und sieht nach, ob Rauch aufsteigt. Eine Rauchprobe
beantwortet „ist der Weg da?", ein ausführlicher Test beantwortet „stimmt das Ergebnis?".
*Im Projekt:* Ein Multipass-Auftrag mit 96 Bildpunkten Kantenlänge und vier Strahlen je
Punkt (`tests/test_multipass.py`) ist eine Rauchprobe — er belegt, dass die Prozessgrenze
zu Blender trägt, und sagt nichts über Bildqualität. Auch die ersten fünf Aufträge an die
HomeStation waren Rauchproben: Sie fragten nur, ob der Kompositor überhaupt durchschreibt.

**Metrik (Messgrösse)** — Eine Zahl, die aus Daten berechnet wird, damit etwas
vergleichbar wird, das man sonst nur beurteilen könnte. Eine Metrik ersetzt kein Urteil:
Sie sagt „0,84", nicht „gut". Was „0,84" bedeutet, muss eigens festgestellt werden —
siehe *Kalibrierung*. *In diesem Projekt gibt es zwei: den Stil-Score
(`src/aiimaging/stil_qa.py`) und den Geometrie-Score (`src/aiimaging/geometrie_qa.py`).*

**Schwelle (Grenzwert)** — Die Zahl, ab der eine Metrik als bestanden gilt. Sie ist nicht
Teil der Messung, sondern eine Entscheidung darüber, wo „gut genug" anfängt. *In diesem
Projekt `SCHWELLE_GEOMETRIE = 0,65` und `SCHWELLE_STIL = 0,30`. Beide sind an wenigen
Einzelfällen gesetzt und nicht hergeleitet worden — der Grund, warum es die
Schwellenstudie überhaupt gibt.*

**Kalibrierung** — Den Zusammenhang zwischen einer Messgrösse und dem, was sie bedeuten
soll, an Fällen festmachen, deren Antwort man bereits kennt. Eine Waage kalibriert man mit
bekannten Gewichten, nicht mit unbekannter Fracht. Kalibrieren heisst dabei nicht
zwangsläufig, eine bessere Zahl zu finden — zuerst heisst es, die Frage überhaupt messbar
zu machen: Bei welcher Art und Stärke von Abweichung reagiert die Metrik, und wie stark?
*In diesem Projekt `src/aiimaging/schwellenstudie.py`: Eine bekannte Soll-Tiefenkarte wird
in bekannter Art und bekannter Stärke verfälscht, und gemessen wird, wie der Score darauf
antwortet. Das Ergebnis steht in `docs/SCHWELLENSTUDIE_2026-08-18.md`.*

**Validierung (eines Verfahrens)** — Die Gegenprobe zur Kalibrierung: prüfen, ob das
ausgerichtete Verfahren auch dort taugt, wo es angewandt werden soll — an Fällen, die beim
Ausrichten nicht dabei waren. Wer beides an denselben Fällen tut, hat nur geprüft, ob er
sich selbst zugehört hat. *In diesem Projekt noch offen und ausdrücklich so benannt: Die
erste Schwellenstudie kalibriert an synthetischen Störungen und ohne Tiefenschätzer;
validiert wäre die Schwelle erst an echten Renders — die zweite Hälfte, siehe
`docs/SCHWELLENSTUDIE_2026-08-18.md`, Kapitel 6. Genau darum bleibt 0,65 vorerst stehen,
obwohl 0,90 auf der Studienszene besser trennt.*
*Nicht zu verwechseln mit* **Validierung** *in Abschnitt 8 — dort die Prüfung von Daten
gegen ihr Schema; gleiches Wort, anderer Sachverhalt.*

**Setzung vs. Messung** — Eine Zahl kann zweierlei Herkunft haben: Entweder hat jemand sie
festgelegt (Setzung), oder sie stammt aus Daten (Messung). In einer Tabelle sehen beide
gleich aus, sie tragen aber verschiedene Beweislast — eine Messung kann falsch sein, eine
Setzung kann nur unpassend sein; widerlegen lässt sie sich nicht. Wird der Unterschied
nicht mitgeschrieben, wird aus einer Verabredung stillschweigend ein Befund. *In diesem
Projekt darum durchgängig kenntlich gemacht: Dass eine Störung bis zur Stärke 0,2 noch als
„treu" gilt, ist eine Setzung; sie heisst `grenzstaerke` und steht in jedem Ergebnis von
`trennschaerfe_kurve` (`src/aiimaging/schwellenstudie.py`), damit niemand sie für ein
Naturgesetz hält. Auch die Schwelle 0,65 ist eine Setzung —
`docs/SCHWELLENSTUDIE_2026-08-18.md` nennt sie deshalb „nicht verteidigt, sondern
beibehalten".*

**Belegt / vermutet / unbekannt** — Drei Stufen, in denen eine Auskunft gegeben werden
kann, und sie gehören zusammen mit der Auskunft ausgeliefert. **Belegt** heisst: Die
Quelle sagt es selbst, und man kann es nachsehen. **Vermutet** heisst: Es spricht etwas
dafür, aber die Quelle sagt es nicht. **Unbekannt** heisst: nichts davon. Der Sinn der
Dreiteilung ist, dass eine Vermutung sonst mit der Zeit zur Tatsache wird, ohne dass
jemand sie je geprüft hätte — sie steht in derselben Tabellenspalte wie ein Beleg und
sieht dort genauso aus.

*In diesem Projekt an zwei Stellen tragend. Erstens in der Connector-Schicht
(`src/aiimaging/herkunft.py`, die Werte `BELEGT`, `VERMUTET`, `UNBEKANNT`): Dass eine
IFC-Datei Z-oben ist, folgt aus der Norm — belegt. Dass eine glTF-Datei aus Blender Y-oben
ist, folgt aus der Gewohnheit des Exportprogramms — vermutet. Dass eine glTF-Datei aus
Rhino Y-oben ist, folgt aus gar nichts, denn dort entscheidet beim Export ein Schalter,
von dem die Datei nichts mitteilt — unbekannt. Und die Folge ist hart: `fordere_up_axis`
nimmt einen belegten Wert an, eine Vermutung dagegen **nicht**; sie wird in der
Fehlermeldung genannt, damit ein Mensch sie bestätigen kann. Eine Vermutung, die sich
selbst durchwinkt, ist ein Vorgabewert mit besserer Begründung.*
*Zweitens in den Modell-Verzeichnissen, dort für die Herkunft einer Lizenzangabe: am
Original geprüft, nur aus zweiter Hand bekannt, oder ungeprüft
(`src/aiimaging/lizenzquelle.py`).*

*Verwandt mit* **Setzung vs. Messung** *im vorigen Eintrag, aber nicht dasselbe: Dort geht
es darum, **woher** eine Zahl kommt — festgelegt oder gemessen —, hier darum, **wie gut**
eine Aussage gestützt ist. Eine Setzung kann belegt sein, wenn nachweislich jemand sie so
beschlossen hat, und eine Messung kann von unbekannter Herkunft sein. Die beiden Fragen
werden nebeneinander gestellt, nicht nacheinander.*

**Störung / kontrollierte Verfälschung (Perturbation)** — Eine absichtlich eingebrachte
Abweichung, deren Art und Stärke man selbst bestimmt. Der Sinn liegt darin, die Antwort
schon zu kennen: Wer weiss, was er verändert hat, kann prüfen, ob das Messverfahren es
bemerkt — und ob es das Richtige bemerkt. *In diesem Projekt acht Arten in `STOERUNGEN`
(`src/aiimaging/schwellenstudie.py`), jede einer wirklichen Fehlerart eines Bildmodells
nachgebildet: Rauschen, Silhouette verbreitern, Silhouette abtragen, die Karte verschieben,
Detail glätten, einen Baukörper hinzuerfinden, nah und fern vertauschen, die Tiefe streng
monoton umrechnen. Jede Art trägt eine **Erwartung**, welchen Anteil des Scores sie treffen
soll — damit ist jede Störung eine Vorhersage, die zutreffen oder scheitern kann, statt
bloss eine weitere Kurve.*

**Nullprobe** — Der Messpunkt ganz ohne Störung. Sie sagt nichts über den Gegenstand,
sondern über das Messverfahren: Zeigt schon sie etwas anderes als das Erwartete, ist jede
weitere Zeile der Messreihe wertlos — dann wird nicht die Störung gemessen, sondern ein
Fehler im Vergleich. *In diesem Projekt gehört die Stärke 0,0 darum fest zu
`VORGABE_STAERKEN` (`src/aiimaging/schwellenstudie.py`): Die unverfälschte Karte, mit sich
selbst verglichen, **muss** den Score 1,000 ergeben. Jede Zeile der Studie wird ausserdem
gegen ihre eigene Nullprobe gehalten und nicht gegen einen angenommenen Idealwert.*

**Kontrolle (im Experiment)** — Ein mitgeführter Fall, dessen Ergebnis vorher feststeht.
Er misst nicht den Gegenstand, sondern das Verfahren — und gehört deshalb getrennt
ausgewiesen und nicht in die Auswertung der übrigen Fälle eingerechnet. *In diesem Projekt
zwei, beide in `STOERUNGEN` mit `ist_kontrolle=True` markiert: `monoton` (eine
rangerhaltende Umrechnung darf den Score nicht bewegen — tut sie es doch, ist nicht die
Schwelle falsch, sondern die Metrik kaputt) und `tiefenumkehr` (vertauschte Tiefenordnung;
der Score benutzt bewusst den Betrag der Rangkorrelation und **kann** diesen Fall darum
nicht sehen — mitgeführt, damit diese Grenze in Zahlen steht statt in einem Nebensatz).
`trennschaerfe_kurve` lässt beide aus der Auswertung heraus.*

**Widerlegbarkeit (Falsifizierbarkeit)** — Eine Aussage ist widerlegbar, wenn sich sagen
lässt, welches Messergebnis sie umwerfen würde. Aussagen, die jeder Ausgang bestätigt,
sind bequem und ohne Erkenntniswert. *In diesem Projekt der Grund, warum die
Monotonie-Kontrolle mehr wiegt als jede Kurve der Schwellenstudie: Die Kurven beschreiben
nur — sie können gar nicht falsch ausgehen. Die Kontrolle kann es: Fällt der Score unter
einer rangerhaltenden Umrechnung auch nur geringfügig, ist die Metrik widerlegt. Der
Modulkopf von `src/aiimaging/schwellenstudie.py` nennt sie darum „die einzige Prüfung
hier, die widerlegen kann statt nur zu beschreiben".*

**Trennschärfe** — Wie gut eine Grenze zwei Gruppen auseinanderhält. Eine Schwelle mit
hoher Trennschärfe lässt fast alles Gute durch und hält fast alles Schlechte auf; eine mit
geringer tut beides nur ungefähr. *In diesem Projekt rechnen `trennschaerfe` und
`trennschaerfe_kurve` (`src/aiimaging/schwellenstudie.py`) sie für eine ganze Reihe von
Schwellen durch. Der Ertrag ist nicht die eine beste Zahl, sondern die Kurve: Sie zeigt,
wie sich das Verhältnis der beiden Fehlerarten verschiebt, wenn man die Grenze bewegt —
auf der Studienszene wird bis 0,85 kein einziger treuer Fall gesperrt, sie anzuheben
kostete dort also nichts.*

**Falsch frei / falsch gesperrt** — Die zwei Fehlerarten, die eine Schwelle machen kann:
*falsch frei* heisst durchgelassen, obwohl hätte aufgehalten werden müssen; *falsch
gesperrt* heisst aufgehalten, obwohl alles in Ordnung war. In der Statistik heissen sie
**falsch negativ** und **falsch positiv** — irreführende Namen, solange nicht dazugesagt
ist, dass „positiv" hier „Alarm" bedeutet und nicht „gut". Entscheidend ist, dass die
beiden **verschieden teuer** sind: Ein durchgelassenes untreues Bild zeigt einen Entwurf,
den es nicht gibt, und kann so in eine Präsentation geraten; ein unnötig gesperrtes kostet
einen weiteren Render. *In diesem Projekt stehen sie darum einzeln in jedem Punkt von
`trennschaerfe_kurve` (`falsch_frei`, `falsch_gesperrt`) statt nur in einer Gesamtnote —
wer eine Schwelle wählt, soll sehen, welchen der beiden Fehler er einkauft.*

**Trefferquote** — Der Anteil der richtig eingeordneten Fälle: richtig durchgelassene plus
richtig gesperrte, geteilt durch alle. Die naheliegendste Kennzahl — und für sich genommen
irreführend, sobald die beiden Gruppen unterschiedlich gross sind: Dann erreicht schon eine
Grenze eine ansehnliche Quote, die einfach immer dasselbe sagt. *In diesem Projekt
vorführbar: Die Studie hat 36 gestörte Fälle gemessen; nach der Entdopplung bleiben **32
ausgewertete**, davon gelten 12 als treu und 20 als untreu. Eine Schwelle, die schlicht
**alles** sperrt, käme allein dadurch auf 0,625 — deutlich mehr als die 0,438 der heutigen
Schwelle 0,65, und trotzdem wäre sie unbrauchbar. Darum wird die Trefferquote nie ohne
`falsch_frei` und `falsch_gesperrt` gelesen.*
*Die Zahlen 36 / 12 / 24 / 0,667 standen bis zum 18.08.2026 hier und stammten aus der
Auswertung **vor** der Entdopplung; sie sind mit* **Entdopplung** *berichtigt worden.*

**Rasterung der Stärkeachse (Stärkeraster)** — Dass eine als Kommazahl angegebene
Stärke in Wahrheit nur wenige verschiedene Eingriffe erzeugen kann, weil der Eingriff
selbst in ganzen Einheiten rechnet und die Angabe darauf gerundet wird. *In diesem
Projekt rechnen die räumlichen Störungen der Schwellenstudie in ganzen Bildpunkten:
Auf einer Szene von 64 × 64 Punkten ergeben die Stärken 0,2 und 0,3 beide eine
Verschiebung um **zwei** Bildpunkte, und die
zwei Tabellenzeilen sind darum gleich. Wer die Tabelle liest, darf die Stärkeachse deshalb
nicht für eine feine Skala halten — vergleichbar sind die Kurvenverläufe, nicht die
einzelnen Stärkewerte untereinander.*
*Derselbe Sachverhalt wie beim* **Quantisierungsschritt** *in Abschnitt 5 — dort für die
Graustufen eines Bildes, hier für die Stärkeachse eines Versuchs.*
*Code und Studie nennen den Sachverhalt kurz **Stärkeraster**
(`src/aiimaging/schwellenstudie.py`, im Rumpf von `trennschaerfe_kurve`;
`docs/SCHWELLENSTUDIE_2026-08-18.md`, Kap. 4a). Was er in der Auswertung anrichtet, steht
im nächsten Eintrag.*

**Entdopplung / Dublette (in einer Messreihe)** — Eine **Dublette** ist eine Zeile einer
Messreihe, die einer anderen nicht bloss ähnelt, sondern **dieselbe Messung** ist: Nach
der Rasterung war die Eingabe punktgleich, also ist es auch das Ergebnis.
**Entdopplung** heisst, solche Zeilen aus der Auswertung zu nehmen — und, das ist der
eigentliche Punkt, ihre Zahl mit auszuweisen. Eine stillschweigende Bereinigung wäre nur
die zweite Art, dieselbe Zahl zu erfinden.
*In diesem Projekt gemessen und teuer bezahlt: Weil die räumlichen Störungen in ganzen
Bildpunkten rechnen (siehe den vorigen Eintrag), ergaben die Stärken 0,2 und 0,3 dieselbe
Ist-Karte — und die gesetzte Grenze zwischen „treu" und „untreu" lag genau dazwischen.
Zwei Zeilen mit **derselben** Messung standen damit auf verschiedenen Seiten der Grenze,
und keine Schwelle kann sie trennen: Jede zählt zwangsläufig einen Fehler. Vier solche
Paare gingen in die erste Auswertung als „falsch frei" ein, also als Aussage über die
Metrik, wo eine Aussage über das Raster stand. `trennschaerfe_kurve`
(`src/aiimaging/schwellenstudie.py`) erkennt sie am **Abdruck** der Ist-Karte — einer
kurzen Kennzahl, die aus deren Zahlen berechnet wird und für gleiche Karten gleich ist,
also einem Hash im Sinn von Abschnitt 8 —, verwirft sie und führt jede einzeln im Feld
`entdoppelt` auf; `n_roh` und `n_ausgewertet` nennen beide Anzahlen nebeneinander. Aus 36
rohen wurden so 32 ausgewertete Zeilen.*

**Idempotenz** — Eigenschaft eines Vorgangs, der mehrfach ausgeführt dasselbe Ergebnis
liefert wie einmal ausgeführt. Macht Wiederholung nach Abbruch gefahrlos.

**Race Condition (Wettlaufsituation)** — Fehler, der davon abhängt, welcher von zwei
gleichzeitigen Vorgängen zuerst fertig wird. Schwer zu finden, weil unregelmässig.
*Auch ein **Test** kann eine Wettlaufsituation enthalten, und dann ist er unbrauchbar: Er
besteht oder scheitert je nach Tagesform des Rechners. Beim Prüfen des
Fortschrittsbeobachters (21.08.) trat genau das auf — der Test stellte die künstliche Uhr
von aussen, während der Beobachtungsfaden sie las, und wer zuerst drankam, entschied über
das Ergebnis. Die Abhilfe war nicht, länger zu warten, sondern das Rennen bedeutungslos zu
machen: eine Uhr, die bei **jedem Blick von selbst** weiterspringt. Dann ist die Frist nach
zwei Blicken gerissen, gleich in welcher Reihenfolge die beiden Fäden zum Zug kommen.*

**Blockierender Aufruf** — Ein Aufruf, der die Kontrolle erst zurückgibt, wenn er fertig
ist. Während er läuft, kann das Programm an dieser Stelle **nichts anderes** tun — auch
nicht nachsehen, ob noch etwas vorangeht.
*Das ist der Grund, warum dieses Projekt an zwei Stellen einen zweiten Faden braucht: Der
Abholer ruft `verarbeite(auftrag)` auf, und dieser Aufruf blockiert bis zum Ende des
Renderlaufs. Zwischen Aufruf und Rückkehr gibt es keinen einzigen Moment, in dem der
Abholer von sich aus nachsehen könnte, ob der Lauf noch vorankommt.*

**Hintergrundfaden und Daemon-Faden** — Ein **Hintergrundfaden** ist ein zweiter
Ausführungsstrang, der neben dem Hauptstrang herläuft (siehe *Thread*, *GIL*). Ein
**Daemon-Faden** ist einer, der das Programm nicht am Beenden hindert: Endet der
Hauptstrang, verschwindet er mit, ohne dass jemand auf ihn wartet.
*Die Beobachtungsfäden dieses Projekts sind Daemon-Fäden. Sie halten keinen Zustand, den
jemand vermissen würde — bricht der Hauptstrang ab, soll kein Beobachter den Prozess
offenhalten, der einem Auftrag zusieht, den es nicht mehr gibt.*

**Fortschrittsbeobachter** — Der Teil, der eine *Fortschrittswache* in Abständen fragt,
während anderswo ein blockierender Aufruf läuft, und sich den **schlimmsten** gesehenen
Befund merkt.
*Dass er den schlimmsten merkt und nicht den letzten, ist die eigentliche Entscheidung:
Ein Lauf, der zwanzig Minuten stand und sich dann fing, **hat gestanden**. Nähme der
Bericht den letzten Blick, löschte die Rettung in letzter Sekunde genau die Beobachtung,
für die das Ganze gebaut ist. Er bricht nichts ab — abgebrochen wird eine Stufe höher, wo
man weiss, was ein Abbruch kostet.*

**Monotonie (einer Metrik)** — Eine Metrik ist **monoton im Fehler**, wenn ein grösserer
Fehler immer einen schlechteren Wert ergibt. Klingt selbstverständlich, ist es nicht.
*Der Geometrie-Score dieses Projekts war es nicht: Gemessen am 20.08.2026 gab ein Versatz
von 2 m den Wert 0.1191 und einer von 4 m den Wert 0.2301 — mehr Fehler, besserer Wert.
Wer eine solche Zahl als „Abstand vom Richtigen" liest, liest sie falsch, denn zwei
verschiedene Fehler können denselben Wert ergeben, und der grössere von beiden kann der
bessere sein. Eine nicht-monotone Grösse lässt sich auch durch keine Umrechnung
(Normierung) monoton machen — die Umrechnung erbt den Knick.*

**Faltung der Skala (durch den Betrag)** — Was passiert, wenn man von einer Grösse, die
von −1 bis +1 läuft, nur noch den **Betrag** wertet: Aus zwei Enden wird eines, und der
schlechteste Wert liegt danach in der **Mitte** statt am Rand.
*Genau das war die Ursache der Nicht-Monotonie oben. Die Rangkorrelation ist bei −1 und
bei +1 gleich aussagekräftig (nur mit umgekehrter Richtung) und bei 0 wertlos. Wer ihren
Betrag wertet, erklärt 0 zum schlechtesten Wert — und der liegt mitten im Fehlerbereich.
Eine Metrik mit einem Minimum in der Mitte kann nicht monoton sein.*

**Boden (einer Ähnlichkeitsmetrik)** — Wie ähnlich sich zwei Dinge sind, die **gar nichts**
miteinander zu tun haben. Man erwartet null; in der Wirklichkeit ist es fast nie null.
*Gemessen an 4950 zusammenhanglosen Bildpaaren liegt der Boden von SigLIP 2 bei 0,526 —
zwei beliebige Bilder sind einander in diesem Modell also schon „zur Hälfte ähnlich".
Der Boden ist die Zahl, unter der eine Schwelle nie liegen darf: Sonst besteht jedes Paar,
und das Gate ist keines.*

**Rauschboden (Boden einer Metrik ohne Geometrie)** — Der Wert, den eine Qualitätsmetrik
erreicht, wenn das geprüfte Bild von der gesuchten Eigenschaft **gar nichts** enthält. Man
erwartet null und bekommt es fast nie.
*Gemessen: Ein Bild ohne jede Geometrie erreicht über der Bauwerksmaske eine
Rangkorrelation von −0,52 statt 0 — weil der Tiefenschätzer auch in reinem Rauschen eine
Rampe von oben nach unten sieht und die Soll-Karte ebenfalls eine hat
(`RAUSCHBODEN_UEBER_MASKE` in `src/aiimaging/geometrie_qa.py`). Wer gegen 0 prüft statt
gegen diesen Boden, prüft gegen die falsche Zahl. Der Wert gehört zum Paar aus Schätzer und
Szenenart; für eine andere Szenenart ist er ungemessen.*
*Dasselbe Wort bezeichnet in Abschnitt 6 einen anderen Sachverhalt — dort die Streuung
einer Saatreihe, also wie weit der blosse Zufall zwei Läufe auseinandertreibt. Hier geht es
um den Nullpunkt einer Skala, dort um ihre Körnigkeit. Die Trennung ist gewollt und in
`tests/test_lexikon.py` als solche ausgewiesen.*

**Abgeleitete Schwelle** — Eine Grenze, die nicht als Zahl gesetzt, sondern aus einer
Messung gerechnet wird — hier ``Boden + k · Streuung``. *Der Grund ist Haltbarkeit: Eine
feste Zahl gehört zu dem Modell, das sie hervorgebracht hat, und wandert beim Wechsel
stillschweigend mit. Genau das ist in diesem Projekt passiert; die Zahl 0,30 stammte aus
einem anderen Einbetter und war im neuen wirkungslos. Eine abgeleitete Schwelle wird beim
Wechsel neu gerechnet, oder es gibt sie nicht.*

**Ausleseort** — Die Stelle im Modell, an der man den Vektor abgreift. Bei Bildmodellen
üblich sind der zusammenfassende Ausgang (``pooler_output``) und der Mittelwert über alle
Bildkacheln (``last_hidden_state``). *Zwei verschiedene Räume mit zwei verschiedenen
Böden — auch beim selben Modell. Eine Schwelle gilt darum immer für ein Modell **und**
einen Ausleseort.*

**Ausgabeschema-Verletzung** — Ein Werkzeug antwortet anders, als es in seinem eigenen
Vertrag zugesagt hat: Es verspricht Text und liefert „nichts". *Das Cockpit prüft die
Zusage und verwirft die ganze Antwort — samt der Fehlermeldung, die eigentlich erklärt
hätte, was schiefging. Der Benutzer sieht dann einen Schemafehler statt der Ursache.
Solche Verletzungen leben fast immer auf den **Fehlerwegen**, weil nur der glückliche Weg
geprüft wird.*

**Rundlauf (Round-Trip)** — Etwas in eine andere Form übersetzen und wieder zurück, um zu
sehen, ob unterwegs etwas verlorengegangen ist. Kommt dasselbe heraus, war die Übersetzung
verlustfrei; kommt etwas anderes heraus, hat man den Verlust in der Hand statt nur eine
Vermutung.
*In diesem Projekt zwischen unserer Auftragsform und der von KosmoVis
(`src/aiimaging/kosmo_naht.py`). Der Rundlauf hat dort einen echten Verlust gefunden: Die
Angabe „freigegeben" überlebte den Hinweg, aber nicht den Rückweg — sie verschwand
stillschweigend, und ein gesperrter Auftrag wäre nach einem Rundlauf als ungeprüft
zurückgekommen.*

**xfail (erwarteter Fehlschlag)** — Ein Test, von dem man **weiss**, dass er scheitert,
und der darum als scheiternd angemeldet wird. Er hält damit zweierlei fest: dass die Lücke
bekannt ist, und wann sie sich schliesst — denn ein `xfail`, der plötzlich besteht, meldet
sich als `XPASS` und verlangt, dass jemand nachsieht.
*Der Unterschied zum Auskommentieren oder Überspringen: Ein übersprungener Test schweigt
für immer. Ein `xfail` ist eine Aussage mit Verfallsdatum — er ist die ehrliche Form,
einen bekannten Mangel im Testnetz zu führen, statt ihn zu verstecken.*

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

**glb-Block (Chunk)** — Wie eine glb-Datei innen aufgebaut ist: zuerst ein **Kopf** von
zwölf Byte — die Kennung `glTF`, die Fassungsnummer und die Gesamtlänge —, danach eine
Folge von **Blöcken**. Jeder Block nennt zuerst seine Länge und seine Art und erst dann
seinen Inhalt. Der erste Block ist nach Norm immer der beschreibende Teil in JSON; die
eigentliche Geometrie folgt als zweiter. Wer nur wissen will, welches Programm die Datei
geschrieben hat, liest deshalb den Kopf und den ersten Block und hört dann auf
(`_glb_json` in `src/aiimaging/herkunft.py`).

*Derselbe Bauplan wie beim* **PNG-Block** *weiter unten — Länge, Kennung, Inhalt —, und
aus demselben Grund: So kann ein Leser überspringen, was er nicht kennt, statt daran zu
scheitern. Und dieselbe Vorsicht: Die Fassungsnummer im Kopf wird gelesen und nicht
angenommen. Eine glb-Datei der Fassung 1 hat einen anderen Aufbau; sie wird mit einer
Begründung abgewiesen, statt versuchsweise falsch gedeutet zu werden.*

**Bounding Box (Hüllbox)** — Der kleinste achsparallele Quader, der ein Objekt
umschliesst. Nützlich für schnelle Grössen- und Lageabschätzungen, etwa zur automatischen
Kamerasetzung.
*Sechs Zahlen statt einer Million Dreiecke — das ist der Grund, warum der Torwächter
(`src/aiimaging/torwaechter.py`) einen Massstabsfehler erkennt, bevor eine
Grafikkartenstunde verbrannt ist. Die Kameraableitung
(`src/aiimaging/kameras.py`) arbeitet aus demselben Grund darauf: Ob ein Gebäude ins Bild
passt, entscheidet sich an den **acht Ecken** der Hüllbox, nicht an seiner Geometrie.*

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

**float32 / float64 (einfache und doppelte Genauigkeit)** — Die zwei üblichen Grössen
für Kommazahlen: 32 Bit mit rund sieben, 64 Bit mit rund sechzehn brauchbaren Stellen.
Python rechnet von sich aus in float64, Blender und die meisten Grafikbibliotheken in
float32. *Deshalb können zwei Programme, die dieselbe Formel auf dieselben Daten anwenden,
im letzten darstellbaren Schritt auseinanderliegen: Liegt ein Zwischenwert genau auf der
Rundungsgrenze, fällt er einmal so und einmal anders. Beim Wechsel der Normalisierung von
Blender nach `src/aiimaging/bildschreiben.py` wichen 18 von 65 536 Bildpunkten um genau
eine Quantisierungsstufe ab, kein einziger um mehr — Rundung, kein Fehler im Verfahren.*

**STEP / ISO-10303-21** — Das Textformat, in dem eine IFC-Datei tatsächlich vorliegt.
Jede Zeile ist eine nummerierte Entität, die auf andere verweist (`#42= IFCWALL(...)`).
Lesbar, aber weitschweifig — eine kleine IFC hat schnell Hunderte Zeilen.
*In diesem Projekt schreibt `tools/make_test_ifc.py` STEP direkt, ohne Bibliothek — so
braucht das Erzeugen von Testdaten kein GPL-behaftetes Environment. Seit dem 18.08.2026
wird STEP auch **gelesen**, aber nur der Dateikopf (`lies_ifc_kopf` in
`src/aiimaging/herkunft.py`): Für zwei Zeilen einen Subprozess jenseits der Prozessgrenze
zu starten, wäre eine Prozessgrenze für eine Textsuche.*

**`FILE_NAME` (der Kopfeintrag einer STEP-Datei)** — Die Zeile am Anfang jeder IFC-Datei,
die sagt, wer sie wann und womit geschrieben hat. Ihre Felder haben **keine Namen**,
sondern nur eine feste Reihenfolge, die die Norm ISO 10303-21 vorschreibt: Dateiname,
Zeitstempel, Autor, Organisation, Programmfassung, erzeugendes System, Freigabe. Wer
daraus etwas herauslesen will, muss also **nach Position** zählen — das fünfte und sechste
Feld nennen das Programm, alle übrigen nicht.

*Daran hing am 18.08.2026 ein Fehler, und zwar von der Sorte, die man nicht bemerkt: Die
erste Fassung der Erkennung sammelte einfach alle nichtleeren Texte aus `FILE_NAME` und
nahm die letzten drei. In der Testdatei sind nur drei Felder gefüllt, darunter der
**Dateiname** — und damit galt `rhino-haus.ifc` als von Rhino erzeugt, obwohl das
Programmfeld Rhino nirgends nennt. **Wer eine Datei umbenannte, änderte ihre Herkunft.**
Das ist keine ungenaue Erkennung, sondern eine falsche. Gelesen werden jetzt nur die zwei
Felder, die die Norm für diesen Zweck vorsieht; Dateiname, Autor und Organisation bleiben
draussen, denn ein Autorenfeld „Blenderweg 12" ergäbe sonst „Blender".*

*Zwei Feinheiten des Formats machen dabei Arbeit, und beide sind der Grund, warum ein
blosses Zerlegen an den Kommas nicht genügt: Autor und Organisation sind selbst Listen und
dürfen Kommas enthalten — ein Komma darin verschöbe jedes folgende Feld um eine Stelle,
und dann zählt man an der falschen Position —, und ein Hochkomma im Text wird durch
Verdoppelung geschrieben. Beides erledigt `_step_felder`
(`src/aiimaging/herkunft.py`).*

**SI-Vorsatz (Präfix)** — Die Silbe vor einer Masseinheit, die für einen Zehnerfaktor
steht: *Milli* für ein Tausendstel, *Zenti* für ein Hundertstel, *Kilo* für das
Tausendfache. Eine IFC-Datei gibt ihre Längeneinheit genau so an — die Grundeinheit
`METRE` plus einen Vorsatz —, und aus dem Vorsatz folgt die Zahl, mit der die Koordinaten
der Datei in Meter übergehen: `.MILLI.` heisst 0,001 Meter je Einheit. *Die Tabelle steht
als `SI_VORSAETZE` in `src/aiimaging/herkunft.py`.*

*Eine Unterscheidung darin ist wichtiger, als sie aussieht: Findet sich kein Faktor, gibt
die Funktion **nicht** 1,0 zurück, sondern „unbekannt". 1,0 wäre bereits eine Behauptung
— „die Datei ist in Metern" —, und wäre sie falsch, entstünde genau der Fehler, den der
Torwächter danach als unplausibel grosses oder kleines Bauwerk auffangen müsste.*

**Umrechnungseinheit (`IfcConversionBasedUnit`)** — Der andere Fall: eine Längeneinheit,
die sich nicht über einen Zehnerfaktor auf eine SI-Einheit zurückführen lässt, sondern nur
über eine krumme Zahl — Zoll, Fuss, Yard. Die IFC-Datei nennt dann den Namen der Einheit
an einer Stelle und ihren Umrechnungsfaktor an einer anderen, auf die sie bloss verweist.

*In diesem Projekt wird der Name gelesen und der Faktor **nicht** aufgelöst: Dem Verweis
zu folgen hiesse, einen vollständigen Leser des STEP-Formats zu bauen, und das wäre ein
zweites Projekt. Der Faktor bleibt darum ausdrücklich offen, mit einer Warnung im Klartext
— damit ihn niemand stillschweigend für 1,0 hält (`_laengeneinheit` in
`src/aiimaging/herkunft.py`). Eine bekannte Lücke, die sich meldet, ist etwas anderes als
eine Lücke, die geraten wird.*

**Extrusion / SweptSolid** — Die häufigste Art, wie IFC Geometrie beschreibt: ein
zweidimensionales Profil, entlang einer Richtung in die Höhe gezogen. Eine Wand ist ein
Rechteck, drei Meter hochgezogen. Deshalb steht in einer IFC kein fertiges 3D-Modell,
sondern eine Bauanweisung — jemand muss daraus erst Dreiecke rechnen.

**Raum (`IfcSpace`)** — In einem Gebäudemodell ist ein Raum kein Bauteil, sondern ein
**Luftvolumen**: der Bereich, in dem sich jemand aufhält, begrenzt von Wänden, Boden und
Decke. In IFC steht er als eigener Eintrag namens `IfcSpace` neben den Wänden — mit Namen,
Grundriss und Höhe, aber ohne Material. Viele Modelle tragen gar keine; sie zu setzen ist
Arbeit, die jemand im Autorenprogramm bewusst machen muss. *In diesem Projekt die
Voraussetzung für jede Aufnahme von innen: Ohne Räume gibt es nichts, worin eine Kamera
stehen könnte.*

**Grundriss (als Polygon)** — Der Umriss eines Raums, waagerecht gesehen, als Kette von
Eckpunkten. Vier Punkte bei einem rechteckigen Zimmer, sechs bei einem L-förmigen. Das ist
die schlichteste Form, in der sich „wo ist dieser Raum" weiterreichen lässt — sie kommt
ohne Geometriebibliothek aus, und genau darum kann der Kern des Projekts sie verarbeiten,
obwohl der Leser der IFC-Datei hinter einer Prozessgrenze liegt.

**Umlaufsinn** — Die Richtung, in der die Eckpunkte eines Polygons aufgezählt sind: gegen
den Uhrzeigersinn oder mit ihm. Für die Fläche ist es gleichgültig, für manche Rechnungen
nicht — etwa für die Frage, welche Seite einer Kante „innen" ist. *Hier wird er gemeldet
und nicht begradigt: Wer den Ring dreht, soll wissen, dass er es getan hat.*

**Platzierungskette** — In IFC steht kein Bauteil bei absoluten Koordinaten. Es hängt an
einer Kette: Der Raum liegt im Geschoss, das Geschoss im Gebäude, das Gebäude auf dem
Grundstück — und jedes Glied trägt eine eigene Verschiebung und Drehung. Wer die Kette
nicht bis oben durchrechnet, bekommt ein Bauteil an der falschen Stelle. Besonders
tückisch: Lässt man **ein** Glied aus, liegen alle Bauteile gleich falsch, und der
Grundriss sieht trotzdem plausibel aus.

**Bezugspunkt (einer Höhenangabe)** — Der Nullpunkt, von dem aus eine Höhe gemessen wird.
„2,70 m" ist ohne ihn keine Angabe: über Fussboden, über Geschossnull, über Meer — das
sind drei verschiedene Orte. *Dieses Projekt hat an genau dieser Verwechslung zweimal
verloren; eine Kamerahöhe „absolut" gemeint landete bei einem Bauwerk auf 400 m über Meer
vierhundert Meter unter dem Erdgeschoss. Seither trägt jede Höhe im Code den Namen ihres
Bezugspunkts mit sich.*

**Lichte Höhe** — Der freie Abstand zwischen Fussboden und Decke eines Raums, also das,
was ein Mensch darin wirklich an Luft über sich hat. Zu unterscheiden von der
**Geschosshöhe**, die von Rohdecke zu Rohdecke misst und die Deckenstärke mit einschliesst.
Der Unterschied beträgt leicht einen halben Meter. *Welche der beiden ein IFC-Raumkörper
darstellt, sagt die Datei nicht — das ist eine Gewohnheit des erzeugenden Programms, und
darum wird die Zahl hier keiner von beiden gleichgesetzt.*

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

**Multipass** — Ein Renderlauf, der mehrere solche Kanäle **in einem Durchgang** erzeugt,
statt für jeden neu zu rechnen. *Der Grund ist nicht nur Zeit, sondern Deckungsgleichheit:
Zwei getrennte Läufe können minimal auseinanderliegen — anderes Rauschen, andere
Zufallszahlen —, und dann passt die Tiefenkarte nicht mehr pixelgenau zum Bild. Die
Geometrie-QA dieses Projekts vergleicht aber punktweise; sie lehnt bei ungleicher Länge zu
Recht ab.*

**Rangkorrelation (Spearman)** — Misst, ob zwei Messreihen dieselbe *Reihenfolge* haben,
nicht dieselben Werte. Wert zwischen −1 und 1. *Hier zentral: Eine aus einem Bild
zurückgerechnete Tiefenkarte hat einen anderen Massstab und Nullpunkt als echte Meter —
vergleichbar ist nur die Reihenfolge „was ist näher".*

**Bindung (Tie)** — Gleiche Werte in einer Messreihe. Bei Rangkorrelation bekommen sie
den mittleren Rang. *In Tiefenkarten der Normalfall: Eine Wand parallel zur Bildebene
liefert lauter gleiche Werte. Die verbreitete Kurzformel für Spearman rechnet dort
systematisch falsch.*

**Streng monoton (rangerhaltend)** — Eine Umrechnung heisst streng monoton, wenn sie die
Reihenfolge unangetastet lässt: Was vorher grösser war, ist es nachher auch. Der
Zahlenwert darf sich dabei beliebig ändern. Meter in Zentimeter umrechnen ist streng
monoton, ebenso „mal zehn, minus fünfzig" oder das Quadrieren positiver Zahlen; nah und
fern zu vertauschen ist es nicht. *Der Begriff trägt die ganze Geometrie-Metrik: Weil die
Rangkorrelation nur die Reihenfolge liest, muss sie jede streng monotone Umrechnung
unverändert überstehen. Die Kontrolle `monoton` in `src/aiimaging/schwellenstudie.py`
wendet Massstab, Nullpunkt und Potenz zugleich an — der Score bleibt bei exakt 1,000.*

**Invarianz** — Eine Eigenschaft, die sich unter einer bestimmten Umformung **nicht**
ändert. Man verlangt sie überall dort, wo etwas gemessen werden soll, das von der
Umformung gar nicht betroffen ist: Die Fläche eines Grundrisses ändert sich nicht, wenn
man den Plan dreht — täte sie es, wäre die Flächenberechnung falsch und nicht der Plan.
*In diesem Projekt die tragende Zusage der Geometrie-Metrik: Sie soll die Reihenfolge der
Tiefen vergleichen und nicht deren Zahlenwerte, also muss ihr Ergebnis unter jeder streng
monotonen Umrechnung der Tiefe gleich bleiben. Erst diese Invarianz macht eine geschätzte
Tiefenkarte mit echten Metern vergleichbar — Massstab und Nullpunkt der beiden stimmen nie
überein, die Reihenfolge kann es. Geprüft wird sie von der Kontrolle `monoton` der
Schwellenstudie; sie ist die einzige dortige Prüfung, die das Verfahren widerlegen könnte.*

**Inkommensurabel** — Zwei Grössen, für die es kein gemeinsames Mass gibt: Keine noch so
feine Einheit geht in beiden ganzzahlig auf, ihr Verhältnis lässt sich nicht als Bruch
zweier ganzer Zahlen schreiben. Das Schulbeispiel ist die Diagonale eines Quadrats zu
seiner Seite — das Verhältnis ist √2 ≈ 1,4142…, und die Nachkommastellen brechen nie ab.
*In diesem Projekt der Grund für eine unscheinbare Zeile in `baue_testszene`
(`src/aiimaging/schwellenstudie.py`): Die Tiefe der Testszene entsteht aus zwei
Achsenanteilen, und die werden nicht gleich gewichtet, sondern im Verhältnis 1 : √2. Bei
gleicher Gewichtung ergäben (x + 1, y − 1) und (x, y) denselben Tiefenwert, und die Karte
bestünde grösstenteils aus Bindungen — beim ersten Studienlauf gemessene 1837 auf 1936
Punkte. Mit dem inkommensurablen Verhältnis fällt die Bindungszahl auf null, und die
Monotonie-Kontrolle steht bei exakt 1,000 statt bei 0,999997.*

**Normalverteiltes Rauschen / Standardabweichung (σ)** — Zufällige Abweichungen, die sich
um null häufen: kleine sind häufig, grosse selten, und die bekannte Glockenkurve
beschreibt, wie häufig genau. Die **Standardabweichung** σ ist das Mass für ihre Breite —
grob gesagt bleiben rund zwei Drittel aller Abweichungen kleiner als σ. *In diesem Projekt
die Störung `rauschen` der Schwellenstudie; Stärke 1,0 heisst dort σ = eine halbe
Bautiefe. Selbst bei dieser Stärke bleibt die Rangkorrelation bei 0,45 — die Reihenfolge
der Tiefen ist gegen Rauschen erheblich unempfindlicher als der einzelne Tiefenwert.*

**Perzentil** — Der Wert, unter dem ein bestimmter Anteil aller Messwerte liegt: Das
95. Perzentil ist die Zahl, die 95 % aller Fälle unterschreiten, das 5. Perzentil die, die
nur 5 % unterschreiten. Anders als der Mittelwert sagt es etwas über die **Spanne** aus.
*In den Kamerarecherchen die Form, in der Körpermasse angegeben werden: Die Augenhöhe im
Stehen reicht vom 5. Perzentil der Frauen (1,43 m) bis zum 95. der Männer (1,74 m). Der im
Projekt gesetzte Wert 1,70 m ist damit keine Durchschnitts-Augenhöhe, sondern ein hoher
Wert — wer 1,70 gegen 1,60 verteidigt, verteidigt einen Geschmack und keine Zahl.*

**Mittelwertfilter (Glättung)** — Jeder Bildpunkt wird durch den Durchschnitt aus sich
selbst und seinen Nachbarn ersetzt, je nach Stärke mehrfach hintereinander. Kanten werden
weich, feine Gliederung verschwindet, die grobe Form bleibt. *In diesem Projekt die
Störung `glaettung`: Sie bildet nach, was ein Bildmodell an Detail verliert. Ein Nebenbefund
gehört hierher, weil er leicht in die Irre führt — über einer gleichmässigen Rampe richtet
ein Mittelwertfilter gar nichts an, denn der Durchschnitt einer gleichmässig ansteigenden
Folge ist wieder dieselbe Folge. Die erste Testszene war eine solche Rampe, und die Störung
blieb völlig wirkungslos; erst ein Tiefensprung gibt ihr eine Kante zum Zerstören.*

**Polarität (einer Tiefenkarte)** — Ob grosse Werte *nah* oder *fern* bedeuten. Blender
liefert Meter (gross = fern), viele Schätzer liefern Disparität (gross = nah). *Wird in
diesem Projekt nie aus den Daten erraten, sondern deklariert — aus den Daten schliessen
hiesse die Ordnung vorauszusetzen, die man gerade messen will.*

*Seit dem 21.08.2026 gibt es dazu eine Präzisierung, und sie beantwortet genau den
Einwand im Satz davor. Die Polarität gehört zum **Schätzer** und nicht zum einzelnen
Bild: Ein Verfahren, das Disparität liefert, liefert sie bei jedem Bild. Man darf sie
darum einmal **bestimmen** — aber nur an Läufen mit **bekannt guter** Geometrie
(Blender-Renders derselben Szene, aus der die Vergleichskarte stammt). Genau diese
Auflage schliesst den Zirkel aus: Aus einem Lauf, dessen Geometrie fraglich ist, liesse
sich die Polarität nicht bestimmen, ohne den Fehler mitzubestimmen, den sie später
aufdecken soll. Aus demselben Grund genügt ein einzelner Lauf nicht.*

*Und sie gehört zum **Paar** aus Schätzer und Vergleichskonvention, nicht zum Schätzer
allein — eine Angabe aus der Modellkarte des Schätzers wäre nur die halbe Auskunft, weil
sie nichts darüber sagt, wie die eigene Vergleichskarte herum liegt. Für
`depth-anything-v2-small` gegen unsere Blender-Karte ist sie an 24 Läufen gemessen:
Disparität.*

*Warum das mehr ist als Buchhaltung: Solange die Polarität unbekannt ist, muss man den
**Betrag** der Rangkorrelation werten — und der faltet die Skala (siehe dort), was die
Metrik nicht-monoton macht und nebenbei eine vollständig invertierte Tiefenkarte wie eine
perfekte bewertet.*

**Hintergrundmarke** — Die Festlegung, welche Bildpunkte als „kein Gebäude" gelten. Bei
gerenderten Tiefenkarten ist das eindeutig (der Himmel hat keine Tiefe); bei *geschätzten*
nicht — dort bekommt auch der Himmel eine gewöhnliche Zahl. Ohne Marke zählt das ganze
Bild als Geometrie, und der Silhouettenvergleich wird strukturell unmöglich.

**Silhouette** — Die Menge der Bildpunkte, die überhaupt Geometrie tragen (im Unterschied
zum Hintergrund). *Der Teil der Geometrie-QA, der die Halluzination fängt.*
*Die Schwellenstudie vom 18.08.2026 hat das eingegrenzt: Gefangen wird zuverlässig eine
Halluzination, die die Geometrie **ersetzt** — steht der erfundene Bau woanders, geht die
Überdeckung gegen null. Ein Bau, der bloss **danebengesetzt** wird, kostet weit weniger:
Ein Zusatzkörper von der Fläche des Baus selbst besteht mit 0,698 — er geht also durch.*

**IoU (Intersection over Union)** — Überlappungsmass zweier Flächen: gemeinsame Fläche
geteilt durch Gesamtfläche. 1 heisst deckungsgleich, 0 heisst keine Überlappung.

**Geometrisches Mittel** — Die Wurzel aus dem Produkt zweier Werte, statt ihres
Durchschnitts. *Hier bewusst gewählt: Es verlangt, dass **beide** Anteile gut sind. Beim
belegten Halluzinationsfall ergibt der Durchschnitt 0,52 — fast bestanden —, das
geometrische Mittel 0,20.* *Das gilt für den geprüften Fall, in dem der erfundene Bau die
echte Geometrie **ersetzt**. Wird bloss etwas **hinzugefügt**, sinkt allein die
Silhouetten-Überdeckung, und auch die nur um die hinzugekommene Fläche — dann hilft auch
das geometrische Mittel wenig; siehe* **Silhouette**.

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

**Bauwerksmaske** — Eine Liste mit einem Ja/Nein je Bildpunkt: *hier steht das Bauwerk*
oder *hier steht es nicht*. Sie wird aus dem Material-ID-Pass gewonnen, indem man
Hintergrund und Gelände abzieht. *Wozu: Die Geometrieprüfung dieses Projekts rechnete
über das ganze Bild und verglich damit in einer bodenlastigen Szene vor allem zwei
Bodenflächen miteinander — weisses Rauschen kam so auf 72 von 100 Punkten. Über der
Bauwerksmaske gerechnet wird dieselbe Prüfung wieder scharf.*

**Einspringende Ecke (Innenecke)** — Eine Ecke eines Grundrisses, an der der Innenwinkel
grösser als 180° ist — die Ecke eines L-förmigen Raums, gesehen von innen. Der Gegensatz
ist die *vorspringende* Ecke, die gewöhnliche Zimmerecke mit weniger als 180°.
*Sie ist der Grund, warum sich Räume nicht mit einfacher Mittelpunktsmathematik behandeln
lassen: In der Kerbe eines L-förmigen Raums liegen Punkte, die innerhalb der umgebenden
Rechteckfläche liegen und trotzdem ausserhalb des Raums — eine Kamera dort stünde im
Nachbarzimmer. Und eine Winkelhalbierende zeigt an einer solchen Ecke nach aussen statt
nach innen, weshalb dort kein Kamerastandpunkt entsteht.*

**Tiefenkante (an der Maskengrenze)** — Der Sprung in der geschätzten Tiefe genau dort,
wo die Silhouette des Bauwerks endet: vorne die Fassade, dahinter der ferne Hintergrund.
Gemessen als Unterschied zwischen den Punkten knapp innerhalb und knapp ausserhalb der
*Bauwerksmaske*, geteilt durch die Spanne der ganzen Schätzung — sonst misst man den
Zahlenbereich des Schätzers statt der Kante.
*Sie beantwortet die Frage, an der alle bisherigen Masse dieses Projekts gescheitert
sind: **Steht dort überhaupt etwas?** Ein leeres Grundstück hat an dieser Stelle keinen
Sprung, weil Boden und Himmel stetig ineinander übergehen — gemessen 0,0006 gegen 0,1615
beim richtigen Bild.*
*Der Preis, und er ist keine Schwäche, sondern die Definition: Die Maske ist die
Silhouette des **richtigen** Bauwerks. Ein gedrehtes oder anders geformtes hat seine
Kanten woanders, und dort steht dann Grund — die Tiefenkante fragt also nicht «steht dort
etwas», sondern «steht dort **das Richtige**». Genau die Fälle, die sie darum verfehlt,
fängt die Rangkorrelation.*

**Umrisstreue (Anteil der Grenze mit Kante)** — Wieviel vom Umriss eines Bauwerks ein
erzeugtes Bild **wirklich zeichnet**. Gemessen als Anteil der Silhouettengrenze, an dem
das Bild einen Tiefensprung zeigt — nicht wie stark der Sprung im Mittel ist, sondern an
**wievielen Stellen** es überhaupt einen gibt.
*Der Unterschied ist der ganze Witz: Ein Mittel- oder Medianwert über die ganze Grenze
bricht zusammen, sobald ein Teil des Umrisses fehlt. Ein Bild, das ein Viertel seines
Umrisses zeichnet, sieht im Median aus wie eines, das gar nichts zeichnet. Der Anteil
fällt stattdessen allmählich — und nur eine allmählich fallende Grösse taugt als Tor.*
*Gemessen am 22.08.2026: perfektes Bild 87,4 %, bestes erzeugtes 24,3 %, ohne
Tiefenführung 6,4 %, ein Bild ohne echte Führung 2,8 %.*

**Zufallsniveau (eines Anteilsmasses)** — Der Wert, den ein Mass erreicht, wenn zwischen
den beiden verglichenen Dingen **gar kein Zusammenhang** besteht. Bei den meisten Massen
muss man ihn eigens messen (siehe *Rauschboden*); bei manchen folgt er aus der
Konstruktion.
*Bei der Umrisstreue folgt er: Werden die stärksten 5 % der Bildpunkte als „Kante"
gewertet, trifft eine beliebige, bezugslose Linie ebenfalls rund 5 % davon. Alles darüber
ist Signal. Das spart die Nullprobe — mit einer Einschränkung, die beim Bauen auffiel:
Hat ein Bild viele **gleiche** Werte, lassen sich die stärksten 5 % gar nicht abtrennen,
und das Zufallsniveau steigt. Es wird darum nicht angenommen, sondern jedes Mal
mitgerechnet.*

**Paarurteil** — Ein Urteil, das **zwei Messwerte nebeneinander stehen lässt**, statt sie
zu einer Zahl zu verrechnen. Es besteht nur, wenn beide bestehen, und es sagt dazu,
welcher der beiden ein Nein trägt.
*Warum das eine eigene Bauform ist: Der frühere Geometrie-Score multiplizierte zwei Masse
zu einer Zahl und verschmolz damit zwei verschiedene Fragen — «steht dort etwas» und
«stimmt, was dort steht». Der Faktor, der die erste beantworten sollte, belohnte am Ende
sogar die Abwesenheit. Zwei Fragen brauchen zwei Antworten; eine Zahl, die beide
behauptet, beantwortet keine.*
*Und ein Urteil aus nur einer der beiden Zahlen gilt als **nicht gemessen** — nicht als
«bestanden aufgrund der anderen». Für eine fehlende Antwort gibt es keinen Ersatz.*

**Geländeregel** — Die ausdrückliche Vorschrift, woran das Gelände in einem Modell zu
erkennen ist — im einfachsten Fall eine Liste von Namen («Boden_Platte», «IfcSite…»).
Sie ist nötig, weil ein Rechner einem Bauteil nicht ansieht, ob es Boden oder Wand ist;
er sieht nur einen Namen. *Der wunde Punkt der Bauwerksmaske: Greift die Regel nicht,
steckt der ganze Boden unbemerkt im «Bauwerk». Deshalb meldet dieses Projekt in dem Fall
«nicht gemessen» statt eine Maske auszuliefern, die niemand nachprüft.*

**Goldener Winkel** — Ein Verteilungstrick: Nimmt man bei jedem Schritt rund 137,5°
(bzw. den Anteil 0,618 eines vollen Kreises), liegen aufeinanderfolgende Werte immer
weit auseinander, egal wie viele es werden. *Wird hier benutzt, um jedem Bauteil im
Material-ID-Pass eine gut unterscheidbare Farbe zu geben — auch beim zwanzigsten.*
In der Natur dasselbe Prinzip wie bei der Blattstellung am Trieb.

**Normalisierung** — Messwerte auf einen festen Bereich umrechnen, meist 0 bis 1.
*Die Tiefenkarte trägt echte Meter; das Bildmodell erwartet Graustufen. Die
Rückrechnungsformel wird darum mitgeliefert, sonst wären die Meter verloren.*

**OpenEXR (Scanline)** — Bildformat für Messwerte statt Bildeindrücke: hohe Genauigkeit,
Werte weit über den sichtbaren Bereich hinaus. *Scanline* heisst zeilenweise abgelegt (im
Gegensatz zu gekachelt). *Hier trägt die EXR echte Meter, das PNG nur Graustufen.*

**Half-Float** — Kommazahl mit 16 statt 32 Bit. Halb so gross, deutlich ungenauer. Bei
Tiefendaten in Metern zu grob — deshalb schreibt dieses Projekt 32 Bit.

**Ebene (Layer) in einer Bilddatei / Multilayer-EXR** — Gewöhnlich enthält eine
Bilddatei ein Bild. Eine *mehrschichtige* EXR enthält mehrere Ergebnisse desselben
Renderlaufs übereinander in **einer** Datei — etwa Farbe, Tiefe und Materialzuordnung.
Auseinandergehalten werden sie über die Kanalnamen: Dem Namen wird die Ebene punktgetrennt
vorangestellt, aus `V` wird `tiefe_.V`, aus `Z` wird `ViewLayer.Depth.Z`. Wer eine solche
Datei selbst liest, muss diese zusammengesetzten Namen zerlegen, sonst findet er den
gesuchten Kanal nicht. *Blender 5.2 lässt am File-Output-Knoten nur noch dieses Format zu;
`src/aiimaging/bildlesen.py` sucht den Tiefenkanal deshalb ausdrücklich auch hinter einem
Ebenen-Präfix.*

**Verlustfrei / verlustbehaftet (Kompression)** — Verlustfrei gepackte Daten kommen beim
Entpacken Bit für Bit wieder so heraus, wie sie hineingingen (PNG, zlib, die
ZIP-Kompression in EXR). Verlustbehaftet heisst, dass zugunsten der Dateigrösse etwas
weggelassen wird, das nicht zurückkommt (JPEG). *Hier liegt beides nebeneinander: Das PNG
ist in sich verlustfrei gepackt, ist aber als Ganzes eine verlustbehaftete Ableitung der
EXR — die echten Meter werden auf 65 536 Graustufen gerundet. Deshalb bleibt die EXR das
massgebliche Artefakt.*

**Prädiktor (Vorhersage bei Kompression)** — Der Grundkniff beim Packen von Messwerten:
Statt den Wert selbst abzulegen, sagt man ihn aus schon bekannten Nachbarwerten voraus und
legt nur die *Abweichung* von dieser Vorhersage ab. Trifft die Vorhersage ungefähr zu,
stehen in der Datei lauter kleine, einander ähnliche Zahlen nahe null — und die lassen
sich weit besser packen als die Ausgangswerte. Verloren geht dabei nichts: Der Leser
bildet dieselbe Vorhersage und addiert die Abweichung wieder dazu.

**Prädiktor / Byte-Entflechtung** — Zwei Kniffe, mit denen OpenEXR seine Daten vor dem
Packen umsortiert, damit `zlib` besser greift: Erst wird jeder Wert als Differenz zum
vorigen abgelegt, dann werden die Bytes einer Zahl auseinandergezogen und gruppiert. Wer
die Datei selbst liest, muss beides rückgängig machen — mehr steckt in der
ZIP-Kompression von OpenEXR nicht.
*Der Prädiktor ist hier die einfachste denkbare Vorhersage: „der nächste Wert ist wie der
vorige". PNG benutzt dieselbe Idee mit anderen Nachbarn — siehe Zeilenfilter.*

**zlib** — Die überall verbreitete Bibliothek zum verlustfreien Packen und Entpacken von
Daten; sie gehört zur Standardbibliothek von Python und bringt auch die Berechnung der
CRC-Prüfsumme mit. *Der Grund, warum dieses Projekt EXR und PNG ohne Fremdabhängigkeit
lesen **und schreiben** kann — und damit ohne neue Lizenzfrage.*

**Zeilenfilter (PNG)** — Der Prädiktor des PNG-Formats, zeilenweise angewandt. „Filter"
heisst hier **keine Bildbearbeitung**: Am Bild ändert sich nichts, und nichts geht
verloren. Es ist eine Umrechnung *vor* dem Packen, die die abzulegenden Zahlen kleiner und
einander ähnlicher macht, und die der Leser exakt rückgängig macht. PNG stellt fünf
Verfahren zur Wahl, jede Zeile darf ein anderes benutzen, und die gewählte Nummer steht
als erstes Byte der Zeile:

- **0 — None:** keine Vorhersage, der Wert wird unverändert abgelegt.
- **1 — Sub:** Abweichung vom linken Nachbarn.
- **2 — Up:** Abweichung vom Wert an derselben Stelle in der Zeile darüber.
- **3 — Average:** Abweichung vom Mittel aus linkem und oberem Nachbarn.
- **4 — Paeth:** Abweichung von einer Vorhersage aus drei Nachbarn — siehe unten.

*Wer ein PNG liest, muss alle fünf rückgängig machen können
(`src/aiimaging/bildlesen.py`); wer eines schreibt, muss je Zeile eines wählen
(`src/aiimaging/bildschreiben.py`). Dort werden absichtlich alle fünf benutzt: So prüft
jede geschriebene Testdatei nebenbei den Entfilterer des Lesers an echten Daten.*

**Paeth-Prädiktor** — Die vierte und meistgebrauchte PNG-Vorhersage, benannt nach Alan W.
Paeth. Sie zieht drei bereits bekannte Nachbarn heran — links, oben und oben-links — und
wählt unter ihnen denjenigen aus, der einer einfachen Abschätzung am nächsten liegt
(`links + oben − obenlinks`). Anschaulich: An einer senkrechten Kante gewinnt der obere
Nachbar, an einer waagrechten der linke. Die Vorhersage erkennt also von selbst, in
welcher Richtung das Bild gerade gleichmässig ist. *`_paeth` in
`src/aiimaging/bildschreiben.py`.*

**MSAD-Heuristik (minimum sum of absolute differences)** — Die Faustregel, nach der ein
PNG-Schreiber den Filter für eine Zeile wählt: Er rechnet alle fünf durch, addiert je
Ergebnis die Beträge aller Bytes und nimmt dasjenige mit der kleinsten Summe. Die Annahme
dahinter ist, dass kleine Zahlen sich besser packen lassen als grosse; nachgeprüft wird
das nicht, denn dafür müsste man jede der fünf Fassungen wirklich packen. Die Bytes werden
dabei als vorzeichenbehaftet gelesen — ein Byte fasst 256 Werte, und 255 steht dann nicht
für 255, sondern für −1, also für eine Abweichung um **eins** nach unten. *Die
PNG-Spezifikation empfiehlt diese Regel, die Referenzbibliothek libpng hat sie eingeführt;
`_zeile_filtern` in `src/aiimaging/bildschreiben.py` setzt sie um.*

**PNG-Block (Chunk)** — Eine PNG-Datei ist nicht ein Stück, sondern eine Folge benannter
Blöcke: `IHDR` mit Breite, Höhe und Bittiefe, `IDAT` mit den gepackten Bilddaten, `IEND`
als Abschluss. Jeder Block trägt seine Länge, eine vierbuchstabige Kennung, die Nutzlast
und eine Prüfsumme. Dadurch kann ein Leser Blöcke, die er nicht kennt, überspringen statt
zu scheitern. *`_block` in `src/aiimaging/bildschreiben.py` setzt einen solchen zusammen.*

**Endianness (Bytefolge)** — In welcher Reihenfolge die Bytes einer Zahl im Speicher oder
in einer Datei liegen. Eine 16-Bit-Zahl besteht aus zwei Bytes: *Big-Endian* legt das
gewichtigere zuerst ab — so, wie wir Zahlen schreiben, Hunderter vor Einern —,
*Little-Endian* das leichtere zuerst. Wer ein Binärformat selbst liest oder schreibt, muss
die richtige wählen, sonst kommen sinnlose Werte heraus. *PNG schreibt Big-Endian
zwingend vor; daher das `>` in den `struct.pack(">I", ...)`-Aufrufen in
`src/aiimaging/bildschreiben.py`. OpenEXR verlangt umgekehrt Little-Endian — die beiden
Formate, die dieses Projekt selbst liest, sind hierin gegenläufig.*

**CRC-Prüfsumme (CRC32)** — Eine kurze Kontrollzahl, die aus einem Datenblock berechnet
wird und sich ändert, sobald sich am Block etwas ändert. Sie zeigt Beschädigungen an —
gegen absichtliche Fälschung schützt sie nicht. *PNG führt sie je Block mit, in der
32 Bit langen Variante CRC32, gerechnet über Kennung **und** Nutzlast (`_block` in
`src/aiimaging/bildschreiben.py`; die Rechnung liefert `zlib` mit).*
*Verwandt mit, aber nicht dasselbe wie* **Hash / Prüfsumme** *in Abschnitt 8: Die CRC
bewacht einen Datenblock gegen Übertragungsschäden, der Hash dient dem Wiederfinden
gleicher Inhalte.*

**Quantisierungsschritt / Quantisierungsstufe** — Der Abstand zwischen zwei darstellbaren
Werten; beide Wörter meinen dasselbe. Ein Format mit endlich vielen Stufen kann nichts
dazwischen ausdrücken, es muss runden. *Bei 16 Bit über eine Bautiefe von 8,7 m sind das
0,13 mm; der gemessene Rückrechnungsfehler liegt bei genau der Hälfte davon — also reine
Rundung, kein Fehler im Verfahren. Dieselbe Einheit taucht beim Wechsel der Normalisierung
auf die Produktseite wieder auf: 18 von 65 536 Bildpunkten weichen um genau **eine** Stufe
ab.*
*Nicht zu verwechseln mit* **Quantisierung (Modellgewichte)** *in Abschnitt 6 — gleiches
Wort, anderer Sachverhalt.*

**LSB (niedrigstwertiges Bit, least significant bit)** — Ein Bit ist die kleinste
Speichereinheit: eine Stelle, die nur 0 oder 1 sein kann. Das niedrigstwertige ist
dasjenige mit dem kleinsten Gewicht — kippt es, ändert sich die Zahl um genau eine
Quantisierungsstufe. „Eine Abweichung im LSB" ist deshalb die knappe Art zu sagen: die
kleinste, die dieses Format überhaupt ausdrücken kann. Kleiner ginge nur, indem beide
Werte gleich wären. *Genau diese Grössenordnung trennt den eigenen Normalisierer von
Blender.*

**Farbtyp (PNG)** — Die Zahl im PNG-Kopf, die sagt, was in einem Bildpunkt steht:
0 = Graustufen, 2 = RGB, 3 = Palette, 4 = Graustufen mit Deckungskanal, 6 = RGB mit
Deckungskanal. Sie entscheidet, wie viele Zahlen pro Bildpunkt in der Datei liegen — wer
sie ignoriert, liest die richtigen Bytes in der falschen Bedeutung.
*In diesem Projekt trennt sie zwei Leser mit entgegengesetzter Absicht: `lies_png_graustufen`
**lehnt** Farbe ab (aus drei Farbkanälen eine Entfernung zu machen wäre geraten, nicht
gelesen), `lies_png_luminanz` **nimmt** sie an (ein gerendertes Bild ist farbig).*

**Palette (PNG-Farbtyp 3)** — Eine Speicherweise, bei der in der Datei nicht Farben
stehen, sondern **Nummern**, die in eine mitgelieferte Farbtabelle zeigen. Ohne diese
Tabelle sind die Zahlen bedeutungslos: Die 7 ist keine Helligkeit, sondern der siebte
Eintrag. *Beide PNG-Leser dieses Projekts weisen Palettenbilder darum ausdrücklich ab,
statt ihre Indizes als Helligkeiten zu deuten.*

**Alphakanal (Deckungskanal)** — Ein vierter Wert je Bildpunkt neben Rot, Grün und Blau,
der sagt, wie **deckend** dieser Punkt ist: 0 heisst völlig durchsichtig, der Höchstwert
völlig deckend. *In der Belichtungsmessung dieses Projekts wird er bewusst **ignoriert**:
Ein halbdurchsichtiges Pixel hat trotzdem eine Helligkeit, und was dahinter liegt, weiss
der Leser nicht — es hineinzurechnen hiesse, einen Hintergrund zu erfinden.*

**Luminanz (Leuchtdichte, Luma)** — Die Helligkeit eines Farbwerts als **eine** Zahl. Sie
entsteht durch Gewichten der drei Farbkanäle, denn das Auge sieht Grün viel heller als
Blau: Ein reines Grün wirkt hell, ein reines Blau fast schwarz, obwohl beide „voll
aufgedreht" sind.

**Rec.709** — Die verbreitete Vereinbarung, mit welchen Gewichten man aus Rot, Grün und
Blau eine Luminanz rechnet: **0,2126 · R + 0,7152 · G + 0,0722 · B**. Der Name stammt aus
einer Fernsehnorm. Es gibt ältere Gewichte (Rec.601, dort zählt Rot deutlich mehr) — wer
Zahlen aus beiden Rechnungen vergleicht, vergleicht Äpfel mit Birnen.
*In diesem Projekt stehen die Gewichte an genau einer Stelle (`LUMA_R/G/B` in
`bildlesen.py`), damit nicht drei Module drei Begriffe von Helligkeit führen.*

**Gammakorrektur / sRGB** — Bildzahlen in einer üblichen Datei sind **nicht**
proportional zur Lichtmenge, sondern gekrümmt gespeichert: Die dunklen Stufen liegen
enger beieinander als die hellen, weil das Auge dort feiner unterscheidet. Diese Krümmung
heisst Gamma, die verbreitete Ausprägung **sRGB**. Wer physikalisch rechnen will (Licht
addieren, Mittelwerte über Helligkeiten bilden), muss sie zuerst herausrechnen —
*linearisieren*; wer fragt „wie viel Fläche sieht hell aus", darf und soll es nicht.
*In diesem Projekt wird ausdrücklich **nicht** linearisiert, und im Docstring steht
warum: Die Schwellen der Belichtungsprüfung meinen, was man sieht.*

**Clipping (ausgefressen / zugelaufen)** — Wenn ein Bildbereich am oberen oder unteren
Ende der Skala anstösst und dort **keine Zeichnung mehr** trägt: Alles ist gleich weiss
beziehungsweise gleich schwarz, und die Unterschiede, die es einmal gab, sind
unwiederbringlich fort. Oben heisst es umgangssprachlich *ausgefressen*, unten
*zugelaufen*.
*In diesem Projekt ist es ausdrücklich **nicht** immer ein Fehler: Die Messung des
Referenzkorpus (`auf-20260818-14`) ergab „oben hell, unten offen" — 7,55 % der Fläche
liegen über 0,95, das Sechsfache gewöhnlicher Fotos. Der Prompt-Baustein sagt darum
`allowed to clip`, ausdrücklich, weil es Absicht ist.*

**Belichtungsrahmen** — In diesem Projekt der Satz von Schwellen, gegen den ein Bild auf
Helligkeit geprüft wird (`Rahmen` in `src/aiimaging/belichtung.py`). Der Begriff ist eigens
eingeführt, weil die geerbte Lösung diese Schwellen als **feste Konstanten** führt — und
eine feste Schwelle beschreibt nicht gute Belichtung, sondern einen **Stil**. Jeder Rahmen
sagt darum mit, **welche seiner Zahlen gemessen sind**; eine ungemessene Schwelle darf
höchstens warnen und nie einen Fehler melden.

**EXR** — Bildformat mit hoher Genauigkeit, das Werte ausserhalb von 0–255 speichern
kann. Notwendig für Tiefendaten, weil dort echte Meterwerte stehen.

**Compositor** — Nachbearbeitungsstufe im Renderer, in der einzelne Passes verrechnet
und ausgegeben werden.

**Sample** — Ein einzelner Rechenschritt pro Bildpunkt beim Raytracing. Mehr Samples
bedeuten weniger Bildrauschen und längere Rechenzeit.
*Wichtige Einschränkung, am 20.08.2026 gemessen: Bei eingeschaltetem* **adaptivem
Sampling** *ist die eingestellte Samplezahl eine* **Obergrenze** *und keine Angabe der
Rechenzeit — derselbe Lauf brauchte mit 6000 Samples zwölf Sekunden und mit 3000
Samples ohne adaptives Sampling über drei Minuten. Wer aus einer Samplezahl auf eine
Dauer schliesst, kann um mehr als eine Grössenordnung danebenliegen.*

**Adaptives Sampling** — Der Renderer misst während des Rechnens, wie stark ein
Bildbereich noch rauscht, und **hört dort früher auf**, wo es schon ruhig ist. Eine
glatte weisse Wand braucht wenige Rechenschritte, eine Spiegelung mit Unschärfe viele.
Das spart oft ein Vielfaches an Zeit — und macht die eingestellte Samplezahl zu einer
Obergrenze statt zu einer Vorgabe. *In Blender/Cycles voreingestellt; für Messungen der
Laufzeit muss es abgeschaltet werden, sonst misst man das Abbruchkriterium statt den
Renderer.*

**Blockpufferung (der Standardausgabe)** — Ein Programm schreibt seine Ausgabe nicht
Zeichen für Zeichen, sondern sammelt sie und gibt sie in Blöcken ab. Wohin geschrieben
wird, ändert das Verhalten: Auf einem Terminal wird meist zeilenweise abgegeben, in eine
**Datei** oder **Pipe** blockweise. Wer die Ausgabe eines fremden Programms beobachtet,
sieht darum nicht, was es sagt, sondern was es **abgegeben** hat.
*Praktische Folge in diesem Projekt: Blenders umgeleitete Ausgabe wächst gemessen nur
alle 32 Sekunden (`docs/BLENDER_AUSGABETAKT_2026-08-20.md`) — jede Stillstandsfrist muss
über diesem Takt liegen, sonst bricht sie gesunde Läufe ab.*

**Sandbox-Paket (Snap, Flatpak)** — Eine Art, ein Programm samt allem, was es braucht,
in einem abgeschlossenen Bereich auszuliefern. Der Vorteil: Es läuft überall gleich. Der
Preis: Es sieht nur einen Ausschnitt des Systems, und was ausserhalb liegt, darf es
manchmal nicht anfassen.
*Am 19.08.2026 gemessen und teuer: Das Snap-Paket von Blender 5.2.0 LTS — das einzige mit
GPU-Unterstützung — **beendet sich bei einer Umleitung der Ausgabe in eine Datei nach
1,3 Sekunden mit Rückgabewert 0, ohne Ausgabe und ohne Bild**. An vier Ablageorten
gegengeprüft. Über eine Pipe rendert dasselbe Programm einwandfrei. Eine Erfolgsmeldung
ohne Ergebnis ist die teuerste Sorte Fehler, die dieses Projekt kennt.*

**Artefakt einer Messung** — Ein Ergebnis, das nicht die untersuchte Sache beschreibt,
sondern den Aufbau, mit dem gemessen wurde. Es sieht genauso überzeugend aus wie ein
echtes — oft überzeugender, weil es sauber und reproduzierbar ist.
*In diesem Projekt am 20.08.2026 in Reinform: Blenders Ausgabetakt von 32 Sekunden war an
zwei CPU-Läufen sauber reproduzierbar und beschrieb doch nur Cycles-auf-CPU. Auf der GPU
gibt es gar keinen Takt. Die daraus abgeleitete Frist hätte auf der Maschine, die
wirklich rechnet, jeden gesunden Lauf abgebrochen.*
*Merksatz: Eine Messung gilt so weit, wie gemessen wurde — und das gehört in denselben
Satz wie das Ergebnis.*

**Pipe-Blockade (deadlock beim Lesen)** — Startet ein Programm ein anderes und leitet
dessen Ausgabe in eine **Pipe**, ohne sie zu lesen, so bleibt das gestartete Programm
stehen, sobald der Puffer der Pipe voll ist: Es wartet darauf, weiterschreiben zu dürfen.
Der Aufrufer wartet gleichzeitig darauf, dass es fertig wird — beide warten aufeinander.
*Die Fortschrittswache dieses Projekts leitet darum in eine temporäre Datei um und nicht
in eine Pipe. Sonst hätte ausgerechnet die Wache, die einen Stillstand verhindern soll,
selbst einen erzeugt.*

**Add-on / Plugin** — Eine Erweiterung, die *innerhalb* eines Wirtsprogramms läuft und
dessen Innenleben mitbenutzt. Technisch bequem, lizenzrechtlich heikel: Ein Add-on ist
kein eigenständiges Programm.
*In diesem Projekt ausgeschlossen (Regel 2).*

**bpy** — Blenders Python-Schnittstelle. `import bpy` funktioniert nur *innerhalb* von
Blender und macht den eigenen Code zum Teil von Blender.

**Depsgraph (Abhängigkeitsgraph)** — Blenders innere Buchhaltung darüber, welches Objekt
von welchem abhängt, und damit die Liste dessen, was zum Zeitpunkt des Renderns
tatsächlich in der Szene steht — nach allen Modifikatoren, Kopien und Verknüpfungen.
*Wer wissen will, ob ein Nachbargebäude die Sicht verstellt, muss dagegen fragen und nicht
gegen die Rohobjekte. Das ist einer der wenigen Punkte, die sich nur* innerhalb *von
Blender beantworten lassen — und darum in diesem Projekt jenseits der Prozessgrenze im
Runner liegen, nicht in `src/aiimaging/kameras.py`.*

---

**Brennweite** — Die Kenngrösse eines Objektivs in Millimetern. Klein heisst weitwinklig
(28 mm: viel Bild, aber kippende Fluchten), gross heisst teleskopisch (200 mm: enger
Ausschnitt, flache Wirkung). *In der Architekturfotografie sind 24–35 mm üblich, weil man
auf der Strasse steht und nicht beliebig weit zurücktreten kann.*

**Bildwinkel (Field of View, FOV)** — Wie viel von der Welt das Bild erfasst, als Winkel.
Er folgt aus Brennweite und Sensorgrösse: `2·atan(Sensor / (2·Brennweite))`. Ein 28-mm-
Objektiv auf Kleinbild (36 mm breiter Sensor) sieht rund 65° in die Breite.
*Der Bildwinkel ist der Grund, warum sich der Kameraabstand ausrechnen und nicht bloss
schätzen lässt: Wenn man weiss, wie breit ein Gebäude ist und welchen Winkel die Kamera
erfasst, folgt der Abstand aus dem Tangens. In diesem Projekt `bildwinkel` in
`src/aiimaging/kameras.py`.*

**Sensor / Bildebene** — Die lichtempfindliche Fläche in der Kamera, auf der das Bild
entsteht: früher der Film, heute ein Chip. Ihre **Grösse** in Millimetern bestimmt zusammen
mit der Brennweite, wie viel ins Bild passt (siehe *Bildwinkel*); ihre **Lage im Raum**
bestimmt, ob senkrechte Kanten des Bauwerks im Bild senkrecht bleiben (siehe *stürzende
Linien*). *Im Renderer gibt es keinen Chip — „Sensorbreite" ist dort eine gesetzte Zahl,
und die Bildebene steht genau so, wie die Kamera ausgerichtet wird.*

**Kleinbild (Vollformat, 35 mm)** — Das Sensor- bzw. Filmformat 36 × 24 mm, in den 1920er-
Jahren von Oskar Barnack für Leica aus dem Kinofilm abgeleitet und bis heute der
Bezugsmassstab der Fotografie. Weil eine Brennweite nur zusammen mit einem Format etwas
aussagt — 90 mm sind an einer Grossformatkamera weitwinklig und am Kleinbild ein Tele —,
rechnet man fremde Formate um: Das **Kleinbild-Äquivalent** ist die Brennweite, die am
Kleinbild denselben Bildwinkel ergäbe. *Alle Brennweitenzahlen der Kamerarecherchen sind
Kleinbild-Äquivalente. Der Objektivsatz, den die Dokumentationsnorm für 4 × 5 Zoll
vorschreibt (65/90/150/210 mm), entspricht umgerechnet 18/25/42/59 mm Kleinbild.*

**Seitenverhältnis** — Breite zu Höhe des Bildrahmens, meist als Verhältnis (3:2) oder als
Dezimalzahl (1,50) angegeben. Gebräuchlich sind 1:1 (Quadrat), 4:5 hoch = 1,25 (Planfilm
4 × 5 Zoll, heute auch Instagram), 5:7 = 1,40, 3:2 = 1,50 (Kleinbild), 16:9 = 1,78
(Bildschirm) und ab 2,0 „Panorama". *Für dieses Projekt ein wunder Punkt: Der Hausstil
`kosmo_standard` schreibt ein Quadrat vor, und kein einziger geprüfter fotografischer
Standard arbeitet quadratisch. Das Quadrat ist eine Stilentscheidung gegen die Konvention,
nicht innerhalb ihrer — für einen 40 × 15 m breiten Bau (8:3) das ungünstigste verfügbare
Format.*

**Fachkamera (Grossformat)** — Eine Kamera, bei der Objektivträger und Bildebene als zwei
getrennte, gegeneinander verschieb- und neigbare Standarten auf einer Schiene sitzen.
Genau diese Verstellbarkeit erlaubt es, den Bildausschnitt zu verschieben, ohne die Kamera
zu neigen. Übliche Formate 4 × 5, 5 × 7 und 8 × 10 Zoll. *Die amerikanische
Bauwerksdokumentationsnorm HABS schreibt sie ausdrücklich vor. Im Renderer gibt es keine
Standarten — was sie leistet, ist dort der Zahlenwert* **Shift**.

**Planfilm (Blattfilm)** — Film in einzelnen Blättern statt auf einer Rolle, in Zoll
gemessen (4 × 5, 5 × 7, 8 × 10). Er ist der Bildträger der Fachkamera und die Herkunft der
Seitenverhältnisse 1,25 und 1,40, die bis heute benutzt werden — auch von Leuten, die nie
einen Planfilm in der Hand hatten.

**Bildkreis** — Ein Objektiv wirft keinen rechteckigen Ausschnitt, sondern einen runden
Lichtfleck. Das Rechteck des Sensors liegt darin. Ist der Kreis deutlich grösser als das
Rechteck, lässt sich das Rechteck darin verschieben, ohne dass eine Ecke dunkel bleibt —
und genau das ist die technische Voraussetzung für *Shift* und *Shift-Stitch*. Ein
Objektiv mit knappem Bildkreis kann beides nicht.

**Stürzende Linien (konvergierende Vertikalen)** — Senkrechte Kanten eines Bauwerks, die
im Bild nicht parallel bleiben, sondern aufeinander zulaufen. Sie entstehen **allein**
dadurch, dass die Kamera geneigt wird, die Bildebene also nicht mehr lotrecht steht — nicht
durch die Brennweite, nicht durch den Standort und ausdrücklich unabhängig von der
Augenhöhe der Fotografin. Steht die Bildebene lotrecht, bleiben die Vertikalen parallel,
egal wie hoch oder tief die Kamera sitzt.
*Das ist die einzige institutionell verbindliche Regel des ganzen Fachs: Die
US-Bundesnorm HABS/NPS verlangt die Perspektivkorrektur zwingend und **bei der Aufnahme**.
Und dieses Projekt verletzt sie in jedem Bild, das es bisher erzeugt hat:
`src/aiimaging/kameras.py` legt das Blickziel über die Augenhöhe
(`ZIEL_ANTEIL_HOEHE = 0.20`), was 9,46° Neigung und rund 9 bis 12 % Konvergenz ergibt (bei waagrechter Kamera waere sie exakt null). Der
Kommentar an dieser Stelle nannte das „den üblichen Griff der Architekturfotografie" — der
übliche Griff ist das Gegenteil: waagrecht halten und shiften (`docs/KAMERAREGELN_2026-08-21.md`).*

**Perspektivkorrektur** — Das Vermeiden oder Beseitigen stürzender Linien. Zwei Wege: bei
der Aufnahme (Fachkamera oder Shift-Objektiv, Kamera bleibt waagrecht) oder nachträglich
am Rechner, indem das Bild verzogen wird. Der zweite Weg kostet Bildfläche und Auflösung
und wirkt bei starker Korrektur unnatürlich. *Die Dokumentationsnorm lässt nur den ersten
zu; in einem Renderer ist er ohnehin der billigere.*

**Shift (Tilt-Shift-Objektiv, PC-Objektiv)** — Das Verschieben des Objektivs **parallel**
zur Bildebene, meist nach oben. Die Kamera bleibt dabei waagrecht, der Ausschnitt wandert
trotzdem nach oben — man bekommt das Dach ins Bild, ohne zu kippen. Übliche Höchstwerte am
Kleinbild sind 11 bis 12 mm. Das **Tilt** desselben Objektivtyps meint etwas anderes: das
Neigen der Objektivebene, um die Schärfe schräg durch den Raum zu legen; mit der
Perspektive hat es nichts zu tun. *Im Renderer ist Shift ein reiner Zahlenwert und kein
Bauteil — die häufigste handwerkliche Fehlerquelle der realen Architekturfotografie lässt
sich hier per Konstruktion ausschliessen, indem Neigung und Rollwinkel auf 0 geklemmt
werden und die Höhenkorrektur über Shift läuft.*

**Unsymmetrischer Bildrahmen (durch Shift)** — Die Folge, die man beim Shift übersieht:
Weil der Rahmen gegen die Blickachse verschoben ist, reicht er **oben weiter und unten
weniger weit**. Die Achse — bei waagrechter Kamera zugleich der Horizont — sitzt nicht
mehr in der Bildmitte.
*Daraus folgt eine Regel, die dem Gefühl widerspricht: Wer stärker shiftet, muss unter
Umständen **weiter weg** statt näher heran, weil ihm sonst der Gebäudefuss aus dem Bild
fällt. Welche Kante bindet, entscheidet der Bau: Beim hohen Turm bindet das Dach, und der
Shift lässt die Kamera näher heran; beim flachen Bau aus der Nähe bindet der Fuss, und er
kostet Abstand. Im Grenzfall — 12 mm Shift bei 24 mm Sensorhöhe — liegt der Horizont
exakt auf der Bildunterkante, und zwar **unabhängig von der Brennweite**.*

**Ungerufenes Modul (die tote Kante im Grossen)** — Ein Modul, das vollständig gebaut,
getestet und dokumentiert ist — und von keiner Stelle des Produktivwegs aufgerufen wird.
*Es fällt nicht auf, und das ist der Punkt: Seine Tests sind grün, seine Abdeckung sieht
vorbildlich aus, die Suite meldet nichts. Nur beurteilt es nie etwas Wirkliches. In
diesem Projekt traf es `komposition.py` — 1400 Zeilen fotografisches Regelwissen mit
Belegstufen und Quellenangaben, ein halbes Jahr lang ausschliesslich von den eigenen
Tests gerufen. Ein Regelwerk, das nur seine eigenen Tests beurteilt, beurteilt nichts.
Die Prüfung dagegen ist billig: auflisten, welche Module ausserhalb von `tests/`
niemand nennt.*

**Auswählen gegen den eigenen Rauschboden (Kreisschluss)** — Den besten Wert einer
Messreihe daran messen, wie stark **dieselbe** Reihe streut.
*Sieht nach Statistik aus und ist keine: Der Abstand zwischen dem Besten und dem Zweiten
einer Stichprobe hängt systematisch mit deren eigener Streuung zusammen — die Prüfung
bestätigt sich selbst. Der Ausweg ist ein **unabhängig** gemessener Boden aus einer
anderen Reihe. In diesem Projekt sind das 0,2269 aus neun Läufen desselben Aufbaus.*

**Bester Wurf gegen besserer Startwert** — Zwei verschiedene Aussagen über dasselbe
Ergebnis. „Ich behalte das bestbewertete von drei Bildern" ist immer richtig — man nimmt
den besten Wurf, den man hat. „Startwert 2 ist besser als Startwert 0" ist nur richtig,
wenn der Abstand grösser ist als das Rauschen.
*Der Unterschied ist nicht akademisch: Aus der zweiten Aussage folgt, dass man diesen
Startwert künftig bevorzugt — und damit bevorzugt man Rauschen. In diesem Projekt trennt
der Auswahlbericht die beiden seit dem 23.08.2026 ausdrücklich; selbst der oft zitierte
Fall ρ = −0,91 gegen −0,27 ist gegen den gemessenen Boden **nicht** belegt.*

**Sensorbezug (`sensor_fit`)** — Die Angabe, auf welche Bildkante sich eine genannte
Sensorgrösse bezieht. Bei `AUTO` bezieht das Renderprogramm sie auf die **grössere**
Bildkante, bei `HORIZONTAL` immer auf die Breite.
*Für Quer- und Quadratformate ist das dasselbe, und darum fällt ein falscher Bezug nie
auf, solange nur quer gerendert wird. Im **Hochformat** gehen die beiden auseinander:
Bildwinkel und Ausschnitt sind dann andere als die, mit denen die Kamera gerechnet wurde
— still und in beide Richtungen. Der Hausstil dieses Projekts ist quadratisch bis
hochformatig; der Bezug wird deshalb seit dem 22.08.2026 ausdrücklich gesetzt statt
überlassen.*

**Shift-Stitch** — Mehrere Aufnahmen vom **selben Standort** mit seitlich versetztem
Objektiv, die anschliessend zu einem breiteren Bild zusammengesetzt werden. Weil der
Aufnahmepunkt sich nicht bewegt, bleibt das Ergebnis eine einzige, geometrisch korrekte
Zentralprojektion — anders als beim Schwenken der Kamera, wo die Teilbilder verschiedene
Perspektiven haben. Erreichbar ist damit am Kleinbild ein Seitenverhältnis von rund 2,42:1.

**Einpunkt-, Zweipunkt- und Dreipunktperspektive** — Wie viele Fluchtpunkte ein Bild hat,
und was dadurch parallel bleibt. **Einpunkt:** Kamera waagrecht und senkrecht auf die
Fassade — Vertikalen *und* Horizontalen der Fassade bleiben parallel, es gibt einen
Fluchtpunkt, meist im Bild. **Zweipunkt:** Kamera waagrecht, aber schräg zur Fassade — nur
die Vertikalen bleiben parallel, zwei Fluchtpunkte liegen auf dem Horizont, meist
ausserhalb des Bildes. **Dreipunkt:** Kamera geneigt — nichts bleibt parallel, der dritte
Fluchtpunkt liegt über oder unter dem Bild. *Für den Code der entscheidende Satz: Ein- und
Zweipunkt unterscheiden sich **nur im Azimut**, beide haben Neigung 0°. Die
Dreipunktperspektive ist die einzige mit Neigung ≠ 0 — und damit der Fall der stürzenden
Linien.*

**Fluchtpunkt** — Der Punkt, in dem sich im Bild Linien treffen, die in Wirklichkeit
parallel verlaufen. *Es gibt eine belegte Konvention dafür, wo er sitzt, und sie gilt nur
im Innenraum: Bei der frontalen Einpunktaufnahme gehört er in die Bildmitte, die Kamera
also auf die Mittelachse des Raums und senkrecht zur Stirnwand. Für Aussenaufnahmen sagt
keine gefundene Quelle, wo er sitzen soll — nur, wo er geometrisch landet.*

**Horizontlinie** — Die Linie im Bild, die auf Höhe des Objektivs liegt; alles, was in der
Welt auf Kamerahöhe liegt, liegt im Bild auf dieser Linie. Bei waagrechter Kamera **ohne**
Shift liegt sie exakt in der Bildmitte — das ist keine Gestaltungswahl, sondern eine
Zwangsfolge, unabhängig von Brennweite und Abstand. Shift verschiebt sie nach unten, bei
vollem Shift bis auf wenige Prozent über die Bildunterkante.
*Damit ist der Bodenanteil eines Aussenbildes eine eingestellte Grösse zwischen rund 50 %
(kein Shift) und rund 4 % (voller Shift) — und die an der Versuchsszene gemessenen 59,8 %
Boden sind mit korrekt gehaltener Kamera überhaupt nicht erzeugbar.*

**Über-Eck-Ansicht (Drei-Viertel-Ansicht)** — Die Aufnahme schräg auf eine Gebäudeecke, bei
der zwei Fassaden gleichzeitig sichtbar sind; üblicherweise um 45° zur Fassadennormale,
geometrisch eine Zweipunktperspektive. *Sie ist der Regelfall, nicht die Ausnahme: Die
HABS-Norm verlangt zwei Über-Eck-Ansichten gegen eine einzige frontale. Für dieses Projekt
ist sie der übersehene dritte Weg — ein 40 × 15 m breiter Bau (8:3) projiziert sich schräg
betrachtet nicht mehr als 8:3. Die Perspektive erledigt die Formatanpassung, die weder der
Rahmen noch ein gefüllter Vordergrund leisten kann.*

**Rektilineare Projektion** — Die Abbildung, bei der jede Gerade der Welt auch im Bild eine
Gerade bleibt. Sie ist der Normalfall gewöhnlicher Objektive und die Abbildung jeder
gerenderten Lochkamera; das Gegenstück ist das Fischauge, das gerade Kanten krümmt. Ihr
Preis ist die Randstreckung (siehe *Volumenanamorphose*).

**Volumenanamorphose (Randstreckung)** — Räumliche Körper am Bildrand erscheinen gedehnt:
Kugeln werden zu Ellipsen, Köpfe breit. Das ist kein Objektivfehler, sondern die
unvermeidliche Folge der rektilinearen Projektion, und sie wächst mit dem Bildwinkel. Die
Flächenstreckung in der Bildecke gegenüber der Bildmitte beträgt `1/cos³θ`, wobei θ der
halbe Diagonal-Bildwinkel ist: bei 35 mm rund 1,6-fach, bei 24 mm 2,4-fach, bei 17 mm über
4-fach. *Das ist eine harte Grenze für Personen, Bäume und Fahrzeuge am Bildrand — nicht
für den Baukörper selbst, dessen ebene Flächen korrekt abgebildet werden.*

**Objektivverzeichnung** — Ein optischer Fehler, bei dem gerade Kanten gekrümmt abgebildet
werden, nach aussen (Tonne) oder nach innen (Kissen). Mit Perspektive hat sie nichts zu
tun. *Drei Dinge werden in der Ratgeberliteratur ständig zu einer „Weitwinkelverzerrung"
verrührt und sind sauber zu trennen: die perspektivische Wirkung (hängt am **Abstand**),
die Randstreckung (hängt am **Bildwinkel**) und die Verzeichnung (hängt am **Objektiv**).
Eine gerenderte Lochkamera hat die dritte per Definition nicht — sie kann nur absichtlich
eingebaut werden.*

**Streckungsverhältnis** — Der Abstand zum entferntesten wichtigen Objekt im Bild, geteilt
durch den Abstand zum nächsten. Je grösser die Zahl, desto stärker übertreibt das Bild die
Tiefe: Ein Sessel 0,8 m vor der Linse und die Stirnwand in 6,4 m ergeben 8:1, und der
Sessel wirkt riesig. *Diese Grösse ist als Prüfwert robuster als eine Brennweitenschwelle,
weil die Übertreibung nicht von der Brennweite abhängt, sondern vom Verhältnis der
Abstände — dieselbe Brennweite lügt nah und sagt fern die Wahrheit. Die Ableitung stammt
aus `docs/recherche/KOMPOSITION_INNEN.md` und steht in keiner Quelle.*

**Azimut** — Eine Himmelsrichtung als Winkel, im Uhrzeigersinn ab Norden gezählt: 0° Nord,
90° Ost, 180° Süd, 270° West. *Nicht zu verwechseln mit dem Winkel am Einheitskreis, der
gegen den Uhrzeigersinn ab der Ost-Achse zählt — wer die beiden verwechselt, dreht eine
ganze Kameraanlage um 90°, und zwar unauffällig.*

**Deckungsgrad** — Welcher Anteil des Bildes vom Gebäude gefüllt werden soll, als Zahl
zwischen 0 und 1. Ein Wert unter 1 schiebt die Kamera weiter weg und lässt Luft um das
Bauwerk. *Das ist die gestalterische „Zweidrittel-Komposition" als Zahl ausgedrückt: 0.55
heisst, gut die Hälfte des Bildes ist Gebäude, der Rest Himmel und Umgebung.*

**Füllgrad** — Welchen Anteil des Bildes das Bauwerk tatsächlich einnimmt. Zu
unterscheiden vom **Deckungsgrad**, der sagt, welchen Anteil es einnehmen *soll*.
*Gemessen wird er an der zugewandten Fassade, nicht in der Gebäudemitte — der Abstand
wird zur Mitte gerechnet, aber gesehen wird die nahe Seite. Und in beiden Richtungen, denn
bei einem hohen Bau im Breitbild führt die Höhe. Beide Feinheiten sind nicht Pedanterie:
Ohne sie meldet die Prüfung jedes Hochhaus und jeden langen Riegel als „zu klein im Bild".*

**Zusammenhängende Fläche (Connected Component)** — Eine Gruppe von Bildpunkten, die
lückenlos aneinandergrenzen. Ob zwei Punkte, die sich nur über eine **Ecke** berühren, als
verbunden gelten, ist eine Wahl: *Vierer-Nachbarschaft* sagt nein, *Achter-Nachbarschaft*
sagt ja.
*In diesem Projekt Vierer — mit Achter genügte ein einziger diagonaler Kontakt zwischen
Bauwerk und einem Bildfehler, damit beide gemeinsam verworfen würden. Die Regel wäre an
einer einzigen Pixelecke zerbrechlich.*

**Randberührung** — Ob eine Fläche im Bild bis an dessen Kante reicht. *Klingt nebensächlich
und ist in diesem Projekt das entscheidende Merkmal: Ein freistehendes Gebäude in der
Bildmitte berührt den Rand nicht, eine vom Tiefenschätzer in den leeren Grund gelegte
Bodenebene immer. An dieser einen Eigenschaft liessen sich die beiden trennen — und der
Anteil echter Bauwerkspunkte stieg dadurch von 41 % auf 99 %.*

**Frustum (Sichtpyramide)** — Der Raumbereich, den eine Kamera sieht: ein Pyramidenstumpf,
der von der Linse aus nach vorn breiter wird. Was ausserhalb liegt, ist im Bild nicht zu
sehen. *„Passt das Gebäude ins Bild?" heisst genau: Liegen alle acht Ecken seiner Hüllbox
innerhalb des Frustums?*

**Perspektivische Division** — Der Rechenschritt, der aus einem Punkt im Raum einen Punkt
im Bild macht: Man teilt seinen seitlichen Abstand von der Blickachse durch seine Tiefe.
Weit entfernte Dinge erscheinen dadurch klein, nahe gross. *Sie ist der Grund, warum die
scheinbare Grösse mit `1 / Abstand` geht — und darum lässt sich umgekehrt ausrechnen, wie
weit eine Kamera zurück muss, statt es zu ertasten.*

**Raycast (Strahlenschuss)** — Von einem Punkt aus einen Strahl in eine Richtung schicken
und fragen, was er als Erstes trifft. *In diesem Projekt der Test, ob ein Nachbargebäude
die Sicht auf das Bauwerk verstellt. Er braucht die vollständige Szene und liegt darum im
Runner; nur die Schrittlogik — wie weit die Kamera bei verstellter Sicht herangezogen
wird — ist reine Rechnung und liegt diesseits der Prozessgrenze
(`ziehe_bis_frei` in `src/aiimaging/kameras.py`).*

**Orthografische Projektion / Ortho-Scale** — Eine Abbildung ohne Perspektive: Parallelen
bleiben parallel, gleich grosse Dinge erscheinen gleich gross, egal wie weit weg sie sind.
Statt eines Bildwinkels hat eine solche Kamera eine **Ortho-Scale** — die Breite des
Ausschnitts in Metern. *Das ist die Darstellung von Grundriss, Schnitt und Ansicht.*

**Axonometrie** — Eine parallele Darstellung aus schräger Richtung, in der man drei Seiten
eines Baukörpers gleichzeitig sieht. *Ihre Tücke ist die Verkürzung: Aus 30° Höhenwinkel
erscheint der Grundriss auf die Hälfte gestaucht und die Höhe fast unverkürzt. Wer beim
Zuschneiden des Rahmens `sin` und `cos` vertauscht, schneidet das Gebäude an — genau
dieser Vorzeichenfehler ist im Vorläufercode nachweislich passiert und wurde dort von
einem Test festgehalten.*

**Bildebenen: Vordergrund, Mittelgrund, Hintergrund** — Die Gliederung eines Bildes in
drei Tiefenschichten. Der Vordergrund liegt nah bei der Kamera und gibt dem Bild Massstab
und einen Einstieg, der Mittelgrund trägt meist das Hauptmotiv, der Hintergrund liefert
den Zusammenhang. *Zwei Feststellungen dazu gehören zusammen: Ein Vordergrund entsteht
nicht durch die Kamerasetzung, sondern durch **Szeneninhalt** — eine Kamerabibliothek kann
ihn anfordern, aber nicht herstellen. Und dieses Projekt hat gemessen, was passiert, wenn
er fehlt: In `docs/KAMERABLICK_2026-08-19.md` wirken zwölf Ansichten eines Baukörpers ohne
Boden und ohne Umgebung falsch, obwohl alle Kennzahlen grün waren, und der Tiefenschätzer
erfindet eine Bodenebene, die es nicht gibt.*

**Anschnitt** — Ein Motiv, das der Bildrand durchschneidet, statt es ganz zu zeigen. *Hier
trennen sich zwei Welten sauber, und beide sind belegt: Die Bauwerksdokumentation verbietet
ihn (HABS verlangt die vollständige Fassade und untersagt sogar das nachträgliche
Beschneiden), die redaktionelle und künstlerische Fotografie benutzt ihn routinemässig als
Mittel. Für dieses Projekt heisst das: Anschnitt ist **kein Fehlerzustand, sondern ein
Modus**. Ein Prüfwert `vollstaendig: True` beantwortet die Dokumentationsfrage, nicht die
Bildfrage — zwölf Kameras meldeten ihn und lieferten trotzdem unbrauchbare Bilder.*

**Negativraum / funktionaler Raum** — Der bewusst leer gelassene Teil der Bildfläche.
**Und ein benannter Streit, kein Lehrsatz.** Die eine Seite hält mindestens ein Drittel
Negativraum für nötig, damit ein Bauwerk „atmen" kann, und meint damit meist den Himmel.
Die Gegenposition stammt vom Architekturfotografen Joel Tjintjelaar (BWVision):
grosszügige Leerflächen im Sinne der minimalistischen Fotografie „works against the purpose
of architectural photography"; er setzt dagegen den *functional space* — genau so viel
freie Fläche, wie das Bauwerk braucht, um eindeutig als Motiv gelesen zu werden, „no more
and no less". *Beide Positionen stammen von arbeitenden Fotografen, keine Norm entscheidet:
Geschmackssache mit Begründung, nicht Wissen. Für den Entscheid „Vordergrund füllen" ist
das der Kern — nicht belegbar ist ein grosser Bodenanteil **ohne Inhalt**; leere Fläche
wird in keiner geprüften Quelle als Gestaltungsmittel genannt, sondern als Fehler.*

**Axial / nicht-axial** — Tjintjelaars Ersatz für die üblichen Kompositionsregeln:
**axial** heisst, die waagrechten Linien des Baus laufen parallel zu den waagrechten
Bildkanten — man steht frontal davor; **nicht-axial** heisst, man sieht den Bau schräg.
Dazu kommt als zweite Grösse die Zahl der sichtbaren Fassaden. *Für ein Programm ist dieses
Begriffspaar brauchbarer als die Drittelregel, weil beides aus der Geometrie ablesbar ist:
axial heisst Azimut 0° zur Fassadennormale, nicht-axial alles andere.*

**Drittelregel** — Die verbreitetste Kompositionslehre der Fotografie: Man denkt sich zwei
waagrechte und zwei senkrechte Linien ins Bild, die es in Drittel teilen, und legt Motive
auf diese Linien oder ihre Schnittpunkte. **Sie wird breit gelehrt und ist als Beschreibung
der Praxis widerlegt.** Amirshahi, Hayn-Leichsenring, Denzler und Redies verglichen in
*Art & Perception* 2 (2014) 163–182 grosse Bildmengen — darunter 679 regelkonforme und 403
nicht regelkonforme Fotografien, 200 hochbewertete Aufnahmen und 727 Gemälde — mit
subjektiven Bewertungen: Die ästhetische Bewertung hing nur schwach mit der beurteilten
Drittelregel zusammen (Rangkorrelation ρ = 0,17) und **gar nicht** mit den gerechneten
Werten; hochbewertete Bilder erreichten ungefähr so niedrige Werte wie Bilder, die der
Regel nicht folgen.
Dazu die Begriffsgeschichte, die den zweiten Teil der Sache erklärt: 1797 meinte John
Thomas Smith mit „Rule of Thirds" ein **Flächenverhältnis von hell zu dunkel** (⅓ zu ⅔),
nicht die Lage eines Motivs; 1908 lautete die Fassung „nahe, aber nicht **in** der Mitte";
**1955 vermischte das *British Journal of Photography* Drittelregel und goldenen Schnitt**
erstmals, und seither werden beide in einem Atemzug genannt; die heute gelehrte Fassung
(„exakt auf den Schnittpunkten") entstand erst um 1960.
*Für dieses Projekt: Die Drittelregel darf als wählbare Voreinstellung im Code stehen — als
**Setzung des Owners**. Sie darf nicht mit „so machen es Architekturfotografen" begründet
werden, und sie sollte im Code auch nicht so heissen.*

**Goldener Schnitt** — Die Teilung einer Strecke im Verhältnis 1 : 1,618, im Bild also bei
etwa 0,382 der Kante. Als ästhetisches Gesetz ist er unhaltbar: George Markowsky wies 1992
im *College Mathematics Journal* 23, 2–19 nach, dass die verbreiteten Behauptungen zu
Kunst und Architektur grösstenteils falsch oder aus wählbaren Massen zusammengesucht sind
— und dass Versuchspersonen zwischen 48 Rechtecken im Bereich 1,6 bis 1,7 überhaupt keinen
Unterschied sahen. *Er ist ausserdem **nicht** dasselbe wie die Drittelregel (0,382 gegen
0,333); dass beide gemeinsam genannt werden, geht auf einen Redaktionsfehler von 1955
zurück. Wer sie in einem Atemzug nennt, wiederholt ihn.*

**Bürgerliche, nautische und astronomische Dämmerung** — Die drei Dämmerungsphasen, über
den Winkel der Sonne unter dem Horizont definiert: bürgerlich 0° bis −6°, nautisch −6° bis
−12°, astronomisch −12° bis −18°. *Das sind feste astronomische Konventionen, in jedem
Sonnenstandsrechner gleich implementiert — im Gegensatz zur „goldenen Stunde" also Zahlen,
auf die sich ein Programm stützen darf.*

**Goldene Stunde / blaue Stunde** — Die Tageszeiten kurz nach Sonnenaufgang und kurz vor
Sonnenuntergang (goldene Stunde, warmes flaches Licht) beziehungsweise die Zeit danach, in
der der Himmel tiefblau steht (blaue Stunde). **Beide haben keine definierte Dauer und
keinen definierten Winkel** — die vielzitierten Werte (goldene Stunde +6° bis −4°
Sonnenhöhe, blaue Stunde −4° bis −6°) sind Konventionen von Planungsprogrammen, keine Norm.
*Ein Programm darf mit ihnen rechnen, aber nur als **Setzung**, nicht als gefundenes
Faktum — dieselbe Unterscheidung wie unter* Setzung vs. Messung. *Die blaue Stunde hat
dabei ein technisches Argument für sich: Nur dann zeichnen Kunstlicht im Gebäude und
Himmelshelligkeit gleichzeitig, der Kontrast ist also klein genug für ein Bild.*

**Blendenstufe (EV, Lichtwert)** — Die Masseinheit für Helligkeitsunterschiede in der
Fotografie: Eine Stufe ist eine Verdopplung oder Halbierung der Lichtmenge, zwei Stufen das
Vierfache, zehn Stufen das Tausendfache. „EV" (exposure value) meint dasselbe. *Die einzige
wiederkehrende Zielgrösse der Innenraumfotografie ist in dieser Einheit formuliert: Die
Fensterflächen sollen im fertigen Bild ein bis zwei Blendenstufen heller wirken als der
Innenraum — also Faktor 2 bis 4, nicht mehr (ausgebrannt) und nicht weniger (wirkt tot). Es
ist kein Normwert, sondern die Faustregel arbeitender Fotografen.*

**Dynamikumfang (Kontrastumfang)** — Der Abstand zwischen der hellsten und der dunkelsten
Stelle, die eine Szene enthält oder eine Kamera in einer Aufnahme festhalten kann,
gemessen in Blendenstufen. *Das ist der Grund für den Fenster-Innen-Konflikt: Ein
tageslichtbeleuchteter Innenraum umfasst je nach Quelle 14 bis 18 Stufen, mit der Sonne im
Bild noch weit mehr; eine Einzelaufnahme fasst grob 12 bis 14. Was nicht hineinpasst,
läuft zu oder frisst aus (siehe* Clipping*). Im Renderer entschärft sich das, weil dort
Helligkeitswerte ungeklippt gespeichert werden können (siehe* EXR *und* Half-Float*).*

**Belichtungsreihe (Bracketing)** — Dieselbe Aufnahme mehrfach mit verschiedener Belichtung,
anschliessend zu einem Bild verrechnet. In der Innenraumfotografie das Standardverfahren:
drei Bilder bei −2/0/+2 EV im Normalfall, fünf bei schwierigem Licht, sieben bei
Dämmerung. *Für dieses Projekt kein Verfahren, sondern eine Auskunft: Die Zahl der nötigen
Stufen sagt, wie gross der Kontrast eines echten Innenraums ist.*

**flambient (flash + ambient)** — Ein Verfahren der Innenraumfotografie: Man belichtet auf
das **Fenster** — die Aussenwelt ist dann richtig gezeichnet, der Raum zu dunkel — und
hebt anschliessend den Raum mit entfesseltem Blitz auf dieselbe Belichtung an. Der Blitz
muss neben der Kamera stehen, sonst spiegelt er sich im Fenster. Das Kunstwort mischt
*flash* und *ambient* (vorhandenes Licht).

**dpi (dots per inch, Punkte pro Zoll)** — Wie fein ein Bild gedruckt wird. 300 dpi gilt
als Druckqualität, 72 dpi als Bildschirmwert. *Die Zahl ist für sich genommen ohne
Aussage: Sie sagt erst zusammen mit der Ausgabegrösse etwas, und was ein Bild wirklich
hergibt, ist seine Pixelzahl. Genau so verfahren die Publikationen — die geprüften
Einreichungsvorschriften regeln Pixelzahl und Auflösung, aber **kein einziges
Seitenverhältnis**.*

**HABS (Historic American Buildings Survey)** — Das Bauwerksdokumentationsprogramm des
US-amerikanischen National Park Service, dessen Aufnahmen in die Library of Congress
eingehen. Seine Fotografie-Richtlinien sind die **einzige verbindliche Vorschrift**, die
die Recherchen dieses Projekts gefunden haben: Grossformat-Fachkamera, Perspektivkorrektur
zwingend bei der Aufnahme, Formate 4 × 5 / 5 × 7 / 8 × 10 Zoll mit Vorzug für 5 × 7, ein
fester Objektivsatz, kein Beschneiden — und ein Katalog der verlangten Ansichten, in dem
zwei Über-Eck-Ansichten einer frontalen gegenüberstehen. *Alles andere, was in der
Architekturfotografie „Regel" heisst, ist Ratgeberliteratur.*

---

**IFC4 und IFC2X3** — Zwei Fassungen desselben Austauschformats. IFC2X3 ist von 2006 und
gilt bis heute als die verlässlichste gemeinsame Sprache; IFC4 von 2013 kann mehr,
verbreitet sich aber langsamer. *Beide sind in freier Wildbahn anzutreffen — an 40 echten
Bürodateien gemessen: 30-mal IFC4, 10-mal IFC2X3, und die zehn kamen alle aus ArchiCAD.
Ein Prüfwerkzeug, das nur eine Fassung kennt, ist damit für ein Viertel der Wirklichkeit
blind.*

**Pflichtattribut** — Eine Angabe, die eine Norm nicht als „darf" führt, sondern als
„muss". *Der Unterschied zwischen den beiden IFC-Fassungen liegt genau hier und ist der
Grund, warum eine selbstgebaute Testdatei danebengehen kann: Die Herkunftsangabe
`IfcOwnerHistory` ist in IFC2X3 **Pflicht** und in IFC4 **freigestellt**. Wer eine
IFC4-Datei kennt und daraus eine IFC2X3-Datei baut, lässt sie weg — und erzeugt eine
Datei, die aussieht wie IFC2X3 und keines ist.*

**OwnerHistory** — Das Feld in einer IFC-Datei, das festhält, wer ein Bauteil wann mit
welchem Programm angelegt oder geändert hat. *Siehe Pflichtattribut: in IFC2X3 zwingend,
in IFC4 nicht.*

**Schema-Validierung** — Eine Datei gegen die Regeln ihres Formats prüfen: Sind alle
Pflichtangaben da, haben alle Felder den richtigen Typ, stimmen die Verweise? *Der
Unterschied zum blossen Einlesen ist der entscheidende: Eine Datei kann sich fehlerfrei
öffnen lassen und trotzdem ungültig sein. Eine selbst erzeugte IFC2X3-Testdatei dieses
Projekts liess sich lesen — und sammelte in der Validierung dreizehn Fehler. **Dass etwas
gelesen wird, ist kein Beleg dafür, dass es gültig ist.***

**`preprocessor_version` und `originating_system`** — Zwei benachbarte Felder im Kopf
jeder STEP-/IFC-Datei (Position 5 und 6 im `FILE_NAME`-Eintrag). Das eine nennt die
Bibliothek, die geschrieben hat, das andere das Programm, aus dem exportiert wurde.
*An 40 echten Dateien gemessen trägt Feld 5 in **zwei von drei Fällen einen fremden
Namen** — die Exportbibliothek statt des Programms (`DDS_IFC` für ArchiCAD, `ODA SDAI`
für Revit). Erkannt wurde trotzdem alles, weil beide Felder in derselben Zeichenkette
standen. Hiesse eine Exportbibliothek einmal „Rhino…", ergäbe Feld 5 eine **falsche**
Herkunft — und eine falsche Herkunft ist schlimmer als keine, weil sie eine Up-Achse zur
Bestätigung vorschlägt. Erkannt wird darum aus Feld 6 zuerst.*

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

**Negativer Prompt** — Beschreibung dessen, was *nicht* erscheinen soll.

**CFG (Classifier-Free Guidance)** — Regelt, wie streng sich das Modell an den Prompt
hält. Zu niedrig heisst beliebig, zu hoch heisst überzeichnet.

**Seed (Startwert)** — Die Zahl, mit der der Zufallsgenerator beginnt. Gleicher Seed
und gleiche Einstellungen ergeben dasselbe Bild — die Grundlage reproduzierbarer Versuche.
*Voraussetzung dafür, dass ein Ergebnis später überprüfbar ist: Ohne Seed lässt sich ein
Render nicht wiederholen, und die Schwellenstudie in Phase 4 wäre nicht durchführbar.*
*Er ist zugleich die Grösse, die eine* **Saatreihe** *durchfährt — und die eine*
**kontrollierte Reihe** *gerade nicht anfassen darf.*

**Saatreihe** — Mehrere Läufe, die sich **nur im Seed** unterscheiden. Sie messen nicht,
ob etwas besser wird, sondern **wie stark der Zufall allein streut**. Erst wenn man das
weiss, lässt sich ein Unterschied zwischen zwei Bildern überhaupt einordnen.

**Kontrollierte Reihe** — Mehrere Läufe, die sich in **genau einer** Grösse unterscheiden,
bei **festem Seed**. Sie messen die Wirkung dieser Grösse. Läuft der Seed mit, ändern sich
zwei Ursachen zugleich, und ein Unterschied lässt sich keiner von beiden zuordnen — die
Reihe beantwortet dann die Frage nicht, für die sie gefahren wurde.
*In diesem Projekt weigert sich `varianten.kontrollierte_reihe`, den Seed mitzufahren.*

**Rauschboden (Streuung einer Saatreihe)** — Die Streuung, die eine Saatreihe **bei
sonst gleichen Parametern** zeigt. Er ist der Massstab für jeden späteren Vergleich:

> Ein Unterschied ist erst dann einer, wenn er den Rauschboden übersteigt.

*Dieselbe Denkweise, mit der die Stil-Schwelle zustande kam: Dort wurde erst der Boden von
SigLIP 2 gemessen (0,526 an 4950 Bildpaaren), und erst danach war eine Schwelle darüber
sinnvoll. Eine Schwelle unter dem Boden lässt alles durch — und ein Unterschied unter dem
Rauschboden belegt nichts. Dasselbe Wort bezeichnet in Abschnitt 4 den Boden einer
Metrik über einem Bild ohne Geometrie — ein anderer Sachverhalt, siehe dort.*

**Laplace-Varianz (Schärfemass)** — Ein Zahlenwert dafür, wie stark sich benachbarte
Bildpunkte unterscheiden: viele harte Kanten ergeben einen hohen Wert, ein weiches Bild
einen niedrigen. Verbreitet als schnelles Mass für „scharf oder unscharf".
*Warnung aus dem Altbestand: Sein Variantenbewerter gewichtet die Laplace-Varianz mit 0,50
— die Hälfte des Urteils. Ein Nebel- oder Skizzenstil bekommt damit systematisch den
schlechtesten Platz, nicht weil er misslungen wäre, sondern weil er weich ist. Ein
Schärfemass ist keine Qualität, sondern eine Eigenschaft.*

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

**Monokulare Tiefenschätzung** — Aus einem einzelnen Foto eine Tiefenkarte schätzen, ohne
zweite Kamera und ohne Messgerät. Ein neuronales Netz leitet aus Bildmerkmalen ab, was
vorne und was hinten liegt. *In diesem Projekt die **Ist-Seite** der Geometrie-QA: Sie
rechnet aus dem erzeugten Bild zurück, was das Modell dort für Geometrie hält.*

**CC-BY-NC (Creative Commons, nicht kommerziell)** — Erlaubt Nutzung und Weitergabe mit
Namensnennung, **verbietet aber kommerzielle Verwertung**. Unter Regel 1 ausgeschlossen.
*Für eine wissenschaftliche Untersuchung bleibt so lizenziertes Material dennoch nutzbar —
untersagt ist die Verwertung, nicht die Forschung.*

**diffusers** — Die Apache-2.0-Bibliothek von Hugging Face, mit der Diffusionsmodelle
geladen und ausgeführt werden. *In diesem Projekt der Ersatz für ComfyUI, das wegen
GPL-3.0 ausscheidet: `diffusers` ist eine Bibliothek, die man aufruft, kein Programm, das
man umhüllt.*

**txt2img / img2img / image-edit** — Drei Betriebsarten der Bilderzeugung: aus reinem
Text, ausgehend von einem vorhandenen Bild, oder als gezielte Änderung daran. *Hier
gebraucht wird die dritte — der Cycles-Render ist der Anker, das Modell soll ihn
veredeln, nicht ersetzen.*

**Backbone** — Das Hauptmodell einer Pipeline, im Unterschied zu den Hilfsmodellen.

**Quantisierung** — Verkleinerung der Gewichte durch gröbere Zahlendarstellung. Spart
Speicher, kostet etwas Qualität.
*Nicht zu verwechseln mit* **Quantisierungsschritt** *in Abschnitt 5 — dort geht es um
die Auflösung von Messwerten, nicht um die Grösse von Modellgewichten.*

**fp16 / fp8** — Zahlenformate der Gewichte (16 bzw. 8 Bit). Je kleiner, desto
sparsamer und ungenauer.

**GGUF** — Ein quantisiertes Dateiformat, verbreitet für den Betrieb auf schwacher
Hardware.

**VRAM** — Der Speicher auf der Grafikkarte. Die harte Obergrenze dafür, welche Modelle
überhaupt laufen.

**Upscaling** — Nachträgliches Vergrössern eines Bildes unter Hinzuerfindung von Details.

**Modellkarte (Model Card)** — Das Beiblatt eines veröffentlichten Modells: eine
Textdatei im Modellverzeichnis, die beschreibt, was das Modell kann, worauf es trainiert
wurde und unter welcher Lizenz es steht. Auf Hugging Face ist es die Datei `README.md`
des Modell-Repositoriums, mit der Lizenz im Kopfblock (siehe *Front-Matter*,
Abschnitt 3). *In diesem Projekt die **Primärquelle** für jede Lizenz eines Modells: Die
Registrys der Modelle im Code (`src/aiimaging/backbone.py`, `einbetter.py`,
`tiefenschaetzer.py`) führen zu jedem Eintrag den Vermerk, gegen welche Karte und an
welchem Tag geprüft wurde.
Zwei Vorbehalte gehören dazu, beide am 18.08.2026 belegt: Kopfblock und Fliesstext
derselben Karte können verschiedene Lizenzen nennen, und die Lizenz kann innerhalb einer
Modellfamilie an der **Grösse** hängen — FLUX.2-klein gibt es als 4B unter Apache-2.0 und
als 9B nur nicht-kommerziell, Depth-Anything-V2 als Small unter Apache-2.0 und darüber
nicht-kommerziell. Wer die Familie prüft, hat nichts geprüft.*

**Gated Model / Gated Repository** — Ein Modell, dessen Gewichte erst nach Zustimmung zu
Bedingungen und oft nach einem Antragsverfahren herunterladbar sind. *Für eine
wissenschaftliche Arbeit ein Problem: Was hinter einem Antrag liegt, kann niemand
nachvollziehen.* **Gated Repository** ist dasselbe eine Stufe höher: Gesperrt ist nicht
die Gewichtsdatei allein, sondern das ganze Verzeichnis — die Modellkarte und der
Lizenztext eingeschlossen. Wer nicht angemeldet ist und zugestimmt hat, bekommt vom
Server nur ein `401` zurück (siehe *HTTP-Statuscode*, Abschnitt 3).
*Was dann noch öffentlich lesbar bleibt, ist allein die Angabe im Kopfblock der Karte —
ein Name wie `flux-1-dev-non-commercial-license`, nicht der Vertrag dahinter. Die
Lizenzprüfung vom 18.08.2026 musste FLUX.1-dev, FLUX.2-dev, SD3.5-large und DINOv3
deshalb ausdrücklich als **nicht abschliessend geprüft** führen, statt sie stillschweigend
abzuhaken (`docs/LIZENZPRUEFUNG_2026-08-18.md`, Kap. 0 und 4).*

**Selbstüberwachtes Lernen (self-supervised)** — Training ohne von Hand vergebene
Beschriftungen: Das Modell lernt aus der Struktur der Daten selbst, etwa indem es
verdeckte Bildteile vorhersagt. *DINOv2/v3 sind so trainiert, CLIP und SigLIP dagegen an
Bild-Text-Paaren.*

---

**Prompt** — Der Text, mit dem man einem Bildmodell sagt, was zu sehen sein soll.
*In diesem Projekt trägt er ausdrücklich **nicht** das Gebäude: Was gebaut ist, sagt die
Tiefenkarte; der Prompt sagt nur, wie es aussieht — Licht, Wetter, Material, Umgebung.*

**Negativ-Prompt** — Der Gegentext: was **nicht** zu sehen sein soll. Technisch rechnet
das Modell zweimal, einmal mit und einmal ohne, und zieht den Unterschied ab.
*Die Falle: Unterhalb einer Führung von 1.0 wird gar nicht mehr doppelt gerechnet, und
dann ist der Negativ-Prompt wirkungslos — er steht im Protokoll und nie im Bild. Bei
destillierten Turbo-Modellen ist das immer so.*

**Prompt-Baustein** — Ein einzelner, wiederverwendbarer Textabschnitt („weiches
gleichmässiges Tageslicht"), aus dem sich ein vollständiger Prompt zusammensetzen lässt.
*Sieben Fächer gibt es in diesem Projekt — Bildcharakter, Licht, Himmel, Atmosphäre,
Material, Bewuchs, Menschen. **Keines davon nennt ein Bauteil**, und darin liegt ihr
eigentlicher Wert: Die Einteilung ist die Regel „der Prompt beschreibt alles ausser dem
Gebäude", in Fächer gegossen.*

**Trainingssprache (eines Bildmodells)** — Die Sprache der Bildbeschreibungen, mit
denen ein Bildmodell trainiert wurde. Bei allen heute gebräuchlichen ist das ganz
überwiegend Englisch.
*Das ist keine Feinheit für Sprachliebhaber, sondern eine Messgrösse. Ein Prompt in einer
anderen Sprache wird nicht „etwas schlechter" verstanden, sondern **anders**: Das Modell
kennt das Wort nicht und füllt die Lücke mit dem, was seine Trainingsbilder zu einem
unverstandenen Prompt am häufigsten zeigen. Am 21.08.2026 im Projekt gemessen, über acht
gepaarte Startwerte: „bedeckter Himmel" ergab bei **8 von 8** einen deutlich blaueren
Himmel als „overcast sky" — also genau das Gegenteil dessen, was dastand.*

**Glossar (Übersetzungsglossar)** — Eine feste Liste „deutsches Wort → englisches Wort",
die einen Text Wendung für Wendung übersetzt. Kein Übersetzungsmodell, sondern ein
Nachschlagewerk.
*Warum in diesem Projekt ein Glossar und kein Modell: Es ist **bestimmt** — derselbe Text
ergibt immer denselben Prompt, und ohne das wäre keine Vergleichsreihe mehr lesbar —,
es ist **lizenzfrei** (Text statt Gewichte, siehe Regel 1) und es braucht kein Netz. Ein
Übersetzungsmodell lässt sich später an derselben Stelle einhängen; die Stelle heisst
`uebersetzer` und ist genau dafür da.*

**Kompositum (zusammengesetztes Wort)** — Deutsch fügt Wörter zu neuen zusammen:
*Holz* + *Fassade* = *Holzfassade*. Der letzte Teil bestimmt, was das Ding ist (der
„Kopf"), die vorderen beschreiben es näher.
*Für ein Übersetzungsglossar ist das die grösste einzelne Lücke: Jede denkbare
Zusammensetzung müsste einen eigenen Eintrag haben. In diesem Projekt wird stattdessen
zerlegt — beide Teile müssen im Glossar stehen, und die Zerlegung wird im Ergebnis
mitgeführt. Ihre Grenze: Ein Kompositum ist nicht immer die Summe seiner Teile.
`Hochhaus` wird so zu „tall house" statt „high-rise".*

**Beugung (Flexion)** — Die Veränderung eines Wortes je nach seiner Rolle im Satz:
*lang*, *langen*, *langem*; *Baum*, *Bäume*, *Bäumen*.
*Ein Glossar kennt nur die Grundform. Die Endung abzustreifen und die Grundform
nachzuschlagen ist darum die zweite grosse Verbesserung — und sie kann nichts erfinden,
weil sie nur gilt, wenn danach wirklich ein Eintrag dasteht. Welche Endungen mitspielen,
ist eine Entscheidung mit Folgen: `s` musste weichen, weil `Dachs` sonst zu „roof" wird;
`n` musste bleiben, weil ohne es jede Mehrzahl stehenbliebe (`Fassaden`).*

**Signalwort (bei der Spracherkennung)** — Ein Wort, dessen blosses Vorkommen für eine
Sprache spricht: „ohne", „zwischen", „keine" für Deutsch; „the", „without", „between"
für Englisch.
*Die Kunst liegt im Weglassen. Wörter, die es in **beiden** Sprachen gibt — „die", „in",
„am", „war", „hell", „see", „wind", „film" — dürfen nicht in der Liste stehen: Sie
entscheiden nichts und erzeugen Fehlalarme. Ein Signalwort, das in beiden Sprachen
vorkommt, ist kein Signal.*

**Dreiwertiges Urteil (ja / nein / nicht entscheidbar)** — Ein Befund, der neben „trifft
zu" und „trifft nicht zu" ausdrücklich einen dritten Zustand kennt: *dazu sagt die
Messung nichts*.
*Beispiel aus dem Projekt: „Ist dieser Prompt englisch?" Bei ``24mm f8`` steht kein
einziges Signalwort und kein Umlaut — die ehrliche Antwort ist weder ja noch nein. Wer
hier „ja" zurückgäbe, machte die Warnung stumm; wer „nein" zurückgäbe, warnte vor jeder
Objektivangabe, und nach dem dritten Fehlalarm wird auch die richtige Warnung
weggeklickt. Derselbe Gedanke wie bei `raeume: None` („nicht gemessen") gegen
`raeume: []` („gemessen, keine gefunden").*

**Übermelden (einer Prüfung)** — Eine Prüfung so einstellen, dass sie im Zweifel zu viel
meldet statt zu wenig.
*Bewusst gewählte Richtung, kein Mangel: Der Rest eines übersetzten Prompts wird gegen
einen sehr kleinen englischen Wortschatz gehalten, und alles Unbekannte gilt als „nicht
übersetzt". Damit fallen „Nordfassade" und „langen" auf — und „cantilevered" fällt
mit auf. Ein Fehlalarm kostet einen Blick, ein übersehenes deutsches Wort ein Bild.
Dieselbe Richtung wie beim Bauteilwächter.*

**Renderstil** — Eine benannte Zusammenstellung solcher Bausteine, plus einer
Handschrift: „Wettbewerbsbild", „Modellfoto", „Einskizziert".
*Nicht jeder Stil taugt zum Messen. Nebel verdeckt den Fuss des Bauwerks, eine Skizze
löst seine Kanten auf — die Geometrie-Prüfung misst dann den Stil und nicht das
Bildmodell. Darum trägt jeder Stil die Angabe, ob er messtauglich ist, und warum nicht.*

**Halluzination (bei Bildmodellen)** — Wenn das Modell etwas Plausibles, aber Falsches
erzeugt — etwas, das in der Vorgabe nicht steht: ein Dach auf einem Gebäude, das keines
hat. *Im Architekturkontext der entscheidende Mangel: ein schönes Gebäude, das nicht das
entworfene ist.*
*Die gefährliche Sorte, weil das Ergebnis **gut aussieht**. Ein abgestürztes Programm
merkt jeder; ein erfundenes Dach sieht aus wie ein Dach. In diesem Projekt am 18.08.2026
selbst erzeugt — der Prompt sagte „clean flat roof", die Geometrie war oben offen, und das
Modell tat schlicht, was dastand.*

**ControlNet-Stärke (`controlnet_conditioning_scale`)** — Der Regler dafür, wie streng
das Bild der vorgegebenen Geometrie folgen muss. 1.0 heisst: die Tiefenkarte bindet
vollständig, das Modell darf die Kubatur nicht verändern. 0.3 heisst: sie ist ein
Vorschlag. *Das ist der wichtigste Regler dieses Projekts, weil er genau die Frage stellt,
um die es geht — wie viel Freiheit darf die Bildmaschine über dem Entwurf haben, ohne ihn
zu erfinden?*

**ControlNet-Union** — Ein einzelnes ControlNet, das mehrere Steuerarten beherrscht
(Tiefe, Kanten, Pose, Segmentierung) statt nur eine. *Vorteil: ein Modell statt fünf im
Speicher. Für dieses Projekt zählt nur der Tiefenzweig, aber die verfügbaren Modelle
kommen fast alle in dieser gebündelten Form.*

**Blockwise-ControlNet** — Bauart, bei der die Steuerung nicht auf einmal, sondern in
jede Schicht des Bildmodells einzeln eingespeist wird. *Für die Benutzung unerheblich —
wichtig nur, weil solche Modelle einen eigenen Ladeweg brauchen und nicht auf jede
Pipeline passen.*

**Destilliertes Modell (Turbo, Lightning, Schnell)** — Ein grosses Modell, dem ein
kleineres oder schnelleres beigebracht wurde, dasselbe in wenigen Schritten zu tun. Statt
40 Diffusionsschritten genügen 4 bis 8.
*Der Haken steht nicht auf der Packung: Destillierte Modelle sind darauf trainiert, **ohne
Führung** zu laufen. Wer sie mit der üblichen Führung von 5.0 betreibt, bekommt
überzeichnete Bilder bei doppelter Rechenzeit — und wer den richtigen Wert 0.0 setzt,
verliert stillschweigend den negativen Prompt.*

**Führung (`guidance_scale`, klassifikatorfreie Führung)** — Wie stark der Prompt das Bild
zwingt. Technisch rechnet das Modell zweimal — einmal mit und einmal ohne Prompt — und
verstärkt den Unterschied um diesen Faktor. Hohe Werte treffen den Prompt genauer und
sehen härter aus, niedrige wirken natürlicher und weichen ab.
*Die Falle: **Unterhalb von 1.0 wird gar nicht mehr doppelt gerechnet** — und damit ist
auch der **negative Prompt** wirkungslos, denn der lebt genau von dieser zweiten
Rechnung. Er steht dann weiter im Protokoll und hat nie ein Bild beeinflusst. In diesem
Projekt meldet `src/aiimaging/render.py` diesen Fall ausdrücklich, statt ihn geschehen zu
lassen.*

**`control_context_scale`** — Ein zusätzlicher Regler mancher ControlNet-Fassungen, der
neben der Stärke auch die Reichweite der Steuerung einstellt. *Erwähnt, damit er nicht mit
der ControlNet-Stärke verwechselt wird — dieses Projekt benutzt ihn nicht.*

**Single-File-Konverter** — Eine Hilfsfunktion, die Gewichte aus **einer** grossen
`.safetensors`-Datei in die Form bringt, die eine Bibliothek erwartet. *Nötig, weil viele
Modelle in zwei Welten veröffentlicht werden: als aufgeteilter Ordner für `diffusers` und
als eine einzige Datei für die Oberflächen der Bastlerszene. Ein Konverter, der eine
neuere Fassung nicht kennt, scheitert erst beim Laden — vorher sieht die Datei
einwandfrei aus.*

**`.safetensors`-Kopf (Header)** — Die ersten Bytes einer Gewichtsdatei: ein JSON-Verzeichnis,
das jeden Tensor mit Namen, Datentyp und Grösse nennt, noch vor den eigentlichen Zahlen.
*Praktischer Nutzen: Man kann den Speicherbedarf eines Modells auf die Nachkommastelle
genau ausrechnen, ohne die Datei herunterzuladen — es genügen die ersten Kilobyte. So
wurden die 22,0 GiB des empfohlenen Backbones bestimmt: gerechnet aus gemessenen
Datentypen, nicht geschätzt.*


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

**Vertragsfeld** — Ein Feld, das im vereinbarten Schema einer Schnittstelle
**vorgesehen** ist — im Unterschied zu einem Zusatzfeld, das man mitschickt, weil es
nützlich ist, auf das sich aber niemand verlassen kann.
*Der Unterschied ist praktisch und nicht akademisch: Dieses Projekt kann sein Ergebnis in
zwei Fassungen abgeben, mit oder ohne Zusatzfelder (`nur_vertragsfelder`). Was in der
strengen Fassung ankommen soll, muss darum in einem Vertragsfeld stehen. Der längste
Stillstand eines Laufs wandert deshalb in `timings` und nicht in unsere `hinweise`: Wer in
der fremden Oberfläche wissen will, warum ein Auftrag eine halbe Stunde brauchte, findet
die Antwort dort, wo er ohnehin nachsieht.*

**Node (Knoten)** — Ein einzelner Arbeitsschritt in einer Verarbeitungskette, mit
Eingängen und Ausgängen.

**Graph** — Ein Netz aus Knoten und Verbindungen.

**DAG (Directed Acyclic Graph)** — Ein gerichteter Graph ohne Kreise: Die Verbindungen
haben eine Richtung, und kein Weg führt zum Ausgangspunkt zurück. Dadurch ist immer eine
gültige Reihenfolge bestimmbar. Die übliche Grundform von Bildketten.

**Bedarf (eines Knotens)** — Die Aufschreibung dessen, was ein Arbeitsschritt von seinen
Vorgängern **erwartet** und was er selbst **zusagt**. Ohne sie weiss eine Kette nicht, ob
sie richtig verdrahtet ist: Ein Knoten nimmt entgegen, was kommt, und merkt erst beim
Rechnen — oder gar nicht —, dass das Erwartete fehlt. *In diesem Projekt die Klasse
`Bedarf` (`src/aiimaging/graph.py`) mit drei Angaben: `braucht` nennt je Eingang die dort
erwarteten Feldnamen, `liefert` die Felder, die ein gelungener Lauf immer trägt, und
`dateien` diejenigen Felder, deren Wert ein Dateipfad ist. Der Bedarf hängt an der **Art**
des Schritts, nicht an seinem Namen — was ein Schritt braucht, folgt daraus, was er tut.
Welche Felder es überhaupt gibt, weiss nicht der Ablaufkern, sondern die Bildkette; die
ausgefüllte Tabelle steht darum in `src/aiimaging/kette.py` unter `BEDARF`.*

**Eingangsslot** — Ein nummerierter Steckplatz für einen Vorgänger. Die **Position** trägt
Bedeutung: Slot 0 ist etwas anderes als Slot 1, auch wenn beide dasselbe Feld liefern.
*Daran hängt in diesem Projekt ein Unterschied, der leicht verwechselt wird: Der
**äussere** Graph (KosmoOrbit) verdrahtet über **Feldnamen** — die Ausgaben aller
Vorgänger werden übereinandergelegt, und eine Kante entsteht, wo zwei Namen gleich sind.
Der **innere** Graph (`src/aiimaging/graph.py`) verdrahtet über die **Position** — jeder
Knoten bekommt die Ausgaben seiner Vorgänger als Liste in der Reihenfolge seiner Eingänge,
unvermischt. Warum das nötig ist, zeigt die Geometrie-QA: Slot 0 ist das Soll aus dem
Multipass, Slot 1 das Ist aus dem Render, und **beide** führen ein Feld `depth_png`.
Würden sie nach Feldnamen verschmolzen, wäre nicht mehr entscheidbar, welches gemeint ist
— verglichen würde am Ende etwas mit sich selbst.*

**Pflichtfeld** — Eine Angabe, die ein Ergebnis **immer** tragen muss, damit es als
gelungen gilt. Fehlt sie oder ist sie leer, ist das Ergebnis unbrauchbar, gleichgültig was
sein Statusfeld behauptet. *In diesem Projekt die Liste `liefert` eines `Bedarf`
(`src/aiimaging/graph.py`), entstanden aus einem gemessenen Fehler: In Sitzung 07 galt ein
Multipass-Ergebnis als „ok", obwohl seine normalisierte Tiefenkarte gar nicht da war. Es
wanderte in den Zwischenspeicher und wurde nie wieder gerechnet — auch nicht, nachdem die
Ursache behoben war. „Leer" ist dabei genau abgegrenzt: eine fehlende Angabe und eine
leere Liste zählen als leer, ein ausdrückliches „nein" (`False`) und die Zahl `0`
**nicht**. Ein durchgefallenes QA-Urteil ist ein Ergebnis und kein fehlendes Feld.*

**Entwurfszeit-Prüfung** — Etwas prüfen, **bevor** es läuft, allein an dem, was
aufgeschrieben ist. Das Gegenstück ist die **Laufzeit-Prüfung**, die erst beim Rechnen
zuschlägt — dann ist die teure Arbeit schon getan. Der Gewinn liegt nicht im Befund,
sondern in der Reihenfolge: Ein falsch verdrahteter Ablauf soll das sagen, bevor Blender
startet und die Grafikkarte eine Stunde rechnet, nicht danach. Was so prüfbar ist, ist
allerdings nur die Form; ob die Zahlen stimmen, zeigt weiterhin erst der Lauf.
*In diesem Projekt `pruefe_bedarf` (`src/aiimaging/graph.py`) und `pruefe_kette`
(`src/aiimaging/kette.py`): Sie melden fehlende Eingänge und tote Kanten, ohne einen
einzigen Schritt auszuführen — auch bei einem Graphen mit Kreis, damit der eine Fehler den
anderen nicht verdeckt. Das Vorbild ist KosmoOrbits `pipelineReadiness`, das für die
äussere Naht dasselbe leistet (`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`, Kap. 2/3).*

**Tote Kante** — Eine Verbindung zwischen zwei Arbeitsschritten, die aufgeschrieben ist,
aber nichts überträgt: Der Empfänger fragt nach einem Feld, das der Absender gar nicht
liefert. Der Ablauf sieht vollständig verdrahtet aus und läuft mit leeren Händen.
*Der Vorläufer KosmoOrbit verbindet über Namensgleichheit und sagt **nichts**, wenn keine
Verbindung zustande kommt — der Befund, mit dem dieses Projekt angefangen hat. Eine tote
Kante ist darum kein Sonderfall, sondern die häufigste stille Fehlerart einer
Knotenoberfläche: Sie erzeugt kein Problem, sondern ein plausibel aussehendes Ergebnis.*
*Wo sie in diesem Projekt gemeldet wird: im **inneren** Graphen als Befund
`fehlendes-feld` aus `pruefe_bedarf`/`pruefe_kette` (`graph.py`, `kette.py`), im
**äusseren** aus einem anderen Grund — dort genügen zwei ungleich geschriebene Feldnamen
(`mcp_schemas.py`). Beide melden vor dem Lauf.*
*Auch in eigener Sache aufgetreten: `Stil.seitenverhaeltnis` wurde am 18.08.2026
eingeführt, geschrieben und von niemandem gelesen; und ein `pfad`-Parameter der
Fortschrittswache wurde entgegengenommen und liegengelassen. Beide am Folgetag behoben —
**dass ein Wert in einem Feld steht, ist kein Beleg dafür, dass ihn jemand liest.***

**Skip-on-Error** — Wenn ein Knoten in einer Kette scheitert, werden alle von ihm
abhängigen Knoten übersprungen statt mit unvollständigen Eingaben gerechnet. Ein Ergebnis
aus halben Daten ist schlimmer als gar keines — es sieht gültig aus.

**Node-Tree (Knotenbaum)** — Eine Oberfläche, in der man Arbeitsschritte als Kästchen
hinlegt und mit Linien verbindet, statt sie hinzuschreiben. Blender, KosmoOrbit und die
Oberflächen der Bildmodelle arbeiten so.
*Ein Node-Tree ist nicht automatisch ein Ablaufplan. Der ältere KosmoVis-Baum sieht aus wie
einer, ist aber keiner: Beim Aufbau werden alle Verbindungen gelöscht, und die Knoten
reden über Szenen-Eigenschaften am Baum vorbei. Er ist eine **Werkzeugpalette mit
Reihenfolge** — brauchbar für Menschen, aber nichts, woraus sich ableiten liesse, was
wovon abhängt.*

**Socket (Sockel, Anschluss)** — Der einzelne Ein- oder Ausgang eines Knotens, an dem eine
Verbindung andocken kann. Sockeltypen legen fest, was zusammenpasst: Ein Bild-Ausgang
gehört nicht an einen Zahlen-Eingang.
*Sockeltypen sind die eigentliche Aussage einer Knotenoberfläche darüber, welche Datenarten
es überhaupt gibt. Der ältere Bestand kennt vier — Kameraeinstellung, Bild, Render-Ebene
und Variante —, und das ist die brauchbarste Erbschaft aus jenem Baum: nicht der Code,
sondern die Antwort auf die Frage, was zwischen den Stufen fliesst.*

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

**Erreichbarkeit einer Schwelle (Deckel)** — Die Frage, ob ein Messwert eine Schwelle
unter den gegebenen Umständen **überhaupt** erreichen kann — unabhängig davon, wie gut das
Geprüfte ist. Liegt die beste erreichbare Zahl unter der Schwelle, misst die Prüfung nicht
mehr den Gegenstand, sondern die Umstände.
*In diesem Projekt am 20.08.2026 nachgerechnet: Der Geometrie-Score ist
`sqrt(|spearman| × geom_iou)`, für 0.65 braucht es also ein `geom_iou` von 0,4225. Auf der
Testszene **ohne Boden** — der einzigen, auf der je gerendert wurde — deckelt `geom_iou`
bei 0,406. Die Schwelle war dort **arithmetisch unerreichbar**, und ein durchgefallenes
Bild belegte nichts über seine Geometrietreue.*
*Die Prüfung kostet nichts und gehört vor den Lauf:* `geometrie_qa.erreichbarkeit()`.

**Schluss aus einer Abwesenheit** — Aus dem Ausbleiben eines Zeichens auf eine Ursache
schliessen: „ich sehe es nicht, also gibt es das nicht", „nichts ist passiert, also tut
der Knopf nichts". Der Schluss trägt nur, wenn feststeht, dass das Zeichen **erschienen
wäre**, hätte es die Ursache gegeben.
*In diesem Projekt an einem einzigen Tag in fünf Verkleidungen aufgetreten: ein
geschlossenes Menü („gibt es nicht" — war nur zugeklappt), ein Begriff, der in einem
veralteten Klon fehlte („fremder Bestand"), ein Verzeichnis, das nirgends auffindbar war
(„andere App" — wurde gerade gebaut), ein grüner Wächter („hat geprüft" — sein Artefakt
trug `{"geprueft": 0}`) und ein wirkungsloser Klick („der Knopf tut nichts" — der Klick
traf einen anderen Knopf).*
*Merksatz:* **Bevor du aus einem Ausbleiben etwas schliesst, prüfe, ob die Ursache
überhaupt gewirkt haben konnte.**

**Vakuum-wahre Zusicherung** — Eine Zusicherung über **alle** Elemente einer Sammlung,
die auch dann hält, wenn die Sammlung **leer** ist: „alle Warnungen sind Zeichenketten"
stimmt, wenn es gar keine Warnung gibt; „keine Warnung enthält X" ebenso. Ein Test dieser
Bauart besteht auch dann, wenn der Mechanismus, der die Sammlung füllen soll, vollständig
kaputt ist.
*Der lateinische Ausdruck dafür lautet* vacuous truth *— wahr, weil es nichts gibt, was
sie widerlegen könnte.*

**Vakuumprobe** — Die Gegenprüfung dazu, in diesem Projekt `tools/vakuumprobe.py`: Auf
einer **Kopie** der Testsuite werden alle solchen Zusicherungen durch eine Fassung
ersetzt, die bei leerer Sammlung fehlschlägt. Was danach rot ist, war vorher grün **und
leer**. Verwandt mit der *Mutationsprobe*, aber billiger und enger: Sie sucht nicht nach
unbemerkten Fehlern überhaupt, sondern nach einer bestimmten, sehr häufigen Bauart.
*Erste Messung am 20.08.2026: 40 Stellen umgeschrieben, 6 Treffer, und für jeden Treffer
lag eine Gegenprobe in derselben Datei — kein einziger falsch-grüner Test.*

**Gegenprobe (zu einer Abwesenheits-Zusicherung)** — Der Test, der eine vakuum-wahre
Zusicherung erst tragfähig macht: Er zeigt am **selben** Mechanismus, dass sich die
Sammlung im umgekehrten Fall **füllt**. „Bei ausreichender Führung erscheint kein Hinweis"
sagt für sich nichts; zusammen mit „bei zu geringer Führung erscheint einer" sagt es alles.
*Merksatz aus dem Anlass:* **Ein bestandener Test ist kein Beleg dafür, dass er etwas
geprüft hat.*

**Cache** — Zwischenspeicher für teuer berechnete Ergebnisse, damit sie nicht doppelt
berechnet werden.

**Zusage (eines Cache-Eintrags)** — Die Liste der Dateien, die ein Eintrag im
Zwischenspeicher verspricht. Sie ist nötig, weil der Eintrag die Dateien nicht enthält,
sondern nur auf sie zeigt: Gespeichert wird der Bericht eines Arbeitsschritts — Pfade,
Masse, Kennzahlen —, während die schweren Bilddateien liegen bleiben, wo sie entstanden
sind. Sie hineinzukopieren hiesse, einen zweiten Ort der Wahrheit zu schaffen. Ein Pfad
allein ist aber nur eine Behauptung.
*In diesem Projekt nimmt `ArtefaktCache.lege_ab` die Zusage als eigenes Argument entgegen
und vermerkt sie im Eintrag; `hole` sieht bei jedem Zugriff nach, ob die Dateien noch da
sind, und meldet sonst einen Fehltreffer, worauf neu gerechnet wird
(`src/aiimaging/graph.py`). Der Anlass ist gemessen: Ein aufgeräumtes Temporärverzeichnis
genügt, und die Zusage geht ins Leere. Umgekehrt gilt weiter, was dieses Projekt mehrfach
bezahlt hat — dass eine Datei **daliegt**, ist kein Beleg für ihren **Inhalt**; den
liefert der Hash.*

**Selektive Verwerfung** — Einen **einzelnen** Eintrag aus dem Zwischenspeicher wegwerfen
statt aller. Das klingt selbstverständlich und fehlte lange: Wer nur „alles leeren" kann,
greift in der Praxis zum Löschen des ganzen Ausgabeordners — und wirft die teure
Geometriestufe mit weg, um einen Render zu wiederholen.
*In diesem Projekt `ArtefaktCache.verwirf` (`src/aiimaging/graph.py`); den nötigen
Schlüssel gibt jeder Lauf je Schritt selbst zurück, und `schluessel()` listet auf, was
überhaupt drinliegt. Verworfen wird **nicht** kaskadierend: Die nachfolgenden Schritte
hängen am Ergebnis und nicht am Eintrag — rechnet der verworfene Schritt dasselbe noch
einmal, bleiben sie gültig. Wer eine andere Rechnung will, ändert Parameter oder Eingabe,
und dann ändern sich deren Schlüssel ohnehin von selbst.*

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

**Validierung (Daten gegen Schema)** — Die Prüfung tatsächlicher Daten gegen ihr Schema.
Schlägt sie fehl,
stimmt die Wirklichkeit nicht mit dem Vertrag überein.
*Nicht zu verwechseln mit* **Validierung (eines Verfahrens)** *in Abschnitt 4 — dort die
Gegenprobe zur Kalibrierung; gleiches Wort, anderer Sachverhalt.*

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

**Leistungsgrenze (Power Limit)** — Obergrenze, wieviel elektrische Leistung eine
Grafikkarte aufnehmen darf, in Watt. Sie wird im Treiber gesetzt (`nvidia-smi -pl 400`),
nicht in der Software, die die Karte benutzt; die Karte drosselt sich dann selbst, statt
mehr zu ziehen. *Im Projekt:* Die RTX 5090 der HomeStation löst ohne Grenze unter
Volllast die Schutzschaltung des Netzteils aus — der ganze Rechner geht aus. Jeder
Auftrag führt darum die Auflage `leistungsgrenze_w: 400` mit, und `tools/homeworker.py`
prüft vor dem Start, ob sie gesetzt ist. Setzen kann das Skript sie nicht selbst, das
braucht Administratorrechte; es prüft und sagt, was zu tun wäre.

**Leerlauf-Torwächter** — Prüfung, ob ein Gerät gerade frei ist, bevor eine lange
Rechnung darauf gestartet wird. *Im Projekt:* `nur_bei_leerlauf: true` in jedem Auftrag —
gestartet wird nur unter 120 Watt Aufnahme und unter 8 GB belegtem Grafikspeicher. Lässt
sich der Zustand nicht feststellen, wird **abgelehnt** statt geraten (siehe
*Fail-closed*): Ein übersprungener Auftrag kostet Wartezeit, ein abgestürzter Rechner
mehr.

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
| 2026-08-23 | Ergaenzt aus den zwei Uebersetzungsregeln: **Kompositum (zusammengesetztes Wort)** und **Beugung (Flexion)**. Beide tragen den gemessenen Ertrag mit: An dreizehn Prompts war vorher **einer** vollstaendig uebersetzt, nachher **dreizehn** — und die Wahl der Endungen ist keine Kleinigkeit, `s` musste weichen (Dachs → roof), `n` musste bleiben (Fassaden) |
| 2026-08-23 | Ergaenzt aus dem Anschluss von `komposition.py` und der Seedauswahl: **Ungerufenes Modul (die tote Kante im Grossen)**, **Auswaehlen gegen den eigenen Rauschboden (Kreisschluss)**, **Bester Wurf gegen besserer Startwert**. Alle drei aus Befunden ueber dieses Repo selbst: `komposition.py` war ein halbes Jahr lang nur von den eigenen Tests gerufen, und die Seedauswahl behielt zu Recht das beste Bild — sagte aber nicht dazu, dass der Vorsprung im Rauschen liegt |
| 2026-08-22 | Ergaenzt aus der waagrechten Kamera (`kameras.MODUS_SHIFT`): **Unsymmetrischer Bildrahmen (durch Shift)** und **Sensorbezug (`sensor_fit`)**. Der erste traegt den Befund, den zwei Testanlaeufe gebraucht haben: Ob ein Shift Abstand kostet oder spart, haengt daran, WELCHE Rahmenkante bindet — beim Turm das Dach (spart), beim flachen Bau aus der Naehe der Fuss (kostet). **Berichtigt:** Vier Dokumente sagten „`kameras.py` kippt 9,46°". Nachgemessen ueber zwoelf Richtungen, vier Gebaeudehoehen und zwei Formate sind es **1,92°–4,70°**; die 9,46° gelten bei 1,2 × Gebaeudehoehe Abstand, und dort steht `kamerasatz` nie |
| 2026-08-22 | Ergaenzt aus der Prompt-Uebersetzung (`src/aiimaging/sprache.py`): **Trainingssprache (eines Bildmodells)**, **Glossar (Uebersetzungsglossar)**, **Signalwort (bei der Spracherkennung)**, **Dreiwertiges Urteil (ja / nein / nicht entscheidbar)**, **Uebermelden (einer Pruefung)**. Der erste Eintrag traegt die Messung, aus der die ganze Sache folgt: Ueber acht gepaarte Startwerte ergab „bedeckter Himmel" bei 8 von 8 einen deutlich blaueren Himmel als „overcast sky" — das Modell versteht das Wort nicht und fuellt die Luecke |
| 2026-08-22 | Ergaenzt aus dem Raumleser (`src/aiimaging/runners/ifc_raeume_runner.py`, `seams.ifc_raeume`): **Raum (`IfcSpace`)**, **Grundriss (als Polygon)**, **Umlaufsinn**, **Platzierungskette**, **Bezugspunkt (einer Höhenangabe)**, **lichte Höhe**. Die letzten beiden tragen den Grund, warum es diesen Auftrag ueberhaupt so gab: Eine Zahl ohne Bezugspunkt ist in diesem Projekt keine Zahl |
| 2026-08-21 | Ergaenzt aus den drei Kompositionsrecherchen (`docs/recherche/KOMPOSITION_AUSSEN.md`, `KOMPOSITION_INNEN.md`, `BILDPROPORTIONEN.md`): 34 Begriffe der Architekturfotografie — Aufnahmetechnik (**Sensor/Bildebene**, **Kleinbild**, **Seitenverhältnis**, **Fachkamera**, **Planfilm**, **Bildkreis**, **Shift**, **Shift-Stitch**, **Perspektivkorrektur**), Projektionsgeometrie (**stürzende Linien**, **Ein-/Zwei-/Dreipunktperspektive**, **Fluchtpunkt**, **Horizontlinie**, **Über-Eck-Ansicht**, **rektilineare Projektion**, **Volumenanamorphose**, **Objektivverzeichnung**, **Streckungsverhältnis**), Bildaufbau (**Bildebenen**, **Anschnitt**, **Negativraum/funktionaler Raum**, **axial/nicht-axial**, **Drittelregel**, **goldener Schnitt**), Licht (**Dämmerungsphasen**, **goldene/blaue Stunde**, **Blendenstufe/EV**, **Dynamikumfang**, **Belichtungsreihe**, **flambient**) und Ausgabe (**dpi**, **HABS**); dazu **Perzentil**. Zwei Eintraege tragen den Befund der Recherche und nicht die Lehrmeinung: Die **Drittelregel** ist als Beschreibung der Praxis widerlegt (Amirshahi et al. 2014, ρ = 0,17) und wurde 1955 mit dem goldenen Schnitt verwechselt; **stuerzende Linien** sind die einzige institutionell verbindliche Regel des Fachs — und unser eigener Code verletzt sie in jedem Bild (9,46° Neigung, rund 9–12 % Konvergenz; die urspruenglich genannten 11,8–21,8 % waren falsch gerechnet und noch in derselben Nacht korrigiert). **Getrennt:** **Rauschboden** bezeichnet zwei Sachverhalte — die Streuung einer Saatreihe und den Boden einer Metrik ueber einem Bild ohne Geometrie; beide Titel tragen jetzt einen Klammerzusatz, die Trennung steht in `tests/test_lexikon.py` |
| 2026-08-21 | Ergaenzt aus der Bauwerksmaske (`src/aiimaging/maske.py`): **Bauwerksmaske** und **Geländeregel**. Beide aus der Messung vom 21.08.2026: Der Material-ID-Pass liefert dieselbe Maske wie eine zweite Blender-Aufnahme (100.000 % Uebereinstimmung), aber nur, solange eine Regel sagt, woran das Gelaende zu erkennen ist |
| 2026-08-20 | Ergaenzt: **Erreichbarkeit einer Schwelle (Deckel)**. Nachgerechnet: Auf der Szene ohne Boden — der einzigen, auf der je gerendert wurde — war die Geometrie-Schwelle 0.65 arithmetisch unerreichbar |
| 2026-08-20 | Ergaenzt: **Schluss aus einer Abwesenheit**. Der Begriff fasst einen Fehler zusammen, der an diesem Tag in FUENF Verkleidungen auftrat — geschlossenes Menue, veralteter Klon, ein Verzeichnis das gerade entsteht, ein gruener Waechter der nichts mass, und ein Klick der einen anderen Knopf traf |
| 2026-08-20 | Ergaenzt aus den Variantenreihen (`src/aiimaging/varianten.py`): **Saatreihe**, **kontrollierte Reihe**, **Rauschboden**, **Laplace-Varianz** (mit der Warnung, dass ein Schaerfemass keine Qualitaet ist). **Berichtigt:** **Seed** stand ZWEIMAL im Lexikon, in Abschnitt 6 als Kurzfassung und als ausfuehrliche Fassung — zusammengefuehrt zu einem Eintrag. Ein Lexikon, das denselben Begriff zweimal erklaert, veraltet an einer der beiden Stellen |
| 2026-08-20 | Ergaenzt aus dem Schrittzaehler im Renderlauf: **Rueckruf (Callback)** und **Diffusionsschritt** — letzterer mit der Einschraenkung, dass im Bildbearbeitungsmodus nur `schritte x denoise` Schritte laufen |
| 2026-08-20 | Ergaenzt aus der Herzschlagmessung: **GIL (Global Interpreter Lock)** und **Lebenszeichen gegen Fortschrittszeichen**. Beide sind gemessen: Cycles gibt die GIL frei (61 Faden-Schlaege gegen null Aufrufe der beiden dokumentierten Blender-Haken), und der Herzschlag belegt Leben, nicht Fortschritt |
| 2026-08-20 | Ergaenzt aus der Vakuumprobe (`tools/vakuumprobe.py`): **vakuum-wahre Zusicherung**, **Vakuumprobe**, **Gegenprobe zu einer Abwesenheits-Zusicherung**. Anlass war ein Befund der HomeStation ueber sich selbst — ein als gruen gemeldeter Waechter, dessen Fundartefakt `{"geprueft": 0}` trug |
| 2026-08-20 | Aus dem GPU-Ergebnis zu `auf-20260820-18`: **Sandbox-Paket (Snap, Flatpak)** und **Artefakt einer Messung**. Beide sind teuer erworben — das GPU-faehige Blender-Snap liefert bei Dateiumleitung Rueckgabewert 0 ohne Bild, und der am selben Tag gemessene 32-Sekunden-Takt war ein Artefakt der CPU-Messung |
| 2026-08-20 | Ergaenzt aus dem Abholer (`src/aiimaging/abholer.py`): **Laufzettel**, **Waise (verwaister Auftrag)** |
| 2026-08-20 | Ergaenzt aus der Taktmessung an Blender: **adaptives Sampling**, **Blockpufferung der Standardausgabe**, **Pipe-Blockade**. **Sample** um die gemessene Einschraenkung ergaenzt: Bei adaptivem Sampling ist die Samplezahl eine OBERGRENZE und keine Angabe der Rechenzeit — 6000 Samples in 12 s gegen 3000 ohne adaptives Sampling in ueber drei Minuten |
| 2026-08-22 | Ergaenzt aus dem zweiten Bein des Paartests: **Umrisstreue (Anteil der Grenze mit Kante)** und **Zufallsniveau (eines Anteilsmasses)**. Das zweite ist der erste Fall in diesem Projekt, in dem der Nullwert aus der Konstruktion folgt statt gemessen werden zu muessen — mit der Einschraenkung, die beim Bauen auffiel |
| 2026-08-22 | Ergaenzt aus dem Innenraum-Standpunkt: **Einspringende Ecke (Innenecke)** — der Grund, warum Raeume nicht mit Mittelpunktsmathematik zu behandeln sind |
| 2026-08-22 | Ergaenzt aus dem Umbau der Geometrie-QA: **Tiefenkante (an der Maskengrenze)** und **Paarurteil**. Beide tragen den Grund mit, aus dem sie entstanden sind — ein einzelner Score kann Existenz und Richtigkeit nicht zugleich beantworten |
| 2026-08-21 | Ergaenzt aus dem Nicht-Monotonie-Befund: **Monotonie (einer Metrik)**, **Faltung der Skala (durch den Betrag)**, ausgebaut **Polaritaet (einer Tiefenkarte)** um die Frage, wann man sie bestimmen DARF, ohne im Kreis zu messen. Alle drei aus einer Messung, die eine eigene Entscheidung widerlegt hat |
| 2026-08-21 | Ergaenzt beim Anhaengen der Wache an den Abholer: **Blockierender Aufruf**, **Hintergrundfaden und Daemon-Faden**, **Fortschrittsbeobachter**, **Vertragsfeld**. Ausgebaut: **Race Condition** um den Fall, in dem der TEST das Rennen enthaelt — und um die Abhilfe, das Rennen bedeutungslos zu machen statt laenger zu warten |
| 2026-08-20 | Ergaenzt aus der Fortschrittswache (`src/aiimaging/fortschritt.py`): **Timeout**, **Gesamt-Timeout gegen Fortschrittsfrist**, **Stillstand (Stall)**, **behauptetes gegen belegtes Fortschrittszeichen**, **monotone Uhr**. Anlass war wieder ein Befund: Der geerbte Stillstandswaechter stellt bei den Zustaenden `running` und `queued` die Uhr zurueck — also genau in dem Fall, fuer den er gebaut wurde |
| 2026-08-20 | Ergaenzt aus der Belichtungspruefung (`src/aiimaging/belichtung.py`) und dem farbfaehigen PNG-Leser: **Farbtyp (PNG)**, **Palette (PNG-Farbtyp 3)**, **Alphakanal**, **Luminanz**, **Rec.709**, **Gammakorrektur/sRGB**, **Clipping (ausgefressen/zugelaufen)**, **Belichtungsrahmen**. Der Anlass war ein Befund und keine Fleissarbeit: Die geerbte Schwelle von 8 % geclippter Lichter haette unseren eigenen, gemessenen Hausstil (7,55 % ± 6,9, Hoechstwert 30,0 %) zum Fehler erklaert — eine Belichtungsschwelle ist keine Eigenschaft guter Belichtung, sondern eines Stils |
| 2026-08-19 | Aus dem Uebergabeblatt an die Vis-Oberflaeche (`docs/UEBERGABE_VIS_2026-08-19.md`): **nullbares Feld (nullable)** — der Begriff wurde dort gebraucht, um zu erklaeren, warum `job_id` leer sein darf, stand aber nirgends. Alle uebrigen Fachbegriffe jenes Blatts (tote Kante, Bildwinkel, Backbone, SigLIP, Spearman, Freigabe-Token, Bounding Box, Subprozess, MCP) waren bereits erfasst und wurden geprueft, nicht angenommen |
| 2026-08-18 | Ergaenzt aus der Prompt-Bibliothek: **Prompt**, **Negativ-Prompt**, **Prompt-Baustein**, **Renderstil**, **Halluzination (bei Bildmodellen)**. Alle fuenf vor dem Schreiben dieser Zeile im Text nachgezaehlt |
| 2026-08-18 | Ergaenzt aus der Kameraanbindung und auf-12: **Fuellgrad** (abgegrenzt zum Deckungsgrad), **zusammenhaengende Flaeche** samt Vierer-/Achter-Nachbarschaft, **Randberuehrung**. Vor dem Schreiben dieser Zeile nachgezaehlt — die Gegenmassnahme aus der Zeile darunter |
| 2026-08-18 | Ergaenzt aus den drei HomeStation-Ergebnissen (auf-10, auf-11, MCP-Registrierung): **Boden (einer Aehnlichkeitsmetrik)**, **abgeleitete Schwelle**, **Ausleseort (pooler_output / last_hidden_state)**, **Ausgabeschema-Verletzung**. **Berichtigt:** **Stil-Score** und **Schwelle** trugen 0.30 als Massstab — gemessen ist die Zahl kleiner als der Boden von SigLIP 2 und laesst jedes beliebige Bildpaar durch; die Schwelle ist jetzt abgeleitet (0.666). **Praezisiert:** Der Eintrag zum Muster "innen stimmig, aussen daneben" nannte nur die erfundene Kubatur als Ursache — die zweite (Silhouettenauswahl aus einer hineingelegten Bodenebene) ist nachgetragen |
| 2026-08-18 | **Schuld aus drei Straengen beglichen (Sitzung 07, Fortsetzung).** *Kameraableitung* (`src/aiimaging/kameras.py`, aus dem alten Add-on-Bestand nachgebaut): Brennweite, Bildwinkel, Azimut, Deckungsgrad, Frustum, perspektivische Division, Raycast, orthografische Projektion/Ortho-Scale, Axonometrie, Depsgraph; **Bounding Box** zu *Bounding Box (Huellbox)* erweitert und um die Acht-Ecken-Pruefung ergaenzt. *Echte IFC-Dateien:* IFC4/IFC2X3, Pflichtattribut, OwnerHistory, Schema-Validierung, `preprocessor_version`/`originating_system`. *ControlNet-Suche:* ControlNet-Staerke, ControlNet-Union, Blockwise-ControlNet, destilliertes Modell, Fuehrung/`guidance_scale`, `control_context_scale`, Single-File-Konverter, `.safetensors`-Kopf. *Pruefen:* Rundlauf, xfail. *Knotenoberflaeche:* Node-Tree, Socket, Multipass. **Nachgetragen, was ein frueheres Aenderungsverzeichnis behauptet hat:** die Zeile vom selben Tag versprach *tote Kante* im Graph-Kern — der Begriff stand nur in der Prosa eines anderen Eintrags, nie als eigener. Zum zweiten Mal in dieser Sitzung derselbe Befund: Ein Verzeichnis, das Eintraege behauptet, die es nicht gibt, macht die Luecke unauffindbar |
| 2026-08-14 | Erstfassung: 9 Themengruppen, ~200 Begriffe |
| 2026-08-14 | Ergaenzt: IPC, stdout/stderr, Exit-Code, Protokoll, Subprozess praezisiert |
| 2026-08-18 | **Connector-Schicht, Binaerpruefung und Lizenzvokabular nachgetragen** (wieder erreichten mehrere Laeufe `docs/` nicht). *Connector-Schicht* (`src/aiimaging/herkunft.py`): SI-Vorsatz, Umrechnungseinheit, Lesefenster, glb-Block, `FILE_NAME` samt Feldreihenfolge, belegt/vermutet/unbekannt; **STEP** um das Lesen des Dateikopfs ergaenzt. *Binaer-Lizenzpruefung:* gebuendeltes Binary, Ausnahmeklausel/GCC Runtime Library Exception, proprietaer, EULA, Platzhalterpaket, Metapaket, transitive Abhaengigkeit, `dist-info`, Symbol/Symbolverweis, Versionen festschreiben, Range-Abruf; **Dual License** um die Lizenzwahl zwischen zwei offenen Lizenzen (FreeType) erweitert, **Wheel**, **PyPI** und **LGPL** ergaenzt. *Lizenzvokabular* (`src/aiimaging/lizenzquelle.py`): **Regel-1-Spannung** neu, **permissive Lizenz** um „permissiv ist nicht kommerziell erlaubt", **vakuoeser Test** um die zweite Bauart — ein Test fand das gesuchte Wort im falschen Eintrag. **Berichtigt:** **Optionale Abhaengigkeitsgruppe** behauptete, „alles Schwere" liege jenseits der Prozessgrenze; torch, diffusers, transformers und Pillow werden im Produkt-Environment importiert — die Grenze trennt nach Lizenz, nicht nach Gewicht. **Runner** nannte zwei Dateien als Beispiele, die es in diesem Repo nicht gibt: Sie gehoeren zu KosmoDraw |
| 2026-08-18 | **Aufgelaufene Schuld aus drei Straengen nachgetragen** (drei fruehere Laeufe kamen nicht an `docs/` heran). *Graph-Kern:* Bedarf, Eingangsslot, Pflichtfeld, tote Kante, Entwurfszeit-Pruefung, Zusage eines Cache-Eintrags, selektive Verwerfung. *Lizenzpruefung:* CreativeML OpenRAIL-M (abgegrenzt zu OpenRAIL++-M), CDDL, Contributor License Agreement, Primaerquelle/Sekundaerquelle, Modellkarte, Front-Matter, Markdown, HTTP-Statuscode; **Gated Model** zu *Gated Model / Gated Repository* erweitert. *Schwellenstudie-Abnahme:* Charakterisierungstest, Entdopplung/Dublette, **Rasterung der Staerkeachse** um den Kurznamen *Staerkeraster* ergaenzt. **Berichtigt:** **Trefferquote** nannte 36 Faelle, 24 untreue und 0,667 — Zahlen aus der Auswertung *vor* der Entdopplung; richtig sind 32 ausgewertete, 20 untreue und 0,625 |
| 2026-08-18 | Ergaenzt aus der Schwellenstudie: Metrik, Schwelle, Kalibrierung, Validierung (eines Verfahrens), Setzung vs. Messung, Stoerung/kontrollierte Verfaelschung, Nullprobe, Kontrolle (im Experiment), Widerlegbarkeit, Trennschaerfe, falsch frei/falsch gesperrt, Trefferquote, Rasterung der Staerkeachse, streng monoton, Invarianz, inkommensurabel, normalverteiltes Rauschen/Standardabweichung, Mittelwertfilter. **Validierung** in zwei Bedeutungen getrennt (Verfahren / Daten gegen Schema). Praezisiert: **Silhouette** und **geometrisches Mittel** fangen eine *ersetzende* Halluzination zuverlaessig, eine *ergaenzende* nur schwach (Zusatzkoerper 0,698) |
| 2026-08-18 | Ergaenzt aus dem eigenen PNG-Schreiber: PNG-Block, Paeth-Praediktor, MSAD-Heuristik, Praediktor (Vorhersage), verlustfrei/verlustbehaftet, Ebene/Multilayer-EXR, float32/float64, LSB, Standardbibliothek, Heuristik, Traceback, Referenzimplementierung, Rueckwaertskompatibilitaet/stiller Bruch, fail-open/Befund als Feld. Ausgebaut: Zeilenfilter (alle fuenf Filter benannt, von Abschnitt 6 nach Abschnitt 5 verschoben), Endianness (Big-/Little-Endian), CRC32, Quantisierungsschritt/-stufe, zlib. **Quantisierung** in zwei Bedeutungen getrennt (Messwerte / Modellgewichte) |
| 2026-08-18 | Ergaenzt aus der Kettenverdrahtung: Fabrikfunktion, Closure |
| 2026-08-18 | Ergaenzt aus der Ist-Seite: Polaritaet, Hintergrundmarke |
| 2026-08-18 | Ergaenzt aus der Tiefenschaetzer-Pruefung: monokulare Tiefenschaetzung, CC-BY-NC |
| 2026-08-18 | Ergaenzt aus dem EXR-Leser: OpenEXR/Scanline, Half-Float, Praediktor/Byte-Entflechtung, zlib, Endianness, CRC, Quantisierungsschritt |
| 2026-08-18 | Ergaenzt aus Renderstufe und Bildlesen: diffusers, txt2img/img2img/image-edit, Seed, Zeilenfilter |
| 2026-08-18 | Ergaenzt aus der Einbetter-Pruefung: Gated Model praezisiert, selbstueberwachtes Lernen |
| 2026-08-18 | Ergaenzt aus dem Multipass-Ausbau: Beauty-Pass, Emissions-Shader, View-Transform, Dithering, Denoiser, Bittiefe |
| 2026-08-18 | Ergaenzt aus Backbone/Stil-QA: Registry, Dataclass/frozen, Depth-ControlNet-Naht, Multi-Reference-Editing, Referenzset, Stil-Score, Attrappe, vakuoeser Test, OpenRAIL++-M, Stability Community License. **Aggregation** in zwei Bedeutungen getrennt (Lizenzrecht / Messwerte) |
| 2026-08-18 | Ergaenzt aus dem Multipass: Goldener Winkel, Normalisierung |
| 2026-08-18 | Ergaenzt aus der Geometrie-QA: Rangkorrelation, Bindung, Silhouette, IoU, geometrisches Mittel, Disparitaet |
| 2026-08-18 | **Schuld beglichen (Sitzung 07):** Die Zeile unten versprach *Leistungsgrenze* und *Rauchprobe* — beide standen nie im Text. Jetzt nachgetragen, dazu Leerlauf-Torwaechter. Ein Aenderungsverzeichnis, das Eintraege behauptet, die es nicht gibt, ist schlimmer als keines: Es laesst die Luecke unauffindbar |
| 2026-08-18 | Ergaenzt aus Phase 3: Leistungsgrenze, Rauchprobe, fail-closed praezisiert |
| 2026-08-18 | Ergaenzt aus Phase 2: Skip-on-Error, Freigabe-Token, Pfad-Trickserei, Positivliste, fsync, atomares Schreiben, Zustandsautomat, Endzustand, Content-Hashing, Mutationsprobe |
| 2026-08-18 | Ergaenzt aus der Paketierung: pyproject.toml, src-Layout, optionale Abhaengigkeitsgruppe, SPDX |
| 2026-08-18 | Ergaenzt aus Phase 1: STEP/ISO-10303-21, Extrusion/SweptSolid, GUID, Determinismus, Testfixture, Orchestrator |
| 2026-08-14 | Ergaenzt aus Phase 0: stdio, Pfad-Sandbox, write-gated, Runner |
| 2026-08-14 | Ergaenzt aus der KosmoOrbit-Einbindung: Tauri, TypeScript, React, REST/Endpoint, SSE, Sidecar, topologische Sortierung, JSON-Schema, Validierung, inputSchema/outputSchema, structuredContent, Cockpit-Prinzip, Read-only-Gate, Lane |
| 2026-08-14 | Ausgebaut: Apache-2.0 (Auflagen, Patent- und Verteidigungsklausel), MCP (Abgrenzung zum Subprozessaufruf) |
