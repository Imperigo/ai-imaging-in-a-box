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

**Fremdprogramm (vom Nutzer installiert)** — Ein Programm mit eigener, nicht-offener Lizenz, das Visbox
nicht mitliefert, aber aufrufen darf, wenn der Nutzer es selbst installiert und lizenziert hat — nur auf seinem
Rechner, nie als Dienst für andere, und nie als Voraussetzung.
*Im Projekt:* Präzisierung in `CLAUDE.md` (Entscheid 79), heute Epic RealityScan.

**Git** — Das Programm, das jede Änderung an den Projektdateien aufzeichnet. Es
speichert nicht nur den aktuellen Stand, sondern die vollständige Geschichte. Jeder
frühere Zustand ist wiederherstellbar.

**Relightable Gaussian Splatting (lichtaktiver Splat)** — Ein Splat, der auf neues Licht reagiert. Ein
gewöhnlicher Splat speichert das Licht der Aufnahme fest; damit er neu beleuchtet werden kann, muss er in
Materialeigenschaften zerlegt werden (Grundfarbe, Rauheit, Ausrichtung). Heute Forschung.
*Im Projekt:* Forschungsfrage des Owners zu Entscheid 79, nicht gebaut (`docs/SPLAT_WEGE_2026-10-13.md`).

**Repository (kurz: Repo)** — Der Projektordner samt seiner gesamten Geschichte. Ein
Repo liegt lokal auf dem Rechner und meist zusätzlich auf einem Server (siehe *GitHub*).

**GitHub** — Ein Dienst, der Git-Repositories im Internet hostet. Zusätzlich zur reinen
Ablage bietet er Oberflächen für Diskussion, Überprüfung und Zusammenarbeit.

**Commit** — Ein festgeschriebener Zwischenstand, vergleichbar mit einem datierten
Planstand. Ein Commit umfasst die geänderten Dateien, Zeitpunkt, Urheber:in und eine
Nachricht, die erklärt *warum* geändert wurde. Er ist unveränderlich und wird durch eine
Prüfsumme identifiziert (z. B. `ae2cfa7`).

**Codestand (eines Dokuments)** — Der Commit, gegen den eine veröffentlichte Zahl
gemessen wurde, als Zeile im Dokument: `**Codestand:** \`b118fdb\``. *Ohne ihn ist eine
Messung nicht falsch, aber auch nicht nachfahrbar: Wer sie wiederholt und etwas anderes
herausbekommt, weiss nicht, ob er einen Fehler gemacht hat oder eine andere Software
fährt. Anlass war der 01.09.2026 — eine einzige Änderung entwertete sieben Dokumente, und
acht Tage lang fiel es niemandem auf.*

**Grundlage (eines Dokuments)** — Die Liste der Programmteile, auf denen die Zahlen eines
Dokuments stehen: `**Grundlage:** \`kameras\`, \`maske\``. *Sie beantwortet die
Gegenfrage zum Codestand — nicht «fahre ich dieselbe Software?», sondern «geht mich diese
Änderung überhaupt etwas an?». `**Grundlage:** keine` ist eine vollständige Angabe: Ein
Text, der fremde Arbeiten liest, misst nichts an unserem Code.*

**Berührung (einer Messung)** — Der Befund, dass sich seit dem Codestand eines Dokuments
etwas an seiner Grundlage geändert hat. **«Berührt» heisst ansehen, nicht falsch.**
*Gezählt wird je Programmteil, und der ist gröber als eine Zahl: Der erste gemeldete Fall
betraf eine geänderte Wartezeit, die nicht ändert, was gerechnet wird. Ein Werkzeug, das
nur meldet, was sicher falsch ist, meldet fast nie etwas — und dann heisst sein Schweigen
nichts mehr.*

**Herkunftstabelle** — Eine Liste, die zu jedem Programm, das eine 3D-Datei erzeugen
kann, festhält, **wie herum** dessen Dateien stehen — welche Achse nach oben zeigt. *Sie
ist kein Nachschlagewerk, sondern eine Anweisung: Ein Leser dreht die Datei danach. Steht
dort eine Vermutung, dreht er falsch, und niemand sieht es der Zeile an.*

**Belegt, gemessen, vermutet, unbekannt** — Die vier Stufen, mit denen dieses Projekt die
Sicherheit einer solchen Angabe kennzeichnet. *«Belegt» heisst: folgt aus der Norm des
Dateiformats. «Gemessen» heisst: an echten Dateien nachgeprüft — seit dem 11.09.2026, als
die Höhenachse von KosmoOrbit an zwei Dateien exakt bestätigt wurde. Die ersten beiden
werden ohne Rückfrage benutzt, die anderen nie. Eine Sicherheit gehört an ihre Quelle.*

**Warum eine Antwort fehlt — die vier Lagen** — Ein unbeantworteter Auftrag kann aus
vier verschiedenen Gründen unbeantwortet sein, und sie verlangen Verschiedenes: *Er ist nie
hinausgegangen* (unser Fehler), *er ist zu frisch* (noch keine Aussage), *der Empfänger hat
danach anderes beantwortet* (er war da — hier ist Nachfragen angebracht), oder *vom
Empfänger kam seither gar nichts* (**wir wissen es nicht** — hier wäre Mahnen falsch, denn
wer nichts schickt, hat die Mahnung vielleicht ebenso wenig gesehen wie den Auftrag).
*Erst messen, dann mahnen.*

**Örtliche Ergänzung (Drop-in)** — Eine kleine Zusatzdatei neben einer
Dienstbeschreibung, die einzelne Einstellungen überschreibt, ohne die Hauptdatei
anzufassen. *Das Betriebssystem liest beide. Unser Wächter las lange nur die Hauptdatei —
und meldete darum «alles gleich», während der Dienst mit einer anderen Einstellung lief.*

**Zweite Differenz (Krümmung)** — Nicht «wie stark ändert sich der Wert von Punkt zu
Punkt», sondern «ändert sich die Änderung». *Der Unterschied entscheidet hier alles: Eine
gleichmässig ansteigende Tiefenkarte — eine leere Wand — hat eine ständige, aber immer
gleiche Änderung; die zweite Differenz ist null. Eine Kante hat sie nicht. Deshalb erkennt
sie eine strukturlose Vorlage, während die erste Differenz beide Fälle gleich bewertet.*

**Ersatzschreibung der Umlaute** — «ae», «oe», «ue» statt ä, ö, ü — was jeder tippt, der
keine deutsche Tastatur hat. *Unser Wörterbuch war auf echte Umlaute geschlüsselt, und
darum blieb «betonwaende» unübersetzt, während «betonwände» zu «concrete walls» wurde.*

**Stilles Abstreifen (unbekannter Felder)** — Wenn eine Schnittstelle ein Feld, das sie
nicht kennt, einfach wegwirft, statt sich zu beschweren. *Klingt harmlos und ist es nicht:
Wer ein Feld setzt und kein Wort hört, hält es für bedient. Bei uns hätte ein
`qualitaet: "FINAL"` so einen Renderlauf von zwölf Minuten gekostet, an dessen Ende ein
Bild steht, das niemand bestellt hat. Seit dem 11.09.2026 hält ein unbekanntes Feld den
Lauf auf.*

**Rückstand gegen Einbau-Stand** — Zwei Zählungen, die verschiedene Dinge zählen: Der
*Rückstand* zählt Aufträge, auf die noch keine Antwort da ist. Der *Einbau-Stand* zählt
Posten, die noch nicht in der fremden Software stehen. *Zwischen beiden liegt ein Zustand,
den lange niemand zählte: Der Posten steht offen, und die Antwort, auf die er wartet, liegt
längst da. Am 09.09.2026 traf das auf 21 von 23 offenen Posten zu.*

**Nachgesehen bis** — Der Vermerk, bis zu welchem Commit jemand ein gemeldetes Dokument
durchgesehen hat. *Ohne ihn ruft die Meldung ewig weiter, auch nach der Klärung — und ein
Wächter, der nach der Klärung weiterruft, wird abgestellt.*

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

**Nachziehen per Merge (statt Neuaufsetzen)** — Einen eigenen Zweig auf einen neueren Hauptstand bringen, indem
man den Hauptstand *hineinführt*: Die bisherige Geschichte bleibt, wie sie war, und ein zusätzlicher Schritt hält fest,
dass der neue Stand dazugekommen ist. Das Gegenstück, das «Neuaufsetzen» (Rebase), schreibt die Geschichte um und
verlangt danach ein **Überschreiben mit Gewalt (Force-Push)** — dabei ersetzt man den Zweig auf dem Server, und wer
schon den alten Stand hatte, verliert den gemeinsamen Boden.
*Im Projekt:* Runde 29 wurde am 14.10.2026 so in «claude/kosmovis-startgraph» und «claude/kosmovis-kamera-aus-3d»
geholt (Protokoll 74 §122) — auf fremden und eigenen Zweigen wird nicht mit Gewalt überschrieben.

**Hilfszweig** — Ein Zweig, der nur als Zwischenstand dient und nie eingespielt werden soll. Er bündelt mehrere
Zweige, damit man eine Kopie von genau einem Stand nehmen oder prüfen kann, ob die Zweige ohne Zusammenstoss
zusammengehen.
*Im Projekt:* «claude/kosmovis-visbox-stand» (Runde 29 + startgraph + kamera-aus-3d) ist die Herkunft der
Visbox-Kopie unter `kosmovis/`; im Blatt an den Integrator steht ausdrücklich, dass er nicht eingespielt wird.

**Abgleich (der Kopie mit dem Original)** — Der Vergleich jeder wörtlich kopierten Datei mit dem **aktuellen** Stand
des Originals, nicht mit dem Fingerabdruck, den man beim Kopieren festgehalten hat. Die gewöhnliche Prüfung sagt nur, ob
die Kopie seit dem Kopieren still verändert wurde; ob das Original inzwischen weitergegangen ist, sieht sie nie. Der
Abgleich liest den Stand direkt aus der Versionsgeschichte (ohne die Dateien auszupacken) und sagt je Datei: gleich,
abweichend, dort weggefallen, hier noch nicht übernommen — oder auf einem eigenen Zweig geändert, der noch nicht
eingespielt ist (das ist kein Fehler, sondern ein angemeldeter Weg). *Im Projekt:* `tools/kosmovis_uebernahme.py
--abgleich`; `tools/knoten_bau.py` baut die Knotenansicht nicht, wenn der Abgleich eine Abweichung findet, ausser man
sagt ausdrücklich «gegen den festen Stand» (`--fester-stand`), und dann steht das im Stempel des Baus.

**Veraltete Spur (eines Zweigs)** — Die Kopie, die ein örtliches Repository von einem Zweig auf dem Server hält, ist nur
so frisch wie das letzte Abholen. Holt ein Klon nur einen Zweig (so ist er eingerichtet), bleiben die Spuren aller
anderen auf ihrem alten Stand stehen, und ein Vergleich gegen sie sieht aus wie einer gegen den echten Stand. *Im
Projekt:* `--abgleich --holen` holt den Integrator-Zweig und die eigenen Zweige vorher ausdrücklich ab (am 21.10.2026
stand die Spur des Hilfszweigs noch vor S3/S4, die des Kopf-Zweigs vor seinen neuen Nahtstellen, Protokoll 74 §163).

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

**Tag (Markierung im Verlauf)** — Ein fester Name für einen bestimmten Commit, etwa `v0.2.1`. Anders als ein Zweig
wandert ein Tag nicht mit, wenn weitergearbeitet wird: Er zeigt für immer auf denselben Stand. *Im Projekt:* Die
Prüfstrecke erkennt eine neue Nummer daran, dass es für sie noch keinen Tag gibt (Entscheid 84b).

**Freigabe auf GitHub (Release)** — Eine Seite auf GitHub, die zu einem Tag gehört: ein Begleittext und Dateien zum
Herunterladen. Anders als die Ablage eines Laufs der Prüfstrecke (nach 14 Tagen weg) bleibt sie, und sie hat eine
feste Adresse, die ein Programm ohne Anmeldung fragen kann («die neueste Freigabe»). *Im Projekt:* seit Visbox 0.2.1
(Entscheid 84) legt die Prüfstrecke bei neuer Nummer eine an — mit Mac-App, iPad-Paket, Fassungsblatt und
Prüfsummen —, und beide Apps fragen beim Start und einmal täglich danach.

**Prüfsummen-Datei (`SHA256SUMS.txt`)** — Eine kleine Textdatei, die zu jeder Datei einer Freigabe ihren Fingerabdruck
(siehe *SHA-256*) nennt, eine Zeile je Datei. Wer eine Datei lädt, rechnet ihren Fingerabdruck nach und vergleicht:
Stimmt er nicht, ist die Datei beschädigt oder ausgetauscht. *Im Projekt:* Die Mac-App ersetzt sich nur, wenn die
geladene Datei zu ihrer Zeile passt — und, wenn GitHub selbst einen Fingerabdruck nennt, auch zu diesem. Was sie
**nicht** beweist: wer die Freigabe gemacht hat.

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

**Photogrammetrie** — Aus vielen Fotos eines Gegenstands oder Ortes ein 3D-Modell rechnen: Das Programm
findet dieselben Punkte auf mehreren Bildern und schliesst daraus, wo sie im Raum liegen; heraus kommt ein Netz mit
aufgemalter Fotofarbe (Textur). Im Projekt der bessere Weg zur Umgebung als ein Splat, wenn die Fotos da sind.
*Im Projekt:* Epic RealityScan als vom Nutzer installiertes Fremdprogramm (Entscheid 79,
`docs/SPLAT_WEGE_2026-10-13.md`).

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


**CC0 (Gemeinfreiheitserklärung)** — Eine Erklärung, mit der jemand auf alle Rechte an einem Werk
verzichtet, soweit das Gesetz es erlaubt: Jede und jeder darf es ohne Bedingung und ohne Nennung
benutzen. *Im Projekt:* die Lizenz der Logo-Sammlung Simple Icons auf den Tafelkarten
(`docs/WERKZEUGE_UND_ARCHITEKTUR.md`).

**Simple Icons** — Eine frei verfügbare Sammlung einfarbiger Logos bekannter Programme und Firmen,
je als kleine Vektorgrafik, unter CC0. *Im Projekt:* Quelle der Logos auf den Tafelkarten
und Abbildungen zu den Werkzeugen (`docs/abbildungen/`, Fassung 13.21.0); wo die Sammlung kein Logo hat, steht eine Monogramm-Kachel.

**Markenzeichen (auf einer Logo-Karte)** — Das Logo eines Programms gehört als Marke seinem Inhaber,
auch wenn die Grafikdatei frei weitergegeben werden darf. Eine Karte, die solche Logos zeigt, sagt
das darum dazu und gibt keine eigene Zeichnung als Logo aus. *Im Projekt:* Fusszeile «trademarks
belong to their owners» auf jeder Werkzeugkarte.

---

## 3 · Programmieren, allgemein

**Eigenes Adressschema** — Der Anfang einer Adresse sagt, wer sie beantwortet: `https://` geht ins Netz, `file://`
auf die Festplatte. Ein Programm darf sich einen eigenen Anfang ausdenken — Visbox nimmt `visbox://`. Das eingebaute
Webfenster fragt dann nicht das Netz, sondern das Programm selbst, und das Programm entscheidet je Adresse: diese Datei
liegt in mir, jene Frage reiche ich an den Heim-PC weiter. So läuft eine Webseite ganz im Programm, ohne dass ein
Rechner sie ausliefern muss.
*Im Projekt:* Die Mac-App zeigt die Knotenansicht seit dem 20.10.2026 unter `visbox://app/knoten/` aus ihrem eigenen
Paket (`Kern/Knotenwege.swift`, `Start/Knotenquelle.swift`); nur Mappe, Modell und Render-Aufträge gehen an den Heim-PC.

**App-Bündel** — Auf dem Mac sieht ein Programm aus wie eine Datei, ist aber ein Ordner mit fester Ordnung: das
Programm selbst, seine Beschreibung, Bilder, Schriften und andere mitgelieferte Teile. Was im Bündel liegt, kommt mit
jeder neuen Fassung des Programms mit.
*Im Projekt:* `Visbox.app/Contents/Resources/` trägt Schriften, Icon, Beispielmappe und seit dem 20.10.2026 die
Knotenansicht (`Knoten/`); die Prüfstrecke setzt es zusammen (`.github/workflows/ipad.yml`).

**Ursprung (einer Webseite)** — Woher eine Webseite stammt: Anfang, Rechner und Anschluss ihrer Adresse zusammen
(etwa `https://heim.example:8443`). Ein Browser lässt eine Seite nur mit ihrem eigenen Ursprung frei sprechen und
trennt danach, was sie sich merkt. Bei einem eigenen Adressschema darf ein Browser den Ursprung auch «null» nennen.
*Im Projekt:* Die Knotenansicht baute die Adresse ihrer Brücke früher aus dem Ursprung; seit dem 20.10.2026 aus ihrer
eigenen Adresse (`brueckenAdresse` in `kosmovis/apps/visbox-knoten/src/mappe.ts`), damit sie auch unter `visbox://`
stimmt.

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

**Anlauffrist (Anlauf gegen Stillstand)** — Zwei Lagen, die eine Wache leicht
verwechselt: *«hat noch nicht angefangen»* und *«ist stehengeblieben»*. Beide sehen von
aussen gleich aus — es kommt kein Zeichen —, bedeuten aber das Gegenteil voneinander.
Die Anlauffrist ist die längere Frist, die **nur so lange** gilt, wie überhaupt noch kein
Zeichen kam; nach dem ersten Zeichen greift wieder die kurze.
*Gemessen, viermal derselbe Aufruf `blender --background --version`: 12,63 s / 0,66 /
0,26 / 0,15. Der erste Start kostet das Fünfzigfache der folgenden. Die Frist stand bei
10 s — ein kalter Start riss sie **zuverlässig**, nicht gelegentlich, und vier
kerngesunde Beweisläufe sind in einer Nacht daran gestorben. `Wache.anlauf_s` in
`fortschritt.py`; die Mutationsprobe «Anlauf gilt immer» fällt, denn dann bewacht die
Wache einen Prozess, der nie anfängt, ewig.*

**Seitencache (page cache)** — Der Teil des Arbeitsspeichers, in dem das Betriebssystem
zuletzt gelesene Dateien behält. Beim ersten Zugriff wird von der Platte gelesen, danach
aus dem Speicher — derselbe Aufruf ist dann um ein Vielfaches schneller, ohne dass am
Programm etwas anders wäre.
*Er ist der Grund für die Anlauffrist: Das Blender-Binary ist gross, und sein erster
Start bezahlt das Lesen. Er ist auch eine Falle für Zeitmessungen — wer den ersten Lauf
mitmisst, misst die Platte, nicht das Programm.*

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
nicht", `410` „diesen Weg gibt es hier nicht mehr" (seit Entscheid 118a die Antwort des
Heim-PC an ein iPad, das direkt statt über den Mac spricht — mit dem Satz, was zu tun ist). *Die Unterscheidung entschied in der Lizenzprüfung vom 18.08.2026 über die
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


**Base64** — Ein Verfahren, beliebige Daten als reinen Text zu schreiben, damit sie dort
durchkommen, wo nur Text erlaubt ist (in einem JSON-Dokument, in einer Web-Adresse). Aus
**drei Bytes werden vier Zeichen** — der Text ist also rund ein Drittel länger als die
Daten, die er trägt.

*Dieser Faktor 4/3 ist am 03.09.2026 zu einem Befund geworden: Ein Deckel für Bilder
verglich* Zeichen*, eine Fehlermeldung nannte die gemessene Grösse aber in* Bytes *und
die Grenze in* Zeichen — *beides mit der Einheit «MB» beschriftet. Die genannte Grenze
war dadurch um ein Drittel zu hoch, und wer ihr folgte, wurde ein zweites Mal abgewiesen.
Wenn zwei Zahlen in einem Satz stehen, müssen sie dieselbe Einheit haben — sonst ist die
Meldung eine Falle und keine Hilfe.*

**Aufräumen auch im Fehlerfall (try/finally, Kontextmanager)** — Eine Schreibweise in Python,
die garantiert, dass ein Schlussschritt läuft, egal wie ein Abschnitt endet: regulär, mit
einem Fehler oder durch einen Abbruch von aussen. Vergleichbar mit der Regel «wer die Baustelle
verlässt, schliesst das Tor» — auch wer wegen eines Unfalls weggeht. Ein **Kontextmanager**
ist dieselbe Garantie, in einen wiederverwendbaren Baustein verpackt (`with …:`).
*In diesem Projekt seit dem 07.10.2026 für das Bildmodell: `render.ein_modell_je_auftrag()`
gibt am Ende eines Auftrags den Grafikspeicher frei, auch wenn eine Variante mit einem Fehler
endet.*

**Kontextvariable** — Ein Wert, den ein Programmteil für «die gerade laufende Arbeit» ablegt,
ohne ihn durch jede Funktion einzeln weiterreichen zu müssen — und den ein zweiter, gleichzeitig
laufender Arbeitsstrang (ein *Faden*) nicht sieht. Wie ein Laufzettel, der an genau einem
Auftrag klebt. *Hier trägt sie den Modellvorrat des laufenden Auftrags: Die Fläche rechnet jeden
Lauf in einem eigenen Faden, und ein Lauf soll das Modell eines anderen nie zu fassen bekommen.*


**numpy** — Eine Python-Bibliothek für das schnelle Rechnen mit grossen Zahlenfeldern, etwa allen
Bildpunkten eines Bildes auf einmal (BSD-3). *Im Projekt:* rechnet im Renderschritt die 16-Bit-
Tiefenkarte um; ihr Installationspaket bringt libquadmath (LGPL) mit — ein im `NOTICE` offen
benannter Punkt.

**Pillow** — Die gebräuchliche Python-Bibliothek zum Öffnen, Umrechnen und Speichern von Bildern
(Lizenz MIT-CMU). *Im Projekt:* liest und schreibt die Bilder der Renderkette und der Prüfung;
wahlweise Zusatz, der Kern braucht sie nicht.

**Mermaid** — Eine Schreibweise, mit der man ein Ablaufbild als kurzen Text in ein Dokument
schreibt (Kästchen, Pfeile, Beschriftung); Anzeigeprogramme wie GitHub zeichnen daraus das Bild.
*Im Projekt:* das Architekturbild in `docs/WERKZEUGE_UND_ARCHITEKTUR.md`.

**Chromium ohne Fenster (headless)** — Der quelloffene Kern des Browsers Chrome, so gestartet, dass
kein Fenster erscheint: Er lädt eine Seite und speichert ein Bildschirmbild davon. *Im Projekt:* so
entstehen die Tafelkarten aus einer HTML-Seite (`tools/knoten_tafel.py`, Werkzeug- und
Architekturkarten vom 20.10.2026).

---

## 4 · Qualität und Absicherung

**Test** — Code, der anderen Code überprüft. Ein Test beschreibt eine Erwartung und
schlägt Alarm, wenn sie verletzt wird.

**Unit-Test** — Prüft einen einzelnen, kleinen Baustein isoliert.

**Integrationstest** — Prüft das Zusammenspiel mehrerer Bausteine.
*Warum er nicht durch viele gute Einzeltests zu ersetzen ist — an einem Fall aus diesem
Projekt (26.08.2026): Acht neue Prüfungen waren jede für sich geprüft und grün. Der erste
Test, der einen Auftrag durch die **ganze** Kette fuhr, fand binnen Minuten, dass eine
Angabe auf ihrem letzten Meter verlorenging — sie wurde ermittelt, geprüft und an der
Übergabestelle nicht weitergereicht. Ein Auftrag, den jemand **abbestellt** hatte, kam
draussen als „ungeprüft" an statt als „abbestellt": zwei sehr verschiedene Auskünfte, von
denen nur eine einen zweiten Lauf verlangt.*
*Der Einzeltest fragt: Tut dieses Stück, was es verspricht? Der Integrationstest fragt:
**Kommt das Versprochene auch an?** Die zweite Frage stellt sich niemand von selbst.*

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

**Uhrenabweichung (Clock Skew)** — Zwei Rechner zeigen nicht dieselbe Zeit. Über ein
Netzlaufwerk trifft das aufeinander: Wann eine Datei zuletzt geschrieben wurde, sagt die
Uhr des **Servers**; wie spät es *jetzt* ist, sagt die Uhr des eigenen Rechners.
*Warum das hier zählt:* Eine Sperre, die nach vier Stunden abläuft, rechnet mit beiden
Uhren gleichzeitig. Geht die eine um Stunden nach, sieht eine frische Sperre alt aus und
wird aufgebrochen.
*Wie das Projekt damit umgeht:* Es fragt **zwei** Quellen — die Dateizeit und den
Zeitpunkt, den die Rechnung selbst hineingeschrieben hat — und nimmt die **jüngere**. Im
Zweifel bleibt zu. *Eine Sperre, die eine falsch gehende Uhr aufbricht, ist keine Sperre,
sondern eine Verzögerung.*

**Sperre (Lock) und der verlorene Schreibvorgang** — Ein Schutz davor, dass zwei
Vorgänge gleichzeitig dasselbe bearbeiten.
*Was ohne ihn passiert, hier gemessen:* Zwei Rechnungen auf demselben Projekt lesen beide
die Projektdatei, rechnen beide, und schreiben beide zurück. Der zweite überschreibt den
ersten. **Beide melden Erfolg**, und eine der beiden Arbeiten ist weg — das nennt man
einen *verlorenen Schreibvorgang*, und er ist deshalb gefährlich, weil nichts danach
aussieht.
*Wie die Sperre gemacht wird:* Eine Datei, die **nur angelegt werden kann, wenn es sie
noch nicht gibt** — darüber entscheidet das Betriebssystem in einem einzigen Schritt.
Erst nachsehen und dann anlegen hätte genau dazwischen dieselbe Lücke.
*Und warum sie von selbst abläuft:* Stürzt eine Rechnung ab, bleibt ihre Sperrdatei
stehen. Nach vier Stunden darf die nächste sie übernehmen. **Eine Sperre, die man nur von
Hand lösen kann, wird von Hand gelöscht — auch dann, wenn sie gerade zu Recht steht.**

**Zwischenspeicher (Cache) einer Rechenkette** — Ein Ablageort für **Ergebnisse**, damit
ein Rechenschritt, dessen Eingaben sich nicht geändert haben, nicht noch einmal läuft.
*Warum es ihn hier gibt:* Ein Blender-Lauf dauert Minuten, ein Bild ebenso. Wer nur den
Text ändert, soll nicht auf die Geometrie warten.
*Woran er erkennt, dass zwei Aufträge dieselben sind:* an einem Fingerabdruck über alle
Angaben des Schritts — nicht am Dateinamen. Ein Modell, das unter demselben Namen
ausgetauscht wird, ist ein anderes, und das merkt er.
*Und was er nie tut:* ein Ergebnis ausliefern, dessen Dateien inzwischen fehlen. Dann
rechnet er lieber neu. **Ein Speicher darf langsam machen, nie falsch.**

**Relativer und absoluter Pfad** — Zwei Arten, eine Datei zu benennen.
*Absolut:* der ganze Weg von der Wurzel der Festplatte an, mit allen Ordnern dazwischen —
und damit fast immer mit dem **Namen des Benutzers** darin.
*Relativ:* der Weg von einem Bezugspunkt aus, hier vom Projektordner. `../haus.ifc` heisst
«eine Ebene höher, dann haus.ifc».
*Warum das Projekt seit dem 21.09.2026 relativ speichert:* Der absolute Pfad trägt einen
Benutzernamen, und Regel 3 verbietet den in diesem öffentlichen Repo. Er wurde beim
Speichern ersetzt — und zeigte danach **auf nichts**. Jede Mappe verlor so ihr Modell.
*Und der Nebeneffekt, der mehr wert ist als die Reparatur:* Eine Mappe mit relativen
Pfaden lässt sich **verschieben**. Wer sie samt Modell auf einen Stick kopiert, hat dort
ein gültiges Projekt.

**Fail-closed** — Entwurfshaltung: Im Zweifel oder bei Störung *nicht* handeln. Für
teure, nicht rückholbare Vorgänge wie GPU-Renderläufe die richtige Grundeinstellung.
*Zweites Beispiel im Projekt, seit 21.09.2026 (E25):* Wer die Oberfläche im Netz
erreichbar machen will und **kein Kennwort** setzt, bekommt keinen Server, sondern eine
Erklärung. Das Gegenteil wäre: Sie startet, und der Schutz fehlt still.
*Der Satz dazu:* **Eine Sperre, die man vergessen kann, ist im entscheidenden Augenblick
vergessen.**

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
Teil der Messung, sondern eine Entscheidung darüber, wo „gut genug" anfängt.
*In diesem Projekt `SCHWELLE_GEOMETRIE = 0.65` und `SCHWELLE_STIL = 0.666`. Die beiden
stehen inzwischen auf verschiedenen Beinen, und der Unterschied ist lehrreich.*
*Die **Stil-Schwelle** stand bis zum 18.08.2026 auf 0,30 und war damit **wirkungslos**: Der
Boden des Verfahrens — was zwei völlig unähnliche Bilder erreichen — liegt bei 0,526. Eine
Schwelle darunter lässt **jedes beliebige Bildpaar** durch. Sie ist seither **abgeleitet
statt gesetzt**: Boden plus zwei Streuungen, gemessen an 4950 Paaren.*
*Die **Geometrie-Schwelle** ist weiterhin gesetzt und nicht hergeleitet — der Grund, warum
es die Schwellenstudie gibt. Sie galt lange als unerreichbar; am 24.08.2026 hat sich
gezeigt, dass nicht sie zu hoch stand, sondern die Kamera zu weit (siehe **Rahmen gegen
Messen**).*
*Die Lehre aus der Stil-Schwelle gilt für jede: **Eine Schwelle unterhalb des eigenen
Zufallsniveaus ist kein Tor, sondern eine Verzierung** — und sie sieht aus wie Schutz.*

**Kalibrierung** — Den Zusammenhang zwischen einer Messgrösse und dem, was sie bedeuten
soll, an Fällen festmachen, deren Antwort man bereits kennt. Eine Waage kalibriert man mit
bekannten Gewichten, nicht mit unbekannter Fracht. Kalibrieren heisst dabei nicht
zwangsläufig, eine bessere Zahl zu finden — zuerst heisst es, die Frage überhaupt messbar
zu machen: Bei welcher Art und Stärke von Abweichung reagiert die Metrik, und wie stark?
*In diesem Projekt `src/aiimaging/schwellenstudie.py`: Eine bekannte Soll-Tiefenkarte wird
in bekannter Art und bekannter Stärke verfälscht, und gemessen wird, wie der Score darauf
antwortet. Das Ergebnis steht in `docs/SCHWELLENSTUDIE_2026-08-18.md`.*

**Abgelesene Schwelle** — Eine Grenzzahl, die jemand aus einer Handvoll gemessener Fälle
*abgelesen* hat: «die guten lagen über 0,8, die schlechten darunter, also nehmen wir 0,8».
Sie sieht aus wie eine kalibrierte Schwelle und ist keine. Der Unterschied liegt nicht in
der Zahl, sondern darin, was man über sie sagen kann: Bei einer kalibrierten Schwelle weiss
man, **wie viele gute Fälle sie fälschlich sperrt und wie viele schlechte sie durchlässt**;
bei einer abgelesenen weiss man nur, dass sie die paar Fälle trennte, an denen man sie
abgelesen hat.
*In diesem Projekt tragen zwei Zahlen diesen Vorbehalt ausdrücklich im Quelltext:
`PAAR_RHO_SCHWELLE = 0.80` — abgelesen an **sieben** Fällen aus **einer** Szene — und
`PAAR_KANTENANTEIL_SCHWELLE = 0.20`, die beim Vierfachen des Zufalls und bei einem knappen
Viertel des perfekten Bildes liegt. Beide dürfen deshalb nichts sperren; sie stehen als
Anzeige da, bis `auftraege/offen/auf-20260827-61.json` sie kalibriert.*
*Warum das Ablesen trotzdem richtig war: Eine abgelesene Schwelle, die sich als solche zu
erkennen gibt, ist ehrlicher als gar keine Zahl — sie sagt, wo man heute steht. Unehrlich
wird sie erst, wenn sie anfängt zu entscheiden.*

**Beleg im Repo vs. Beleg am Gerät** — Zwei Arten, eine Behauptung zu stützen, und sie
sind **nicht austauschbar**. Eine Datei im Repo belegt, was jemand *geschrieben* hat. Ob
das auf einem anderen Rechner auch **läuft**, sagt sie nicht — dort entscheidet die
Installation, und die kann älter sein, anders heissen oder gar nicht existieren.
*In diesem Projekt am 27.08.2026 teuer gelernt: Ein Posten stand **sechs Tage** als
erledigt, weil die eingecheckte Diensteinheit den nötigen Schalter trug. Die installierte
stammte vom 20.08. und kannte ihn nicht; in der Zwischenzeit blieb jede über diesen Weg
bestellte Arbeit liegen.*
*Der Wächter darüber konnte es nicht sehen — er prüfte, ob ein Beleg **existiert**, und
der existierte. Seither muss jede erledigte Zeile sagen, welcher Art ihr Beleg ist, und
«im Repo» ist gesperrt, sobald der Beleg einen Kommandozeilenschalter, eine Diensteinheit
oder einen Betriebspfad nennt. Nachgesehen wird auf dem fremden Gerät weiterhin nicht —
das kann von hier niemand. Was sich erzwingen lässt, ist die **Angabe**, und danach ist
prüfbar, was vorher Auslegung war.*

**Zustellweg (eines Auftrags)** — Der Weg, auf dem ein Auftrag seinen Adressaten
tatsächlich **erreicht** — nicht der Ort, an dem er abgelegt wird. Die beiden sind leicht
zu verwechseln, weil eine abgelegte Datei aussieht wie eine zugestellte.
*In diesem Projekt am 27.08.2026 aufgefallen: Zwei der drei Worker lesen unser Repo und
bekommen ihre Aufträge über `git pull`. Der dritte hat es nicht — für ihn lagen vier
Aufträge, der älteste seit drei Tagen, an einem Ort, den er nicht öffnen kann. Der
Rückstand wurde die ganze Zeit korrekt gezählt und war trotzdem irreführend: Er sah aus
wie Wartezeit bei ihm.*
*Daraus die Regel:* **Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein
Rückstand bei ihm — er ist einer beim Absender.** *Die Abhilfe ist der Block
(`aiimaging.auftragspost`): der ganze Auftrag als ein selbsttragender Text, der ohne das
Repo gelesen werden kann.*

**Boden einer Kennzahl** — Der Wert, den eine Kennzahl schon **ohne jede Leistung**
erreicht. Er entsteht nicht durch Messen, sondern durch die Bauart der Zahl, und er hängt
oft an etwas, das mit der gemessenen Sache nichts zu tun hat.
*In diesem Projekt exakt bestimmt (27.08.2026): Ein völlig gleichförmiges Bild — das
wertloseste denkbare Ergebnis — bekommt bei* `geom_iou` *genau den Anteil der Bildfläche,
den die Szene mit Geometrie füllt. Auf drei Szenen gemessen: 0,1104 · 0,1729 · 0,5297,
jedes Mal auf volle Rechengenauigkeit gleich. Kein Messwert, sondern Arithmetik: Ein
gleichförmiges Bild trägt nirgends die Marke «hier ist nichts», also gilt das ganze Bild
als Geometrie, und der Anteil der Übereinstimmung ist genau der Anteil der Szene.*
*Warum das gefährlich ist:* **0,53 liest sich wie «zur Hälfte richtig» und heisst «die
Szene ist gross».** *Wer eine Schwelle über einer Kennzahl setzt, ohne ihren Boden zu
kennen, setzt sie über einer Zahl, deren untere Hälfte niemandem gehört.*
*Die Abhilfe seit dem 28.08.2026 (Owner-Entscheid) ist nicht, die Zahl zu ändern, sondern
sie zu **begleiten**:* `geom_iou_norm = (geom_iou − Vordergrundanteil) / (1 − Vordergrundanteil)`
*steht daneben — 0 heisst «so gut wie ein gleichförmiges Bild», 1 heisst «deckungsgleich».
Der Score selbst bleibt unangetastet, damit die Schwelle 0,65 und die Kalibrierung vom
18.08. gültig bleiben. Negative Werte werden nicht abgeschnitten: «schlechter als nichts»
und «so gut wie nichts» sind zwei verschiedene Aussagen.*

**Doppelte Vorgabe** — Derselbe Voreinstellungswert, an zwei Stellen geschrieben. Solange
beide gleich sind, fällt es nicht auf; ändert jemand die eine, sieht die andere weiterhin
schlüssig aus und ist trotzdem falsch. **Kein Test schlägt an, weil beide Stellen für sich
in Ordnung sind.**
*In diesem Projekt am 28.08.2026 fünf Tage lang wirksam: Der Owner hatte am 23.08.
entschieden, dass die Kamera waagrecht steht statt gekippt — die Bibliothek wurde
umgestellt, das ausführende Skript nicht. Dort stand seit dem 21.08. ein Rückfall auf den
alten Wert, der an jenem Tag richtig war und durch einen Entscheid an anderer Stelle falsch
wurde. Jeder Renderlauf seither kippte die Kamera, obwohl entschieden war, dass er es nicht
tut.*
*Aufgefallen ist es nicht einem Test, sondern dem Owner am fertigen Bild.* **Die Abhilfe
ist nicht, beide Stellen gleichzusetzen, sondern die zweite zu streichen:** *Wo nur eine
Stelle die Vorgabe trägt, kann nichts auseinanderlaufen. Der Wächter dazu prüft den
Quelltext auf einen zweiten Rückfall — nicht das Verhalten, denn das Skript läuft nur
innerhalb von Blender.*

**Abgeleiteter Zustand** — Ein Zustand, den niemand einträgt, weil er sich aus etwas
anderem **ergibt**. Sein Gegenteil ist das gepflegte Feld: eine Angabe, die jemand von
Hand richtig halten muss. *Ein gepflegtes Feld verfällt; ein abgeleiteter Zustand kann es
nicht.*
*In diesem Projekt am 28.08.2026 nach einer Messung der HomeStation eingeführt: Im
Auftragsordner lagen **63** Aufträge und daneben **44** Ergebnisse — **40 Paare**. Vierzig
Aufträge galten als offen, obwohl ihre Antwort danebenlag, und **keiner der 63** trug ein
Zustandsfeld. Aufgeräumt hatte nie jemand.*
*Der Zustand wird seither aus dem Ergebnis gelesen, mit fünf Werten:* kein Ergebnis =
**offen**, `ok` = **beantwortet**, Fehler oder Ablehnung = **gerechnet, nicht
beantwortet**, ein Weiterleitungsvermerk = **weitergereicht**, eine Rücknahme =
**zurückgezogen**.
*Die Unterscheidung ist nicht Pedanterie:* **Ein Ergebnis zu haben heisst nicht,
beantwortet zu sein.** *Gemessen: Von zwei Aufträgen an den Vertrags-Worker, die ein
Ergebnis trugen, waren zwei von zwei blosse Weiterleitungsvermerke. Nach der alten
Zählung galten acht Aufträge als erledigt, die niemand beantwortet hat.*

**Auftragsart (`multipass`, `render`, `qa`, `frage`)** — Woran der Empfänger eines
Auftrags erkennt, **ob eine Maschine oder ein Mensch ihn beantwortet**. Die ersten drei
sind Läufe: Sie starten eine Rechnung und liefern Messwerte. `frage` ist keiner — sie
verlangt eine Auskunft, und ein Runner kann sie nicht geben.
*Wozu die vierte Art am 01.09.2026 dazukam:* Neun der Aufträge an die HomeStation trugen
`qa` und meinten eine Frage — *«Warum reicht `/api/mcp/tools` keine Schemata durch?»* ist
nichts, was ein Renderer ausführen kann. Ein Sammellauf über alle offenen Aufträge hätte
sie angefasst und für jede einen Fehlschlag geschrieben. Seit der Trennung zählt und nennt
der Homeworker sie, **fasst sie aber nicht an** — dieselbe Behandlung wie ein Auftrag, der
einem anderen Worker gehört.
*Und was sie ausdrücklich nicht tut:* Eine Frage umzutypisieren beantwortet sie nicht. Der
Rückstand sank dadurch um **null**.

**Rückstandsdeckel** — Eine Obergrenze für die Zahl **offener Aufträge je Adressat**, die
das Werkzeug durchsetzt und nicht der Vorsatz. Wer den elften Auftrag an jemanden
schreiben will, der schon acht offene hat, bekommt keinen — sondern die Liste der drei
ältesten, die zuerst zu schliessen wären.
*Warum es ihn gibt:* Ein Rückstand wächst nicht durch eine Entscheidung, sondern durch
vierzig kleine, von denen jede für sich vernünftig war. *Was von Hand eingehalten wird,
wird irgendwann nicht mehr eingehalten.*
*Die Zahl ist eine Setzung und keine Messung* (acht, beschlossen am 28.08.2026) — sie
steht deshalb als benannte Konstante und nicht als Zahl im Code.

**Geerbter Vorbehalt** — Eine Einschränkung, die man aus einer **fremden** Messung
übernimmt und im eigenen Text weiterträgt, ohne sie nachgerechnet zu haben. Sie wird mit
jeder Weitergabe unschärfer, und irgendwann liest sie sich wie eigenes Wissen.
*Im Projekt am 02.09.2026:* Die Bauwerksmaske trug den Satz, der Kantenanteil sei bei
einem Nachbargebäude hinter dem Bau eingeschränkt — samt zwei Zahlen aus einer Messung
der HomeStation. Nachgerechnet **reproduzierte er hier nicht**: Mit gebauten Karten
trennt der Kantenanteil mit Nachbarn genauso gut wie mit Himmel (0.9431 gegen 0.9480).
*Das war kein Widerspruch, sondern die **Eingrenzung**:* Der Befund ist eine Aussage über
den **Schätzer** und nicht über die **Szene** — bei 170 m Abstand ist ein Nachbar 1 m
dahinter ein relativer Unterschied von 0,6 %, den eine gebaute Karte exakt trägt und ein
Schätzer nicht.
*Was daraus folgt:* Ein Vorbehalt nennt, **wessen** Messung er trägt, **wofür** sie gilt
und **was daran nicht nachgerechnet** ist. *Ein Vorbehalt, der mehr behauptet als er
belegt, ist derselbe Fehler wie eine Zahl ohne Anker — nur in die vorsichtige Richtung.*

**Die Bedingung nicht hergestellt** — Der häufigste Weg, eine Messung zu verfehlen: Der
Aufbau sieht aus wie der gefragte Fall, stellt aber die Bedingung gar nicht her, und das
Ergebnis liest sich trotzdem wie eine Antwort.
*Im Projekt, zweimal am selben Nachmittag:* Ein Nachbargebäude sollte den Hintergrund
hinter einem Bauwerk füllen. Im ersten Anlauf war es zu klein und deckte **9,8 %**; im
zweiten war es gross genug, aber die Kamera rahmte die **ganze Szene** statt des Ziels —
also stand über dem Nachbarn Himmel und der Hintergrund war zu **86 %** wieder Himmel.
Erst der dritte Anlauf (51,7 %) hat gemessen, was gefragt war.
*Die Abhilfe ist eine Zahl im Bericht, die sagt, ob die Bedingung herrschte* — hier
``anteil_hintergrund_endlich``. Ohne sie wäre «Nachbar ja/nein» nur ein Dateiname gewesen.

**Fassungsabstand (zwischen zwei Maschinen)** — Wenn zwei Rechner dasselbe Repo mit
verschiedenen Sprachfassungen bearbeiten und der neuere Code schreibt, den der ältere
nicht einmal **einlesen** kann.
*Im Projekt am 02.09.2026:* Die HomeStation fährt Python **3.14.4**, diese Umgebung
**3.11.15**, das Repo sagt `>=3.11` zu. Ein mehrzeiliger Ausdruck *innerhalb* eines
f-Strings (erlaubt ab 3.12, PEP 701) machte `abholer.py` hier unlesbar: **25 Testdateien
brachen ab, bevor eine einzige Probe lief** — während dieselbe Sammlung drüben grün war.
*Das Tückische ist die Richtung:* Der Bruch entsteht auf der neueren Maschine und zeigt
sich nur auf der älteren. Wer ihn verursacht, kann ihn nicht sehen; wer ihn sieht, hat ihn
nicht verursacht. **Ein Wächter kann nur die eine Seite decken** — `ast.feature_version`
deckt Sprachmerkmale ab, nicht den Tokenizer. Die andere Hälfte der Antwort ist keine
Probe, sondern eine Ansage.

**Erfundener Status** — Ein Wort im Ergebnisfeld, das der Vertrag nicht kennt, von Hand
geschrieben und an der Prüfung vorbei: `teilweise`, `erledigt`, `teilweise — gerettet aus
einem abgebrochenen Lauf`.
*Warum es zählt:* Die Zustandsableitung las bis zum 02.09.2026 **alles** als Antwort, was
kein *benannter* Fehlschlag war. Drei Aufträge galten damit als beantwortet — einer sagte
in seinem eigenen Ergebnistext *«Die übrigen Teile folgen.»*
*Seither gilt:* Was `baue_ergebnis` nicht kennt, ist **keine Antwort** — der Auftrag
bleibt im Rückstand und der Fund wird benannt. *Ein zu Unrecht offener Auftrag kostet eine
Rückfrage, ein zu Unrecht geschlossener eine Antwort, die nie kommt.*
*Dieselbe Entscheidung wie beim **Weiterleitungsvermerk**, eine Ebene tiefer.*

**Selbstbindung (gegen Hausregel)** — Eine Regel, die nur den bindet, der sie sich gegeben
hat, weil sie an *seinem* Werkzeug hängt und nicht am Gegenstand.
*Im Projekt:* Der **Rückstandsdeckel** wirkt in `schreibe_auftrag`. Wer seine Auftragsdatei
selbst anlegt — die HomeStation tut das —, kommt daran vorbei. Owner-Entscheid 02.09.2026:
**Das bleibt so**, denn sie kennt ihre Lage am besten, und eine Bremse, die ein Dritter
bedient, ist Bürokratie und keine Steuerung.
*Was daraus folgt, ist keine Änderung, sondern ein Name:* Der Deckel heisst seither
Selbstbindung und nicht Regel — samt der gemessenen Zahl, dass der Rückstand seit seiner
Einführung von 27 auf 36 gestiegen ist, ohne dass er ein einziges Mal ausgelöst hätte.
*Ein Deckel, der nur den bindet, der ihn eingeführt hat, bremst niemanden — er darf dann
aber nicht so tun.*

**Ungedrückter Schalter** — Ein Bedienelement, das keine Probe je benutzt hat. Es kann
still nichts tun: Kein Test wird rot, kein Benutzer bekommt eine Fehlermeldung, und wer
es setzt, hält das Ausbleiben der Wirkung für seine eigene Schuld.
*Gemessen am 01.09.2026:* **9 von 33** Kommandozeilenschaltern kamen in keiner einzigen
Probe vor. Zwei waren kaputt — einer legte keine Datei ab, obwohl er es versprach; einer
wies einen gültigen Adressaten mit «invalid choice» ab, weil seine Liste ein zweites Mal
im Skript stand. Drei weitere **konnten** gar nicht geprüft werden: Ihr Einstieg nahm
kein ``argv`` entgegen und las die Kommandozeile des Testlaufs.
*Der Satz dahinter, und wir geben ihn sonst an die Oberfläche weiter:* **Ein
Bedienelement ohne Wirkung ist schlimmer als keines — es sagt, etwas sei geschehen.**
*Gezählt wird von `tools/schalterprobe.py`, und die Zahl steht auf null statt auf einer
Obergrenze: Eine Obergrenze wäre ein Vorrat, den man aufbraucht.*

**Gleichstand (in einer Auswahl)** — Wenn mehrere Möglichkeiten denselben Bestwert
erreichen und die Auswahl trotzdem **eine** davon zurückgibt, als wäre sie *die* Antwort.
Die Wahl fällt dann in Wahrheit an die Reihenfolge der Liste.
*Im Projekt gemessen (01.09.2026):* Bei der Wahl von drei Kamerastandpunkten aus zwölf
Richtungen erreichen auf einem würfelförmigen Bau **16 von 56** Kombinationen denselben
Wert, auf anderen Formen 4 bis 8. Das ist **kein Fehler** — eine Hüllbox ist symmetrisch,
spiegelbildliche Standpunkte sind gleich gut. Der Fehler wäre, es nicht zu sagen.
*Zwei Dinge gehören dazu:* Der Gleichstand wird **deterministisch** aufgelöst (sonst wäre
jeder Lauf ein anderer Auftrag), und er wird **gemeldet** — *gemeldet heisst nicht
gewürfelt.*

**Eine Zahl, die an einer falschen Messung geeicht wurde** — Eine Kennzahl kann richtig
gerechnet und trotzdem wertlos sein, wenn die Messreihe, aus der ihre Rechtfertigung
stammt, einen Fehler enthielt.
*Im Projekt:* Die Begründung für das Mass `flaechenanteil` lautete «schwankt um den
Faktor 2,3 bis 1,9 — es *kann* also unterscheiden». Beide Zahlen waren mit einem um 24
bis 25 % zu grossen Kameraabstand gemessen; ein grosser Teil der Spanne **war der
Abstandsfehler**. Nachgerechnet bleibt 1,07 bis 2,25 — auf würfeligen Grundrissen
unterscheidet das Mass praktisch nichts.
*Die Lehre ist nicht «neu rechnen», sondern:* Wenn eine Messung berichtigt wird, sind die
**Begründungen** mit zu prüfen, die auf ihr ruhen — sie stehen in Docstrings und
Dokumenten und ändern sich nicht von selbst.

**Vorzeichenfehler** — Ein Fehler, der die **Lage** einer Sache verkehrt und ihre
**Masse** unverändert lässt. Er überlebt jede Prüfung, die Längen, Grössen oder Anteile
vergleicht — und das sind die meisten.
*Im Projekt am 01.09.2026:* Eine Drehung um +90° statt −90° ergab zusammen mit Blenders
eigener Drehung eine halbe Umdrehung. Das Gebäude stand auf dem Kopf, das Dach lag 26,7 m
unter dem Nullpunkt — und **jede Kantenlänge blieb dieselbe**. Aufgefallen ist es erst,
als zum ersten Mal ein unsymmetrisches Modell von Augenhöhe fotografiert wurde; an einem
symmetrischen Quader sieht kopfüber aus wie richtig herum.
*Was hilft:* eine Probe, die **Vorzeichen** vergleicht statt Beträge — hier der Rundlauf
«fremde Drehung, dann eigene Gegendrehung, ergibt den Ausgangspunkt» an einem Punkt mit
drei **verschiedenen** Koordinaten. Mit `(1,1,1)` wäre auch sie blind.

**Einbahnstrasse (zwischen Annahme und Entscheidung)** — Wenn ein Wächter zwei Grössen
vergleicht, darf **höchstens eine** von der Zahl abhängen, die er bewachen soll. Hängen
beide daran, prüft er eine Identität und lässt jeden Wert durch.
*Im Projekt, am selben Tag und im eigenen neuen Code:* Der Rundlauf oben verglich
«Blenders Drehung» mit «unserer Gegendrehung». Im ersten Entwurf leiteten *beide* ihren
Winkel aus derselben Konstanten ab — zwei entgegengesetzte Drehungen heben sich auf, egal
um welchen Winkel. Die Mutationsprobe liess ihn grün. Richtig ist: Die **Annahme über ein
fremdes Programm** trägt ihre eigene Zahl, die **eigene Entscheidung** hängt an der
Konstanten.
*Die Faustregel:* Was du bewachst, darf nur auf einer Seite der Gleichung stehen.

**Umfeld (gegen Bauwerk und Gelände)** — Was in einer Szene steht und **nicht dazugehört**:
Bäume, Nachbargebäude, Strassenmöbel.
*Warum es einen eigenen Namen braucht:* Die Bauwerksmaske fragt nicht «ist das Gelände?»,
sondern «ist das unser Bauwerk?» — und darauf gibt es **zwei verschiedene Nein**. Der Boden
trägt das Bauwerk, das Umfeld steht daneben. Ein Nachbargebäude als Gelände zu führen wäre
eine falsche Aussage über die Szene.
*Gemessen am 01.09.2026:* An echtem Bestand standen Bäume als `IfcGeographicElement` und
ein Nachbargebäude als `IfcCivilElement` — bis dahin zählte beides als **Bauwerk**,
gemessen wurde also der Bau plus die Nachbarschaft. Ausgeschlossen wird es seither **und
benannt**: *Ein benannter Ausschluss ist widerlegbar, ein stiller nicht.*
Seit 24.10.2026 zählen auch Namen mit einem *Vegetationswort* (siehe dort) als Umfeld, ohne IFC-Klasse.

**Ein Feldname, zwei Bedeutungen** — Wenn dasselbe Feld je nach Alter oder Herkunft
zweierlei enthält und **nichts prüft, welches von beiden vorliegt**. Der Code liest dann
die eine Bedeutung und bekommt manchmal die andere.
*Im Projekt am 01.09.2026, zweimal am selben Tag:* `auflagen` war in den älteren
Aufträgen das Wörterbuch, das der ausführende Runner liest (Leistungsgrenze,
Leerlauf-Gate), und in den neueren eine Liste von Sätzen für einen Menschen. Der Runner
rief `.get` — an einer Liste ein Absturz. `rueckgabe` war einmal die Transportangabe
(wohin, nur Zahlen) und einmal die Liste der Fragen; über die Transportform gezählt kam
in jedem verschickten Auftrag die Zeile *«verzeichnis / nur_zahlen / hinweis»* heraus.
*Was hilft:* an einer Stelle in die gemeinte Form übersetzen (bei uns
`auflagen_maschine`, `auflagen_text`, `rueckgabepunkte`) und dort prüfen — nicht an
jedem Leser einzeln, denn einer vergisst es.

**Formprüfung statt Inhaltsprüfung** — Ein Wächter, der prüft, ob ein Feld *da* ist, und
damit zusichern soll, dass etwas *drinsteht*. Er ist grün, solange die Hülle stimmt.
*Im Projekt:* Der Test *«jeder Auftrag sagt, was zurückkommen soll»* liess
ausdrücklich beide Formen zu und war damit für 42 Dateien wirkungslos — die
Transportform ist wahr und nennt keinen einzigen Rückgabepunkt. Drei der betroffenen
Aufträge lagen bei Adressaten, die noch nie geantwortet hatten; ihr Abschnitt *«WAS
ZURUECKKOMMEN SOLL»* bestand aus drei Schlüsselnamen.
*Verwandt mit dem **vakuösen Test**, aber nicht dasselbe:* Der vakuöse Test prüft eine
leere Menge; dieser prüft eine volle Menge auf das falsche Merkmal.

**Die Attrappe baut die kaputte Gestalt nach** — Der Grund, warum eine ganze Testsammlung
einen Fehler nicht sehen kann: Die erfundenen Daten der Tests sehen anders aus als die
wirklichen Daten, und zwar genau an der Stelle, an der es darauf ankommt.
*Im Projekt:* 118 Proben prüften den Homeworker — mit Aufträgen, die alle die
Wörterbuchform trugen. Die echten Dateien trugen seit fünf Tagen die Liste. *Die Sammlung
prüfte das Skript mit erfundenen Aufträgen und die Aufträge ohne das Skript; dazwischen
lag der Fehler.* Die Abhilfe ist eine Probe, die die **wirklichen** Dateien durch den
**wirklichen** Aufruf schickt.

**Ein Satz, der nur auf einer Maschine wahr ist** — Ein Kommentar behauptet eine Tatsache
über *die Umgebung*, in der der Code läuft. Auf der Maschine, auf der er geschrieben
wurde, stimmt er; auf jeder anderen ist er falsch — und dort **lädt er zu genau der
Änderung ein, die er verhindern sollte.**
*Im Projekt am 06.09.2026:* Neben `szene.cycles.device = "CPU"` stand
`# in dieser Umgebung gibt es keine GPU`. Im Entwicklungscontainer wahr; auf der
HomeStation steht eine RTX 5090. Wer den Satz dort las, sah eine ungenutzte Karte und
hatte jeden Grund umzustellen. Gemessen wurde dann statt umgestellt: OptiX ist bei den
real genutzten 8–128 Samples auf 512 px in allen drei Konfigurationen **10–35 %
langsamer** (fester Anlaufaufwand), und es verschiebt Kantenpixel der Material-ID-Maske
(bis 217/255 bei 28 von 262 144 Pixeln). *Der Kommentar war falsch, das Verhalten
richtig.*
*Die Abhilfe ist nicht Löschen, sondern Ersetzen:* Der Grund heisst jetzt «gemessen am
…, so viel langsamer, und ein Wechsel verschiebt Zahlen». Der falsche Satz steht als
**Zitat** daneben — wer ihn spurlos löscht, nimmt dem nächsten die Warnung, und der stellt
dieselbe Frage neu. Verwandt mit **Fassungsabstand**: Dort ist die Maschine verschieden,
hier der Satz über sie.

**Baulich zwingende Deckung** — Zwei Stellen sehen dieselben Daten nicht **zufällig**,
sondern weil sie **dieselbe Quelle lesen**. Der Unterschied entscheidet, ob eine Messung
nötig ist oder ob sie sich erübrigt.
*Im Projekt am 09.09.2026:* Ob Box- und Bildseite dieselben Namen sehen, musste gemessen
werden — Materialnamen decken sich zu **0 %**, Objektnamen zu 100 %. An **einer** Stelle
war die Messung überflüssig: `blender_depth_stage._bbox_bauwerk` und
`_material_id_zuweisen` lesen beide ``obj.name`` desselben Blender-Objekts. Dort ist die
Deckung keine Beobachtung, sondern eine Eigenschaft des Baus.
*Warum das trotzdem dasteht:* Eine baulich zwingende Deckung kann durch eine Änderung an
einer der beiden Stellen aufhören zu gelten, **ohne dass irgendwo etwas bricht**. Sie ist
darum kein Grund, nicht hinzusehen — sondern einer, den Grund aufzuschreiben.

**Brücke zwischen zwei Regeln** — Ein **Ergebnis** von der einen Seite zur anderen
tragen, statt die **Regel** zu verdoppeln. Die zweite Seite lernt nichts dazu; sie bekommt,
was die erste gemessen hat.
*Warum das nicht dasselbe ist wie eine zweite Regel:* Eine kopierte Regel läuft auf beiden
Seiten eigenständig und kann eigenständig danebenliegen — dann gibt es zwei Wahrheiten und
keine Auskunft, welche gilt. Ein übertragenes Ergebnis hat genau eine Quelle, und die steht
im Befund.
*Im Projekt seit dem 08.09.2026:* `maske.bauwerksmaske(gelaende_zusatz=…)` nimmt die
Geländenamen, die `glbbox` an der **Form** erkannt hat. Die Bildseite hat keine Geometrie
und könnte die Formregel gar nicht rechnen. Der Befund sagt `gelaende_quelle: "name+form"`
— und zwar erst, wenn ein übertragener Name wirklich **gegriffen** hat: *Eine
Herkunftsangabe, die eine Absicht meldet statt einer Wirkung, ist keine.*
*Und eine Brücke muss vor dem Bau vermessen werden.* Ob beide Ufer zusammenpassen, war hier
nicht selbstverständlich — siehe **Ein Mangel, der benannt ist, ist kein Loch mehr**.

**Ein Mangel, der benannt ist, ist kein Loch mehr** — Wo etwas nachweislich nicht geht,
ist der Satz darüber das Ergebnis. Nicht als Entschuldigung, sondern als Auskunft: Wer ihn
liest, sucht nicht mehr nach einer Lösung, die es nicht gibt, und hält den Zustand nicht
für versehentlich.
*Im Projekt am 08.09.2026:* Trägt die Materialtabelle Materialnamen, kann die Formregel der
Boxseite der Bildseite **nicht** aushelfen — gemessen: Deckung null. Die Boxseite findet
das Gelände, die Bildseite nicht; die Rahmung wäre richtig und die Maske trotzdem leer.
*Ohne diesen Satz liest jemand `glbbox`, sieht dort die Zweitmeinung und hält beide Seiten
für versorgt.* Er steht nur, wo er zutrifft — bei Objektnamen trägt die Brücke, und dort
wäre er eine **Dauerwarnung**.

**Zweitmeinung (gegen zweite Regel)** — Zwei Verfahren beurteilen dieselbe Frage. Der
Unterschied entscheidet, ob daraus Hilfe wird oder Widerspruch.
*Eine **zweite Regel** widerspricht der ersten.* Dann sind zwei im Spiel, und wenn sie
verschieden urteilen, ist eine falsch — nur weiss niemand welche. *Eine **Zweitmeinung**
spricht nur, wenn die erste schweigt.* Sie überstimmt nichts; sie füllt eine Lücke.
*Im Projekt seit dem 07.09.2026:* `gelaendeform` erkennt Gelände an der Gestalt statt am
Namen. Sie wird in `glbbox.bauwerksbox` **erst gefragt, wenn die Namensregel unter 5 %
Schrumpfung geblieben ist** — am echten Bestand mit 2,32 % also sehr wohl. Wo der Name
getrennt hat, bleibt der Name zuständig, auch wenn die Form noch etwas fände. Und der
Befund sagt, **welche** entschieden hat (`entschieden_durch`): *Eine Box, der man nicht
ansieht, woher sie kommt, ist die Box, die um 2,32 % schrumpfte und wie eine Lösung
aussah.* Drei Antworten: «name» (die Wortliste hat getrennt), «form» (die Gestalt) und «keine» (nichts hat getrennt) —
seit dem 22.10.2026 auf beiden Wegen gleich; der Blender-Weg sagte bis dahin «keine», auch wenn der Name getrennt hatte
(Ergebnis 334, Protokoll 74 §250).

**Gelände an der Form** — Gelände daran erkennen, wie ein Körper **aussieht**, nicht wie
er **heisst**. Drei Zahlen, alle relativ zur Szene: **Grundrissanteil** (Fläche des
Körpers ÷ Fläche der Szene), **Flachheit** (Höhe ÷ kleinere Grundriss-Kante) und
**Tieflage** (wo die Oberkante im Höhenbereich sitzt). Gelände ist gross, flach und unten.
*Warum es das braucht:* Die Namensregel versagt auf echtem Bestand — 2,32 % Schrumpfung
statt Zehnerprozenten. Und es gibt kein Wort, das sie retten könnte: `decke` wäre nötig
(111 von 112 Geländeknoten heissen so) und ist unmöglich (418 von 2742 Knoten einer
Gebäudedatei ebenso). *Wo die Namen die Unterscheidung nicht tragen, muss sie von aussen
kommen* — und die Gestalt ist das «von aussen», für das niemand gefragt werden muss.
*Was sie nicht kann, und das steht im Befund:* Eine grosse flache Platte auf halber Höhe
trennt sie nicht — Geländesockel und Tiefgaragendecke haben dieselben drei Zahlen. Dort
sagt sie **nicht entscheidbar** (siehe **Die dritte Antwort**), zählt sie in der Rahmung
als Bauwerk und nennt sie beim Namen. *Gelände in der Maske ist teurer als Gelände
daneben:* Auf einer Bodenszene erreichte weisses Rauschen dort den Score 0,72.

**Zugestellt an die Adresse, nicht an den Adressaten** — Eine Sendung erreicht den Ort,
an dem der Empfänger vermutet wird, aber nicht ihn. Der Zustellbeleg ist echt und trotzdem
wertlos: Er belegt den Ort, und gemeint war der Mensch.
*Im Projekt am 06.09.2026, und es ist die genaue Fassung nach zwei ungenauen:* Die Blöcke
für `cloud` und `ui` lagen seit dem 01.09. in deren Repo — auf `main`. Beide Worker
entwickeln auf Feature-Zweigen, die `main` nie zusammenführen. Der UI-Worker hat es selbst
gemessen: *«17 Dateien auf origin/main, 0 auf unserem Entwicklungszweig. Es hat uns nichts
auf eine neue Datei aufmerksam gemacht, weil es für uns keine Datei gab.»*
*Warum es zweimal falsch diagnostiziert wurde:* Beide Seiten massen den falschen
Gegenstand. Wir massen unsere eigene Ablage und schlossen auf den Hinweg; die HomeStation
mass das fremde Repo und schloss auf den Empfänger. **Ein Verzeichnis ist kein Leser.**
*Die Regel daraus:* Ein Zustellbeleg, der eine Datei prüft, misst Ankunft am Ort. Ob
jemand sie sieht, misst nur eine Antwort — was der **Zustellbeleg** von Anfang an
erbeten hatte, und was hier tatsächlich die einzige Auskunft war, die trug.

**Zustellung ist gerichtet** — Dass etwas **hinkommt**, sagt nichts darüber, ob etwas
**zurückkommt**. Ein Weg, der in einer Richtung trägt, ist noch kein Kanal, und ein Beleg
über die eine Richtung belegt nicht die andere.
*Im Projekt am 06.09.2026:* Nach fünfzehn Tagen Stille von `cloud` und `ui` lautete der
Schluss: «Der Weg über ihr Repo ist gemessen und trägt nicht.» Er trug. Die Blöcke waren
seit dem 01.09. dort, und beide Adressaten hatten am **03.09.** auf **alle siebzehn**
geantwortet — ihre Antworten lagen im Orbit-Repo, und nur zwei erreichten je unseres.
*Der Fehler lag auf dem Rückweg, und geprüft worden war der Hinweg.*
*Was die Verwechslung teuer machte:* Auf dem falschen Schluss wurde ein dritter
Zustellweg gebaut, und in den Blöcken stand als Begründung ein Vorwurf, der nicht stimmte.
Der eigene `zustellung.json` belegte immer nur die Hinrichtung — gelesen wurde er, als
belege er beide. Verwandt mit **Abgelegt gegen ausgeliefert**, eine Richtung weiter: Dort
war offen, ob etwas hinausging; hier, ob etwas zurückkam.

**Vorschrift ohne Vergabestelle** — Eine Regel, die eine Ordnung *verlangt*, aber
niemandem sagt, welcher Platz darin frei ist.
*Was dabei geschieht:* Die Arbeit verlagert sich auf den, der zuletzt kommt. Jeder
Einzelne tut das Naheliegende und nimmt eine Zahl, die aus seiner Sicht frei aussieht;
wer als Letzter ankommt, findet den Widerspruch und räumt ihn auf. Der Fehler sieht dabei
wie ein Fehler des Letzten aus, und er ist keiner.
*Im Projekt am 09.09.2026 zweimal an einem Abend:* `tests/test_auftraege.py` verlangt je
Adressat eine **lückenlose Rangreihe von eins an**. Vier Lanes schreiben in dieselbe
Warteschlange, und keine sah die Ränge der anderen. Erst nahm eine fremde Lane einen
belegten Rang, eine Stunde später Rang **und** Laufnummer — beide Male wurde `main` rot.
*Die Abhilfe ist keine strengere Vorschrift, sondern eine Vergabestelle:*
`auftrag.naechste_laufnummer` und `auftrag.naechster_rang` lesen den Bestand und sagen,
was frei ist; `tools/einbau.py` nennt es dort, wo ohnehin gezählt wird. Verwandt mit
**Tote Kante**: Dort ist etwas gebaut und wird nicht gerufen, hier ist etwas verlangt und
wird nicht angeboten.

**Flächenbeherrschte Aufnahme** — Ein Bild, dessen Tiefenkarte zum grossen Teil auf
*einem* Wert liegt: Die Kamera sieht im Wesentlichen eine Fläche senkrecht zur
Blickachse.
*Warum das zählt:* Die Geometrie-QA dieses Projekts ruht auf **Tiefenrängen**. Wo alles
gleich weit weg ist, gibt es keine Ordnung zu vergleichen — eine Rangkorrelation misst
dort nicht die Geometrie, sondern den Schätzer. Die Aufnahme wird dadurch nicht
*ungenauer*, sondern **unmessbar**, und das sieht man ihr nicht an: Es ist ein
vollständiges, plausibles Bild.
*Gemessen wird der Anteil des **ganzen Bildes** auf einer Tiefenebene, nicht die Spanne.*
Ein Bild kann fünf Meter Spanne haben und trotzdem zu vier Fünfteln auf einer Ebene
liegen. Und der Anteil wird nicht an der Geometrie gerechnet — *ein Blick, der halb aus
Himmel besteht, ist nicht dadurch besser, dass die andere Hälfte eine einzige Wand ist.*
*Im Projekt am 09.09.2026* (`docs/INNENANSICHT_2026-09-09.md`): Eine frontale
Innenaufnahme liegt zu 56,9 % bzw. 78,8 % auf einer Ebene, dieselben Räume über Eck zu
0,5 % bzw. 0,6 %. Und ohne übergebene Brennweite — der Runner stellt dann 50 mm — trägt
die Karte des grösseren Raums **einen einzigen Wert**. Verwandt mit **Die dritte
Antwort**: Nicht messbar ist weder bestanden noch durchgefallen.

**Vorprüfung (gegen tragende Messung)** — Eine Messung, die ein Verfahren **widerlegen**
kann, aber nicht **tragen**.
*Der Unterschied ist eine Hausregel dieses Projekts vom 24.08.2026, und sie ist teuer
gelernt:* `kantenanteil`, Variante F und R2 sind alle drei an Blender-Renders und
Nullankern geeicht worden, sahen dort gut aus und sind am erzeugten Bild gefallen.
*Was eine Vorprüfung darf:* ausschliessen. Zeigt die Soll-Karte keine Tiefenordnung, kann
kein Schätzer eine hineinbringen — dieser Schluss gilt.
*Was sie nicht darf:* etwas zusagen. Dass die Soll-Karte Ordnung trägt, sagt über das
erzeugte Bild nichts.
*Warum das Wort nötig ist:* Beide Sorten Messung sehen im Bericht gleich aus — eine
Tabelle mit Zahlen. Wer die eine für die andere hält, baut auf einem Ergebnis, das nur
in eine Richtung gilt.

**Zielzahl, die nur durch Verstecken erreichbar ist** — Eine Zahl, die einen Zustand
beschreiben soll, aber nur dadurch erreicht wird, dass etwas aus dem Blickfeld wandert.
*Sie misst dann nicht mehr die Sache, sondern die Sichtbarkeit der Sache.*
*Der Unterschied zu einer schlicht verfehlten Zahl ist der ganze Punkt:* Eine verfehlte
Zahl sagt etwas Wahres — die Sache ist nicht so weit. Eine nur durch Verstecken
erreichbare sagt etwas Falsches, sobald sie erreicht wird, und niemand merkt es, weil das
Ergebnis richtig aussieht.
*Im Projekt am 09.09.2026:* Für Woche 2 stand als Ziel *«`PLAN.md` unter 800 Zeilen»*.
Nachgemessen: 48 Abschnitte, davon 22 vollständig abgehakt (1205 Zeilen, beweglich), und
110 offene Punkte, verstreut über fast jeden langen Abschnitt. Nach dem Umzug alles
Fertigen bleiben rund 4300 Zeilen. Die 800 wären nur erreichbar gewesen, indem man offene
Punkte von ihren Messungen trennt — dann stünde der Punkt ohne seine Begründung im Plan
und die Begründung ohne ihre Frage im Archiv. *Der Owner hat das Ziel korrigiert statt es
still fallenzulassen:* Die Zahl steht im Plan als **gemessen unerreichbar**, mit den
Zahlen daneben. Denn eine Zielzahl, die einfach verschwindet, sieht aus wie eine, die
erreicht wurde. Verwandt mit **Aus Nichtwissen einen Vorwurf machen** — beide Male ist
das Gemessene und das Behauptete auseinandergefallen; hier zugunsten des eigenen Berichts.

**Deckelzeile** — Drei Zeilen unter der Überschrift eines langen Dokuments, die sagen:
*was entschieden wurde, was gemessen wurde, was offen blieb.* Sie ersetzt das Lesen nicht,
sie ersetzt das **Suchen** — wer wissen will, ob ein Protokoll seine Frage berührt, muss
nicht dreitausend Zeilen überfliegen.
*Warum sie gelesen und nicht erzeugt wird:* Eine Vorlage, die aus Überschriften Sätze
baut, liefert Text, der aussieht wie eine Zusammenfassung und keine ist — und weil er
aussieht wie eine, liest danach niemand mehr nach. Wo eine Sitzung keinen Entscheid trug,
sagt die Zeile das: **Ein Protokoll ohne Entscheid ist ein Bericht, und das darf
dastehen.**
*Im Projekt seit dem 09.09.2026* in allen 23 Sitzungsprotokollen und in jedem Abschnitt
von `docs/PLAN.md` ab 40 Zeilen. `tests/test_plan.py` prüft **Existenz und
Vollständigkeit der drei Felder**, nicht ihren Inhalt — ob ein Satz zutrifft, entscheidet
weiterhin ein Mensch.

**Aus Nichtwissen einen Vorwurf machen** — Ein Werkzeug meldet nicht, was es gemessen
hat, sondern was es daraus über andere schliesst. *Der Unterschied fällt erst auf, wenn
der Schluss falsch war.*
*Im Projekt am 06.09.2026:* `tools/einbau.py` schrieb `NIE GEANTWORTET` neben einen
Adressaten. Gemessen war: «in unserer Ablage liegt keine Ergebnisdatei». Behauptet war:
«dieser Adressat hat nie geantwortet». Am selben Tag fand der Home-PC-Worker **fünfzehn**
Antworten von `cloud` und `ui`, datiert auf den 03.09., in einem Verzeichnis, in das wir
nie sehen — darunter die Antworten auf genau die beiden Aufträge, die nur nach dem Empfang
fragten. Der Vorwurf war zu diesem Zeitpunkt bereits hinausgegangen: Der Owner hatte zwei
Blöcke übergeben, in denen wörtlich stand «Auf keinen davon kam je eine Antwort».
*Die Regel daraus:* Was ein Werkzeug schreibt, muss **ohne Kenntnis fremder Verzeichnisse
wahr bleiben**. «Bei uns liegt keine» ist es; «du hast nicht geantwortet» ist es nicht.
Der Text heisst seither `KEINE ANTWORT IN UNSERER ABLAGE`. Verwandt mit **Die dritte
Antwort**: Nicht messbar ist weder bestanden noch durchgefallen — und *nicht gefunden* ist
weder *nicht vorhanden* noch *nicht geschickt*.

**Abgelehnt (Lauf gegen Frage)** — Derselbe Ergebnisstatus bedeutet Entgegengesetztes,
je nachdem, worauf er antwortet.
*Bei einem **Lauf*** heisst `abgelehnt`: Die Maschine hat nicht gerechnet. Es ist noch
nichts da, der Auftrag zählt zu Recht weiter als unbeantwortet, und irgendwann wird
nachgefragt.
*Bei einer **Frage*** heisst dasselbe Wort: Hier ist die Antwort, und sie lautet nein. Ein
begründetes «machen wir nicht» ist die **vollständige** Antwort — so steht es in jedem
Block, den dieses Projekt hinausgibt: *«Ein 'machen wir nicht' ist eine verwertbare
Antwort, Schweigen ist keine.»*
*Was die Verwechslung kostet:* Die Antwort zählt weiter als offen. Wir fragen nach, was
uns längst beantwortet wurde, und der Adressat sieht seine Antwort ignoriert — bei
Adressaten, die überhaupt zum ersten Mal antworten, der teuerste denkbare Fehler.
*Im Projekt am 06.09.2026:* beim Bau von `tools/antwort.py` beinahe eingebaut; der
Schalter stand schon in der Hilfe. Aufgefallen an einer Probe, die `beantwortet` erwartete
und `gerechnet, nicht beantwortet` bekam. Das Werkzeug weist `abgelehnt` auf eine Frage
jetzt ab und nennt den richtigen Weg. **Der Status beschreibt, ob die Aufgabe erfüllt ist,
nicht ob die Antwort gefällt.**

**Ein Wort, zwei Gegenstände** — Derselbe Begriff bezeichnet im Projekt zwei
verschiedene Dinge. Solange beide selten nebeneinander vorkommen, fällt es nicht auf; wer
dann etwas nach dem Namen sucht oder anlegt, greift irgendwann daneben.
*Im Projekt am 06.09.2026:* «Prompt» hiess bis dahin der Textbaustein, der an den
Bildgenerator geht (`src/aiimaging/prompts.py`, dazu `tests/test_prompts.py` mit 59
Proben). Für den neuen Zustellweg an fremde Worker wurde ein Ordner `auftraege/prompts/`
angelegt — und die zugehörige Probendatei überschrieb die bestehende. *Zehn Minuten, eine
verlorene Datei, und der Fehler steckte nicht im Schreiben, sondern im Namen.*
Zurückgeholt aus der Versionsgeschichte; der Ordner heisst seither `auftraege/bloecke/`,
«Prompt» bleibt dem Bildgenerator. Nicht zu verwechseln mit **Ein Feldname, zwei
Bedeutungen**: Dort trägt ein Feld zwei Gestalten und stürzt beim Lesen ab, hier tragen
zwei Gegenstände einen Namen und kollidieren beim Anlegen.

**Ein Kommentar ist kein Wächter** — Eine Regel, die eine Datei nur *beschreibt*, statt
sie zu erzwingen. Sie sieht aus wie eine Vorkehrung, verlangt aber, dass ein Mensch sie
im richtigen Moment liest und befolgt.
*Woran man sie erkennt:* Der Satz enthält ein «bitte», ein «darum» oder ein «wer X tut,
muss auch Y» — und nichts wird rot, wenn Y ausbleibt.
*Im Projekt am 06.09.2026:* Neben dem Stichtag des **Zustellbelegs** stand seit dem 03.09.
der Hinweis *«wer die Post neu erzeugt, zieht darum dieses Datum mit»*. Er war beim ersten
Mal gelesen, beim zweiten Mal von derselben Hand übergangen worden — die Post ging am
06.09. wieder mit dem Datum vom 03. hinaus. Die Zahl daneben war jedes Mal richtig, weil
sie **gezählt** wurde. Der Stichtag wird seither ebenfalls gerechnet.

**Die Probe prüft ihre eigene Zufälligkeit** — Ein Wächter, der grün ist, weil zwei Dinge
zufällig zusammenfielen, und nicht, weil die geprüfte Regel gilt. Er schlägt dann genau
dann an, wenn der Zufall ausbleibt — also **nicht bei einem Fehler, sondern bei einer
langsamen Maschine**.
*Im Projekt am 06.09.2026:* Eine Probe legte zwei Aufträge an, den alphabetisch späteren
zuerst, und verlangte danach alphabetische Reihenfolge. Sortiert wird aber nach
Erstellzeit, mit der Kennung nur als Gleichstands-Regel. Grün war die Probe also nur,
solange beide Aufträge in **dieselbe Sekunde** fielen. Unter Last schob sich eine
Sekundengrenze dazwischen, der zuerst angelegte stand zu Recht vorn — und die Probe wurde
rot, *weil der Code tat, was sein Docstring verspricht*. Sie konnte Zeit- und
Namenssortierung nie unterscheiden. Verwandt mit **Die Bedingung nicht hergestellt**:
Dort wird die Lage nicht hergestellt, hier wird sie erhofft.

**Abgelegt gegen ausgeliefert** — Zwei Zustände eines Auftrags, die in jeder Liste
gleich aussahen. **Abgelegt** heisst: Die Datei liegt in unserem Repo. **Ausgeliefert**
heisst: Ein Block daraus ist an den Ort gegangen, an den der Adressat sieht.
*Wozu die Unterscheidung:* Zwei unserer drei Adressaten haben unser Repo nicht. Für sie
ist eine abgelegte Datei so unerreichbar wie eine ungeschriebene — und trotzdem steht sie
in jeder Zählung als Rückstand **bei ihnen**. Nach unserem eigenen Satz ist sie dann einer
**bei uns**: *Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei
ihm — er ist einer beim Absender.*
*Im Projekt am 03.09.2026:* Zwei Aufträge an die Oberfläche lagen zwei bzw. einen Tag im
Repo und waren nirgends sonst; der letzte Postlauf war vom 01.09. Gemerkt hat es niemand,
weil es nichts zu merken gab. Seither führt `auftraege/zustellung.json` mit, welche
Kennung wirklich hinausgegangen ist, und der Einbau-Bericht meldet den Unterschied als
erste Zeile — vor allen anderen Zahlen, weil er der einzige Rückstand ist, den wir selbst
sofort beheben können. Nicht zu verwechseln mit dem **Zustellbeleg**: Der sagt, ob
*gelesen* wurde; dieser nur, ob *hinausgegangen* wurde.

**Stale Bytecode nach einer Mutationsprobe** — Eine Falle des Verfahrens selbst, gefunden
am 03.09.2026. Eine Mutationsprobe ändert eine Datei, lässt die Proben laufen und stellt
sie zurück. Ist die Änderung **gleich lang** wie das Original und geschieht die
Rückstellung **in derselben Sekunde**, hält Python den zwischengespeicherten Bytecode für
gültig — er wird an Zeitstempel und Länge erkannt, nicht am Inhalt — und führt weiter die
**mutierte** Fassung aus.
*Was man dann sieht:* eine rote Probe, die im Quelltext nicht mehr rot sein kann, und
Ausgabezeilen aus einer Reihenfolge, die dort nicht mehr steht. *Der Fehler steckt nicht
im Wächter und nicht im Bau, sondern im Werkzeug, mit dem geprüft wird* — die
unangenehmste Sorte, weil beide Seiten korrekt aussehen. Abhilfe: `__pycache__` nach
jeder Mutationsprobe löschen — und die Probe erst glauben, wenn sie das auch überlebt.

**Zustellbeleg** — Die Bitte an einen Adressaten, **den Empfang zu bestätigen**, ohne
inhaltlich zu antworten: ein Satz, mit Datum, mehr nicht.
*Wozu, wenn doch eine Antwort gewünscht ist:* Weil Schweigen zwei ganz verschiedene Dinge
heissen kann. Entweder liegt die Frage quer und braucht Zeit — dann ist Warten richtig.
Oder niemand sieht an die Stelle, an der sie liegt — dann ist es **kein Rückstand beim
Empfänger, sondern einer beim Absender**, und jede weitere Sendung dorthin ist verlorene
Arbeit. Von aussen sehen beide gleich aus.
*Im Projekt am 01.09.2026:* Zwei Adressaten trugen elf Aufträge und hatten **nie**
geantwortet. Der Beleg steht seither im Erzeuger der Auftragsblöcke und nicht in den elf
Dateien — *elf Dateien sind elf Gelegenheiten, ihn bei einer zu vergessen*. Er verschwindet
von selbst, sobald einmal geantwortet wurde: Ein Hinweis, der immer dasteht, wird nicht
mehr gelesen (siehe **Dauerwarnung**).

**Antwortverhalten (eines Adressaten)** — Wie oft jemand auf gestellte Aufträge **selbst
geantwortet** hat, und wann zuletzt. Die Zahl steht neben dem Rückstand, weil dieser eine
andere Frage beantwortet: *Wie viel liegt bei jemandem?* — aber nicht: *Ist dort überhaupt
jemand?*
*Gezählt wird gegen den abgeleiteten Zustand und nicht gegen Ergebnisdateien:* Ein
Weiterleitungsvermerk trägt `status: ok`. Über die Dateien gezählt hätte der Vertrags-Worker
wie ein antwortender Adressat ausgesehen, obwohl beide Vermerke von einem Dritten stammten.

**Rang (eines Auftrags)** — Eine freiwillige ganze Zahl im Auftrag, kleinere zuerst, die
sagt, **was vor was gerechnet wird**. Ohne Rang läuft ein Auftrag nach allen anderen.
*Warum er nötig wurde:* Solange ein Mensch jeden Lauf von Hand startete, entschied er die
Reihenfolge. Sobald ein Zeitgeber je Durchgang **einen** Auftrag nimmt, entscheidet sie die
Sortierung — und die kannte nur den Dateinamen. Damit hätte der Zufall der Benennung
bestimmt, was zuerst gemessen wird.
*Und warum er im Auftrag steht und nicht im ausführenden Skript:* Wer weiss, was zuerst
zählt, ist der, der den Auftrag stellt. Eine Sortierregel im Skript wäre eine
Betriebsentscheidung an der falschen Stelle.
*Seit dem 21.10.2026:* Ränge sind je Adressat eindeutig, dürfen aber **Lücken** haben, wo ein erledigter Auftrag
stand; ein neuer Auftrag kommt hinter den letzten offenen, nie in eine Lücke. Vorher riss jedes Ergebnis eine Lücke,
und eine Prüfung wurde rot.

**Obergrenze (eines Befundes)** — Ein Messaufbau, der einer Sache absichtlich die
**besten denkbaren** Bedingungen gibt, um zu klären, ob sie unter *irgendwelchen*
Bedingungen taugt. Das Ergebnis ist einseitig belastbar: Was hier scheitert, ist erledigt;
was hier gelingt, ist noch nicht bestätigt.
*In diesem Projekt am 27.08.2026 vor einem teuren Auftrag: Bevor die HomeStation GPU-Zeit
auf die Kalibrierung der Paarschwellen ausgibt, wurde hier gefragt, ob die beiden Masse
mit **perfekten** Tiefenkarten überhaupt trennen — 36 Sekunden statt eines Abends. Die
Antwort war für das eine Mass ja und für das andere nein, und das hat den Auftrag
verändert, bevor er ausgeführt wurde.*
*Der Nutzen liegt in der Reihenfolge: Eine Obergrenze kostet fast nichts und kann eine
teure Messung ganz ersparen. Ihre Gefahr liegt darin, sie für das Ergebnis zu halten —
darum trägt sie ihren Vorbehalt im Namen.*

**Ersatzmessung / Ersatzkalibrierung** — Eine Messung, die an die Stelle einer noch
ausstehenden tritt, **ohne sie zu ersetzen**. Sie beantwortet dieselbe Frage unter
leichteren Bedingungen und trägt ihren Abstand zur echten Messung ausdrücklich mit.
*Im Projekt am 01.09.2026:* Die Kalibrierung der Paarschwellen liegt als Auftrag bei der
HomeStation und braucht dort einen echten Tiefenschätzer. Bis sie zurückkommt, wurde
dieselbe Tabelle hier mit **gebauten** Karten gerechnet — als Obergrenze, in acht Kurven,
und der Auftrag blieb offen.
*Die Gefahr ist immer dieselbe:* Eine Ersatzmessung, die niemand mehr als solche liest,
wird zur Antwort. Darum ist sie hier nicht nur im Text als Vorbehalt geführt, sondern im
Ergebnis der Rechnung — siehe **Mitgebrachter Vorbehalt**.

**Mitgebrachter Vorbehalt** — Eine Einschränkung, die man einer Messung **von aussen
mitgibt**, weil sie in den Zahlen selbst nicht steht. Die Wächter einer Auswertung prüfen,
was sie prüfen können — Fallzahl, Streuung, nicht messbare Zeilen. Dass die Eingangsdaten
aus einer Werkstatt und nicht aus dem Betrieb stammen, sieht ihnen keiner an.
*Im Projekt:* `paarschwellen.trennkurve` nimmt `zusatz_vorbehalte` entgegen, stellt sie
**vor** die selbst gerechneten und setzt damit `genuegt_als_kalibrierung` auf falsch. Der
Weg kann eine Auswertung nur strenger machen, nie milder; einen Schalter, der eine
Einschränkung abstellt, gibt es mit Absicht nicht.
*Der Satz dahinter:* **Eine Messung, die ihren eigenen Vorbehalt aufweichen kann, ist
keine.**

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

**Korngrösse (einer Regel)** — Die Frage, **worüber** eine Regel urteilt: über jedes
einzelne Stück oder über die Gruppe, zu der es gehört. Dieselbe Regel mit denselben
Zahlen kann bei der einen Korngrösse zutreffen und bei der anderen nicht.
*Der Fall, an dem es dieses Projekt gelernt hat: Eine Geländeplatte kommt aus dem
Bestandsmodell als **zwanzig** Streifen. Jeder einzelne ist zu schmal, um als Gelände zu
gelten — die Hüllbox über alle zwanzig zusammen dagegen wird zweifelsfrei erkannt
(Grundrissanteil 0,918 statt 0,221). Es war also kein Schwellenproblem: Die Schwelle war
richtig, sie wurde nur auf das falsche Korn angewandt. Wer in so einem Fall die Schwelle
nachzieht, hat sie an genau dieser Datei geeicht — und die Regel wird schlechter, nicht
besser.*

**Familienprüfung (in der Geländeform)** — Knoten, deren Namen dieselben ersten zwei
Segmente tragen, werden als **eine** Familie beurteilt: Erst wird jeder für sich geprüft,
und erst wenn keiner davon als Gelände gilt, urteilt dieselbe Regel noch einmal über die
gemeinsame Hüllbox.
*Sie ist Vorgabe **aus**, und das ist keine Vorsicht, sondern eine Hausregel: Was als
Gelände gilt, bestimmt die Bauwerksmaske, und an der hängt jede Messwertreihe des
Projekts. Eine stillschweigend geänderte Maske macht alle früheren Zahlen unvergleichbar,
ohne dass es auffällt. Die Gegenprobe steht daneben — zwanzig Fassadentafeln teilen sich
ebenfalls einen Namensstamm, und ihre gemeinsame Hüllbox ragt auf, also fängt sie die
Flachheit.*

**Vertauschprobe** — Dasselbe Bild ein zweites Mal messen, aber gegen die **falsche**
Vorlage: das Bild eines fünfgeschossigen Baus gegen die Soll-Tiefenkarte einer 8 × 5 × 3 m
grossen Schachtel. Zwei Bauwerke, die nichts gemein haben ausser dem Standpunkt.
*Sie beantwortet eine Frage, die keine Bestätigung beantworten kann: **Misst die Prüfung
das Bauwerk — oder etwas, das jedes Bild hat?** Am 08.09.2026 bestanden alle zwölf
erzeugten Bilder die Schwelle auch gegen die falsche Karte (0,8279–0,8763). Das war der
Befund, der die Geometrie-Schwelle in ihre Schranken gewiesen hat: Bei viel Boden im Bild
trägt sie den Boden-Himmel-Aufbau, den jedes Architekturbild auf Augenhöhe hat.*

**Stärkeprobe** — Dieselbe Messung noch einmal, aber mit **abgeschwächter Führung**: Die
ControlNet-Stärke wird von 1,00 auf 0,75 und 0,30 gesenkt, alles andere bleibt gleich.
*Bei 0,30 hat das Bild mit dem Modell nachweislich nichts mehr zu tun — die Übereinstimmung
über der Bauwerksmaske liegt bei null. Eine Prüfung, die dort noch besteht, misst nicht
das Bauwerk. Elf von zwölf bestanden.*

**Konditionierungsweg** — **Wie** die Tiefenkarte in das Bildmodell hineinkommt, nicht
**ob**. Ein echter Steuereingang (ControlNet) führt das Bild; dieselbe Karte über den
Bildeingang eingespeist *ersetzt* dagegen nur das Ausgangsbild — die Kette sieht in beiden
Fällen gleich aus und tut etwas völlig anderes.
*Der teuerste Einzelbefund dieses Projekts hängt daran. Der Fehlschlag vom 18.08.2026
(Score 0,359) galt vier Wochen lang als Aussage über die Kette; er war eine Aussage über
den Konditionierungsweg. Das damalige Modell hat gar keinen ControlNet-Eingang, die
Tiefenkarte ging als `image` hinein. Mit einer echten Tiefen-Naht liegt derselbe Wert bei
0,98. **Er stand in keinem der beiden Verdachte, die wir untersucht hatten.***

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

**Grenzstärke** — Die Stärke, bis zu der eine gestörte Vorlage in einer Kalibrierung noch
als *treu* gilt. Sie ist eine **Setzung und keine Messung**: Jemand legt fest, dass eine um
zwei Bildpunkte versetzte Geometrie noch in Ordnung sei und eine um vier nicht mehr. *In
diesem Projekt steht sie darum in jedem Rückgabewert von `trennschaerfe_kurve`
(`grenzstaerke`, voreingestellt 0,2) — nicht damit man sie ändert, sondern damit niemand
sie für ein Naturgesetz hält. Ihre Wahl entscheidet mit über die «beste» Schwelle: Alle
sieben Fälle, die am 26.08.2026 auf echter Geometrie bei Schwelle 0,85 zu Unrecht gesperrt
wurden, liegen bei Stärke 0,2 — also genau auf der gesetzten Grenze.*

**Rasterdublette** — Zwei Zeilen einer Studie, die verschiedene Störungsstärken tragen und
trotzdem **punktgleich dasselbe** Bild erzeugen. Sie entstehen, wenn eine Störung in ganzen
Bildpunkten rechnet: `round(0,2 · k)` und `round(0,3 · k)` ergeben oft dieselbe Zahl. Für
sich harmlos — verheerend, sobald die *Grenzstärke* dazwischen liegt: Dann stehen zwei
Zeilen mit **derselben Messung** auf verschiedenen Seiten der Grenze, und keine Schwelle
der Welt kann sie trennen. Jede zählt zwangsläufig einen Fehler, und der sieht wie eine
Aussage über das Messverfahren aus, wo eine über das Stärkeraster steht. *In diesem Projekt
am 18.08.2026 gefunden, nachdem vier solche Paare bereits in eine veröffentlichte
Auswertung eingegangen waren. `trennschaerfe_kurve` verwirft sie seither — und nennt im
Feld `entdoppelt`, welche und wie viele: Eine stillschweigende Bereinigung wäre nur die
zweite Art, dieselbe Zahl zu erfinden. Bei 400 × 400 Bildpunkten bleibt je Szene noch
**eine** übrig; das Raster war eine Frage der Auflösung.*
*Am 27.08.2026 dieselbe Falle an einer **anderen Achse** gefunden: In der
Obergrenzen-Studie der Paarmasse waren **23 von 33 Fallarten auf vier
Nachkommastellen identisch** zwischen zwei Kameras. Zwei Ursachen — Fälle, deren
Wert durch die Konstruktion festliegt (1,0000, −1,0000, «nicht messbar»), und
rotationssymmetrische Geometrie, die von zwei Seiten gleich aussieht. Die Zeile
«3 Szenen · 2 Kameras» sah nach Streuung aus und war zu zwei Dritteln keine.
**Eine Dublette braucht kein Stärkeraster; sie braucht nur zwei Wege zur selben
Zahl.***

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
*Seit dem 27.08.2026 gibt es dieselben zwei Zahlen ein zweites Mal, für Fälle, die nicht
aus einer Störungsreihe stammen, sondern **von Hand als gut oder schlecht benannt**
wurden: `paarschwellen.trennkurve` (`falsch_bestanden`, `falsch_gesperrt`). Der andere
Name für dieselbe Sache ist Absicht — dort entscheidet kein Stärkeschwellwert darüber,
was «treu» heisst, sondern ein Mensch, und das soll man der Spalte ansehen.*

**Trennkurve (über benannte Fälle)** — Dieselbe Rechnung wie die Trennschärfe-Kurve,
aber über Fälle, deren Etikett *gut* oder *schlecht* jemand vergeben hat, statt es aus der
Stärke einer künstlichen Störung abzuleiten. Sie beantwortet die einzige Frage, die eine
Schwelle rechtfertigen kann: **Was kostet sie an beiden Fehlern?**
*In diesem Projekt `src/aiimaging/paarschwellen.py` und `tools/paarschwellen.py`, gebaut
am 27.08.2026 für die Kalibrierung der beiden Paarschwellen. Ihr wichtigster Teil ist
nicht die Tabelle, sondern das Schweigen: Fehlt eine der beiden Gruppen, ist die Trennung*
**nicht beurteilbar** *und nicht etwa sauber — ohne schlechte Fälle sperrt jede Schwelle
nur richtig, und die Tabelle sähe perfekt aus.*

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

**Fixpunkt eines Masses** — Ein Eingabefall, dessen Messwert **von der Definition des
Masses** feststeht und nicht davon, woran gemessen wurde. Er sieht in einer Tabelle aus wie
ein Beleg, ist aber keiner: Man kann ihn hinschreiben, ohne je gemessen zu haben.
*Beispiele aus der Rangkorrelation ρ:* Ein unverändertes Bild ergibt immer 1,0000; eine
streng monotone Umrechnung ebenfalls (ρ ist rangbasiert und damit massstabsfrei); eine
exakt umgekehrte Rangfolge immer −1,0000; ein konstantes Bild hat keine Rangfolge und ist
**nicht messbar**.
*Warum das eine Falle ist:* Am 01.09.2026 trugen 40 gute Zeilen einer Messreihe nur 18
verschiedene ρ-Werte, weil vier der elf Fallarten Fixpunkte sind — und über acht Zeilen je
Gruppe denselben Wert lieferten. Zuvor war derselbe Befund als *«symmetrische
Kamerapaare»* gedeutet worden: die falsche Erklärung für die richtige Beobachtung.

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

**Nachfragen (Polling)** — Statt auf eine lange Antwort zu warten, holt sich die Seite in kurzen
Abständen den Stand ab: «läuft noch» — «läuft noch» — «fertig». Das hält keine Leitung minutenlang offen,
und die Seite kann zwischendurch zeigen, was gerade geschieht. *Im Projekt:* «Datei laden …» (Entscheid
90): Der Heim-PC nimmt die Datei an, wandelt sie in einem **Hintergrundfaden** um, und der Modell-Knoten
fragt alle 0,8 s unter `GET /knoten/modell-laden` nach — eine IFC kann Minuten brauchen.

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

**Die blinde Wache** — Eine Überwachung, die an der falschen Stelle hinsieht. Sie läuft,
sie meldet, sie kostet nichts — und sie kann nichts sehen.
*Der Fall aus diesem Projekt: Die Fortschrittswache beobachtete den Ausgabeordner
`out/`; geschrieben wird aber in einen Unterordner davon, einen je Kamerastandpunkt. In
fünf Läufen meldete sie als längste Pause jeweils **exakt die Gesamtdauer** — sie hat nie
ein einziges Lebenszeichen bemerkt —, und ihr einziger Alarm war ein Fehlalarm.*
*Woran man sie erkennt: Ihre Meldung ist zu **glatt**. Eine Pause, die genau der Laufzeit
entspricht, ist keine Messung, sondern das Fehlen einer. Dasselbe Erkennungszeichen wie
bei einer Prüfung, die immer besteht.*
*Die Abhilfe ist hier bewusst begrenzt: **eine** Ebene tiefer zählen, nicht beliebig
tief. Eine Wache, die den ganzen Ordnerbaum durchsucht, wird mit jedem Blick teurer —
gerade in einem Ordner, in den gerade geschrieben wird — und dann seltener befragt. Sie
würde ihren eigenen Zweck untergraben.*

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

**Nullanker** — Ein zweiter Durchgang derselben Messung, bei dem das Bild durch
**weisses Rauschen** ersetzt wird — also durch reinen Zufall, in dem nichts abgebildet
ist. Die Maske und alle übrigen Bedingungen bleiben gleich.
*Wozu:* Er sagt, wieviel von einer Zahl auch ohne Bauwerk herausgekommen wäre. Ein
Messwert von 0,4 klingt nach Übereinstimmung — steht daneben ein Nullanker von 0,38, war
fast alles davon die Eigenart des Verfahrens und nicht das Bauwerk. Bei einem
Tiefenschätzer sind in diesem Projekt bis zu **95,75 %** eines Werts allein aus seiner
Vorliebe für bestimmte Bildstellen erklärbar gewesen (sein *Ortsfeld*).
*Wo im Projekt:* in jedem QA-Auftrag an die HomeStation, und als Rückgabepunkt in
`auf-20260909-90`. **Ohne Nullanker ist eine Zahl eine Zahl ohne Bezug.**

**Startwertstreuung** — Bildmodelle beginnen jedes Bild bei einem Zufallsrauschen; welches
Rauschen es ist, legt der **Startwert** (engl. *seed*) fest. Derselbe Auftrag mit einem
anderen Startwert ergibt ein anderes Bild. Die Startwertstreuung ist, wie weit die
Messwerte allein dadurch auseinandergehen.
*Warum sie hier ständig auftaucht:* In dieser Kette beträgt sie **0,2269** und ist damit
grösser als jeder Einfluss, den irgendeine Einstellung je gezeigt hat. Ein Vergleich
zweier Einstellungen mit je einem Bild misst darum den Zufall und nicht die Einstellung —
darum verlangen die Aufträge dieses Projekts **drei Startwerte** (0, 1, 2) je Fall.

**Fester Startwert (einer Serie)** — Derselbe Startwert für alle Varianten einer Serie,
damit sie sich nur in dem unterscheiden, was absichtlich geändert wurde (Stimmung,
Prompt). Ohne ihn zog der Heim-PC je Kamera drei Startwerte und behielt den «besten» —
Morgen- und Abendbild konnten so zwei verschiedene Würfe sein (Demolauf Nr. 84).
*Wo im Projekt:* `vis.seed` im Auftrag; das Ergebnis meldet ihn je Kamera als `seed`.

**Blender-Grundlage (eines Renderings)** — Das, was Blender für ein Bild rechnet, bevor
ein Bildmodell daran arbeitet: Kamera, Geometrie und die Bilddurchgänge (Schönbild,
Tiefe, Material-Kennung). Owner-Grundsatz Nr. 85: **ein Rendering = eine Grundlage,
daraus mehrere KI-Varianten.** Die Grundlage wird einmal gerechnet, unter einer Kennung
(`gl-` und 16 Zeichen) abgelegt und für jede Variante wiederverwendet — keine neue
Kamera, kein neuer Blender-Lauf.
*Wo im Projekt:* `abholer.lege_grundlage_ab`/`lies_grundlage`, Ablage
`<Ausgabeordner>/_grundlagen/`; im Auftrag `vis.grundlage`, im Ergebnis
`grundlage {id, wiederverwendet}`. Passt eine Grundlage nicht (andere Auflösung, Samples
oder Kameras), lehnt der Heim-PC laut ab, statt still neu zu rechnen.

**Deckungsgleiche Varianten** — Bilder derselben Grundlage, die sich Pixel für Pixel
überlagern lassen: gleicher Standpunkt, gleiche Geometrie, nur Licht und Stimmung
anders. Für einen Wettbewerb sind nur solche Varianten vergleichbar. Seit dem 21.10.2026 heisst
«deckungsgleich» zusätzlich: die **Kanten-IoU** des KI-Bilds gegen die Grundlage liegt über einer Schwelle;
darunter steht «gleiche Grundlage, Form weicht ab». Die Schwelle war zuerst 0,30 (gesetzt, nicht gemessen) und ist seit
Auftrag 317 **0,10**: Ein Bild, das die Form hielt und nur Fenster und Fugen dazumalte, traf 0,20, ein anderer Bau 0,03.
*Nachgeführt 22.10.2026:* Seit den Messungen 337 und 339 ist die Schwelle **0,25**, und «gleiche Form» heisst auch «gleiche
Fensterteilung». Bilder ohne Bildeingang, die die Fenster verloren oder ein anderes Haus malten, lagen bei 0,14 bis 0,22,
Bilder vom Grundbild aus bei 0,29 bis 0,48. Liegt ein Bild darunter, steht im Ergebnis der Satz «FORM WEICHT VOM GRUNDBILD AB».

**Nur Grundlage («nur Cycles»)** — Ein Auftrag ohne KI-Schritt: geliefert wird das rohe
Blender-Bild (Weissmodell) mit seinen Bilddurchgängen, zur Kontrolle vor dem teuren
Bildmodell (Nr. 81). Im Vertrag ist das `vis.skip: true`. Vom 26.08. bis 20.10.2026 las
der Heim-PC das als «gar nichts rechnen» — das Häkchen bekam darum kein Bild (Nr. 83).

**Variante ohne Hochladen** — Eine Variante (ein neues KI-Bild auf einer schon gerechneten
Grundlage) braucht kein Blender und darum auch kein neu geschicktes Modell. Seit dem 20.10.2026
nimmt der Heim-PC eine solche Bestellung ohne Modelldatei an und holt das Modell aus dem
Auftrag, der die Grundlage gelegt hat (`knotenweg.modell_der_grundlage`). Fehlt die Grundlage
auf diesem Rechner, kommt sofort ein Satz statt Warten. **Seit dem 21.10.2026 auch auf dem
zweiten Weg:** Kam die Bestellung nicht über die Visbox-Tür, sondern über die Brücke, liess der
Heim-PC sie mit leerem Geometriepfad liegen («ohne geometry.path»), und die Variante rechnete nie.
Jetzt nimmt er sie mit gültiger Grundlage an, sucht das Modell beim Auftrag der Grundlage und
rechnet notfalls aus der abgelegten Grundlage allein (`bruecke.lies_auftrag`,
`abholer.verarbeiter`). Ohne Grundlage bleibt der Satz.

**Endgültiger Mangel** — Ein Fehler in einer Bestellung, den kein Warten heilt, weil er in
der Bestellung selbst steht — etwa «Güte Vorschau» zusammen mit «nur Grundlage», was sich
widerspricht. Ein solcher Auftrag endet seit dem 20.10.2026 sofort mit Fehler und Satz.
Andere Mängel (etwa eine fehlende Freigabe) lassen den Auftrag weiter mit Grund warten.

**Kantenrauschen (einer Tiefenkarte)** — Einzelne Bildpunkte genau am Umriss eines Körpers,
die beim Rechnen einmal knapp «getroffen» und einmal knapp «verfehlt» werden. Zwei sonst
gleiche Ansichten unterscheiden sich darum oft in einer Handvoll Randpunkten. Die Erkennung
der Zwillingsansicht lässt seit dem 20.10.2026 höchstens zwei von hunderttausend Punkten
Abweichung zu, und nur am Umriss (Befund am Quader: 3 von 1,6 Millionen).

**Einzelinstanz (einer App)** — Eine App läuft nur einmal: Wer sie ein zweites Mal startet,
bekommt die laufende nach vorn statt einer zweiten Kopie mit eigenem Fenster. Seit Visbox 0.2.10
am Mac (`Einzelstart.swift`); Anlass waren zwei, dann drei Fenster nach dem Aktualisieren.

**Pose (einer Kamera)** — Wo eine Kamera steht, wohin sie blickt und wie weit ihr
Bildwinkel ist (`position`, `target`, `fov`, dazu die Hochachse). Das Ergebnis meldet
die **gerechnete** Pose je Kamera, auch bei der Auto-Kamera — so kann ein gelungener
Standpunkt als feste Kamera weiterleben (Nr. 68).

**Fortschritt (eines Renderauftrags)** — Was während eines Laufs am Auftrag steht: in welchem
Schritt er ist (Blender, Bildmodell, Prüfung), bei welcher Kamera von wie vielen, wie weit er
insgesamt ist (0 bis 1), das jüngste Vorschaubild und eine geschätzte Restzeit. Im Vertrag
heisst das Feld `progress`. Der Anteil der drei Schritte an einer Kamera ist eine feste
Annahme (0,2 / 0,7 / 0,1), keine Messung — er dient nur der Anzeige. Geschrieben vom Heim-PC
(`abholer._Fortschritt`) seit dem 20.10.2026. Nach einem Abbruch steht die Phase
«abgebrochen» mit dem erreichten Anteil da, damit der Auftrag nicht aussieht, als liefe er
noch.

**Restzeit (geschätzt)** — Wie lange ein Lauf voraussichtlich noch braucht, in ganzen Sekunden.
Sie fehlt, bis die erste Kamera fertig gerechnet ist, denn vorher gibt es nichts, woraus man
schätzen könnte; danach ist sie die mittlere Dauer der fertigen Kameras mal die verbleibenden,
abzüglich der schon gelaufenen Zeit der aktuellen Kamera.

**Teilbild (abgebrochen)** — Das letzte fertige Zwischenbild eines Auftrags, den jemand
mitten im Lauf abgebrochen hat: das KI-Bild der letzten fertigen Kamera, sonst ihr rohes
Blender-Bild. Es trägt **keine** Gütewerte, weil die Prüfung nicht gelaufen ist, und
steht nur bei einem abgebrochenen Auftrag (Vertragsfeld `teilbild`). Sein Name nennt die
Kamera, zu der **das Bild** gehört — nicht die, bei der der Lauf gerade stand (seit der
Geräteprobe vom 20.10.2026).

**Zwischenbild** — Das Bild der zuletzt fertig gerechneten Kamera eines Auftrags, der noch
läuft (Vertragsfeld `progress.vorschau`). Der Render-Knoten zeigt es hinter Text und Balken des
Fortschritts; ein Klick zeigt es gross. Es ist noch nicht geprüft und darum kein Ergebnis.

**Zeilenregister (Render-Knoten)** — Die Liste, die für jede Zeile im Render-Knoten festhält,
wie hoch sie sein darf (in Bildpunkten), einmal in Ruhe und einmal während eines Laufs. Aus ihr
wird die Höhe des Knotens berechnet; eine Probe verlangt, dass jede gezeichnete Zeile im
Register steht und umgekehrt. Wer eine Zeile hinzufügt, ohne das Register nachzuführen, schnitte
sonst still Inhalt ab. Für den Schalter «Güte» wurde darum keine neue Zeile angelegt.

**Fokusring** — Die farbige Umrandung, die zeigt, welches Bedienelement gerade die Tastatur
hat (etwa das Textfeld, in das man tippt). Sie ist für alle wichtig, die ohne Maus arbeiten,
und darf darum nie ganz fehlen. In der Knotenansicht wurde sie ausserhalb der Felder gezeichnet
und vom Knoten abgeschnitten — es blieben nur ihre runden Ecken stehen. Seit dem 20.10.2026
färbt ein Feld im Knoten stattdessen seinen eigenen Rand ein.

**Feste Bildbox (Einpassen)** — Ein Rahmen, dessen Grösse vorher feststeht, und ein Bild, das
sich darin einpasst, ohne verzerrt zu werden (im Code `object-fit: contain`). Das Gegenteil ist
ein Rahmen, der sich nach dem Bild richtet. Beim Zoomen der Knotenansicht rechnete der Browser
diesen zweiten Rahmen bei jedem Schritt etwas anders, und das Bild sprang; die feste Box springt
nicht. *In diesem Projekt: das Hauptbild des Render-Knotens.*

**Kooperativer Abbruch** — Ein Abbruch, der nicht hart eingreift, sondern nur einen Vermerk
setzt («abgebrochen»), den der Rechnende selbst liest und dann aufhört. Der Heim-PC sieht
zwischen zwei Schritten nach; ein Schritt, der schon läuft (Blender oder das Bildmodell),
wird zu Ende gerechnet. Vorteil: nichts bleibt halb geschrieben zurück. Preis: Der Abbruch
greift erst beim nächsten Übergang.

**Beweisgang** — Ein Durchlauf, dessen Ergebnis **Bilder** sind und nicht Zahlen. Er misst
nichts Neues; er macht sichtbar, was die Software an jeder Station tatsächlich tut.
*Abgrenzung zur Messung:* Eine Messung beantwortet eine offene Frage. Ein Beweisgang
beantwortet die Frage, ob das Beschriebene überhaupt läuft — und er beantwortet sie so,
dass man es ansehen kann, statt es zu glauben.
*Die zwei Regeln, die ihn tragen:* Erstens **keine Montage** — jede Station bleibt ein
eigenes Bild, denn eine Collage entscheidet vorweg, was verglichen wird. Zweitens **die
misslungenen gehören dazu**; ein Beweisgang, aus dem die Fehlschläge herausfallen, beweist
die Auswahl.
*Wo im Projekt:* `tools/beweis/`, gefahren von `tools/beweise_fahren.py`, und als Auftrag
`auf-20260909-90` an die HomeStation für den Teil, der hier nicht laufen kann.

**Kontrollbild (überlagerte Maske)** — Das erzeugte Bild mit der Umrisslinie der
Bauwerksmaske darübergelegt.
*Wozu:* Eine Zahl sagt, wie gut Bild und Geometrie zusammenpassen. Das Kontrollbild sagt,
**wo** sie es nicht tun — ob das Bauwerk um zwei Pixel verrutscht ist oder ob im ganzen
oberen Bilddrittel etwas steht, das in der Geometrie nicht vorkommt. Diese beiden Fälle
können dieselbe Zahl ergeben.
*Wo im Projekt:* `aiimaging.bildschreiben.schreibe_kontrollbild`, und als Station S6 im
Beweisgang.

**Zwei Tore statt einer Kennzahl** — Zwei getrennte Prüfungen, die beide bestanden sein
müssen, statt einer einzigen Zahl, die beide verrechnet.
*Wozu:* Die alte Prüfung stellte zwei Fragen auf einmal — *folgt das Bild dem Modell
überhaupt* und *folgt es genau diesem Modell*. Sie zog aus beiden Antworten eine
Durchschnittszahl, und damit konnte ein sehr guter Wert der einen Frage einen sehr
schlechten der anderen verdecken. Gemessen: Elf von zwölf absichtlich erzeugten
Müllbildern kamen so durch. Werden die zwei Fragen einzeln gestellt und beide verlangt,
kommt keines mehr durch. *Eine Kennzahl, die zwei Fragen zu einer verrechnet, beantwortet
keine von beiden.*
*Wo im Projekt:* `aiimaging.geometrie_qa.zwei_tore`, an KosmoOrbit ausgeliefert als
Vertragsfeld `geometry_gates` in `aiimaging.kosmo_szene`.

**Rauschband** — Der Wertebereich, den eine Messgrösse annimmt, wenn nachweislich *nichts*
zu messen ist.
*Wozu:* Eine Schwelle braucht einen Boden. Erzeugt man absichtlich Bilder, die der
Geometrie nicht folgen, und misst sie trotzdem, streut die Zahl um null herum — im Projekt
zwischen −0,047 und +0,055. Alles innerhalb dieses Bandes ist ununterscheidbar von Zufall.
Eine Schwelle darunter wäre wertlos.
*Wo im Projekt:* Begründung von `SCHWELLE_FOLGT` in `aiimaging.geometrie_qa`; gemessen in
`auf-20260909-92`.

**Fehlalarm gegen Durchlasser** — Die zwei Arten, auf die ein Riegel danebenliegen kann:
Er weist etwas Gutes ab (Fehlalarm), oder er lässt etwas Schlechtes durch (Durchlasser).
*Wozu:* Sie sind nicht gleich schlimm. Ein Fehlalarm ist sichtbar — jemand wundert sich
und schaut nach. Ein Durchlasser ist unsichtbar; er sieht aus wie ein Erfolg, und niemand
sucht danach. Wer eine Schwelle setzt, entscheidet damit, welchen der beiden Fehler er
lieber macht. Im Projekt gilt: lieber Fehlalarm.
*Wo im Projekt:* Die Schwelle von Tor A weist ein brauchbares Bild von zwölf ab — das ist
festgehalten, nicht wegkalibriert.

**Ein gemeldeter Mangel, der in der Naht abgefangen wird** — Ein Fehler in der Bibliothek,
den die Schicht darüber zusätzlich abfängt, statt sich auf die Reparatur zu verlassen.
*Wozu:* Die Reparatur kann später wieder herausfallen — bei einem Umbau, einem
Zusammenführen, einer Rücknahme. Prüft die äussere Schicht selbst nach, statt der inneren
zu glauben, hält sie auch dann. Der Preis ist eine doppelte Rechnung; der Gewinn ist, dass
zwei Fehler gleichzeitig passieren müssten.
*Wo im Projekt:* `aiimaging.kosmo_szene.als_zwei_tore_block` rechnet die Gegenprobe selbst
nach, obwohl `zwei_tore` sie seit dem 18.09.2026 richtig meldet.

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

**Instanzen (in einer glb, `EXT_mesh_gpu_instancing`)** — Ein Bauteil, das oft gleich vorkommt
(etwa ein Stein einer Mauer), steht nur **einmal** als Form in der Datei; dazu kommt eine Liste,
wo es überall liegt, wie es gedreht und wie gross es ist. Die Datei bleibt so klein, und die
Grafikkarte zeichnet alle Lagen auf einmal. *Im Projekt seit dem 21.10.2026:* Blender 5.2 und
die 3D-Vorschau lesen solche Dateien; die Hüllbox des Heim-PC (`glbbox`) zählt seither alle Lagen
mit, statt nur den einen Stein zu sehen.

**Ausrollen (von Instanzen)** — Was Blender beim Einlesen einer glb mit Instanzen tut: Aus jeder Lage des
einen Steins wird ein eigenes Objekt, alle teilen sich dieselbe Form (ein *geteiltes Mesh*). Die Datei bleibt klein,
in Blender aber stehen dann zwanzigtausend Objekte. *Im Projekt:* an der Steine-Probe gemessen (auf-20261021-316) —
19 600 Objekte, rund 31 s Blender und 2,4 GB je Kamera.

**Geteiltes Mesh** — Mehrere Objekte zeigen auf dieselbe Form, wie mehrere Kopien eines Bauteils, die alle denselben
Plan benutzen. Wer am Plan etwas ändert, ändert es an allen Kopien. *Im Projekt der Grund für die verketteten
Material-Namen:* Die Kennung wurde am Plan getauscht, und die nächste Kopie las schon den getauschten Namen. Seither wird
zuerst geplant und erst dann getauscht (`aiimaging.material_id`).

**Kennfarbe (im Material-ID-Pass)** — Die Farbe, an der man im Material-ID-Bild ein Material erkennt; dazu gehört ein
Name in der Tabelle des Laufs. Jede Kennfarbe darf nur einmal vorkommen, sonst lässt sich nicht mehr sagen, welches
Material ein Bildpunkt zeigt. *Im Projekt:* seit dem 21.10.2026 überspringt die Planung eine schon vergebene Farbe.

**Rolle am Knoten (`extras.role`)** — Ein Zusatzfeld an einem Teil der Modelldatei, das sagt, was dieses Teil *ist*,
unabhängig von seinem Namen: `"existing"` für Bestand, `"ground"` für Boden oder Gelände. *Wozu:* Namen tragen das
nicht verlässlich — «boden» kann ein Geschossboden sein. Die Rolle sagt es eindeutig. *Im Projekt:* gelesen von
`kosmo_szene.bestand_in_glb` und `kosmo_szene.gelaende_in_glb`; ein Teil mit Rolle `ground` zählt nicht zum Bauwerk.
Im Befund heisst die Herkunft dann `gelaende_quelle: "name+rolle"` — gebaut wie `"name+form"`: vorn steht immer die
Namensregel, dahinter, was zusätzlich griff (seit Auftrag 318 angeglichen; vorher hiess es mit Rolle nur `"rolle"`).

**Fassungszeile (in `visbox_status`)** — Die Zeile mit der Nummer der laufenden Mac-App (etwa 0.3.21), wie sie in
ihrer Info-Datei steht. Seit dem 21.10.2026 nennt die Statusantwort an Claude sie in einer
eigenen Zeile, damit im Gespräch klar ist, welche App antwortet.

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

**Accessor (Zugriffsbeschreibung)** — In einer glb-Datei die kleine Tabelle, die
beschreibt, *wie* eine Zahlenreihe im Geometrieblock zu lesen ist: wie viele Werte, von
welchem Typ, ab welcher Stelle. Für Eckpunkte verlangt die Norm zusätzlich, dass jeder
solche Eintrag **den kleinsten und den grössten vorkommenden Wert mitführt**.

*Diese Pflicht ist der Grund, warum die Hüllbox jedes Bauteils schon im beschreibenden
Teil der Datei steht und die Dreiecke selbst nie gelesen werden müssen. Eine Bestandsdatei
von 25 Megabyte wird so in acht Hundertstelsekunden ausgemessen, statt in vierzig Sekunden
Blender-Zeit (`src/aiimaging/glbbox.py`). An derselben Datei nachgezählt: alle 4771
Einträge halten die Pflicht — und wenn einer sie nicht hielte, wird die Auskunft
verweigert statt eine zu kleine Box gemeldet.*

**Quaternion** — Eine Schreibweise für eine Drehung im Raum, aus vier Zahlen statt aus
drei Winkeln. Der Vorteil gegenüber Winkeln: Es gibt keine Stellungen, in denen zwei
Drehachsen zusammenfallen und eine Bewegungsrichtung verlorengeht.
*Kommt hier nur an einer Stelle vor: Ein Knoten in einer glb-Datei kann seine Lage
entweder als fertige Zahlentafel angeben oder zerlegt in Verschiebung, Drehung und
Grössenänderung — und die Drehung steht dann als Quaternion da
(`_knotenmatrix` in `src/aiimaging/glbbox.py`).*

**Bounding Box (Hüllbox)** — Der kleinste achsparallele Quader, der ein Objekt
umschliesst. Nützlich für schnelle Grössen- und Lageabschätzungen, etwa zur automatischen
Kamerasetzung.
*Sechs Zahlen statt einer Million Dreiecke — das ist der Grund, warum der Torwächter
(`src/aiimaging/torwaechter.py`) einen Massstabsfehler erkennt, bevor eine
Grafikkartenstunde verbrannt ist. Die Kameraableitung
(`src/aiimaging/kameras.py`) arbeitet aus demselben Grund darauf: Ob ein Gebäude ins Bild
passt, entscheidet sich an den **acht Ecken** der Hüllbox, nicht an seiner Geometrie.*

**Augenhöhe (einer Kamera)** — Wie hoch das Objektiv über dem Boden steht, auf dem die Fotografin steht — nicht über
irgendeinem Nullpunkt. Ein Architekturbild «aus Augenhöhe» zeigt das Haus so, wie man es beim Hingehen sieht.
*Im Projekt:* die Auto-Kameras des Vis-Werkzeugs setzen den Standpunkt «Eingang» 1,6 m über den Boden am Standpunkt
(`AUGENHOEHE_MM` in `derive/kamera.ts`), der Heim-PC seine Richtungskameras 1,70 m über den Geländestand
(`kameras.AUGENHOEHE_M`). Eine Prüfung meldet, wenn «Eingang» ausserhalb 1,5–2,0 m liegt; seit 22.10.2026 misst sie über
dem Boden des Standpunkts (`bodenM`), vorher über dem Nullpunkt — daher die fünf Meldungen «Augenhoehe 0.15 m» vom 16.10.

**Bodenbezug (Referenzpunkt der Augenhöhe)** — Die Fläche, von der aus eine Höhe gemessen wird. Vier Möglichkeiten
tragen im Projekt eigene Namen: das **Gelände an der Kamera** (verlässlich), die **Oberkante des fertigen Fussbodens**
im Erdgeschoss, kurz OKFF (verlässlich), die **Unterkante der Hüllbox**, also der tiefste Punkt irgendeines Bauteils
(unverlässlich: bei einer Bodenplatte 40 cm zu tief, bei einem Keller eine Geschosshöhe), und der **Weltnull**, der
Ursprung der Koordinaten (unverlässlich, er kann irgendwo liegen). *Im Projekt:* `CameraSpec.referenzpunkt` im Vertrag
(`terrain_an_kamera`, `okff`, `huellbox_unterkante`, `weltnull`); «Eingang» nennt seit 22.10.2026 dazu die Höhe selbst
(`bodenM`). *Eine Höhe ohne ihren Nullpunkt ist keine Höhe.*

**Geländefläche und Schürze** — Das Gelände als Fläche mit Höhenpunkten (statt als einzelne Profillinie); die
**Schürze** ist der senkrechte Rand, der von der Fläche nach unten reicht, damit das Gelände im Schnitt und im Bild als
Körper wirkt — nach Vorgabe 1 m unter den tiefsten Geländepunkt. *Im Projekt:* `Gelaendeflaeche` im Datenmodell, seit
15.10.2026. Bis 22.10.2026 zählten Fläche und Schürze für die Auto-Kamera als Teil des Gebäudes: Sie schoben den
Standpunkt «Eingang» um die Breite des Grundstücks zurück, und die Schürzen-Unterkante wurde zum tiefsten Punkt. Jetzt
ist das Gelände nur noch der Boden unter dem Standpunkt, nicht mehr Teil der Box.

**Gelände am Standpunkt (gemessen)** — Die Höhe der Geländefläche genau unter der Kamera, abgelesen an der Fläche selbst
(an den Dreiecken, aus denen sie besteht) statt angenommen oder von Hand eingetragen. *Wozu:* Ob eine Kamera auf
Augenhöhe steht, entscheidet sich an diesem Boden. Ohne ihn misst Visbox über dem tiefsten Punkt des Hauses — beim
Demohaus der Unterkante der Bodenplatte, 38 cm unter dem Gelände —, und eine Kamera 1,32 m über dem Gelände hiess «1,70 m,
zu hoch». *Im Projekt:* `kameras.gelaende_hoehe_am_punkt`, gemessen im Blender-Lauf an den Objekten, die als Gelände
erkannt sind (Name, Form oder Rolle «ground»), Feld `gelaende_am_standpunkt_z` im Kamerabericht; die Augenhöhen-Prüfung
stützt ihr Urteil darauf (Bezug `terrain_an_kamera`). Gestellt wird die Kamera dadurch nicht anders — nur ehrlich
berichtet (Ergebnis 341, Protokoll 74 §260). *Gemessen heisst hier: abgelesen am Modell; eine eingetippte Zahl heisst
«gesetzt» (Owner-Entscheid 22.09.2026).*

**Gelände in der Nähe** — Die Höhe des nächsten Rands der Geländefläche, wenn die Fläche nicht bis unter die Kamera
reicht — zusammen mit dem Abstand dorthin. *Wozu:* Am Demohaus reicht das modellierte Gelände nur 8 m über das Haus
hinaus, die Kameras stehen 25–35 m davor. Ohne diese Zahl fiel die Augenhöhen-Prüfung auf die Unterkante der Bodenplatte
zurück, 38 cm zu tief, und kehrte ihre Urteile um. Sie ist **nicht** das Gelände am Standpunkt und heisst darum ausdrücklich
anders; der Satz nennt den Abstand. *Im Projekt:* `kameras.gelaende_naechster_punkt`, im Kamerabericht
`gelaende_nahe_z` und `gelaende_nahe_abstand_m`, Bezug `gelaende_in_der_naehe` — gilt nur bis 50 m Abstand (gesetzt) und
nur anstelle der Hüllbox-Unterkante (Ergebnis 343, Protokoll 74 §262).

**Reihenfolge der Bezüge (Augenhöhe)** — Welcher Boden für das Urteil «augenhoch» zählt, wenn mehrere in Frage kommen: der
erste vorhandene in einer festen Folge — Gelände am Standpunkt (gemessen), dann der Bezug, den die Bestellung selbst nennt
(`referenzpunkt`, etwa OK EG), dann das Gelände in der Nähe, zuletzt die Unterkante der Hüllbox. *Wozu:* Eine Höhe ist nur so
gut wie ihr Nullpunkt; die Folge stellt den verlässlichsten zuerst und sagt im Satz, welcher gegriffen hat. *Im Projekt:*
`kameras.BEZUGSFOLGE_AUGENHOEHE`, `kameras.augenhoehe_befund` (seit Ergebnis 343). Ohne eingetragene Erdgeschosskote gilt
OK EG = Weltnull, und der Satz sagt das.

**Warnung des ganzen Satzes (gegen Warnung je Kamera)** — Die Kamerarechnung liefert Warnungen auf zwei Ebenen: solche,
die eine einzelne Kamera betreffen («sSE: das Bauwerk füllt nur 17 % des Bildes»), und solche, die für alle Kameras eines
Auftrags gelten («der Geländestand ist nicht feststellbar»). *Wozu die Unterscheidung:* Wer nur die erste Ebene
weiterreicht, verliert die zweite still — genau so kam «GELAENDESTAND NICHT FESTSTELLBAR» nie im Bericht an.
*Im Projekt:* `kameras.satzwarnungen`; der Blender-Lauf hängt sie seit Ergebnis 341 an die Warnungen jeder Kamera.

**Doppelter Prompt-Teil** — Ein Stück Text, das nach dem Zusammensetzen zweimal im Prompt steht, weil der Besteller es
schrieb und Visbox denselben Teil mit seinem eigenen Satz noch einmal anfügt («evening mood, evening mood, warm low
sunlight …»). *Wozu vermeiden:* Das Bildmodell gewichtet Wiederholtes stärker; ein doppelter Teil ist eine stille
Verschiebung der Bestellung. *Im Projekt:* `stimmung.ohne_teile_des_satzes` nimmt die durch Komma getrennten Teile heraus,
die wörtlich im angefügten Stimmungssatz stehen, und vermerkt sie (`prompt_zusaetze[].doppelt_herausgenommen`); alles
andere bleibt Wort für Wort (Ergebnis 342).

**Bildkegel** — Der Raum, den eine Kamera sieht: von ihrem Standpunkt aus eine Pyramide, die sich in Blickrichtung
öffnet, waagrecht um den Bildwinkel, senkrecht um den kleineren Winkel, der aus dem Seitenverhältnis folgt (bei 55°
waagrecht und einem Bild 16:10 sind es 36° senkrecht). Was ganz im Bild sein soll, muss ganz in dieser Pyramide liegen.
*Im Projekt:* Ob das Haus ganz im Bild ist, entscheidet sich an den acht Ecken seiner Hüllbox — liegen sie alle im
Bildkegel, ist kein Teil angeschnitten. Die Messung 341 zeigte am Standpunkt «Eingang» Ecken bis 138 % der halben
Bildhöhe, also First und Seiten ausserhalb.

**Abstand aus Bildwinkel (mit Rand)** — Wie weit eine Kamera von einem Haus wegstehen muss, damit es ganz ins Bild
passt: halbe Hausbreite geteilt durch den Tangens des halben waagrechten Bildwinkels — und ebenso für die Höhe über und
unter dem Auge mit dem senkrechten Winkel; der grössere Wert gilt. Der **Rand** (hier 1,15) streckt das knappe Mass, damit
das Haus nicht am Bildrand klebt und auch ein etwas breiteres Bildformat es nicht anschneidet. *Im Projekt:* seit
23.10.2026 die Regel für den Standpunkt «Eingang» (`eingangAbstandMm` im Vis-Werkzeug); am Demohaus trägt die Höhe bis
zum First (24,9 m), nicht die Breite (17,5 m). Vorher stand die Kamera 0,8 × die längere Hausseite vor dem Haus, 12,6 m.

**Up-Achse** — Vereinbarung darüber, welche Achse „oben" bedeutet. IFC und Blender
verwenden Z, glTF verwendet Y. Wird die Umrechnung vergessen, liegt das Gebäude auf der
Seite.

**Georeferenzierung** — Verortung eines Modells in einem Landeskoordinatensystem
(z. B. LV95). Führt zu sehr grossen Zahlenwerten und damit zu Genauigkeitsproblemen —
siehe *Float*. In einer IFC steht sie an zwei Stellen: als Breite/Länge/Höhe an der Parzelle
und als Umrechnung auf Landeskoordinaten (`IfcMapConversion`; in IFC2X3 als Eigenschaftssatz).
*Beim **Neutralisieren** werden beide entfernt. Liegen aber die Koordinaten der Geometrie selbst
in Landeskoordinaten, verrät schon die Geometrie die Lage — darum schiebt das Werkzeug das Modell
dann an einen lokalen Ursprung (siehe dort).*

**Landeskoordinaten** — Die Koordinaten der amtlichen Landesvermessung: In der Schweiz (LV95)
liegt jeder Punkt rund 2 600 000 m östlich und 1 200 000 m nördlich eines festen Bezugspunkts.
Viele Schweizer Wettbewerbs- und Situationsmodelle werden so geliefert, damit Pläne verschiedener
Büros zusammenpassen. Zwei Folgen für dieses Projekt: Die Zahlen **verraten den Ort**, und sie
sind für Grafikprogramme zu gross — mit rund sieben brauchbaren Stellen (siehe *float32*) bleibt
bei Millionen nur noch Dezimeter-Genauigkeit, Kameras und Gelände rechnen weit draussen.

**Lokaler Ursprung (Modell an den Ursprung schieben)** — Das ganze Modell um einen festen Betrag
verschieben, so dass es um den Nullpunkt liegt statt Millionen Meter davon entfernt; die Form
bleibt unverändert. *In diesem Projekt beim Neutralisieren (`--ursprung`, Vorgabe an,
24.10.2026): Der Betrag ist die Mitte der Bauteile, auf 100 m gerundet, abgezogen an der
obersten Platzierung, damit alles — Parzelle, Gelände, jedes Bauteil — gleich mitwandert. Die
Höhe über Meer bleibt. Der Bericht nennt nur, **dass** verschoben wurde und die Grössenordnung
(«1000–10000 km»), nie den Betrag — der Betrag wäre die Lage.*

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
*In diesem Projekt werden sie für Testdaten bewusst **deterministisch** erzeugt.* Beim
**Neutralisieren** einer Datei werden alle neu und zufällig vergeben: Über die alte Kennung
liesse sich die Kopie sonst dem Original zuordnen (`runners/ifc_neutral_runner.py`, 24.10.2026).

**Neutralisieren (eines Modells)** — Aus einer echten Gebäudedatei eine Kopie machen, in der
nichts mehr steht, was auf Menschen, Büros, Orte oder das Projekt zeigt: Namen, Adressen,
Beschreibungen, Nummern, Texte, die Verortung auf der Landkarte. Was das Bild trägt, bleibt —
die Form, die Art jedes Bauteils, Öffnungen, Materialien und Farben. Die Eingabe wird nie
verändert. *In diesem Projekt `tools/ifc_neutralisieren.py` (Auftrag 354, 24.10.2026), damit ein
echtes Wettbewerbsmodell den Vorführlauf tragen kann, ohne dass ein Name ins Bild oder ins
Repo gerät. **Grenze:** Es tilgt Texte, nicht die Gestalt — ein bekannter Ort bleibt an seiner
Form erkennbar.*

**Schwärzen (von Beschriftungen)** — Das Entfernen sichtbarer Schrift aus einem Modell: Texte,
die in der Datei als Zeichnungsinhalt stehen (siehe *Anmerkung*), und Bauteile, die sich Schild,
Logo oder Schriftzug nennen. Der Begriff kommt vom Schwärzen eines Dokuments; hier wird nicht
übermalt, sondern weggenommen, damit das Bild gar nichts mehr zum Lesen hat.

**Anmerkung (`IfcAnnotation`)** — Ein Eintrag in einer Gebäudedatei, der nicht gebaut wird,
sondern beschreibt: Beschriftungen, Masslinien, Planköpfe, Nordpfeile. Er kann echten Text
tragen (Büro, Projekt, Planverfasser). *Die Umwandlung ins Bildmodell lässt Anmerkungen ohnehin
weg; beim Neutralisieren werden sie samt Text und Schriftstil entfernt.*

**Eigenschaftssatz (Property Set)** — Eine benannte Liste von Zusatzangaben an einem Bauteil,
etwa «aussen liegend: ja» oder «Fläche: 12,5 m²». Die Norm hat Standardsätze (`Pset_WallCommon`),
Programme und Büros legen eigene an, oft mit ihrem Namen im Satznamen. *Beim Neutralisieren
fallen Angaben mit Text weg; Zahlen und Ja/Nein bleiben, eigene Satznamen werden zu
«Eigenschaften N».*

**Restprüfung (Resttexte)** — Der Schluss des Neutralisierens: Jeder Text der fertigen Kopie
wird gegen eine Liste unverfänglicher Werte gehalten (Wörter der Norm, «Projekt», «Geschoss 0»,
Stoffwörter wie «Beton»). Was nicht passt, ist ein **Resttext** — gezählt mit Klasse und Feld,
**nie mit seinem Wortlaut**, denn der könnte ein Name sein. Erst bei «0 Resttexte» darf die
Kopie weiter.

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

**Betragsmass gegen Rangmass** — Zwei Arten, aus derselben Messreihe eine Aussage zu
gewinnen. Ein **Betragsmass** fragt *wie gross* ein Unterschied ist, ein **Rangmass** nur,
*welches von beiden grösser* ist.
*Der Unterschied entscheidet, wo ein Mass noch trägt. Ein Tiefenschätzer, der nur ein
einzelnes Bild sieht, gibt **relative** Tiefe: Die Reihenfolge stimmt, die Skala ist
willkürlich. Fragt man ihn nach dem Betrag, bekommt man eine Zahl, die von der Skala
abhängt — und die staucht er dort, wo ihm der Bildhinweis fehlt.*
*Am 23.08.2026 gemessen, an derselben Stelle desselben Bildes: Bauwerk 1,7124, Nachbar
1,6112. Die Reihenfolge ist richtig — der Nachbar liegt hinten. Der Betrag beträgt aber nur
3 % der Kartenspanne, obwohl in Wirklichkeit 15 m dazwischen liegen. Ein Betragsmass misst
dort nichts mehr, ein Rangmass auf denselben Daten 67 % gegen einen Zufallswert von 34 %.*
*Der Preis ist gleich mitgemessen: Das Rangmass beantwortet «steht da etwas», nicht «wie
gut ist es gezeichnet» — seine Werte fallen nicht gleichmässig, wenn das Bauwerk
schrittweise verschoben wird. Ein Rangmass ist darum kein besseres Mass, sondern ein
anderes.*

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

**Zweigipflige Verteilung (bimodal)** — Eine Messreihe, deren Werte sich nicht um eine
Mitte scharen, sondern um **zwei** getrennte Häufungen, mit einem weitgehend leeren Bereich
dazwischen. Der Mittelwert liegt dann genau dort, wo fast nichts ist, und beschreibt
niemanden. *In diesem Projekt die Regel und nicht die Ausnahme: Eine Tiefenkarte aus einem
Innenraum mit Fenster enthält den Raum (wenige Meter) und die Welt draussen (hunderte
Meter), und dazwischen nichts. Am 11.09.2026 lagen an einem gemessenen Raum 98,6 % der
Punkte zwischen 1,75 m und 10 m, 1,13 % bei 1600 m — und zwischen 146 m und 1000 m kein
einziger.*

**Lücke (einer Verteilung)** — Der leere Bereich zwischen zwei Häufungen einer
zweigipfligen Verteilung. Sie ist die Stelle, an der sich die Verteilung **von selbst**
teilt: Man muss keine Grenze erfinden, man liest ab, wo das Bild nichts hat.
*In diesem Projekt trennt :func:`ferne_abtrennen` die Ferne an dieser Lücke ab, statt ein
festes Perzentil zu verwenden. Der Anlass war ein Fehlschlag: Ein 99er-Perzentil schneidet
das oberste Prozent weg — die gemessene Fernsichtebene machte aber 1,13 % aus, also mehr
als eines. Das Ergebnis war eine flachgedrückte Karte, auf der 98,7 % aller Punkte über
0,99 lagen. **Ein festes Perzentil setzt voraus, dass man vorher weiss, wie viel Ferne im
Bild steht — und wie viel Himmel im Bild steht, weiss nur das Bild.***

**Feste Schranke (einer Tiefennormierung)** — Ein vorab gesetzter Meterwert, ab dem ein
Tiefenwert als „Hintergrund" gilt und nicht mehr mitgerechnet wird. *In diesem Projekt
`hintergrund_ab_m` = 10 000 000 m in `bildschreiben.normalisiere_tiefe`. Sie wurde
eingeführt, weil Blenders eigener `Normalize`-Knoten über **alle** Bildpunkte normiert,
also auch über den Hintergrund mit rund 10¹⁰ Metern — das Gebäude landet dann in den
untersten Promille und wäre gleichmässig schwarz. Die Begründung stimmt, aber sie löst nur
den extremen Fall. Am 16.09.2026 nachgerechnet: Eine Fernsichtebene bei 1600 m liegt weit
unter der Schranke, gilt also als Gebäude — und das eigentliche Bauwerk nutzt danach
**0,52 %** des Grauwertbereichs. **Eine feste Schranke setzt genauso wie ein festes
Perzentil voraus, dass man vorher weiss, wo die Ferne anfängt.** Der Fall war der
HomeStation aufgefallen, die ihn für einen Fehler ihrer eigenen Normierung hielt; er ist
unserer.*

**Nutzung des Wertebereichs** — Welchen Anteil der verfügbaren Helligkeitsstufen ein
Bildinhalt tatsächlich belegt. Zwei Karten können dieselben Meter enthalten und trotzdem
verschieden brauchbar sein: Drängt sich alles Wesentliche in ein halbes Prozent der Stufen,
fallen feine Tiefenunterschiede beim Runden einfach weg. *In diesem Projekt die Zahl, an
der die Lücken-Trennung ihren Nutzen zeigt: 0,52 % gegen 100 % an derselben Karte — die
192-fache Auflösung dort, wo das Bild stattfindet, für 1,14 % Punkte, die dafür geklemmt
werden.*

**Boden (eines Wertebereichs)** — Ein kleinster Wert, den echter Bildinhalt nicht
unterschreiten darf, damit er sich von „nichts" unterscheidet. *In diesem Projekt der
Grund, warum geklemmte Geometrie nicht auf Grauwert 0 landet: Das **ist** der Wert des
Hintergrunds. Am 16.09.2026 gemessen — die geklemmte Fernsichtebene war im Bild
byte-gleich mit dem Himmel. Der Schaden liegt nicht im Bild, sondern in der Kennzahl: Die
Silhouette entsteht aus „heller als der Hintergrund", geklemmte Punkte fielen heraus, und
`geom_iou` fiele mit ihnen — **das Bild bliebe gleich gut, die Zahl würde schlechter, und
niemand wüsste warum.** Der Boden gilt für alle Geometrie desselben Laufs und nicht nur
für die geklemmten Punkte: Zöge man ihn nur dort hoch, wären die fernsten Punkte heller
als die zweitfernsten, und die Tiefenordnung stünde auf dem Kopf.*

**Quantisierungsschritt als Prüfstein** — Ein Unterschied zählt erst, wenn die Datei ihn
noch trägt. Zwischen zwei Grauwerten kann rechnerisch etwas liegen und nach dem Runden auf
die Stufen der Datei trotzdem nichts. *In diesem Projekt an der eigenen ersten Fassung
vorgeführt: Als Boden war ein **halber** 8-Bit-Schritt gewählt, mit der Begründung, er
überlebe beide Bittiefen. Nachgemessen tut er das nicht — ein halber Schritt rundet auf
null, das ist die Bedeutung von «halb». Erst ein ganzer Schritt übersteht 16 **und** 8 Bit.
Die Begründung war plausibel und falsch, und nur das Nachmessen hat den Unterschied
gemacht.*

**Klemmen (einer Tiefenkarte)** — Alles jenseits einer Obergrenze auf genau diese Grenze
setzen, statt es wegzuwerfen. Der geklemmte Punkt bleibt Geometrie, verliert aber seine
Abstufung. *In diesem Projekt der Preis der Lücken-Trennung, und er muss in den Angaben zur
Karte stehen: Wer aus dem PNG wieder Meter rechnet, hält geklemmte Punkte sonst für echte
Messwerte — ein Fehlschlag, der wie ein Erfolg aussieht.*

**Verhältnissprung gegen Abstandssprung** — Zwei Arten, „hier ist eine Lücke" zu messen.
Der **Abstand** fragt *wie viele Meter* zwischen zwei benachbarten Werten liegen, das
**Verhältnis** fragt *um welchen Faktor* der grössere den kleineren übertrifft. *In diesem
Projekt trägt das Verhältnis, aus zwei Gründen. Erstens ist absolut gemessen ein Sprung
bei 1600 m immer grösser als einer bei 5 m — ein Wächter fände dann in jeder Aussenansicht
dieselbe Lücke ganz hinten und nie die, die das Bild teilt. Zweitens ist ein Verhältnis
massstabsfrei: dieselbe Szene in Zentimetern ergibt dieselbe Trennung.*

**Strukturwert einer Tiefenkarte** — Eine Zahl dafür, ob eine Tiefenkarte **Kanten**
enthält oder nur einen gleichmässigen Verlauf. Gemessen wird sie als *zweite Differenz*:
nicht wie stark sich die Tiefe von Punkt zu Punkt ändert, sondern wie stark sich diese
Änderung selbst ändert. *Der Unterschied ist der ganze Punkt und wurde am 12.09.2026 an
16×16-Karten nachgemessen: Ein reiner Verlauf und eine harte Kante haben **dieselbe**
erste Differenz (beide 0,0333) — die erste Differenz unterscheidet sie also nicht. Die
zweite trennt sie sauber: 0,0000 gegen 0,0714. Ein gleichmässiger Anstieg hat überall
dieselbe Steigung, eine Kante ändert sie sprunghaft.*

**Auskunft neben dem Urteil** — Ein gemessener Wert, der im Ergebnis **steht** und warnt,
aber über Bestehen oder Durchfallen **nicht mitentscheidet**. *In diesem Projekt der
Strukturwert in der Rahmungsprüfung. Der Anlass, ihn zu messen, war ein Fehlurteil: Der
Riegel misst nur den Füllgrad, wies darum am 12.09.2026 die brauchbare Übersichtskamera ab
(59,9 % statt nötiger 65 %) und liess die nutzlose Nahaufnahme durch — 100 % Füllgrad,
5,1 m vor einer fensterlosen Wand, die Tiefenkarte ein reiner Verlauf. Trotzdem bricht der
Strukturwert nichts ab, denn seine Schwelle ist **gesetzt und nicht kalibriert**; die
Messreihe dazu liegt als Auftrag bei der HomeStation. Der Grund für die Zurückhaltung ist
selbst ein Argument: **Wer eine Schwelle vorzieht, verliert die Messung, mit der er sie
hätte eichen können** — ab dann läuft der Fall gar nicht mehr durch.*

**Auskunft (im Befund, gegen Warnung)** — Ein Satz im Prüfbericht, der sagt, *was* getan wurde, ohne dass etwas
aufgefallen ist. Eine **Warnung** dagegen meldet eine Abweichung, die jemand ansehen sollte; leer heisst dort «nichts
aufgefallen». *Wozu die Trennung:* Ein Normalfall unter den Warnungen liest sich wie ein Fehler und stumpft den Leser
gegen echte Warnungen ab. *Im Projekt:* das Feld `auskunft` der Bauwerksmaske (`maske.bauwerksmaske`), heute mit dem Satz
«Gelände aus der Datei: …», wenn die Modelldatei ihr Gelände selbst über die **Rolle am Knoten** als Boden kennzeichnet.
Bis zum 23.10.2026 stand derselbe Befund als «Kein Gelände erwartet, aber …» unter den Warnungen (Ergebnis 345, S7;
Protokoll 74 §267).

**Rückkanal** — Eine Auskunft, die **vom Adressaten** kommt und nicht aus der eigenen
Buchführung geschlossen ist. *In diesem Projekt der Vermerk «gesehen». Die Auswertung, warum
ein Auftrag unbeantwortet ist, liest sonst nur unsere Seite: wann er entstand, ob er
hinausging, wann der Adressat zuletzt irgendetwas beantwortet hat. Ein zugestellter Auftrag
ohne Antwort kann gelesen und verworfen, ungelesen liegengeblieben oder nie angekommen
sein — von hier aus sieht das dreierlei gleich aus. Darum schlägt ein bestätigter Blick die
beiden geschlossenen Lagen: **Eine Tatsache vom Adressaten ist stärker als jeder Schluss
aus seinem Antwortverhalten.** Er schlägt aber nicht «nicht zugestellt» — widersprechen
sich beide, ist das ein Fehler in unserer eigenen Ablage, und ihn zuzudecken hiesse, die
einzige Stelle zu verlieren, an der er noch auffällt.*

**Falscher Freund** — Ein Wort, das in zwei Sprachen gleich aussieht und etwas anderes
bedeutet. *In diesem Projekt der Grund, warum `elf` **nicht** im Übersetzungsglossar steht:
Im Englischen ist es ein Fabelwesen. Der Eintrag hätte `elf statue` zu `eleven statue`
gemacht und den englischen Prompt zugleich für deutsch gehalten. Es ist der einzige echte
falsche Freund unter den zwölf Zahlwörtern — nachgemessen am 16.09.2026, indem jeder
Eintrag versuchsweise gesetzt und geprüft wurde, was sich an englischem Text ändert. Alle
übrigen änderten genau nichts ausser sich selbst.*

**Kollision beim Endungsabstreifen** — Wenn die Regel, mit der ein Wort auf seine Grundform
zurückgeführt wird, zwei verschiedene Wörter auf denselben Eintrag führt. *In diesem Projekt
der Grund, warum `acht` nicht im Glossar steht — obwohl es im Englischen völlig harmlos ist.
`achte` und `achten` streifen ihre Endung ab und landen beide auf `acht`; der Eintrag hätte
darum durch die Hintertür die **Ordnungszahl** (`achte` = eighth, nicht eight) und den
Verbstamm von «achten» mitübersetzt. Es ist das einzige der zwölf Zahlwörter, dem das
passiert: Bei `zweite`, `vierte`, `zehnte` bleibt `zweit`, `viert`, `zehnt` übrig, und das
ist kein Eintrag. Die Abwägung dahinter ist die Hausregel im Kleinen: Ein stehengebliebenes
`acht` wird als unbekannt gemeldet und kostet einen Blick — ein stilles `achte` → `eight`
kostet ein Bild.*

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

*Und dieser Satz war bis zum **26.08.2026** kein Gedankenspiel, sondern der Zustand
unserer eigenen Kette: Das gemessene Vorzeichen wurde nur im Maskenweg benutzt, das
eigentliche Tor rechnete mit dem Betrag. Eine Tiefenkarte mit vertauschtem Vorne und
Hinten kam damit auf **0,7071** und bestand die Grenze 0,65. Seit die Messung am Tor
ankommt, fällt sie durch. Die Zahl steht in einem Test, nicht nur hier — sie ist das Mass
dafür, wie gross die Lücke war.*

*Eine Auflage ist dabei neu, und sie trennt zwei Verwendungen: Für einen **Diagnosewert**
darf die deklarierte Angabe einspringen, wenn nichts gemessen ist — besser als keine. Für
ein **Urteil** nicht: Dort schneidet ein Vorzeichenfehler den Wert auf null, und aus einer
falschen Zeile in einer Modellkarte würde ein durchgefallenes Bild, ohne dass am Bild etwas
falsch wäre.*

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

**Geometrieanteil** — Wie viel eines Bildes überhaupt Bauwerk ist: die Zahl der
Bildpunkte mit Geometrie, geteilt durch alle Bildpunkte. Ein Bau, der klein im Bild steht,
hat einen kleinen Geometrieanteil; einer, der es füllt, einen grossen. Die Zahl hängt
**nicht** an der Auflösung — dasselbe Bild doppelt so gross gerechnet hat denselben
Anteil. *In diesem Projekt ist sie keine Beschreibung, sondern eine Bedingung: `geom_iou`
hängt an ihr. Am 19.08.2026 gemessen: Bei 17 % Anteil deckelt `geom_iou` bei 0,256, bei
60 % bei 0,967 — dieselbe Metrik, derselbe perfekte Render, ein anderes Ergebnis. Unsere
Testszenen liegen bei 0,0822 (Hochbau mit Gelände), 0,1111 (Quader) und 0,1730 (Hochbau),
die synthetische Studienszene bei 0,4489. Darum nennt jedes Studienergebnis den Anteil mit
(`schwellenstudie`, Feld `geometrieanteil`): Eine Schwelle, die bei 44 % kalibriert wurde
und bei 8 % angewandt wird, ist nicht dieselbe Schwelle.*

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
Beleuchtung wiedergeben.* Ebenso für die Umgebung (Splat, Netz, Textur), mit der **Stärke 1**: Ihre
Farbe ist schon das Licht der Aufnahme; noch einmal beleuchtet, sähe sie doppelt belichtet aus — mit
Stärke 1 steht im Bild genau die Farbe der Datei.

**View-Transform (AgX, Standard)** — Die Umrechnung von berechneten Lichtwerten in
Bildwerte. `AgX` bildet filmisch ab und ist für Ansichtsbilder schöner; `Standard` rechnet
unverfälscht und ist nötig, wenn aus dem Bild wieder Zahlen werden sollen. *Seit
auf-20261020-292:* Mit Himmelsbild rechnet das Schönbild mit `AgX` (sonst dem älteren `Filmic`),
weil «Standard» die sehr hellen Werte eines Himmels einfach abschneidet; der Kennfarben-Durchgang
und alle Läufe ohne Himmelsbild bleiben bei `Standard`. Siehe **Tonwerte (Tonwertkurve)**.

**Tonwerte (Tonwertkurve)** — Die Regel, nach der ein Programm die gerechneten Helligkeiten in die
Helligkeiten eines Bildes übersetzt. Ein Bildschirm kann nur von Schwarz bis Weiss zeigen; ein Himmel
mit Sonne ist aber tausendmal heller. Eine gerade Kurve («Standard») schneidet alles über Weiss ab —
dort wird das Bild flach weiss. Eine weiche Kurve wie **AgX** führt die hellen Werte sanft gegen Weiss,
wie ein Film: Kanten und Schattierungen bleiben auch im hellen Licht sichtbar. *Im Projekt:* seit
auf-20261020-292 bei jedem Bild mit Himmelsbild, dazu eine **Belichtung je Stimmung**.

**Belichtung (je Stimmung)** — Wie hell das ganze Bild gestellt wird, gemessen in Blendenstufen: eine
Stufe weniger halbiert das Licht im Bild, eine mehr verdoppelt es. *Im Projekt:* Jede Stimmung trägt ihren
Wert als Daten (`stimmung.STIMMUNGEN[…]['belichtung_ev']`) — Mittag dunkler gestellt als Abend, weil das
Haus bei Mittag überstrahlte. Die Zahlen sind ein erster Stand und werden am Heim-PC nachgemessen
(auf-20261020-293).

**Überstrahlung (voll weisse Bildpunkte)** — Ein Bildpunkt ist überstrahlt, wenn er so hell ist, dass
alle drei Farben auf dem Höchstwert stehen (255 von 255): Er zeigt nur noch «hell», nicht mehr, was dort
ist — Kanten, Fugen und Schatten gehen verloren. *Im Projekt:* gemessen als Anteil voll weisser Punkte
**am Haus** (nur auf der Bauwerksmaske, der Himmel darf hell sein); Ziel unter 1 %. Steht im Ergebnis
als `qa.ueberstrahlt_anteil`, je Kamera und für den Lauf (`belichtung.ueberstrahlt_anteil`).

**Ruhiger Hintergrund (Kamerastrahl)** — Was die Kamera hinter dem Haus sieht, wenn ein Himmelsbild
das Licht gibt. Ein Himmelsbild ist ein Rundumfoto — mit Bäumen, Felsen, Strassen —, und direkt gezeigt
schwebt das Haus vor einem fremden Foto. Darum unterscheidet der Rechner zwei Arten von Lichtstrahlen:
Strahlen, die von der Kamera ausgehen («Kamerastrahl»), sehen einen schlichten Farbverlauf vom Horizont
zum Himmel in den Farben dieses Himmelsbilds; alle anderen Strahlen — Licht, Schatten, Spiegelungen in
Glas — sehen das echte Himmelsbild. *Im Projekt:* seit auf-20261020-292, `_ruhiger_hintergrund` im Runner.

**Tönung (je Stimmung)** — Das Himmelslicht einer Stimmung wärmer oder kühler färben, angegeben als
**Farbtemperatur** in Kelvin (6500 K neutral, darunter wärmer, darüber kühler). *Im Projekt:* Eine
Stimmung kann ihr Himmelslicht damit tönen (Abend warm, Winter kühl), ohne es heller
oder dunkler zu machen — Helligkeit regelt die **Belichtung**.

**Bestellte Bildgrösse und Raster** — Das Bildmodell kann nur Bilder rechnen, deren Breite und Höhe durch
16 teilbar sind. Bis auf-20261020-292 wurde darum schon das Blender-Bild auf diese Masse abgerundet
(960 × 600 wurde 960 × 592) — und damit verschoben sich Bildwinkel und Kamerastandpunkt. Seither rechnet
Blender die bestellte Grösse; nur das Bildmodell rechnet intern gerundet, und sein Bild wird danach
wieder auf die bestellte Grösse gebracht.
*Seit auf-20261020-293:* Das Bildmodell hat zusätzlich eine **Untergrenze** — siehe **Untergrenze im
KI-Schritt**.

**Untergrenze im KI-Schritt (kleinste lange Seite)** — Wie gross ein Bild mindestens sein muss, damit das
Bildmodell das Haus darin noch «sieht». Auf einem kleinen Grundlagenbild (480 Bildpunkte breit) malte die
schnelle Vorschau Strand und Wolken statt des Hauses; auf 960 Bildpunkten folgte sie dem Haus. Seither
werden die Vorlagen für das Bildmodell vorher vergrössert (auf mindestens 1024 Bildpunkte lange Seite),
und das fertige KI-Bild wird danach wieder auf die bestellte Grösse gebracht. *Im Projekt:* ein Wert am
Eintrag des Bildmodells (`Backbone.ki_mindest_lange_seite`), seit auf-20261020-293.

**Kontrast Haus–Hintergrund** — Wie deutlich sich das Haus im Bild von dem abhebt, was dahinter liegt:
die mittlere Helligkeit des Hauses minus die mittlere Helligkeit des Himmels gleich daneben, auf einer
Skala von 0 (schwarz) bis 255 (weiss). Bei 0 ist das Haus so hell wie sein Hintergrund und verschwimmt
darin, auch wenn es scharf gerechnet ist. *Im Projekt:* gemessen am Bild aus Blender, nur auf dem Haus
(Bauwerksmaske) und am Himmel daneben; steht im Ergebnis als `qa.kontrast_haus_hintergrund`. Bis zum 23.10.2026 stand
unter 20 der Satz «HAUS KAUM SICHTBAR»; seither hängt der Satz am **Kontrast am Umriss** (unten), und diese Zahl gilt nur
noch dort, wo der Umriss fehlt (Rückfall). Anlass: auf-20261020-293 (Winter −0,5, Mittag +66,9). Seit dem 22.10.2026 steht bei
einem KI-Bild **daneben** derselbe Wert am KI-Bild (`qa.kontrast_haus_hintergrund_ki`, gleiche Maske, gleiche Formel, ohne
Warnung) — die zwei können sich umkehren (334: Blender −27,7, KI-Bild grob +37; Protokoll 74 §250).

**Vorprobe (der Stimmung)** — Ein kleines, schnelles Probebild vor dem eigentlichen Bild, nur um eine Zahl
zu messen: wie hell das Haus in diesem Licht wird. Danach wird der ruhige Hintergrund so gestellt, dass er
um einen festen Abstand dunkler oder heller ist als das Haus — eine Blendenstufe, also halb oder doppelt so
hell —, und erst dann wird das richtige Bild gerechnet. *Im Projekt:* `_hintergrund_abstimmen` im Runner,
ein Viertel der Bildgrösse, seit auf-20261020-293.

**Fülllicht** — Das weiche Licht, das die Schattenseiten eines Gebäudes aufhellt, damit sie nicht schwarz
werden. Draussen kommt es vom ganzen Himmel. *Im Projekt:* Das Himmelsbild einer Stimmung gibt seit
auf-20261020-293 nur noch dieses Fülllicht, mit geringerer Stärke (`fuell_staerke`); die Sonne darin wird
abgeschnitten, weil eine eigene Sonnenlampe ihre Arbeit übernimmt — sonst stünde die Sonne doppelt da.

**Sonnenlampe (aus dem Himmelsbild)** — Ein Licht, das wie die Sonne aus einer einzigen Richtung kommt und
darum harte Schatten wirft. *Im Projekt:* Seit auf-20261020-293 sucht der Rechner im Himmelsbild die
Sonnenscheibe (den kleinen, sehr hellen Fleck), nimmt ihre Richtung, Farbe und relative Stärke und stellt die
Lampe genau dorthin — gedreht, wenn das Himmelsbild gedreht ist. Bei Stimmungen ohne Sonne (bedeckt, Nebel,
blaue Stunde, Weissmodell) eine **weiche** Lampe aus dem hellsten Bereich: Sie ist gross gedacht und wirft
darum nur weiche Schatten. Die Stärken sind gesetzt, nicht gemessen.

**Streiflicht** — Licht, das sehr flach über eine Fläche streicht, etwa von einer tiefen Morgen- oder
Abendsonne. Es macht jede Unebenheit und jede Kante sichtbar und wirft lange Schatten. *Im Projekt:* Bei
«morgen» und «abend» steht die Sonne im Himmelsbild tief; die Sonnenlampe übernimmt diese Höhe (mindestens
2° über dem Horizont), und das ergibt Streiflicht.

**Schattenwinkel (Grösse der Lichtquelle)** — Wie gross eine Lichtquelle vom Haus aus gesehen ist, in
Grad. Die echte Sonne ist ein halbes Grad gross: Ihre Schatten haben scharfe Kanten. Eine grosse
Lichtquelle (ein bedeckter Himmel, ein Softbox im Studio) wirft weiche, verlaufende Schatten. *Im Projekt:*
`winkel_grad` je Stimmung — unter 2° für Sonne, 20–50° für die weichen Lampen. Findet sich bei einer
Stimmung mit Sonne keine Sonnenscheibe im Himmelsbild, nimmt die weiche Ersatzlampe seit auf-20261020-294
ihren eigenen, grossen Winkel (`winkel_weich_grad`, 25°) — vorher behielt sie den kleinen der Sonne und warf
harte Schatten, obwohl sie «weich» hiess.

**Kontrast am Umriss** — Wie deutlich sich das Haus **an seiner Kante** vom Hintergrund abhebt: an jeder Stelle, an der
Haus und Hintergrund aneinandergrenzen, ein Bildpunkt knapp innerhalb gegen einen knapp ausserhalb, und davon der
Unterschied ohne Vorzeichen gemittelt (0 bis 255). *Wozu:* Der Mittelwert-Kontrast (oben) vergleicht das ganze Haus mit dem
ganzen Hintergrund; ein Haus mit heller Sonnen- und dunkler Schattenseite vor mittelgrauem Himmel hat dort fast null und
ist doch deutlich zu sehen — das Auge sieht ein Haus an seinem Umriss. *Im Projekt:* `belichtung.kontrast_am_umriss`, im
Ergebnis `qa.kontrast_umriss_haus_hintergrund`. Seit dem 23.10.2026 trägt diese Zahl die Warnung «HAUS KAUM SICHTBAR»:
unter 15 (`belichtung.KONTRAST_UMRISS_SCHWELLE`). Anlass: Messung 344 — mittags war das Haus von Auge klar zu sehen, der
Mittelwert sagte −5, der Umriss 54. Die 15 ist **nachgerechnet, nicht am Gerät gemessen**: an den Stimmungsbildern von
Messung 293 lag der Umriss bei «verschwimmt» zwischen 1 und 10, bei «lesbar» ab 18 (Protokoll 74 §263). Seit dem
Nachtrag S7 (Ergebnis 345, Protokoll 74 §267) folgt auch der Schalter `kaum_sichtbar` im Kontrastbefund diesem Urteil
(fehlt der Umriss, der Mittelwert); die Antwort des Mittelwerts allein steht als `kaum_sichtbar_mittelwert` daneben.

**Look (einer Tonwertkurve)** — Eine Spielart derselben Tonwertkurve mit mehr oder weniger Kontrast, wie
eine Filmsorte. *Im Projekt:* Seit auf-20261020-293 rechnen Bilder mit Himmelsbild mit «AgX – Medium High
Contrast» statt der neutralen Fassung, gegen den milchigen, flachen Eindruck. Blender nennt den Look je
Fassung etwas anders; der Rechner versucht beide Schreibweisen und meldet, wenn keine ging.

**Frontallicht** — Licht, das von hinten über die Schulter der Kamera auf das Haus fällt. Die Fassade, die
man sieht, ist gleichmässig hell, ihre Schatten fallen nach hinten, hinter das Haus, wo die Kamera sie nicht
sieht — das Bild wirkt flach. *Im Projekt:* der Befund aus auf-20261020-294: In allen acht Himmelsbildern
stand die Sonne zufällig 0–40° neben der Blickrichtung der Kamera.

**Sonne seitlich der Kamera (Drehung zur Kamera)** — Das Himmelsbild einer Stimmung wird für jede Kamera
so um die Hochachse gedreht, dass die Sonne um einen festen Winkel neben der Linie Haus–Kamera steht, auf
einer gewählten Seite (links oder rechts, von der Kamera aus gesehen). 0° wäre Sonne im Rücken der Kamera,
90° Licht genau von der Seite, 180° Gegenlicht. Bei 60–100° ist eine Fassade beleuchtet, die andere im
Schatten, und der Schlagschatten fällt seitlich ins Bild. *Im Projekt:* `sonne_seitlich_grad` und
`sonne_seite` je Stimmung (mittag 65° links, abend 80° rechts, sonst 70° links), gerechnet in
`stimmung.drehung_zur_kamera`, seit auf-20261020-294. Bestellt jemand ausdrücklich eine Drehung
(`rotationGrad`), gilt seine.

**Gemischter Prompt** — Ein Bildauftrag in zwei Sprachen, etwa «zeitgenoessisches Wohnhaus, Sichtbeton,
Architekturfotografie, no people»: deutsche Fachwörter und ein englischer Zusatz. Weil «no» englisch ist
und die deutschen Fachwörter weder Umlaut noch typisch deutsche Füllwörter tragen, hielt die
Spracherkennung ihn für englisch und übersetzte nichts — das Bildmodell verstand «Sichtbeton» nicht und
malte Holzlamellen. *Im Projekt:* Seit auf-20261020-294 zählen Wörter, die wörtlich im Glossar stehen; ein
gemischter Prompt wird übersetzt, der englische Teil bleibt stehen (`sprache.ist_gemischt`).

**Neue Baumasse ausserhalb des Umrisses** — Wieviel Gebäude das KI-Bild dort zeigt, wo das Modell nur
Himmel hat, im Verhältnis zur Fläche des Hauses: 0 heisst, das Bild baut nur, was modelliert ist; 1 hiesse,
neben dem Haus steht noch einmal so viel Gebäude. Gezählt wird seit der Eichung an auf-20261021-297 alles, was
dort **nicht Himmel** ist — der Tiefenschätzer legt den Himmel und die Wolken auf «unendlich fern»; Bäume und
ferne Hügel zählen mit —, ohne den Boden und ohne einen schmalen Rand um das Haus. Hat das Bild gar keinen
Himmel (das Gipsmodell vor einer Fels- oder Studiowand), zählt nur, was so nah wie das Haus ist; das war bis 297
die einzige Zählung, und sie war bei Häuserzeilen, die etwas hinter dem Haus stehen, viel zu klein (0,30 statt
2,2). *Im Projekt:* `qa.ausserhalb_umriss_anteil` (Modul `baumasse`), mit dem Satz «KI BAUT UEBER DEN
UMRISS HINAUS» ab 0,25 — gesetzt, nicht gemessen; eine Auskunft, kein Tor. Anlass: auf-20261020-294, wo aus
der Geländeplatte ein Gebäude über die ganze Bildbreite wurde. Weil die Zahl an der Hausfläche gemessen wird, kann sie
über 1 liegen (in 295–297 nach der Eichung: Aussenbilder 2,0 bis 4,3, Gipsmodelle 0 bis 0,2).

**Eichung (einer Zahl)** — Das Abgleichen einer Rechnung mit einer Zählung, der man traut: Man legt dieselben Bilder
neben beide, sieht, wo sie auseinanderliegen, und stellt die Rechnung so ein, dass sie die Zählung trifft — ohne dabei
die Fälle zu verderben, die schon stimmten. *Im Projekt:* `ausserhalb_umriss_anteil` wurde an den Bildern aus 295–297
gegen die Nachzählung der HomeStation geeicht (Protokoll 74 §169, mit Tabelle); fünf Rechenwege standen zur Wahl.

**Kantendichte** — Wie viele deutliche Hell-Dunkel-Übergänge auf einer Fläche liegen. Ein Himmel hat fast keine, eine
Fassade mit Fenstern viele — eine Felswand aber auch. *Im Projekt:* als Kandidat für die Eichung von
`ausserhalb_umriss_anteil` gerechnet und verworfen, weil sie Felswände als Gebäude zählt.

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

**Himmel hinter dem Umriss** — Der Anteil der Silhouettengrenze eines Bauwerks, hinter
dem im *Entwurf* nichts mehr steht — kein Nachbargebäude, kein ansteigendes Gelände,
sondern offener Himmel. Abgelesen wird er am Entwurf und **nicht** am erzeugten Bild.
*Er entscheidet, ob die Umrisstreue überhaupt etwas messen kann. Wo Himmel dahintersteht,
ist der Tiefensprung an der Silhouette riesig und für jedes Verfahren sichtbar. Steht dort
ein Nachbarhaus, ist der Sprung im Entwurf zwar immer noch gross — gemessen 15 m — aber
ein Tiefenschätzer, der nur ein einzelnes Bild sieht, legt zwei ähnliche Betonkörper in 34
und 49 m praktisch nicht auseinander. Er hat dafür keinen Bildhinweis.*
*Am 23.08.2026 gemessen: bei 63 % Himmel misst die Umrisstreue 0,42, bei 0 % nur noch
0,0016 — und ein zufälliges Rauschbild kommt dort auf −0,0024. Das Mass trennt in solchen
Szenen ein perfektes Bild nicht mehr von Rauschen. Dass es trotzdem eine Zahl ausgab, war
der gefährliche Teil.*

**Zuständigkeitsgrenze (eines Messverfahrens)** — Die vorab beantwortbare Frage, ob ein
Verfahren in einer bestimmten Lage **überhaupt etwas messen kann** — gestellt, *bevor*
gemessen wird, und beantwortet aus dem, was ohnehin schon vorliegt.
*Der Unterschied zu einer Schwelle: Eine Schwelle trennt gute von schlechten Messwerten.
Eine Zuständigkeitsgrenze trennt Messwerte von Nicht-Messwerten. Wer sie weglässt, bekommt
statt einer Fehlanzeige eine Zahl — und Zahlen werden geglaubt.*
*Eine Prüfung, die das Ergebnis der Messung braucht, ist keine: Sie käme zu spät und hinge
von genau der Messung ab, die sie beurteilen soll. Darum liest die Zuständigkeitsprüfung
in diesem Projekt ausschliesslich den Entwurf, der in der Kette immer vorher vorliegt.*
*Die Folge im Betrieb ist ungewohnt: Das Prüfergebnis lautet dann weder «bestanden» noch
«durchgefallen», sondern «hier ist nichts zu messen». Das ist eine dritte Antwort, und sie
muss eigens gemeldet werden — sonst sieht sie aus wie ein bestandenes Tor.*

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

**Anwesenheitsmass gegen Gütemass** — Zwei Fragen, die man leicht verwechselt, weil beide
mit «ist das Bild gut» anfangen. Ein **Anwesenheitsmass** beantwortet *«steht dort
überhaupt etwas»*, ein **Gütemass** *«wie gut ist es getroffen»*.
*Der Unterschied ist daran erkennbar, wie sich ein Mass verhält, wenn man das Bauwerk
schrittweise verschiebt. Ein Gütemass muss dabei gleichmässig fallen — sonst kann man aus
seinem Wert nicht auf die Güte schliessen. Ein Anwesenheitsmass darf zwischendurch wieder
steigen; es sagt nur, dass etwas da ist.*
*Am 23.08.2026 gemessen: Das Rangmass dieses Projekts ging bei wachsendem Versatz 75,5 →
71,7 → **73,8** → 71,1 → 63,1 → 59,4 Prozent — der Sprung nach oben in der Mitte ist der
Beweis, dass es kein Gütemass ist. Es bleibt trotzdem nützlich, denn es trägt in Szenen,
in denen das Gütemass gar nichts mehr misst.*
*Daraus folgt: Man ersetzt das eine nicht durch das andere. Wer ein Gütemass durch ein
Anwesenheitsmass ersetzt, gibt eine Frage auf, statt eine zu beantworten.*

**Durchgelaufen gegen richtig** — Der Unterschied zwischen «ein Arbeitsschritt hat keinen
Fehler gemeldet» und «sein Ergebnis stimmt». Der erste ist billig zu haben und wird
regelmässig für den zweiten gehalten.
*Am 24.08.2026 an neun echten Gebäudedateien vorgeführt: Zwei verschiedene Leseprogramme
verarbeiteten alle neun ohne einen einzigen Fehler — und **kein einziger Vergleich prüfte,
ob die herausgekommene Geometrie der Vorlage entspricht.* Genau dieselbe Verwechslung stand
am Anfang der Bildprüfung dieses Projekts: Eine Bewertung über das ganze Bild lief ebenfalls
immer durch und beantwortete nicht, ob im Bild überhaupt ein Gebäude steht.*
*Prüfen lässt sich das nur dort, wo die Wahrheit **unabhängig** feststeht. Bei einer echten
Datei kennt sie niemand — man müsste sie mit demselben Werkzeug ausrechnen, das man prüfen
will, und das ist ein Zirkelschluss. Bei einer selbst erzeugten Testdatei kennt man jede
Kante, weil man sie geschrieben hat.*
*Was so eine Prüfung wert ist, gehört mitgesagt: Läuft sie am Testfall schief, läuft es
überall schief. Läuft sie richtig, ist über echte Dateien **nichts bewiesen** — nur etwas
ausgeschlossen.*

**Ortsfeld (eines Tiefenschätzers)** — Die Neigung eines Schätzers, einem Bildpunkt eine
Tiefe **nach seiner Lage im Bild** zuzuweisen — unten nah, oben und in der Mitte fern —
weitgehend unabhängig davon, was dort tatsächlich zu sehen ist.
*Am 24.08.2026 zirkelfrei gemessen: Was unser Schätzer auf einem **leeren** Bild ausgibt,
ist zu **95,75 %** eine Funktion des Ortes. Das Feld wurde aus fünfzehn Zufallsbildern
gewonnen und an fünfzehn anderen geprüft — es sagt deren Ausgabe voraus, ohne sie gesehen
zu haben.*
*Die Folge trifft jedes Mass, das «innerhalb des Bauwerks» gegen «ausserhalb» vergleicht.
Verschiebt man dieselbe Maske über dieselbe Zufallskarte, wandert der gemessene Nullwert
von −0,62 auf +0,65 — er wechselt sogar das Vorzeichen. **Der Nullwert misst dann die Lage
des Bauwerks im Bild und nicht die Bildqualität.** Wer einen einmal gemessenen Nullwert als
Konstante weiterverwendet, vergleicht mit der Zahl einer anderen Bildlage.*
*Das Feld hängt an der **Bildgrösse**, nicht am Seitenverhältnis: Zwei Felder derselben
Grössenklasse stimmen zu 97 % überein, auch wenn eines breit und eines quadratisch ist;
zwei verschiedene Grössen nur zu 85 %. Ein Feld einfach herauszurechnen trägt darum nur je
Bildgrösse — und am oberen Bildrand am wenigsten, also genau dort, wo bei einer
Aussenaufnahme der Himmel steht.*
*Der Ausweg, den dieses Projekt gewählt hat: den Nullwert **je Lauf** an der tatsächlichen
Lage messen. Er wurde ohnehin schon gemessen — nur nie gelesen.*

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
*Beim Rangmass folgt er ebenfalls, und noch einfacher: Hat die Schätzung **gar keinen**
Bezug zum Umriss, ist der Vergleich zweier unabhängiger Mittelwerte ein Münzwurf — also
**50 %**. Das ist am 23.08.2026 zum Anlass geworden, eine vorgeschlagene Schwelle
zurückzuweisen: Sie lag bei 45 % und damit **unter** dem Zufall. Weisses Rauschen bestand
sie in 138 von 200 Versuchen. Die Schwelle war an **einem einzigen** Rauschwert abgelesen,
und derselbe Wert streute über viele Versuche von 23 % bis 77 %.*
*Die Lehre daraus ist dieselbe wie bei einer Spanne aus einer Stichprobe: Ein einzelner
Nullwert ist keine Nulllinie, sondern eine Ziehung.*

**Paarurteil** — Ein Urteil, das **zwei Messwerte nebeneinander stehen lässt**, statt sie
zu einer Zahl zu verrechnen. Es besteht nur, wenn beide bestehen, und es sagt dazu,
welcher der beiden ein Nein trägt.
*Seit dem 29.09.2026 urteilt nur noch der erste der beiden Werte (ρ, die Tiefenordnung).
Der zweite (die Kante am Gebäudeumriss) wird weiter gemessen und angezeigt, entscheidet
aber nicht mehr mit: An echten, erzeugten Bildern streute er um seine eigene Grenze herum.
Owner-Entscheid, Sitzung 72.*
*Warum das eine eigene Bauform ist: Der frühere Geometrie-Score multiplizierte zwei Masse
zu einer Zahl und verschmolz damit zwei verschiedene Fragen — «steht dort etwas» und
«stimmt, was dort steht». Der Faktor, der die erste beantworten sollte, belohnte am Ende
sogar die Abwesenheit. Zwei Fragen brauchen zwei Antworten; eine Zahl, die beide
behauptet, beantwortet keine.*
*Und ein Urteil aus nur einer der beiden Zahlen gilt als **nicht gemessen** — nicht als
«bestanden aufgrund der anderen». Für eine fehlende Antwort gibt es keinen Ersatz.*
*Am 27.08.2026 hat die Bauform ihren stärksten Beleg bekommen: Die beiden Masse
versagen in **entgegengesetzte Richtungen**. Ein Bild kann ein ordentliches ρ
erreichen und den Umriss an 2,8 % der Grenze zeichnen (gemessen, `auf-20260822-30`);
und ein Bauwerk, dessen Tiefen **innen gespiegelt** sind, zeichnet seinen Umriss
**vollkommen** — Kantenanteil 1,0000 — bei ρ = **−1,0000**. Ein Mittelwert aus beiden
wäre null, und null hiesse hier weder das eine noch das andere.*

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
Und dieses Projekt hat sie in jedem Bild verletzt, das es bis zum 23.08.2026 erzeugt hat:
Die Kamerarechnung legte das Blickziel über die Augenhöhe und neigte die Kamera dadurch.*
*Wie stark, ist zweimal falsch behauptet worden, und beide Male von uns.* **Vier Dokumente
sagten «9,46°»** — diese Zahl gilt bei einem Abstand von 1,2 × Gebäudehöhe, den die
Rechnung nie einnimmt. Nachgemessen über zwölf Richtungen, vier Gebäudehöhen und zwei
Formate waren es zunächst 1,92°–4,70°, und nach einer Nachmessung im Hochformat
**−0,51° bis +5,98°** — die negativen Werte fehlten in der ersten Stichprobe, weil sie kein
Hochformat und keine flachen Bauten enthielt.
*Seit dem 23.08.2026 ist die Vorgabe **waagrecht mit Shift**; die geneigte Rechnung bleibt
erhalten und ist ausdrücklich anzufordern. Der Kommentar an jener Stelle nannte das Neigen
einst „den üblichen Griff der Architekturfotografie" — der übliche Griff ist das Gegenteil
(`docs/KAMERAREGELN_2026-08-21.md`).*

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

**Senkrechte Perspektive (Zwei-Punkt-Perspektive)** — Ein Bild, in dem alle senkrechten Kanten des Gebäudes
auch im Bild senkrecht stehen; nur die waagrechten Kanten laufen auf zwei Fluchtpunkte zu. So fotografiert man
Architektur: Die Kamera bleibt waagrecht, und was oben fehlt, holt der **Shift** ins Bild. Das Gegenstück ist
die «freie» Perspektive: die Kamera wird nach oben gekippt, und die Kanten stürzen. *Im Projekt:* Entscheid 109,
Vorgabe «senkrecht» am Knoten «Kamera»; auch eine von Hand gesetzte Kamera kann sie tragen (`perspektive`).

**Fester Abstand (Auto-Kamera)** — Statt «das Haus füllt 70 % des Bilds» wird der Standpunkt in Metern bestellt,
waagrecht von der Mitte des Bauwerks. Der Heim-PC rückt die Kamera dann nicht mehr zurück, wenn etwas über den
Rand ragt — er sagt es nur. *Im Projekt:* `cameras_auto.abstand {art: 'fest', meter}`, 20.10.2026.

**Angewandte Vorgaben (im Ergebnis)** — Was der Heim-PC wirklich gerechnet hat, mit allen Werten, die er selbst
eingesetzt hat, weil die Bestellung sie offenliess — etwa 1,70 m Augenhöhe oder Relief 0,6. *Im Projekt:* das
Feld `angewandt` im Ergebnis, je für Stimmung, Auto-Kamera und Materialien; `vorgaben` nennt die selbst
gesetzten Felder.

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

**Auswahleffekt beim Minimum (Extremwertstatistik)** — Das Kleinste aus mehreren
zufälligen Werten ist im Mittel kleiner als ein einzelner Wert — und zwar umso mehr, je
mehr Werte man zieht. Bei drei Ziehungen liegt das Minimum rechnerisch **0,845
Streuungen** unter dem Mittel, bei fünf 1,163.
*In diesem Projekt ist das keine Theorie: Das Urteil eines Auftrags ist das seiner
schwächsten Kamera. Als die automatischen Ansichten am 23.08.2026 von einer auf drei
gingen, wurde das Gate dadurch strenger — ohne dass jemand das entschieden hätte, und um
eine Grössenordnung (rund 0,19), die grösser ist als jeder Parametereffekt, den die Kette
je gezeigt hat. Die Regel bleibt richtig; was sie kostet, steht seither im Ergebnis.
Merksatz: **Wer mehr misst, misst nicht dasselbe strenger, sondern etwas anderes.***

**Auswählen gegen den eigenen Rauschboden (Kreisschluss)** — Den besten Wert einer
Messreihe daran messen, wie stark **dieselbe** Reihe streut.
*Sieht nach Statistik aus und ist keine: Der Abstand zwischen dem Besten und dem Zweiten
einer Stichprobe hängt systematisch mit deren eigener Streuung zusammen — die Prüfung
bestätigt sich selbst. Der Ausweg ist ein **unabhängig** gemessener Boden aus einer
anderen Reihe. In diesem Projekt sind das 0,2269 aus neun Läufen desselben Aufbaus.*
*Und auch dieser Boden hat eine Grenze, die am 24.08.2026 gemessen wurde: Er gehört der
**Bildlage**, nicht dem Verfahren. Am selben Standort, nur mit anderer Achsenlage, streuten
dieselben Startwerte um 0,0088 statt um 0,1216 — Faktor vierzehn. Die Zahl taugt als
Grössenordnung; wer sie als feste Untergrenze verrechnet, urteilt **zu vorsichtig und nicht
falsch**, aber er urteilt an der Lage vorbei. Dieselbe Ursache wie beim **Ortsfeld**.*

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

**Zweizählige Drehsymmetrie** — Ein Körper sieht nach einer halben Drehung (180°) genau
so aus wie vorher. Ein Quader hat sie, ein Zylinder auch, ein Haus mit Eingang auf einer
Seite nicht.
*Warum das hier steht: Bei einem solchen Körper fallen die **beiden** vorgeschriebenen
Über-Eck-Ansichten zusammen — von Südost und von Nordwest sieht man dasselbe. Gemessen an
einem Testquader: Die beiden Aufnahmen waren Byte für Byte identisch. Die zweite kostete
24,5 Sekunden und lieferte nichts Neues.*
*Woran es sich NICHT entscheiden lässt: an der Hüllbox. Die hat immer zweizählige
Symmetrie, auch bei einem völlig unsymmetrischen Bau — sonst schlüge die Erkennung bei
jedem echten Gebäude falschen Alarm. Entschieden wird an der **Soll-Tiefenkarte**, also
an dem, was die Kamera wirklich sieht.*
*Und die eingesparte Ansicht darf hinterher nicht mitzählen. Wird aus mehreren Ansichten
die schlechteste gemeldet, sinkt dieser Wert allein dadurch, dass man öfter hinsieht —
eine Wiederholung ist aber kein zweites Hinsehen. Sie mitzuzählen machte die Prüfung
stillschweigend strenger.*

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

**Der Nullpunkt des Azimuts (Süd- gegen Nord-Konvention)** — *Ab welcher Richtung* der
Winkel zählt, ist **nicht** einheitlich geregelt, und die beiden gebräuchlichen
Festlegungen liegen 180 Grad auseinander:
* **Von Norden**, positiv nach Osten — Meteorologie, Karten, Navigation (siehe *Azimut*).
* **Von Süden**, positiv nach Westen — Architektur und Bauphysik; dort ist Süden die
  interessante Richtung, und Mittag liegt bei 0°.
*Der Unterschied ist keine Feinheit: Er vertauscht **Vormittag und Nachmittag**. Ein
Gebäude, das morgens von Osten beschienen werden soll, steht dann im Nachmittagslicht —
und das Bild sieht für sich genommen völlig richtig aus. Genau darin liegt die Gefahr:
Der Fehler ist an keinem einzelnen Bild erkennbar, nur am Vergleich mit der Bestellung.*
*In diesem Projekt gilt die **Süd**-Konvention, und zwar als **Setzung**: Die fremde
Bestellung sagt nicht, welche sie meint. Die gewählte Annahme wandert darum in jeden
Bericht mit — damit ein falsch gewählter Nullpunkt später auffindbar ist statt unsichtbar.*

**Deckungsgrad** — Welcher Anteil der Bildbreite vom Gebäude gefüllt werden soll, als Zahl
zwischen 0 und 1. Ein Wert unter 1 schiebt die Kamera weiter weg und lässt Luft um das
Bauwerk. *Das ist die gestalterische „Zweidrittel-Komposition" als Zahl ausgedrückt.*
*In diesem Projekt **0,70 seit dem 25.08.2026**, vorher 0,55. Der Wechsel ist keine
Geschmacksfrage gewesen, sondern eine gemessene: Die automatische Prüfung, die vergleicht,
ob das erzeugte Bild dieselbe Geometrie zeigt wie der Entwurf, **kann unterhalb von rund
0,60 gar nicht bestehen** — es steht dann zu wenig Gebäude im Bild, als dass sich etwas
vergleichen liesse. Die alte 0,55 lag knapp darunter — und eine Woche lang galt die
Prüfung deshalb als zu streng eingestellt, obwohl die Kameraaufstellung schuld war.*
*Der Preis ist gestalterisch und gehört dazu: Ein höherer Deckungsgrad heisst weniger
Umgebung im Bild — mehr Bauwerk, weniger Ort.*

**Rahmen gegen Messen (der Rahmungsbruch)** — Der Fehler, der entsteht, wenn eine Kamera
auf etwas **anderes** ausgerichtet wird, als anschliessend geprüft wird.
*Der Fall aus diesem Projekt: Die Kamera stellte sich so, dass die **ganze Szene** gut ins
Bild passt — Gebäude *und* Geländeplatte. Geprüft wurde danach nur das **Gebäude**. Steht
es auf einer Platte mit zehnfacher Grundfläche, füllt es keine 2 % des Bildes, und die
Prüfung kann rechnerisch nicht bestehen. Sie meldete dann «durchgefallen», und alle sahen
auf das Bildmodell — die Ursache lag in der Kameraaufstellung.*
*Woran man es erkennt: Die Prüfung fällt nicht **manchmal** durch, sondern **immer**, und
ihr Wert wird umso schlechter, je grösser die Umgebung ist — nicht je schlechter das Bild.
Ein Mass, das an etwas hängt, das mit der gestellten Frage nichts zu tun hat, ist daran zu
erkennen, dass es sich mit der falschen Grösse ändert.*
*Die Abhilfe ist nicht, die Anforderung zu senken. Sie ist, beides auf dasselbe
auszurichten — und dafür muss überhaupt bekannt sein, wo das Gebäude ohne seine Umgebung
steht. Genau diese Angabe fehlte: Es wurde nur **eine** Umgrenzung mitgeführt.*

**Vorprüfung (Abbruch vor dem teuren Schritt)** — Eine Prüfung, die **vor** dem
aufwendigen Arbeitsschritt läuft und ihn ganz ausfallen lässt, wenn er nichts bringen
kann. Das Gegenstück zur Prüfung *danach*, die nur noch feststellt, dass etwas schiefging.
*Der Anlass in diesem Projekt ist ein Satz des Auftraggebers vom 25.08.2026: «Das sollte
gar nicht so weit kommen — die Modelle müssen prüfen, ob die Geometrie richtig ist, bevor
das Bild entsteht.» Bis dahin lief ein Auftrag, bei dem das Gebäude 17,5 % der Bildbreite
füllte, vollständig durch die Bilderzeugung — und das Bildmodell erfand dann eine
Nahaufnahme einer Fassade, weil ihm die Vorlage fehlte.*
*Damit eine Vorprüfung möglich ist, muss die entscheidende Angabe **früh genug** vorliegen.
Hier ist es die Umgrenzung des Gebäudes ohne seine Umgebung (siehe Rahmungsbruch): Sie
entsteht beim Aufbau der Szene, lange vor dem Bild — sie wurde nur bis dahin nirgends
weitergereicht.*

**Abbruchschwelle** — Der Wert, unterhalb dessen ein Arbeitsschritt gar nicht erst
begonnen wird. Zu unterscheiden von der **Prüfschwelle**, die über *bestanden* und
*durchgefallen* entscheidet: Die Abbruchschwelle entscheidet über *durchführen* und *sein
lassen*, und sie darf strenger sein.
*In diesem Projekt `BILDBREITE_ABBRUCH = 0.65`: Füllt das Gebäude weniger als 65 % der
Bildbreite, wird kein Bild erzeugt. Der Grund ist gemessen und überrascht — bei 30 %
Bildbreite fällt das Ergebnis **schlechter** aus als bei 17,5 %. Wo mehr Aufwand nicht
mehr zu einem besseren Ergebnis führt, ist der Aufwand nicht „wenigstens ein Versuch",
sondern verlorene Rechenzeit.*
*Weil der Verlauf nicht gleichmässig steigt, wird zwischen den gemessenen Stützstellen
**nicht** gerechnet: Ein Zwischenwert sähe aus wie eine Messung und wäre eine Erfindung.*

**Bauwerksbox (gegen Szenenbox)** — Zwei verschiedene Quader um dieselbe Szene. Die
**Szenenbox** umschliesst *alles*, was in der Datei steht, die Geländeplatte eingeschlossen.
Die **Bauwerksbox** umschliesst nur das, was gezeigt werden soll — das Gebäude.
*Warum der Unterschied zählt:* Die Kamera rahmt nach einer der beiden. Nach der Szenenbox
gerahmt hält sie den bestellten **Deckungsgrad** ein — und füllt ihn mit Gelände: Am
26.08.2026 gemessen sank der Anteil des Bauwerks am Bild dadurch von 17,3 % auf 7,9 %, und
im Beweisgang vom 09.09. schrumpfte es auf einen Streifen von 0,2795, wo 0,6985 bestellt
waren. *Der Bericht beschreibt, was dasteht; die Kamera rahmt, was gezeigt werden soll —
zwei Fragen, zwei Boxen.*
*Woran erkannt wird, was Gelände ist:* an einer **Namensregel** (Wörter wie «Gelände»,
«Terrain») und, seit dem 07.09.2026, ersatzweise an der **Form** — ein Körper, der flach
und weit ist, ist Gelände, auch wenn er anders heisst. Die Namensregel ist auf einem
verdeckten Namen blind; die Formregel nicht.

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

**Tiefenpass (Z-Pass) und Material-ID-Pass** — Zwei Nebenbilder, die derselbe Render
neben dem sichtbaren Bild ausgibt. Der **Tiefenpass** hält je Bildpunkt fest, wie weit das
Getroffene entfernt ist; der **Material-ID-Pass** hält fest, *welches* Material getroffen
wurde, als Kennfarbe. Beide beschreiben dieselbe Szene aus derselben Kamera und müssen
darum übereinstimmen: Wo der eine ein Bauteil meldet, kann der andere nicht Himmel melden.

*Am 03.09.2026 taten sie es doch. Der Material-ID-Pass läuft in diesem Projekt seit jeher
mit abgeschalteter Transparenz, der Tiefenpass nicht — sobald Glas im Modell ankam,
schrieb der Tiefenpass hinter jeder Scheibe, was dahinter liegt. Der Riegel dagegen ist*
`geometrie_qa.durchsichtiges_soll`.

**Transparenz-Bounce (`transparent_max_bounces`)** — Eine Einstellung des Renderers: Wie
oft darf ein Sehstrahl durch eine durchsichtige Fläche *hindurch*gehen, statt an ihr
stehenzubleiben? Bei `0` bleibt er an der ersten Fläche stehen — Glas verhält sich dann
wie eine Wand. Für das **sichtbare** Bild ist das falsch (eine Scheibe soll durchsichtig
aussehen), für **Kennbilder** ist es richtig: Eine Kennung oder eine Entfernung soll die
Scheibe beschreiben und nicht das, was dahinter steht.

*Genau darin lag der Rückschritt von Demolauf 17: dieselbe Einstellung, in zwei
Durchgängen desselben Renders verschieden gesetzt — und niemand hatte je gefragt, ob sie
zusammenpassen, weil es bis dahin gar kein Glas gab.*

**Alphakanal, `alphaMode: BLEND`** — Der vierte Wert neben Rot, Grün und Blau: wie
*deckend* eine Farbe ist. `1.0` heisst undurchsichtig, `0.25` heisst, dass ein Viertel der
eigenen Farbe und drei Viertel des Dahinterliegenden zu sehen sind. In einer glb-Datei
sagt das Feld `alphaMode` je Material, wie der Wert zu behandeln ist; `BLEND` heisst
«mischen», `OPAQUE` heisst «ignorieren, das Material ist dicht».

*In diesem Projekt das Merkmal, an dem geprüft wird, ob eine ausgeführte glb überhaupt
Fenster trägt: 700 IfcWindow in der Quelle und kein einziges Material mit `BLEND` heisst,
dass die Scheiben unterwegs verlorengegangen sind.*

**Kastenmittel (Box-Filter)** — Ein Bild verkleinern, indem jeder neue Bildpunkt der
**Mittelwert** des Rechtecks alter Bildpunkte wird, das er ersetzt. Die einfachere
Alternative, der **nächste Nachbar**, greift stattdessen einen einzelnen alten Punkt
heraus und wirft die übrigen weg.
*Seit dem 22.09.2026 auch beim Zusammensetzen einer Skizze auf ihre Unterlage — dort
gewichtet danach, wie stark jeder Bildpunkt deckt, damit ein durchsichtiger Grund nicht
als Farbe mitzählt.*

*Bei einer Gebäudeansicht ist der Unterschied sichtbar: Fenstersprossen und
Geländerstäbe sind oft nur einen Bildpunkt breit. Der nächste Nachbar lässt sie je nach
Raster ganz verschwinden oder springen; das Kastenmittel graut sie ab, und die Ansicht
behält ihre Struktur.*

**Splat (3D Gaussian Splatting)** — Eine Aufnahme eines Ortes, die nicht aus Flächen
besteht wie ein Modell, sondern aus Hunderttausenden kleiner, weicher, farbiger Wölkchen
(«Gaussians»). Jedes hat eine Lage, eine Grösse in drei Richtungen, eine Farbe und eine
Deckkraft; zusammen ergeben sie aus der Nähe ein Bild wie ein Foto, das man umrunden kann.
Entsteht meist aus vielen Fotos oder einem Video des Ortes.
*In diesem Projekt seit dem 08.10.2026 (Owner-Entscheid 76) die Umgebung neben dem
Bauwerk: Er läuft im Bild mit, gemessen wird er nicht. Testdaten erzeugt
`tools/make_test_splat.py` — ein Boden, eine Wand, ein Quader; ein echter Splat ist eine
Aufnahme eines echten Ortes und darf nach Regel 3 nicht ins Repo.*

**PLY (Dateiformat)** — Ein einfaches Dateiformat für Punkte: oben eine Textzeile je
Spalte («x», «y», «z», «opacity» …), darunter die Zahlen. Splats werden fast immer so
gespeichert. *Unser Erzeuger schreibt es mit der Standardbibliothek, Blender liest es mit
einem eingebauten Befehl.*

**Punktwolke** — Eine Menge einzelner Punkte im Raum, ohne Flächen dazwischen. Ein
Laserscan ist eine, ein Splat ist eine mit zusätzlichen Angaben je Punkt.
*Im Bild wird jeder Punkt des Splats zu einer kleinen Kugel — so kann der Renderer sie
zeichnen und ihren Abstand in die Tiefenkarte schreiben.*

**Punktwolke oder Splat (am Dateikopf erkannt)** — Beide kommen oft als PLY-Datei und
sehen in der Liste gleich aus. Eine **gewöhnliche Punktwolke** (Laserscan, Vermessung)
trägt je Punkt nur Lage und meist eine Farbe. Ein **Splat** (3D Gaussian Splatting, kurz
3DGS) trägt je Punkt dazu eine Deckkraft (`opacity`), eine Grösse in drei Richtungen
(`scale_0` bis `scale_2`) und seine Grundfarbe als Formel (`f_dc_0` bis `f_dc_2`). Welche
Angaben eine Datei hat, steht in ihren ersten Zeilen (dem Kopf) — dafür muss man die
Millionen Punkte dahinter nicht lesen. *In Visbox: Nur ein Splat kann als Umgebung ins Bild;
eine Punktwolke, die als Umgebung bestellt ist, wird mit dem Satz «PUNKTWOLKE OHNE
SPLAT-FELDER — als Kontext weggelassen» übergangen, und das Bild wird ohne sie gerechnet
(`kontext_netz.fehlende_splat_felder`, Geräteprobe R59). Die Oberfläche erkennt sie schon
vorher daran, dass alle ihre Punkte gleich gross sind, und schickt sie gar nicht mit.*

**Geometry Nodes, «Mesh to Points»** — Blenders Baukasten, um Geometrie mit verbundenen
Bausteinen umzuformen, statt sie von Hand zu bearbeiten. Der Baustein «Mesh to Points»
macht aus jedem Eckpunkt eines Netzes einen Punkt mit eigenem Radius.
*Damit wird der eingelesene Splat (in Blender zuerst ein Netz ohne Flächen) zur
Punktwolke, die Cycles als Kugeln zeichnet.*

**SH-Grad 0 (Grundfarbe eines Gaussians)** — Die Farbe eines Splat-Wölkchens ist als
Formel gespeichert, die je nach Blickrichtung etwas anders ausfällt («Kugelflächen­
funktionen», englisch *spherical harmonics*, SH). Grad 0 ist der Teil, der aus jeder
Richtung gleich ist — die Grundfarbe. Gerechnet: `0,5 + 0,2821 · f_dc`, auf 0 bis 1
begrenzt. *Wir lesen nur ihn: Ein Bild aus einer Richtung braucht den Glanz je Richtung
nicht, und Kugeln im Renderer könnten ihn nicht tragen.*

**Deckkraft eines Gaussians (Opazität, Sigmoid)** — Wie undurchsichtig ein Wölkchen ist,
von 0 (unsichtbar) bis 1 (dicht). In der Datei steht sie verschlüsselt als beliebige Zahl;
die **Sigmoid**-Funktion `1 / (1 + e^−x)` macht daraus den Wert zwischen 0 und 1.
*Unter 0,10 werfen wir ein Wölkchen weg (gesetzt, nicht gemessen): Im Bild wird jedes zu
einer festen Kugel, und ein Hauch Rauschen in der Luft würde sonst zur Wand vor dem
Bauwerk.*

**Splat-Brücke (Splat → Netz)** — Der Weg, auf dem aus einer Splat-Aufnahme eine gewöhnliche Fläche aus
Dreiecken wird: Der Splat wird aus vielen Richtungen fotografiert (richtig, mit seinen weichen Wölkchen), aus
jedem Bild wird abgelesen, wie weit die Dinge entfernt sind, und diese Entfernungen werden zu einer einzigen
Oberfläche zusammengesetzt. Die Fläche trägt die Farben der Aufnahme. Ein Programm, das Flächen zeichnen kann
(Blender), zeichnet sie dann ohne Lücken. *Im Projekt:* Entscheid 79, `seams.splat_zu_netz`,
`runners/splat_zu_netz_runner.py`; ersetzt die Kugel-Notlösung, die das «Konfetti» verursachte.

**Rastern (Rasterization)** — Ein 3D-Ding in ein Bild aus Bildpunkten verwandeln: für jedes Teil ausrechnen,
auf welche Bildpunkte es fällt und mit welcher Farbe. Das Gegenstück zum Strahlenverfolgen, bei dem für jeden
Bildpunkt ein Sehstrahl in die Szene geschickt wird; Rastern ist schneller. *Im Projekt:* gsplat rastert die
Wölkchen eines Splats auf der Grafikkarte, weich überlagert und in ihrer richtigen Form und Drehung
(`gsplat.rasterization`).

**Erwartete Tiefe** — Bei einem Splat liegt hinter einem Bildpunkt oft nicht eine Fläche, sondern mehrere
halbdurchsichtige Wölkchen hintereinander. Die erwartete Tiefe ist ihr gewichteter Mittelwert: Jedes zählt so
viel, wie es zur Farbe des Bildpunkts beiträgt. So bekommt jeder Bildpunkt **eine** Entfernung, auch wenn
mehrere Wölkchen beteiligt sind. *Im Projekt:* `render_mode="RGB+ED"` in gsplat («ED», expected depth);
Bildpunkte, die zu weniger als der Hälfte gedeckt sind, gelten als leer (`kontext_netz.DECKKRAFT_LEER`).
*Ihre Schwäche (13.10.2026, `auf-20261013-276`):* Steht eine halbdurchsichtige Wolke vor einer Wand,
liegt der Mittelwert irgendwo dazwischen, in der Luft — darum der **Tiefenfilter**. gsplat rechnet sie
als akkumulierte Tiefe geteilt durch die **akkumulierte Deckkraft**; ein Vergleich der beiden prüft
also nichts.

**TSDF (Verschmelzen von Tiefenbildern)** — Ein Verfahren, viele Tiefenbilder aus verschiedenen Richtungen zu
einer Oberfläche zusammenzusetzen. Der Raum wird in kleine Würfel (Voxel) geteilt; jeder merkt sich, wie weit
er vor oder hinter der gesehenen Fläche liegt, gemittelt über alle Bilder, die ihn sehen. Wo der Wert von
«davor» zu «dahinter» wechselt, liegt die Oberfläche; daraus entsteht ein Netz aus Dreiecken. Der Name kommt vom
Englischen *truncated signed distance function* — gekappter, vorzeichenbehafteter Abstand. *Im Projekt:* Open3D
(`VoxelBlockGrid`) in der Splat-Brücke, 7-cm-Würfel (`kontext_netz.VOXEL_M`, gesetzt; 5 cm brachten Open3D am
echten Splat zum Absturz, siehe **Blockwache**).

**Voxel** — Ein kleiner Würfel in einem dreidimensionalen Raster, so wie ein Bildpunkt ein kleines Quadrat in
einem Bild ist. *Im Projekt:* die Rechenzellen der TSDF; ihre Kantenlänge bestimmt, wie fein das Netz der
Umgebung wird und wieviel Speicher es braucht.

**Eckpunktfarbe (Vertexfarbe)** — Eine Farbe, die nicht als Bild auf eine Fläche geklebt ist, sondern an jedem
Eckpunkt eines Netzes steht; dazwischen wird übergeblendet. Einfacher als eine Textur, und für ein dichtes Netz
genau genug. *Im Projekt:* So trägt das Netz der Splat-Brücke die Farben der Aufnahme; Blender zeichnet sie als
leuchtende Farbe, ohne sie neu zu beleuchten. Für das Netz aus RealityScan seit Fassung 3 nur noch der Rückfall:
An Fensterwänden war eine Farbe je Ecke zu grob, das Bild unlesbar (HomeStation, 14.10.2026).

**Textur** — Ein Bild, das auf die Flächen eines Netzes geklebt wird wie eine Tapete. Das Netz gibt die Form,
die Textur die Farbe und die Feinheiten — Fensterrahmen, Fugen, Schrift —, die viel kleiner sein können als
die Dreiecke darunter. *Im Projekt:* Seit Fassung 3 der RealityScan-Brücke (14.10.2026) trägt das Umgebungsnetz
eine Textur aus den Fotos statt Eckfarben; gemessen war das Bild damit so scharf wie der Splat oder schärfer.

**Himmelsbild (HDRI)** — Ein Rundumfoto des Himmels und der Umgebung, so aufgenommen, dass es nicht nur
Farben, sondern auch die echte Helligkeit trägt (die Sonne ist darin tausendmal heller als eine Wolke). Legt
man es als «Welt» um ein Modell, beleuchtet es das Modell so, wie der Himmel am Aufnahmeort es getan hätte —
mit Licht, Schatten und Spiegelungen in einem. *Im Projekt:* acht Himmelsbilder von Poly Haven (frei von
Rechten, CC0), eines je Stimmung; sie liegen nur am Heim-PC, nie im Repo. Fehlt eines, wird der Auftrag mit
dessen Namen abgewiesen (Entscheid 113). `src/aiimaging/stimmung.py`.

**Stimmung (Knoten)** — Die Wahl, unter welchem Himmel und Licht ein Bild entsteht: Morgen, Mittag, Abend,
Blaue Stunde, bedeckt, Nebel, Winter oder Weiss. Jede Stimmung bringt ein Himmelsbild und einen Satz für das
Bildmodell mit. Der Himmel lässt sich drehen (woher das Licht kommt) und heller oder dunkler stellen. Mit
Himmelsbild gibt es keine zusätzliche Sonnenlampe — sonst käme das Licht doppelt —, ausser eine Sonne ist
ausdrücklich bestellt. *Im Projekt:* `render.environment`, gerechnet seit dem 20.10.2026 (Entscheid 110).

**Gipsmodell (Stimmung «Weiss»)** — Alle Flächen des Modells bekommen dasselbe matte Weiss, wie ein
Arbeitsmodell aus Gips oder Karton. Übrig bleiben nur Form, Licht und Schatten. *Im Projekt:* Entscheid 113;
der Heim-PC tauscht dafür jedes Material gegen ein diffuses Weiss (siehe **Principled BSDF**: hier genügt
die einfachere «Diffuse»-Fläche ohne Glanz).

**Principled BSDF** — In Blender die eine «Allzweck-Oberfläche», mit der fast jedes Material beschrieben wird:
Farbe, wie rau oder glänzend, wie metallisch, wie durchsichtig. BSDF ist die Fachabkürzung für «wie eine Fläche
das Licht zurückwirft». *Im Projekt:* Für jede gewählte Materialwahl baut der Heim-PC eine solche Oberfläche
aus den Bildern des Materials (Farbe, Rauheit, Höhe) — `_material_aus_wahl` im Runner.

**Box-Projektion** — Eine Art, ein Musterbild (Backstein, Beton) auf ein Modell zu legen, ohne das Modell vorher
aufzuschneiden (siehe **Abwicklung**): Das Bild wird von den drei Hauptrichtungen her aufgeworfen, wie mit drei
Diaprojektoren von vorn, von der Seite und von oben, und an schrägen Flächen weich überblendet. Vorteil: geht mit
jedem Modell. Nachteil: an schrägen Flächen können Nähte sichtbar werden. *Im Projekt:* Überblendung 0,2, der
Massstab in Metern (ein Bild deckt so viele Meter ab), drehbar; ein nicht quadratisches Bild wird nach seinem
Seitenverhältnis gestreckt.

**Relief (Bump)** — Eine Fläche sieht rau oder gefugt aus, obwohl sie geometrisch glatt bleibt: Ein
Graustufenbild sagt je Punkt «höher» oder «tiefer», und das Licht wird so berechnet, als wäre die Fläche dort
gewölbt. Die Form selbst ändert sich nicht — die Silhouette bleibt gerade. *Im Projekt:* `relief` 0 bis 1 an
der Materialwahl (Vorgabe 0,6), aus dem Höhenbild des Materials; eine «Normal-Map» (ein Bild, das die
Neigung statt der Höhe speichert) geht mit der Box-Projektion nicht, weil dort die Richtung «nach rechts im
Bild» je Fläche fehlt.

**Materialwahl (je Bauteil-Art)** — Die Bestellung «Fassade in Sichtbeton, Boden in Stampflehm»: je Art ein
Material aus der Bibliothek, mit Massstab, Drehung, Relief und wahlweise einer Tönung (eine Farbe, die zu
einem Anteil darübergemischt wird). Nicht gewählte Arten behalten das Material des Modells, das Gelände bleibt
immer, wie es ist. *Im Projekt:* `render.materialien`, elf Materialien von ambientCG (CC0) am Heim-PC,
`src/aiimaging/materialwahl.py`.

**Bauteil-Art** — Welche Rolle ein Teil des Modells spielt: Fassade, Dach, Fenster, Boden oder «übrige» (Türen,
Treppen, Stützen …), dazu das Gelände. Erkannt am Vermerk, den KosmoOrbit jedem Bauteil mitgibt, oder am Namen
aus der IFC-Datei («IfcWall_…» ist eine Wand). *Im Projekt:* `materialwahl.art_von`, mit zwei Tabellen, die
das Programm drüben nachbaut.
 *Nachgeführt 22.10.2026 (N5):* Trägt ein Teil weder Vermerk noch IFC-Namen (eine glb aus einem anderen Programm),
zählt zuletzt ein Wort im Namen des Teils: «Wand»/«Fassade» → Fassade, «Dach» → Dach, «Fenster» → Fenster,
«Bodenplatte»/«Geschossdecke» → Boden. Sagt auch der Name nichts, ist es ein *Bauteil ohne Art* (siehe dort).

**Bauteil ohne Art** — Ein Teil des Modells, über das die Datei nichts sagt: kein Vermerk, kein IFC-Name, kein Wort wie
«Wand» oder «Dach» im Namen — etwa ein Baum, eine Terrasse oder ein Betonsockel aus einem anderen Zeichenprogramm. Es
zählt als «übrige», behält aber sein *benanntes Material* aus der Datei, auch wenn für «übrige» ein Material gewählt
ist; nur Flächen ohne sprechenden Materialnamen bekommen die Wahl. *Wozu:* Im Mac-Demolauf vom 22.10.2026 lag sonst die
Holzlattung auf Beton, Bäumen und Terrasse. *Im Projekt:* `materialwahl.art_und_herkunft` (Herkunft «unbestimmt»),
Bericht `objekte_ohne_art` und `datei_material_behalten`; Protokoll 74 §247.

**Benanntes Material (aus der Datei)** — Ein Material im Modell, dessen Name etwas sagt («Beton», «Baum_Rinde»,
«Terrasse_Holz») — im Gegensatz zu den Vorgabenamen, die Zeichenprogramme selbst vergeben («Material.001», «Default»,
«lambert1»). Was der Name bedeutet, deutet Visbox nicht; er wird nur nicht überschrieben. *Im Projekt:*
`materialwahl.ist_benanntes_material`.

**Rauheit (eines Materials)** — Wie matt oder glänzend eine Oberfläche ist, als Zahl von 0 (spiegelglatt) bis 1 (ganz
matt). Glas mit Rauheit 1 sieht aus wie Milchglas: kein Durchblick, keine Spiegelung. *Im Projekt:* Seit dem
22.10.2026 bekommt jedes Material mit *Durchlass* höchstens 0,05 — in der glb der IFC-Umwandlung
(`glb_nachtragen`) und in Blender (`_glas_klar`, Bericht `glas_klar`); Anlass Ergebnis auf-20261022-332, wo der
IFC-Stil 1,0 mitbrachte.

**Ohne Bauteil / nur behalten (im Materialbericht)** — Zwei Gründe, warum eine gewählte Art im Bild nichts verändert,
beide gewollt: *ohne Bauteil* — die Datei hat kein Teil dieser Art (Dach gewählt, aber kein Dach im Modell); *nur
behalten* — es gibt solche Teile, aber alle ihre Flächen blieben wie in der Datei (ein Fenster, das nur aus Glas
besteht, oder benannte Materialien eines Bauteils ohne Art). Bis zum 22.10.2026 stand beides zusammen unter
«nicht getroffen», was sich wie ein Fehler las. *Im Projekt:* Blender-Bericht `materialien.ohne_bauteil`,
`materialien.nur_behalten`, `lesart`.

**Fuge (im Material)** — Der dunkle, etwas vertiefte Spalt zwischen zwei Latten. Das Bild der Holzlattung zeigt
eine geschlossene Schalung; die Fugen werden darum beim Rechnen hineingeschnitten — alle 7 cm (5 cm Latte,
2 cm Fuge), dunkler gefärbt und im Relief vertieft. *Im Projekt:* `fugen` am Bibliothekseintrag
«holzlattung-fichte».

**Abwicklung (UV-Abwicklung)** — Das Netz wird gedanklich aufgeschnitten und flach ausgelegt, wie ein
Schnittmuster aus Stoff, damit jedes Dreieck seinen Platz auf einem flachen Bild bekommt. Die Lage auf dem Bild
heisst **UV** (zwei Zahlen je Ecke, «u» nach rechts, «v» nach oben, damit sie nicht mit x, y, z verwechselt
werden). *Im Projekt:* RealityScan wickelt mit `-unwrap` ab — und nur mit einer **Abwicklungsdatei**
(`betrieb/realityscan/unwrap-optimal.xml`); die Schalter in der Befehlszeile wirkten nicht.

**Texel** — Ein Bildpunkt der Textur, so wie ein Pixel ein Bildpunkt des Bildschirms ist. Die Texelgrösse sagt,
wie viel Fläche am Gebäude ein Texel deckt — je kleiner, desto schärfer. *Im Projekt:* mit der
Abwicklungsdatei etwa 3 mm je Texel auf 3–4 Bildern zu 8192 × 8192, mit den Vorgaben von RealityScan 7.6 mm.

**OBJ und MTL (Dateiformate)** — Zwei einfache Textdateien für ein texturiertes Netz. Das **OBJ** zählt die
Ecken (`v`), ihre Lage auf der Textur (`vt`) und die Flächen auf (`f`, je Ecke «Nummer der Ecke / Nummer der
Texturlage»); die **MTL** sagt, welches Bild zu welchem Material gehört (`map_Kd`). Die Bilder liegen als
eigene Dateien daneben. *Im Projekt:* Das Netz aus RealityScan kommt seit Fassung 3 als OBJ + MTL + PNG; die
Brücke nimmt den **Deckel** heraus, nummeriert neu und schreibt die Prüfsumme der Bilder ins OBJ
(`realityscan.bereinige_obj`).

**Insel (im Netz)** — Ein kleines Netzstück, das mit dem Rest nicht verbunden ist — meist ein Fetzen aus einer
einzelnen falschen Tiefe. *Im Projekt:* Die Splat-Brücke entfernt Inseln unter 200 Dreiecken
(`kontext_netz.INSEL_MIN_DREIECKE`, gesetzt). Am echten Splat waren es 42 % der Dreiecke — dort keine falschen
Tiefen, sondern schlecht gesehene echte Fläche. Die Zahl bleibt absolut (13.10.2026): Ein Anteil wüchse mit der
Szene und würfe mehr weg; geheilt werden die Fetzen durch bessere Blickwinkel (**Kamerapose**).

**CUDA** — Die Programmierschnittstelle von NVIDIA, über die Programme auf der Grafikkarte rechnen. Proprietär
und nur auf NVIDIA-Karten. *Im Projekt:* gsplat rendert nur mit CUDA; darum läuft die Splat-Brücke am Heim-PC,
nicht in der Cloud-Sitzung.

**Ersatzrenderer (cpu-probe)** — Ein absichtlich einfacher Zeichner für Proben: Er malt jedes Wölkchen als
kleines Quadrat und behielt bis zum 13.10.2026 je Bildpunkt das nächste; seither mischt er wie gsplat
von vorn nach hinten und gibt **erwartete Tiefe** und **akkumulierte Deckkraft** zurück. Die Tiefe nimmt er seit dem 13.10.2026 dort, wo der
Sehstrahl die flache Scheibe des Wölkchens trifft — vorher trug jedes Quadrat die Tiefe seiner Mitte, und bei
flachem Blick lag der Boden im Netz drei Würfel zu hoch. Er sieht schlechter aus als gsplat, braucht aber keine
Grafikkarte — so lässt sich der Rest der Brücke (Blickwinkel, Verschmelzen, Datei) überall prüfen.
*Im Projekt:* `--renderer cpu-probe`; ein so entstandenes Netz trägt `nur_probe: true` und gilt nie als echtes.

**COLMAP** — Ein freies Programm (BSD-Lizenz, von der ETH Zürich mitentwickelt), das aus vielen Fotos eines Ortes
herausrechnet, wo jede Kamera stand und wohin sie blickte, und dazu eine lockere Punktwolke der gesehenen
Flächen. Das Ergebnis liegt als kleiner Satz Dateien in einem Ordner `sparse/0` (`cameras`, `images`, `points3D`,
seit Fassung 4 auch `rigs` und `frames`). Splat-Trainingsprogramme wie Brush lernen den Splat auf genau diesen
Kameras. *Im Projekt:* Die Splat-Brücke liest diese Dateien selbst, ohne Zusatzprogramm
(`kontext_netz.lies_aufnahme`) — das fertige Python-Paket `pycolmap` bringt GPL-Teile mit und ist darum nicht
zugelassen (Regel 1).

**Kamerapose (Pose)** — Wo eine Kamera steht und wohin sie blickt, zusammen: ein Ort und eine Drehung. COLMAP
schreibt sie als «Welt → Kamera»: wie ein Punkt der Welt in die Sicht der Kamera umgerechnet wird. *Im Projekt:*
Seit dem 13.10.2026 rendert die Splat-Brücke den Splat aus den Posen der Aufnahme, statt aus gesetzten
Blickwinkeln — der Splat ist nur dort verlässlich, wo die Aufnahme ihn sah. Die Pose geht unverändert an gsplat,
weil beide dieselbe Achsenrichtung benutzen (x rechts, y unten, z Blick; `kontext_netz.pose_zu_ansicht`).

**Rig (Kamera-Rig)** — Mehrere Kameras, fest miteinander verbunden, die gleichzeitig auslösen — etwa vier
Kameras nach vorn, hinten, links und rechts auf einem Gestell. Weil sie starr verbunden sind, genügt es, die Lage
des Gestells je Augenblick zu kennen. *Im Projekt:* Die Aufnahme der HomeStation ist ein Rig aus vier Kameras,
je 240 **Augenblicke**; die Brücke nimmt höchstens 240 Bilder, gleichmässig über die Augenblicke verteilt,
jeweils alle vier Kameras (`kontext_netz.AUFNAHME_BLICKE_MAX`, gesetzt).

**Augenblick (Frame)** — Ein Auslösezeitpunkt eines **Rigs**: die Bilder, die alle Kameras im selben Moment
gemacht haben. COLMAP 4 führt sie in der Datei `frames`. *Im Projekt:* die Einheit, in der die Splat-Brücke Bilder
aus der Aufnahme auswählt — ganze Augenblicke, nie einzelne Kameras daraus.

**Gleichheitsprüfung (Aufnahme ↔ Splat)** — Die Probe, ob eine Aufnahme und ein Splat im selben
Koordinatensystem liegen, bevor ihre Kameras benutzt werden. Gemessen wird, wie weit die Punkte der Aufnahme von
den nächsten dichten Wölkchen des Splats liegen (Median und 90-%-**Perzentil**, als Anteil der Ausdehnung) und
ob die Kameras im Bereich des Splats stehen. *Im Projekt:* Liegt etwas über der Schwelle, nimmt die Brücke den
Ring und schreibt den Grund in den Bericht. Am echten Splat lag der Median bei 0,25 % der Ausdehnung, die
Schwelle steht bei 1 % (`kontext_netz.GLEICH_MEDIAN_MAX`, gesetzt).

**Deckung (des Netzes)** — Welcher Anteil der dichten Wölkchen eines Splats nahe an einer Fläche des daraus
gerechneten Netzes liegt (höchstens drei **Voxel** entfernt). Ein Mass für die Löcher, ohne Bild und ohne
Kamera. *Im Projekt:* `deckung.anteil` im Bericht der Splat-Brücke; am synthetischen Strassenraum 71 % mit dem
Ring gegen 96 % mit den Kameras der Aufnahme. Gezählt wird seit dem 13.10.2026 eine
**Zufallsstichprobe mit festem Startwert** über alle dichten Wölkchen.

**Blockwache** — Eine Zählung während des Verschmelzens (**TSDF**): Die Würfel liegen in Blöcken, und Open3D 0.20
stürzt beim Herausziehen des Netzes ab, wenn zu viele Blöcke belegt sind (am echten Splat bei rund 300 000). Die
Wache zählt nach jedem Bild; wird es zu viel, beginnt die Brücke mit grösseren Würfeln neu und sagt es im
Bericht. *Im Projekt:* `kontext_netz.BLOECKE_MAX` (250 000, gesetzt), `voxel.vergroessert` im Bericht.

**Statisch eingebunden (Bibliothek)** — Eine Bibliothek, die beim Übersetzen fest in eine andere Programmdatei
hineinkopiert wurde, statt daneben als eigene Datei zu liegen. Von aussen sieht man sie nicht — aber ihre Lizenz
reist mit. *Im Projekt:* Das Python-Paket `pycolmap` (selbst BSD) enthält so Teile der Rechenbibliothek
SuiteSparse unter GPL; darum liest die Splat-Brücke COLMAP mit eigenem Code (13.10.2026).

**RealityScan-Brücke (Fotos → Netz)** — Der Weg, auf dem Visbox die Umgebung nicht aus dem Splat,
sondern direkt aus den **Fotos** der Aufnahme zu einem farbigen Netz rechnen lässt — vom Programm Epic
RealityScan, das der Nutzer selbst installiert hat (**Fremdprogramm**). Visbox schreibt die Aufnahme in
die Form, die RealityScan liest, startet es, prüft das Ergebnis und nimmt es nur, wenn es am richtigen
Ort liegt. *Im Projekt:* `aiimaging/realityscan.py`, Owner-Entscheid 81 (13.10.2026); eingeschaltet nur
mit der Variable `AIIMAGING_REALITYSCAN`, sonst bleibt der offene Weg. Anleitung:
`betrieb/REALITYSCAN_BRUECKE.md`. Seit dem 14.10.2026 (Messung `auf-20261013-278`, Owner-Entscheid)
der Weg fürs Umgebungsnetz: 93 % der Umgebung gedeckt statt 10 % beim offenen Weg.

**Bewegungssensor (IMU)** — Ein kleiner Messbaustein in der Kamera, der tausendmal je Sekunde
misst, wie stark sie beschleunigt und sich dreht. Aus der Beschleunigung lässt sich zurückrechnen,
wie weit die Kamera in Metern gegangen ist — und damit, wie gross die gescannte Szene in echt ist.
*Im Projekt:* Vorschlag der HomeStation (14.10.2026) für den **Massstab** des Splats; gebaut wird die
Stufe bei KosmoPrepare, Visbox liest nur das Ergebnis.

**Massstab (des Splats)** — Wie viele echte Meter einer Einheit des gescannten Modells entsprechen.
Ein Scan aus Fotos kennt von sich aus keine Meter, nur Verhältnisse. *Im Projekt:* KosmoPrepare
schreibt ihn mit Unsicherheit, **Gegenprobe** (eine zweite, unabhängige Schätzung) und einer
**Ampel** (grün: still übernommen; gelb: übernommen, um ein **Kontrollmass** — eine von Hand gemessene
Länge am Bau — gebeten; rot: nicht übernommen) in die Verortung; Visbox sagt die Ampel als Satz im
Urteil (`kosmo_szene.massstab_aus_verortung`). Ein Handmass gewinnt immer. **Drift** heisst, dass der
Massstab entlang des Wegs der Kamera nicht gleich bleibt.

**Selbst-Aktualisieren (Updater)** — Der Teil einer App, der nachsieht, ob es eine neuere Fassung gibt,
sie auf Wunsch lädt, prüft, die alte ersetzt und die App neu startet — wie man es von Browsern kennt. *Im
Projekt:* in der Mac-App von Visbox selbst gebaut (Entscheid 84, seit 87 mit einem Klick und Neustart von
selbst); für KosmoOrbit empfohlen: das Updater-Plugin von Tauri. Eine App, die das noch nicht kann, muss
einmal von Hand ersetzt werden.

**AppImage** — Eine Form, ein Linux-Programm als **eine einzige Datei** auszuliefern, die man ohne
Installation starten kann. Weil es nur eine Datei ist, kann das Programm sie selbst gegen eine neuere
tauschen. *Im Projekt:* die Linux-Form, in der sich KosmoOrbit über den Tauri-Updater selbst ersetzen
könnte (ein `.deb`-Paket kann er nicht ersetzen).

**Prozessgruppe** — Startet ein Programm weitere Programme, bilden sie zusammen eine Familie, die das
Betriebssystem als eine Gruppe führen kann. Wer die **ganze Gruppe** beendet, trifft auch die Kinder und
Enkel; wer nur das erste Programm beendet, lässt sie weiterlaufen. *Im Projekt:* RealityScan läuft unter
Wine — beendete die Frist nur Wine, blieb RealityScan als **verwaister Prozess** (ein Programm ohne den,
der es gestartet hat) stehen und hielt die Grafikkarte (278). Die Brücke startet es darum in eigener
Gruppe und beendet bei Ablauf der Frist alle (`realityscan._starte_gruppe`). Nicht zu verwechseln mit
der **Waise** der Auftragsliste.

**Deckel (im Netz)** — Wenige, sehr grosse Dreiecke, mit denen RealityScan Bereiche schliesst, für die
es keine Fotos hat — etwa eine waagrechte Platte über die ganze Szene. Sie sehen aus wie eine Wand oder
ein Dach, wo keines ist, und würden im Bild das Gebäude verdecken. *Im Projekt:* am Heim-PC 123 Dreiecke
mit 59 % der Fläche (278); `realityscan.bereinige_export` nimmt jedes Dreieck weg, dessen längste Kante
mehr als 2,5 % der Netzgrösse misst (bis M3 waren es 5 %, und Reste blieben im Bild); für das texturierte
OBJ dasselbe in `realityscan.bereinige_obj`.

**Farbe als Ganzzahl oder Kommazahl (uchar / float)** — Eine Farbe je Ecke kann auf zwei Arten in der
Datei stehen: als ganze Zahl von 0 bis 255 (`uchar`) oder als Kommazahl von 0 bis 1 (`float`). Ein
Programm, das die eine Art erwartet und die andere bekommt, liest «0.6» als fast nichts von 255 — das
Netz wird schwarz. *Im Projekt:* RealityScan schreibt Kommazahlen, Blender 5.2 liest sie so falsch; die
Brücke schreibt die Farben darum auf ganze Zahlen um (278).

**Wine** — Ein freies Programm, das Windows-Programme unter Linux laufen lässt, ohne Windows: Es
übersetzt die Aufrufe des Windows-Programms an das Betriebssystem in die von Linux. Dateien sieht das
Windows-Programm dabei auf einem Laufwerk `Z:`, das für das ganze Linux-Dateisystem steht — aus
`/mnt/lauf/images` wird `Z:\mnt\lauf\images`. *Im Projekt:* RealityScan für Linux ist ein
Windows-Programm, das sein eigenes Wine mitbringt; Visbox schreibt jeden Pfad für RealityScan so um
(`realityscan.wine_pfad`). Wine gehört zur Installation des Nutzers, nicht zu Visbox (`NOTICE`).

**Export-Parameterdatei (RealityScan)** — Eine kleine Datei, in der RealityScan festhält, *wie* es ein
Netz speichert: welches Dateiformat, ob mit Farben, in welchen Koordinaten. Sie wird einmal im Programm
mit der Maus eingestellt und gespeichert und danach bei jedem Lauf wiederverwendet. *Im Projekt:* Ihr
Aufbau ist nicht öffentlich beschrieben, darum erfindet Visbox sie nicht — der Owner legt sie an
(«PLY mit Eckpunktfarben, Koordinaten unverändert») und nennt ihren Ort in
`AIIMAGING_REALITYSCAN_EXPORT_XML`. Ihr Inhalt steht im Speicherschlüssel: Eine andere Einstellung
ergibt ein anderes Netz.

**COLMAP-Textformat** — Dieselben Angaben wie die **COLMAP**-Dateien einer Aufnahme (Kameras, Posen,
Punkte), aber als lesbarer Text statt als Bytes: eine Zeile je Kamera, zwei je Bild, eine je Punkt.
Ältere Programme lesen nur diese Form, und sie kennt kein **Rig** — jedes Bild trägt seine eigene Pose.
*Im Projekt:* RealityScan liest eine Aufnahme nur so; `realityscan.colmap_als_text` schreibt sie aus der
Binärform um, und eine Probe liest sie mit dem eigenen Leser zurück und vergleicht jede Pose.

**Lageprüfung (Netz ↔ Aufnahme)** — Die Probe, ob ein Netz, das ein fremdes Programm geliefert hat,
dort liegt, wo die Aufnahme liegt — nicht verschoben, gedreht oder in anderem Massstab. Gezählt wird,
wie viele Punkte der Aufnahme eine Ecke des Netzes in ihrer Nähe haben, und ob beide etwa gleich gross
sind. *Im Projekt:* `realityscan.lage_befund`; liegt das Netz aus RealityScan daneben, wird es nicht
benutzt, und der offene Weg läuft (Grund `lage`). Die Schwellen sind gesetzt, nicht gemessen.

**Umeyama-Verfahren** — Eine Rechnung, die aus Paaren zusammengehöriger Punkte in zwei Koordinatensystemen
die eine Verschiebung, Drehung und Massstabsänderung findet, die das eine am besten auf das andere legt.
*Im Projekt:* Damit hat die HomeStation nachgewiesen, dass Splat und Aufnahme im selben System liegen
(13.10.2026). Für ein neu gelagertes Netz aus RealityScan ist es eine offene Frage, nicht gebaut.

**Akkumulierte Deckkraft (alpha)** — Wie viel von einem Bildpunkt insgesamt zugedeckt ist, wenn
mehrere halbdurchsichtige Wölkchen hintereinander liegen: 0 heisst, man sieht ganz hindurch, 1 heisst,
nichts kommt mehr durch. Zwei Wölkchen mit je halber Deckkraft decken zusammen drei Viertel. *Im
Projekt:* gsplat gibt sie je Bildpunkt mit; die Splat-Brücke nimmt eine Tiefe nur, wo sie mindestens
0,7 beträgt (`kontext_netz.DECKKRAFT_TIEFE`, gesetzt). Seit dem 13.10.2026 rechnet auch der
**Ersatzrenderer (cpu-probe)** sie aus.

**Tiefenfilter (Splat-Brücke)** — Ein Sieb für die Tiefenbilder, bevor sie zum Netz verschmolzen
werden (**TSDF**): Ein Bildpunkt, dessen Tiefe nicht trägt, bekommt die Tiefe null und wird
übergangen. Sechs Siebe, jedes für sich gezählt: zu wenig **akkumulierte Deckkraft**, **Sprenkel**,
**Streuung entlang des Strahls**, **Nahbereich**, der **Weg der Aufnahme** und die **Maske der
Aufnahme**. *Im Projekt:* eingeführt
am 13.10.2026, nachdem am echten Splat gesprenkelte Tiefe und die gefilmte Person das Netz in fast
500 000 Stücke zerlegt hatten (`auf-20261013-276`); der Bericht nennt je Sieb den Anteil der
verworfenen Bildpunkte (`tiefenfilter.je_filter`).

**Sprenkel (in der Tiefe)** — Einzelne Bildpunkte, deren Tiefe gegen ihre Nachbarn springt, wie
Salz und Pfeffer in einem Bild. Eine echte Fläche ändert ihre Tiefe von Punkt zu Punkt gleichmässig,
auch schräg gesehen; ein Sprenkel springt gegen alle Nachbarn. Erkannt wird er am **Median** der
acht Nachbarn und des Punkts selbst: Weicht die Tiefe mehr als 5 % davon ab, wird sie verworfen
(`kontext_netz.TIEFE_SPRUNG_REL`, gesetzt). Der Median ist der mittlere Wert der Reihe — ein
einzelner Ausreisser verschiebt ihn nicht.

**Streuung entlang des Strahls** — Wie weit die Wölkchen, die zu einem Bildpunkt beitragen, in der
Tiefe auseinanderliegen. Liegen sie alle auf einer Fläche, ist die Streuung klein; steht eine
halbdurchsichtige Wolke vor einer Wand, ist sie gross — und die **erwartete Tiefe** liegt dann in der
Luft zwischen beiden. Gerechnet als Wurzel aus «Mittel der Quadrate minus Quadrat des Mittels»,
mit denselben Gewichten wie die erwartete Tiefe. *Im Projekt:* Ein zweiter Durchgang von gsplat
mischt statt der Farbe die Tiefe und ihr Quadrat; streut die Tiefe um mehr als 10 % ihres Werts,
wird sie verworfen (`kontext_netz.TIEFE_STREUUNG_REL`, gesetzt, 13.10.2026). Gefunden am
synthetischen Strassenraum: Gegen die Wolke vor der Kamera halfen weder Nahbereich noch Masken.

**Nahbereich (der Kamera)** — Was näher als 1,5 m vor der Kamera liegt (`kontext_netz.NAH_MIN_M`,
gesetzt): Dort steht bei einer Aufnahme meist der Mensch, der filmt — Körper, Arm, Stange. Seine
Tiefe wird verworfen. *Im Projekt:* in Metern der Welt angegeben und über den Massstab der
Verortung in die Einheiten des Splats umgerechnet (am echten Splat ist eine Einheit rund 6 m).

**Weg der Aufnahme (Filter)** — Der Raum, durch den die Kamera getragen wurde, ist leer — ausser dem
Menschen, der sie trug. Darum wird jede Tiefe verworfen, die näher als 1,2 m an **irgendeiner**
Kamera der Aufnahme liegt, nicht nur an der, aus der gerade gerendert wird
(`kontext_netz.WEG_MIN_M`, gesetzt). *Warum es ihn braucht:* Die Person steht in jedem
**Augenblick** woanders; der **Nahbereich** und die Maske nehmen nur die Person des eigenen
Augenblicks weg, die der Nachbaraugenblicke sieht die Kamera ein paar Meter entfernt. *Warum 1,2 m:*
Die Kugel um die Kamera auf Brusthöhe soll den Boden darunter nicht berühren.

**Maske der Aufnahme (Personenmaske)** — Zu jedem Foto einer Aufnahme ein Schwarz-Weiss-Bild gleicher
Grösse, das sagt, welche Bildpunkte gelten: weiss behalten, schwarz ausblenden (die Person, die
Hand). *Im Projekt:* Liegen solche Masken neben der Aufnahme (`masks/` neben `sparse/0`, Name des
Fotos plus `.png`), blendet die Splat-Brücke die schwarzen Bildpunkte aus; ihr Inhalt geht in den
Speicherschlüssel des Netzes ein. Masken aus einem **anderen** Lauf derselben Szene werden nie
übernommen — dessen Kameras sind nicht als gleich geprüft.

**Maskenpolarität** — Welche Farbe einer Maske «behalten» heisst. Üblich ist weiss = behalten; manche
Werkzeuge machen es umgekehrt. *Im Projekt:* Sagt es die Datei `maske.json` neben den Masken, gilt
sie; sonst weiss = behalten. Ist ohne `maske.json` über alle Masken weniger als die Hälfte weiss,
gilt die **Mehrheitsregel** — eine Person füllt nicht das halbe Bild, also ist dann schwarz das
Behaltene —, und der Bericht warnt.

**Zufallsstichprobe mit festem Startwert** — Eine Auswahl, in der jedes Stück gleich wahrscheinlich
vorkommt, gezogen mit einem Zufallsgenerator, der immer bei derselben Zahl beginnt (**Seed
(Startwert)**). So ist sie unabhängig von der Reihenfolge der Daten und trotzdem bei jedem Lauf
dieselbe. *Im Projekt:* Die **Deckung (des Netzes)** zählt seit dem 13.10.2026 bis zu 200 000
dichte Wölkchen so ausgewählt, über den ganzen Splat; vorher jeden n-ten in der Reihenfolge der Datei.

**Feste Reihenfolge (eines Netzes)** — Dasselbe Netz kann in einer Datei verschieden aufgeschrieben
sein: Die Ecken und Dreiecke sind dieselben, nur ihre Reihenfolge nicht — dann ist die Prüfsumme
(**Hash / Prüfsumme**) eine andere. *Im Projekt:* Open3D füllt beim Verschmelzen eine Tabelle
gleichzeitig auf mehreren Rechenkernen, und die Dreiecke kamen bei jedem Lauf anders heraus
(`auf-20261013-276`). Die Splat-Brücke ordnet das Netz seither nach Lage, bevor sie es
vereinfacht und schreibt — gleicher Schlüssel, bitgleiche Datei (**Determinismus**).

**Transformationsmatrix (4×4, zeilenweise)** — Sechzehn Zahlen in vier Zeilen, die sagen,
wie ein Ding gedreht, vergrössert und verschoben wird, um an seinen Platz zu kommen. Die
Verschiebung steht in der letzten Spalte, die letzte Zeile ist immer `0 0 0 1`.
«Zeilenweise» heisst: Die ersten vier Zahlen sind die erste Zeile.
*Sie legt den Splat zum Modell (Feld `transform` im Vertrag mit KosmoOrbit). Gemeint ist
die Welt der glb-Datei — Meter, Y oben —, und in Blender bekommt der Splat danach dieselbe
Drehung wie das Modell (Y oben → Z oben). Eine Probe mit Verschiebung und Drehung um die
Hochachse prüft das am echten Lauf.*

**Umgebung im Bild (Kontext)** — Was im Bild um das Bauwerk herum steht, aber nicht
bewertet wird: heute ein Splat. Er ist in Schönbild und Tiefenkarte zu sehen; die
Hüllbox, nach der die Kamera rahmt, und die Bauwerksmaske, auf der gemessen wird, kennen
ihn nicht. In der Material-ID-Tabelle trägt er die Herkunft `kontext`, und die Maske nimmt
ihn vor jeder Regel heraus. *Ohne diese Herausnahme kippte er am Testbau den
Katalog-Nullbefund, und die Maske fiel aus — obwohl sich am Modell nichts geändert hatte.*


**IfcOpenShell** — Eine quelloffene Bibliothek, die IFC-Gebäudemodelle liest und ihre Bauteile in
Flächen umrechnet (LGPL-3.0, mit eingebauten GPL-Teilen der Geometriebibliothek CGAL). *Im
Projekt:* läuft nur in der eigenen Umgebung `.venv-ifc` als eigenes Programm, nie im Kern
(Prozessgrenze).

**trimesh** — Eine kleine Python-Bibliothek für Dreiecksnetze: zusammensetzen, prüfen, als Datei
schreiben (MIT). *Im Projekt:* schreibt im IFC-Umwandler das Modell als GLB-Datei für Blender.

**shapely / GEOS** — shapely ist eine Python-Bibliothek für flache Geometrie (Umrisse, Flächen,
Schnitte, BSD-3); sie rechnet mit der mitgelieferten Bibliothek GEOS (LGPL-2.1). *Im Projekt:* liegt
nur in `.venv-ifc`, also hinter der Prozessgrenze.

**gsplat** — Eine Bibliothek, die einen Splat auf der Grafikkarte zu Bildern rendert, aus beliebigen
Blickwinkeln (Apache-2.0). *Im Projekt:* erster Schritt der Splat-Brücke in `.venv-splat`.

**Open3D** — Eine Bibliothek für 3D-Daten wie Punktwolken und Netze (MIT). *Im Projekt:* verschmilzt
in der Splat-Brücke die Tiefenbilder aus gsplat zu einem farbigen Netz.

---

## 6 · KI-Bildmodelle

**Modell** — Ein trainiertes System, das aus Eingaben Ausgaben erzeugt. Umgangssprachlich
sowohl die Bauform als auch die konkreten trainierten Zahlen.

**Gewichte (Weights)** — Die im Training gelernten Zahlen. Sie *sind* das Können des
Modells. Dateigrössen von mehreren Gigabyte sind üblich.

**Schritte eines Bildmodells** — Ein Bildmodell malt sein Bild nicht in einem Zug, sondern
beginnt bei reinem Rauschen und macht es in mehreren Durchgängen ein Stück klarer; jeder
Durchgang ist ein *Schritt*. Mehr Schritte heisst meist feinere Bilder und längere Rechenzeit,
ungefähr im selben Verhältnis. Manche Modelle sind eigens auf wenige Schritte trainiert
(«destilliert») und brauchen nicht mehr. *Im Projekt:* z-image-turbo ist auf 8 Schritte
destilliert und rechnet in voller Güte heute 20 (ob 8 reichen, misst Auftrag 288);
qwen-image-2.1 rechnet 40. Die Zahl steht je Modell im Register (`backbone.py`,
`schritte_vorgabe`, `vorschau_schritte`).

**Vorschau (Güte)** — Die schnelle Stufe des Schalters «Güte: Vorschau | Voll» am
Render-Knoten (Entscheid 104; seit Entscheid 143 vom 24.10.2026 für Varianten nicht mehr Vorgabe,
nur noch gewählt — siehe *Vorgabe je Bestellart*). Sie rechnet immer mit z-image-turbo (auch wenn ein
anderes Modell gewählt ist), mit einem einzigen Zufallswert statt der Auswahl aus drei, mit
den 8 Schritten, auf die das Modell trainiert ist, und mit einem kleineren KI-Bild (lange
Seite 1024 Pixel), das danach auf die Grösse der Blender-Grundlage gebracht wird. Das Bild
wird geprüft wie jedes andere und trägt den Vermerk «Vorschau» (104a). Die Grundlage bleibt
unverändert, sodass dieselbe Ansicht danach in voller Güte gerechnet werden kann. *Im
Projekt:* Vertragsfeld `vis.guete` (`'vorschau' | 'voll'`, fehlt = `'voll'`), im Ergebnis
`guete`; gerechnet in `abholer.verarbeiter` (`gerechnetes_backbone`, `schritte_des_laufs`,
`seeds_der_kamera`, `vorschau_steuerbilder`). Ziel: höchstens zwei Minuten je Variante. Seit dem 22.10.2026 hält
auch die Vorschau die Umgebung ausserhalb des Hauses fest wie die volle Güte (*Halbe M2*).
Sie geht nicht vom Grundbild aus — am Testhaus übermalte sie darum ein Fensterband (Messung
346); ihre Marke sagt «Fenster und Form nicht gesichert».

**Vorgabe je Bestellart (Güte)** — Welche Güte gilt, wenn niemand am Schalter wählt, hängt seit
Entscheid 143 (24.10.2026) davon ab, *was* bestellt wird: Eine **Variante** — der Knopf «Variante
erzeugen» am Render-Knoten oder der Varianten-Knoten — rechnet **voll**, also vom Grundbild aus mit
Bildeingang 0,5 (rund 33–45 Sekunden je Bild); für den Render-Knoten selbst steht weiter die
Vorschau als Vorgabe (Entscheid 104), sie wirkt aber heute auf keinen Bestellweg, weil am
Render-Knoten nur «Variante erzeugen» eine Güte bestellt. Wer ausdrücklich «Vorschau» wählt, bekommt
die Vorschau. *Im Projekt:* `guete.ts` (`GUETE_VORGABE_JE_ART`, `gueteAmKnoten(params, art)`);
der Heim-PC liest `vis.guete: 'voll'` wie eine Bestellung ohne Feld.

**Steuerbild** — Ein Bild, das dem Bildmodell nicht als Vorlage zum Abmalen, sondern als
Vorgabe dient, woran es sich halten muss — bei Visbox vor allem die Tiefenkarte (wie weit
jeder Punkt entfernt ist) und das rohe Blender-Bild. Für die Vorschau werden verkleinerte
Kopien davon gemacht; die Originale bleiben liegen.

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
*Nachgeführt 22.10.2026:* Das Gegenstück heisst **txt2img** — das Bild entsteht nur aus der
Beschreibung, aus reinem Rauschen. *Im Projekt:* Jedes Ergebnis nennt seit Auftrag 337 unter
`angewandt.ki.modus`, welche der beiden Arten das Bildmodell **wirklich** gerechnet hat. Unser
Standardmodell rechnet im Haus heute txt2img, weil es kein Eingangsbild annimmt; nur mit dem
Schalter `vis.bildeingang` beginnt es beim gerenderten Grundbild (siehe «Eigener Start»).

**Denoise-Stärke** — Wie stark das Ausgangsbild bei img2img überschrieben wird. Niedrig
heisst nah am Original, hoch heisst freier. *Nachgeführt 22.10.2026:* Eine Zahl von 0 bis 1:
0,5 heisst, die Hälfte des Wegs vom Rauschen zum Bild wird neu gemalt, die andere Hälfte kommt
vom Ausgangsbild; 1,0 heisst alles neu, also dasselbe wie txt2img. *Im Projekt:* steht als
`angewandt.ki.denoise` im Ergebnis, und zwar der **wirksame** Wert (ein txt2img-Lauf trägt 1,0,
auch wenn 0,6 bestellt war; das Bestellte steht daneben als `denoise_bestellt`). Beim Schalter
`vis.bildeingang` ist dessen Stärke die Denoise-Stärke. Gemessen am grauen Gipsmodell: ab 0,4
hält das Haus seine Form, ab 0,9 wandert sie (Aufträge 298, 300); am Bild mit Materialien
misst es Auftrag 337.

**Rückfall auf txt2img (beim Bildmodell)** — Bestellt ist ein Bild, das vom gerenderten
Grundbild ausgeht, das Bildmodell kann so ein Ausgangsbild aber nicht annehmen und beginnt
stattdessen aus reinem Rauschen. Das Bild ist gültig, aber es ist ein anderes, als bestellt
war: Form und Fensterteilung folgen dann nur noch grob der Tiefenkarte. In anderen Programmen
(etwa ComfyUI, einem Baukasten für Bildmodelle) entspräche das einem leeren Startbild
(«EmptyLatentImage») statt einem aus dem Grundbild gewonnenen. *Im Projekt:* So rechnet unser
Standardmodell z-image-turbo jede Variante im Haus (gemessen in Auftrag 123, wieder gesehen in
333 bis 336). Seit Auftrag 337 steht es im Ergebnis als `angewandt.ki.rueckfall: true` mit
einer Warnung, die mit «KI-RUECKFALL AUF TXT2IMG» beginnt — nicht nur als Fachfeld. *Nachgeführt
22.10.2026:* Seit Entscheid 138 geht eine Variante ohne eigene Einstellung vom Grundbild aus (*Bildeingang
mit Stärke*, 0,5); der Rückfall bleibt nur, wo der Bildeingang ausgeschaltet ist oder nicht gilt.

**Inpainting** — Gezieltes Neuerzeugen nur eines maskierten Bildbereichs.

**Bild-Eingang** — Die Möglichkeit, ein **fertiges Bild wieder in eine Rechnung zu
geben**, statt es nur anzusehen, zu vergleichen oder auszudrucken. *Klingt
selbstverständlich und war es hier lange nicht: Bis zum 19.09.2026 konnte in diesem
Projekt ein Bild entstehen und geprüft werden — aber kein Rechenschritt konnte es als
Ausgangsmaterial entgegennehmen. Damit gab es für die zweite Hälfte des
Entwurfsablaufs (ins Bild zeichnen, das Bild weiterbearbeiten) keinen Weg, nicht
einmal einen halben.*

**Hineinskizzieren** — Der Arbeitsschritt, den Architektinnen von Hand kennen: Man nimmt
ein fertiges Bild, zeichnet etwas hinein — einen Balkon, ein Vordach, einen Baum — und
lässt es neu berechnen, damit die Zeichnung aussieht wie der Rest des Bildes. *In der
Software heisst das: Bild erzeugen, Datei öffnen, zeichnen, speichern, noch einmal
rechnen lassen. Der Mensch sitzt dabei mitten im Ablauf, und der Rechenweg muss das
aushalten.*

**Bildquelle (als Arbeitsschritt)** — Ein Schritt im Rechenweg, der nichts anderes tut,
als **eine Bilddatei von der Festplatte hereinzuholen**. *Er wirkt überflüssig und ist
der Angelpunkt: Er ist die Stelle, an der ein Mensch wieder hereinkommt. Alle anderen
Schritte bekommen ihr Material vom Schritt davor; dieser bekommt es von jemandem, der
gerade etwas gezeichnet hat.*

**Nachrender** — Ein Rechenschritt, der **nicht bei null anfängt**, sondern auf einem
Bild weiterarbeitet, das schon da ist. Er bekommt zwei Dinge: die Geometrie des Modells
und das Bild, auf dem gerechnet werden soll. *Der Unterschied zum gewöhnlichen
Renderschritt ist genau diese zweite Zutat — und dass sie von überall kommen darf: aus
einem früheren Bild derselben Rechnung oder aus einer Datei, in die jemand hineingemalt
hat.*

**Ein Bildeingang, den die Tiefenkarte gewinnt** — Eine Falle, die am Gerät gemessen
wurde und nicht vermutet ist. Manche Bildmodelle haben nur **einen einzigen** Platz für
ein hineingegebenes Bild. Unser Programm gibt dorthin die Tiefenkarte (die Information
über die Form des Gebäudes), weil sie die wichtigere ist. Das hineingezeichnete Bild
fällt dann weg. *Der Lauf gelingt, ein Bild liegt am Ende da, und ohne einen
ausdrücklichen Hinweis hätte niemand einen Grund, nach der verschwundenen Zeichnung zu
suchen. Gemessen am 18.08.2026 an `Qwen-Image-Edit` — ausgerechnet an dem Modell, dessen
Betriebsart «integriertes Edit» heisst.*

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

**Auslagerung (Offloading) und der Geräteweg** — Passt ein Modell nicht ganz in den
Speicher der Grafikkarte, kann es **stückweise** laufen: Immer nur der gerade benötigte
Teil liegt auf der Karte, der Rest wartet im Arbeitsspeicher des Rechners und wird
herübergeholt, wenn er an der Reihe ist. Das funktioniert und ist **viel langsamer** —
das Hin- und Herschieben kostet mehr Zeit als das Rechnen.
*In diesem Projekt gibt es vier solcher Wege, absteigend nach Geschwindigkeit: alles auf
der Karte; je eine Komponente auf der Karte; je ein einzelnes Untermodul auf der Karte;
gar nichts auf der Karte. Welcher genommen wird, entscheidet nicht das Kartenmodell,
sondern der im Augenblick **freie** Speicher — wer nebenher einen Browser offen hat, kann
denselben Auftrag auf einem anderen Weg laufen lassen als eine Stunde später.*
*Der **Geräteweg** ist die Angabe, welcher der vier es war. Sie wurde in diesem Projekt
seit dem 19.08.2026 ermittelt und bis zum 26.08. nirgends aufgeschrieben — mit der Folge,
dass ein Fehlschlag wie ein neu eingebauter Fehler aussah, obwohl sich am Programm nichts
geändert hatte. Entschieden hatten zwei Zehntel Gigabyte freier Speicher.*

**Bedarfsrechnung (vor dem Ladeweg)** — Die Rechnung, die entscheidet, ob ein Modell ganz
auf die Grafikkarte darf oder stückweise laufen muss. Sie vergleicht, was jetzt frei ist,
mit dem, was der Lauf voraussichtlich braucht.
*Warum sie überhaupt schwierig ist:* Was ein Modell braucht, steht nirgends. Es lässt sich
nur schätzen — und die beiden Schätzwege liefern verschiedene Grössen, die leicht
verwechselt werden.
*Die zwei Wege:* **Grösse der Dateien auf der Festplatte** — leicht zu haben, aber nur die
Zahlen des Modells, ohne den Platz, den das Rechnen selbst braucht; die Datei kann
ausserdem in einem grösseren Zahlenformat vorliegen als der Lauf. Oder eine **frühere
Messung im Betrieb** — sie enthält alles, aber nur für die Bedingungen, unter denen
gemessen wurde.
*Und der Fehler, der daraus wurde* (gemessen am 21.09.2026): Auf die Dateigrösse gehört
ein Aufschlag für das Rechnen. Auf eine Messung im Betrieb gehört er **nicht** — dort ist
er schon drin. Beide gleich zu behandeln zählte dieselbe Sache zweimal und schickte einen
Lauf, der mit fünf Gigabyte Luft auf die Karte passte, auf den langsamen und kaputten Weg.

**Aktivierungen** — Die Zwischenergebnisse, die während des Rechnens entstehen und
ebenfalls im Speicher der Grafikkarte liegen müssen. Sie kommen zu den Zahlen des Modells
noch hinzu.
*Wozu der Begriff hier gebraucht wird:* Er ist der Unterschied zwischen «die Datei ist so
gross» und «der Lauf braucht so viel». Und er wächst mit der Bildgrösse — was bei einem
kleinen Bild bequem passte, kann bei einem grossen nicht mehr passen.

**Spielraum (einer Ladewegentscheidung)** — Wie viel Speicher nach der Entscheidung noch
frei geblieben wäre: frei minus verlangt.
*Wozu:* Eine Entscheidung, die knapp ausging, sieht von aussen genauso aus wie eine, die
bequem ausging — bis der nächste, etwas grössere Lauf stirbt. Die Zahl steht seit dem
21.09.2026 in jedem Ergebnis, und unter zwei Gigabyte meldet sich der Kurzbefund.
*Negativ heisst:* Es reichte nicht, also wurde ausgelagert.

**Vergleich in gleichbleibender Zeit** — Zwei Kennwörter so vergleichen, dass es immer
gleich lange dauert, egal wo der erste Unterschied liegt.
*Warum das nötig ist:* Ein gewöhnlicher Vergleich hört beim ersten falschen Zeichen auf.
Wer misst, wie lange die Antwort braucht, kann daraus ein Kennwort Zeichen für Zeichen
erraten — ohne es je ganz zu kennen.
*Der Satz dazu:* **Ein Vergleich, dessen Dauer vom Inhalt abhängt, verrät den Inhalt.**

**Unverschlüsselte Verbindung (HTTP)** — Eine Verbindung, bei der alles im Klartext durch
das Netz geht: die Bilder, die Namen, und auch das Kennwort.
*Im Projekt:* So läuft die Oberfläche, auch im Heimnetz. Das Kennwort hält Geräte fern,
die zufällig im selben Netz sind — **nicht** jemanden, der dort mithört.
*Und warum es so bleibt:* Die verschlüsselte Fassung bräuchte ein Zertifikat. Ein selbst
ausgestelltes erzeugt auf dem Tablet eine Warnung, die man wegklickt — *und eine
Sicherheitswarnung, die man täglich wegklickt, erzieht zum Wegklicken.*

**Belegter Fortschritt und Lebenszeichen** — Zwei Auskünfte über einen laufenden
Rechenvorgang, die leicht verwechselt werden und **nie gleich aussehen dürfen**.
*Belegter Fortschritt:* Es ist gezählt worden, wie viel schon getan ist, und es steht
fest, wie viel es insgesamt wird. Nur hier ist ein Fortschrittsbalken ehrlich.
*Lebenszeichen:* Es ist erkennbar, dass etwas noch arbeitet — mehr nicht. Wie weit es ist,
weiss niemand.
*Im Projekt:* Die Bildstufe zählt ihre Rechenschritte und meldet damit **belegten**
Fortschritt. Der Blender-Lauf meldet nur, dass er noch lebt.
*Und warum das aufgeschrieben ist:* Ein Balken, der aus einem Lebenszeichen gemacht wird,
sieht aus wie eine Messung und ist geraten — dieselbe Art Fehler wie ein grünes
Prüfzeichen an einem ungeprüften Bild.

**Hintergrundfaden (Thread)** — Ein zweiter Arbeitsstrang im selben Programm. Während er
rechnet, kann der erste weiter antworten.
*Wozu hier:* Ein Bildlauf dauert Minuten. Ohne zweiten Strang bliebe die Oberfläche so
lange stumm — der Browser zeigte nichts an und gäbe irgendwann selbst auf.
*Und die Falle dabei:* Geht in einem Hintergrundstrang etwas schief, verschwindet der
Fehler spurlos — der Strang endet einfach. Darum wird dort **alles** aufgefangen und in
den Laufstand geschrieben. *Ein Fehler, den niemand sieht, ist schlimmer als einer, der
eine Meldung macht.*

**Zeigerereignisse (Pointer Events)** — Die Art, wie ein Browser meldet, dass jemand
etwas berührt, klickt oder mit einem Stift darauf zeichnet. **Ein** Weg für alle drei
Geräte, statt je einem für Maus, Finger und Stift.
*Warum das Projekt genau diesen nimmt:* Er ist der einzige, der **Druck** und **Gerätart**
mitliefert — ob also ein Stift geschrieben hat oder ein Finger, und wie fest. Ohne beides
wäre eine Zeichenfläche auf einem Tablet dasselbe wie eine mit der Maus.
*Und was er nicht löst:* Wie schnell der Strich erscheint. Das hängt am Gerät und am
Browser und ist in diesem Projekt **nicht gemessen**.

**Leinwand (Canvas)** — Eine Fläche in einer Webseite, auf die ein Programm zeichnen kann
— im Unterschied zum übrigen Seiteninhalt, der aus Text und Bildern besteht.
*Im Projekt:* Sie liegt **durchsichtig über** dem Bild, auf das gezeichnet wird. So bleibt
die Zeichnung von dem Bild getrennt, das darunter liegt, und lässt sich einzeln ablegen.
*Und darum arbeitet der Radierer anders, als man denkt:* Er malt nicht weiss, sondern
**nimmt weg**. Weisse Farbe würde das Bild darunter verdecken statt die eigene Linie zu
entfernen — auf dem Bildschirm sähe beides zuerst gleich aus.

**Darstellungsmodus und Entwurfsmodus** — Die zwei Betriebsarten, die Visbox seit dem
21.09.2026 hat, und sie stellen fast entgegengesetzte Fragen.
*Darstellung:* Zeigt das Bild, was im Gebäudemodell wirklich steht? Erfundenes Volumen ist
hier ein **Fehler**, und die Prüfung fällt als Urteil aus: bestanden oder nicht.
*Entwurf:* Wie sähe es aus, wenn dort etwas anderes stünde? Hier ist das erfundene Volumen
**das Ergebnis** — jemand zeichnet eine Idee ins Bild, und das Modell malt sie aus.
*Und die Prüfung ist beide Male dieselbe:* Sie vergleicht Bild und Gebäudemodell. Im
ersten Modus liest man daraus ein Urteil ab, im zweiten die **Differenz** — also, was neu
dazugekommen ist. Genau diese Differenz ist es, die ein anderes Programm später braucht,
um die Idee ins Modell nachzubauen.

**Erfundenes Volumen** — Bauteile oder Baumassen, die in einem erzeugten Bild zu sehen
sind, im Gebäudemodell aber nicht vorkommen.
*Warum das Projekt dagegen misst:* Ein Bild, das ein Gebäude zeigt, das es nicht gibt,
ist als Darstellung wertlos und als Täuschung gefährlich — es sieht genauso überzeugend
aus wie ein richtiges.
*Und warum es trotzdem erlaubt wird:* Im Entwurfsmodus ist es der Zweck. Der Unterschied
ist nicht, **ob** erfunden wird, sondern ob es **absichtlich** geschieht und ob am Bild
steht, dass es geschehen ist.

**Verweis (Symlink)** — Ein Eintrag im Dateisystem, der kein eigener Inhalt ist, sondern
auf eine andere Datei zeigt — wie eine Verknüpfung auf dem Schreibtisch.
*Warum er hier vorkommt:* Die Oberfläche liefert nur Bilder **aus dem Projektordner** aus.
Ein Verweis liegt im Projektordner und kann trotzdem auf etwas ganz anderes zeigen. Darum
wird nicht der Name geprüft, sondern das Ziel, dem er folgt.
*Der Satz dazu:* **Ein Name sagt, wie etwas heisst, nicht wo es liegt.**
*Ein zweites Mal (13.10.2026, `auf-20261013-276`):* KosmoOrbit legt den Splat als Verweis in seinen
Projektordner. Die Splat-Brücke suchte die Aufnahme neben dem Verweis und fand keine; seither sucht
sie zuerst dort und dann neben dem Ziel.

**Nullbar (nullable)** — Ein Feld, das ausdrücklich auch «nichts» enthalten darf, nicht
nur einen Wert. In der Beschreibung eines Werkzeugs steht dann nicht «Text», sondern
«Text oder nichts».
*Wozu es gebraucht wird:* Damit ein Werkzeug im Fehlerfall ehrlich antworten kann. Wer
keine Datei erzeugt hat, soll keinen erfundenen Dateinamen zurückgeben.
*Und wo es zur Falle wird:* Wenn das nächste Werkzeug in der Kette «nichts» **nicht**
annimmt. Im guten Fall merkt es niemand, denn dort kommt ja ein Wert. Erst wenn der
Vorgänger scheitert, kommt das Nichts an einer Stelle an, die keines verträgt.
*Im Projekt gemessen* (21.09.2026): An der Kante vom Zeichenprogramm zu uns stehen vier
solche Stellen — und eine fünfte in unserer eigenen Kette.

**Tote Kante und leere Kante** — Zwei verschiedene Fehler an einer Verbindung zwischen
zwei Werkzeugen, und sie sehen gleich aus.
*Tot:* Die beiden Seiten haben **kein einziges** Feld gemeinsam. Über diese Verbindung
fliesst nichts, und das fällt auf.
*Leer:* Sie haben Felder gemeinsam, aber keines davon ist das, worauf es ankommt. Ein
Beispiel aus dem Projekt: Ein Werkzeug liefert die Masse eines Gebäudes, aber nicht das
Gebäude. Die Verbindung sieht gesund aus und trägt nichts.
*Warum die Unterscheidung zählt:* **Die tote sieht man.** Die leere nicht — bis der Lauf
ohne Modell dasteht.

**Geteilte Parameter (Parameter Sharing)** — Zwei Teile eines Modells benutzen
**dasselbe** Stück Zahlenwerk, statt jeder eine eigene Kopie zu halten. Das spart
Speicher und ist gewollt.
*Beim stückweisen Laden auf die Grafikkarte (siehe Auslagerung) wird es zur Falle: Die
Verwaltungsschicht prüft nur, wo das **erste** Stück eines Teils liegt, und schliesst
daraus auf den Rest. Teilen sich zwei Teile ausgerechnet dieses erste Stück, gilt der
zweite als längst umgezogen, obwohl das meiste von ihm noch im Arbeitsspeicher liegt.
In diesem Projekt gemessen: 67 gemeinsame Stücke, und danach blieben 454 von 521 Teilen
des Bildmodells liegen — der Lauf starb im ersten Rechenschritt mit einer Meldung, die
den wahren Grund nicht nennt.*
*Die Abhilfe ist, dem einen Teil vor dem Auslagern eigene Kopien zu geben. Sie kostet
Speicher — und darum darf sie nur dort greifen, wo wirklich ausgelagert wird. Eine
Reparatur, die auch den gesunden Fall verteuert, kann ihn in den kranken kippen.*

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
*Beweis 27 zeigt den Fall an einem Bild: «ein Gebäude mit Dach, **Fenstern** und einem
Balkon» ergibt beim Bauteilwächter im deutschen Original **zwei** Funde und nach der
Übersetzung **drei** — die Wortliste kennt `fenster`, nicht die gebeugte Form `fenstern`.
Genau darum werden beide Fassungen geprüft.*

**Differenzbild** — Zwei Bilder Punkt für Punkt voneinander abgezogen; übrig bleibt
genau das, was sich geändert hat. Wo beide gleich sind, ist es schwarz.
*Zwei Beweise dieses Projekts hängen daran, und sie fragen Gegenteiliges. Beweis 25
verlangt, dass es **nicht** schwarz ist: Morgen gegen Abend muss die Fassade hell werden,
die im Tagesverlauf ins Licht kommt — sonst kam die bestellte Sonne nicht an. Beweis 26
verlangt, dass es **vollständig** schwarz ist: Vier verschiedene IFC-Spielarten desselben
Bauwerks müssen dasselbe Bild ergeben, der grösste Unterschied betrug 0,00000.*

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

*Die Frage, die sich erst stellt, wenn **zwei** solche Urteile zusammenkommen: Wie
verknüpft man sie? Bei zwei Toren, die beide bestehen müssen, lautet die Antwort — sie
heisst nach ihrem Urheber **UND nach Kleene**:*

| | *und* wahr | *und* falsch | *und* unbekannt |
|---|---|---|---|
| **wahr** | wahr | falsch | **unbekannt** |
| **falsch** | falsch | falsch | **falsch** |
| **unbekannt** | unbekannt | **falsch** | unbekannt |

*In Worten: Ein gerissenes Tor entscheidet allein — es hilft nichts, dass die zweite
Prüfung ausfiel. Ein bestandenes Tor entscheidet nicht allein: Zusammen mit einer
fehlenden Prüfung bleibt das Ergebnis offen, denn ein Freispruch aus Mangel an Messung
ist die teuerste Sorte Urteil.*

*Und die Falle, die in jeder Programmiersprache lauert: Pythons eigenes `and` tut das
**nicht**. Bei ihm ergibt `False and None` ein `False` (richtig), `None and False` aber
ein `None` (falsch) — die **Reihenfolge der Argumente** entschiede über das Ergebnis.
Darum steht die Verknüpfung in `gate.gesamturteil` ausgeschrieben da und nicht abgekürzt.*

**Katalogbeweis (gegen Nullbefund über Hausnamen)** — Ein „nichts gefunden" wiegt völlig
verschieden, je nachdem, worüber gesucht wurde. Läuft die Suche über eine **geschlossene,
genormte Liste**, dann heisst „nicht dabei" wirklich *nicht vorhanden*. Läuft sie über
frei vergebene Namen, heisst es nur *unter diesen Namen nicht gefunden* — und beides sieht
im Ergebnis gleich aus.

*In diesem Projekt entscheidet der Unterschied darüber, ob eine Messung stattfindet. Die
Bauwerksmaske muss das Gelände aussortieren und erkennt es am Namen. Findet sie keines,
sind zwei Fälle möglich: Es gibt keines — oder die Regel hat es verfehlt. Über
**IFC-Klassennamen** fallen die beiden zusammen, denn `IfcSite` ist die genormte Klasse
für das Grundstück: Trägt jeder Eintrag eine IFC-Klasse und ist keiner davon `IfcSite`,
gibt es kein Grundstück. Über **Materialnamen** fallen sie auseinander — echte
Projektgeometrie meldet «Beton» und «kalksandstein», und ein Boden hiesse dort «Erdreich»
oder «Kies» und stünde in keiner Liste.*

*Die Auflage dazu heisst **alle, nicht die meisten**: Ein einziger Eintrag ohne
IFC-Klasse unter hundert mit ist genau der, um den es geht — er könnte der Boden sein. Ein
Beweis, der einen Ausreisser verträgt, ist keiner.*

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

**Union-2.1 (die neuere Fassung des ControlNet)** — Die zweite Fassung des Steuermodells, das
bei uns die Tiefenkarte ins Bild bringt. Die HomeStation hat im September gesehen, dass sie
ein sauberes, freistehendes Gebäude genau auf den Umriss setzt, wo die ältere Fassung beim
Hochhaus eher eine «Gasse» malt. Im Projekt seit dem 30.09.2026 als eigener Registereintrag
`z-image-turbo-union21` — bestellbar, aber nicht Vorgabe, bis ein Vergleich mit vorab
festgelegter Regel es trägt.

**Gewichte-Ordner (eines Registereintrags)** — Der Ordner auf der Platte, in dem die
Gewichte eines Modells liegen. Bis zum 30.09.2026 hiess er immer wie der Eintrag. Seit es
`z-image-turbo-union21` gibt — dieselbe Basis wie `z-image-turbo`, nur ein anderes
Steuermodell —, sagt ein eigenes Feld, wo die Basis liegt. Ohne es suchte das Programm einen
Ordner, den es nicht gibt, und wies den Lauf ab (Befund des Heim-PC, Auftrag 199).

**Tunnel (verschlüsselte Verbindung übers Internet)** — Eine Leitung, die zwei Geräte an
verschiedenen Orten so verbindet, als stünden sie im selben Heimnetz — verschlüsselt, damit
unterwegs niemand mitliest. Für Visbox nötig, weil der Heim-PC rechnet (Grafikkarte, Blender),
präsentiert aber auswärts wird (Owner-Entscheid 30.09.2026). Welcher Tunnel, ist noch offen.

**Vorführmodus** — Eine Betriebsart für Präsentationen: Ist der Heim-PC nicht erreichbar, zeigt
die App vorher gerechnete Bilder statt eines Fehlers — und sagt, dass es vorher gerechnete sind.
Geplant für die Vorführfassung.
*Im Projekt:* Gebaut für die Mac-App (Oktober 2026), **seit dem 20.10.2026 entfallen** (Entscheid
103b): Ohne Heim-PC bleibt die gewöhnliche Arbeitsfläche, nur Rechnen und Assistent sind gesperrt
(siehe *Ohne Rechner*).

**Rechenserver** — Ein Rechner, der für andere Geräte die schweren Arbeiten übernimmt, aber selbst
keine Oberfläche zeigt und keine Unterlagen aufbewahrt: Er nimmt einen Auftrag an, rechnet, gibt
das Ergebnis zurück und vergisst den Auftrag danach wieder. Gearbeitet wird am eigenen Gerät; der
Rechenserver ist nur die starke Maschine dahinter.
*Im Projekt:* Der Heim-PC soll mit der Fassung 0.3 genau das werden — Blender, Bildmodell und
Sprachmodell rechnen dort, Mac und iPad zeigen alles selbst (Plan «Visbox eigenständig»,
20.10.2026).

**Ohne Rechner** — Der Zustand, in dem kein Rechner antwortet: Der Heim-PC ist aus, das Netz weg,
oder er war drei Versuche lang und eine halbe Minute nicht zu erreichen. Die App bleibt dann ganz
bedienbar — Knoten verschieben, verbinden, vergleichen, ablegen —, und oben steht ein schmales
Band: «Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht.» mit dem
Knopf «Erneut verbinden». Was gesperrt ist, sagt an Ort und Stelle einen Satz statt einer
Fehlermeldung. Ein einzelner Aussetzer zeigt davor nur ein leises «kurz nicht erreichbar —
verbinde neu …».
*Im Projekt:* Mac-App seit «Visbox eigenständig», Schritt 2 (20.10.2026), ersetzt den
*Vorführmodus*; die Regel steht im Kern (`Kern/Leitungsschalter.swift`).

**Rechner-Wahl** — Für jede schwere Arbeit lässt sich wählen, welcher Rechner sie übernimmt: der
Heim-PC oder dieses Gerät. Visbox kennt drei solche Arbeiten — das Rendern mit Blender, das
Bildmodell und die Bedien-KI (das Sprachmodell, das in der Assistent-Leiste antwortet). Vorgabe ist
der Heim-PC. «Dieses Gerät» steht sichtbar daneben, ist aber gesperrt und sagt, warum («kein
Blender gefunden», «zu wenig Grafikspeicher»), bis ein Rechner am Gerät selbst gebaut ist. Claude,
das Visbox von aussen steuert, ist davon nicht betroffen.
*Im Projekt:* Mac-App, Einrichten › «Wer rechnet?» (20.10.2026, Schritt 6); die Wahl wird
gespeichert, ändert heute aber noch nichts am Weg (`Kern/Rechnerwahl.swift`).

**App-Einstellungen** — Ein kleiner Speicher, den jedes Programm am Mac für seine eigenen
Vorlieben bekommt: was man zuletzt gewählt hat, welche Ansicht offen war. Er übersteht das
Schliessen und Neustarten, gehört nur diesem Programm und ist **kein** Ort für Geheimnisse — ein
Kennwort gehört in den Schlüsselbund.
*Im Projekt:* Die Mac-App merkt sich dort die Rechner-Wahl und ob sie das iPad über den Mac anbietet;
Kennwörter liegen nie darin (bewacht von `tests/test_ipad_geruest.py`).

**Mappe am Mac** — Die Mappe ist der Ordner, in dem die Arbeit an einem Projekt zusammenbleibt:
das Modell, der Knotengraph, die Skizzen und die Bilder. Bis Visbox 0.3.14 lag sie nur am Heim-PC;
seither liegt sie am Mac, als gewöhnlicher Ordner unter `~/Visbox-Mappen/<Name>/`, den man im
Finder sehen und sichern kann. Der Heim-PC bekommt je Auftrag nur, was er zum Rechnen braucht
(Modell und Szene), und gibt die Bilder zurück; die App legt sie in die Mappe. Ist keine Mappe am
Mac offen, arbeitet alles wie vorher mit der Mappe am Heim-PC.
*Im Projekt:* «Visbox eigenständig», Schritt 3 (Entscheid 103); Fenster «Mappen» der Mac-App
(Palette am Logo «Mappen …» oder ⌘O), Regeln in `Kern/Macmappe.swift`.

**An den Mac holen (Mappenpaket)** — Eine Mappe, die noch am Heim-PC liegt, wird mit einem Klick
an den Mac kopiert. Der Heim-PC beschreibt dafür, was in ihr steckt (das «Paket»: Modell, Skizzen,
Bilder, Graph, mit Grösse), und gibt jede Datei einzeln heraus — nur Dateien, die in dieser
Beschreibung stehen. Bricht die Leitung ab, holt ein zweiter Klick nur, was noch fehlt.
*Im Projekt:* `aiimaging.mappenpaket`, Wege `/knoten/mappen`, `/knoten/mappe-paket`,
`/knoten/mappe-datei` am Heim-PC; die Mac-App in `Start/Mappenablage.swift`.

**Zwillingsmappe** — Die Mappe am Heim-PC, von der eine Mappe am Mac geholt wurde. Sie bleibt
dort liegen und wird nicht gelöscht: Bis das iPad seine Skizzen an den Mac schickt (Schritt 4),
kommen sie weiter dort an, und ein Auftrag mit einer Skizze wird dort gerechnet. Auch die
Standpunkte des Kamera-Knotens rechnet der Heim-PC an ihr.
*Im Projekt:* Feld `heimMappe` in `mappe.json`; ein Auftrag nennt sie im Kopf `X-Mappe-Heim`,
seine Mappe am Mac in `X-Mappe-Am-Mac`.

**Zuletzt geöffnete Mappe** — Die Mappe, die der Heim-PC zeigt, wenn ein Gerät nicht sagt, welche es will: die
Visbox-Seite ohne Angabe, die Knotenansicht ohne Mappe am Mac, das iPad im Übergang. Sie wechselt, wenn jemand am
Heim-PC eine Mappe öffnet oder eine Datei lädt — **nicht** aber, wenn die Datei aus einer Mappe am Mac kommt: Dann legt
der Heim-PC nur einen Zwilling an (Befund vom 21.10.2026: vorher stellte ein Laden vom Mac die Mappe für alle Geräte um).
*Im Projekt:* `zuletzt_geoeffnet` in `oberflaeche/server.py`; der Stand von `GET /knoten/modell-laden` sagt mit
`zuletzt_geoeffnet`, ob ein Laden sie umgestellt hat.

**Zertifikat des Mac (für das iPad)** — Ein digitaler Ausweis, den sich der Mac selbst ausstellt, damit die Leitung zum
iPad verschlüsselt ist. Der geheime Schlüssel dazu entsteht im Schlüsselbund des Mac und verlässt ihn nie. Das iPad merkt
sich beim Koppeln den Fingerabdruck dieses Ausweises und spricht danach mit keinem Gerät, das einen anderen zeigt.
*Im Projekt:* Entscheid 118; gebaut im Kern `Kern/Maczertifikat.swift`, abgelegt von `Start/Macidentitaet.swift`,
angeheftet am iPad von `Verbindung/Maclotse.swift`.

**DER (Kodierung eines Zertifikats)** — Die feste Form, in der ein Zertifikat als Bytes aufgeschrieben wird: jedes Stück
mit einer Kennung, seiner Länge und seinem Inhalt, ineinander geschachtelt. Wer die Form kennt, kann ein Zertifikat ohne
fremde Bibliothek bauen. *Im Projekt:* `Der` in `Kern/Maczertifikat.swift`; geprüft mit OpenSSL.

**Zertifikat-Gegenprobe (beim Koppeln)** — Nach dem Koppeln nennt der Mac den Fingerabdruck seines Zertifikats, und das iPad
vergleicht ihn mit dem, den es in derselben Verbindung gesehen hat (und mit dem aus dem QR-Code, wenn es einen gab).
Stimmen sie nicht, merkt es sich nichts. *Im Projekt:* `Macanbindung.pruefeKopplung`.

**Kein Rückfall auf unverschlüsselt** — Regel für die Leitung iPad–Mac: Geht die verschlüsselte Verbindung nicht, nimmt
das iPad nicht still die unverschlüsselte, sondern verbindet nicht und sagt warum. *Im Projekt:* Entscheid 118;
`Anbindungsart.darfSprechen`, `Macanbindung.wiedergefunden`; der Mac bietet sich ohne Zertifikat gar nicht an.

**Übergangsfassung** — Eine Fassung, in der ein alter Weg noch geht, aber mit einem Satz, dass er bald wegfällt. So
verliert niemand die Verbindung ohne Erklärung. *Im Projekt:* Visbox mit Schritt 4 — ein iPad, das noch direkt mit dem
Heim-PC gekoppelt ist, arbeitet weiter und sagt «Direkt am Heim-PC (Übergang)»; ab der nächsten Fassung soll der Heim-PC
es mit Satz abweisen. Seit Entscheid 118a (21.10.2026) tut er das: Antwort 410 mit dem Satz «Das iPad verbindet sich jetzt
über den Mac …», und das iPad zeigt ihn an.

**Kein Rechner eingerichtet (Mac ohne Heim-PC)** — Der Zustand, in dem am Mac kein Heim-PC eingerichtet ist. Der Mac
vermittelt dann trotzdem fürs iPad: Es koppelt mit dem Mac und sieht Mappe, Bilder und Skizzen der Mappe am Mac; nur, was
der Heim-PC rechnen müsste, beantwortet der Mac mit dem Satz «Kein Rechner eingerichtet». *Im Projekt:* Entscheid 118a,
Frage 3; die Antworten bestimmt der Kern (`Ipadmappenwege.ohneRechner`).

**TestFlight und Apple-Entwicklerkonto** — Das Konto (99 USD im Jahr) erlaubt, eigene Apps über
Apples Testverteilung «TestFlight» wie gewöhnliche Apps aufs iPad zu bringen und Mac-Apps so zu
signieren, dass der Mac beim Öffnen nicht warnt. Ohne Konto (Owner-Entscheid 30.09.2026) läuft
die iPad-App über Swift Playgrounds oder per Kabel vom Mac (sieben Tage gültig), und die Mac-App
wird beim ersten Mal über *Systemeinstellungen → Datenschutz & Sicherheit → «Trotzdem öffnen»*
freigegeben (siehe *Gatekeeper*; «Rechtsklick → Öffnen» reicht seit macOS 15 nicht mehr).

**Gatekeeper** — Die Schranke des Mac, die beim ersten Öffnen prüft, ob eine App von Apple
beglaubigt ist. Eine App ohne Apple-Konto ist es nicht; der Mac öffnet sie erst, wenn man sie
einmal in den Systemeinstellungen (Datenschutz & Sicherheit → «Trotzdem öffnen») freigibt.
Betrifft die Mac-App von Visbox (Entscheide 36 und 58).

**Behelfs-Unterschrift (ad-hoc)** — Eine Unterschrift, die der Rechner beim Bauen selbst unter
eine App setzt, ohne Apple-Konto. Macs mit Apple-Chip starten gar keine App ohne irgendeine
Unterschrift; diese genügt dafür, ersetzt aber nicht die Freigabe durch Gatekeeper. Die
Prüfstrecke setzt sie beim Bau der Visbox-Mac-App.

**Vermittler (Relay)** — Ein Gerät, das Anfragen eines anderen entgegennimmt und weiterreicht.
In Visbox ist der Mac der Vermittler: Das iPad findet ihn im selben WLAN und schickt seine
Anfragen an ihn; der Mac reicht sie über die Leitung nach Hause zum Heim-PC weiter, mit seinem
eigenen Kennwort (Entscheid 42, Plan v0.1.7 Strom B).

**Lieferblatt** — Ein einziges Blatt, mit dem eine Bauetappe an den Integrator übergeben wird:
was neu ist, was er einbauen soll, und woran er erkennt, dass es eingebaut ist (Abnahme je
Punkt). Ersetzt viele Einzelaufträge, damit der Owner nur einen Satz weiterleiten muss
(Entscheid 62).

**Vollbau** — Eine kurze Etappe (ein bis zwei Tage), in der alle geplanten Teile einer Fassung
gleichzeitig gebaut werden, statt einer nach dem anderen — danach Abgabe an den Integrator. Der
erste: v0.1.7, 01.–03.10.2026 (`docs/PLAN_V017_2026-10-01.md`).

**Sammel-Nachprobe** — Ein einziger Prüfauftrag an den Heim-PC, der alle Posten, die bei uns
gebaut, am echten Gerät aber noch nicht bestätigt sind, auf einmal am laufenden KosmoOrbit prüft
(Entscheid 55).

**Vorführmappe** — Ein Ordner mit vorher gerechneten Bildern und einer Beschreibungsdatei
(`vorfuehrmappe.json`). Die Mac-App bringt ihn mit, damit sie ohne Heim-PC etwas zeigen kann;
jedes Bild trägt sein Prüfzeichen und den Tag, an dem es gerechnet wurde. Erzeugt mit
`tools/vorfuehrmappe.py` (Plan v0.1.7, Strom C).

**Platzhalter (Beispielmappe)** — Graue Ersatzbilder mit von Hand gesetzten Prüfzeichen. Sie
zeigen, wie die Vorführmappe aussieht, bis der Heim-PC echte Bilder gerechnet hat — und sagen
das an jedem Bild.

**Wachsender Abstand (Backoff)** — Nach jedem erfolglosen Versuch wartet das Programm länger
bis zum nächsten, in Visbox 5, 10, 20, 40, dann 60 Sekunden, damit es den Heim-PC nicht
ständig anklopft. «Erneut verbinden» setzt den Abstand zurück.

**Bestätigte Antwort** — Eine Antwort, an der das Programm sicher erkennt, dass wirklich der
Heim-PC geantwortet hat und nicht eine Zwischenstation. Nur sie holt die Mac-App aus dem
Vorführmodus zurück.

**Begleitdaten (eines Bildes)** — Unsichtbare Zusatztexte in einer Bilddatei, etwa Pfad,
Rechnername oder der Bildauftrag. Sie werden vor dem Weitergeben entfernt (Regel 3).

**Formatkennung** — Der feste Name eines Dateiformats samt Fassung, etwa
`visbox.vorfuehrmappe/v1`. Daran erkennt ein Programm, ob es eine Datei lesen kann; der Name
soll eine Umbenennung der App überleben.

**Bündel (.app)** — Der Ordner, den der Mac als *ein* Programm zeigt. Darin liegen das
Programm selbst, seine Angaben (*Info.plist*) und Beigaben wie Schriften und die
Beispielmappe.

**Info.plist** — Die Angabenliste einer App — Name, Kennung, nötige Mac-Fassung, Erlaubnisse
wie «lokales Netzwerk» —, die das System liest, bevor es die App startet.

**«Trotzdem öffnen»** — Der Knopf in den Systemeinstellungen (Datenschutz & Sicherheit), mit
dem man auf macOS 15 eine nicht von Apple beglaubigte App einmal freigibt (siehe
*Gatekeeper*).

**Provisioning-Profil (`embedded.mobileprovision`)** — Eine kleine Datei, die Xcode beim Aufspielen einer App aufs
iPad in die App legt. Sie sagt, auf welchem Gerät die App laufen darf und **bis wann**; danach startet sie nicht mehr.
Mit dem kostenlosen Apple-Konto sind das 7 Tage. *Im Projekt:* Die iPad-App liest daraus ihr Ablaufdatum und warnt
zwei Tage vorher (Entscheid 84). Fehlt die Datei (Simulator, App Store), sagt die App nichts.

**Sparkle** — Eine verbreitete, freie Bibliothek (MIT), mit der sich Mac-Apps selbst aktualisieren. Sie liest eine
Liste der Fassungen (einen «Appcast», eine Art Nachrichtenfeed) und prüft jede neue Fassung mit einer eigenen
Unterschrift (EdDSA, ein Unterschriftverfahren mit geheimem und öffentlichem Schlüssel). *Im Projekt:* geprüft und
verworfen (Entscheid 84, Bau): Sie wäre die erste fremde Abhängigkeit der Mac-App und verlangte einen geheimen
Schlüssel in der Prüfstrecke; der Eigenbau braucht beides nicht.

**Wirt (der Knotenansicht)** — Die kleine, Visbox-eigene Seite, die das aus KosmoOrbit kopierte Vis-Werkzeug im
Browser startet und mit dem Heim-PC verbindet (Mappe laden, «Datei laden …», Tastenkürzel). *Wozu:* Was KosmoOrbit in
seinem Hauptprogramm erledigt, fehlt in der Kopie; der Wirt übernimmt genau diese Teile, ohne die Kopie zu verändern.
*Im Projekt:* `kosmovis/apps/visbox-knoten/src/` — seit dem 14.10.2026 auch Strg+Z (`kurztasten.ts`).

**Neustart-Helfer** — Ein winziges Hilfsprogramm, das die Mac-App nach dem Aktualisieren startet, bevor sie sich
beendet. Es wartet, bis die alte App wirklich zu ist, und öffnet erst dann die neue. *Wozu:* Öffnet die alte App die neue
selbst, hält macOS beide für dieselbe App und holt nur die alte wieder nach vorn — am Mac des Owners stand dann ein neues
Fenster vor dem alten. *Im Projekt:* `Aktualisierung.neustartBefehl` im Kern, aufgerufen von `Fassungswaechter.starteNeu`
und vom Umzug nach «Programme» (seit Visbox 0.2.8).

**Prozessnummer (PID)** — Die Nummer, unter der das Betriebssystem ein laufendes Programm führt. Wer sie kennt, kann
fragen, ob das Programm noch läuft. *Im Projekt:* Der Neustart-Helfer bekommt die Nummer der alten Mac-App und wartet,
bis es sie nicht mehr gibt.

**Ein Fenster statt Fenstergruppe (`Window` / `WindowGroup`)** — Zwei Arten, wie eine Mac-App in SwiftUI ihr Fenster
anlegt. Eine *Gruppe* darf beliebig viele gleiche Fenster haben, und jedes erneute Öffnen kann ein weiteres machen; ein
*einzelnes Fenster* gibt es genau einmal, erneutes Öffnen holt es nach vorn. *Im Projekt:* Die Mac-App hat seit 0.2.8 ein
einzelnes Fenster.

**Wiederverbinden** — Das iPad nimmt eine schon einmal gekoppelte HomeStation von selbst wieder auf, ohne neue Zahl:
beim Öffnen der App und jedes Mal, wenn sie wieder nach vorn kommt. Es fragt die gemerkte Adresse mit kurzer Zeitgrenze
(5 s) und sucht gleichzeitig im WLAN nach ihrem Namen, falls der Router ihr eine neue Adresse gegeben hat. *Nicht* von
selbst geht das erste Koppeln. *Im Projekt:* `Verbindungsstand.wiederAktiv` (seit Visbox 0.2.8).

**App Translocation (verschobener Startort)** — Ein Schutz von macOS: Öffnet man eine heruntergeladene App, ohne sie
vorher aus dem Download-Ordner zu verschieben, startet macOS sie aus einem verborgenen, schreibgeschützten Ordner.
*Im Projekt:* Dort kann sich die Mac-App nicht selbst ersetzen; das Blatt «Aktualisieren» bittet dann, sie in den
Ordner «Programme» zu ziehen.

**Weiterleitung (Redirect)** — Die Antwort eines Servers «die Datei liegt woanders, frag dort». Das Programm folgt
ihr meist von selbst. *Im Projekt:* GitHub leitet beim Herunterladen einer Freigabe auf seine Ablage um; die Mac-App
folgt nur Weiterleitungen zu GitHub selbst und bricht sonst ab.

**Startzeile** — Eine der vier Zeilen beim Öffnen der Mac-App (Leitung, Rechner am Heim-PC,
Assistent, iPad). Jede sagt, ob ihr Teil steht, lädt, wartet oder fehlt — und warum
(Entscheid 38).

**Anschluss (Port)** — Die Nummer hinter einer Adresse, mit der ein Rechner mehrere Dienste
auseinanderhält. Die Visbox-Fläche hört am Heim-PC auf 8731, von unterwegs erreichbar über die
Tailscale-Weiterleitung auf 8443.

**Basic-Anmeldung (Herausforderung)** — Die einfachste Anmeldung im Web: Der Server fragt nach
Benutzer und Kennwort, bevor er etwas herausgibt, und das Programm schickt beides bei jeder
Anfrage mit. Die Leitung muss darum verschlüsselt sein — bei Visbox unterwegs über Tailscale.

**WKWebView** — Apples eingebautes Browserfenster für Apps. Die Mac-App zeigt darin, was der
Heim-PC ausliefert, statt es nachzubauen: seit Entscheid 85 (14.10.2026) zuerst die
**Knotenansicht**, per Schalter die Visbox-Seite.

**Dateiwähler (Öffnen-Dialog, `NSOpenPanel`)** — Das gewohnte Fenster «Datei öffnen» des Mac, in dem
man eine Datei aussucht. Eine Webseite fragt mit einem Knopf «Datei wählen» danach; in einem Browser
erscheint es von selbst, in einem eingebauten Browserfenster (**WKWebView**) nur, wenn die App es selbst
öffnet. *Im Projekt:* «Datei laden …» am Modell-Knoten (Entscheid 90) — die Mac-App öffnet es in
`Arbeitsansicht.swift`.

**UI-Delegat (`WKUIDelegate`)** — Ein Teil der App, den das eingebaute Browserfenster fragt, wenn die
Seite etwas will, das über die Seite hinausgeht: ein Fenster für eine Datei, eine Rückfrage, ein neues
Fenster. Fehlt er, geschieht an dieser Stelle einfach nichts — der Knopf sieht bedienbar aus und ist es
nicht. *Im Projekt:* `Flaechenlotse` in der Mac-App, seit Entscheid 90.

**Segmentschalter** — Ein Bedienelement aus zwei oder mehr nebeneinander liegenden Feldern, von
denen genau eines gewählt ist — wie die Tasten eines alten Radios. *Im Projekt:* oben in der
Mac-App «Knoten | Visbox-Seite» (Entscheid 85 A).

**Gedankentext (thinking)** — Was ein Sprachmodell wie Qwen3 vor der Antwort für sich
«überlegt». Visbox liest ihn getrennt mit (`think: true`) und zeigt ihn nie an.

**Entladen (des Sprachmodells)** — Das Sprachmodell von der Grafikkarte nehmen
(`keep_alive: 0`), damit das Bildmodell dort Platz hat. Geschieht bei jedem «Anwenden», bevor
gerechnet wird; der Wechsel kostet am Heim-PC rund 4 Sekunden. Seit Entscheid 106d
(20.10.2026) entlädt Visbox **nur ihr eigenes Modell** (`qwen3:14b`), nie eines von
KosmoOrbit; der Abholer darf es auch selbst entladen, wenn es allein die Karte belegt und
gerade keine Frage läuft. **Seit Entscheid 127 (22.10.2026)** gilt vor jedem Bildauftrag mehr:
siehe **Grafikkarte freigeben (vor dem Bild)**.

**keep_alive** — Eine Angabe, die man Ollama (dem Programm, das am Heim-PC die Sprachmodelle
bereithält) mit einer Anfrage mitgibt: wie lange das Modell danach noch auf der Grafikkarte
bleiben soll. Ohne Angabe sind es einige Minuten, damit die nächste Frage sofort beantwortet
wird. `keep_alive: 0` heisst «sofort wieder herunternehmen». *Wozu:* So lässt sich ein
Sprachmodell von der Karte nehmen, ohne es zu löschen oder etwas daran zu ändern — bei der
nächsten Frage lädt Ollama es von selbst wieder. *Im Projekt:* der einzige Eingriff, den Visbox
an einem Sprachmodell macht (`assistent.gib_karte_frei`, `Ollama.entlade`).

**Grafikkarte freigeben (vor dem Bild)** — Bevor Visbox ein Bild rechnet, fragt sie Ollama, welche
Sprachmodelle gerade auf der Grafikkarte liegen, und nimmt **alle** herunter (`keep_alive: 0`) —
auch das eines anderen Programms auf demselben Rechner. Dann wartet sie wenige Sekunden, bis Ollama
die Karte leer meldet. *Wozu:* Die Karte des Heim-PCs hat 32 GB; das Bildmodell braucht rund 28 GB,
ein grosses Sprachmodell daneben 22 GB — beides zusammen passt nicht, und dann rechnet eines der
beiden stark verlangsamt auf dem Hauptprozessor. *Was es nicht tut:* kein Modell laden, löschen
oder umstellen; fehlt Ollama oder antwortet es nicht, rechnet das Bild trotzdem. Die
Sprachmodelle kommen bei der nächsten Frage von selbst zurück. *Im Projekt:* Entscheid 127 des
Owners; `assistent.gib_karte_frei`, gerufen vom Abholer vor jedem Auftrag und vom Dienst vor jedem
Lauf; was freigegeben wurde, steht im Ergebnis unter `angewandt.freigegeben`.

**Eigenes Modell (des Assistenten)** — Das Sprachmodell, das nur der Visbox-Assistent
benutzt: `qwen3:14b` (Apache-2.0). Bis zum 20.10.2026 war es `qwen3:30b` — dasselbe Modell,
das KosmoOrbit als «Leiter» hält; Visbox entlud es dann mitten aus der fremden Arbeit.

**Rollenkarte (von KosmoOrbit)** — Die Liste, welches Sprachmodell bei KosmoOrbit welche
Aufgabe hat (Meister, Leiter, Zeichner, Seher). Visbox führt eine Abschrift davon
(`assistent.KOSMO_ROLLENKARTE`, mit Herkunft) als Schutzliste: Diese Modelle entlädt sie nie.

**Marke «eine Frage läuft»** — Eine kleine Datei, die der Heim-PC hinlegt, solange der
Assistent eine Frage beantwortet, und danach wieder entfernt. Der Abholer ist ein eigenes
Programm und sieht sonst nicht, ob gerade gefragt wird; mit der Marke entlädt er das Modell
nie mitten in einer Antwort.

**Laden (eines Bildmodells)** — Die Gewichte eines Bildmodells von der Platte lesen,
zusammensetzen und auf die Grafikkarte legen. Im Protokoll des Dienstes erscheint dafür die
Zeile «Loading pipeline components». Kostet am Heim-PC beim Schnellmodell rund 1–2 Sekunden,
bei grossen Modellen deutlich mehr — und die Entscheidung, ob das Modell ganz oder nur stückweise
auf der Karte liegt (siehe *Auslagerung*), fällt genau in diesem Moment.

**Ein Modell je Auftrag (Modellvorrat)** — Ein Bildmodell wird für einen ganzen Auftrag
**einmal** geladen und für alle seine Bilder benutzt — alle Varianten einer Reihe, alle
Kameras einer Bestellung — und am Ende des Auftrags wieder freigegeben. Wie ein Gerüst, das
für die ganze Fassade stehen bleibt, statt für jedes Fenster neu aufgestellt zu werden, und
nach der Fassade abgebaut wird. Wechselt mitten im Auftrag das Modell, wird das alte zuerst
abgebaut: nie zwei Bildmodelle zugleich, sonst hält das erste die Karte, und das zweite muss
auf den langsamen, stückweisen Weg ausweichen.
*Anlass (Messung `auf-20261001-221`): Drei Varianten luden das Modell dreimal. Seit dem
07.10.2026 `render.ein_modell_je_auftrag()`; zwischen zwei Aufträgen bleibt es beim Freigeben.*

**Freigeben (des Grafikspeichers)** — Nach einem Lauf den Speicher der Grafikkarte, den das
Bildmodell belegt hat, wirklich zurückgeben, damit ein anderes Programm (etwa das Sprachmodell
des Assistenten) ihn nehmen kann. Zwei Schritte: Erst werden Reste eingesammelt, die niemand
mehr benutzt (`gc.collect`), dann gibt die Rechenbibliothek den Platz, den sie sich für später
zurückgelegt hatte, an die Karte zurück (`torch.cuda.empty_cache`). *Ohne den zweiten Schritt
sieht die Karte von aussen voll aus, obwohl das Programm nichts mehr darauf rechnet.*

**Werkzeugbeschreibung** — Der Text, mit dem dem Sprachmodell gesagt wird, welche Handgriffe
es vorschlagen darf und mit welchen Angaben. Der Assistent von Visbox hat drei: Standpunkt,
Bildauftrag, Varianten.

**Vorschlagskarte** — Der violett gerahmte Kasten in der Seitenleiste, der zeigt, was der
Assistent einstellen würde. Gerechnet wird erst nach «Anwenden» (Entscheid 41).

**Verlauf (eines Gesprächs)** — Die früheren Beiträge, die bei jeder Frage mitgeschickt werden,
damit der Assistent weiss, worum es ging. Das Sprachmodell selbst behält nichts.

**nvidia-smi** — Ein Programm des Grafikkartentreibers, das sagt, wie viel Grafikspeicher frei
ist. Der Heim-PC liest damit die Zeile «Rechner am Heim-PC» der Mac-App.

**TXT-Eintrag** — Ein kleiner Zettel, den ein Dienst bei der Suche im WLAN (Bonjour)
mitschickt. Am Eintrag `vermittler=mac` erkennt das iPad, dass nicht der Heim-PC antwortet,
sondern der Mac, der für ihn vermittelt. Seit dem 22.10.2026 steht auf dem Zettel des Mac auch
`abdruck=…`: der Fingerabdruck seines Zertifikats, also seine **feste Kennung** (siehe dort).

**Feste Kennung (eines Geräts)** — Ein Merkmal, an dem ein Gerät wiedererkannt wird und das
sich nicht ändert, wenn jemand das Gerät umbenennt. Ein Name ist dafür ungeeignet: Er ist nur
Anzeige. *In diesem Projekt* ist die feste Kennung des Mac der Fingerabdruck seines Zertifikats —
das iPad merkt ihn sich ohnehin beim Koppeln, um nur mit diesem Mac zu sprechen. Seit dem
22.10.2026 nennt der Mac ihn auch auf seinem TXT-Eintrag, und das iPad sucht den gekoppelten Mac
daran statt am Namen. Ein Mac mit altem Stand nennt ihn nicht; dann sucht das iPad weiter am
Namen (Rückfall).

**Gekoppelt gegenüber erreichbar** — Zwei verschiedene Zustände eines Geräts. *Gekoppelt* heisst: Die beiden Geräte
kennen sich, das Koppeln ist einmal gelungen. *Erreichbar* heisst: Das Gerät hat sich eben gemeldet. *In diesem Projekt*
ist die Zeile «iPad» am Mac seit dem 22.10.2026 nur grün, wenn das iPad gekoppelt **und** in den letzten fünf Minuten
erreichbar war; sonst ist sie gelb und sagt «gekoppelt, aber nicht erreichbar seit …».

**Neu koppeln (ohne Trennen)** — Ein zweites Koppeln, während die alte Kopplung noch gemerkt ist. *In diesem Projekt*
bietet das iPad es seit dem 22.10.2026 an, wenn der gekoppelte Mac nicht antwortet; die alte Kopplung wird erst ersetzt,
wenn die neue gelungen ist — ein gescheiterter Versuch kostet also nichts.

**Namenskonflikt (Computername)** — Melden sich zwei Geräte im selben Netz unter demselben Namen,
hängt macOS beim eigenen Rechner still eine Zahl an («MacBook Pro (2)»). Für den Menschen ist es
derselbe Mac, für ein Programm, das ihn am Namen sucht, ein fremder. *In diesem Projekt* stand das
iPad beim Demolauf am 22.10.2026 darum auf «getrennt»; seither erkennt es den Mac an seiner festen
Kennung.

**Kopf (HTTP-Kopfzeile, Header)** — Die Begleitzeilen einer Anfrage im Web, etwa die
Anmeldung oder die Art des Inhalts. Der Mac reicht vom iPad nur wenige davon weiter und
ersetzt die Anmeldung durch seine eigene.

**Hop-by-Hop-Kopf** — Eine Begleitzeile, die nur für eine Teilstrecke gilt (etwa «Verbindung
offen halten»). Ein Vermittler gibt sie darum nie weiter.

**100 Continue** — Ein kurzes «Schick ruhig», das ein Server sendet, bevor ein grosser Inhalt
kommt. Der Mac sagt es dem iPad erst, wenn dessen Anmeldung stimmt — sonst würde er eine Skizze
annehmen, die er ohnehin abweist.

**Absage der Tür (401/403)** — Der Heim-PC antwortet, lässt aber nicht herein, meist weil das
Kennwort nicht stimmt. Die Mac-App behandelt das **nicht** wie einen stummen Heim-PC: kein
Vorführmodus, sondern die Startansicht mit dem Satz und dem Knopf «Einrichten».

**Flüchtige Sitzung (ephemeral)** — Eine Art, Anfragen zu schicken, bei der nichts auf der
Platte bleibt: kein Zwischenspeicher, keine Kekse. Die Mac-App nutzt sie für alle Wege zum
Heim-PC, damit keine Antwort von dort auf dem Mac liegen bleibt.

**Fensterinhalt** — Was das eine Fenster der Mac-App gerade zeigt: Start, Arbeit oder
Vorführmodus. Entschieden im Kern aus dem Stand der Leitung, nicht in der Oberfläche.

**ASCII** — Der Grundvorrat von 128 Zeichen (lateinische Buchstaben, Ziffern 0–9, Satzzeichen),
den jeder Rechner gleich liest. Die Koppelzahl muss aus diesen Ziffern bestehen; Ziffern anderer
Schriften zählen als falscher Versuch, statt den Server stolpern zu lassen.

**Prozentschreibung** — Eine Art, ein Zeichen in einer Webadresse als `%` plus Code zu
schreiben (`%6E` steht für «n»). Wer Wege vergleicht, muss sie vorher gleich lesen — sonst
sieht derselbe Weg in zwei Schreibweisen wie zwei verschiedene aus.

**Gegenstelle** — Das Gerät am anderen Ende einer Verbindung, erkannt an seiner Adresse. Der
Mac lässt je Gegenstelle nur wenige Verbindungen zu, damit ein Gerät nicht alle Plätze belegt.

**Uhr mit Ruhezustand** — Eine Uhr, die weiterläuft, während der Laptop zugeklappt ist. Mit ihr
läuft die Frist einer Koppelzahl auch im Schlaf ab, statt nach dem Aufklappen weiterzugelten.

**TLS mit festgehaltenem Schlüssel (Zertifikat anheften, Pinning)** — Verschlüsselung, bei der
sich ein Gerät beim Koppeln den Ausweis der Gegenseite merkt und danach nur noch mit genau ihr
spricht — auch wenn kein Aussteller ihn beglaubigt hat. Für den Weg iPad ↔ Mac geprüft und nicht
gebaut; der Owner wählte stattdessen Tailscale direkt (Entscheid 63). **Gebaut seit dem
13.10.2026** für den Mac im Heim-WLAN (Entscheid 83b): Er merkt sich den Fingerabdruck des
Zertifikats des Heim-PC und nimmt danach kein anderes mehr an (`Start/Heimvertrauen.swift`).

**Selbst unterschriebenes Zertifikat** — Ein Ausweis, den sich ein Rechner selbst ausstellt,
ohne dass eine anerkannte Stelle ihn beglaubigt. Er verschlüsselt genauso gut, beweist aber für
sich allein nicht, wer dahinter steht — darum merkt sich der Mac ihn beim Koppeln (anheften).
*In diesem Projekt* erzeugt ihn der Heim-PC beim ersten Start mit `--heimnetz` mit dem Programm
`openssl`; er liegt neben der Kennwortdatei, nie im Repo.

**Vertrauen beim ersten Mal (TOFU)** — Ein Gerät glaubt der Gegenseite beim allerersten Kontakt
und merkt sich, wen es da vor sich hatte; ab dann fällt jeder Tausch auf. Bekannt aus SSH.
Schwachstelle ist genau dieser erste Kontakt. *In diesem Projekt* sichert ihn die Zahl am
Bildschirm des Heim-PC gegen jedes andere Gerät im WLAN ab (Entscheid 83b).

**Dazwischenstellen (Man-in-the-Middle)** — Ein Angriff, bei dem sich jemand unbemerkt
zwischen zwei Geräte schaltet und beiden vorspielt, er sei das andere. Er liest dann alles mit,
auch eine Zahl zum Koppeln. *In diesem Projekt* der eine Fall, gegen den die Zahl im WLAN nicht
hilft — nur der Vergleich des «Zeichens des Heim-PC» auf beiden Bildschirmen.

**PAKE (Anmeldung mit kurzem Geheimnis)** — Eine Familie von Verfahren, mit denen zwei Geräte
aus einer kurzen Zahl einen sicheren Schlüssel machen, ohne dass ein Mithörer die Zahl
durchprobieren kann. *In diesem Projekt* bewusst nicht gebaut (13.10.2026): Es selbst zu bauen
hiesse, Verschlüsselung zu erfinden; darum gibt es stattdessen das Zeichen zum Vergleichen.

**Zeichen des Heim-PC** — Die ersten 16 Stellen des Fingerabdrucks seines Zertifikats, in
Vierergruppen («ab12 cd34 ef56 7890»). Es steht im Fenster am Heim-PC und beim Koppeln am Mac;
stimmen beide überein, spricht der Mac sicher mit dem eigenen Heim-PC. 16 Stellen lassen sich —
anders als 4 oder 6 — nicht mit einem gefälschten Zertifikat durch Probieren treffen.

**Mitteilung (am Bildschirm)** — Das kleine Fenster, das ein Betriebssystem oben am Rand
einblendet, etwa bei einer neuen Nachricht. *In diesem Projekt* zeigt der Heim-PC damit die Zahl
zum Koppeln des Mac (Entscheid 83a), über das Programm `notify-send`, wenn es installiert ist.

**Drossel** — Eine Grenze, wie oft etwas in einer Zeit geschehen darf. *In diesem Projekt*
gibt der Heim-PC höchstens alle 30 Sekunden eine neue Zahl zum Koppeln heraus: Wer raten will,
bekommt so wenige Versuche, und jede neue Zahl erscheint sichtbar am Bildschirm.

**Auflösen (eines Fundes)** — Der zweite Schritt der Suche im WLAN: Bonjour meldet zuerst nur
einen Namen («Visbox Heim-PC»); erst das Auflösen ergibt Adresse und Anschluss, unter denen das
Gerät wirklich antwortet. *In diesem Projekt* hat es seit dem ersten Gerätetest (13.10.2026)
eine Frist von 5 Sekunden; danach steht «nicht erreicht» mit dem Grund da, statt endlos
«wird aufgelöst …».

**Tailscale-Befehlszeile** — Das Tailscale-Programm ohne Fenster, das auf Befehle antwortet.
*In diesem Projekt* fragt die Mac-App damit, welche Geräte im eigenen Tailscale-Netz gerade an
sind (`tailscale status --json`), und fragt dann jedes, ob es ein Visbox-Heim-PC ist.

**MagicDNS** — Der Teil von Tailscale, der Namen wie `<rechner>.<netz>.ts.net` in eine Adresse
übersetzt. Ist Tailscale am Gerät aus, kennt es den Namen nicht — die App sagt dann «Tailscale am
iPad an?».

**Zertifikat** — Ein digitaler Ausweis eines Servers. Damit prüft das Gerät, dass es wirklich
mit dem eigenen Heim-PC spricht und nicht mit einem Fremden. Tailscale Serve liefert dem Heim-PC
ein gültiges, darum braucht die App keine Ausnahme. Im Heim-WLAN ohne Tailscale ist es ein
selbst unterschriebenes, das der Mac anheftet (siehe dort, Entscheid 83b).

**Schema (einer Adresse)** — Der Anfang einer Adresse wie `http://` oder `https://`; er sagt, ob
unverschlüsselt oder verschlüsselt gesprochen wird. Unterwegs nimmt die iPad-App nur `https`.

**Strecke** — Der Weg, über den die App den Heim-PC erreicht: zuhause durchs Heimnetz, unterwegs
über Tailscale. Danach richtet sich, welcher Satz bei einem Fehler erscheint.

**local-prepare (Prüf-Helfer)** — Ein fünfter Adressat für Aufträge, als Versuch: ein lokales
Sprachmodell am Heim-PC, das einfache Prüfaufträge für KosmoPrepare abarbeitet — nur lesend. Jeder
Auftrag an ihn muss im Feld «rechte» sagen, welche Ordner er lesen, welche Befehle er ausführen
und in welche eine Datei er schreiben darf; alles andere weist die Prüfung des Auftrags ab.

**Versionsnummer (Visbox 0.1.0)** — Die Nummer, an der man erkennt, welcher Stand einer
Software vorliegt, in drei Teilen: grosse Änderung · neue Fähigkeit · Korrektur. Visbox zählt
seit dem 01.10.2026 selbst, ab 0.1.0 (Entscheid 66), an allen Stellen gleich — Bibliothek,
iPad-App, Mac-App. KosmoOrbit zählt eigen (0.1.6, 0.1.7 …); das KosmoVis-Werkzeug darin ist Teil
dieser Fassung und trägt keine eigene Nummer.

**Aufsicht** — Eine Kamera, die höher als das Gebäude steht und von oben darauf schaut, etwa
KosmoOrbits Auto-Kamera «Übersicht». Seit Entscheid 67 wird sie gerechnet, aber nicht nach den
Regeln für Architekturfotos in Augenhöhe beurteilt; das steht als Auskunft am Bild.

**Pipeline-Klasse** — Der Bauplan in der Bildmodell-Bibliothek (diffusers), mit dem ein
bestimmtes Bildmodell geladen wird. Fehlt er in der installierten Fassung, lässt sich das Modell
gar nicht starten — Visbox sagt das seit dem 01.10.2026 vorher, statt beim Laden abzustürzen.

**Randlose Silhouette** — Das Gebäude füllt jeden Bildpunkt; es gibt keinen Himmel und keinen
Hintergrund, typisch für eine Kamera im Raum. Ein Mass, das Gebäude und Hintergrund vergleicht,
sagt dann nichts mehr.

**Gesamtwert (der Prüfung)** — Die ältere der beiden Zahlen, mit denen wir ein Bild gegen die
Geometrie prüfen: wie gut die geschätzte Tiefe des ganzen Bildes zur Soll-Tiefe passt, mit
Bestehensgrenze 0,65. Er ist nur aussagekräftig, wenn das Haus einen genügenden Teil des Bildes
füllt; unter 20 % kann er rechnerisch nicht bestehen. Daneben steht die Gebäude-Prüfung, die nur
auf dem Haus misst.
*Im Projekt:* `geometrie_qa.geometrie_gate`; seit dem 08.10.2026 unter 20 % «nicht anwendbar»
(`tiefenschaetzer.qa_gegen_soll`, Feld `gesamtwert_anwendbar`, Visbox-Entscheid 70).

**Nicht beurteilbar** — Die dritte Antwort einer Prüfung neben «bestanden» und «durchgefallen»:
Wir wissen es nicht, und wir sagen das, statt zu raten. Im Ergebnis steht dann `bestanden: null`
und ein Satz, warum.
*Im Projekt:* ohne Maskenweg; ein Haus unter 20 % des Bildes (Visbox-Entscheid 70). Für den
zweiten Fall zeigen Fläche und iPad seit dem 08.10.2026 ein eigenes Zeichen «NICHT BEURTEILBAR» —
gelb und gestrichelt wie «nicht gemessen», getrennt nur durch das Wort, denn gemessen *wurde*
(Server-Zeichen `nicht-beurteilbar`, App `Zeichenart.nichtBeurteilbar`, Blatt 16).

**Nicht anwendbar (not_applicable)** — Eine Zahl, die sich zwar ausrechnen lässt, in dieser
Lage aber nichts misst — darum weggelassen und so benannt, statt als Ergebnis gezeigt. Die dritte
Antwort neben «bestanden» und «durchgefallen».

**Bildauftrag der Innenkamera** — Der Text an das Bildmodell für eine Kamera im Raum: um Wörter
wie «Himmel» oder «Fassade» bereinigt und mit «Innenansicht» eingeleitet, damit das Bild nicht
nach draussen zeigt.

**Quellstand (einer Bibliothek)** — Der laufende Arbeitsstand einer fremden Programmbibliothek,
direkt aus ihrem Code-Archiv geholt, nicht als geprüfte, nummerierte Freigabe. Neue Fähigkeiten
stehen dort zuerst. Im Projekt: Qwen-Image-2.1 lässt sich nur mit dem Quellstand von diffusers
laden; selbst die Freigabe 0.40.0 kennt es nicht.

**Dienst-Unit** — Eine kleine Textdatei, die dem Heimrechner sagt, wie er ein Programm als
Dauerdienst startet und neu startet. Im Projekt: `betrieb/visbox-flaeche.service` für die
Visbox-Fläche; liegt eine alte Kopie am Heim-PC, gilt deren Einstellung weiter, bis sie neu kopiert
wird.

**Journal** — Das Logbuch des Heimrechners, in das Dauerdienste ihre Meldungen schreiben. Ohne
die Einstellung «ungepuffert» kommen Meldungen der Visbox-Fläche dort erst verspätet an.

**Geschütztes Leerzeichen** — Ein Leerzeichen, das am Bildschirm wie ein gewöhnliches aussieht,
für den Rechner aber ein anderes Zeichen ist (es verhindert eigentlich einen Zeilenumbruch). Im
Projekt: KosmoOrbit schickte «klarer Himmel» damit, und unsere Übersetzung erkannte die Wendung
nicht; seit dem 02.10.2026 zählt jeder Leerraum als Zwischenraum.

**Xvfb** — Ein unsichtbarer Bildschirm im Arbeitsspeicher: Programme zeichnen darauf, ohne dass ein
echter Bildschirm angeschlossen ist. Im Projekt prüft die HomeStation damit KosmoOrbit, ohne einen
fremden Bildschirm zu bedienen. *Seit dem 15.10.2026 auch für RealityScan:* Es startet unter wine nur mit einem X-Bildschirm, auch ohne Fenster; der Abholer bekommt dafür ein eigenes Xvfb (`:87`), nie den Bildschirm des Owners (`AIIMAGING_REALITYSCAN_DISPLAY`).

**Grafikbeschleunigung** — Die Grafikkarte übernimmt das Zeichnen der Oberfläche, statt dass der
Prozessor jeden Bildpunkt selbst rechnet. Fehlt sie, nehmen manche Programme einen anderen, älteren
Zeichenweg — und der verhält sich nicht immer gleich (siehe B5).

**Software-GL** — Eine Grafikschnittstelle, die nur vorgibt, eine Grafikkarte zu sein, und alles auf
dem Prozessor rechnet. Langsam, aber sie lässt ein Programm den beschleunigten Zeichenweg nehmen —
im Projekt der Prüfweg für B5 (`auf-20261006-239`).

**WebKitGTK** — Die Webansicht, mit der die Desktop-App von KosmoOrbit unter Linux ihre Oberfläche
zeigt; dieselbe Familie wie Safari.

**foreignObject** — Ein Stück gewöhnliche Webseite (Eingabefelder, Knöpfe), eingebettet in eine
Vektorzeichnung. Die Knoten der Vis-Station sind so gebaut: Rahmen gezeichnet, Felder darin echt.

**Trefferfläche** — Die Stelle auf dem Bildschirm, auf die ein Klick wirken muss, damit ein Knopf
reagiert. Liegt sie woanders als der gezeichnete Knopf, scheint der Knopf tot.

**Zentrale** — Der gemeinsame Briefkasten aller beteiligten KI-Arbeitskräfte, betrieben von der
Sitzung am Heim-PC. Wer einer anderen Stelle etwas sagen will, legt eine Nachricht als Datei auf einen
eigenen Zweig im KosmoOrbit-Repo; die Zentrale stellt sie zu und bringt die Antwort zurück. Seit dem
06.10.2026 muss der Owner nichts mehr von Hand weiterleiten.

**Oberflächenstil (IFC)** — Die Angabe in einem Gebäudemodell, wie eine Fläche aussieht: Farbe,
Glanz, Durchsicht. Ein Material wie «Beton» ist nur ein Name; erst der Oberflächenstil sagt, welche
Farbe es trägt. Fehlt er, erfindet das Lesewerkzeug eine Vorgabe (etwa ein Grau je Bauteilart).
*Im Projekt:* `auf-20261007-259` zählte im Demohaus null Oberflächenstile — darum wird die Übernahme
von Materialien in unsere 3D-Datei vorerst nicht gebaut.

**Deckend (Material)** — Ein Material, durch das man nicht hindurchsieht. In der 3D-Datei für die
Tiefenkarte setzen wir jedes Material deckend, auch Glas: Blender zählt im Tiefendurchgang nur Flächen,
die deckend genug sind — ein durchsichtiges Fenster verschwände sonst aus der Soll-Tiefe.
*Im Projekt:* `ifc_to_glb_runner._glb_material`; die Durchsicht aus der IFC steht nur im Bericht.

**sRGB und linear (Farbraum)** — Zwei Arten, dieselbe Farbe als Zahl zu schreiben. sRGB ist die
Schreibweise «wie am Bildschirm gesehen», linear die, mit der ein Renderprogramm rechnet. Das
3D-Format glTF verlangt linear; IFC sagt es nicht, die Programme schreiben meist sRGB. Darum rechnen
wir beim Übernehmen um — sonst käme jede Farbe zu hell an.
*Im Projekt:* `ifc_to_glb_runner.srgb_zu_linear` (Annahme, nicht gemessen).

**Bestand (Körper)** — Ein Körper im Modell, der ein schon stehendes Gebäude darstellt und nicht
den Entwurf, etwa ein Quader, den KosmoOrbit aus einer Punktaufnahme der Umgebung übernommen hat. KosmoOrbit
markiert ihn in der Modelldatei mit dem Vermerk «existing». Visbox hängt dann an den Bildauftrag an, dass das
Gebäude als schlichter Baukörper ohne Schrift erscheinen soll — sonst erfindet das Bildmodell Fassaden und
Schriftzüge.
*Im Projekt:* `kosmo_szene.bestand_in_glb`, `kosmo_szene.BESTAND_ZUSATZ`; ob der Zusatz wirkt, misst
`auf-20261008-271`.

**Ausblenden (in der Prüfung)** — Bildpunkte, die bei der Prüfung gar nicht mitzählen: weder als
Gebäude noch als Fehler. Gebraucht für die Umgebung aus der Punktaufnahme (Bäume, Nachbarbauten): Sie ist im Bild,
aber geprüft wird nur, ob das Bild zum geplanten Gebäude passt. Vorher zählte die Umgebung als Gebäude mit, und ein
Haus auf 3 % des Bildes sah aus wie eines auf 30 %.
*Im Projekt:* `tiefenschaetzer.qa_gegen_soll(ausblenden=…)`, `maske.bauwerksmaske` (`kontext_pixel`),
`auf-20261008-271`.

**Glätten der Umgebung** — Die Punktaufnahme der Umgebung hat Lücken; im Tiefenbild sähe sie aus wie
verstreute Scheiben, und das Bildmodell malt daraus «Konfetti». Glätten heisst: die kleinen Lücken zwischen den
Punkten füllen (nur dort, wo vorher leerer Himmel war, nie auf dem Gebäude) und die Entfernungen dort über eine
kleine Umgebung mitteln, damit Flächen entstehen. Dazu bekommt das Gebäude den mittleren Bereich der Grautöne,
die Umgebung davor und dahinter je einen gestauchten Rand — so bleibt «nah ist hell» überall erhalten.
*Im Projekt:* `kontext.schliesse_umgebung`, `kontext.glaette_tiefe`, `bildschreiben.MODELL_BAND`; Entscheid 77.

**Ausschnitt (Kamera)** — Ein Bild, das ein Gebäude nicht ganz zeigt, sondern näher heran geht, so
dass seine Enden aus dem Bild laufen. Bei sehr langen, flachen Bauten (z. B. einer 66 m langen, 3,45 m hohen
Halle) wäre das ganze Gebäude sonst nur ein dünner Streifen im Bild und nicht prüfbar.
*Im Projekt:* `kameras.kamerasatz(ausschnitt=True)`, Entscheid 75; nicht zu verwechseln mit dem
Öffnungselement darunter.

**Ausschnitt (Öffnungselement)** — Ein Loch, das in eine Wand geschnitten wird, wo später ein Fenster
oder eine Tür sitzt. Es ist kein Bauteil, nur die Lücke. Liefert ein Modell nur den Ausschnitt und
nicht das Fenster selbst, sieht die Geometrie an dieser Stelle ein offenes Loch.
*Im Projekt:* Der Demohaus-Export von KosmoOrbit schreibt Fenster und Türen heute nur als Ausschnitte
(`auf-20261007-259`).

**Fassung (je Knotenart)** — Eine Zahl je Rechenschritt der Bildkette (Geometrie, Blender,
Bild, Prüfung …), die in den Schlüssel des Zwischenspeichers eingeht. Ändert sich, was ein
Schritt bei gleichen Eingaben herausgibt — etwa weil ein Fehler behoben wurde —, wird seine
Zahl um eins erhöht; dann rechnet genau dieser Schritt und was darauf aufbaut neu, der Rest
kommt weiter aus dem Speicher. Anlass: Sitzung 70, ein alter Bildschritt kam nach einer
Reparatur unverändert aus dem Speicher. Im Projekt: `kette.FASSUNGEN`, seit 30.09.2026.

**Tailscale (und das eigene Tailscale-Netz)** — Ein Dienst, der eigene Geräte über das
Internet so verbindet, als stünden sie in einem gemeinsamen, verschlüsselten Netz — ohne dass am
Router zuhause ein Tor geöffnet werden muss; im Uni-Netz weicht er auf den gewöhnlichen
Web-Anschluss aus. Das Kernprogramm ist frei (BSD-3-Clause), die Vermittlung ein gehosteter
Dienst. KosmoOrbit erreicht den Heim-PC schon so; Visbox benutzt denselben Weg. Im Projekt:
`docs/VORFUEHRFASSUNG_2026-10-01.md`. Nicht mitgeliefert, sondern vom Owner installiert.

**Tailscale Serve (Weiterleitung)** — Eine Funktion von Tailscale, die einen Dienst, der nur
auf dem eigenen Rechner lauscht (`127.0.0.1`), im eigenen Tailscale-Netz unter einer Adresse
mit Verschlüsselung (https) anbietet — ohne ihn dem ganzen Netz zu öffnen. Die Kehrseite: Für
den Dienst sieht jede Anfrage aus, als käme sie vom eigenen Rechner. Visbox verlangt darum bei
weitergeleiteten Anfragen immer ein Kennwort (Befund `auf-20261001-213`).

**Ollama** — Ein Programm (MIT-Lizenz), das Sprachmodelle auf dem eigenen Rechner bereitstellt
und über eine einfache Schnittstelle ansprechbar macht. Es kann ein Modell nach einer Antwort
sofort aus der Grafikkarte entladen — wichtig, weil am Heim-PC Bildmodell und Sprachmodell
dieselbe Karte teilen. Kosmo in KosmoOrbit benutzt es schon.

**Qwen3** — Eine Familie freier Sprachmodelle (Apache-2.0) von Alibaba; `qwen3:30b` ist das
Modell, mit dem Kosmo am Heim-PC arbeitet, und der Vorschlag für den Visbox-Assistenten. Nicht zu
verwechseln mit den Bildmodellen derselben Firma (Qwen-Image).

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

**Basis (eines Bildes)** — Das Layer-1-Bild, das unter einem Layer-2-Bild liegt: das
letzte Bild der Kette, das noch aus dem Modell gerechnet wurde. *Sie wird **benannt**,
nicht behauptet — mit Knotennamen, Bildpfad und der Angabe, **wie** die Zuordnung
zustande kam (über die Bildkette, also belegt, oder über dieselbe Geometrie, also
plausibel zugeordnet). Bei mehreren Runden bleibt die **erste** Basis die Basis: Die
vorige Runde ist selbst Layer 2 und hätte nur weiterzureichen, was sie selbst geerbt hat
— Hörensagen zweiter Ordnung. In `aiimaging.kette` steht sie im Feld `basis`, zusammen mit ihrer Herkunft.*

**Basis-Urteil (geerbtes Urteil)** — Das Geometrie-Urteil, das über die **Basis** gefällt
wurde, mitgeführt an einem Layer-2-Bild. *Es beantwortet die Frage «ist die Geometrie
unter diesem Bild geprüft?» — und ausdrücklich **nicht** die Frage «folgt dieses Bild dem
Modell?». Damit die beiden nie verwechselt werden, stehen sie unter verschiedenen Namen:
das eigene Urteil heisst `bestanden`, das geerbte `basis.geometrie_bestanden`. Ein
geerbtes Urteil ist nie ein eigenes; sähe es je so aus, als hätte ein bearbeitetes Bild
die Geometrieprüfung bestanden, wäre der Bau falsch. Ein **durchgefallenes** Basis-Urteil
wird genauso weitergereicht wie ein bestandenes — es ist die unangenehmere und die
wichtigere Auskunft.*

**Variantenstudie** — Mehrere Bildfassungen derselben Sache nebeneinander, um zu
vergleichen und zu entscheiden: acht Lichtstimmungen, drei Materialien, zwei
Fassadengliederungen. *Ein Begriff aus dem Architekturbüro, kein Fachbegriff der
Informatik. Er trägt im Projekt eine technische Bedingung: Die Varianten müssen **als
Varianten derselben Basis erkennbar** sein. Acht Bilder ohne gemeinsam benannte Grundlage
sind acht Bilder und keine Studie. Geprüft wird das in `tests/test_schichten.py`.*



**PyTorch (torch)** — Die verbreitete Bibliothek, mit der neuronale Netze gerechnet werden, auf
Wunsch auf der Grafikkarte (BSD-3). *Im Projekt:* die Rechenmaschine unter diffusers und
transformers am Heim-PC und in der Splat-Brücke; keine Abhängigkeit des Kerns.

**transformers** — Die Bibliothek von Hugging Face, die viele vortrainierte Modelle für Bild und
Text mit einheitlichem Aufruf lädt (Apache-2.0). *Im Projekt:* betreibt die Prüfmodelle für Tiefe
(Depth Anything V2) und Stil (SigLIP 2).

**Z-Image Turbo** — Ein Bildmodell, das in wenigen Rechenschritten ein Bild erzeugt (Apache-2.0).
*Im Projekt:* das Vorgabe-Bildmodell von Visbox (`VORGABE_BACKBONE`), immer mit einem ControlNet, das
es an die Tiefenkarte aus Blender bindet.

**Depth Anything V2 (Small)** — Ein Modell, das aus einem einzelnen Foto schätzt, wie weit jede
Stelle entfernt ist. Die kleine Fassung steht unter Apache-2.0, die grösseren sind nicht-kommerziell.
*Im Projekt:* die Geometrieprüfung vergleicht seine Schätzung am KI-Bild mit der Tiefe aus Blender.

**SigLIP 2** — Ein Modell, das ein Bild in eine Zahlenreihe übersetzt, sodass ähnlich aussehende
Bilder ähnliche Zahlen bekommen (Apache-2.0, von Google). *Im Projekt:* misst in der Stilprüfung, ob
ein Bild wie die Referenzen aussieht; gewählt statt DINOv3, dessen Lizenz ausscheidet.

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

**MCP-Anschluss in der Mac-App** — Seit dem 20.10.2026 (Plan KI-Bedienung, Stufe 2) hat die Visbox-App
am Mac einen eigenen MCP-Server, über den Claude (Claude Code oder Claude Desktop) Visbox bedienen soll. Er
ist nur auf diesem Rechner erreichbar, ab Werk eingeschaltet und braucht kein Kennwort. Alles, was etwas
ändert, wird eine Karte in der Assistent-Leiste; Rendern gibt immer ein Mensch frei, Löschen geht nur über
eine Karte. *Im Projekt:* `ipad/Visbox.swiftpm/Kern/Mcpkern.swift` (die Regeln) und
`ipad/VisboxMac/Sources/VisboxMac/Claude/` (das Netz). Bis Stufe 3 antwortete nur `visbox_status`; seit
Stufe 3 (20.10.2026, abends) reicht er die Werkzeuge der Knotenansicht und vier eigene der Mac-App durch
(siehe **KI-Werkzeugsatz (der Knotenansicht)**, **Werkzeuge der Mac-App (für Claude)**).

**JSON-RPC** — Eine feste Form für Fragen und Antworten zwischen zwei Programmen, geschrieben als
**JSON** (siehe dort). Eine Frage nennt, was getan werden soll («method»), die Angaben dazu
(«params») und eine Nummer («id»); die Antwort trägt dieselbe Nummer und entweder das Ergebnis oder
eine Fehlermeldung mit Zahl. Eine Nachricht ohne Nummer ist eine blosse Mitteilung und bekommt keine
Antwort. *Im Projekt:* die Sprache, in der Claude mit dem MCP-Anschluss der Mac-App redet —
`initialize` (Begrüssung, man einigt sich auf eine Fassung), `tools/list` (welche Werkzeuge gibt es),
`tools/call` (eines benutzen), `ping` (bist du da?).

**Hörer (Listener)** — Der Teil eines Programms, der an einem Anschluss (siehe **Anschluss (Port)**)
wartet, bis jemand anklopft, und dann die Verbindung annimmt — wie ein Empfang, der die Tür öffnet.
*Im Projekt:* `Claudeanschluss.swift` in der Mac-App; er wartet auf Anschluss 8631 auf Claude.

**Loopback (127.0.0.1, «nur dieser Rechner»)** — Eine Adresse, die immer auf den eigenen Rechner zeigt
und nie ins Netz hinausgeht. Wer einen Hörer nur an diese Adresse bindet, ist im WLAN unsichtbar: Andere
Geräte können ihn weder sehen noch erreichen, nur Programme auf demselben Rechner. *Im Projekt:* Der
MCP-Anschluss der Mac-App hört nur auf `127.0.0.1:8631` (Entscheide 106 und 106e) und prüft dazu jede
Verbindung, ob sie wirklich vom eigenen Rechner kommt.

**DNS-Rebinding (umgebogener Name)** — Ein Trick fremder Webseiten: Eine Seite lässt ihren eigenen
Namen nachträglich auf die Adresse 127.0.0.1 zeigen und könnte so aus dem Browser heraus mit Programmen
auf dem eigenen Rechner reden. Die Abwehr: Jede Anfrage muss im Kopf («Host») ausdrücklich
`127.0.0.1` oder `localhost` nennen, und eine mitgeschickte Herkunft («Origin», siehe **Ursprung
(einer Webseite)**) muss lokal sein. *Im Projekt:* `Mcpzugang` in `Kern/Mcpleitung.swift`, wie in
KosmoOrbit.

**Streamable HTTP (MCP über HTTP)** — Die Form, in der MCP über eine gewöhnliche Web-Anfrage läuft statt
über **stdio** (siehe dort): Jede Nachricht von Claude ist eine `POST`-Anfrage an eine feste Adresse
(hier `/mcp`), die Antwort kommt als JSON zurück. Ein offener Strom für spätere Mitteilungen ist
erlaubt, aber nicht nötig. *Im Projekt:* Claude Code trägt den Anschluss mit
`claude mcp add --transport http visbox http://127.0.0.1:8631/mcp` ein; Claude Desktop startet die App
mit `--mcp-stdio`, und dieser Weg reicht jede Zeile an denselben Anschluss weiter.

**Wartefrist (eines Aufrufs von Claude)** — Wie lange ein Werkzeugaufruf auf das Ergebnis oder auf den
Klick des Architekten an der Karte wartet: 45 Sekunden, knapp unter der Zeitgrenze der Claude-Programme.
Danach bekommt Claude «wartet noch — Vorschlag K-n liegt in der Assistent-Leiste» und fragt später mit
`visbox_vorschlag_status` nach, statt den Aufruf zu wiederholen. *Im Projekt:* `Mcp.wartefrist`, wie
KosmoOrbit.

**Werkzeugträger** — Der Teil der App, der die Werkzeuge, die Claude aufruft, wirklich ausführt oder als
Karte vorlegt. Der MCP-Kern selbst führt nichts aus, er reicht nur weiter und wartet. *Im Projekt:* ein
Protokoll im Kern (`Werkzeugtraeger`); bis Stufe 3 ein Platzhalter, seit Stufe 3 der `Knotentraeger`: Er
fragt die Knotenansicht (über den **Boten «visboxKi»**, siehe dort) und führt die Werkzeuge der Mac-App
selbst aus. Ohne laufende App (Weg über stdio) bleibt der Platzhalter.

**KI-Werkzeugsatz (der Knotenansicht)** — Die eine Liste von Werkzeugen, mit denen eine KI die Knotenansicht
bedient: den Knotengraph lesen, Knoten setzen, einstellen, verbinden, schieben, löschen, ein Bild oder
Varianten bestellen, und ein Paket aus bis zu 40 Schritten. Jedes Werkzeug hat eine Art — lesen, ändern,
löschen, rendern —, und daraus folgt, ob der Architekt erst zustimmen muss (siehe **Karte (Vorschlag der
KI)**). Bevor etwas vorgeschlagen wird, rechnet der Satz es auf einer Kopie durch; ein ungültiger Schritt
wird gar nicht erst vorgeschlagen. *Im Projekt:* `ki-werkzeuge.ts`, wörtlich aus KosmoOrbit; Claude bekommt
ihn über MCP, später der Assistent dieselbe Liste.

**Karte (Vorschlag der KI)** — Ein Vorschlag von Claude oder dem Assistenten, der in der Assistent-Leiste
liegt, bis der Architekt «Anwenden» oder «Ablehnen» drückt. Bis dahin ändert sich nichts. Kopf «Vorschlag
von Claude · K-12», darunter, was geschehen würde; bei einem Render-Auftrag der Satz «Rendern braucht danach
deine Freigabe am Knoten.» *Im Projekt:* Entscheid 106a; `Kikarte` im Kern, gezeichnet in `Kileiste.swift`.

**Kartenablage (offene Vorschläge in der App)** — Der Ort in der Mac-App, an dem die offenen Karten liegen, jede mit der
Mappe, zu der sie gehört, und der Zeit, seit der sie wartet. Die Knotenansicht wird bei jedem Wechsel der Ansicht neu
geladen und vergisst dabei alles; die App nicht. Kommt die Knotenansicht zurück, gibt die App ihr die Karten ihrer Mappe
wieder. *Im Projekt:* `Kartenablage` im Kern, gehalten von der `Kizentrale`; Protokoll 74 §184.

**Zurückgeben (einer Karte, mit neuer Probe)** — Eine Karte, die die App aufgehoben hat, geht nach dem Neuladen nicht
unbesehen zurück, sondern wird in der Knotenansicht noch einmal zur Probe durchgerechnet, als käme der Vorschlag neu.
Geht die Probe auf, liegt die Karte wieder da; scheitert sie (etwa weil der betroffene Knoten gelöscht ist), bleibt die
Karte sichtbar und gilt als «passt nicht mehr». Zurückgegeben wird immer als Karte, nie still angewendet. *Im Projekt:*
`visboxKi.stelleWieder` in `ki-wirt.ts`.

**Echtes Beenden (der Arbeit mit Claude)** — Die zwei Fälle, in denen offene Karten von Claude wegfallen, ohne dass der
Architekt entschieden hat: Die App wird geschlossen, oder er schaltet «Claude über MCP» aus. Claude bekommt dann je Karte
einen Satz mit dem Grund, soweit es noch verbunden ist, und die Leiste sagt, was wegfiel. Ein Wechsel der Ansicht oder
eine kurze Unterbrechung ist kein Beenden. Ablaufen lässt die App eine Karte nicht. *Im Projekt:* `Kartenablage.beende`,
Regel wie KosmoOrbit v0.1.10; Protokoll 74 §186.

**Leitung unterbrochen (Vermerk)** — Der Hinweis an einer Karte von Claude, solange die App Claude nicht erreicht (ihr
Anschluss für Claude ist ausgefallen). Die Karte bleibt stehen und lässt sich entscheiden; was der Architekt entscheidet,
erfährt Claude erst, wenn die Verbindung zurück ist — und dann erst, nachdem die App ihm die noch offenen Karten neu
gemeldet hat. *Im Projekt:* `Kartenablage.leitungWeg`, `leitungWieder`, `Mcpkern.meldeNeu`.

**Passt nicht mehr (Karte)** — Eine Karte, die zu einer anderen Mappe gehört als der offenen, oder deren Probe im
jetzigen Knotengraph scheitert. Sie bleibt stehen, bis der Architekt entscheidet; «Anwenden» ändert dann nichts und sagt
in einem Satz, warum — dem Architekten in der Leiste und Claude als Antwort. *Im Projekt:* `Kartenablage.entscheide`.

**Selbständigkeit (Karte, Coop, Voll)** — Wie frei die KI arbeiten darf, eingestellt oben in der
Assistent-Leiste (seit dem 20.10.2026 in der Knotenansicht an der **Claude-Marke**, mit den Schaltern «Coop – ändert
frei» und «Vollautomatik» aus KosmoOrbit): **Karte** (Vorgabe) — jede Änderung wird erst eine Karte; **Coop** und **Voll** —
Änderungen gehen ohne Karte. In jedem Fall bleibt Löschen eine Karte. Ein Bild gibt in Karte und Coop ein Mensch frei;
in **Voll** rechnet es seit Entscheid 146 (24.10.2026) ohne Klick, mit Grenzen (siehe **Vollautomatik**). Die Wahl gilt für Claude und den Assistenten zugleich und wird gemerkt. *Im Projekt:*
Entscheide 106b, 108 A; `Selbstaendigkeit` im Kern.

**Vollautomatik** — Die freieste Stufe der Selbständigkeit: Die KI wendet ihre eigenen Vorschläge an, ohne dass jemand
auf «Anwenden» drückt. Im Partnerprogramm heisst sie so; dort startet damit auch ein bestelltes Bild sofort, und seit der
Geräteprobe R57 (23.10.2026) sagt der Satz auf der Bestellung das auch («rechnet ohne Freigabe»), statt eine Freigabe
durch den Architekten zu versprechen. In Visbox heisst die Stufe «Voll». Bis 0.3.55 gab sie die Grafikkarte nicht frei
(ein Bild blieb eine Karte, danach «Freigeben»); seit Entscheid 146 (24.10.2026, «Alles ohne Klick, Grenzen bleiben»)
rechnen `vis_render`, `vis_varianten` und `vis_grundlage` dort sofort, ohne Karte und ohne Freigabe-Klick — höchstens fünf
Läufe in der letzten Stunde (siehe **Gleitendes Fenster**), nie mit einem Bildmodell mit offener Lizenz, Löschen bleibt eine
Karte. *Im Projekt:* Leser `setzeOhneFreigabeLeser` im Kern der Knotenansicht (`vis-kartenzeile.ts`) und
`setzeVollRenderLeser` im Werkzeugsatz, beide angemeldet von `voll-render.ts`; durchgesetzt am Heim-PC in
`aiimaging.knotenweg` (`voll_stand`, `lege_an(ohne_klick=…)`); Proben `freigabe-voll.test.ts`, `kv-ki-voll-render`,
`tests/test_voll_ohne_klick.py`.

**Tätigkeitsstrom** — Eine Zeile in der Assistent-Leiste, die sagt, was die KI gerade tut («● Claude
legt einen Knoten an …»). Sie steht nur, solange die KI arbeitet, und ein paar Sekunden danach; ein
Verlauf ist sie nicht. In der Knotenansicht übernimmt das seit dem 20.10.2026 die **Erzählzeile**. *Im Projekt:*
Entscheid 108 C; `Kileistenstand.strom`.

**Zwei Rückgängig-Verläufe (eigene Schritte und KI-Schritte)** — Was die KI ohne Karte ändert (Coop,
Voll), steht in einem eigenen Verlauf. **Strg+Z nimmt nur die eigenen Schritte des Architekten zurück**;
den letzten Schritt von Claude nimmt der Knopf «Claudes letzten Schritt zurücknehmen» zurück (in der Knotenansicht
«Zurücknehmen» am letzten Schritt unter «Im Projekt» an der **Claude-Marke**). Hat jemand
seither am selben Graphen weitergearbeitet, ändert der Knopf nichts und sagt, woran es hängt — und
umgekehrt hält Strg+Z an, statt Claudes Arbeit zu überschreiben. Eine Karte, die der Architekt anwendet,
ist sein eigener Schritt. *Im Projekt:* Entscheid 114, wie KosmoOrbit; `rueckgaengigKi` und
`kiVerlaufWache` in `ki-werkzeuge.ts`, gesetzt vom Wirt `ki-wirt.ts`.

**Verlaufs-Wache** — Eine Prüfung vor jedem Strg+Z und Strg+Y: Würde das Zurücknehmen Arbeit überschreiben,
die jemand anderes seither gemacht hat, geht es nicht, und ein Satz sagt warum. *Im Projekt:*
`setzeVerlaufWache` im Store; in Visbox setzt sie der Wirt der Knotenansicht (`kiVerlaufWache`).

**Bote «visboxKi» (Script-Message-Handler)** — Der Weg, auf dem eine Webseite in einer App der App etwas
sagen kann: Die Seite ruft `webkit.messageHandlers.visboxKi.postMessage(…)`, die App bekommt die Nachricht.
Umgekehrt ruft die App Funktionen der Seite auf (`callAsyncJavaScript`). *Im Projekt:* So meldet die
Knotenansicht der Mac-App jede Karte, jeden Entscheid und was die KI gerade tut; die App nimmt nur
Nachrichten der eigenen Knotenseite an (`Knotenki.swift`), nie von der Visbox-Seite des Heim-PC.

**Werkzeuge der Mac-App (für Claude)** — Vier Werkzeuge, die die Mac-App selbst ausführt statt der
Knotenansicht: `mappe_lesen` (was in der Mappe liegt), `skizzen_lesen` (die Skizzen vom iPad, auf Wunsch als
Bild), `bild_ansehen` (das Bild eines fertigen Laufs an Claude) und `lauf_abbrechen` (einen Render-Lauf
anhalten — das gibt die Grafikkarte frei und braucht darum keine Karte). Keines gibt die Grafikkarte frei.
*Im Projekt:* `Macwerkzeuge` im Kern, über die bestehenden Wege des Heim-PC (`Heimlesen.swift`).

**Werkzeugliste im Bau** — Die Liste der Werkzeuge der Knotenansicht, als Datei mitgeliefert
(`ki-werkzeugliste.json`). Claude fragt die Liste nur einmal, wenn es sich verbindet; ist die Knotenansicht
dann noch nicht offen, kennt Claude die Werkzeuge trotzdem — sie antworten dann mit dem Satz, dass die
Knotenansicht nicht offen ist. *Im Projekt:* geschrieben von `tools/knoten_bau.py`, gelesen von der
`Kizentrale`.

**Claude Desktop** — Die Fassung von Claude als eigenes Programm auf dem Mac (neben **Claude Code** im
Terminal). Es startet MCP-Server als Programm und spricht über **stdio** mit ihnen. *Im Projekt:* Im
Einrichten › «Claude über MCP» schreibt «Visbox hinzufügen» den Eintrag in die Einstellungsdatei von
Claude Desktop (Visbox mit `--mcp-stdio`); alles andere in der Datei bleibt.

**Blick (der KI auf die Knotenansicht)** — Was Claude oder der Assistent von der Knotenansicht sieht, ohne
etwas zu ändern: ein Lagebild als Text (welcher Bereich offen ist, welche Knöpfe und Felder sichtbar sind,
welche Karten liegen, welche Regel gerade gilt) und für Claude auf Wunsch ein Bild der Ansicht. Der Assistent
bekommt nur den Text — sein Modell kann keine Bilder lesen. *Im Projekt:* Werkzeug `visbox_blick`, braucht den
Schalter «Mitschauen»; der Text kommt aus `kosmo-blick-live.ts`, wörtlich aus KosmoOrbit.

**Maus der KI (eigener Zeiger)** — Eine zweite, eigene Maus in der Knotenansicht, mit der Claude oder der
Assistent klicken, tippen, ziehen oder scrollen — nicht die Maus des Architekten, die bleibt frei. Man sieht
sie als kleine Figur mit einem Schild («Claude · klickt …») und oben eine Leiste «Claude bedient — Esc
beendet». Ändert ein Klick den Render-Graph, gilt dieselbe Regel wie bei jedem Werkzeug: Karte, Coop oder
Voll; Löschen und Rendern immer eine Karte. *Im Projekt:* Werkzeug `visbox_maus`, braucht den Schalter
«Bedienen»; `kosmo-maus.ts` wörtlich aus KosmoOrbit, die Weiche zum **KI-Werkzeugsatz** in `kosmo-coop.ts`.

**Sperrzone (der Maus der KI)** — Ein Knopf oder Feld, das die Maus der KI nie trifft, auch nicht in
«Voll»: «Freigeben» am Render-Knoten und «Alle freigeben» (beides startet die Grafikkarte), die Knöpfe, die
ein Bild direkt bestellen, Löschen, die Karten selbst, die Schalter an der Marke, Rückgängig,
Kennwort-Felder, die Anmeldung am Heim-PC und das Gespräch mit dem Assistenten. Solange eine KI bedient, sind
die Sperrzonen gestrichelt umrandet. *Im Projekt:* `sperrGrund` in `kosmo-maus.ts` (dazu `WIRT_SPERRZONEN`
in `ki-wirt.ts`); Probe `kv-maus-sperrzonen`.

**Mitschauen und Bedienen (Schalter)** — Zwei Schalter je KI an der **Claude-Marke**: «Mitschauen» erlaubt den
**Blick**, «Bedienen» die **Maus der KI**. Ab Werk beide an; schaltet der Architekt einen aus, bleibt er aus,
auch nach dem Neuladen. Eine KI kann sich nie selbst einschalten, nur ihr Bedienen beenden. *Im Projekt:*
`kosmo-maus-freigabe.ts`, wörtlich; gemerkt von der Mac-App (`kosmo.maus.freigabe`).

**Werkzeugschleife (des Assistenten)** — Wie der Assistent mit Werkzeugen arbeitet: Sein Modell am Heim-PC
sagt, welches Werkzeug es aufrufen will; die Mac-App führt den Aufruf in der Knotenansicht aus und schickt
das Ergebnis zurück; das Modell entscheidet den nächsten Schritt, bis es eine Antwort gibt. Höchstens zwölf
Schritte je Frage. Ändert ein Schritt etwas, liegt eine Karte «Vorschlag des Assistenten · A-n» im
Gesprächsfeld. *Im Projekt:* `frage_mit_werkzeugen` in `assistent.py` (die Schleife), `Assistentengespraech`
im Kern der App (die Regeln des Gesprächs), Plan KI-Bedienung Stufe 5.

**Prüfung im Kern statt Bitte** — Was ein Sprachmodell tun soll, steht in seiner Anweisung (dem Systemprompt); ob es
sich daran hält, ist aber nicht sicher. Darum prüft das Programm selbst, was sich prüfen lässt, bevor ein Werkzeugaufruf
ausgeführt oder eine Antwort gezeigt wird: Eine Kennung, die das Modell nirgends gelesen haben kann, gilt als geraten und
wird zurückgewiesen; eine Angabe, die niemand nannte, gilt als erfunden. Das Modell bekommt den Grund und darf
korrigieren. *Im Projekt:* `_pruefe_angaben` und `_berichtige_antwort` in `assistent.py` (Befunde aus Messauftrag 305,
Protokoll 74 §187).

**Lokales Modell** — Ein Modell, das auf eigener Hardware läuft. Kein Datenabfluss,
keine laufenden Kosten, dafür begrenzt durch die eigene Grafikkarte.

**llama.cpp / Ollama / vLLM** — Programme zum Betrieb lokaler Sprachmodelle.

**Guardrail** — Eine technische Schranke, die verhindert, dass ein Modell etwas
Unerwünschtes auslöst. *In diesem Projekt: Freigabe-Token und GPU-Leerlaufprüfung vor
jedem Render.*

---

## 8 · Systemarchitektur

**KosmoVis** — **Der Name dieser Arbeit selbst.** KosmoVis ist die Komponente, die aus
Gebäudegeometrie Bilder macht und sie prüft; sie lebt in der Software *KosmoOrbit*.

Das Repo `ai-imaging-in-a-box` **ist** KosmoVis. Dass es ein eigenes Repo hat, ist eine
Trennung für die Vertiefungsarbeit und keine zweite Software: Hier liegt nur, was
öffentlich sein darf — Apache-2.0, keine Bürodaten, keine Kundenprojekte (Regel 3).

*Warum das hier steht* (Owner-Klarstellung 26.08.2026): Etliche Docstrings dieses Repos
sprechen vom **«Vorläufer KosmoVis»**. Gemeint ist der **ältere Stand derselben Sache** —
der Code, aus dem dieser Neubau hervorgeht —, nicht ein fremdes Produkt. Wer das anders
liest, hält die eigene Vorgeschichte für die Arbeit von jemand anderem und sucht Fehler an
der falschen Stelle. Genau das ist an jenem Tag passiert.

**KosmoOrbit** — Die Software, in der KosmoVis steckt. Sie ist **knotenbasiert**: Der
Benutzer verdrahtet Bausteine zu einem Ablauf, und die Verbindung zwischen zwei Knoten
entsteht über die **Gleichheit von Feldnamen**. Heisst die Eingabe des einen anders als
die Ausgabe des anderen, entsteht die Kante **nicht** — und zwar ohne Fehlermeldung. Das
ist der Befund, mit dem dieses Projekt in Phase 0 begonnen hat.

Praktisch heisst KosmoOrbit für dieses Repo dreierlei: die **Oberfläche**, an der ein
Mensch einen Auftrag auslöst; der **Vertrag**, dessen Feldnamen bindend sind
(`render-scene/v1` hinein, `render-result/v2` hinaus); und die **Brücke** — Dateien in
`/tmp/kosmo-jobs/`, die einzige Verbindung zwischen beiden Seiten. Gemeinsamen Code gibt es
nicht.

**KosmoDraw** — Ein weiterer Baustein desselben Ökosystems, der Geometrie liefert. Er
kommt in diesem Repo fast nur als **Gegenbeispiel** vor: KosmoDraw und der ältere
KosmoVis-Stand liefern beide ein Feld `glb_path`, aber mit **verschiedener Hochachse**
(Z-oben gegen Y-oben). Eine verdrehte Hochachse dreht Tiefenkarte, Kamera und
Geometrie-Prüfung gemeinsam — und fällt an einem einzelnen Bild nicht auf. Daher die Regel
dieses Projekts, die Achse **anzugeben statt anzunehmen**.

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
*Die Falle liegt auf der anderen Seite: Alles, was **kein** Vertragsfeld ist, muss
irgendwo daneben landen — und wenn „daneben" in Wahrheit „gar nicht" heisst, ist es
umsonst gerechnet. Genau das war hier bis zum 23.08.2026 der Fall: Kompositionsbefund,
Kameraspanne, Maskenbefund und Sprachurteil wurden gerechnet, in ein Wörterbuch gelegt
und mit dem Prozess vergessen. Der Code sah dabei gründlich aus und die Tests waren grün.
Seither gibt es `befund.json` neben dem Vertragsergebnis.*
*Und dieselbe Falle gibt es spiegelverkehrt, auf der **Eingangsseite**: Ein Vertragsfeld,
das die Gegenseite ausfüllen darf und das bei uns nichts bewirkt. Am 23.08.2026 waren es
fünf — Sonnenstand, Hochskalieren, Überspringen und die beiden Stilfelder. Das
gefährlichste ist der Sonnenstand: Er wird gelesen, verworfen, und das Bild kommt sauber
belichtet und **falsch** zurück, ohne dass irgendetwas nach einem Fehler aussieht.*

**Klassifikatorfreie Führung (und warum ein Negativ-Prompt daran hängt)** — Das Verfahren,
mit dem ein Bildmodell dazu gebracht wird, dem Prompt *stärker* zu folgen: Es rechnet jeden
Schritt **zweimal** — einmal mit dem Prompt, einmal ohne — und verstärkt dann die
Differenz.
*Daran hängt der **negative Prompt**, also die Liste dessen, was **nicht** im Bild sein
soll. Er wirkt, indem er den «ohne Prompt»-Durchlauf ersetzt: Statt von nichts entfernt
sich das Bild von dem, was man ausgeschlossen hat.*
*Die Folge ist unangenehm konkret: Wird die Verstärkung ganz abgeschaltet — bei schnellen
«Turbo»-Modellen ist das üblich, weil sie sonst ihre Geschwindigkeit verlieren —, gibt es
keinen zweiten Durchlauf mehr, und ein negativer Prompt hat **nichts, worauf er wirken
könnte**. Er wird trotzdem entgegengenommen, erscheint im Protokoll und ändert kein
Bildpunkt.*
*In diesem Projekt am 23.08.2026 nachgezählt: Alle sieben Bildstile führen einen negativen
Prompt, das voreingestellte Modell schaltet die Verstärkung ab, und der Prompt hätte
ohnehin keinen Weg dorthin gefunden. Beides zugleich, und beides sah nach Sorgfalt aus.*

**Stehengebliebenes Feld** — Ein Feld, das eine Schnittstelle **entgegennimmt** und das
danach nichts bewirkt. Es ist die Eingangsseite derselben Sache wie eine *tote Kante*: Die
Bestellung wird angenommen, quittiert und nicht ausgeführt.
*Warum es schlimmer ist als eine Fehlermeldung: Wer ein Feld setzt und eine Fehlermeldung
bekommt, weiss Bescheid. Wer ein Feld setzt und ein tadelloses Ergebnis bekommt, glaubt,
es habe gewirkt — und wundert sich später über etwas anderes.*
*Die Gegenmassnahme in diesem Projekt ist eine Tabelle, in der **jedes** gelesene Feld in
genau einer von zwei Listen steht: «kommt an» oder «bleibt stehen, und zwar aus diesem
Grund, und dies müsste geschehen». Ein Test prüft, dass keine dritte Möglichkeit entsteht —
denn die dritte, «steht nirgends», ist die bequemste.*
*Gemeldet wird nur, was auch wirklich bestellt wurde. Eine Meldung bei jedem Auftrag wäre
die nächste Dauerwarnung und damit wieder unsichtbar.*

**Dauerwarnung** — Eine Warnung, die bei **jedem** Durchgang erscheint, weil sie an einer
festen Eigenschaft hängt und nicht am einzelnen Vorgang. Nach dem dritten Mal wird sie
überlesen; damit ist sie wirkungslos.
*Und sie richtet mehr Schaden an als nur den eigenen: Zeigt die Ausgabe nur die ersten
drei Warnungen — eine übliche und vernünftige Begrenzung —, dann füllen drei
Dauerwarnungen alle drei Plätze. Jede echte Warnung, die im Programmablauf später
entsteht, ist dann **unsichtbar**. Genau so gemessen in diesem Projekt am 26.08.2026: Die
Begrenzung hat nicht die Geschwätzigkeit begrenzt, sondern die Auskunft gelöscht.*
*Die Abhilfe ist nicht Löschen — das wäre Verschweigen — und nicht Wegbegrenzen. Sie ist
**Trennen**: Was alle betrifft, steht einmal am Ende; was diesen einen Vorgang betrifft,
steht bei ihm. Danach lässt sich die Begrenzung ganz aufheben, weil die verbleibende Liste
kurz ist.*
*Die Probe, ob eine Warnung eine Dauerwarnung ist, ist billig: Erscheint sie bei einem
Vorgang, bei dem gar nichts Besonderes vorliegt? Dann hängt sie nicht an ihm.*

**Selbstlöschende Meldung** — Das Gegenstück zur Dauerwarnung: eine Meldung, die an einer
Bedingung des **einzelnen** Vorgangs hängt und deshalb von allein verschwindet, sobald die
Lage nicht mehr vorliegt. Niemand muss sie später wegräumen, und niemand gewöhnt sich an
sie.
*In diesem Projekt tragen mehrere Zeilen diesen Bauplan, jede mit einem Kommentar
«SELBSTLOESCHEND» darüber. Die jüngste (27.08.2026, `abholer.befund_kurz` und
`kosmo_szene`) steht nur, wenn der Score besteht **und** das Paarurteil zugleich
durchgefallen ist — die Lage, in der ein Bild ohne Bauwerk als geprüft durchgeht. In jedem
gewöhnlichen Lauf ist sie nicht da.*
*Die Probe ist dieselbe wie bei der Dauerwarnung, nur andersherum gelesen: Erscheint die
Meldung auch bei einem Vorgang, bei dem nichts vorliegt? Dann ist sie keine
selbstlöschende, sondern eine Dauerwarnung mit gutem Vorsatz.*

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

**Ablage (eines Auftrags)** — Der Ordner, in dem wartende Aufträge liegen. Nicht dasselbe
wie die Warteschlange als Idee: Die Ablage ist der wirkliche Ort auf der Festplatte, an
dem eine Datei liegt, bis jemand sie holt. *In diesem Projekt gibt es **zwei** — eine, in
die die Bedienoberfläche schreibt, und eine, in die der Werkzeugzugang schreibt.*

**Quelle (eines Abholers)** — Das Stück Programm, das **eine** Ablage lesen und
fortschreiben kann. Es beantwortet immer dieselben Fragen: Was liegt an? Wie lese ich
einen Auftrag? Wie schreibe ich seinen Zustand fort? Wohin kommt das Ergebnis?

*Wozu die Unterscheidung.* Zwei Ablagen legen Aufträge in **verschiedener Form** ab — die
eine als Bestellung nach einem vereinbarten Vertrag, die andere in unserer eigenen Form.
Der Abholer soll beide bearbeiten, ohne beide Formen zu kennen. Er spricht darum nicht mit
der Ablage, sondern mit ihrer Quelle, und die übersetzt. *Der Gewinn ist nicht Eleganz,
sondern dass es weiterhin **einen** Ausführer gibt: Alle Prüfungen vor dem Bildlauf laufen
für beide Wege, weil beide durch dieselbe Stelle gehen. Zwei Ausführer hätten zwei Sätze
von Prüfungen, und die laufen auseinander, sobald jemand nur einen davon pflegt.*

**Nullbefund** — Ein Ergebnis, das lautet «nichts gefunden» — und das **etwas aussagt**,
weil vorher etwas gesucht wurde. Der Gegensatz ist nicht «etwas gefunden», sondern
«**gar nicht gesucht**», und die beiden werden dauernd verwechselt.

Ein Beispiel aus diesem Projekt: Eine Regel sucht in der Baustoffliste einer Szene nach
Namen, die auf Gelände hindeuten. Sie kann drei Dinge melden. *Gelände gefunden.* Oder:
*elf Baustoffe gelesen, keiner heisst nach Gelände* — ein Nullbefund. Oder: *die Liste war
leer oder namenlos* — dann wurde nichts gelesen, und «nichts gefunden» wäre eine Lüge.

*Und ein Nullbefund ist trotzdem kein Beweis.* Er belegt, dass die **Regel** nicht
angeschlagen hat. Dass es die gesuchte Sache nicht gibt, folgt daraus nur, wenn die Regel
vollständig ist — und ob sie das ist, sieht man einem einzelnen Durchgang nicht an.

**Riegel** — Eine Prüfung, die **vor** einem teuren Schritt steht und ihn im Ernstfall gar
nicht erst beginnen lässt. Der Name ist wörtlich gemeint: kein Ratschlag, sondern ein
geschlossenes Tor. *In diesem Projekt stehen die Riegel vor dem Bildlauf — sie kosten
Millisekunden, der Lauf dahinter kostet Minuten Grafikkartenzeit.*

*Ein Riegel, der auf jede Beanstandung schliesst, hält am Ende alles auf; er schliesst
darum auf eine **benannte** Bedingung. Und ein Riegel, der nur auf einem von zwei Wegen
steht, ist keiner — deshalb führt dieses Projekt eine Tabelle darüber, welcher Riegel auf
welchem Weg läuft, und verlangt für jede Einseitigkeit einen Grund.*

**Freigabe-Token** — Eine Zeichenfolge, die eine Befugnis belegt: Erst mit ihr darf ein
teurer Vorgang starten. *Hier `CONFIRMED_RENDER_*`. Es wird bewusst **nie** in die
Auftragsdatei geschrieben — läge es darin, wäre die Befugnis mit der Datei weiterreichbar,
und jeder, der das Verzeichnis lesen kann, hätte sie.*

**Form und Befugnis** — Zwei verschiedene Fragen an dieselbe Zeichenfolge. *Sieht sie aus
wie ein Schlüssel?* ist die Form. *Ist es ein Schlüssel, den wir ausgegeben haben?* ist die
Befugnis. *Bis zum 09.09.2026 prüfte dieses Projekt nur die Form: Wer `CONFIRMED_RENDER_`
kannte und irgendein Zeichen anhängte, kam durch — und das Muster steht in jedem Schema,
das ein Sprachmodell liest. Gemeldet hat es die HomeStation am 21.08.2026.*

**Tokenbuch** — Die Liste der Freigaben, die tatsächlich erteilt wurden, samt Vermerk, ob
eine schon verbraucht ist. *Es macht aus der Formprüfung eine Befugnisprüfung: Ein Token
gilt nur, wenn es im Buch steht und noch nicht verbraucht ist — und es gilt genau einmal,
sonst wären zwei Renderläufe mit einer Zusage bezahlt.*

**Abdruck (eines Tokens)** — Eine kurze, nicht rückrechenbare Zahl, die aus dem Token
berechnet wird (ein **Hash**, siehe Abschnitt 8). Im Tokenbuch steht der Abdruck, nicht das
Token. *Damit kann das Buch wiedererkennen, ob ein vorgelegtes Token ausgegeben wurde, ohne
selbst eine gültige Freigabe zu enthalten. Dasselbe Verfahren, mit dem ein Dienst Passwörter
speichert, ohne sie zu kennen.*

**Pfad-Trickserei (Path Traversal)** — Ein Angriff, bei dem in einem Namen `..` oder `/`
steckt, um aus dem vorgesehenen Verzeichnis auszubrechen — etwa `../../etc/passwd`. Abwehr:
Namen prüfen, bevor sie zu Pfaden werden.
*Seit 15.10.2026 auch für den Namen einer Skizze in der Bestellung* (Auflage A1 des Integrators):
er muss ein relativer Pfad in der Mappe sein — kein `.`/`..`, kein führender `/`, kein Backslash, kein
Laufwerksbuchstabe, keine Steuerzeichen, höchstens 255 Zeichen. Drüben prüft der Vertrag, hier prüfen
Server und Abholer **unabhängig nochmals**.

**Positivliste / Verbotsliste** — Zwei Arten zu prüfen: erlauben, was ausdrücklich zulässig
ist (Positivliste), oder ablehnen, was ausdrücklich schädlich ist (Verbotsliste). *Bei
Sicherheitsfragen ist die Positivliste die richtige — eine Verbotsliste übersieht immer
etwas.*
*Zweites Beispiel im Projekt, seit 21.09.2026:* Die Oberfläche liefert nur die
Dateiendungen aus, die als Bild gelten. Alles andere bleibt liegen, auch wenn es im
Projektordner steht — die Projektdatei zum Beispiel.

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

**Reproduzierbarkeit — und warum sie zwei verschiedene Dinge heissen kann** — Dass
dieselbe Rechnung dasselbe Ergebnis liefert. Das klingt nach einer Ja/Nein-Frage und ist
keine, denn «dasselbe Ergebnis» kann zweierlei bedeuten:

* **Bytegleich** — die erzeugte Datei ist Byte für Byte dieselbe.
* **Inhaltsgleich** — was in der Datei *steht*, ist dasselbe; die Datei selbst
  unterscheidet sich.

*Der Unterschied ist in diesem Projekt gemessen worden* (26.08.2026): Zweimal dasselbe
Bild gerendert ergibt **identische Bildpunkte** und **verschiedene Dateien** — Blender
schreibt die Uhrzeit als Notiz mit hinein. Drei von 30 659 Bytes, und die drei sind das
Datum.

Warum das zählt: Wer prüfen will, ob zwei Rechnungen dasselbe ergeben haben, und dafür die
**Dateien** vergleicht, bekommt bei Bildern aus Blender **immer** «verschieden» — und
schliesst daraus das Falsche.

**Content-Hashing** — Einen Zwischenspeicher nicht über Dateinamen oder Änderungsdatum
adressieren, sondern über eine Prüfsumme des **Inhalts**. Identischer Inhalt ergibt
denselben Schlüssel, auch unter anderem Namen — und geänderter Inhalt einen anderen, auch
bei gleichem Namen.

**Verdeckung** — Etwas steht zwischen Kamera und Bauwerk: ein Nachbarhaus, ein Baum, eine
Geländekante. Für ein Messverfahren ist das heimtückisch, weil das Bild dann teilweise
etwas anderes zeigt als das, wogegen gemessen wird — die Geometrie-Treue fällt, und der
Grund dafür steht nirgends. *In diesem Projekt heute unbehandelt: Die Funktion, die die
Kamera aus einer verdeckten Stellung herauszieht, hat keinen Aufrufer, und an der
synthetischen Testgeometrie — einem freistehenden Quader — verdeckt nichts. Gemessen wird
es mit `auf-20260826-46`.*
*Seit dem 08.10.2026 auch durch die **Umgebung im Bild** (Splat): Steht sie vor dem
Bauwerk, verdeckt sie es in Tiefe, Bild und Maske — richtig so, die Kamera sähe es genauso.
Der Bericht meldet den verdeckten Anteil der Bildpunkte des Modells; dafür rechnet der
Blender-Schritt das Kennbild einmal mit und einmal ohne Splat (billig, ein Strahl je
Bildpunkt).*

**Triage** — Aus der Notfallmedizin entlehnt: eine Menge von Meldungen so sortieren, dass
sichtbar wird, welche sofort behandelt werden müssen und welche warten können. Wichtig ist
dabei, dass **jede** Meldung ein Urteil bekommt — auch «kein Handlungsbedarf». Eine Liste,
in der nur die dringenden Fälle markiert sind, sieht nach Übersicht aus, sagt aber über
den Rest nichts. *In diesem Projekt: `docs/TOTE_KANTEN_TRIAGE_2026-08-26.md` urteilt über
alle 80 gemeldeten Funktionen ohne Aufrufer.*

**Wächter** — Ein Test, dessen Zweck nicht das Prüfen einer Rechnung ist, sondern das
**Festhalten einer Aussage**, die sonst still veralten würde. Er rechnet nichts aus; er
vergleicht, was irgendwo behauptet wird, mit dem, was wirklich der Fall ist — und fällt,
sobald die beiden auseinanderlaufen. *In diesem Projekt bewacht `tests/test_lexikon.py`
das Lexikon und `tests/test_readme.py` das README: dessen Testzahl, die Existenz jeder
verlinkten Datei und die Existenz der Funktionen, die es als Beleg der vier Regeln nennt.
Anlass war ein README, das in Fettschrift behauptete, ein Bildlauf habe nie
stattgefunden — acht Tage nachdem er stattgefunden hatte.*

**Toleranzband** — Statt einer festen Zahl eine Spanne zuzulassen («zwischen 3500 und
3700 Tests»). Bei Messwerten ist das richtig, weil dieselbe Messung selten zweimal exakt
dasselbe ergibt. Bei einer **gezählten** Zahl ist es eine Einladung zum Driften: Das Band
hält still, solange sich wenig ändert, und schweigt genau dann, wenn sich über Wochen viel
geändert hat — also im einzigen Fall, der zählt.

**Mutationsprobe** — Eine Gegenprüfung für Tests: Man baut absichtlich einen Fehler ein
und schaut, ob die Tests ihn bemerken. Tun sie es nicht, bewachen sie nichts. *Ohne das
kann eine grüne Testreihe blosse Beruhigung sein.*

**Wirkungsprüfung gegen Textprüfung** — Zwei Arten, einen Test zu schreiben. Eine
**Textprüfung** liest das Programm wie einen Aufsatz und sucht ein Wort darin («steht
`compare_digest` im Text?»). Eine **Wirkungsprüfung** lässt das Programm laufen und
schaut, was herauskommt («werden bei einer falschen Zahl wirklich zwei Vergleiche
gemacht?»). Nur die zweite merkt, wenn das Wort noch dasteht, aber nichts mehr tut.
*In diesem Projekt am 22.09.2026 an vier Wächtern nachgewiesen:* Jeder blieb grün, während
eine Mutationsprobe die Tür aufsperrte oder den Vergleich abkürzte. Ausnahme, und die
einzige: die **Prüfung auf Abwesenheit** — dass etwas *nicht* im Text steht, etwa
`import bpy` oder eine zweite Kopie einer Regel. Dort ist der Text selbst der Gegenstand.

**Bestellbar, aber nicht lieferbar** — Ein Zustand, in dem man etwas auswählen kann, das
danach nie entstehen kann. Schlimmer als ein fehlendes Feld, weil es aussieht, als ginge
es. *In diesem Projekt seit dem 22.09.2026 an der Innenansicht:* Sie lässt sich in der
Oberfläche bestellen, aber Räume gibt es nur, wenn das Modell als IFC hereinkommt — und die
Projektmappe rechnet immer mit der umgewandelten glb-Datei. Jeder solche Lauf endet mit
einer ehrlichen Fehlermeldung statt mit einem falschen Aussenbild; lieferbar wird die
Innenansicht erst, wenn die Mappe die Räume mitführt.

**Modusabweichung** — Der Fall, dass ein Bild auf eine andere Art gerechnet wurde, als
bestellt war — etwa «aus dem Ausgangsbild weiterzeichnen» bestellt, «nur aus dem Text»
gerechnet, weil das Ausgangsbild unterwegs fehlte. Das Bild sieht dann aus wie jedes
andere. Darum steht die Abweichung seit dem 22.09.2026 **in der Projektmappe**, beim Lauf
und beim einzelnen Bild — und daneben, welche Knoten es **nicht gemeldet** haben: Eine
leere Liste der Abweichungen hiesse sonst zweierlei, «alles wie bestellt» und «niemand
hat nachgesehen».
Seit dem 21.10.2026 steht sie auch **im Ergebnis jedes Bildauftrags** (Feld `angewandt.modus`):
bestellte und gerechnete Art, und ob sie abweichen — oben für den ganzen Auftrag, darunter je
Kamera. «Nicht gemeldet» ist dort ein eigener Wert (leer) und nie dasselbe wie «gleich».

**Laufmessung (in der Mappe)** — Was die Bildstufe während eines Laufs über sich selbst
gemessen hat: bestellte und gerechnete Betriebsart, Schrittzahl, Gerät, Hinweise. Bis zum
22.09.2026 wurde das gemessen und dann zwischen Lauf und Projektdatei weggeworfen. *Eine
Messung, die niemand aufschreibt, hat nicht stattgefunden* — sie muss nur ein einziges Mal
gebraucht werden, um zu fehlen.

**Konvergenz (stürzender Linien)** — Wie stark senkrechte Kanten eines Gebäudes im Bild
aufeinander zulaufen, weil die Kamera nach oben oder unten geneigt ist. Null heisst: Die
Kanten stehen parallel, wie es die Architekturfotografie verlangt. *In diesem Projekt am
22.09.2026 berichtigt:* Fehlte die Angabe der Neigung, rechnete die Prüfung mit null
Grad — und bescheinigte damit parallele Kanten, die nie gemessen waren. Heute heisst eine
fehlende Neigung «nicht gemessen».

**Pipeline-Familie** — Eine Gruppe von Bildmodellen, die denselben Bauplan in der
Bildbibliothek teilen, etwa «z-image» oder «qwen-image». Der Bauplan (die
«Pipeline-Klasse») sagt, wie das Modell zusammengesetzt und aufgerufen wird; ein fremder
passt nicht. *In diesem Projekt seit dem 22.09.2026 im Register vermerkt:* Bis dahin
bekam jedes Modell mit getrenntem Tiefen-Steuermodell denselben Bauplan, und ein Modell
einer anderen Familie wäre damit falsch geladen worden. Heute wird eine unbekannte Familie
abgewiesen statt geraten.

**Flache Kopie gegen tiefe Kopie** — Wer ein verschachteltes Datenbündel kopiert, kann
nur die oberste Ebene neu anlegen (flach) oder alles darin (tief). Bei der flachen Kopie
teilen sich Original und Kopie alles darunter: Wer in der einen Liste etwas ändert, ändert
es in der anderen mit, ohne dass es zu sehen ist. *In diesem Projekt am 22.09.2026
gefunden:* Die Messung am Bild und die im Lauf waren dasselbe Stück Speicher — eine
Berichtigung am Bild hätte den Lauf still umgeschrieben.

**Angabe gegen Messung** — Eine **Messung** hat ein Programm selbst festgestellt (wie
viele Schritte gerechnet wurden). Eine **Angabe** teilt es nur mit, ohne sie geprüft zu
haben (welche Lizenz im Datensatz eines Gewichts steht; welche Geländehöhe jemand von
Hand eingetippt hat). Beide gehören in die Mappe, aber getrennt: *Eine Angabe, die neben
den Messungen steht, sieht aus wie eine.*

**Rollwinkel** — Wie weit die Kamera um ihre eigene Blickachse gedreht ist, wie ein
schief gehaltener Fotoapparat. Bei null Grad stehen senkrechte Kanten parallel zum
Bildrand. *In diesem Projekt bis zum 22.09.2026 eine feste Null,* die «nicht verkantet»
behauptete, ohne dass je jemand den Winkel gemeldet hat. Heute steht dort «nicht
gemessen», bis der Blender-Schritt ihn wirklich abliest.

**Geländeangabe** — Die Höhe des Bodens, die der Betreiber von Hand eingibt. Besser als
die Unterkante des Modells (die bei einem Untergeschoss im Erdreich liegt), aber niemand
prüft sie nach — darum heisst sie im Bericht «nicht geprüft» und nicht «verlässlich».
*Owner-Entscheid vom 22.09.2026:* Auf beiden Kamerawegen heisst sie jetzt «nicht
geprüft» — bis dahin nannte eine zweite Stelle dieselbe Eingabe «Gelände an der Kamera»,
also verlässlich.

**Adresse im Heimnetz gegen «alle Adressen» (0.0.0.0)** — Ein Programm, das Anfragen aus
dem Netz annehmen soll, kann auf **allen** Anschlüssen des Rechners zuhören; das schreibt
man «0.0.0.0». Aufrufen kann man diese Adresse aber nicht — ein iPad braucht die Adresse,
unter der **dieser** Rechner im Heimnetz steht (etwa 192.168.…). Die Adresse
127.0.0.1 («Loopback») erreicht nur den Rechner selbst. *In diesem Projekt druckte die
Startzeile bis zum 22.09.2026 «0.0.0.0» — eine Adresse, die man nirgends eintippen kann.*
Heute fragt das Programm das Betriebssystem, über welche eigene Adresse es ins Netz ginge
(ohne etwas zu senden, über eine reservierte Beispieladresse), und sagt ehrlich, wenn es
das nicht herausfindet.

**Kameraweg (abgeleitet, vorgegeben, Rückfall)** — Die drei Arten, wie der Blender-Schritt
seine Kamera stellt: aus einer gewählten Himmelsrichtung **gerechnet**, als Standpunkt
**von Hand** übergeben, oder als feste Schrägansicht, wenn gar nichts bestellt ist. *In
diesem Projekt am 22.09.2026 untersucht:* Der Bildausschnitt (Deckungsgrad) wirkt nur auf
dem gerechneten Weg. Auf den beiden anderen kommt er an und wird nie gelesen — der Bericht
nannte ihn trotzdem.

**Bildpunkt-Prüfsumme gegen Datei-Prüfsumme** — Ein Fingerabdruck nur der Farbwerte eines
Bildes, im Unterschied zu dem der ganzen Datei. Die Datei trägt oft unsichtbare
Zusatzangaben (Datum, Renderzeit); zwei Dateien können darum dasselbe Bild zeigen und
trotzdem verschiedene Datei-Prüfsummen haben. *In diesem Projekt:* Ob sich ein
Blender-Vorschaubild wirklich geändert hat, lässt sich nur an den Bildpunkten sagen —
am Gerät gefragt.

**Zufallsstreuung einer Rangkorrelation** — Wie weit eine Rangkorrelation schon durch
Zufall von null abweicht, grob eins geteilt durch die Wurzel aus der Zahl der Punkte. Bei
848 Punkten etwa 0,034. *In diesem Projekt am 22.09.2026 gefunden:* Die Prüfung meldete
«vorne und hinten vertauscht» bei +0,037 — einem Wert in der Grösse des Zufalls. Richtig
wäre «kein messbarer Zusammenhang» gewesen.

**Die erste Zustellung zählt** — Wird ein Auftrag ein zweites Mal verschickt, bleibt als
Zustellzeit die erste stehen. Sonst sähe ein Auftrag, der seit Tagen liegt, nach jedem
neuen Versand frisch aus. *In diesem Projekt am 22.09.2026 repariert, nachdem es beim
Verschicken selbst passiert war.*

**Richtungsgrenze** — Wie deutlich eine Rangkorrelation unter null liegen muss, bevor die
Prüfung «vorne und hinten vertauscht» meldet: zwei Zufallsstreuungen, also zwei geteilt
durch die Wurzel aus der Punktzahl minus eins. Darüber heisst die Meldung «kein messbarer
Zusammenhang». *In diesem Projekt seit dem 22.09.2026* — vorher genügte jedes negative
Vorzeichen, auch eines in der Grösse des Zufalls. **Seit dem 23.09.2026 gilt sie in beide
Richtungen:** Auch die Bestätigung «zeigt in die erwartete Richtung» steht erst über der
Grenze; darunter heisst es auf beiden Seiten «die Richtung ist nicht bestimmbar». Vorher
las die eine Seite eine Richtung aus Rauschen, und nur die andere war gebunden.

**Wirkungslos (im Bericht)** — Eine Angabe, die angenommen, am Bild aber nicht benutzt
wurde. Der Bericht sagt dann ausdrücklich warum, statt eine Zahl hinzuschreiben, die nichts
bewirkt hat. *In diesem Projekt seit dem 22.09.2026 beim Bildausschnitt:* Auf den
Kamerawegen «vorgegeben» und «Rückfall» steht dort keine Zahl mehr, sondern der Grund.
*Seit dem 23.09.2026 auch bei Augenhöhe, Winkel (Bias) und Kameramodus* — mit einem
Unterschied: Dort steht der Grund nur, wenn der Wert **bestellt** war; ein Vorgabewert, den
niemand verlangt hat, ist nicht «wirkungslos bestellt».

**Standpunkt-Vorgabe** — Der Blick auf das Gebäude, den die Software nimmt, wenn niemand einen
bestellt hat. Seit dem 07.10.2026 ist das auf beiden Wegen «frontal von Süden» (Kürzel `s`): beim
Abholer (Bestellungen aus KosmoOrbit) schon seit August, beim Weg über die Mappe («Anwenden») neu.
Vorher fiel die Mappe auf die alte Schrägsicht von oben zurück, in der das Haus klein und schief im
Bild stand — und die Prüfung gegen die Geometrie fiel durch. Das Ergebnis sagt in einem Satz, dass
die Vorgabe galt — und seit dem 08.10.2026 steht dieser Satz auch **am Bild in der Mappe**, so dass
Fläche und iPad unter dem Bild «Kein Standpunkt bestellt — von Süden gerechnet.» zeigen, auch nach
dem Neuladen (Entscheid 73, Blatt 16).
*Im Projekt:* `arbeitsgang.STANDPUNKT_VORGABE`, `STANDPUNKT_VORGABE_ZEILE`, am Bild
`herkunft.standpunkt_vorgabe`; Befund in `auf-20261007-261`.

**Sprungmarke (Anker)** — Eine benannte Stelle auf einer Webseite, zu der ein Verweis springt,
statt eine neue Seite zu öffnen — wie ein Lesezeichen im selben Dokument. Geschrieben wird sie als
`#name` hinter der Adresse.
*Im Projekt:* «Standpunkt setzen» unter einem Bild auf der Fläche springt zur Sprungmarke
`#standpunkt`, dem Abschnitt mit dem Grundriss, in dem man den Standpunkt bestellt (Entscheid 73).

**Komponiert (eine Ansicht)** — Eine Kameraeinstellung, die nach dem Gebäude ausgerichtet ist: aus
einer bestimmten Richtung, auf Augenhöhe, so nah, dass das Gebäude das Bild füllt. Das Gegenteil ist
ein Notblick, der nur «irgendwie» auf die Szene zeigt.
*Im Projekt:* Die Richtungskameras (`s`, `sSE`, `nNW` …) sind komponiert, der Rückfall des
Blender-Schritts nicht.

**Standpunkt zweimal bestellt** — Eine Bestellung, die den Blick auf das Gebäude auf
zwei Arten zugleich festlegt: mit einer Himmelsrichtung (daraus rechnet die Bibliothek
einen Standpunkt) **und** mit einem Standpunkt von Hand. Bis Runde 6/7 gewann still der
Standpunkt von Hand. Seither wird die Bestellung abgewiesen, an jeder Stelle — Kette,
seams und HomeStation. *Zwei Quellen für dieselbe Sache werden nicht geordnet, sondern
zurückgegeben.*

**Bias (Winkel einer Über-Eck-Ansicht)** — Um wie viel Grad eine schräge Ansicht gegen die
Hauptachse des Gebäudes gedreht ist. Er regelt, wie viel man von den beiden sichtbaren
Fassaden sieht. Er wirkt nur, wenn der Standpunkt aus einer Himmelsrichtung abgeleitet
wird.

**Nicht gerahmt** — Die Angabe im Urteil, dass für ein Bild **keine** Rahmung gewirkt hat,
weil der Standpunkt von Hand kam. Vorher stand dort die Vorgabe 0,70, als hätte sie
gegolten. *«Nicht gerahmt» ist etwas anderes als «nicht bekannt»:* Das eine sagt der
Runner ausdrücklich, das andere heisst, ein alter Bericht kennt das Feld nicht.

**Listenlage** — Die drei Zustände einer Liste, die die App vom Rechner bekommt: **nicht
geliefert** (das Feld fehlt), **nicht lesbar** (ein Eintrag ist Unsinn) und **gelesen**.
Dazu die Regel **ganz oder gar nicht**: Eine Liste wird ganz gelesen oder gilt als nicht
gelesen — sie wird nie still kürzer. Eine kürzere Liste sähe aus wie «es gibt weniger»,
und das wäre gelogen.

**Überlauf** — Eine Zahl, die zu gross ist für die Art, in der ein Programm sie rechnen
will. Eine ganze Zahl mit 400 Stellen kann Python lesen, aber nicht in eine Kommazahl
verwandeln — dort bricht die Rechnung ab. *In diesem Projekt:* Eine solche Zahl in einer
Bestellung ist seit dem 23.09.2026 ein Mangel mit Satz, kein Absturz.

**Zweite Linie** — Ein Fang hinter der eigentlichen Prüfung: Übersieht die Prüfung einen
Fall, fällt er nicht durch bis zum Absturz, sondern wird dort mit Satz aufgefangen. *In
diesem Projekt:* eine gemeinsame Liste der Lesefehler für Brücke und eigene Ablage — eine
Liste, nicht zwei, damit beide Wege dasselbe fangen.

**Obergrenze, gesetzt, nicht gemessen** — Eine Grenze, die aus einer Quelle abgelesen
(hier: dem Quelltext von Blender 4.2) und nicht am eigenen Gerät nachgeprüft ist. Sie wird
so beschriftet, bis die Messung kommt (`auf-151` V7 fragt nach Blender 5.2). *Nachgemessen am 23.09.2026 an Blender 5.2.2 auf der HomeStation: dieselben Grenzen.*

**Lieferstatus** — Ob bestellte Bilder angekommen sind: **geliefert**, **übersprungen**
(ein regulärer Weg, auf dem absichtlich kein eigenes Bild entsteht, etwa eine Ansicht, die
genau gleich aussieht wie eine andere) oder **fehlgeschlagen** (die bestellende Seite müsste
etwas ändern, um das Bild zu bekommen). Dazu zwei Zahlen **nebeneinander**: bestellt und
gekommen. *In diesem Projekt:* Das Feld stand in KosmoOrbits Vertrag mit der Vorgabe
«geliefert», und niemand setzte es — jedes Ergebnis behauptete still eine vollständige
Lieferung. Seit dem 23.09.2026 senden wir es je Kamera.

**Heimrelativer Pfad** — Ein Pfad, der mit `~/` beginnt: «ab dem Heimatordner dessen, der
die Datei öffnet». Er nennt keinen Benutzernamen und stimmt trotzdem auf jedem Rechner, auf
dem der Ordner gleich aufgebaut ist. *In diesem Projekt* für ein Modell im Heimatordner,
wenn die Mappe anderswo liegt (Befund der HomeStation, 23.09.2026).

**Zwillingsansicht** — Eine Kameraansicht, deren Soll-Tiefenkarte genau gleich aussieht
wie die einer anderen (etwa zwei Über-Eck-Ansichten eines Quaders). Sie wird nicht neu
gerechnet, sondern übernimmt Bild und Urteil der ersten. Darum darf ein Befund über sie
nur **einmal** genannt werden — sonst sieht ein einziger Fehler aus wie zwei.

**Registereintrag** — Eine Zeile in der Tabelle der Bildmodelle, in der alles steht, was
man über ein Modell vor dem Laden weiss: Lizenz, Speicherbedarf, Bauplan-Familie und seit
dem 22.09.2026 auch, ob ein Ausgangsbild bei ihm ankommt — jedes Urteil mit der Kennung
des Auftrags, der es gemessen hat. *Ein Urteil ohne Messung kommt nicht hinein*; die
Tabelle lädt sonst gar nicht.

**Anforderung** — Was eine Software können soll, festgelegt, bevor gebaut wird. *In diesem Projekt:* sieben Schritte vom Modell zum veränderten Bild, aufgeschrieben in «Produkt — die Schritte».

**Randbedingung** — Was eine Software nie tun darf oder immer einhalten muss, auch wenn ein anderer Weg bequemer wäre. *In diesem Projekt:* die vier Regeln — permissive Lizenzen, Blender nur von aussen, keine echten Projektdaten, der Kern ist eine Bibliothek.

**Erfolgskriterium** — Ein nachprüfbarer Satz, woran man erkennt, dass ein Vorhaben gelungen ist. *In diesem Projekt:* Eine fremde Person öffnet die Software zum ersten Mal und kommt ohne Hilfe zu einem veränderten Bild.

**Kleinste Fassung, die ein Erfolg wäre** — Der kleinste zusammenhängende Umfang, der schon als gelungen gilt; alles darüber ist Zugabe. Er schützt davor, am Ende viel Halbes und nichts Ganzes zu haben (Visbox-Entscheid E4).

**Kippstelle (eines Entscheids)** — Die ausdrücklich genannte Bedingung, unter der ein Entscheid anders ausfiele. Wer widersprechen will, muss nur dort nachsehen und nicht die ganze Begründung lesen.

**Schnittstelle** — Die Stelle, an der zwei Bausteine sich berühren, samt der Festlegung, was hineingeht und was herauskommt. *In diesem Projekt:* die Wege zwischen iPad-App und Rechner, beschrieben im Visbox-Protokoll.

**Blender** — Ein freies 3D-Programm unter der GPL. Visbox rechnet damit aus dem Gebäudemodell Vorschaubild, Tiefenkarte und Materialmaske — und ruft es wegen der Lizenz nur **von aussen** auf, als eigenes Programm (Regel 2).

**Versionsverwaltung** — Ein Werkzeug, das jeden Stand einer Software mit Urheber, Zeit und Begründung festhält, so dass man zu jedem früheren Stand zurückkehren kann. Git ist die Versionsverwaltung dieses Projekts.

**Sitzungsprotokoll** — Die Datei, in der jede Arbeitssitzung ihre Entscheidungen mit Begründung, die korrigierten Fehlannahmen und das Offene festhält. *Was nicht in einer Datei steht, ist weg* — das Gedächtnis einer Sitzung verschwindet mit ihr.

**Die dritte Antwort** — Die Hausregel, dass eine Prüfung neben «bestanden» und «nicht bestanden» auch «nicht gemessen» kennt — und dass daraus nie still «in Ordnung» werden darf. Die förmliche Fassung steht unter «Dreiwertiges Urteil».

**Ersatzwert (Vorgabewert)** — Ein Wert, den ein Programm einsetzt, wenn keiner angegeben ist. Bequem, aber gefährlich: So wird aus «nicht gemessen» unbemerkt eine Messung. *In diesem Projekt mehrfach gefunden* — etwa eine fehlende Kameraneigung, die als «lotrecht» galt.

**Einbau** — Der Schritt, durch den eine gebaute Fähigkeit dort ankommt, wo sie gebraucht wird: am echten Gerät, in der fremden Software, auf dem Weg eines Menschen. *Gebaut ist nicht eingebaut.*

**Produktweg gegen direkten Aufruf** — Der Weg, den ein Mensch wirklich geht (Oberfläche, Mappe, Vertrag), im Unterschied zum direkten Aufruf einer Funktion, dem man alles von Hand hineinreicht. Was auf dem einen Weg geht, kann auf dem anderen nie ankommen — geprüft wird darum auf dem Produktweg.

**Worker (local, cloud, ui)** — Die drei mitarbeitenden Stellen ausserhalb dieses Repos, jede mit anderen Mitteln: die Rechenmaschine zu Hause, der Vertrag von KosmoOrbit, die Oberfläche von KosmoOrbit. Jeder Auftrag nennt genau einen von ihnen.

**HomeStation** — Die Rechenmaschine zu Hause mit Grafikkarte, Blender und echten Modellgewichten (Worker «local»). Sie misst und rechnet, was hier nicht geht, und antwortet über Dateien im Repo.

**Durchsicht (durch einen zweiten Agenten)** — Ein zweiter Agent liest eine Änderung, ohne etwas anzufassen, und urteilt «taugt» oder «taugt nicht», mit Fundstellen. *Eine Zustimmung ohne eigene Fundstelle ist keine Durchsicht.*

**Open Font License (OFL)** — Eine freie Lizenz eigens für Schriften. Sie erlaubt, Schriften mit einer Software mitzuliefern, und verbietet nur den Verkauf der Schrift allein. *In diesem Projekt seit dem 22.09.2026 als einzige ausdrückliche Ausnahme von Regel 1 zugelassen* — nur für Schriften, nicht für Code.

**Tür (Anmeldung der Oberfläche)** — Die Anmeldung mit Kennwort, die die Visbox-Oberfläche schützt, sobald sie im Heimnetz erreichbar ist. Unangemeldet antwortet sie nur mit «nicht angemeldet» — ausser auf dem einen Weg zum Koppeln.

**Native App gegen Webseite** — Eine native App ist ein Programm, das eigens für ein Gerät geschrieben und dort installiert wird; eine Webseite läuft im Browser. Die App kommt an alles heran, was das Gerät kann — beim iPad etwa an den Doppeltipp des Stifts —, braucht aber einen Mac zum Übersetzen. *In diesem Projekt seit dem 22.09.2026:* Die iPad-Fassung von Visbox ist eine eigene App.

**Swift** — Die Programmiersprache von Apple für Apps auf iPad, iPhone und Mac. *In diesem Projekt* ist die iPad-App in Swift geschrieben; ihr Kern lässt sich auch unter Linux prüfen.

**SwiftUI** — Apples Baukasten für Bildschirme in Swift: Man beschreibt, was zu sehen ist, und das System zeichnet es. Die Ansichten der iPad-App sind in SwiftUI gebaut.

**PencilKit** — Apples Baukasten für das Zeichnen mit dem Apple Pencil: Strich, Druck, Radierer, Zurück. Die Zeichenfläche der iPad-App steht darauf.

**Xcode** — Apples Werkzeug auf dem Mac, mit dem Apps übersetzt und aufs Gerät gebracht werden. Ohne Mac gibt es kein Xcode — darum übersetzt in diesem Projekt eine Prüfstrecke auf GitHub die App.

**Swift Playgrounds** — Eine Apple-App, mit der man auf dem iPad selbst kleine Apps bauen und starten kann, ohne Mac. Die Visbox-App ist so angelegt, dass sie sich in Xcode **und** in Swift Playgrounds öffnen lässt.

**App-Paket (.swiftpm)** — Die Ablageform einer App, die Xcode und Swift Playgrounds beide verstehen: ein Ordner mit einer Beschreibung der App und ihren Quelltexten. *In diesem Projekt:* `ipad/Visbox.swiftpm`.

**Bundle-Kennung** — Der eindeutige Name, unter dem eine App bei Apple und auf dem Gerät geführt wird, in umgekehrter Adressform (etwa «ch.beispiel.visbox»). Zwei Apps mit derselben Kennung sind für das Gerät dieselbe. *In diesem Projekt* steht dort ein Platzhalter, den der Owner vor dem ersten Aufspielen ersetzt.

**Simulator** — Ein nachgebildetes iPad auf dem Mac, auf dem eine App laufen kann, ohne dass ein echtes Gerät angeschlossen ist. Die Prüfstrecke übersetzt die App dafür — das beweist, dass sie baut, nicht, dass sie am Gerät richtig läuft. Im Simulator gibt es keinen Stift — die Maus gilt dort als Finger. Darum nimmt die Zeichenfläche von Visbox nur im Simulator-Bau (der Übersetzung der App für den Simulator) jede Berührung als Strich; auf dem echten iPad zeichnet weiter nur der Stift (seit 23.10.2026).

**Prüfstrecke (auf GitHub)** — Ein automatischer Ablauf, der bei jedem Hochladen die Proben fährt und bei der iPad-App auf einem Mac übersetzt. Rot heisst: etwas ist kaputt, und derjenige, der hochgeladen hat, erfährt es sofort.

**Bonjour (mDNS)** — Apples Verfahren, mit dem sich Geräte im selben Netz gegenseitig finden, ohne dass jemand eine Adresse eintippt: Ein Gerät ruft «wer bietet Dienst X?», das passende antwortet. *In diesem Projekt* antwortet der Rechner, und das iPad sucht. Seit dem 13.10.2026
(Entscheid 83) sucht auch die Mac-App so nach dem Heim-PC im WLAN; der Heim-PC kündigt sich
dafür mit dem Programm `avahi-publish-service` an, wenn er mit `--heimnetz` läuft.

**Rundruf** — Eine Nachricht, die an alle Geräte im Netz zugleich geht statt an eines. *In diesem Projekt* ist der Rundruf die Art, wie sich der Rechner dem iPad bekannt macht (Owner-Entscheid 27), selbst geschrieben, ohne fremden Baustein.

**App Transport Security** — Die Regel von iOS, dass eine App nur verschlüsselt mit Servern spricht. Für Geräte im eigenen Heimnetz lässt sie sich gezielt lockern — die Visbox-App tut genau das und nichts darüber hinaus.

**Wegtafel** — Die Liste, in der der Server nachschlägt, welcher Programmteil eine Anfrage an einen bestimmten Weg (etwa «/api/skizze») beantwortet. Eine Tafel statt einer Kette von Wenn-dann-Abfragen: Neue Wege kommen dazu, ohne dass zwei Leute an derselben Stelle schreiben, und ein Wächter kann die Wege der App gegen die des Servers halten.

**Parkfach** — Der Ort auf dem iPad, an dem eine Skizze wartet, die noch nicht beim Rechner angekommen ist. Jede Skizze geht zuerst dorthin und von dort hinaus; ist der Rechner nicht erreichbar, bleibt sie liegen und geht später von selbst. Ist unklar, ob sie ankam, geht sie nur dann von selbst noch einmal, wenn sie ihren Schlüssel schon beim ersten Mal mitgeschickt hat (siehe *Doppelsendeschutz*), und höchstens fünfmal — sonst entscheidet ein Mensch. Angekommene Skizzen räumt das Fach nach sieben Tagen oder ab fünfzig Stück weg. *Stand 23.09.2026; bis zur Welle 2 ging eine ungewisse Skizze nie von selbst ein zweites Mal.*

**Schlüsselbund** — Der geschützte Speicher von iPad und Mac für Kennwörter. *In diesem Projekt* liegt dort das Kennwort der Kopplung — nicht in den gewöhnlichen Einstellungen, wo es eine frühere Fassung abgelegt und wieder verloren hatte. *Seit 21.10.2026* liegen am Mac auch das Zertifikat und der geheime Schlüssel für die Leitung zum iPad dort; in der Schlüsselbundverwaltung heissen sie «Visbox Mac …» (Zertifikat) und «Visbox · iPad-Leitung» (Schlüssel). Bis Fassung 0.3.54 sammelten sich nach jedem Update neue davon an — warum, steht unter *Zugriffsrecht im Schlüsselbund* (Protokoll 74 §278).

**Doppelsendeschutz** — Eine Vorkehrung, dass dieselbe Skizze nicht zweimal ankommt, wenn das iPad nach einem Abbruch noch einmal sendet: Jede Skizze trägt einen Schlüssel, und der Server erkennt ihn wieder. Derselbe Schlüssel mit einer **anderen** Zeichnung wird abgewiesen.

**Identität einer Ansicht** — Woran ein Bildschirm-Baukasten erkennt, dass ein Teil des Bildschirms nach einer Änderung *derselbe* ist wie vorher. Erkennt er ihn nicht wieder, wirft er ihn weg und baut ihn neu — samt allem, was darin lag. *In diesem Projekt:* Beim Drehen des iPads wurde das Zeichenblatt anfangs neu gebaut, und «Zurück» wirkte danach auf ein Blatt, das es nicht mehr gab. Seit der Welle 2 bleibt es dasselbe; am Gerät unbestätigt.

**Treffertest** — Wie das iPad entscheidet, welche Fläche eine Berührung bekommt, wenn mehrere übereinander liegen. Versteckte Flächen werden dabei übergangen — wer eine Fläche versteckt, nimmt ihr auch die Finger weg. *In diesem Projekt:* Darum wird eine ausgeblendete Ebene nicht versteckt, sondern mit einer leeren Schablone (Maske) verdeckt.

**Unterlage (einer Skizze)** — Das Bild, über das hineingezeichnet wird. Die Skizze selbst hat einen durchsichtigen Grund; erst der Rechner legt sie auf die Unterlage und gibt beides zusammen dem Bildmodell. Fehlt die Unterlage, liegt die Skizze auf mittlerem Grau — nicht auf Schwarz, das das Bild ins Dunkle ziehen würde (Annahme, nicht gemessen). *In diesem Projekt:* Die Webseite schickt die Unterlage mit, die App seit der Welle 2b ebenfalls (siehe *Blattunterlage*).

**Eingangsbild (des Nachrenders)** — Das Bild, das der Rechner aus Unterlage und Skizze zusammensetzt und dem Bildmodell als Ausgangsbild gibt. Hat die Unterlage ein anderes Seitenverhältnis als das Zeichenblatt, wird die **Skizze** auf die Unterlage gestreckt (nicht umgekehrt — das Bild behält seine Masse), und das steht als Hinweis am Bild. Die App zeigt die Unterlage nach derselben Regel, damit gezeichnet wird, wo gerechnet wird — am Gerät unbestätigt.

**Nachholen (nach einer Schreibkollision)** — Ein Lauf, der beim Speichern merkt, dass jemand anderes die Mappe inzwischen geändert hat, liest sie neu und trägt seine Vermerke auf den neuen Stand nach, statt ihn zu überschreiben. Die Alternative wäre eine Sperre — aber ein Lauf kann Stunden dauern, und so lange soll niemand ein Bild umbenennen oder eine Skizze ablegen müssen. Eine inzwischen verworfene Skizze bleibt dabei verworfen (Welle 2b).

**Handlungsquittung** — Die Antwort der App auf «Rechnen», «Abbrechen» oder «Namen geben», mit vier möglichen Ausgängen: angenommen, abgelehnt, ungewiss (die Leitung riss, bevor die Antwort kam) und nicht gesendet. Die Handlungsquittung ist die dritte Antwort, angewandt auf einen Knopfdruck: *Ob etwas geschah, ist eine Frage mit mehr als zwei Antworten.*

**Ebenen-Reihe** — Mehrere Ebenen einer Zeichnung, jede als eigene Skizze gerechnet, und die Ergebnisse nebeneinander als Varianten. Die andere Art, Varianten zu bekommen, ist dieselbe Skizze mit drei verschiedenen Zufallsstartwerten.

**Seitenfeld** — Die eine Spalte neben dem Zeichenblatt, die umschaltbar entweder die Ebenen oder die Mappe zeigt. Eine Spalte, nicht zwei — auf einem 11-Zoll-Bildschirm ist Platz das Knappste.

**Laufwächter** — Der Teil der App, der während eines Laufs öfter beim Rechner nachfragt, wie weit er ist, und danach einmal die Mappe neu holt.

**Aufklappbarer Vorbehalt** — Ein Vorbehalt, der in einer kleinen Bildkachel nur mit seinem festen Anfang steht («SKIZZE NICHT ANGEKOMMEN …») und sich durch Tippen ganz zeigt. Er darf gekürzt stehen, aber nie fehlen.

**Rumpffehler** — Eine Anfrage, deren Inhalt sich nicht aufschreiben lässt, etwa weil eine Zahl «unendlich» oder «keine Zahl» ist. Sie geht dann **nicht** hinaus und sagt, warum — statt still eine leere Anfrage zu schicken, die der Rechner als gültig nähme.

**Unicode-Zeilentrenner** — Unsichtbare Sonderzeichen, die in manchen Programmen eine neue Zeile beginnen, in anderen nicht. In einem Bildnamen würden sie die Anzeige zerreissen oder Zeilen vortäuschen; darum weist die Mappe sie ab.

**Signifikante Stellen** — Die Ziffern einer Zahl, die etwas aussagen, gezählt ab der ersten, die nicht null ist. Zwei Zahlen, die sich erst in der sechzehnten Stelle unterscheiden, sehen mit vier Stellen gleich aus. *In diesem Projekt:* Die Anzeige zeigt so viele Stellen, bis sich eine Zahl von ihrer Schwelle unterscheidet — höchstens siebzehn —, damit ein knapp verfehlter Wert nie als «gleich» dasteht.

**Unicast** — Eine Nachricht an genau ein Gerät, im Gegensatz zum *Rundruf* an alle. *In diesem Projekt* von Belang, weil ein zweites Programm, das ebenfalls auf Rundrufe hört, einem schon laufenden Dienst die direkten Nachrichten wegnehmen kann — geprüft unter Linux, am echten Rechner offen.

**Bekanntes, abgewiesenes Feld** — Ein Feld aus dem Vertrag von KosmoOrbit, das wir kennen und trotzdem ablehnen, mit einem eigenen Satz, warum. Im Unterschied zu einem **unbekannten** Feld, bei dem wir nur sagen können, dass wir es nicht kennen. Beide halten den Lauf an; still übergangen wird keines.

**Innenraum-Bestellung** — Eine Bestellung aus KosmoOrbit, die eine Ansicht **aus einem Raum heraus** will statt von aussen. Sie kommt mit einem IFC-Modell und meist mit den drüben schon gewählten Innenkameras. Bis zum 22.09.2026 wies unsere Seite jede solche Bestellung ab, weil sie das Feld nicht kannte.

**Blattunterlage** — Das Bild aus der Mappe, das in der App **unter** den Zeichenebenen liegt, damit man hineinzeichnen kann. Sie ist keine Ebene: Man radiert nicht auf ihr, und sie wird nicht mitgeschickt — der Rechner hat das Bild ja schon; mit geht nur sein Name. Eine **ausgeblendete** Unterlage geht nicht mit, weil gerechnet wird, was sichtbar ist (Entscheid 7). *Stand 23.09.2026, am Gerät unbestätigt.*

**Darauf skizzieren** — Der Knopf in der Bildansicht der App, der ein fertiges Bild zur Blattunterlage macht. Damit schliesst sich der Kreis: Bild ansehen, hineinzeichnen, neu rechnen lassen. Das Wort steht noch auf keinem Blatt der Entwurfsfläche; es wird nachgezeichnet.

**Ablageplan** — Die Regel im Kern der App, die vor «In die Mappe legen» entscheidet, was ins Parkfach geht — und was nicht, mit einem Satz: etwa eine Unterlage aus einer anderen Mappe, die der Rechner sonst erst beim Rechnen abweisen würde, oder eine Unterlage ganz ohne Striche.

**Fachzählung** — Die getrennte Zählung im Knopf zum Parkfach: geparkt, ungewiss, unterwegs, offen. Vorher stand dort eine einzige Zahl, die ungewisse Skizzen mitzählte, als wären sie geparkt — dasselbe Wort für zwei Zustände.

**Aufräumfehler** — Eine alte, längst angekommene Skizze, die sich nicht löschen liess. Er wird gemeldet, bringt aber nichts zu Fall: Aufräumen darf nie verhindern, dass das Parkfach aufgeht oder eine Ankunft festgehalten wird. *Vorher* konnte eine einzige nicht löschbare Datei das ganze Fach sperren.

**Zug (Stiftzug)** — Alles vom Aufsetzen des Stifts bis zum Abheben. Die App prüft teure Dinge — etwa, ob nach dem flächigen Radieren noch etwas zu sehen ist — erst am Ende eines Zugs statt bei jeder kleinen Bewegung.

**Berührungsart** — Ob eine Berührung vom Finger, vom Stift oder von einem Zeiger kommt. Eine Geste kann festlegen, welche Arten sie annimmt. *In diesem Projekt:* Der Finger schiebt und zoomt, der Stift zeichnet (Entscheid 4) — und auf einer ausgeblendeten Ebene schiebt der Stift auch nicht, ausser mit dem Werkzeug Hand.

**Deckungsbild** — Ein gemaltes Bild, so wie es im Speicher liegt: je Bildpunkt ein paar Zahlen, eine davon sagt, wie stark er deckt. Die App liest daraus, ob eine Ebene nach dem Radieren noch etwas zeigt. In welcher Reihenfolge die Zahlen liegen (die *Byte-Reihenfolge*), sagt das Bild selbst; liest man sie falsch, hält man eine Farbe für die Deckung — darum ist dieser Teil am Gerät zu prüfen.

**Einbausperre** — Ein Fehler, der verhindert, dass etwas Gebautes drüben überhaupt ankommt — nicht, dass es falsch rechnet, sondern dass es gar nicht rechnet. *In diesem Projekt:* Die Brücke kannte nur `model.glb`, KosmoOrbit schreibt aber `model.ifc`; jede Innenraum-Bestellung wäre trotz angenommenem Feld liegen geblieben. Behoben in der Welle 2b.

**Reine Absicherung** — Eine Prüfung, die der gewöhnliche Weg durch das Programm nie erreicht, weil eine frühere Stelle den Fall schon ausschliesst. Sie bleibt stehen, falls sich die frühere Stelle einmal ändert — wird aber **so genannt** und an einem eigens gebauten Fall geprüft, damit niemand glaubt, sie schütze den Alltag.

**Bereich der Anmeldung (realm)** — Der Name, den ein Browser im Anmeldefenster zeigt, wenn eine Seite ein Kennwort verlangt. *In diesem Projekt* ist es der Name der App aus der einen Namenskonstante — damit er nach der Abgabe mit KosmoSketch mitwechselt.

**Prüfsumme im Dateinamen** — Ein kurzer Fingerabdruck, an einen Dateinamen gehängt, damit zwei gleich benannte Dateien aus verschiedenen Ordnern sich nicht gegenseitig überschreiben. *Gefunden in der Welle 2b:* Ohne ihn rechneten zwei Ebenen einer Reihe beide auf der zweiten Zeichnung.

**Mitgesandte Kamera** — Ein Standpunkt, den KosmoOrbit selbst berechnet, benennt und mit der Bestellung mitschickt. Bei einer Innenraum-Bestellung ist das heute der Normalfall: Wir wählen dann **keinen** Raum und rechnen keinen zweiten Standpunkt, sagen aber im Ergebnis, dass eine Innenansicht bestellt war und der Standpunkt von drüben kommt.

**Neuzentrierung** — Ein Modell an den Ursprung schieben, bevor es gerechnet wird. Nötig, wenn ein Gebäude mit echten Landeskoordinaten kommt, also Hunderttausende Meter vom Nullpunkt entfernt: In dieser Entfernung werden die Zahlen, mit denen das Austauschformat rechnet, grob, und Kanten wackeln. Unser Weg zentriert **nicht** neu; empfiehlt die Prüfung es, steht das seit dem 23.09.2026 als Warnung im Befund statt still wegzufallen.

**Gleichwertige Mutation** — Eine absichtliche Änderung am Code, die das Verhalten gar nicht ändert — etwa das Weglassen eines Werts, der ohnehin schon gleich gesetzt ist. Keine Probe kann sie fangen, und das ist kein Mangel der Probe. Man nennt sie beim Namen, damit ein grünes Ergebnis nicht mit einer Lücke verwechselt wird.

**Abschrift-Probe** — Eine Probe für eine Regel, die an zwei Orten steht, weil zwei Programme sie brauchen und keines das andere lesen kann — hier die App (Swift) und der Rechner (Python). Die Probe liest die Abschrift aus dem Quelltext der App und hält sie gegen das laufende Original des Rechners. Ändert jemand die Regel an einem Ort, fällt die Probe. *In diesem Projekt:* die Regel, wann eine Unterlage gestreckt wird.

**Zweiter Zustand (eines Entwurfsblatts)** — Dasselbe Blatt der Entwurfsfläche in einer anderen Lage, per Schalter auf dem Blatt oder als zweite Lage darunter — wenn das Blatt voll ist und ein neues nicht angelegt werden soll (eine Fläche, nicht viele).

**Owner-Entscheid offen (Schild)** — Eine Markierung auf einem Entwurfsblatt für etwas, das so gebaut **und** so gezeichnet ist, dessen Wort oder Farbe der Owner aber nicht gewählt hat. Sie verhindert, dass ein Vorschlag des Baus beim nächsten Lesen wie ein Entscheid aussieht.

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

**Anwendungsdatenordner** — Der Ort, den ein Betriebssystem einer Anwendung für ihre
eigenen Dateien zuweist.
*Wozu:* Jedes System hat einen anderen, und keiner davon ist frei wählbar. Auf macOS ist
es `~/Library/Application Support`, auf Windows `%LOCALAPPDATA%`, auf Linux
`~/.local/share`. Wer stattdessen einen eigenen Ordner direkt unter der Systemwurzel
verlangt — im Projekt war das `/ai` — bekommt auf dem Laptop einer Studierenden einen
Rechtefehler aus dem Inneren einer Bibliothek, bevor überhaupt etwas geladen ist. Auf
Windows gibt es diesen Ordner gar nicht.
*Wo im Projekt:* `aiimaging.render.anwendungsdaten_wurzel`; `/ai` gilt weiterhin, **wenn
es den Ordner gibt**, damit bestehende Maschinen nichts umstellen müssen.

**Zeitfaktor (für Fristen)** — Ein Multiplikator, mit dem alle Zeitgrenzen einer Software
an ein langsameres Gerät angepasst werden, ohne jede einzelne Zahl zu ändern.
*Wozu:* Die Fristen im Projekt (fünf Minuten für einen IFC-Import, fünfzehn für einen
Render) sind auf der schnellen HomeStation gemessen. Auf einem Laptop wäre dieselbe Frist
ein Abbruch mitten in einer gesunden Rechnung — und der sieht aus wie ein Fehler, obwohl
nur die Uhr zu knapp stand. Ein Faktor von 3 verdreifacht alle Fristen auf einmal.
*Wo im Projekt:* `AIIMAGING_ZEITFAKTOR`, gelesen von `aiimaging.seams.zeitfaktor`.

**Einlass (Sichtgang an der Tür)** — Eine kurze Prüfung, die eine Datei ansieht und in
einem Satz sagt, ob mit ihr zu rechnen ist — **bevor** die teure Rechnung beginnt.
*Wozu:* Ein Import kann eine halbe Stunde dauern. Erfährt jemand erst danach, dass die
Datei gar keine ist, hat er die halbe Stunde verloren. Der Sichtgang liest nur den
Dateianfang und ist darum bei einer 500-MB-Datei so schnell wie bei einer 5-KB-Datei.
*Wo im Projekt:* `aiimaging.einlass.sichte` — «Datei hinein, ein Satz heraus».

**Das Format am Inhalt statt an der Endung bestimmen** — Nachsehen, womit eine Datei
*beginnt*, statt dem zu glauben, was hinter dem Punkt im Namen steht.
*Wozu:* Eine Endung ist eine Behauptung dessen, der die Datei benannt hat; der
Dateianfang ist eine des Programms, das sie geschrieben hat. Wer eine Datei umbenennt,
ändert nur die erste. Im Projekt endete eine als `.ifc` umbenannte Fotodatei darum in
einem Absturz tief in einer fremden Bibliothek — statt in dem Satz «das ist ein Bild und
kein Modell».
*Wo im Projekt:* `aiimaging.einlass` und `aiimaging.herkunft.deute`.

**Eine Absage ohne Ausweg ist eine halbe Auskunft** — Wer etwas ablehnt, sagt dazu, wie
man weiterkommt.
*Wozu:* «SketchUp kann ich nicht» beendet den Versuch. «SketchUp kann IFC ausgeben, Datei
→ Exportieren → IFC» setzt ihn fort. Der Unterschied kostet einen Satz und entscheidet,
ob jemand das Werkzeug ein zweites Mal öffnet.
*Wo im Projekt:* Jeder Eintrag in `einlass.FREMDE_FORMATE` führt einen Rat mit, und eine
Probe hält das für jeden künftigen Eintrag fest.

**Ansage gegen Messauftrag** — Zwei Dinge, die eine Datei nicht gleichzeitig sein sollte:
die Mitteilung, dass sich etwas ändert, und die Bitte, etwas zu messen.
*Wozu:* Eine Ansage ist **eilig und billig** — sie muss gelesen werden, bevor der
Adressat den neuen Stand übernimmt, und kostet ihn eine Minute. Ein Messauftrag ist
**träge und teuer** — er kann Tage warten und kostet Rechenzeit. Steht beides in einer
Datei, wartet der eilige Teil hinter dem trägen, und zwar genau so lange wie die ganze
Warteschlange.
*Wo im Projekt:* Am 19.09.2026 nachgezählt: Von sechzehn offenen Aufträgen an die
HomeStation waren zwei reine Ansagen — und **vier weitere nannten sich im ersten Satz
Ansage und verlangten in der Rückgabe Messwerte.**

**Nachfrage gegen Mahnung** — Der Unterschied zwischen «du hast das übergangen» und «wir
wissen nicht, ob es bei dir angekommen ist».
*Wozu:* Bleibt eine Antwort aus, gibt es dafür mindestens vier Gründe, und nur bei einem
davon ist eine Nachfrage berechtigt: wenn der Adressat **nach** diesem Auftrag anderes
beantwortet hat. Dann war er da, und dieser blieb liegen. In allen anderen Fällen — nie
zugestellt, zu frisch, seither gar kein Lebenszeichen — sagt das Ausbleiben nichts über
ihn, sondern über uns, und eine Mahnung wäre eine Unterstellung.
*Wo im Projekt:* `aiimaging.auftragspost.warum_keine_antwort`. Beim ersten Lauf
rechtfertigten von achtzehn Aufträgen genau **zwei** eine Nachfrage. *Ohne die Messung
hätte ich achtzehn gemahnt — sechzehn davon zu Unrecht, und beim siebzehnten hätte es
niemand mehr gelesen.*

**Eine Ablehnung schliesst einen Posten so gut wie eine Erledigung** — Und manchmal
besser.
*Wozu:* Ein abgelehnter Auftrag («machen wir nicht, weil X») verschwindet aus der
Zählung. Ein schweigender bleibt darin stehen und verdeckt die Posten, auf die es
ankommt. Wer nur Erledigungen als Abschluss zählt, züchtet sich eine Liste, in der das
Wichtige zwischen dem Unentschiedenen verschwindet.
*Wo im Projekt:* Ausdrücklich so verlangt in `auf-20260919-118` an `cloud`.

**Absoluter Pfad, und warum er vom System abhängt** — Eine vollständige Adresse einer
Datei, die von der Wurzel aus gilt und nicht davon, wo man gerade steht.
*Wozu:* Was als vollständig gilt, ist je System verschieden. `/home/x/datei` ist unter
Linux und macOS vollständig, `C:\Users\x\datei` unter Windows. Lässt man einen
Linux-Rechner über einen Windows-Pfad urteilen, hält er ihn für **unvollständig** — und
eine Prüfung, die unvollständige Pfade abweist, weist ihn ab. Am 18.09.2026 fiel dadurch
der ganze Windows-Weg der Modellablage durch die Prüfung, ohne dass eine einzige Probe
rot wurde: Das Ergebnis war zufällig trotzdem brauchbar, weil ein Ersatzwert einsprang.
*Wo im Projekt:* `aiimaging.render._ist_absolut` rechnet nach den Regeln des **gemeinten**
Systems, nicht des laufenden.

**Grössenriegel** — Eine Prüfung, die verhindert, dass eine Modellgrösse behauptet wird,
die niemand nachgemessen hat.
*Wozu:* Bei manchen Modellfamilien hängt die Lizenz an der Grösse — die kleine Fassung ist
frei verwendbar, die grosse nicht. Steht im Namen eine Zahl, die nicht zur tatsächlichen
Grösse passt, ist das kein Schönheitsfehler, sondern eine mögliche Lizenzverletzung.
*Wo im Projekt:* `aiimaging.backbone.groessen_riegel`.

**Gebaut, am Gerät unbestätigt** — Ein **dritter** Zustand für einen Posten, der
eingebaut werden soll: hier fertig, drüben noch nie ausprobiert.
*Wozu:* Ohne ihn gibt es nur «erledigt» und «offen», und beide sagen etwas Falsches.
«Erledigt» behauptet eine Bestätigung, die niemand gegeben hat; «offen» behauptet Arbeit,
die längst getan ist. *Es ist dieselbe dritte Antwort wie bei einer Messung, die nicht
möglich war — angewandt auf den Einbau.*
*Wo im Projekt:* `docs/EINBAU_STAND.md`; gezählt von `aiimaging.einbau`.

**Abgelegt ist nicht zugestellt** — Der Unterschied zwischen «der Auftrag liegt bei uns
in der richtigen Schublade» und «der Auftrag ist bei dem angekommen, der ihn ausführen
soll».
*Wozu:* Manche Empfänger haben unser Repo gar nicht. Für sie ist eine Datei bei uns
unsichtbar. In einer Rückstandsliste sah das bisher genauso aus wie ein zugestellter
Auftrag, auf den niemand antwortet — und es ist das Gegenteil: ein Rückstand beim
**Absender**. *Er kann nicht beantworten, was er nicht hat.*
*Wo im Projekt:* `aiimaging.auftragspost.unzugestellt`; die Meldung steht bewusst ganz
oben in `tools/einbau.py`.

**Handeingriff** — Wenn ein Mensch in ein erzeugtes Bild hineinmalt, es beschneidet oder
sonst von Hand verändert, bevor damit weitergerechnet wird.
*Wozu:* Danach lässt sich nicht mehr sagen, ob eine Abweichung vom Gebäudemodell vom
Bildmodell stammt oder von der Hand. Die Prüfung sagt darum **«nicht anwendbar»** statt
einer Zahl — und dieser Vorbehalt wird an jedes daraus entstehende Bild weitergereicht.
*Ein Vorbehalt, der beim Weiterrechnen verfällt, ist keiner.*
*Was er seit dem 19.09.2026 nicht mehr tut:* das Urteil über die Geometrie **darunter**
mit wegwerfen. Das Bild ist dann ein **AI-Imaging-Layer** und führt das **Basis-Urteil**
mit. Der Handeingriff ist im Projekt die Ursache, aus der ein Bild zur zweiten Stufe wird.
*Wo im Projekt:* `aiimaging.kette`, Feld `handeingriff`.

**Geometrielayer und AI-Imaging-Layer** — Die zwei Stufen, aus denen ein fertiges Bild in
diesem Projekt besteht.
*Wozu:* Die **erste** Stufe wird aus dem Gebäudemodell gerechnet und gegen dessen Form
nachgemessen; sie trägt ein echtes Urteil. Die **zweite** Stufe liegt darauf: dort werden
Bildpunkte verändert — Lichtstimmung, Materialien, Varianten —, so wie man es sonst in
einem Bildbearbeitungsprogramm täte, hier aber über KI. Sie trägt **kein eigenes** Urteil
über die Form, wohl aber das ihrer Unterlage.
*Die eine bindende Regel:* Ein geerbtes Urteil ist kein eigenes, und beide dürfen nie im
selben Feld stehen. *Ein Vorbehalt soll die Auskunft einschränken, nicht sie löschen.*
*Abgrenzung:* Mit der **Ebene (Layer) in einer Bilddatei** (Abschnitt 5) hat das nichts zu
tun. Dort ist «Layer» eine technische Spur in einer Datei; hier eine Stufe der Entstehung.
*Wo im Projekt:* Entscheid E20 in `docs/ENTSCHEIDE_VISBOX_2026-09-18.md`; gebaut am
19.09.2026 in `aiimaging.kette` — Feld `schicht` sagt, welche Stufe ein Bild ist, Feld
`basis` trägt das Urteil der Unterlage. Das eigene Urteil heisst weiterhin `bestanden`;
das geerbte heisst `basis.geometrie_bestanden` und **nie** gleich.

**Importeur (3D-Modell-Importeur)** — Der erste Schritt der Software: Er nimmt die
Modelldatei entgegen, die jemand hineinzieht, und macht daraus die eine Form, mit der
alles Weitere rechnet.
*Wozu:* Architekturprogramme geben ganz verschiedene Dateiarten aus. Ohne Importeur
müsste die Benutzerin ihre Datei zuerst selbst in ein anderes Programm laden und dort
umwandeln — *ein Werkzeug, das den Weg kennt und ihn dem Benutzer aufträgt, hat die Arbeit
nicht getan, sondern verteilt.*
*Die drei Wege:* durchreichen (die Datei ist schon im Zielformat), über die IFC-Naht, oder
über einen Blender-Aufruf als eigenständiges Programm.
*Wo im Projekt:* `aiimaging.importeur`, seit dem 21.09.2026.

**Durchreichen** — Eine Datei unverändert weitergeben, statt sie umzuwandeln.
*Wozu:* Jede Umwandlung kann etwas verlieren — Materialnamen, die Gliederung in Bauteile,
Zusatzangaben. Eine Umwandlung, an deren Ende dasselbe Format steht wie am Anfang, kann
darum nur verlieren. *Und sie sieht hinterher aus wie eine gelungene Umwandlung*, weshalb
im Bericht ausdrücklich steht, dass nichts umgewandelt wurde.
*Wo im Projekt:* `importeur.WEG_DURCHGEREICHT`.

**Rundreise mit bekannter Wahrheit** — Eine Prüfung, bei der dieselbe Geometrie einmal im
Kreis durch mehrere Formate geschickt und am Ende mit den Massen verglichen wird, mit
denen sie ursprünglich geschrieben wurde.
*Wozu:* Bei einer echten Datei weiss niemand, wie gross das Gebäude «wirklich» ist — man
müsste es mit demselben Werkzeug ausrechnen, das man prüfen will. Bei einer selbst
erzeugten Datei kennt man jede Kante, *weil man sie geschrieben hat.* Erst dadurch lässt
sich sagen, ob eine Umwandlung stimmt oder bloss durchgelaufen ist.
*Wo im Projekt:* `aiimaging.konversionstreue`; bestellt als Messung in
`auf-20260921-126`.

**Der Vorgabewürfel** — Der Würfel, den Blender beim Start von sich aus in jede neue Szene
stellt.
*Wozu er hier vorkommt:* Bliebe er stehen, wanderte er beim Import in die Ausgabedatei, in
die Hüllbox und damit in jede Kameraberechnung. Ein zwei Meter grosser Würfel neben einem
Gebäude verschiebt den Bildausschnitt, *und niemand sieht ihm an, woher er kommt.* Der
Import räumt die Szene darum zuerst leer.
*Wo im Projekt:* `runners/blender_import_runner.py`, Funktion `_leere_szene`.

**Fassung des Modells (in einer Mappe)** — Lädt man dieselbe Datei noch einmal (weil man sie
weitergezeichnet hat), entsteht keine zweite Mappe, sondern in derselben eine **neue Fassung**: Das Modell
wird ausgetauscht, die bisherigen Bilder und Skizzen bleiben. Die Mappe merkt sich, bis zu welchem Bild die
alte Fassung galt — so lässt sich der alte Stand mit dem neuen vergleichen. *Im Projekt:* Entscheid 90b,
`arbeitsgang.ersetze_modell`, Feld `modell.fassung` und Liste `modell_fassungen`.

**Start-Mappe** — Die Mappe, mit der der Visbox-Server am Heim-PC gestartet wurde (`--ordner`). Neue
Mappen aus «Datei laden …» kommen **daneben**, in denselben übergeordneten Ordner (Entscheid 90a), und
heissen wie die Datei — nur mit Buchstaben, Ziffern, `-` und `_`.

**Geschlossenes Dateiformat** — Ein Format, das nur das Programm lesen kann, das es geschrieben hat,
weil sein Aufbau nicht veröffentlicht ist — etwa die `.pln` von ArchiCAD oder die `.rvt` von Revit. Statt
«unbekannt» sagt Visbox dann, wie man im Programm eine offene Fassung (IFC) speichert (Entscheid 90c).

**Projekt (die Mappe)** — Der Ort, an dem die Arbeit an *einem* Gebäudemodell
zusammenbleibt: welches Modell, welche Einstellungen, welche Bilder daraus entstanden sind
und was die Prüfung zu jedem gesagt hat.
*Wozu:* Ohne ihn lebt jede Fähigkeit in ihrem eigenen Aufruf, und was dabei herauskommt,
liegt in Ordnern, deren Zusammenhang nur im Kopf dessen besteht, der sie angelegt hat.
*Was nicht in einer Datei steht, ist weg.*
*Die Besonderheit:* Das Projekt **verweist** auf das Modell, statt es zu kopieren — eine
Kopie wäre eine zweite Wahrheit auf der Platte, und wer danach die eine ändert, hat zwei
Gebäude.
*Wo im Projekt:* `aiimaging.projekt`, seit dem 21.09.2026.

**Fingerabdruck (einer Datei)** — Eine kurze Zeichenfolge, an der sich eine Datei
wiedererkennen lässt, ohne sie ganz aufzubewahren.
*Wozu:* Damit beim nächsten Öffnen gesagt werden kann, ob das Gebäudemodell noch dasselbe
ist. Ist es ein anderes geworden, wird **nichts** neu gerechnet und nichts verworfen — es
wird gemeldet. Die bisherigen Messungen gehören zum alten Stand und gelten dafür weiter.
*Und der Vorbehalt gehört dazu:* Bei grossen Dateien werden nur Anfang und Ende gelesen.
Das erkennt eine ersetzte Datei zuverlässig und eine Änderung mitten in einer grossen
möglicherweise nicht. Der Abdruck sagt darum selbst, welcher Art er ist — *eine Prüfsumme
ohne Angabe, worüber sie läuft, behauptet mehr, als sie weiss.*
*Wo im Projekt:* `aiimaging.projekt.fingerabdruck`.

**Arbeitsgang** — Die Stelle, an der die einzelnen Fähigkeiten zu einem Ablauf werden:
Modell hereinholen, Bilder rechnen, Urteil in die Mappe schreiben.
*Wozu:* Ohne ihn kann die Software jedes Stück einzeln, und niemand ruft sie in der
richtigen Reihenfolge. *Ein gebautes Modul ohne Aufrufer ist kein Werkzeug, sondern ein
Vorrat.*
*Was er ausdrücklich nicht tut:* selbst rechnen. Er ruft und schreibt auf. Täte er mehr,
wäre er die Stelle, durch die alles hindurch muss — und dann wäre die Bibliothek keine
Bibliothek mehr, sondern ein Programm mit einem Einstiegspunkt.
*Wo im Projekt:* `aiimaging.arbeitsgang`, seit dem 21.09.2026.

**Hochachse** — Welche der drei Raumrichtungen im Gebäudemodell «oben» ist.
*Wozu das eine Frage ist:* Manche Programme schreiben Z nach oben, andere Y. Das
Austauschformat glTF hat dafür **gar kein Feld**. Wird die Achse falsch angenommen, liegt
das Gebäude auf der Seite — und das fällt nirgends auf, weil Tiefenkarte, Kamera und
Prüfung **gemeinsam** mitkippen. Das Ergebnis ist dann in sich stimmig und vollständig
falsch.
*Darum wird sie nicht geraten:* Hat die Software die Datei selbst umgewandelt, weiss sie
es aus dem eigenen Lauf. Kam eine fremde Datei herein, fragt sie nach. Eine IFC trägt die
Angabe von sich aus — *der Weg über IFC beantwortet die Frage, statt sie zu stellen.*
*Wo im Projekt:* `aiimaging.contracts.normalize_up_axis`, `aiimaging.hochachse`,
`aiimaging.arbeitsgang.rechne`.

**Die Oberfläche (von Visbox)** — Das Fenster, in dem man das Programm bedient: Projekt
öffnen, Modell und Bilder ansehen, einen Lauf starten.
*Wo sie liegt und warum dort:* **Ausserhalb** des Programmkerns, im Ordner `oberflaeche/`.
Regel 4 verlangt, dass jede Fähigkeit ohne Fenster nutzbar bleibt — *was nur über einen
Klick erreichbar ist, existiert nicht.* Läge die Oberfläche im Kern, wäre sie irgendwann
dessen Voraussetzung.
*Womit sie gebaut ist:* mit dem, was in Python selbst steckt, und einer Seite, die man im
Browser öffnet. Kein zugekaufter Baukasten — die üblichen sind copyleft (Regel 1), und was
zum Start eine Netzverbindung braucht, ist kein Ein-Klick-Download.
*Die Auflage, um die es geht:* Ein **ungeprüftes** Bild darf nie aussehen wie ein
bestandenes — und auch nicht wie gar nichts. *Kein Abzeichen sieht aus wie kein Problem.*

**Ausbesserung (Inpainting)** — Einem Bildmodell einen **Bereich** vorgeben und sagen, was
dort hin soll, während es den Rest des Bildes nicht anfassen darf.
*Wozu:* Damit lässt sich etwas ins fertige Bild setzen, das im Gebäudemodell gar nicht
vorkommt — ein Mensch, ein Gerät, ein Möbelstück.
*Wie der Bereich übergeben wird:* als **Maske**, ein zweites Bild in derselben Grösse, in
dem hell heisst «hier darf gearbeitet werden» und dunkel «Finger weg». Die Graustufen
dazwischen sind der weiche Übergang — ohne ihn sitzt das eingesetzte Stück wie
ausgeschnitten im Bild.
*Stand 21.09.2026:* **Bei Visbox nicht möglich**, und das ist gemessen: Das
Vorgabe-Bildmodell nimmt überhaupt kein Eingangsbild an — ein Lauf mit Bild liefert
Byte für Byte dasselbe wie einer ohne.
*Und die Folge fürs Urteil:* Ein ausgebessertes Bild bekommt **kein** Geometrie-Urteil
mehr, sondern «nicht anwendbar» — die Prüfung vergleicht mit dem Modell, und was jemand
hineingesetzt hat, steht dort nicht.

**Bestellter und gerechneter Modus** — Zwei Angaben am Ergebnis eines Bildlaufs: die
Betriebsart, die der Aufrufer **wollte**, und die, die tatsächlich **gelaufen** ist.
*Warum getrennt:* Weil sie auseinanderfallen können, ohne dass jemand etwas falsch macht.
Bestellt wird ein Bild «ausgehend von unserem Render»; kann das Modell kein Eingangsbild
annehmen, wird daraus ein reines Textbild — ein gültiges Bild, nur ein anderes.
*Wo es vorkommt:* `render.py` schreibt `modus_bestellt` und `modus_gerechnet` an jedes
Ergebnis und legt einen Hinweis im Klartext dazu, wenn die beiden verschieden sind.
*Warum nicht abgebrochen wird:* Das Bild ist brauchbar. *Falsch war nicht der Lauf,
sondern die Auskunft über ihn.*

**Verträglichkeitsfilter** — Die Stelle, an der vor dem Bildlauf geprüft wird, welche der
vorbereiteten Angaben das gewählte Modell überhaupt kennt. Was es nicht kennt, wird
weggelassen, statt den Lauf abstürzen zu lassen.
*Warum er nötig ist:* Jedes Bildmodell nimmt andere Angaben entgegen. Ohne diesen Filter
stürbe jeder Lauf am ersten unbekannten Wort.
*Und wo die Gefahr liegt:* Eine Angabe kann **zweimal** vorkommen — hineingelegt und
wieder hinausgeworfen. Wer nur die eine Liste liest, sieht ein Eingangsbild ankommen, das
nie angekommen ist. Genau daraus entstand der bestellte/gerechnete Modus.


**Architekturbild (Organigramm der Programme)** — Ein Bild, das zeigt, welche Programme es gibt, wo
sie laufen und wer wem was übergibt — wie ein Organigramm, nur für Software statt für Personen.
*Im Projekt:* Tafelkarte `architektur-00-uebersicht` und das Mermaid-Bild in
`docs/WERKZEUGE_UND_ARCHITEKTUR.md`.

**OpenSSL** — Das verbreitete Programm für Verschlüsselung und Zertifikate (Apache-2.0). *Im
Projekt:* erzeugt am Heim-PC einmal das eigene Zertifikat für das verschlüsselte Heim-WLAN
(`--heimnetz`), als eigenes Programm aufgerufen.

**Avahi** — Ein Linux-Programm, das einen Dienst im lokalen Netz bekannt macht, damit andere Geräte
ihn ohne Adresse finden (LGPL-2.1). *Im Projekt:* meldet den Heim-PC im WLAN, damit der Mac ihn
findet; als eigenes Programm aufgerufen, nicht eingebunden.

**libnotify (notify-send)** — Ein Linux-Programm, das eine kurze Meldung am Bildschirm einblendet
(LGPL-2.1). *Im Projekt:* zeigt am Heim-PC die Zahl zum Koppeln des Mac; als eigenes Programm
aufgerufen.

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

## 10 · Oberfläche und Entwurf

**CSS (Stilregeln)** — Die Sprache, in der eine Web-Oberfläche ihr Aussehen beschreibt: Farben, Abstände, Schriften,
wo ein Element steht. Jede Regel nennt zuerst, *wofür* sie gilt (den Selektor, etwa «alle Leisten der KI-Maus»), und dann
in geschweiften Klammern, *was* gilt. *Im Projekt:* die `.css`-Dateien der Knotenansicht, im Bau zu einer Datei
zusammengehängt.

**Offene Klammer (im CSS)** — Fehlt in einer Stilregel die schliessende Klammer, gilt alles, was danach kommt, als *Teil*
dieser Regel: Moderne Browser lesen Regeln in Regeln («verschachtelt») und wenden sie nur innerhalb des äusseren Elements
an. Weil der Bau alle Stildateien hintereinander hängt, trifft eine offene Klammer auch die Regeln der folgenden Dateien.
Die einzelne Datei sieht dabei richtig aus — der Fehler zeigt sich erst im Bau. *Im Projekt:* Befund 305 B1, eine fehlende
`}` nach `.vis-raster-gross-urteil` liess Leiste, Figur, Sperrzonen und die Inseln ungestaltet; bewacht von
`kosmo-maus-im-bau.test.ts`, das den Bau liest.

**SVG (Vektorgrafik im Browser)** — Ein Bildformat, das aus Formen statt aus Bildpunkten besteht (Linien, Kreise,
Rechtecke) und im Browser wie ein Teil der Seite behandelt wird. Manche Stilregeln für gewöhnliche Elemente wirken dort
nicht — ein Umriss (`outline`) etwa wird um eine SVG-Gruppe nicht gezeichnet; dort braucht es eine eigene Form mit Strich.
*Im Projekt:* die Knoten der Knotenansicht; der gestrichelte Rahmen am Knopf «Node löschen» ist darum ein eigenes
Rechteck.

**Entwurfsblatt (Artboard)** — Ein einzelner gezeichneter Bildschirm in einem
Entwurfsdokument: ein Rechteck in der Grösse, die das Gerät später hat, mit allem darin,
was der Benutzer dort sähe. Ein Entwurfsblatt ist ein Bild eines Programms, nicht das
Programm — es tut nichts, es zeigt nur, wie es aussehen soll.
*In diesem Projekt: die acht Blätter der iPad-Oberfläche.*

**Entwurfsfläche** — Die gemeinsame, beliebig grosse Fläche, auf der mehrere
Entwurfsblätter nebeneinander liegen, so dass man den ganzen Ablauf auf einen Blick sieht
statt Bild für Bild. Man schiebt und zoomt darin wie auf einer Landkarte.

**Berührungsfläche (Touch-Ziel)** — Die Fläche, die ein Bedienelement auf einem
Berührungsbildschirm anbieten muss, damit eine Fingerkuppe sie zuverlässig trifft. Als
Untergrenze gelten 44 Bildpunkte in beide Richtungen. Kleiner heisst: Es sieht bedienbar
aus und ist es nicht.

**Kontrastverhältnis** — Eine Zahl dafür, wie deutlich sich Schrift von ihrem Untergrund
abhebt. 1 zu 1 hiesse unsichtbar; als Mindestmass für gewöhnliche Schriftgrösse gilt
4.5 zu 1. Die Zahl lässt sich aus den beiden Farben ausrechnen, sie ist also keine
Geschmacksfrage.
*In diesem Projekt: Das Rot für «durchgefallen» kam auf dem dunklen Grund nur auf 4.06 zu 1
und wurde für das iPad eine Stufe heller gesetzt.*

**Druckempfindlichkeit** — Die Fähigkeit eines Stiftes, zu melden, wie fest er aufgedrückt
wird. Die Oberfläche kann daraus die Strichbreite oder die Deckkraft ableiten — welche von
beiden, ist eine Entwurfsentscheidung und keine Eigenschaft des Stiftes.

**Wortzeichen** — Der Name eines Produkts in einer festgelegten Schrift, der als Zeichen
benutzt wird. Kein Bild, kein Symbol — nur der geschriebene Name.

**Wischregler** — Zwei Bilder liegen deckungsgleich übereinander, und ein senkrechter
Strich, den man mit dem Finger verschiebt, entscheidet, wo das obere aufhört und das
untere anfängt. Beide Bilder bleiben dabei in voller Grösse — der Unterschied zeigt sich
genau an der Kante.
*In diesem Projekt: als zweite Art, Modellbild und KI-Bild zu vergleichen.*

**Übergabe-Animation** — Eine Bewegung, die einen Gegenstand von einem Ort zu einem
anderen begleitet, statt ihn verschwinden und woanders auftauchen zu lassen. Ihr Zweck ist
nicht Schmuck: Sie beantwortet die Frage «wo ist meine Sache jetzt?», ohne dass jemand
danach suchen muss.
*In diesem Projekt: die Skizze, die vom iPad zur HomeStation reist.*

**Standnummer** — Eine Zahl in einer Datei, die bei jedem Schreiben um eins hochzählt.
Sie sagt nicht, *wann* zuletzt geschrieben wurde, sondern **wie oft** — und darum lässt
sich mit ihr feststellen, ob jemand anderes inzwischen geschrieben hat. Wer von Stand 7
kommt und auf der Platte Stand 9 vorfindet, weiss: Zwei Änderungen liegen dazwischen, die
er nicht kennt.
*In diesem Projekt: in jeder Mappe, damit ein iPad und die HomeStation nicht gegenseitig
ihre Arbeit überschreiben.*

**Kopplungszahl** — Eine kurze Zahl, die ein Gerät **einmal** eintippt, um dafür das
richtige, lange Kennwort zu bekommen. Sie ist absichtlich schwach und darum absichtlich
kurzlebig: Sie gilt Minuten, verträgt wenige Fehlversuche und ist nach dem ersten
erfolgreichen Verbinden verbraucht. Der Sinn ist ein Tausch — ein schwaches Geheimnis für
einen Augenblick gegen ein starkes für immer.
*In diesem Projekt: sechs Stellen, zehn Minuten, fünf Versuche, ein Gerät.* Seit dem
20.10.2026 zeigt der Mac seine Zahl fürs iPad nur noch zwei Minuten lang (das Koppelfenster).

**Koppelfenster** — Das kleine Fenster am Mac unter «iPad» → «iPad koppeln». Es zeigt die
Zahl, die Adresse und einen QR-Code und macht den Mac für ein iPad in der Nähe sichtbar —
**zwei Minuten lang**, dann schliesst es sich von selbst (Entscheid 99a). *Ein Angebot, das
nicht endet, wartet irgendwann auf den Falschen.*

**Koppelschein** — Ein kurzer Text mit genau drei Angaben: die Adresse des Heim-PC, die
einmalige Zahl und bis wann beides gilt. Der Mac gibt ihn dem iPad als QR-Code oder über die
Nähe-Verbindung; das iPad koppelt damit wie beim Abtippen. **Kein Kennwort darin**
(Entscheid 99) — wer den Schein abfotografiert, hat höchstens zwei Minuten und wenige Versuche.
*Seit Entscheid 118 (21.10.2026, Fassung 2):* vier Angaben — die Adresse **des Mac** (verschlüsselt, `https`), die Zahl
des Mac, die Frist und der Fingerabdruck seines Zertifikats; ein Schein der Fassung 1 kommt von einem Mac mit altem
Stand und wird mit Satz abgelehnt.

**Nähe-Verbindung (MultipeerConnectivity)** — Ein Baustein von Apple, mit dem sich zwei
Geräte in der Nähe direkt finden und verbinden — über WLAN oder Bluetooth, ohne Router, ohne
Internet und ohne Entwicklerkonto. *In diesem Projekt* zeigt sich der Mac im Koppelfenster;
das iPad fragt «Mit diesem Mac koppeln?», der Mac fragt «iPad möchte koppeln», und erst wenn
**beide** zustimmen, schickt der Mac über die verschlüsselte Verbindung den Koppelschein.
*Seit dem Demolauf vom 24.10.2026:* Die beiden Geräte verbinden sich sofort, verschlüsselt, sobald das iPad angenommen hat;
erst dann fragt der Mac den Menschen. Geschickt wird weiter erst nach beiden Zustimmungen.

**Einladung und Sitzung (MCSession)** — Die zwei Schritte einer Nähe-Verbindung. Die **Einladung** ist die Anfrage des einen
Geräts an das andere («darf ich mich verbinden?»); die **Sitzung** (bei Apple `MCSession`) ist die stehende Verbindung danach,
über die Daten gehen. Eine Sitzung meldet, in welchem Zustand sie ist: «verbindet», «verbunden» oder «nicht verbunden». *In
diesem Projekt* lehrte der Demolauf vom 24.10.2026, dass ein «nicht verbunden» während des Aufbaus **keine Absage** ist: Das iPad
hatte es so gelesen und aufgegeben, während am Mac die Frage noch stand. Seither unterscheidet die Regel `Naeheeinladung`:
vor der ersten stehenden Sitzung neu einladen, danach gilt es als Absage.

**Platzhaltertext (eines Eingabefeldes)** — Der graue Beispieltext in einem leeren Feld, der zeigt, was hineingehört; er
verschwindet beim ersten Tippen und ist kein Inhalt. *In diesem Projekt* stand im Adressfeld des Koppelbildschirms als
Platzhalter eine vollständige Adresse («https://192.168.1.24:8731»), die im Demolauf vom 24.10.2026 für eine gefundene gehalten
wurde. Seither sagt der Platzhalter nur, wo die Adresse steht — ein Beispiel, das wie ein echter Wert aussieht, wird für einen
gehalten.

**QR-Code** — Ein quadratisches Muster aus schwarzen und weissen Punkten, in dem ein kurzer
Text steckt; eine Kamera liest ihn in einem Augenblick. *In diesem Projekt* steht im
Koppelfenster des Mac der Koppelschein als QR-Code, und die iPad-App liest ihn mit ihrer
eigenen Kamera («Mit QR-Code koppeln») — nicht mit der Kamera-App, die ihn an den Browser gäbe.

**Gerätebuch (des Heim-PC)** — Ein kleiner Vermerk am Heim-PC, ob ein iPad gekoppelt ist,
wann es sich zuletzt gemeldet hat und ob es direkt oder über den Mac kam — nur Zeiten und
eine Art, **kein Kennwort, keine Zahl, kein Gerätename**. Er liegt als Datei neben der
Kennwortdatei und übersteht einen Neustart. *In diesem Projekt* fragt der Mac ihn ab
(`GET /api/geraete`), damit seine Zeile «iPad» sagt, was wirklich ist: Bis zum 20.10.2026
wusste der Mac nicht, dass das iPad längst direkt mit dem Heim-PC gekoppelt war.

**Probename (im Gerätebuch)** — Ein besonderer Gerätename, den nur Proben benutzen: `ipad-probe`. Wer am Heim-PC nachprüfen will, wie ein iPad behandelt wird, schickt ihn statt «ipad». Der Heim-PC behandelt die Anfrage dann genau wie eine des iPad, schreibt sie aber in eine eigene Zeile des Gerätebuchs. *Wozu:* Eine Probe soll den Stand des echten Tablets nicht überschreiben — sonst zeigt der Mac danach «iPad gerade gesehen», obwohl keins da war. *In diesem Projekt* in `src/aiimaging/geraetebuch.py` (`PROBEARTEN`), seit Befund 308 B1.

**Geräteart (Kopf einer Anfrage)** — Ein Zusatz an jeder Anfrage, der nur sagt, welche Art
Gerät fragt («ipad» oder «mac») — nie, wem es gehört oder wie es heisst. Ein «Kopf» ist dabei
eine Zeile, die vor dem eigentlichen Inhalt einer Anfrage mitgeht, wie die Angaben auf einem
Briefumschlag. *In diesem Projekt* führt der Heim-PC damit sein Gerätebuch; was über den Mac
weitergereicht wird, trägt zusätzlich den Vermerk «über den Mac».

**Netzaussetzer** — Ein kurzer Augenblick, in dem eine Leitung nichts durchlässt, obwohl
beide Enden in Ordnung sind — typisch im Mobilfunk, beim Wechsel zwischen Funkmasten oder
wenn Tailscale nach dem Aufwachen neu verbindet. *In diesem Projekt* gilt er nicht als
«getrennt»: Mac und iPad warten drei Fehlversuche und 30 Sekunden, bevor sie es sagen, und
zeigen davor nur ein weiches Band «Heim-PC kurz nicht erreichbar — verbinde neu …».
*Ein Ruckler ist kein Zustand.*

**Stetige Uhr** — Eine Uhr, die nur vorwärts läuft und nicht sagt, wie spät es ist,
sondern wie viel Zeit seit einem beliebigen Anfang vergangen ist. Sie lässt sich nicht
stellen — weder von Hand noch von der Zeitumstellung noch von einem Zeitserver. Fristen
werden darauf gerechnet und nicht auf der Wanduhr: *Eine Sperre, die eine falsch gehende
Uhr aufbricht, ist keine Sperre.*

**Schreibkollision** — Zwei Stellen wollen dieselbe Datei schreiben und kommen beide vom
selben Ausgangsstand. Ohne Vorkehrung gewinnt der Letzte, und die Arbeit des anderen ist
weg — **ohne Meldung**, weil aus Sicht des Programms beide Male alles geklappt hat. Das
ist die gefährliche Form des Datenverlusts: Sie sieht aus wie Erfolg.

**Bewegungsreduktion** — Eine Einstellung im Betriebssystem, mit der jemand sagt, dass
Bewegung auf dem Bildschirm ihm unangenehm ist oder schwindlig macht. Programme können sie
abfragen und ihre Animationen weglassen. Wer sie eingeschaltet hat, darf dadurch keine
Auskunft verlieren — *eine Aussage, die nur in der Bewegung steckt, ist für diese Leute
keine Aussage.*

**Knotenansicht / Knoteneditor** — Eine Darstellung des Ablaufs als Kästchen (Knoten), die
mit Linien verbunden sind: Jede Linie sagt, woher ein Kästchen seine Eingabe liest. Ein
**Knoteneditor** lässt diese Linien auch selbst ziehen und Knoten hinzufügen — so einer ist
der von KosmoOrbit. Die **Knotenansicht** von Visbox ist seit E26 (24.09.2026) **eine Kopie
dieses Knoteneditors** aus KosmoOrbit (`kosmovis/apps/visbox-knoten`); der Heim-PC liefert sie
unter `/knoten/` aus. Die Mac-App zeigt sie seit Entscheid 85 (14.10.2026) als Erstes. Der
frühere eigene Entwurf (feste Kette Modell → Tiefenbilder → KI-Bild → Prüfung, Blatt 11) ist
damit überholt.

**Führungsregler (`true_cfg_scale`)** — Nicht jedes Bildmodell lässt sich über denselben
Knopf führen. Beim Bearbeitungsmodell `qwen-image-edit-2511` heisst der Knopf, der wirklich
wirkt, `true_cfg_scale`; der verbreitete Name `guidance_scale` ist dort ohne Wirkung. Der
Führungsregler ist darum im Register **je Modell** mit Namen, Wert und Beleg eingetragen
(seit dem 23.09.2026, Befund aus `auf-157`).

**Leer-Negativprompt** — Ein einzelnes Leerzeichen als Gegentext. Es sagt dem Modell
inhaltlich nichts, schaltet aber bei manchen Modellen die Führung überhaupt erst ein: Ohne
irgendeinen Gegentext rechnet die Pipeline nur einen Durchgang und führt nicht. Beim
Bearbeitungsmodell lief darum jeder Lauf ohne eigenen Gegentext **ganz ohne Führung**, bis
das Leerzeichen der Modellkarte eingetragen wurde.

**Guidance-destilliert (`guidance_embeds`)** — Manche Gewichte haben den Führungswert als
Eingabe gelernt; nur bei ihnen wirkt `guidance_scale`. Ob das so ist, steht in der
Konfiguration der Gewichte (`guidance_embeds: true/false`). Bei `qwen-image-edit-2511`
steht dort `false` — belegt an der HomeStation.

**Zweite Tür** — Ein Weg, der an der vorgesehenen Prüfstelle vorbei zum selben Ziel führt.
Im Projekt war es das Einstellen eines Renderauftrags mit Freigabe-Token: Es stellte den
Auftrag allein nach der *Form* des Tokens auf «freigegeben» und ging am Tokenbuch vorbei.
Seit dem 23.09.2026 geht es durch dieselbe Prüfung wie jede Freigabe. *Ein Tor mit einer
zweiten Tür daneben prüft nur die, die das Tor benutzen.*

**Freigabe-Abdruck** — Statt des Freigabe-Tokens selbst steht im Auftrag ein Abdruck davon:
eine Zeichenfolge, die sich aus dem Token errechnen lässt, aus der sich das Token aber nicht
zurückgewinnen lässt. Damit kann der Abholer im Tokenbuch nachsehen, ob genau dieser
Auftrag freigegeben wurde — ohne dass jemand, der die Auftragsdatei liest, eine gültige
Freigabe in die Hand bekommt.

**Buchprüfung (`FREIGABE_MIT_BUCH`)** — Der Schalter, der entscheidet, ob eine Freigabe nur
mit einem Token gilt, das wir **ausgegeben** und das noch **niemand benutzt** hat. Heute
aus, weil noch niemand Token ausgibt (die Oberfläche von KosmoOrbit soll es tun,
`auf-20260909-99`). Eine Stelle für beide Wege — Einstellen und nachträgliche Freigabe.

**Schrift mitliefern / registrieren** — Eine Schrift, die nicht zum Betriebssystem gehört,
muss als Datei in der App liegen und beim Start dem System bekannt gemacht
(«registriert») werden; erst dann lässt sie sich beim Namen verwenden. Die iPad-App tut das
mit Apples Schriftbaukasten **CoreText** (Plattform, nicht mitgeliefert). Scheitert es,
zeigt sie die Systemschrift — nie unsichtbaren Text.

**PostScript-Name** — Der Name, unter dem das System eine Schrift nach dem Registrieren
kennt, z. B. `IBMPlexMono-Medium`. Er steht in der Schriftdatei selbst, in ihrer
**Namentabelle**; die App verlangt die Schrift genau unter diesem Namen. Ein Wächter liest
die Tabelle und prüft, dass jeder Name, den die App verlangt, in einer Datei vorkommt.

**Variable Schrift** — Eine einzige Schriftdatei, deren Strichstärke (Achse «wght») und
Breite (Achse «wdth») stufenlos einstellbar sind, statt je Stärke eine eigene Datei
(**Schriftschnitt**: normal, mittel, halbfett). IBM Plex Sans liegt in der Originalquelle
nur so vor; die App stellt die Stärke über die Achse ein.

**TrueType** — Ein verbreitetes Dateiformat für Schriften (Endung `.ttf`). Erkennbar an den
ersten vier Bytes der Datei; ein Wächter prüft sie, damit keine umbenannte andere Datei als
Schrift durchgeht.

**SHA-256 (Prüfsumme einer Datei)** — Ein Fingerabdruck, der sich bei jeder noch so
kleinen Änderung einer Datei völlig ändert. Im `NOTICE` steht er für jede mitgelieferte
Schriftdatei: So ist belegt, dass sie **unverändert** aus der Originalquelle stammt — eine
Auflage der Schriftlizenz OFL.

**Ressource im App-Paket** — Eine Datei, die keine Programmzeile ist (Bild, Schrift) und
trotzdem mit der App ausgeliefert wird. Im Paket muss sie ausdrücklich als solche
angegeben sein (`resources: [.process("Schriften")]`); sonst warnt der Übersetzer, und die
App findet sie nicht.

**Kreuzprobe** — Zwei Läufe unterscheiden sich, und man will wissen, **woran**: Man misst
das Bild des einen gegen die Vorgabe des anderen und umgekehrt. Bleiben die Zahlen am Bild
hängen, liegt der Unterschied im Bild; wandern sie mit der Vorgabe, lag er in der Messung.
Die HomeStation hat so am 23.09.2026 gezeigt, dass der Abstand zum Hintergrund wirklich
ändert, was das Modell zeichnet (`auf-154`).

**Messboden** — Eine gedachte Bodenfläche, die nur die Prüfung kennt. Viele Modelle haben keinen Boden,
das erzeugte Bild aber immer; ohne Boden im Modell verwechselte die Prüfung Boden und Gebäude und konnte gar nicht
messen. Der Messboden liegt auf Geländehöhe und wird aus der Kamera ausgerechnet; das Bildmodell sieht ihn nie.
Seit dem 13.10.2026 hilft er nur beim Trennen von Haus und Hintergrund; in die Punktzahl zählt allein das Haus.
*Im Projekt:* `messboden.mit_messboden`, `abholer._mit_messboden`; Entscheid 78, gegen echtes Blender geprüft.
*Seit auf-20261020-293* auch dann, wenn das Modell eine Geländeplatte hat: Vor einer kleinen Platte malt das
Bildmodell weiter Boden, wo das Modell nur Himmel hat — dort hilft der Messboden beim Trennen ebenso.

**Messschalter** — Eine Einstellung, die es nur gibt, damit sich **eine Ursache von einer
anderen trennen lässt** — nicht, damit jemand sie im Alltag stellt. Sie ist
ausgeschaltet, solange niemand sie setzt, und dann rechnet alles bitgenau wie vorher. Im
Projekt seit dem 23.09.2026 zwei: der **Abstand zum Hintergrund** und die **Umkehr der
Tiefe** (siehe *Polarität*). Die Oberfläche zeigt sie nur, wenn eine Mappe sie schon
trägt — *eine Mappe, die anders rechnet, als ihre Anzeige sagt, wäre schlimmer als ein Feld
zu viel.*

**Abstand zum Hintergrund (`ferne_abstand`)** — In unserer Tiefenkarte ist das Nächste
weiss und das Fernste schwarz, und der leere Himmel dahinter ist ebenfalls schwarz. Das
entfernteste Stück Gebäude sieht darum genauso aus wie *nichts*. Steht ein Gebäude auf
einer Bodenplatte, ist das Fernste der Boden und fällt nicht auf; steht ein Quader frei,
**verschwindet seine Rückkante im Hintergrund.** Der Abstand hebt alles Gebaute um einen
kleinen Grauwert an (z. B. 0,15), der Hintergrund bleibt schwarz — die Kante trennt sich ab.
Ein Messschalter; ob er zur Vorgabe wird, entscheidet die Messung in `auf-154`.

**Vorgabe für Varianten (Entscheid 126)** — Was der Heim-PC einstellt, wenn eine Bestellung zu einer Einstellung nichts
sagt. Seit dem 21.10.2026 sind das drei frühere *Messschalter*: das Material vorne in der Bildbeschreibung, die Umgebung
ausserhalb des Hauses festgehalten («Umriss halten im Lauf») und der Himmel hinter dem Haus. Eine ausdrückliche Angabe
gewinnt immer, auch «aus». Wo eine Einstellung fachlich nicht passt, entfällt sie, und das Ergebnis sagt, warum
(`angewandt.messschalter`, mit «Herkunft»: bestellt, Vorgabe, entfallen oder aus der Grundlage). Seit dem 22.10.2026
(Generalprobe 327) gilt sie auch für die schnelle Vorschau ganz — vorher bekam die Vorschau nur die Hälfte (*Halbe M2*).
*Nachgeführt 22.10.2026:* Seit **Entscheid 138** gehört ein vierter Wert dazu: der *Bildeingang mit Stärke* 0,5 — die
Variante geht vom gerenderten Grundbild aus. Er gilt nicht in der Vorschau, nicht an Modellen ohne passenden Weg und nie an
Modellen mit offener Lizenz.

**Zurückgezogene Vorgabe (beim Bildeingang)** — Eine Vorgabe, die der Heim-PC kurz vor dem Rechnen wieder herausnimmt,
weil sie in diesem Moment nicht gehen würde: Der Lauf mit Bildeingang braucht etwas mehr Speicher auf der Grafikkarte;
liegt dort ein fremdes Programm oder ist zu wenig frei, rechnet die Variante wie früher ohne Grundbild als Start, statt
gar nicht. Ein ausdrücklich bestellter Bildeingang wird dagegen abgewiesen, mit Satz. *Im Projekt:*
`abholer.bildeingang_vorgabe_zurueckziehen`, im Ergebnis unter `angewandt.messschalter.bildeingang` mit Herkunft
«vorgabe_entfaellt» und dem Grund (Entscheid 138).

**Deckungsschwelle** — Die Zahl, ab der ein KI-Bild als «deckungsgleich» mit seinem Grundbild gilt. Gemessen wird, wie
viele Kanten (Linien, an denen sich die Helligkeit sprunghaft ändert) beider Bilder an derselben Stelle liegen, als
Anteil von 0 bis 1. *Im Projekt:* `varianten.DECKUNG_KANTEN_IOU_SCHWELLE`, seit 22.10.2026 0,25 (vorher 0,10), gesetzt aus
den Messungen 337 und 339. Die Zahl hängt auch an der Oberfläche des Grundbilds: Holzlatten haben viele Kanten, glatter
Beton halb so viele. Seit 24.10.2026 wird nur im Haus gemessen (siehe *Deckung im Haus*); die Zahl 0,25 blieb,
gegengeprüft an den Haus-Werten von 337 bis 347 (Form nicht gehalten bis 0,21, gehalten ab 0,27). Die Knotenansicht urteilt mit derselben Zahl (`DECKUNG_SCHWELLE` in
`kosmovis/…/vis/grossansicht.ts`, seit 22.10.2026 abends); steht im Ergebnis schon der Satz «FORM WEICHT VOM GRUNDBILD
AB», gilt dieser.

**Fenster gehalten (Prüfung am KI-Bild)** — Zählt, wie viel vom Glas des Grundbilds im KI-Bild noch Glas ist. Woher man
weiss, wo Glas ist: aus dem Material-ID-Pass, einem Hilfsbild, in dem jedes Material eine eigene Kennfarbe trägt; Glas ist,
wessen Materialname «Glas», «glass», «Verglasung» oder «glazing» enthält. Je solchem Bildpunkt fragt die Prüfung: Sieht das
KI-Bild dort eher aus wie das Grundbild an derselben Stelle oder eher wie die übliche Fassadenfarbe des KI-Bilds (der
*Median*, also der mittlere Wert)? Malt die KI Holz über ein Fenster, gewinnt die Fassade. Unter der Hälfte steht im
Ergebnis der Satz «FENSTER IM KI-BILD NICHT GEHALTEN»; die Hälfte ist gesetzt, nicht gemessen. Ist zu wenig Glas im Bild
(unter 0,2 %) oder sieht das Glas schon im Grundbild aus wie die Fassade, schweigt sie. Sie ist ein Hinweis, kein Tor: Das
Urteil «bestanden» bleibt, wie es ist. *Anlass:* Am 23.10.2026 malte die KI im Testprojekt «haus-am-hang» ein schmales
Fensterband zu, und keine Prüfung sah es — die Tiefe kennt kein Glas, und die Kanten über das ganze Bild verlieren an
einem schmalen Band zu wenig. *Im Projekt:* `varianten.fenster_gehalten`, `abholer.fenster_der_kamera`, Feld `fenster`
am Kamera-Urteil; gemessen mit auf-20261023-346. **Seit 24.10.2026 (Fassung v2)** prüft zusätzlich der *Farbton* (siehe
dort): Ist das Glas im Grundbild deutlich bläulicher als die Fassade, muss eine Glasstelle auch im KI-Bild mindestens die Hälfte
dieses Vorsprungs behalten; und die Fassadenfarbe wird nur aus dem Haus gerechnet, ohne Bäume und Gelände. *Anlass:* In 346
hatte v1 eine Vorschau mit zugemaltem Band «gehalten» genannt, weil helle graue Latten dem hellblauen Glas ähnlicher waren als
der dunklen Fassade samt Bäumen.

**Farbton (Blau minus Rot)** — Wie warm oder kühl eine Farbe ist, hier ganz einfach gemessen: der Blauanteil eines Bildpunkts
minus sein Rotanteil (jeweils 0 bis 255). Glas mit gespiegeltem Himmel ist bläulich (Wert deutlich über null), Holz, Beton und
Latten sind neutral oder warm (um null oder darunter). Anders als die Helligkeit trennt der Farbton helles Glas von hellen
Latten. Verglichen wird nie der Wert allein, sondern der *Vorsprung* gegenüber der Fassade desselben Bilds — so verliert eine
wärmere Stimmung, die alles röter macht, das Glas nicht. *Im Projekt:* `varianten.fenster_gehalten` (Fassung v2),
`FENSTER_FARBTON_TRENNUNG_MIN` (12), `FENSTER_FARBTON_ANTEIL` (die Hälfte).

**Vegetationswörter (Umfeld am Namen)** — Wörter im Namen eines Bauteils oder Materials, an denen das Programm Pflanzen
erkennt: Baum, Tree, Laub, Stamm, Hecke, Strauch, Busch, Vegetation, Pflanze und einige mehr. Ein so benanntes Teil gilt als
*Umfeld* — es gehört nicht zum Haus und nicht zum Boden. Verglichen wird auf Wortgrenzen: «Baum_Laub» trifft, «Laubengang» und
«Stammhaus» nicht. *Anlass:* In 346 lagen Bäume namens «Baum_Laub» ganz in der Hausmaske, und die Vorschau malte sie wie die
Fassade. *Im Projekt:* `maske.UMFELD_WOERTER`, `maske.ist_umfeld`.

**Deckung im Haus (Messbereich)** — Die Deckung (siehe *Kanten-IoU*, *Deckungsschwelle*) zählt seit dem 24.10.2026 nur die
Bildpunkte, die zum Haus gehören: die Hausmaske ohne Bäume, Hecken und Boden. Vorher zählte das ganze Bild. *Anlass:* In
Messung 347 kamen die Bäume unverändert aus dem gerenderten Grundbild; ihre vielen Kanten passten genau, und die Zahl stieg
über die Schwelle, obwohl die KI das Haus zugemalt hatte. Wer ein Haus prüft, muss am Haus messen. Fehlt die Maske oder ist
das Haus kleiner als 1 % des Bilds, misst sie wie früher über das ganze Bild und sagt es. *Im Projekt:*
`varianten.hausbereich`, `varianten.deckung_aus_bildern(maske=…)`, im Urteil `bereich` («haus» oder «ganz»),
`kanten_iou_ganz` daneben.

**Ladezeit des Bildmodells** — Bevor die KI ein Bild rechnen kann, müssen ihre Gewichte (die gelernten Zahlen, viele
Gigabyte) von der Festplatte in die Grafikkarte. Liegen sie schon im Arbeitsspeicher (siehe *Seitencache*), geht das schnell;
nach langer Ruhe kommen sie von der Platte und es dauert spürbar länger. Die gemessene «KI-Zeit» enthält beides, Laden und
Rechnen. *Im Projekt:* seit 24.10.2026 meldet das Bildmodell `laden_s` (null, wenn das Modell schon geladen war), und das
Kameraurteil trägt `ki_zeit` mit `dauer_s`, `laden_s` und `rechnen_s` — Anlass waren 20 s mehr KI-Zeit in Messung 347, die
sich ohne diese Trennung nicht zuordnen liessen.

**Glassatz (Messschalter)** — Ein kurzer Satz, den die Bildbeschreibung auf Bestellung vorne bekommt, direkt hinter dem
Stoff: «clear transparent glazing» (klares, durchsichtiges Glas). Er sagt der KI, dass Glas zum Haus gehört, nicht nur Holz.
Bewusst **ohne** das Wort «windows» (Fenster): Ein Bauteilwort bestellt eine Form, und wo das Modell andere Fenster hat,
malt die KI die bestellten dazu. Die Form kommt aus dem Grundbild. Vorgabe aus, weil ungemessen. *Im Projekt:*
`vis.glas_satz`, `kosmo_szene.GLAS_SATZ`.

**Nennungen des Stoffs vorne** — Wie oft der Hauptstoff (etwa «spruce timber battens», Fichtenlattung) vorne in der
Bildbeschreibung steht. Vorgabe dreimal: «monolithic … building, made entirely of …, uniform … on all exterior surfaces».
Die zweite und dritte Wendung sagen «ganz aus Holz» — und widersprechen damit einem Fensterband. Mit dem Messschalter steht
er nur ein- oder zweimal da. *Im Projekt:* `vis.material_vorne_nennungen` (1 bis 3), `kosmo_szene.material_vorne_satz`.

**Bildraster des KI-Schritts (Umrechnen der Bildgrösse)** — Das Bildmodell rechnet nur in Seitenlängen, die durch 16
teilbar sind. Bestellt die Knotenansicht 1600 × 1000, rechnet die KI 1600 × 992, und ihr Bild wird danach auf 1000 Zeilen
gestreckt; bei 960 × 600 rechnet sie 1024 × 640 und wird verkleinert. Jedes solche Umrechnen mischt benachbarte Bildpunkte
und macht ein Bild ein wenig weicher. *Im Projekt:* `backbone.ki_raster_groesse`, `abholer.ki_steuerbilder`,
`bildschreiben.skaliere_png`; ob es die Unschärfe am Mac erklärt, misst auf-20261023-346 (Schritt S8).

**Halbe M2 (Vorschau bis Fassung 0.3.31)** — Die Vorschau bekam von der Vorgabe *M2* nur den einen Teil, den Stoff vorne
in der Bildbeschreibung, nicht aber den anderen, das Festhalten der Umgebung ausserhalb des Hauses. Ausgerechnet diese
Hälfte allein lässt die KI noch mehr Gebäude neben das Haus malen (gemessen in auf-20261021-303: «M1» 3,08-fache
Hausfläche gegen 2,19 ohne beide). In der Generalprobe zeigte die Vorschau darum 161 bzw. 179 % Baumasse neben dem Haus.
*Im Projekt:* behoben in `kosmo_szene.varianten_vorgabe_entfaellt` (die Vorschau rechnet immer mit z-image-turbo, an dem
das Festhalten gemessen ist), bewacht von `tests/test_generalprobe_327.py`.

**Hintergrund je Kamera (`hintergrund_je_kamera`)** — Was im Blender-Bild hinter dem Haus stand: das *Himmelsbild* der
Stimmung (`himmelsbild`, die Kamera sieht den Himmel) oder ein ruhiger Farbverlauf (`verlauf`). Die Angabe stammt aus dem
Bericht, den Blender je Kamera schreibt, und steht seit dem 22.10.2026 auch im Ergebnis unter
`angewandt.environment.hintergrund_je_kamera` — vorher nur im Bericht, wo die Generalprobe sie nicht suchte. Daneben im
Ergebnis neu: `angewandt.prompt_zusaetze`, die Sätze, die die Knoten (Stimmung, Material, Stoff vorne) an die
Bildbeschreibung gehängt haben.

**Kamerakürzel und deutsches Gleichwort** — Die Standpunkte rund um ein Haus heissen im Projekt mit kurzen
Buchstaben nach den Himmelsrichtungen, englisch geschrieben: `n`, `e`, `s`, `w` und dazwischen `nNE`, `sSE` … («von
Norden, nach Nordost gedreht»). Ein *Gleichwort* ist ein zweiter Name für dasselbe. Seit dem 21.10.2026 versteht der
Heim-PC auch die deutsche Schreibweise mit «O» für Ost (`nNO` für `nNE`, `o` für `e`) und sagt im Ergebnis, dass er
umgedeutet hat; ein Kürzel, das er gar nicht kennt, beendet den Auftrag sofort mit einem Satz, statt ihn liegen zu
lassen (Befund auf-20261021-314, B2).

**OptiX** — Ein Rechenweg der Grafikkarten von NVIDIA, mit dem das Renderprogramm Blender (Cycles) Bilder auf der
Grafikkarte statt auf dem Hauptprozessor (CPU) rechnen kann. Im Projekt zweimal gemessen (06.09. und 21.10.2026): Auf dem
Weg, den der Heim-PC wirklich geht, ist OptiX nicht schneller, belegt aber fast 4 GB Grafikspeicher, den das Bildmodell
braucht. Darum rechnet Blender weiter auf der CPU.

**Paket von Schritten (`vis_paket`, «$neu:N»)** — Ein Werkzeug des KI-Assistenten, das mehrere Bedienschritte in der
Knotenansicht zu **einem** Vorschlag bündelt (eine Karte, ein Rückgängig). Weil ein neuer Knoten seine Kennung erst
bekommt, wenn er angelegt ist, verweist ein späterer Schritt mit «$neu:0» auf das, was Schritt 0 neu anlegt. Seit dem
21.10.2026 prüft der Heim-PC, dass ein solcher Verweis auf einen früheren Schritt zeigt, der wirklich das Passende anlegt
(einen Graph, einen Knoten, eine Kante) — sonst geht das Paket nicht hinaus. Ebenfalls seit dem 21.10.2026 nennen auch
die Beschreibungen der Einzelwerkzeuge «Knoten setzen» und «Verbinden» diesen Weg, weil das Sprachmodell ihn sonst
nicht fand und die Kennung des neuen Knotens riet.

**Zwei-Finger-Geste (Wischen und Pinch)** — Auf dem Trackpad eines Mac zwei Finger
**gemeinsam verschieben** heisst *Wischen*: die Fläche wandert mit den Fingern mit. Zwei Finger
**auseinander- oder zusammenziehen** heisst *Pinch*: die Ansicht wird grösser oder kleiner, und
zwar dort, wo der Zeiger steht. Ein *Mausrad* dagegen dreht in festen Rasten; eine Raste
zoomt. Der Browser meldet alle drei als «Rad-Ereignis», nur verschieden verpackt — Chrome einen
Pinch als Rad mit gedrückter ctrl-Taste, Safari und die Mac-App (WebKit) als eigene
«Gesten-Ereignisse». Im Projekt seit Runde 26 (14.10.2026) in der Knotenansicht von Visbox:
`kosmovis/apps/kosmo-orbit/src/shell/trackpad-geste.ts`, wörtlich aus KosmoOrbit (E152).
Vorher zoomte dort jedes Wischen, statt die Fläche zu schieben.

**Lade-Fähigkeit des Wirts** — Eine Fähigkeit, die das Programm, in dem ein übernommenes Werkzeug
läuft (der **Wirt**), dem Werkzeug von aussen anbietet. Das Werkzeug fragt nur «gibt es eine?» und zeigt
den Knopf dann — oder eben nicht. So läuft **derselbe** Code in zwei Programmen, die Verschiedenes
können. *Im Projekt:* der Modell-Knoten des Vis-Werkzeugs (Entscheid 90): Visbox bietet «Datei laden …»
an, KosmoOrbit nicht (dort kommt das Gebäude aus dem Entwurf), und dort bleibt der Knoten, wie er war
(`modules/vis/modell-laden.ts`).

**Skizzen-Quelle des Wirts** — Eine zweite Fähigkeit nach dem Muster der **Lade-Fähigkeit des
Wirts**: Das Programm, in dem das Vis-Werkzeug läuft, sagt dem Werkzeug, **welche Skizzen es gibt
und wo ihr Bild liegt** — eine Liste (die neueste zuerst) und je Skizze eine Adresse. Das Werkzeug
selbst kennt keine Mappe und keinen Server. *Im Projekt:* der Knoten «Skizze vom iPad» (Entscheide
95/95a): Visbox meldet die Skizzen der offenen Mappe an (`registriereSkizzenQuelle` in
`kosmovis/apps/visbox-knoten/src/main.tsx`, Liste aus `/knoten/mappe`, Bild aus `/knoten/skizze`);
KosmoOrbit meldet nichts an, und der Knoten sagt dort «Skizzen vom iPad gibt es in Visbox.»
(`modules/vis/skizze-quelle.ts`).

**Zulieferer-Knoten** — Ein Knoten ohne Eingang, der etwas **von ausserhalb der Knotenansicht**
hereinholt — eine Skizze vom iPad, den Blick der 3D-Ansicht, ein Bild der Mappe — und es an einem
Ausgang anbietet. Er rechnet nichts; er bringt nur etwas an die Arbeitsfläche, damit es dort
verbunden werden kann. *Im Projekt:* seit Entscheid 94 sind die Knoten die Arbeitsfläche zum
Rendern; was vorher auf anderen Seiten stand, kommt als Zulieferer-Knoten herein («Skizze vom
iPad», «Kamera aus 3D-Ansicht»).

**Daumenbild (Vorschaubild)** — Eine kleine Fassung eines Bildes, gerade gross genug, um es
wiederzuerkennen. Es ersetzt das Bild nicht, es zeigt nur, **welches** gemeint ist. *Im Projekt:*
der Knoten «Skizze vom iPad» zeigt unter seiner Auswahl die geltende Skizze 80 Bildpunkte hoch.

**data:-Adresse (Data-URL)** — Eine Adresse, in der **das Bild selbst steckt** statt eines
Verweises auf einen Ort: Sie beginnt mit `data:image/png;base64,` und dahinter folgen die
Bilddaten als Buchstaben. Sie braucht keinen Server mehr, ist aber gross. *Im Projekt:* der Knoten
«Skizze vom iPad» holt das Bild der geltenden Skizze einmal vom Visbox-Server und hält es so fest,
damit Bildvergleich und «Aufs Blatt» es ohne weiteren Abruf haben.

**Die Skizze führt das Bild (Eingang «Skizze»)** — Ein Bild entsteht nicht aus dem Modell allein,
sondern **aus einer Zeichnung**: Die Skizze vom iPad, auf das Bild gelegt, über das sie gezeichnet
wurde, geht als Eingangsbild an das Bildmodell, zusammen mit einer **Anweisung**, was sich ändern soll.
*Im Projekt:* auf der Seite seit September «aus Skizze rechnen»; in der Knotenansicht seit Entscheid 96
(15.10.2026) über den Eingang «Skizze» am Render-Knoten — gerechnet wird beide Male auf demselben Weg
(`arbeitsgang.rechne_skizze`). Der Eingang steht nur in Visbox; in KosmoOrbit gibt es keine Mappe mit
Skizzen.

**Anweisung (an eine Skizze)** — Der Satz, der sagt, **was sich am Bild ändern soll** («ein Vordach aus
Holz»), im Unterschied zum Prompt, der beschreibt, was entstehen soll. *Im Projekt:* ~~in der
Knotenansicht wird der Prompt des Render-Knotens zur Anweisung~~ — **seit Entscheid 96a (15.10.2026) gilt
in der Knotenansicht die Bemerkung, die beim Zeichnen an der Skizze stand**; die Stimmung (der Prompt)
tritt zurück und wird nicht als Anweisung gesendet. Hat die Skizze keine Bemerkung, sagt der Knoten das
vor dem Klick («am iPad eine schreiben») und sendet nichts.
*Nachgeführt 24.10.2026 (Befund F4):* Seit Entscheid 96c gilt ohne Bemerkung der Prompt des Render-Knotens als Anweisung — auch am Heim-PC. Steht an der Skizze nur ihr *gewünschter Name*, zählt das nicht als Bemerkung.

**Gewünschter Name (einer Skizze)** — Der Name, den das iPad einer Zeichnung beim Ablegen geben will (aus der Kopfzeile, etwa «Variante A»). Als Dateiname taugt er nicht, darum hängt ihn die Visbox an die Bemerkung: «gewünschter Name: Variante A». *Wozu:* Er soll nicht verloren gehen — er ist der Titel der Skizze, solange sie keinen eigenen hat. Er ist aber **keine Anweisung**: Im Demolauf vom 24.10.2026 hielt die Knotenansicht ihn dafür, und «Bild aus Skizze» brach ab. *Im Projekt:* `projekt.bemerkung_ohne_name`, `projekt.gewuenschter_name`, in der Knotenansicht `bemerkungOhneName`.

**Bestelltes Bildwerkzeug** — Das Bildmodell, mit dem ein Auftrag tatsächlich abging — nicht unbedingt das, das am Wähler des Render-Knotens steht: Claude kann über eine Karte ein anderes bestellen. *Wozu:* Die Anzeige am Knoten soll sagen, was gerechnet wird. *Im Projekt:* `NodeLauf.backbone`; am Wähler «Bildwerkzeug · bestellt: Qwen-Image 2.1», seit 24.10.2026.


**Standpunkt eines Bildes** — Von wo ein Bild der Mappe gerechnet wurde: Richtung, Augenpunkt und
Zielpunkt, Brennweite, Raum. *Im Projekt:* seit dem 15.10.2026 steht er an jedem gerechneten Bild
(`herkunft.standpunkt`). Wird eine Skizze auf ein Bild gezeichnet, entsteht das neue Bild **von genau
diesem Standpunkt** (Entscheid 96b) — nur dann liegt die Tiefenkarte unter den Strichen. Ist er nicht
bekannt (ein älteres Bild) oder gibt es kein Bild darunter, gilt der Standpunkt der Mappe, und das steht
am Ergebnis.

**Steuerzeichen** — Unsichtbare Zeichen im Text, die keine Buchstaben sind, sondern einem Gerät etwas
befehlen: Zeilenumbruch, Tabulator, «Ende der Zeichenkette» (Nullzeichen). *Im Projekt:* ein Skizzenname
mit einem Steuerzeichen wird abgewiesen (Auflage A1) — er könnte in einem Protokoll oder Dateinamen etwas
anderes bedeuten, als er zeigt.

**Laufwerksbuchstabe** — Der Buchstabe mit Doppelpunkt, mit dem Windows ein Laufwerk benennt (`C:`). Ein
Name, der so beginnt, zeigt auf eine ganze Platte statt in einen Ordner. *Im Projekt:* ein Skizzenname mit
Laufwerk wird abgewiesen (Auflage A1, siehe Pfad-Trickserei).

**Bearbeitungs-Modell** — Ein Bildmodell, das ein **vorhandenes Bild verändert**, statt eines aus der
Tiefenkarte neu zu rechnen. Nur ein solches kann eine Skizze überhaupt «sehen». *Im Projekt:* gemessen
nimmt weder das Vorgabemodell (Z-Image Turbo) noch Qwen-Image-Edit das Eingangsbild an — dort «kommt die
Skizze nicht an», und das Ergebnis sagt es zuvorderst («SKIZZE NICHT ANGEKOMMEN»). Qwen-Image 2.1 kann
laut Modellkarte bearbeiten; ob die Skizze dort ankommt, ist ungemessen (Auftrag 286), und seine Lizenz
ist offen (E128) — darum nie Vorgabe.

**Eingang nur für eine Knotenart** — Ein Anschluss am Knoten, der nicht jede passende Sorte annimmt,
sondern **nur von bestimmten Knoten**. Sonst gilt allein die Anschlusssorte. *Im Projekt:* der Eingang
«Skizze» am Render-Knoten hat die Sorte «Bild», nimmt aber nur «Skizze vom iPad» — eine Aufnahme oder
ein anderes Render-Bild weist er mit Satz ab, weil die Bestellung nur eine Skizze der Mappe nennen kann
(`VisPort.nurVon`).

**Verborgene Datei (Punktdatei)** — Eine Datei, deren Name mit einem Punkt beginnt. Viele Programme
zeigen sie nicht an, und unser Server liefert sie nie aus. *Im Projekt:* `.mappe.json` neben einem
Auftrag der Knotenansicht nennt den Pfad der Mappe, in der die Skizze liegt — der Abholer braucht ihn,
der Browser darf ihn nicht sehen, weil ein Plattenpfad den Rechnernamen verrät (Regel 3).

**Feld, das ein anderes ausschliesst (Kreuzregel)** — Eine Regel im Vertrag, die nicht ein Feld allein
prüft, sondern **zwei zusammen**: «wenn dieses, dann nicht jenes». *Im Projekt:* mit `skizze` weist der
Vertrag eine Kameraliste, eine Innenansicht und «nur Cycles» ab — eine Skizze ist EIN Bild vom
Standpunkt der Mappe und braucht das Bildmodell. In KosmoOrbit heisst das Werkzeug dafür `superRefine`.

**Additives Vertragsfeld** — Ein neues Feld, das **wegbleiben darf**: Wer es nicht sendet, bestellt
genau wie vorher, und keine bestehende Bestellung wird ungültig. Darum braucht es keine neue Fassung des
Vertrags. *Im Projekt:* `skizze` (Entscheid 96) wie vorher `context` (Splat) und `gelaende`; eine ältere
Bildseite, die das Feld nicht kennt, weist es ab, statt still ohne die Skizze zu rechnen.

**Kurzhilfe (Tooltip)** — Ein kleines Feld, das erscheint, wenn der Zeiger auf einem Element ruht, und
den ganzen Satz zeigt, wo am Ort nur Platz für den Anfang ist. *Im Projekt:* die Zeile «Skizze» am
Render-Knoten zeigt drei Zeilen; den vollen Satz mit Beleg trägt die Kurzhilfe (`KTooltip`).

**Varianten-Knoten («Varianten mit einem Klick»)** — Ein Knoten hinter dem Render-Knoten, der dessen Einstellung in
allen Kombinationen dreier Achsen bestellt: Standpunkte (woher man blickt), Stimmungen (Morgen, Abend, Weissmodell) und
Entwürfe (welches Modell). Ein Zähler sagt vorher, wie viele Bilder es werden, z. B. «6 Bilder (3 × 2 × 1)»; ab zwölf
Bildern warnt er mit der ungefähren Dauer, sperrt aber nichts. *Im Projekt:* Owner-Entscheide 92/92a/92b, gebaut in
`kosmovis/apps/kosmo-orbit/src/modules/vis/VariantenKnoten.tsx`; die Rechnung in `derive/varianten.ts`. Siehe auch
**Variantenachse (Wedge)**.

**Raster (im Bildvergleich)** — Die Bilder einer Variantenbestellung als Tabelle: jede Zeile ein Standpunkt, jede
Spalte eine Stimmung, je Entwurf ein Reiter. Jede Zelle zeigt ihr Bild und einen farbigen Punkt für das Prüfurteil; ein
Klick vergrössert. Eine leere Zelle sagt, warum («wartet», «rechnet», «fehlgeschlagen»). *Im Projekt:*
`VariantenRaster.tsx`, im Knoten «Bildvergleich», sobald ein Varianten-Knoten daran hängt.

**Ebenenkombination (als Entwurf)** — In KosmoOrbit liegt jedes Bauteil auf einer Ebene; eine Kombination ist eine
gespeicherte Auswahl, welche Ebenen sichtbar sind. Legt man zwei Volumenvarianten auf je eine Ebene, zeigt je eine
Kombination nur die eine. Der Varianten-Knoten rechnet so jede Kombination als eigenen Entwurf. *Im Projekt:* In Visbox
gibt es keine Ebenen; dort ist der Entwurf immer «Aktuelles Modell».

**Eine Freigabe für alle** — Jeder Auftrag an den Heim-PC wartet, bis ein Mensch ihn freigibt; technisch hat jeder seinen
eigenen Freigabeschlüssel. Der Knopf «Alle freigeben» gibt alle wartenden Aufträge einer Variantenbestellung mit einem
Klick frei. Kosmo und Claude können bestellen, aber nicht freigeben.

**Befehlsjournal** — Die Liste der Befehle, die in der laufenden Sitzung ausgeführt wurden, mit Urheber (Architekt,
Kosmo, Claude). Nicht zu verwechseln mit dem **Journal** des Heimrechners. *Im Projekt:* Varianten werden gesendet,
sobald der Befehl «Varianten» darin steht — ein Rückgängig oder ein Abgleich von einem anderen Gerät steht nicht darin
und löst darum keinen zweiten Auftrag aus.

**Luft der Werkzeugliste (B19)** — Ein Sprachmodell bekommt mit jeder Frage die Beschreibung aller Werkzeuge, die es
benutzen darf; das kostet Platz im Kontextfenster (gemessen in Token). Die Luft ist, was danach für Gespräch und Antwort
übrig bleibt. KosmoOrbit hält sie über einer Grenze (7000 Token); jeder neue Befehl verbraucht davon. *Im Projekt:* der
Befehl `vis_varianten` kostet 146 Token und wird darum erst eingespielt, wenn ein anderes Paket Platz macht.

**Lauf ohne Karte** — Ein Befehl, der nichts am Projekt ändert, braucht keine Vorschlagskarte zum Freigeben: Kosmo
bekommt die Antwort direkt. *Im Projekt:* `vis_varianten` mit `stand: true` liest den Stand der Bilder so.

**Berechneter Schlüssel** — In einem Verzeichnis im Programmcode steht vor jedem Eintrag sein Name
(«render: …»). Ein berechneter Schlüssel nennt stattdessen eine Konstante, deren Wert der Name ist
(«[KAMERA_AUS_3D_TYP]: …»). Für das Programm ist das dasselbe; ein Werkzeug, das den Code nur als Text
liest, sieht den Eintrag aber nicht, wenn es nur die erste Schreibweise kennt. *Im Projekt:* die
Probe der Kosmo-Tafel (`tests/test_knoten_tafel.py`) übersah so den Knoten «Kamera aus 3D-Ansicht»
und zählte zwölf statt dreizehn Knoten, bis «Skizze vom iPad» dazukam (Protokoll 74 §123).

**Stellvertreter (Stand-in)** — Eine kleine, selbst geschriebene Datei, die **an der Stelle
eines fehlenden Originals steht** und dieselben Namen anbietet, damit der Code, der sie
aufruft, unverändert bleiben kann. Sie tut nur, was im neuen Zusammenhang Sinn ergibt, und
sagt es, wo sie etwas nicht kann. Im Projekt seit dem 24.09.2026 in `kosmovis/`: Das
Vis-Werkzeug von KosmoOrbit ruft zum Beispiel den Assistenten «Kosmo» auf, den es in Visbox
nicht gibt; der Stellvertreter `KosmoOrb.tsx` zeichnet darum nichts. Jeder trägt das Wort
STELLVERTRETER im Kopf und steht in `kosmovis/HERKUNFT.json` — *damit die Rückkehr im
Februar weiss, welche Dateien sie durch das Original ersetzt.*

**Wörtliche Kopie mit Herkunft** — Eine Datei, die Byte für Byte aus einem anderen Projekt
übernommen ist, und neben der festgehalten wird, **woher** (Projekt, Stand) und **welchen
Abdruck** (SHA-256) sie hatte. So lässt sich jederzeit prüfen, ob sie noch das Original ist
oder ob jemand sie geändert hat. Im Projekt: `tools/kosmovis_uebernahme.py --pruefen`.

**npm und Arbeitsbereich (Workspace)** — *npm* ist das Werkzeug, das in der
JavaScript-Welt fremde Pakete holt und Befehle wie «prüfen» oder «bauen» ausführt, so wie
`pip` bei Python. Ein *Arbeitsbereich* fasst mehrere eigene Pakete in einem Ordner
zusammen, die sich gegenseitig benutzen, ohne veröffentlicht zu sein. Im Projekt:
`kosmovis/` mit dem Kern, den Oberflächenbausteinen, den Verträgen und der App.

**Sperrdatei (Lockfile)** — Eine von npm erzeugte Liste, die für **jedes** geholte Paket
die genaue Fassung festhält. Wer später installiert, bekommt dieselben Pakete statt der
jeweils neuesten. Im Projekt: `kosmovis/package-lock.json`.

**Bau (Build)** — Das Übersetzen und Zusammenpacken des Quelltexts in die wenigen Dateien,
die ein Browser tatsächlich lädt. Der Bau ist erzeugt, nicht geschrieben, und gehört darum
nicht ins Repo. Im Projekt: `npm run build` in `kosmovis/` legt ihn nach
`kosmovis/apps/visbox-knoten/dist/`.

**Vite** — Das Bauwerkzeug der Knotenansicht: Es übersetzt TypeScript und React für den
Browser und liefert während der Arbeit eine Vorschau aus. MIT-lizenziert; wird nicht
ausgeliefert, nur benutzt.

**Vitest** — Das Prüfwerkzeug der Knotenansicht, das Gegenstück zu `pytest` auf der
Python-Seite. Die 722 übernommenen Proben des Originals laufen damit.

**zod** — Eine Bibliothek, mit der ein Programm beschreibt, **wie Daten aussehen müssen**
(welche Felder, welche Art Wert), und eingehende Daten dagegen prüft. KosmoOrbit prüft damit
jeden Befehl und jede Antwort des Rechenwegs. MIT-lizenziert.

**woff2** — Das Dateiformat für Schriften im Browser: dieselbe Schrift wie eine
`.ttf`-Datei, aber gepackt, damit sie schnell lädt. Die drei Schriften der Knotenansicht
(Lato, PT Sans Narrow, IBM Plex Mono) liegen so vor.

**Vorsilbe eines Wegs** — Der Anfang einer Adresse, an dem ein Server erkennt, wem eine
Anfrage gehört: alles, was mit `/bruecke/` beginnt, geht an die Knotenansicht-Schnittstelle.
Wichtig ist die **Grenze**: `/brueckenbau` beginnt zwar mit denselben Buchstaben, gehört
aber nicht dazu — darum wird auf «genau `/bruecke` oder `/bruecke/…`» geprüft. Im Projekt:
`oberflaeche/server.py`, `_ist_knotenweg`.

**Formular-Upload (multipart/form-data)** — Die Art, wie ein Browser mehrere Teile in einer
Anfrage schickt, etwa einen Text (die Szene) und eine Datei (das Modell). Die Teile sind
durch eine vereinbarte Grenzzeile getrennt. Im Projekt schickt die Knotenansicht so ihre
Bestellung. Bis zum 20.10.2026 zerlegte der Heim-PC sie mit dem E-Mail-Leser der
Standardbibliothek; seither mit einem streamenden Teiler (siehe dort).

**Streamender Teiler** — Ein Programmteil, der eine grosse Sendung in Stücken liest, statt
sie erst ganz in den Arbeitsspeicher zu holen, und eine mitgeschickte Datei sofort auf die
Platte schreibt. Im Projekt `knotenweg.teile_formular`: Der Heim-PC nimmt so ein Modell an,
ohne dabei alle anderen Anfragen anzuhalten («die Reihe», siehe Sperre).

**Lange Wartezeit (der Mac-App)** — Wie lange die Mac-App auf die erste Antwort des Heim-PC
wartet: üblich 25 Sekunden, damit ein ausgefallener Rechner rasch gemeldet wird; für die zwei
Wege, die ein Modell hochladen (Auftrag stellen, Datei laden), seit dem 20.10.2026 300
Sekunden — sonst meldete die App «nicht erreicht», während der Heim-PC noch arbeitete.

**Freigabe-Marke** — Ein Vermerk im Laufzettel eines Auftrags, der sagt: *Hier hat ein Mensch
freigegeben, nicht die Maschine.* Die fremde Brücke gibt sich ihren Freigabe-Token selbst;
darum zählt ein Token allein bei uns nicht. Die Marke `visbox_freigabe` entsteht nur, wenn in
der Knotenansicht jemand «Freigeben» drückt, und wirkt nur nach diesem Schritt. Im Projekt:
`bruecke.FELD_FREIGABE_KNOTEN`, geschrieben von `knotenweg.freigeben`.

**App-Modus (aus einem Knotengraphen)** — Eine vereinfachte Oberfläche, die aus einem
fertigen Knotengraphen entsteht: Man markiert, welche Eingaben ein Mensch setzen darf und
welches Ergebnis er sieht; alles andere bleibt verborgen und gesperrt. Fast jedes
KI-Knotenwerkzeug hat das seit 2025 (bei Figma Weave «From Workflow to Tool»). Im Projekt
eine Richtungsfrage: Die Visbox-Seite könnte einmal so ein App-Modus der Knotenansicht
werden (`docs/RECHERCHE_KNOTENSYSTEME_2026-09-24.md`, R19).

**Teilgraph (Subgraph, Knotengruppe)** — Mehrere Knoten, zusammengefasst zu einem einzigen
Knoten, den man bei Bedarf aufklappt. Aussen sieht man nur die wichtigen Einstellungen,
innen die ganze Kette. Vorbild für den Render-Knoten: vorne ein Knoten, dahinter Pässe →
Bildmodell → Prüfung.

**Render-Pass (AOV)** — Ein einzelnes Zwischenbild, das ein Renderprogramm neben dem
fertigen Bild ausgibt: Tiefe, Normalen, Material-Kennung, Linien. «AOV» heisst *arbitrary
output variable*. In Blender, Houdini und Unreal ist jeder Pass ein eigener Anschluss am
Knoten. Bei uns sind es die Geometrie-Pässe, die das Bildmodell führen (siehe *Multipass*).

**Ebene (im Ergebnis)** — Unser Wort für einen *Render-Pass*, der mit dem Bild ausgeliefert
wird: das Schönbild aus Blender, die Tiefenkarte oder die Material-Kennung, je Kamera eine
eigene Datei. Jede Ebene kommt mit ihrer **Bedeutung** in Zahlen — bei der Tiefe etwa, wie
viele Meter «ganz hell» und «ganz dunkel» sind —, damit niemand raten muss, was ein Pixel
heisst. Bestellt wird sie mit `render.passes`; eingeführt am 29.09.2026 nach dem
KosmoOrbit-Entscheid E124.

**An der Aussengrenze übersetzen** — Drinnen spricht der Code seine eigenen Wörter
(«fehlt», «nicht entscheidbar»), hinaus geht die Datei in den Wörtern des Empfängers
(«not_measured», `false`). Die Übersetzung steht an genau einer Stelle, dort, wo die Datei
geschrieben wird. So bleibt die feinere innere Unterscheidung für unsere Prüfungen
erhalten, und der Empfänger bekommt nur, was sein Vertrag lesen kann. Im Projekt:
`kosmo_szene.nur_vertragsfelder`, seit dem 29.09.2026.

**Rahmung (nach dem Bauwerk)** — Worauf die Kamera ihren Bildausschnitt einstellt: auf die
ganze Szene mit Grundstück, oder nur auf das Gebäude. Nach der Szene gerahmt, füllte der Testbau
mit grosser Bodenplatte nur 2 % des Bildes — für das Bildmodell ein Detail, das es übermalt.
Nach dem Bauwerk sind es 21 %. Seit dem 30.09.2026 die Vorgabe am Heim-PC; für KosmoOrbit nach
einem Beweislauf.

**Umrisstreue (aus den Bildkanten)** — Ein Mass vom 30.09.2026: Hat das erzeugte Bild dort
Kanten, wo das Gebäude seinen Umriss und seine Stufen hat? Gelesen wird nur das Bild selbst und
die Tiefenkarte aus Blender — kein Hilfsmodell, das Tiefe schätzt und dabei täuschen kann. Die
Zahl «Abhebung» sagt, wie viel besser das Bild den Umriss trifft als ein Bild mit gleich vielen
zufälligen Kanten: eine graue Fläche bekommt 0, Rauschen 1. Im Projekt: `aiimaging.umriss`;
es urteilt noch nicht, bis der Heim-PC gemessen hat, ob es trennt.

**Formprüfung (Augenurteil als Referenz)** — Die Frage, ob die Gebäudeform im erzeugten Bild
steht, beantwortet bisher nur ein Mensch, der das Bild ansieht. Seit dem 30.09.2026 ist dieses
Augenurteil der Massstab, an dem Zahlen geprüft werden: Eine Zahl taugt als Formprüfung erst,
wenn sie dem Auge folgt. Das Auge urteilt dabei **blind** — es sieht das Bild unter einem
Decknamen, bevor es irgendeine Zahl kennt. Im Projekt: `aiimaging.formkandidaten`, Auftrag
`auf-20260930-194`.

**AUC (Fläche unter der Kurve)** — Eine Zahl zwischen 0 und 1, die sagt, wie gut ein Mass zwei
Gruppen trennt. Man nimmt ein Bild, das das Auge «steht» nennt, und eines, das es «steht nicht»
nennt, und fragt: Hat das gute die höhere Zahl? Die AUC ist der Anteil aller solcher Paare, bei
denen das stimmt. 0,5 heisst Münzwurf, 1,0 heisst: trennt immer. Sie braucht keine Schwelle,
darum eignet sie sich, bevor eine festgelegt ist. Im Projekt: `tools/formpruefung_auswertung.py`.

**Störfaktor** — Etwas, das gleichzeitig mit dem Gesuchten schwankt und darum eine Zahl gut
aussehen lässt, ohne dass sie das Gesuchte misst. Am 30.09.2026 gefunden: Fast alle Bilder,
die das Auge «steht nicht» nannte, stammten aus der alten Rahmung. Eine Zahl, die nur die
Rahmung erkennt, sah darum wie eine Formprüfung aus. Die Abhilfe ist die **AUC im Fall**: nur
Bilder desselben Falls (gleicher Körper, gleicher Blick, gleiche Rahmung) werden verglichen.

**Kreuzpaar** — Dasselbe Bild zweimal gemessen: einmal gegen die eigene Soll-Karte, einmal
gegen die eines anderen Blicks. Bei einem Bild, dessen Form steht, muss die eigene gewinnen.
Das braucht kein Auge, weil man weiss, welche Karte die richtige ist.

**Decke (einer Probe)** — Der beste Wert, den eine Probe überhaupt hergeben kann, gemessen an
einem Bild, das sicher richtig ist — bei uns dem Schönbild aus Blender. Verliert schon dieses
vollkommene Bild die Probe, taugt die Probe nichts, nicht die geprüfte Zahl. Am 30.09.2026
fehlte sie bei der Kreuzprobe (Auftrag 194): Alle Zahlen fielen durch, und niemand konnte
sagen, ob es an ihnen lag oder an der Probe. Im Projekt: `decke` in
`tools/formpruefung_auswertung.py`, gemessen in `auf-20260930-195`.

**Vorab festgelegte Regel** — Eine Entscheidungsregel, die aufgeschrieben wird, **bevor**
gemessen wird: ab welchem Wert eine Zahl als tauglich gilt und was dann folgt. Sie schützt
davor, die Regel nachträglich so zu biegen, dass das gewünschte Ergebnis herauskommt. Fällt
eine Messung durch, bleibt das Urteil stehen; eine bessere Regel gilt nur für **neue** Bilder.
Im Projekt: in jedem Messauftrag an den Heim-PC seit dem 30.09.2026.

**Wiederholbarkeit (des Augenurteils)** — Ob derselbe Beurteiler dasselbe Bild beim zweiten
Mal gleich einordnet, ohne zu wissen, dass er es schon gesehen hat. Am 30.09.2026 zufällig
gemessen: 18 Bilder kamen in zwei Serien doppelt vor, und das blinde Auge des Heim-PC gab
18-mal dasselbe Etikett. Das stützt das Auge als Massstab — es ist aber derselbe Beurteiler,
kein zweiter.

**Ausgewogene Trefferquote** — Eine Trefferquote, die beide Seiten gleich wichtig nimmt: der
Anteil der guten Bilder, die als gut erkannt werden, und der Anteil der schlechten, die als
schlecht erkannt werden — davon der Mittelwert. Eine gewöhnliche Trefferquote lässt sich
schönen, wenn fast alle Bilder gut sind: Wer dann immer «gut» sagt, liegt fast immer richtig.
Im Projekt: die Regel für die Schwelle der Formprüfung (`auf-20260930-196`, mindestens 0,80).

**Stichentscheid** — Die Regel, die sagt, wer gewinnt, wenn zwei Kandidaten gleich gut
abschneiden. Am 30.09.2026 (Auftrag 195) stand er vorab fest — «die höhere Hochbau-Zahl im
Fall» —, ergab aber exakten Gleichstand (57 von 59 Paaren bei beiden). Die Wahl der
Umrisstreue fiel darum **nach** der Messung und ist im Protokoll so benannt.

**Nachmessung (Replikation)** — Dieselbe Frage noch einmal an neuen Fällen gestellt, um zu
sehen, ob ein Ergebnis hält oder Glück war. Am 30.09.2026 lehrreich: In Auftrag 195 trennte
die Umrisstreue fast perfekt (0,96), an 96 neuen Bildern in Auftrag 196 nur noch mässig (0,81),
und beim Hochbau unter voller Steuerung gar nicht. Ein einzelnes gutes Ergebnis an wenigen
Bildern ist ein Hinweis, kein Befund.

**Grauzone (des Augenurteils)** — Die Bilder, bei denen auch das Auge «unklar» sagt: beim
Hochbau etwa eine Fassade, die sich wie eine Öffnung in einer Wand liest. Keine der geprüften
Zahlen trennt sie von den stehenden Bildern. Das ist weniger überraschend, als es klingt: Eine
Zahl, die nur Kanten und Helligkeit liest, kann nicht sicherer sein als ein Beurteiler, der
das ganze Bild versteht und trotzdem zögert.

**Richtungstreue (der Kanten)** — Ein Kandidat für die Formprüfung: Laufen die Kanten im Bild
**parallel** zu den Kanten des Gebäudes? Eine Holzfassade hat viele Kanten, aber in alle
Richtungen — sie zählt hier wenig, anders als bei der Umrisstreue. Zufall ergibt 1.

**Flächentrennung** — Ein Kandidat für die Formprüfung: Ist das Bild innerhalb jeder Fläche des
Gebäudes (Wand Süd, Wand West, Platte) ruhig und springt es an deren Grenzen? Gemessen als
Anteil der Helligkeitsunterschiede, der **zwischen** den Flächen liegt statt innerhalb (0 bis 1).
Die Flächen kommen aus dem Material-ID-Bild von Blender. Graue Fläche und Rauschen ergeben 0.

**Sobel-Filter** — Ein kleines Rechenverfahren, das in einem Bild findet, wo die Helligkeit von
einem Pixel zum nächsten stark springt — also Kanten. Es ist alt, einfach und hat keine
Vorlieben: Es sieht nur, was im Bild ist. Im Projekt: in der Umrisstreue.

**Regel B (null-Regel, E123)** — Die Abmachung zwischen allen Teilen von KosmoOrbit vom
29.09.2026: Kommt ein Wert als «unbekannt» (`null`) an, nimmt der Empfänger ihn an und meldet
mit Namen, was fehlt — statt die ganze Lieferung abzuweisen. So steht die Ursache da, wo man sie
lesen kann. Bei uns seit dem 30.09.2026 am Eingang für Aufträge, im Feld `nicht_bekannt`.

**Hinweis gegen Vorbehalt** — Zwei Arten von Zusatzsätzen an einem Ergebnis. Ein *Vorbehalt*
schränkt die Aussage ein («die Schwelle ist nicht geeicht») und verdient ein Warnzeichen. Ein
*Hinweis* sagt nur, woher etwas kommt («der Standpunkt steht im Raum Süd») und soll nicht
warnen. Wer beides gleich zeigt, gewöhnt die Leser daran, Warnzeichen zu übersehen.

**Bildanteil (Geometrieanteil)** — Wie viel des Bildes überhaupt Geometrie zeigt, statt
Himmel oder Leere: 0,56 heisst, gut die Hälfte der Pixel trägt Gebäude oder Gelände. Er
entscheidet mit, ob eine Messung trennen kann — derselbe Hochbau misst mit grosser
Geländeplatte (Anteil 0,56) ganz anders als mit kleiner (0,15). Wer zwei Zahlen vergleicht,
muss darum ihren Bildanteil mitlesen.

**Ordnung an Tiefensprüngen** — Ein Versuch vom 24.09.2026, auch saubere, gut gemachte Bilder
zu prüfen: Stimmt die Reihenfolge «vorne – hinten» an den Stellen, wo die Tiefe springt? Am
Heim-PC trennte sie nicht — eine graue Fläche bekam die Bestnote 1,0. Sie ist darum wieder
entfernt (`auf-20260924-172`) und steht nur noch als Befund da.

**Eingangswächter (bei KosmoOrbit)** — Ein Prüfprogramm im KosmoOrbit-Repo
(`auftrags-eingang-gate`), das jedes neue Blatt in ihrem Eingangsordner meldet, solange es
unbeantwortet ist. Als wir am 29.09.2026 sechs Blätter direkt hineinlegten, meldete er sie
sofort — dafür ist er da. Ob ein Blatt als «gesehen» gilt, entscheidet ihr Integrator, nicht wir.

**Laufnummer (eines Auftrags)** — Die fortlaufende Zahl am Ende eines Auftragsnamens, etwa
178 in `auf-20260929-178`. Sie gilt über alle Worker und alle Tage und darf nur einmal vergeben
werden; `tools/einbau.py` nennt die nächste freie. Nicht zu verwechseln mit dem *Rang*, der nur
die Reihenfolge bei einem Worker angibt. Am 29.09.2026 vergaben zwei Sitzungen gleichzeitig die
177 — die Vergabestelle sieht nur, was schon auf `main` liegt.

**Fassung schneiden (Release)** — Einen Stand der Software festhalten und unter einer Nummer
herausgeben, etwa «v0.1.5». Was bis dahin nicht fertig ist, kommt nicht mit und wandert in die
nächste Fassung. KosmoOrbit hat v0.1.5 am 25.09.2026 geschnitten — ohne das erste echte Bild
vom Heim-PC, das damit in v0.1.6 rutschte.

**Meilenstein** — Ein Zwischenziel mit Datum, an dem sich prüfen lässt, ob ein Plan hält: nicht
«weiterarbeiten», sondern «bis Ende Oktober besteht ein echtes Bild die Prüfung». Im Projekt:
`docs/PLAN_BIS_FEBRUAR_2027.md`.

**Kritischer Pfad** — Die Kette von Schritten, bei der jede Verspätung das Enddatum verschiebt,
weil jeder Schritt auf den vorigen wartet. Was nicht auf ihm liegt, darf sich verzögern, ohne
dass die Abgabe wackelt. Im Projekt: im Plan bis Februar, heute über die Kalibrierung der
Geometrieprüfung und das erste bestandene Bild.

**MPS (Apple-Rechenweg)** — «Metal Performance Shaders»: der Weg, auf dem Bildmodelle auf einem
Apple-Rechner die Grafikeinheit nutzen, statt einer NVIDIA-Karte (CUDA). Er war als Ausweichweg
für einen Laptop geplant; seit dem Owner-Entscheid E21 ist wieder der Heim-PC das Zielgerät, und
der Weg ist nie gebaut worden.

**Integrator (KosmoOrbit Int 1)** — Die Sitzung bei KosmoOrbit, die alle Beiträge in deren
Hauptstand einspielt: Vertrag, Brücke und fremde Lieferungen wie die Knoten des UI-Workers.
Seit dem 29.09.2026 heisst sie «KosmoOrbit Int 1»; Hilfs-Sitzungen «Int 2–5» bereiten zu,
spielen aber nie selbst ein. Für uns heisst das: Antworten und Aufträge gehen immer an Int 1,
und etwas gilt erst als eingebaut, wenn es dort eingespielt ist.

**Insel-Karte (n1)** — Der Entwurf des UI-Workers für die Knoten der Bildstation: jeder Knoten
als freistehende Karte mit runden Ecken und klaren Anschlüssen. Der Owner hat ihn am 24.09.2026
gewählt; eingebaut wird er vom Integrator in Posten KV1–KV10, von denen in v0.1.5 nur KV1 zum
Teil steckt.

**Forschungslizenz** — Eine Lizenz, die ein Modell nur zum Forschen und Ausprobieren
freigibt, nicht zum Verkaufen. Qwen-Image-2.1 steht unter einer solchen («research or
evaluation purposes only»). Wer das Modell in einem verkauften Programm laufen lässt, bricht
sie, auch wenn die Bilder selbst nicht ausdrücklich eingeschränkt sind.

**Lizenz offen (Einbau mit offener Lizenz)** — Die Regel vom 30.09.2026 (Owner-Entscheid
E128) für Qwen-Image-2.1: Das Modell ist regulär bestellbar, obwohl seine Lizenz heute keinen
Verkauf erlaubt. Dafür trägt jedes Ergebnis den Vermerk `engine_license_open`, und bevor die
Software veröffentlicht wird, muss die Lizenz gekauft oder das Modell ersetzt sein. Strenger als
ein freies Modell (nie Standard, immer markiert), lockerer als die Forschungs-Ausnahme (kein
Schalter, auch über KosmoOrbit bestellbar).

**Forschungs-Ausnahme** — Die Erlaubnis des Owners vom 29.09.2026, ein Modell mit
Forschungslizenz für die Vertiefungsarbeit trotzdem rechnen zu lassen. Sie hat enge Grenzen:
nur am Heimrechner, nur mit einem ausdrücklich gesetzten Schalter, nie als Standard, nie von
KosmoOrbit bestellbar, und vor einem Verkauf wird das Modell entfernt oder lizenziert. Im
Projekt: `backbone.ladefreigabe`, Regel 1 in `CLAUDE.md`.

**Variantenachse (Wedge)** — Statt «mach drei Varianten» sagt man, **was** sich ändern soll,
etwa «Startwert × 3, Kamera × 4», und das Programm erzeugt alle Kombinationen, hier 12. So
weiss man vor dem Lauf, wie viele Bilder entstehen und wie lange es dauert. Der Begriff
kommt aus Houdini.

**Übernehmen (Bake)** — Aus einer Vorschau wird ein festes Ergebnis, das nicht mehr
mitläuft, wenn sich der Graph ändert. In Grasshopper heisst das «Bake». Für den
Render-Knoten: Ein Bild ist erst Vorschau; erst «Übernehmen» macht es zum Projektbild der
Mappe.

**Überbrücken (Bypass)** — Einen Knoten ausschalten, ohne ihn zu löschen: Was hineinkommt,
geht unverändert hindurch. Nützlich für den Vergleich «mit und ohne KI-Schritt».

**Credit** — Eine Recheneinheit, die Cloud-Dienste wie Figma Weave je Lauf abziehen; bei
Weave etwa ein US-Cent. Die Dienste zeigen den Preis vor dem Lauf am Knoten. Bei uns ist
der Aufwand keine Gebühr, sondern Rechenzeit auf der HomeStation.

**Abwesenheitsbefund** — Die Aussage «das gibt es nirgends». Sie ist nur so gut wie die
Suche, die sie stützt, und wird darum so gekennzeichnet. Im Projekt: «Kein Werkzeug prüft
das Bild gegen die Geometrie» (Recherche vom 24.09.2026).

**Render-Umgebung** — Die eigene Python-Umgebung (siehe *venv*) auf der HomeStation, in der
die grossen Rechenpakete für das Bildmodell liegen (`torch`, `diffusers`). Das gewöhnliche
Python des Rechners hat sie nicht. Startet man den Abholer von Hand mit dem falschen Python,
nimmt er Aufträge an und scheitert erst beim Rendern. Seit dem 24.09.2026 sagt die Probe
(`tools/abholen.py --probe`) vorher, ob die Render-Umgebung da ist (`render.umgebung_da`).

**Wandabstand (Mindestabstand der Aussenkamera)** — Wie nah die automatisch gesetzte Kamera
der Fassade eines Gebäudes mindestens kommen darf. Die Kamera wird sonst aus dem Bildwinkel
gerechnet: so weit weg, dass das Gebäude den gewünschten Teil des Bildes füllt (siehe
*Deckungsgrad*). Bei kleinen Bauten wäre das sehr nah; der Wandabstand setzt dort eine
Untergrenze. *In diesem Projekt 3 m seit dem 24.09.2026, vorher 10 m.* Der alte Wert war
gesetzt, nie gemessen, und schob die Kamera bei einem 8 m langen Bau so weit zurück, dass das
Gebäude zu klein im Bild stand und die eigene Rahmungsprüfung zwei von drei Ansichten sperrte.
Konstante `kameras.WANDABSTAND_M`. Für Innenräume gilt ein eigener, kleiner Wert
(`raumkamera.WANDABSTAND_INNEN_M`, 0,30 m).

**Abholer-Puls** — Eine kleine Datei (`abholer-puls.json`), die der Abholer nach **jedem**
Durchgang in die Auftragsablage schreibt, auch wenn er nichts zu tun hatte: wann er zuletzt
nachsah und wie viele Aufträge er dabei sah, rechnete oder liegen liess. Wozu: Ohne sie sah
ein Abholer, der läuft und nichts zu tun hat, genau gleich aus wie einer, der gar nicht läuft.
Aus dem Alter des letzten Pulses liest `/health` seit dem 24.09.2026 einen von fünf Zuständen
(nie gesehen, arbeitet, wartet, läuft leer, steht). Siehe *Lebenszeichen gegen
Fortschrittszeichen* — der Puls ist ein Lebenszeichen.

**Farbtemperatur (Kelvin)** — Wie warm oder kalt ein Licht wirkt, als Zahl ausgedrückt: um
2000 K rötlich wie Kerzenlicht, um 5000 K die Nachmittagssonne, um 6500 K neutrales
Tageslicht, darüber bläulich. Die Zahl stammt aus der Physik glühender Körper (je heisser,
desto bläulicher). Im Projekt kann eine Bestellung seit dem 24.09.2026 die Farbtemperatur der
Sonne angeben (`render.sun.kelvin`); `aiimaging.sonne.kelvin_zu_farbe` rechnet daraus die
Lichtfarbe für Blender, als Näherung.

**Speicher-Riegel (Grafikspeicher)** — Eine Prüfung **vor** dem Laden des Bildmodells: Ist auf
der Grafikkarte zu wenig Speicher frei (siehe *VRAM*), wird gar nicht erst geladen. Der
Auftrag wartet in der Reihe, und sein Wartegrund steht dabei, statt dass der Lauf mitten im
Rechnen abbricht. Seit dem 24.09.2026, Grenze 4096 MiB, vorläufig abgeleitet und noch nicht
am Gerät gemessen (`abholer.MINDEST_FREI_MIB`).

**Konvention (einer Himmelsrichtung)** — Die Abmachung, von wo aus ein Winkel gezählt wird.
Beim *Azimut* gibt es zwei verbreitete: ab Norden im Uhrzeigersinn (Karten) oder ab Süden
(Bauphysik). Wer die falsche annimmt, dreht die Sonne um 180 Grad — Vormittag wird
Nachmittag. Im Projekt galt für Bestellungen aus KosmoOrbit bis zum 24.09.2026 die falsche;
ihr Vertrag zählt ab Norden (`sonne.KOSMO_KONVENTION`).

**Transmission (Glas im Renderer)** — Wie viel Licht ein Material **durch sich hindurch**
lässt und dabei bricht, wie eine Glasscheibe. Nicht zu verwechseln mit dem *Alphakanal*:
Alpha lässt einen Teil der Strahlen am Material vorbei, als wäre an der Stelle nichts.
Trägt ein Glas beides (so kam es aus KosmoOrbit), laufen die meisten Strahlen ungebrochen
durch — die Scheibe wirkt wie Luft. Befund vom 24.09.2026 zu B161. Seit dem 29.09.2026 zählt
unsere Modellstand-Prüfung ein Material mit Transmission als durchsichtig, auch wenn es als
deckend (OPAQUE) exportiert ist — vorher zählte nur der Alpha-Weg.

**Stilllegen (eines Bildmodells)** — Ein Modell bleibt im Register des Projekts
eingetragen, mit Lizenz und Befunden, wird aber nicht mehr angeboten und nicht mehr
geladen. Ein Auftrag, der es trotzdem verlangt, wird abgelehnt, bevor etwas geladen wird,
und nennt den Grund. Der Unterschied zum Löschen: Man sieht später noch, dass es geprüft
wurde und warum es draussen ist. Im Projekt seit dem 29.09.2026 für das Qwen-Modell mit
eigener Formsteuerung (`backbone.Backbone.stillgelegt`).

**Kosmo-Tafel (Tafel)** — Eine private Bildwand des Owners auf claude.ai, auf der Bilder aus
Software, Proben und Worker-Arbeit nebeneinander hängen, ähnlich einer Pinnwand. Jeder Worker legt
seine Bilder dafür auf den Zweig `zentrale` im KosmoOrbit-Repo (`tafel/<worker>/`), mit Titel und
kurzer Notiz; aufgehängt werden sie von dort. Keine Personen, keine Adressen, keine Heimpfade.
*Im Projekt:* seit dem 14.10.2026; die Knotenkarten erzeugt `tools/knoten_tafel.py`.

**Knotenkatalog** — Die Liste aller Knotenarten, die das Vis-Werkzeug kennt, mit Namen, Kurzhilfe,
Gruppe und den Ein- und Ausgängen jeder Art. Seit dem 21.10.2026 siebzehn, darunter Modell,
Oberfläche (früher «Material-Bausteine»), Material, Farbpalette, Kamera (früher «Auto-Kamera»), Stimmung,
Prompt, Prompt-Kombinierer, Render, Varianten, Bildvergleich und Aufs Blatt. *Im Projekt:* `VIS_NODE_KATALOG` in `kosmovis/packages/kosmo-kernel/src/derive/visgraph.ts`;
erklärt in `docs/KNOTEN_ERKLAERT.md`.

**Gruppe eines Knotens (Quelle, Wandler, Render, Ausgabe)** — Die Ordnung der Knotenarten nach
ihrer Rolle: *Quellen* bringen etwas in den Graphen (das Modell, ein Bild), *Wandler* formen Text und
Zahlen, *Render* bestellt das Bild, *Ausgaben* zeigen es oder legen es ab. Sichtbar als schmaler
Farbstreifen unter dem Kopf jedes Knotens; am Rechnen ändert sie nichts.

**Anschlusssorte (Porttyp)** — Die Art dessen, was durch eine Linie zwischen zwei Knoten fliesst.
Das Vis-Werkzeug kennt sechs, jede mit eigener Farbe: Szene (das 3D-Modell), Prompt (Text), Material
(Materialsätze), Zahl, Kameras (Standpunkte) und Bild. Verbinden lassen sich nur Anschlüsse
derselben Sorte. *Nicht zu verwechseln mit* **Anschluss (Port)** *im Netzwerk, der Nummer hinter
einer Adresse.*

**Preset (Voreinstellung)** — Ein fertiges Paket von Einstellungen, das man als Ganzes wählt statt
jeden Wert einzeln. Am Render-Knoten: Entwurf schnell, Präsentation, Nacht, Innenraum — je mit
Auflösung, Sonne und Zahl der Samples. Ohne Preset gilt die Vorgabe (1600 × 1000, 128 Samples).

**Geometrie-Treue** — Ein Wert von 0 bis 1, der sagt, wie eng die KI beim Veredeln der Form des
Modells folgen soll. Vorgabe 0,8. Am Heim-PC wird er zur Stärke der Formführung; gemessen ist, dass
mehr nicht immer besser ist (0,8 schnitt besser ab als 1,0).
*Im Projekt:* Eingang «Geometrie-Treue» am Render-Knoten, Feld `render.faithful` im Auftrag.

**Bildwerkzeug** — Am Render-Knoten der Name für das KI-Bildmodell, das ein Blender-Bild veredelt
(Vorgabe Z-Image Turbo). Im Code heisst dasselbe *Backbone*. Bei «nur Cycles» und «Strichzeichnung»
ist keines im Spiel.

**Strichzeichnung (Line-Art)** — Ein Bild nur aus Linien, wie eine Handskizze, ohne Flächen und
Licht. Am Render-Knoten ein Schalter; er rechnet ohne KI-Veredelung.

**Rückgängig (Undo)** — Einen Arbeitsschritt zurücknehmen. Im Vis-Werkzeug ist jede Änderung am
Graphen ein Befehl und darum rückgängig machbar — auch eine ganze Vorlage wie «Drei Stimmungen
einfügen» als *ein* Schritt. Bilder und der Zustand eines Renders gehören nicht dazu; sie liegen nur
im laufenden Programm.

**Viewport-Aufnahme** — Ein Schnappschuss dessen, was die 3D-Ansicht gerade zeigt (*Viewport* heisst
das Fenster, in dem das Modell dreidimensional zu sehen ist). Kein Rendering, kein Heim-PC. In
KosmoOrbit über «Für Vis aufnehmen» im Entwurf; Visbox hat keine 3D-Entwurfsansicht und darum keine
Aufnahmen.

**Kuratierfläche** — Die Vollbildansicht des Vis-Werkzeugs, in der alle fertigen Bilder als Karten
nebeneinander liegen: vergleichen, bewerten, auswählen, nacharbeiten — etwa einen *Farbangleich*, bei
dem ein Bild die Farbstimmung eines Vorbilds bekommt.

**Prüfurteil (QA)** — Das Ergebnis der Prüfung, ob ein erzeugtes Bild zur Form des Modells passt
(*QA* für *Qualitätssicherung*). Am Bild steht es als «QA ok», «QA ✗» oder «nicht beurteilbar»,
daneben der Grund. Rechnet der Heim-PC mehrere Kameras, zählt das schwächste Bild.

**Veraltet (ein Bild am Render-Knoten)** — Ein fertiges Bild, dessen Auftrag sich seither geändert
hat: anderer Prompt, andere Einstellung. Das Bild bleibt stehen, der Knoten sagt aber «veraltet» —
es zeigt nicht mehr, was ein neuer Lauf liefern würde. Derselbe Gedanke beim Laden eines Modells am Heim-PC
(Befund 307 B1, 21.10.2026): Ist seit dem letzten «Datei laden …» eine andere Mappe offen, meldet dessen Stand
`veraltet` mit Satz, statt gelöscht zu werden — nichts geht verloren, und niemand hält ihn für die offene Mappe.

**KosmoPublish (Plakatblatt)** — Der Teil von KosmoOrbit, in dem Pläne und Bilder auf Blätter für
Präsentation und Druck gesetzt werden. Der Knoten «Aufs Blatt» legt ein Render dorthin. In Visbox
gibt es keine Blätter; der Knoten sagt das.

**Fertiger Anfang (Startgraph)** — Ein kleiner, schon verbundener Graph, den ein Dokument ohne
Graph bekommt, damit man nicht vor einer leeren Fläche steht: Modell, Auto-Kamera, Stimmung und
Prompt, zusammengeführt im Kombinierer, dann Render und Bildvergleich. Er rechnet nichts von
selbst — erst «Ausführen» bestellt ein Bild. In Visbox entsteht er beim Öffnen, in KosmoOrbit auf
Knopfdruck («Fertigen Anfang anlegen»), weil dort schon das Öffnen sonst ein gespeichertes, mit
anderen geteiltes Projekt verändern würde. *Im Projekt:* Entscheid 91, `start-graph.ts` im
Vis-Werkzeug.

**Rückgängig-Klammer** — Mehrere Arbeitsschritte, die als **einer** gelten: Ein einziges
«Rückgängig» nimmt sie alle zurück. So kommt der fertige Anfang mit seinen sieben Knoten und sechs
Linien in einem Schritt und geht in einem Schritt wieder. *Im Code:* `history.beginGroup()` …
`endGroup()`.

**Standpunkte des Heim-PCs (Vorschau an der Auto-Kamera)** — Die drei Blickrichtungen, die der
Heim-PC rechnet, wenn ein Auftrag keine eigenen Kameras mitbringt: von Süden frontal, von Südosten
und von Nordwesten über Eck. Visbox zeigt sie am Auto-Kamera-Knoten vorab, gerechnet mit derselben
Regel wie am Heim-PC — als *Vorschau*, nicht als Bestellung: Der Auftrag sagt weiter «automatisch»,
damit der Heim-PC das Objektiv verschieben kann (siehe **Shift**), was eine mitgeschickte Kamera
nicht kann. *Im Projekt:* Entscheid 92, `knotenweg.heim_standpunkte`, `heim-standpunkte.ts`.

**Knoten «Oberfläche» (früher «Material-Bausteine»)** — Ordnet jeder Bauteil-Art (Fassade, Dach, Fenster,
Boden, Übrige) ein Material zu. Hängt an einer Art nichts, behält sie das Material aus dem Modell. Türen
zählen zu «Übrige». Er liest weiter die Wandschichten als Sätze für das Bildmodell. *Im Projekt:* Entscheid 111;
der interne Name bleibt `material`, damit alte Graphen ohne Umbau weiterlaufen; `OberflaecheKnoten.tsx`.

**Knoten «Material» (aus der Bibliothek)** — Ein Stoff aus der Bibliothek der elf Materialien (Sichtbeton,
Fichte, Backstein …) mit Massstab (wie gross ein Bild der Textur auf dem Bauteil wird), Drehung und Relief.
Die Vorschau am Knoten zeigt ihn als Kugel, Würfel oder Fläche. Die eigentlichen Texturen liegen am Heim-PC.
*Im Projekt:* Entscheid 111 B; Bibliothek `VIS_MATERIAL_BIBLIOTHEK`, gleich mit `materialwahl.BIBLIOTHEK`.

**Knoten «Farbpalette» (Leitfarbe)** — Bis zu vier Farben. Die gewählte, die **Leitfarbe**, tönt das Material,
an dem die Palette hängt, so stark wie eingestellt. Alle Farben gehen zusätzlich als Satz an das Bildmodell
(«Farbpalette: Helles Beige, Sand …»). *Im Projekt:* Entscheid 111 C; `farbWort` macht aus einer Farbe ein Wort.

**Erklärkarte (je Knoten, je iPad-Bereich)** — Ein Bild für die Tafel, das genau einen Knoten der Knotenansicht erklärt: wozu er
dient, was man an ihm einstellt (jedes Feld in einem Satz), was hineinfliesst und herauskommt, was er auslöst, womit
er meist verbunden ist und wo seine Grenze liegt. *Wozu:* Wer die Knotenansicht zum ersten Mal sieht, soll einen
Knoten verstehen, ohne den Code zu lesen. *Im Projekt:* seit dem 23.10.2026 siebzehn Karten und eine Übersicht,
erzeugt von `tools/knoten_tafel.py` aus `docs/KNOTEN_ERKLAERT.md` (Protokoll 74, Erklärkarten je Knoten). **Auch für die iPad-App:** seit
dem 24.10.2026 je Bereich eine Karte (Koppeln, Zeichenfläche, Ebenen, Parkfach, Mappe …) mit gezeichnetem Bildschirm,
nummerierten Teilen und — getrennt — dem, was beschlossen, aber nicht gebaut ist; elf Karten im Abteil «Visbox · iPad»,
erzeugt von `tools/ipad_tafel.py`, Blatt `docs/IPAD_ERKLAERT.en.md` (Protokoll 74 §281).

**Typische Kette (der Knoten)** — Die Reihe von Knoten, die man für ein gewöhnliches Bild braucht, so verbunden,
wie man sie von Hand verbinden würde: Stimmung und Prompt in den Kombinierer, Material in die Oberfläche, Modell und
Kamera dazu, alles in den Render-Knoten, dahinter Varianten und Bildvergleich. *Im Projekt:* Visbox legt sie als
«fertigen Anfang» an, wenn eine Mappe noch keinen Graphen hat (`start-graph.ts`); die Übersichtskarte der Tafel zeigt sie.

**Ehrliche Grenze (auf einer Erklärkarte)** — Ein eigenes Feld jeder Erklärkarte, das sagt, was der Knoten **nicht**
kann oder wo er heute noch hinkt — etwa, dass die Vorschau noch nicht vom Grundbild ausgeht. *Wozu:* Eine Erklärung,
die nur sagt, was geht, verspricht mehr, als das Programm hält; schlechte Nachrichten bleiben drin. *Im Projekt:*
gelb umrandet auf jeder Karte von `tools/knoten_tafel.py`.

**Gezeichnetes Schema (Drawn schematic)** — Ein Bildschirm, nachgezeichnet statt fotografiert: Rechtecke, Knöpfe und
Beschriftungen an ihrem Ort, in den Farben und Massen des Programms, aber ohne echten Inhalt. Es sagt das selbst («not a
screenshot»). *Wozu:* Wo kein Gerät läuft, zeigt es trotzdem, wo was liegt — ohne vorzutäuschen, es sei ein Bild vom Gerät.
*Im Projekt:* auf den iPad-Erklärkarten; eine Probe prüft, dass jede Beschriftung darauf wirklich im Programm steht.

**Kamera-Knoten: Auto, Manuell, Modell** — Drei Arten, Standpunkte zu bestellen. **Auto:** der Heim-PC rechnet sie
aus Richtungen, Augenhöhe, Brennweite, Abstand und Perspektive. **Manuell:** ein Klick friert die Auto-Standpunkte
ein, danach tippt man Auge und Blickpunkt in Metern. **Modell:** wie früher die Standpunkte aus dem Entwurf (nur,
wo es einen Entwurf gibt). *Im Projekt:* Entscheide 109 und 113 (3); `KameraKnoten.tsx`.

**Stilprobe (am Bau)** — Eine Probe, die den fertigen Bau der Knotenansicht in einem Browser ohne Fenster öffnet und
nachmisst, ob die Gestaltung greift: ob die Inseln am Rand sitzen, die Kugel klein ist, Claudes Karte und das
Gesprächsfeld im Fenster stehen. Dazu prüft sie ohne Browser, dass jede Stildatei geschlossen ist. *Wozu:* Der Bau selbst
und die übrigen Proben merken eine **offene Klammer (im CSS)** nicht. Seit dem 21.10.2026 misst sie auch die Knoten
Kamera, Stimmung und Varianten nach (**Überstand**, **Reiterleiste**, überlappende Beschriftungen). *Wo:*
`tools/stil_probe.py`, `tests/test_stil_probe.py`.

**Überstand (am Knoten)** — Ein Teil im Knoten — ein Knopf, eine Beschriftung —, das breiter oder tiefer reicht als der
Kasten, in dem es steht. Weil der Kasten abschneidet, was hinausragt, sieht man davon nur eine halbe Schrift oder
gar nichts. *Wozu man es misst:* Ein Knopf, der halb fehlt, wirkt kaputt, und einer, der ganz fehlt, ist nicht zu
bedienen. *Im Projekt:* die **Stilprobe** misst ihn in Pixeln des Knotens, unabhängig davon, wie weit man hineinzoomt.

**Reiterleiste** — Eine Reihe von Wahlknöpfen, von denen immer genau einer gilt, wie die Reiter einer Kartei (etwa
«Auto | Manuell» am Kamera-Knoten oder «Licht + Satz | Licht | Satz» an der Stimmung). *Im Projekt:* sie soll in einer
Zeile stehen; bricht sie in zwei um, wird der Knoten höher als vorgesehen und schneidet unten ab.

**Vorgabe beim Anlegen (eines Knotens)** — Die Einstellung, die ein Knoten bekommt, wenn man ihn neu setzt. Sie gilt
nur in diesem Moment: Ein schon gespeicherter Knoten behält, was er hat, auch wenn sich die Vorgabe ändert. *Im
Projekt:* seit dem 21.10.2026 legt man den Kamera-Knoten auf «Auto» an; alte Graphen bleiben bei «Modell».

**Kegel (einer Kamera im 3D-Fenster)** — Eine kleine Pyramide aus Linien, die zeigt, wo eine Kamera steht und
wohin sie schaut. Im Kamera-Knoten steht für jeden Standpunkt ein Kegel im Modell; darunter das kleine Bild,
das diese Kamera sähe. *Im Projekt:* `kegelLinien` im 3D-Fenster.

**Live-Vorschau der Standpunkte** — Ändert man am Kamera-Knoten eine Einstellung, fragt die Knotenansicht den
Visbox-Server, wo die Kameras damit stünden — mit derselben Rechnung, die der Heim-PC beim Rendern fährt. So
zeigen die Kegel, was bestellt wird, nicht eine zweite Schätzung. *Im Projekt:* `GET /knoten/standpunkte`,
`standpunkteAbfrageDerMappe`.

**Grundlage je Stand** — Jede Stimmung braucht ihre eigene Grundlage, weil das Himmelsbild das Licht in Blender
ändert. Der Render-Knoten merkt sich darum die letzten Grundlagen je Stand der Eingaben; wechselt man zur vorigen
Stimmung zurück, gilt deren Grundlage wieder, ohne neu zu rechnen. *Im Projekt:* Entscheid 110 A, `grundlagenJeStand`.

**Führende Stimmung (bei Mehrfachwahl)** — Am Stimmung-Knoten darf man mehrere Stimmungen anhaken. Der Render-Knoten
bestellt heute die erste davon; ein Bild je Stimmung bestellt der Varianten-Knoten. *Im Projekt:* Entscheid 113 (4),
der Knopf «n Bilder» am Render-Knoten ist offen.

**Vorgeschaltet (Knoten)** — Ein Knoten, der über eine oder mehrere Linien in einen anderen fliesst. Der Render-Knoten
liest Stimmung und Oberfläche aus den vorgeschalteten Knoten, auch wenn sie über den Kombinierer kommen.

**Farbverlauf statt Vorschaubild** — Solange die verkleinerten Bilder der Himmel und Texturen nicht ausgeliefert
sind, zeigt der Knoten einen gezeichneten Farbverlauf bzw. den Grundton des Stoffs — und sagt es in der Kurzhilfe.
*Im Projekt:* `knoten-neu-vorschau.ts`; die Bilder liefert die HomeStation (Entscheid 113 (1)).

**Vertragsvorschlag (Schritt V)** — Eine Erweiterung der Bestellform, die wir vorschlagen, bevor der Hüter des
Vertrags sie selbst aufnimmt: neue Felder, alle freiwillig, mit einer Probe gegen echte Bestellungen. *Im Projekt:*
`cameras_auto`, `CameraSpec.perspektive`, `render.materialien` und die acht Stimmungen.

**Vorbild (Bild-Referenz)** — Ein fremdes Bild, das zeigt, wie etwas aussehen soll — eine Stimmung,
ein Material. Im Vis-Werkzeug hält es der Knoten «Bild-Referenz»; im Bildvergleich steht es neben dem
eigenen Bild. Aufs Blatt kommt es nicht, weil es kein Bild des Projekts ist.


**Monogramm-Kachel** — Ein schlichtes Quadrat mit zwei, drei Buchstaben, das auf einer Karte an
Stelle eines Logos steht, wenn kein freies Logo vorliegt. Es ist absichtlich keine Nachzeichnung
einer Marke. *Im Projekt:* auf den Werkzeugabbildungen (`docs/abbildungen/`), etwa «IFC» oder «gs».

**3D-Fenster (im Modell-Knoten)** — Ein kleines Bildfeld im Knoten «Modell», in dem das Gebäude
räumlich zu sehen ist — genau das Modell, das ein Render-Auftrag mitbekommt. Mit der Maus gezogen
dreht es sich, das Mausrad holt es näher; ein Doppelklick öffnet dasselbe Bild gross über der
Knotenansicht. Solange der Zeiger im Fenster ist, bleibt die Knotenansicht selbst still (sie
verschiebt und vergrössert sich nicht). Fehlt dem Rechner die nötige Grafikfähigkeit (siehe
**WebGL**), steht an der Stelle der Satz «Kein 3D in diesem Fenster», und alles andere geht weiter.
*Im Projekt:* Owner-Entscheid 109 A (klein fest im Knoten, Doppelklick gross),
`ModellKnoten.tsx` und `modell-vorschau-3d.tsx` im Vis-Werkzeug.

**WebGL** — Die Fähigkeit eines Browsers (und jeder Webansicht in einer App), mit der
Grafikkarte räumliche Bilder zu zeichnen — so wie ein CAD-Programm sein 3D-Fenster zeichnet, nur
innerhalb einer Webseite. Ohne sie bliebe ein 3D-Fenster leer. Die meisten Rechner haben sie; in
manchen Umgebungen fehlt sie (etwa auf einem Rechner ohne Bildschirm-Beschleunigung). Darum prüft
das 3D-Fenster zuerst, ob sie da ist, und sagt es sonst in einem Satz. *Im Projekt:* das 3D-Fenster
im Modell-Knoten zeichnet damit, über die freie Bibliothek three.js (MIT, im `NOTICE`).

**Nachgeladener Teil (der Knotenansicht)** — Ein Stück des Programms, das der Browser erst holt,
wenn es gebraucht wird, statt beim Öffnen der Seite. So wird die Seite nicht langsamer, nur weil
sie etwas kann, das gerade niemand benutzt. *Im Projekt:* das 3D-Fenster samt three.js liegt in
eigenen Dateien unter `kosmovis/apps/visbox-knoten/dist/assets/` und kommt erst, wenn ein
Modell-Knoten sein Fenster zeigt.

**Kopfteile (der Knotenansicht)** — Die kleinen Bedienteile, die schwebend am Rand über der Arbeitsfläche
stehen, nicht auf ihr: oben links die **Stationen-Palette** am Logo, oben rechts der **Einstellungs-Kreis**, der
**Speichern-Kreis** und die **Zweitgruppe**, unten links die **Claude-Marke**, oben in der Mitte die **Erzählzeile**.
In KosmoOrbit hängen sie nicht an einer Station, sondern am Programm drumherum; darum fehlten sie in Visbox, obwohl die
Knotenfläche selbst schon gleich war. *Im Projekt:* Entscheide 115/116, `kosmovis/apps/visbox-knoten/src/kopf.tsx`;
was KosmoOrbit zeigt und Visbox nicht, steht mit Grund in `kosmovis/UI_AUSNAHMEN.json`.

**Stationen-Palette (am Logo)** — Ein runder Knopf mit dem Logo oben links. Ein Klick führt zur Startansicht; fährt
man mit der Maus darüber (am iPad: erster Tipp), fächern sich wie Farbtupfer auf einer Malerpalette die Ziele auf — in
Visbox «Knoten» (die offene Fläche, markiert) und «Visbox-Seite». *Im Projekt:* `WerkzeugPalette.tsx`, wortgleich aus
KosmoOrbit; die Ziele meldet der Wirt an (`registrierePalettenQuelle`).

**Speichern-Kreis** — Ein runder Knopf neben dem Zahnrad, der still sagt, ob gesichert ist: ein kleiner Punkt, der nur
bei einem Fehler rot wird — dann auch mit Grund, laut. Angetippt zeigt er den Stand («Gesichert · jeder Schritt ·
zuletzt 14:32»). In Visbox sichert die Knotenansicht den Render-Graph bei jedem Schritt auf dem Heim-PC; Knöpfe zum
Sichern als Datei oder Öffnen gibt es dort nicht, weil die Mappe der Heim-PC hält. *Im Projekt:* `SpeichernKreis.tsx`,
Lage aus `graph-sichern.ts`.

**Zweitgruppe (des Inselkopfs)** — Die kleine Reihe oben rechts neben dem Zahnrad: ein Zustands-Chip, «Rückgängig»,
«Wiederholen» und die Nummer der laufenden Fassung. In KosmoOrbit ist der Chip der Sync (gemeinsames Arbeiten im selben
Modell), in Visbox der **Heim-PC-Chip**. *Im Projekt:* `InselZweitgruppe` in `InselKopf.tsx`.

**Heim-PC-Chip** — Ein kleines Schild in der Zweitgruppe, das in einem Wort sagt, wie es um den Rechenrechner steht
(«Heim-PC · bereit», «· nicht erreichbar», «· nicht gekoppelt»), in den Farben, die KosmoOrbit für den Sync nimmt: grün,
grau, gelb. Ein Klick öffnet «Wer rechnet?». *Im Projekt:* Entscheid 116 (5); Text aus `Knotenwirt.rechnerchip` im Kern.

**Claude-Marke** — Das Schild «Claude verbunden» unten links, das nur steht, solange Claude angeschlossen ist. Darüber
liegen Claudes **Karten** zum Anwenden oder Ablehnen; angetippt klappt die **Selbständigkeit** auf. Daneben zeigt «Im
Projekt: Du · Claude», wer ohne Karte etwas geändert hat, mit «Zurücknehmen» je Schritt. *Im Projekt:*
`ClaudeAnschluss.tsx` und `KosmoCoop.tsx`, wortgleich aus KosmoOrbit; den Zustand liefern die Mac-App und der
KI-Werkzeugsatz der Seite.

**Erzählzeile** — Eine Zeile oben in der Mitte, die in einem Satz sagt, was Claude gerade tut oder worauf es wartet
(«Claude wartet auf dich»). Ohne Erzählung steht sie nicht da. *Im Projekt:* `ErzaehlZeile.tsx`, wortgleich aus
KosmoOrbit. Bis zum 22.10.2026 standen «Anwenden»/«Ablehnen» gleich daneben; seit Entscheid 131 wird nur an der Karte
unten links entschieden, die Zeile zeigt nur den Satz (in Visbox blendet `visbox.css` die Knöpfe aus).

**Kartenzone (der KI-Maus)** — Die Stellen der Oberfläche, an denen die eigene Maus von Claude oder dem Assistenten
nicht klicken darf, weil dort ein Mensch entscheidet: die Karten mit «Anwenden»/«Ablehnen», die Erzählzeile, «Freigeben».
Klickt die Maus dorthin, antwortet sie «VERWEIGERT» mit Grund. *Im Projekt:* `KARTEN_SELEKTOR` in `kosmo-maus.ts`; seit dem
22.10.2026 gehört die Erzählzeile dazu (Fund E des Mac-Demolaufs).

**Lese-Kennung (L-n)** — Die Nummer, die ein Aufruf von Claude bekommt, der nur liest («L-1», «L-2» …). Vorschläge, die
eine Karte werden können, heissen «K-n»; so zählen die Karten ohne Lücken, und eine Nachfrage auf eine Lese-Kennung sagt
«Kein Vorschlag». *Im Projekt:* `Mcpkern.lesevorsatz`, seit dem 22.10.2026 (F15).

**Bild aus Skizze erzeugen** — Der Knopf am Render-Knoten, wenn eine Skizze vom iPad am Eingang «Skizze» hängt: Das
KI-Bild entsteht aus der Skizze und ihrer Bemerkung, ohne vorher eine Grundlage zu rechnen. Wie jeder Auftrag wartet es am
Knoten auf «Freigeben». *Im Projekt:* `BILD_AUS_SKIZZE_KNOPF`, an der Stelle von «Variante erzeugen» (Fund B, 22.10.2026).

**Thema (Papier, Kosmos)** — Die Grundfarbe der ganzen Oberfläche: **Kosmos** dunkel (die Vorgabe in KosmoOrbit und
seit dem 20.10.2026 auch in der Knotenansicht von Visbox), **Papier** hell. Umgeschaltet wird am Mac im Menü
«Darstellung → Thema wechseln (Papier/Kosmos)»; die App merkt sich die Wahl, weil das Webfenster nichts behält. *Im
Projekt:* Entscheid 116 (3), `thema.ts` im Wirt, `Knotenwirt.Thema` im Kern.

**Nahtstelle (für einen zweiten Wirt)** — Eine kleine, vorbereitete Stelle in einer fremden Datei, an der ein zweites
Programm etwas Eigenes anmelden kann, ohne die Datei zu ändern — wie eine Steckdose, die drüben niemand benutzt. So
kommt die Datei unverändert herüber, und doch tut sie in Visbox das Richtige. *Im Projekt:* die Muster
`registriereModellLaden` (Entscheid 90) und seit dem 20.10.2026 `registrierePalettenQuelle`, die wahlfreien Handgriffe
des Speichern-Kreises, `chip` und `onRundgang` der Zweitgruppe, `ausklapper` der Claude-Marke, seit S3/S4
`registriereKosmoName` (der Name «Assistent» an Kugel und Coop-Teilen) und `einstellungen-teile.tsx` (Schale und drei
Abschnitte der Einstellungen als eigene Bausteine) (KosmoOrbit-Zweig `claude/kosmovis-kopf`).

**Bote «visboxWirt» (zweite Brücke)** — Ein zweiter Weg zwischen Knotenansicht und Mac-App, neben dem **Bote
«visboxKi»**: Die Seite sagt der App, was ein Kopfteil will (Startansicht öffnen, Einstellungen, «Wer rechnet?»,
Selbständigkeit), und die App legt ihre Lage in die Seite (Heim-PC-Chip, ob Claude verbunden ist, Fassung,
Selbständigkeit, Thema). Das Kennwort des Heim-PC läuft nie darüber — die Lage hat kein Feld dafür. *Im Projekt:*
`wirt-bruecke.ts`, `Knotenwirtbote` in `Knotenki.swift`, `Knotenwirt` im Kern.

**UI-Ausnahme** — Ein Teil, den KosmoOrbit zeigt und Visbox bewusst nicht, weil es die Sache dahinter in Visbox nicht
gibt (etwa die Sync-Leiste: Visbox hat keinen gemeinsamen Raum). Jede Ausnahme steht mit Grund und Entscheid in einer
Liste, und eine Probe prüft, dass jeder Kopfteil von KosmoOrbit entweder eingesetzt oder dort benannt ist. *Im
Projekt:* `kosmovis/UI_AUSNAHMEN.json`, `tests/test_kosmovis_ui_gleichheit.py`.

**Befehlspalette (⌘K)** — Ein Suchfeld, das mit der Tastenkombination Befehlstaste + K über der Arbeitsfläche aufgeht:
Man tippt ein paar Buchstaben, und die Liste zeigt die passenden Befehle zum Ausführen. In KosmoOrbit trägt sie nur
Befehle der ganzen App (Station wechseln, Projektdatei sichern oder öffnen, Beispielprojekt); das Vis-Werkzeug meldet dort
keinen eigenen Befehl an. Darum ist sie in Visbox eine **UI-Ausnahme** — eine Palette nur mit Visbox-Befehlen wäre eine
eigene, keine gleiche. *Im Projekt:* `kosmovis/UI_AUSNAHMEN.json`; eine Probe wird rot, sobald das Vis-Werkzeug dort
Befehle anmeldet.

**Kugel des Assistenten (Orb)** — Der runde, leicht bewegte Knopf unten rechts in der Knotenansicht. Ein Klick öffnet das
Gesprächsfeld, noch einer schliesst es. Während der Assistent nachdenkt, bewegt sich die Kugel anders und sagt es mit
einem Wort daneben. *Im Projekt:* `KosmoOrb.tsx` und `KosmoEckOrb.tsx`, wortgleich aus KosmoOrbit; dort heisst der
Assistent «Kosmo», in Visbox «Assistent» (Entscheid 116 (2)). Seit dem 22.10.2026 zeigt der Knopf in Visbox
statt der Kugel das **Lot** (Entscheid 133); Ort, Klick und Name sind dieselben.

**Gesprächsfeld (des Assistenten)** — Das Fenster, in dem man dem Assistenten schreibt und seine Antworten liest: oben
der Kopf mit Name, Modell und «Schliessen», in der Mitte der Verlauf und die Karte mit seinem Vorschlag (Anwenden,
Ablehnen, Ändern), unten das Eingabefeld. Fehlt der Heim-PC, steht statt des Eingabefelds ein Satz, warum. *Im Projekt:*
die Optik wortgleich aus KosmoOrbit (`kosmo-panel.css`), der Inhalt ein Stellvertreter (`KosmoPanel.tsx`); das Gespräch
selbst führt die Mac-App, mit denselben Regeln wie ihre frühere Assistent-Leiste.

**Antwortblase (an der Kugel)** — Eine kleine Sprechblase neben der Kugel mit dem Anfang einer Antwort, die kam, während
das Gesprächsfeld zu war. Ein Klick darauf öffnet das Feld; nach zwölf Sekunden verschwindet sie von selbst.

**Seitenfenster (des Gesprächsfelds)** — Auf einem breiten Bildschirm steht das Gesprächsfeld nicht schwebend, sondern
als feste Spalte am rechten Rand, und die Arbeitsfläche rückt zur Seite, statt verdeckt zu werden. Auf einem schmaleren
Bildschirm schwebt es über der Fläche.

**Einstellungs-Insel** — Das Fenster mit allen Einstellungen der Knotenansicht, geöffnet über das Zahnrad oben links
(und über den Heim-PC-Chip gleich bei «Wer rechnet?»). Es enthält Darstellung, Anzeige und Bewegung wie in KosmoOrbit,
dazu was nur Visbox hat: den Heim-PC, «Wer rechnet?», «Claude über MCP», Lizenzen und Neuigkeiten. Adresse und Kennwort
des Heim-PC stehen nicht darin — die bleiben in der Mac-App. *Im Projekt:* `einstellungen.tsx` im Wirt, die Schale aus
`einstellungen-teile.tsx`.

**Gemerkte Einstellung (der Knotenansicht)** — Eine Wahl wie Thema, Farbakzent oder Schriftgrösse, die nach dem Neuladen
noch gilt. Die Webansicht in der Mac-App vergisst alles beim Schliessen; darum sagt die Seite jede solche Wahl der App,
und die App legt sie beim nächsten Öffnen vor dem ersten Bild zurück. Nur eine feste Liste von Einstellungen wird so
gemerkt. *Im Projekt:* `MERKBAR` in `wirt-bruecke.ts`, `Knotenwirt.merkbar` im Kern.

**Metallwert (eines Materials)** — Eine Zahl von 0 bis 1, die sagt, wie sehr eine Fläche wie Metall
wirkt. Metall hat keine eigene Farbe im Licht, es zeigt nur, was es spiegelt; steht nichts zum Spiegeln
herum, wirkt es fast schwarz. *Im Projekt:* Bauteile ohne Material bekamen im 3D-Fenster den Wert 1
(Vorgabe des Dateiformats) und erschienen schwarz; seit dem 20.10.2026 gilt dort höchstens 0,2.

**Umgebungslicht (aus einem Raum)** — Licht, das von allen Seiten kommt, als stünde das Modell in einem
hellen Zimmer: Wände, Decke und Boden geben Helligkeit ab. Anders als eine einzelne Lampe lässt es
keine Seite ganz dunkel. *Im Projekt:* das 3D-Fenster nutzt dafür einen fertigen Raum aus der
Bibliothek three.js, dazu Himmel, Boden und eine Sonne für die Schattierung.

**Normale (Richtung einer Fläche)** — Ein kleiner Pfeil, der senkrecht aus einer Fläche zeigt. Am
Winkel zwischen ihm und dem Licht rechnet das Programm, wie hell die Fläche wird. Fehlt er, sind
alle Flächen gleich hell und das Modell wirkt flach. *Im Projekt:* das 3D-Fenster rechnet fehlende
Normalen beim Laden nach.

**Schnittebene (vorne und hinten)** — Zwei gedachte Wände vor der Kamera: Was näher liegt als die
vordere oder weiter weg als die hintere, wird nicht gezeichnet. Sie sind nötig, damit das Programm
weiss, was vorne und was hinten liegt. Steht die vordere zu weit weg, fehlt beim Heranzoomen der
vordere Teil des Hauses («Clipping»). *Im Projekt:* das 3D-Fenster setzt beide seit dem 20.10.2026 bei
jedem Bild neu, nach dem Abstand zum Modell.

**Entzerren (eines gesicherten Graphen)** — Knoten, die sich überdecken, werden beim Laden so weit nach
unten gerückt, bis sie frei stehen; alles andere bleibt, wo es war. *Im Projekt:* nötig, weil der
Modell-Knoten mit dem 3D-Fenster höher wurde und ältere gesicherte Anordnungen noch mit der alten Höhe
rechneten.

**Mittel in Blendenstufen (geometrisches Mittel)** — Eine Art, Helligkeiten zu mitteln, bei der jede Verdopplung
gleich viel zählt: Eine Fläche, halb so hell wie eine andere, und eine doppelt so helle liegen gleich weit von der
Mitte. Das gewöhnliche Mittel dagegen gehört der hellsten Fläche — ist ein Viertel des Hauses zwanzigmal heller als
der Rest, liegt sein Mittel fast ganz bei diesem Viertel. Das Auge und die Grauwerte eines fertigen Bilds folgen eher
den Stufen. *Im Projekt:* Seit auf-20261020-295 misst die Vorprobe der Stimmung das Haus so
(`stimmung.HAUS_MASS` «stufen»), damit sie dieselbe Grösse steuert, die die Prüfung am Bild als Kontrast misst.
Anlass: Bei «abend» sah die Kamera vor allem die Schattenseite, das gewöhnliche Mittel aber die Sonnenseite — der
Hintergrund blieb zu hell, das Haus verschwamm.

**Haus im KI-Bild nicht wiederzuerkennen** — Der Satz, wenn sich die Fläche des Modells und die Fläche des Hauses im
erzeugten Bild kaum decken (Überdeckung unter 0,1, also weniger als ein Zehntel gemeinsam). Dann zeigt das Bild etwas
anderes als das Haus, etwa den Blick unter ein Vordach. Masse, die nur Farbe und Kanten am Umriss lesen, können dann
trotzdem gut aussehen — sie sehen, dass sich dort etwas ändert, nicht, dass dort das Haus steht. *Im Projekt:* Satz
«HAUS IM KI-BILD NICHT WIEDERZUERKENNEN» in den Hinweisen des Ergebnisses, Grenze `umriss.WIEDERERKENNUNG_GEOM_IOU`
(gesetzt, nicht gemessen), seit auf-20261020-295. Seit auf-20261021-296 steht der Satz auch, wenn das Bild mehr als
doppelt so viel «Haus» zeigt, wie modelliert ist, oder weit über den Umriss baut und sich zugleich wenig mit dem Modell
deckt. Anlass war ein Strassenbild: Dort war das ganze Bild voller Häuser. Ein Teil davon deckte sich darum zufällig
mit dem Modell (0,197), das Haus selbst war aber nicht zu finden (`umriss.wiedererkennung`).

**Umriss-IoU (aus Farbe)** — Ein Mass, das die HomeStation selbst nachrechnet: Es sucht um die Fläche des Modells,
wo sich im erzeugten Bild die Farbe deutlich ändert, und vergleicht die so gefundene Fläche mit der des Modells.
Es misst Farbwechsel, nicht den Baukörper. *Im Projekt:* kein Feld des Ergebnisses; bei «abend voll» in 295 meldete es
0,60, obwohl das Haus nicht zu sehen war — seither gilt es unter der Grenze oben nicht als «gut».

**Drehung je Kamera (des Himmelsbilds)** — Wie weit das Rundumfoto des Himmels für eine bestimmte Kamera gedreht
wurde, damit die Sonne seitlich steht. Zwei Kameras auf gegenüberliegenden Seiten bekommen zwei Drehungen, 180°
auseinander. *Im Projekt:* `angewandt.environment.drehung_je_kamera` im Ergebnis, aus dem Bericht von Blender je
Kamera; seit auf-20261020-295 steht dort dafür kein `rotationGrad` mehr, weil die Vorgabe 0 gar nicht gerechnet wurde.

**Prüfbild (für eine Schwelle)** — Ein Bild, das absichtlich so bestellt wird, dass man vorher weiss, auf welcher
Seite einer Grenze es landen soll — eines, das sicher drinnen bleibt, und eines, das sicher hinausfällt. Erst wenn
die Zahl beide richtig einordnet, ist die Grenze geprüft. *Im Projekt:* für die Grenze 0,25 von
`qa.ausserhalb_umriss_anteil` in auf-20261021-296: ein Gipsmodell mit voller Steuerung (bleibt im Umriss) und ein Bild
mit schwacher Steuerung und einem Strassen-Prompt (bricht aus).


**Flächenverhältnis (Haus im Bild gegen Haus im Modell)** — Wie viele Bildpunkte die Prüfung im erzeugten Bild für
«Haus» hält, geteilt durch die Bildpunkte, die das Modell an dieser Stelle bedeckt. Um 1 heisst: ungefähr so viel Haus,
wie gebaut ist. Über 2 heisst: Das Bild ist voller Gebäude, und das modellierte geht darin unter. *Im Projekt:*
`n_ist ÷ n_soll` am Kameraurteil. Über 2 (`umriss.WIEDERERKENNUNG_FLAECHE_VERHAELTNIS`, gesetzt, nicht gemessen) gilt
das Haus seit auf-20261021-296 als nicht wiederzuerkennen; das Strassenbild dort hatte 2,46.

**Gültigkeitsvermerk der Umrisstreue (`umriss_gilt`)** — Ein Ja/Nein an der Auswahl des Startwerts. Es sagt, ob die
Masse, die nur Kanten und Farbe am Umriss lesen, für dieses Bild etwas über das Haus aussagen. Ja, wenn das Haus
wiederzuerkennen ist; Nein mit Grund, wenn nicht. *Im Projekt:* `seedauswahl.umriss_gilt` am Kameraurteil. Seit
auf-20261021-296 steht es immer, wenn die Überdeckung gemessen ist, auch als «ja»; vorher fehlte das Feld bei «ja», und
ein fehlendes Feld liess offen, ob geprüft wurde.

**Zusatz «leerer Hintergrund» (Messschalter)** — Ein Satz, den der Heim-PC auf Wunsch an die Bildbeschreibung für die
KI hängt: «empty background, no other buildings» (leerer Hintergrund, keine anderen Gebäude). Er soll die KI davon
abhalten, neben das Haus weitere Gebäude zu malen. *Im Projekt:* `vis.leerer_hintergrund: true` in der Bestellung,
Vorgabe aus, `kosmo_szene.ZUSATZ_LEERER_HINTERGRUND`. Vorbereitet, nicht eingebaut, seit auf-20261021-296. Dort blieb nur
das Gipsmodell mit genau diesem Satz im Umriss. Ob es am Satz lag, misst auf-20261021-297 mit und ohne.

**Farbabgleich (nach dem KI-Schritt)** — Die Farben eines erzeugten Bilds werden an ein zweites Bild angeglichen: Die
mittlere Helligkeit und Farbe und wie stark sie schwanken (die Streuung) werden auf die Werte des zweiten Bilds gebracht.
Dabei bewegt sich kein Bildpunkt; jeder Punkt bekommt nur eine neue Farbe, die allein von seiner alten Farbe abhängt.
*Im Projekt:* Schalter `vis.farbabgleich`, Vorgabe aus (Entscheid 117, `aiimaging.farbabgleich`). Das KI-Bild bekommt so
die Farbstimmung des Cycles-Bilds, etwa das warme Abendlicht. Gerechnet für das ganze Bild auf einmal und nicht getrennt
nach Haus, Boden und Himmel, weil das KI-Bild nicht genau auf den Flächen des Modells liegt und getrennte Abgleiche sonst
neue Kanten an den Grenzen schüfen. Gemessen in auf-20261021-298: Er bringt Farbton und Helligkeit der Stimmung und
verschiebt nichts an der Form, aber kein Licht und keine Schatten, und das Bild wird blass. Der Grund: Das Gipsmodell,
an das angeglichen wird, hat von Natur aus wenig Kontrast (weisser Gips), und der Abgleich übernimmt diesen kleinen
Kontrast. Die Untergrenze der Streckung (0,5) bremst das sogar; ohne sie würde es noch blasser.

**Kantenübereinstimmung (`kanten_iou`)** — Eine Zahl von 0 bis 1, die sagt, wie gleich die Kanten zweier Bilder liegen.
Gezählt werden die Bildpunkte, die in beiden Bildern Kante sind, geteilt durch die, die in mindestens einem Bild Kante
sind; 1 heisst: dieselben Kanten am selben Ort. *Im Projekt:* im Vermerk des Farbabgleichs. Sie belegt, dass der
Abgleich nichts an der Form verschoben hat; kleine Abweichungen entstehen nur, wo eine schwache Kante genau an der
Grenze liegt und das Runden auf ganze Farbwerte sie kippt.

**Bildeingang mit Stärke (Cycles-Bild und Tiefe zugleich)** — Die KI bekommt zwei Dinge: die Tiefenkarte, die die Form
festhält, und das gerenderte Bild als Ausgangspunkt. Die Stärke (eine Zahl von 0 bis 1) sagt, wie viel davon die KI neu
malen darf: wenig heisst nah am Rendering mit Licht und Schatten, viel heisst freier wie heute. *Im Projekt:* Schalter
`vis.bildeingang` (Stärke 0,05 bis 1,0), Vorgabe aus, Entscheid 117. Unser Standardmodell nimmt so ein Ausgangsbild von
sich aus nicht an; darum der eigene Start (nächster Eintrag). Gemessen in auf-20261021-298 mit drei Stärken
(0,4 / 0,55 / 0,7): Das gerenderte Bild kommt an, das Haus hält und das Licht kommt voll an, aber das Ergebnis bleibt
das Gipsmodell, und «Sichtbeton» aus der Beschreibung kommt nicht an. Darum misst auf-20261021-300 höhere Stärken
(0,8 / 0,9 / 0,95), bei denen die KI mehr selbst malt. Mit Bildeingang braucht der Lauf rund 3,8 GB mehr Speicher auf
der Grafikkarte; liegt ein fremdes Modell dort, wird er abgewiesen (siehe «Fremdes Modell auf der Grafikkarte»).
*Nachgeführt 22.10.2026:* Seit **Entscheid 138** ist die Stärke **0,5 die Vorgabe für Varianten** — gemessen in 337
(die Giebelfenster bleiben, ohne Bildeingang fielen sie weg) und 339 (Sichtbeton mit Form und Fenstern). `false` schaltet
ab, eine eigene Zahl gewinnt. Nie an einem Modell mit offener Lizenz; reicht die Grafikkarte nicht, wird die Vorgabe
*zurückgezogen* statt den Auftrag abzuweisen (siehe «Zurückgezogene Vorgabe»).

**Eigener Start (beim Bildmodell)** — Ein Bildmodell beginnt sonst mit reinem Rauschen und entfernt es Schritt für Schritt,
bis ein Bild dasteht. Beim eigenen Start beginnt es stattdessen mit dem gerenderten Bild, dem ein Teil Rauschen beigemischt
ist, und rechnet nur noch die letzten Schritte. Je mehr Rauschen, desto mehr malt die KI neu. *Im Projekt:*
`render._eigener_start`, der Weg hinter dem Bildeingang mit Stärke. Unser Code, nach dem Vorbild einer Rechnung aus der
freien Bibliothek diffusers, ohne an ihr etwas zu ändern. Am Heim-PC gemessen (auf-20261021-298): Eine rote Marke im
gerenderten Bild stand danach im KI-Bild. Bei 20 Schritten und Stärke 0,55 rechnet er die letzten 11.

**Spitze und Grundlast (beim Grafikspeicher)** — Die *Spitze* ist der höchste Stand des belegten Speichers auf der
Grafikkarte während eines Laufs; die *Grundlast* ist, was schon vorher belegt war (Bildschirm, Fenster). Was der Lauf
selbst braucht, ist der Unterschied der beiden. *Im Projekt:* am Registereintrag `z-image-turbo` als
`vram_bildeingang_spitze_mib` (31 316 MiB) und `vram_bildeingang_grundlast_mib` (1241 MiB), gemessen in
auf-20261021-298. Der Lauf mit Bildeingang braucht also 30 075 MiB; auf der Karte mit 32 607 MiB bleiben rund 1,3 GB frei.

**Reserve (beim Bildeingang)** — Ein fester Betrag Speicher, der über dem gemessenen Bedarf frei bleiben muss, bevor
ein Lauf startet: hier 512 MiB, gesetzt, nicht gemessen. *Wozu:* Sonst üblich ist ein Aufschlag in Prozent (10 %). Beim
Bildeingang würde er mehr verlangen, als die Karte überhaupt hat, und jeder Lauf würde abgewiesen. Ein fester Betrag
genügt hier, weil die Spitze in allen zehn gemessenen Läufen gleich war. *Im Projekt:* `render.BILDEINGANG_RESERVE_MIB`.

**Fremdes Modell auf der Grafikkarte** — Ein Sprachmodell oder anderes Modell, das ein anderes Programm (meist Ollama)
gerade auf der Grafikkarte hält und das nicht zu unserem Bildlauf gehört. *Wozu der Begriff:* Mit Bildeingang ist die
Karte fast voll; liegt daneben ein fremdes Modell, reicht der Speicher nicht. Modelle anderer Programme entlädt Visbox
nie (Entscheid 106d), darauf zu warten kann beliebig dauern. *Im Projekt:* Mit `vis.bildeingang` fragt der
Abholer vor dem Lauf, was Ollama hält, und weist den Auftrag mit einem Satz ab («ABGEWIESEN: Bildeingang …»), statt zu
laden (`render.pruefe_bildeingang_karte`, seit auf-20261021-298).

**Toleranz (bei einem Vergleich zweier Messwerte)** — Wie weit zwei Zahlen auseinanderliegen dürfen und trotzdem als
gleich gelten. *Wozu:* Eine Zahl, die ein Messgerät oder ein Schätzer zweimal liefert, ist selten aufs letzte Komma gleich.
Ohne Toleranz heisst jede winzige Abweichung «ungleich», und das Feld sagt nichts mehr. *Im Projekt:* beim Farbabgleich
gilt `geom_iou` vor und nach dem Abgleich als gleich bis 0,03 Abweichung (`geom_iou_toleranz`); die Abweichung steht als
Zahl daneben (`geom_iou_abweichung`). Gemessen waren 0,0001 bis 0,023 (auf-20261021-298). Auch beim Vergleich mit einer Grenze: Computer speichern
Kommazahlen oft nur mit rund sieben Stellen; aus 0,05 wird 0,0500000007, streng genommen grösser als 0,05. Bei der Rauheit
von Glas zählt darum erst, was mehr als ein Millionstel darüber liegt (Ergebnis 333, Protokoll 74 §249). Ebenso bei
der Augenhöhe: Die eigene Setzhöhe 1,70 m kam als 1,7000000059604645 zurück und fiel aus dem Band 1,60–1,70 m; seit
Ergebnis 341 gilt das Band mit 0,1 mm Toleranz (`kameras.AUGENHOEHE_TOLERANZ_M`).

**Beide Bilder liefern (Wahl W-4)** — Eine der vier Wahlen aus Entscheid 117: Statt das Licht ins KI-Bild zu mischen,
bekommt der Architekt das gerenderte Bild (mit Licht und Schatten) und das KI-Bild nebeneinander und wählt selbst.
*Im Projekt:* Die Lieferung gibt es schon. Wer das Schönbild als Ebene bestellt (`render.passes ["schoenbild"]`), bekommt
es je Kamera als `<kamera>__schoenbild.png` neben dem KI-Bild. Neu wäre nur, dass der Render-Knoten es von sich aus
bestellt und daneben zeigt.

**CUDA-Kontext** — Der Arbeitsbereich, den ein Programm auf der Grafikkarte anlegt, sobald es zum ersten Mal dort
rechnet. Er belegt Speicher (am Heim-PC rund 500 MB), auch bevor ein Modell geladen ist. *Wozu der Begriff:* Fragt ein
Programm die Karte «wie viel ist frei?», zählt sein eigener Arbeitsbereich schon als belegt. Wer das nicht weiss, hält
den eigenen Speicher für den eines fremden Programms. *Im Projekt:* Genau das wies in auf-20261021-300 jeden Lauf mit
Bildeingang ab. Seither fragen Abholer und Bildmodell dieselbe Stelle, was dem eigenen Programm gehört
(`render.eigener_grafikspeicher_mib`, Rückfall `render.CUDA_KONTEXT_MIB` 504, gemessen).

**Eigenes Assistenzmodell** — Das Sprachmodell, mit dem der Assistent der Visbox antwortet (`qwen3:14b`). Es gehört
Visbox, nicht einem anderen Programm, und ist darum kein fremdes Modell. *Wozu der Begriff:* Liegt es auf der Karte,
während ein Lauf mit Bildeingang bestellt wird, fehlt trotzdem Platz. Der Satz soll dann nicht «fremdes Modell» sagen,
denn Visbox darf dieses Modell selbst entladen. *Im Projekt:* Der Abholer entlädt es vor einem Auftrag mit «nur bei
freier Karte» (`idle_window_only`), wenn gerade keine Frage läuft (Entscheid 106d); sonst nennt die Abweisung es
«eigenes Assistenzmodell» (`render.pruefe_bildeingang_karte`, seit auf-20261021-300). Seit Entscheid 127
(22.10.2026) nimmt der Abholer vor **jedem** Auftrag alle Sprachmodelle von der Karte, dieses eingeschlossen
(**Grafikkarte freigeben (vor dem Bild)**).

**Auslöser (eines Satzes)** — Eine Bedingung an Messzahlen, die einen Hinweissatz ins Ergebnis schreibt. Ein Satz kann
mehrere Auslöser haben, jeder für sich genügt. *Wozu:* So steht im Ergebnis, *warum* der Satz da ist, und eine neue
Bedingung lässt sich dazunehmen, ohne die alten zu ändern. Ein Auslöser ist kein Tor: Er sperrt nichts und ändert kein
«bestanden». *Im Projekt:* «HAUS IM KI-BILD NICHT WIEDERZUERKENNEN» hat vier (`umriss.wiedererkennung`). Der vierte,
seit auf-20261021-299: Das Bild zeigt mehr als 1,2-mal so viel «Haus» wie modelliert UND baut mehr als das 1,5-Fache der
Hausfläche ausserhalb des Umrisses, gemessen an einem Bild mit mindestens 960 Bildpunkten an der langen Seite.

**Augenurteil** — Was ein Mensch beim Betrachten eines Bildes festhält (hier: «Haus ja, teilweise oder nein
wiederzuerkennen»), getrennt von den gemessenen Zahlen. *Wozu:* Eine Schwelle, die ein Rechner anwenden soll, braucht
einen Massstab, an dem sie richtig oder falsch liegt. Das Augenurteil ist dieser Massstab; die Schwelle wird so gelegt,
dass sie es trifft, und heisst danach «gesetzt an einem Augenurteil, nicht gemessen». *Im Projekt:* auf-20261021-299 an
14 KI-Bildern; der vierte Auslöser trennt «teilweise» (bis 1,163) von «nein» (ab 1,274).

**Unteres Quantil (25-%-Quantil)** — Der Wert, unter dem das dunkelste Viertel aller Messpunkte liegt. Bei einem Haus
mit Sonnen- und Schattenseite liegt er auf der Schattenseite, das Mittel dagegen dazwischen. *Im Projekt:* ein
Vorschlag aus auf-20261021-296. Die Vorprobe der Stimmung könnte den Himmel gegen die Schattenseite stellen statt gegen
das Mittel, damit sich bei «abend» auch die dunkle Seite abhebt. Nicht gebaut, weil es mittag und winter verschieben
könnte; erst nachzählen (297).

**Modellwurzel** — Der Ordner, unter dem die Gewichte aller Modelle liegen, jedes in einem eigenen Unterordner. *Wozu:*
Ein Programm muss wissen, wo es sucht; sucht es am falschen Ort, meldet es «Modell fehlt», obwohl es am Rechner liegt.
*Im Projekt:* Gesucht wird in dieser Reihenfolge: die Umgebungsvariable `AIIMAGING_MODELLE`, dann (seit
auf-20261021-301) dieselbe Angabe aus der Dienst-Unit des Abholers, dann `/ai`, dann der Anwendungsordner des
Betriebssystems (`render.modellwurzel`). So findet ein Messprogramm am Heim-PC dieselben Gewichte wie der Abholer.

**Modell-Hub (offline laden)** — Ein Dienst im Internet, von dem Programme Modelle herunterladen (bei uns Hugging Face).
*Offline laden* heisst: nur aus dem eigenen Ordner, nie aus dem Netz. *Wozu:* Ein Programm, das einen Ordner nicht
findet, versucht sonst still den Hub — am Heim-PC ein Fehler statt einer Messung, anderswo ein ungewollter Download.
*Im Projekt:* Der Tiefenschätzer lädt seit auf-20261021-301 nur aus einem vorhandenen Ordner und sagt sonst «nie aus dem
Netz» (`tiefenschaetzer.lade_modell`).
**Umriss halten (Messschalter `vis.umriss_halten`)** — Ausserhalb des modellierten Hauses gilt im fertigen Bild das
Cycles-Bild der Grundlage (Himmel, Boden, Umgebung), innerhalb malt die KI. *Wozu:* Die KI baut fast immer neben das
Haus weitere Gebäude (`ausserhalb_umriss_anteil` rund 2 bei Aussenbildern); ein Satz im Prompt hielt sie nicht davon ab.
Zwei Arten: «nachher» mischt die beiden Bilder nach dem KI-Schritt, «im_lauf» hält den Hintergrund schon während des
Malens fest (siehe *Hintergrund im Fahrplan festhalten*). Vorgabe aus. Gemessen in auf-20261021-303: «im_lauf» hält
den Umriss ohne Naht und kostet keinen Grafikspeicher, verändert allein aber die Form (Rundturm); «nachher» wirkt wie
eine Collage. Seither sagen die Sätze zum Umriss bei «nachher», was am gelieferten Bild gilt (*Urteil nach dem
Halten*). *Im Projekt:* `aiimaging.umrisshalt`, Planblatt `docs/PLAN_MATERIAL_UND_UMRISS_2026-10-21.md`, Messaufträge
auf-20261021-303 und -309. *Nachgeführt 22.10.2026:* Seit Entscheid 126 ist «im_lauf» die Vorgabe für Varianten, seit der
Generalprobe (auf-20261022-327) auch für die Vorschau — siehe *Halbe M2*.

**Anteil freier Zellen (`anteil_frei`)** — Beim «Umriss halten im Lauf» rechnet das Bildmodell nicht mit einzelnen Bildpunkten, sondern mit einem groben Raster aus kleinen Feldern («Zellen», je 8 × 8 Bildpunkte des KI-Bilds). Der Anteil freier Zellen sagt, auf wie viel des Bilds die KI überhaupt malen darf; im Rest bleibt das gerenderte Grundbild stehen. *Wozu:* Ist der Anteil klein, kann ein Prompt nur wenig ändern — Wiese, Hügel oder Bäume ausserhalb des Hauses entstehen dann nicht. *Im Projekt:* `angewandt.umriss_halten.kameras.<kamera>.anteil_frei` im Ergebnis; im Demolauf 0.3.55 waren es 16–19 %, gemessen wird die Wirkung in auf-20261024-353.

**Urteil nach dem Halten** — Bei «Umriss halten nachher» wird ein anderes Bild geliefert als das, an dem die Prüfung
gewählt hat: das KI-Bild, aussen ersetzt durch das gerenderte Bild. Das Prüfurteil bleibt das des KI-Bilds davor; die
Sätze «KI baut über den Umriss» und «Haus nicht wiederzuerkennen» kommen aber vom gelieferten Bild, damit sie nicht
etwas bemängeln, das im Bild gar nicht mehr steht. Die Zahlen von vorher stehen daneben. *Im Projekt:*
`kosmo_szene.urteil_fuer_umrisssaetze`, `abholer.umriss_halten_der_kamera` (`urteil_nachher`), seit 21.10.2026.

**Freigabemaske** — Ein Schwarz-Weiss-Bild: weiss, wo die KI malen darf, schwarz, wo das Grundbild bleibt. Sie ist die
Bauwerksmaske plus ein schmaler Rand (2 % der langen Bildseite), damit Dachkanten, die die KI ein paar Bildpunkte
verschiebt, nicht abgeschnitten werden. *Im Projekt:* `umrisshalt.schreibe_freigabe_png`, je Kamera unter
`_umriss_halten/<kamera>__freigabe.png`.

**Stimmung der Variante (eigene Grundlage)** — Trägt eine Variante im Prompt den Satz einer anderen Stimmung als das
Licht, mit dem ihre Grundlage gerechnet ist (etwa «Mittag» auf einem Abend-Grundbild), rechnet Visbox für sie eine
eigene Grundlage mit dem Himmelsbild dieser Stimmung, statt auf der alten zu malen. *Wozu:* «Umriss halten» übernimmt
Himmel und Boden des Grundbilds; auf dem Abend-Grundbild wurde die Variante «Mittag» im Mac-Demolauf vom 22.10.2026 zur
blauen Nacht. Es kostet einen Blender-Lauf mehr (länger als eine Variante). **Seit dem 22.10.2026 abends (Befund 340)**
gilt dasselbe, wenn das *bestellte Licht selbst* ein anderes ist als das der Grundlage (der Mac bestellte «Licht abend»
auf einem Mittag-Grundbild und bekam bis dahin eine Absage «Stimmung weicht ab»), und bei einer Variante genügt im Prompt
das *Stimmungswort* statt des ganzen Satzes. Modell und Kamera bleiben dieselben. *Im Projekt:*
`kosmo_szene.stimmung_der_variante` und `kosmo_szene.licht_der_variante`, im Ergebnis `angewandt.variante.stimmung` und
der Satz «STIMMUNG DER VARIANTE» in `qa.verdict.hinweise`; Protokoll 74 §247 und §258.

**Stimmungswort (im Prompt)** — Ein einzelnes Wort, an dem man eine Lichtstimmung erkennt, etwa «Abendstimmung»,
«evening», «Nebel» oder «snow», im Gegensatz zum ganzen Satz, den der Stimmung-Knoten in den Prompt legt («Abendstimmung,
warmes Licht, leuchtende Fenster»). *Wozu:* Wer eine Variante von Hand schreibt, tippt selten den ganzen Satz; Visbox
erkennt die gemeinte Stimmung trotzdem und rechnet für sie ein eigenes Grundbild. Gesucht wird nur nach ganzen Wörtern
(«afternoon» ist nicht «noon», «Nachmittag» nicht «Mittag»), englisch nach der Übersetzung durch das Glossar und deutsch
im Wortlaut; stehen zwei Stimmungen da, wird nicht geraten. Nur bei einer Variante mit bestelltem Licht, nicht bei einer frischen
Bestellung und nicht, wenn gar kein Licht bestellt ist («overcast sky» bleibt dann ein Wort im Prompt).
*Im Projekt:* `stimmung.STIMMUNGSWOERTER`, `stimmung.stimmungen_im_text`; Protokoll 74 §258.

**Lichtsaum (um das Haus)** — Ein heller Rand, der im KI-Bild das Haus umgibt, wie ein Heiligenschein. Vermutete
Herkunft: Im schmalen Band der *Freigabemaske* um das Haus malt die KI ihren eigenen, helleren Himmel, ausserhalb steht
das abgedunkelte Grundbild. Beobachtet im Mac-Demolauf vom 22.10.2026 beim KI-Bild ohne Variantenweg, nicht in der
Variante; eingeordnet, nicht behoben — gemessen wird er in auf-20261022-333 (Schritt 6).

**Fahrplan (der Rauschstufen)** — Die Folge von Stufen, über die ein Bildmodell aus reinem Rauschen ein Bild macht:
Stufe 1 heisst «nur Rauschen», Stufe 0 «fertiges Bild», dazwischen ein Gemisch. Jeder Diffusionsschritt geht eine Stufe
weiter. Die Zahl einer Stufe heisst in der Fachsprache *Sigma*. *Im Projekt:* Der eigene Start (Bildeingang) beginnt
mitten im Fahrplan; das Umriss-Halten «im_lauf» setzt nach jedem Schritt den Hintergrund auf die passende Stufe.

**Hintergrund im Fahrplan festhalten (blended latent diffusion)** — Nach jedem Schritt wird das halbfertige Bild
ausserhalb der Freigabemaske durch das Grundbild ersetzt, und zwar so verrauscht, wie es auf dieser Stufe des Fahrplans
sein müsste. Im letzten Schritt steht dort das Grundbild selbst. *Wozu:* Das Modell sieht in jedem Schritt, was neben dem
Haus steht, und malt die Kante dazu passend — anders als beim nachträglichen Mischen, wo es davon nichts weiss.
Gerechnet wird im latenten Raum (der komprimierten Form des Bildes). *Im Projekt:* `umrisshalt.halte_latenten`,
angewandt im Rückruf je Schritt (`render._umriss_halten_rueckruf`).

**Material vorne (Messschalter `vis.material_vorne`)** — Der Hauptstoff des Entwurfs (etwa «exposed concrete») kommt an
den **Anfang** der Bildbeschreibung, und im ganzen Text steht er **höchstens dreimal** (*Nennung eines Stoffs*):
Nennt der Prompt ihn schon, wird der Satz vorne kürzer, und der Satz des Material-Knotens hinten fällt weg. *Wozu:* Mit
«Sichtbeton» an zweiter Stelle malte die KI Sichtbeton nur teilweise, dazwischen Holz und Stein; vorne gestellt malte sie
ihn ganz (auf-20261021-303). Der Stoff kommt aus dem Material-Knoten, sonst aus dem Prompt; der Satz nennt kein Bauteil.
*Im Projekt:* `kosmo_szene.material_vorne_satz`, Vorgabe aus. **Nachgeführt (Befund 337, 22.10.2026):** Ist eine Materialwahl
bestellt, gewinnt sie — eine Variante «Fassade aus Sichtbeton» auf einer Grundlage mit Holzlattung begann darum mit «spruce
timber battens». Seither ersetzt der Wunsch einer Variante zuerst die Materialwahl der Fassade (*Stoff-Variante*), und
vorne steht dann der Wunschstoff.

**Stoff-Variante (Material der Variante)** — Eine Variante, die nicht Licht oder Stimmung ändert, sondern den **Stoff der
Fassade**: «dasselbe Haus, aber in Sichtbeton». Dafür genügt es nicht, das Wort in die Bildbeschreibung zu schreiben — das
gerenderte Grundbild trägt den alten Stoff schon als Bild, und die gewählte Fassade stünde vorne im Text. Darum wird die
Materialwahl der Fassade durch den Wunschstoff ersetzt und das Grundbild **neu gerechnet** (wie bei einer anderen
Stimmung); Dach, Fenster, Boden und Gelände bleiben. Für Glas und Metall gibt es kein Material in der Bibliothek — dort
folgt nur die Bildbeschreibung, das Grundbild bleibt. *Im Projekt:* `kosmo_szene.material_der_variante`, im Ergebnis
`angewandt.variante.material_wunsch` mit `ersetzung` «materialwahl» oder «nur_prompt»; Anlass Ergebnis 337, gemessen in
Auftrag 339.

**Stofffamilie** — Die Gruppe, zu der ein Material gehört: Beton, Holz, Backstein, Stein, Putz, Lehm, Glas, Metall.
«Sichtbeton schalungsglatt» und «Sichtbeton sandgestrahlt» sind dieselbe Familie, «Holzlattung» und «Dreischichtplatte»
auch. *Wozu:* Wünscht eine Variante «Holz» und gewählt ist schon die Holzlattung, ist der Wunsch erfüllt — nichts wird
ersetzt und kein Grundbild neu gerechnet. *Im Projekt:* `materialwahl.FAMILIE`, die Wortliste `materialwahl.STOFF_WUNSCH`.

**Fassadenwort und Nicht-Wand-Wort (beim Stoffwunsch)** — Woran erkannt wird, ob ein Stoff im Text die Fassade meint:
«facade of exposed concrete» ja, «wood window» oder «zinc roof» nein — dort gehört der Stoff dem Fenster bzw. dem Dach.
Zweideutige Wörter («render» heisst auch «ein Rendering», «glass» meist die Fenster) zählen nur mit einem Fassadenwort
daneben. *Im Projekt:* `materialwahl.stoff_wunsch`, `WORTE_FASSADE`, `WORTE_NICHT_WAND`.

**Nennung eines Stoffs** — Wie oft eine Bildbeschreibung denselben Baustoff nennt, gezählt an seinem Hauptwort:
«exposed concrete» und «smooth fair-faced concrete» sind beide Beton, «red brick masonry» ist einmal Backstein. *Wozu:*
In einer Messung stand der Stoff fünfmal im Text, ohne dass der Architekt das wollte — jetzt höchstens dreimal. *Im
Projekt:* `kosmo_szene.stoff_nennungen`, `MATERIAL_VORNE_HOECHSTENS`.

**Gewichtung im Prompt** — Bei manchen Bildmodellen lässt sich einem Wort mehr Gewicht geben, etwa mit
`(concrete:1.4)`. Das geht nur, wenn das Programm diese Schreibweise kennt und das Modell die Wörter einzeln liest. *Im
Projekt:* Z-Image liest den Prompt mit einem Sprachmodell, und die Pipeline kennt die Klammern nicht — sie stünden als
Text da. Was wirkt, sind Stellung und Wiederholung (darum *Material vorne*).

**Kantenbild (Canny, HED)** — Ein Steuerbild aus Linien statt aus Tiefe: Canny findet harte Helligkeitssprünge, HED
weichere, eher gezeichnete Linien. Eine ControlNet-Union kann ein solches Bild statt der Tiefenkarte lesen. *Im
Projekt:* geprüft, nicht gebaut — die Z-Image-Pipeline nimmt nur **ein** Steuerbild je Lauf; Kanten zusätzlich zur Tiefe
bräuchten einen eigenen Nachbau der Mehrfach-Steuerung.

**Mehrfach-Steuerung (MultiControlNet)** — Zwei oder mehr Steuerbilder zugleich (zum Beispiel Tiefe und Kanten): Jedes
geht durch das ControlNet, und die Hinweise werden addiert. *Im Projekt:* für Z-Image in diffusers nicht vorhanden
(gelesen 0.39.0 und 0.42.0.dev0); Option b im Planblatt «Material und Umriss».

**Steuerstärke je Schritt (`control_guidance_start`/`_end`)** — Die Steuerung wirkt nur in einem Teil des Fahrplans,
etwa in den ersten 60 % der Schritte. Früh entscheidet das Modell die Form, spät die Oberfläche; wer die Steuerung früher
enden lässt, bekommt mehr Textur, aber einen lockereren Umriss. *Im Projekt:* an der Z-Image-Pipeline nicht vorhanden;
nachbaubar über einen Haken am ControlNet, zurückgestellt (Planblatt, Option c).

**Ohne Gradienten rechnen (`torch.no_grad`)** — Eine Anweisung an torch, sich für eine Rechnung **keinen Rechenweg**
(Graphen) zu merken. Den bräuchte man nur zum Trainieren; beim Erzeugen eines Bildes hält er bloss Zwischenergebnisse im
Grafikspeicher fest. *Im Projekt:* Die Pipeline von diffusers rechnet so; was ausserhalb davon gerechnet wird, muss es
selbst sagen. Das Umriss-Halten «im_lauf» tat es und brauchte keinen Speicher mehr (auf-20261021-303); seit 21.10.2026
tut es auch der eigene Start des Bildeingangs, dem dort +3,9 GB anhingen — nachgemessen in auf-20261021-309.

**Satz der Stimmung (massgebend)** — Der englische Satz, den der Heim-PC für eine bestellte Stimmung an die
Bildbeschreibung hängt, etwa «evening mood, warm low sunlight, long raking shadows, golden hour» für «Abend». *Wozu:* Der
Stimmungs-Knoten schrieb seinen deutschen Satz selbst in die Beschreibung; halb übersetzt («leuchtende window») hielt er
den Satz des Heim-PC zurück, und das Bild zeigte einen Innenraum. Jetzt gilt immer der Satz des Heim-PC, genau einmal;
der Satz des Knotens wird herausgenommen, und die deutschen Sätze der acht Stimmungen werden als ganze Wendung
übersetzt (*Halbe Übersetzung*). *Im Projekt:* `stimmung.ohne_stimmungssaetze`, `sprache._stimmungssaetze`, Befund B2
aus auf-20261021-306.

**Halbe Übersetzung** — Eine Bildbeschreibung, in der nach dem Übersetzen deutsche und englische Wörter gemischt
stehen («fog, gedämpftes light, Tiefe in the haze»). Für das Bildmodell ist das schlechter als jede ganze Sprache. *Im
Projekt:* `sprache.uebersetze` meldet die übrig gebliebenen Wörter unter `unbekannt`; ganze Wendungen im Glossar
verhindern sie.

**Unvollständiger Gewichtsordner** — Ein Ordner, in dem die Gewichte eines Modells liegen sollten, der aber leer ist oder
dem die Beschreibungsdatei (`config.json`) oder die Gewichtsdatei fehlt. *Wozu:* Das Ladeprogramm meldete dann «unbekanntes
Modell», als wäre das falsche Modell gewählt; jetzt heisst es «Ordner leer oder unvollständig». *Im Projekt:*
`tiefenschaetzer.ordner_unvollstaendig`, Befund B1 aus auf-20261021-302.

**Grundbild (Grundbild mit Licht)** — Das Bild, das Blender aus dem Modell rechnet, bevor die KI etwas dazutut: Form,
Sonne und Schatten sind echt gerechnet, Oberflächen nur so, wie sie modelliert sind. In den Unterlagen heisst es auch
«Cycles-Bild» oder, als Datei, «Schönbild» (`<kamera>__schoenbild.png`). *Wozu:* Das KI-Bild ist ein Entwurf und nimmt
das Licht nicht verlässlich mit (Messungen 298 und 300); daneben zeigt das Grundbild, wie Licht und Schatten wirklich
fallen. *Im Projekt:* Entscheid 117a (W-4): Der Render-Knoten bestellt es bei jedem KI-Bild mit; ein Klick auf das Bild
zeigt KI-Bild und Grundbild gross nebeneinander, umschaltbar «nebeneinander · nur KI · nur Grundbild». Seit Entscheid 119
ist der Render-Knoten breiter, und beide Bilder stehen schon am Knoten nebeneinander; vorher stand dort nur das KI-Bild
mit der Beschriftung «KI-Bild · + Grundbild», weil zwei Bilder unter 96 px geschrumpft wären.

**Innenbreite (eines Knotens)** — Wie breit der Inhalt einer Knotenkarte ist: die Karte ohne den schmalen Rand links
und rechts (je 8 Bildpunkte). *Wozu:* Was in den Knoten passt — zwei Bilder nebeneinander, ein Knopf neben dem anderen —,
hängt an dieser Zahl. *Im Projekt:* Die meisten Knoten sind 200 Bildpunkte breit, innen 184; der Render-Knoten seit
Entscheid 119 212, innen 196, damit KI-Bild und Grundbild je 96 Bildpunkte bekommen. Das Programm fragt die Breite je
Knotenart ab (`nodeBreite`), damit Verbindungen, Platzsuche und Anordnung mit der richtigen Kante rechnen.


---

**Gesicherter Blick** — Ein Standpunkt, den jemand bewusst festgehalten hat: wo das Auge steht, wohin es schaut und
wie weit das Bild reicht (Bildwinkel). *Wozu:* Ein gewählter Blick — etwa der Fussgänger an einer Hausecke — soll für
alle Varianten derselbe bleiben; nur die Stimmung ändert sich. *Im Projekt:* Der Knoten «Kamera» bietet die gesicherten
Blicke im Reiter «Blick» als Auswahl an, ohne dass eine 3D-Ansicht offen sein muss. In Visbox sind das die Standpunkte, die
für ein Bild der Mappe am Grundriss gesetzt wurden (auch der eines Bildes unter einer Skizze vom iPad). Beim Wählen wird
der Blick **festgehalten**: Wird er später verschoben oder gelöscht, bleibt die Kamera, wie sie war, und der Knoten sagt es.
Der Name des Blicks steht im Kopf des Knotens. Festgehalten wird der Blick an seiner **Kennung**, nicht am Namen: Ein
umbenannter Blick bleibt derselbe, und zwei Blicke dürfen gleich heissen.

**Bildzeile mit Blättern** — Eine Zeile in einem Knoten, die **ein** Daumenbild zeigt und daneben zwei Pfeile, mit
denen man zum vorherigen oder nächsten Bild wechselt, dazu «2 von 6». Sie ist in jedem Zustand gleich hoch — leer,
wartend, fehlgeschlagen oder fertig —, damit der Knoten nicht springt. *Im Projekt:* der Varianten-Knoten zeigt so die
Bilder seiner Bestellung (Blatt 36); zwei Bilder nebeneinander hätten die Mindestgrösse von 96 Bildpunkten unterschritten.

**Gewählte Variante** — Das eine Bild einer Varianten-Bestellung, das der Architekt mit «Diese Variante wählen»
markiert. Die Wahl steht im Projekt (ein Schritt, den «Rückgängig» zurücknimmt) und gilt dem gesehenen Bild, nicht nur
der Kombination aus Standpunkt und Stimmung: Eine neue Bestellung hebt sie darum auf. *Im Projekt:* ein blauer Ring und
ein Haken am Daumenbild; der Stand, den Claude und der Assistent lesen, nennt sie.

**Portal (in der Oberfläche)** — Ein Weg, ein Fenster der Oberfläche an einer anderen Stelle der Seite anzuzeigen, als
es im Programm steht — meist ganz oben über allem. Nötig, wenn das Fenster sonst in einer verschobenen oder vergrösserten
Fläche sässe und mit ihr wanderte. *Im Projekt:* die grosse Ansicht eines Varianten-Bildes und die des Rasters im
Bildvergleich liegen so über der Knotenansicht; vorher lag die des Rasters beim Zoomen ausserhalb des Fensters.

**Verschachtelte Stilregel** — Eine Regel des Stilblatts (wie etwas aussieht), die **in** einer anderen steht und dann
nur innerhalb von deren Elementen gilt. Fehlt in einer Regel die schliessende Klammer, werden alle folgenden Regeln
ungewollt zu solchen Unterregeln und greifen nirgends — ohne Fehlermeldung. *Im Projekt:* so fiel am 21.10.2026 ein
ganzer Teil des Aussehens der Knotenansicht aus (Zeile «Grundlage», Marke «Vorschau», die neuen Daumen); eine Probe
zählt seither die Klammern des gebauten Stilblatts (`tests/test_varianten_daumen.py`).

**Hausanteil (an Grundlage und KI-Bild)** — Wieviel der Bildfläche das Haus füllt, als Prozentzahl — **zweimal**
gemessen: an der Grundlage (dem Bild aus dem 3D-Modell, dort gezählt Punkt für Punkt) und am KI-Bild (dort geschätzt
aus der Tiefe, die ein Programm im Bild liest: was so nah ist wie das Haus und daran hängt). *Wozu:* Die KI wählt den
Ausschnitt manchmal selbst — «näher» oder «weiter» als bestellt. Dann füllt das Haus in der Grundlage 3 % und im KI-Bild
17 %, und eine einzige Zahl spräche über ein Bild, das man nicht sieht. *Im Projekt:* seit dem 21.10.2026 im Ergebnis
jedes Bildes und in der grossen Ansicht des Verlaufs als Zeile «Haus im Bild», mit dem Satz «KI-BILD RAHMT ANDERS» und
der Marke «Ausschnitt anders», wenn eine Zahl mindestens doppelt so gross ist wie die andere (gesetzt, nicht gemessen). Seit
Auftrag 312: An der Grundlage zählt nur das Haus, ohne Geländeplatte und ohne Bestand; am KI-Bild wird «stetig gewachsen».

**Abgeschnittener Wert (Geometrie 0.0)** — Eine Zahl, die nicht unter eine Grenze fallen darf und darum dort festgehalten
wird, auch wenn die Rechnung weniger ergäbe. *Im Projekt:* Die Geometrie-Zahl vergleicht, ob das KI-Bild die Tiefe gleich
ordnet wie das Modell (vorne und hinten). Ordnet es sie umgekehrt, wäre die Rechnung negativ; die Zahl bleibt dann bei
**0.0**. Eine 0.0 heisst also «das KI-Bild weicht von der Geometrie ab», nicht «nichts gemessen» und kein Fehler. So steht
es seit dem 21.10.2026 auch im Satz der Prüfung.

**Grossansicht (eines Bildes)** — Das fertige Bild über der ganzen Arbeitsfläche, so gross, wie das Fenster erlaubt.
Die Prüfwerte liegen eingeklappt daneben; ein Knopf legt sie über den Bildrand, ohne dem Bild Breite zu nehmen. *Im
Projekt:* ein Klick auf das Bild am Render-Knoten oder auf ein Daumenbild des Verlaufs; das Bild nimmt mindestens 70 % der
Ansicht (Video-Befund L4-14).

**Läufe einer Grundlage** — Alle Bilder, die das Bildmodell auf **demselben** Blender-Bild gerechnet hat, nur mit anderem
Startwert oder Auftrag. Sie sind deckungsgleich und lassen sich darum nebeneinander vergleichen. *Im Projekt:* der Verlauf
am Render-Knoten ordnet seine Daumen danach, ein Strich trennt zwei Grundlagen; die Grossansicht zeigt sie «nebeneinander».

**Modellstand (einer Grundlage)** — Ein kurzer Fingerabdruck des Gebäudemodells: Ändert sich eine Wand, ein Fenster oder
ein Dach, ändert sich der Fingerabdruck. Die Grundlage am Render-Knoten merkt sich, mit welchem Modellstand sie gerechnet
wurde; passt er nicht mehr, heisst sie «veraltet», und Varianten warten auf eine neue. *Im Projekt:* Bilder, die in die
Projektdatei gesichert werden, und Blätter gehören seit dem 21.10.2026 nicht mehr dazu — vorher machte schon das Sichern
des ersten Bildes seine eigene Grundlage veraltet.

**Kontextmaske** — Eine Liste mit einem Ja/Nein je Bildpunkt: *hier steht die Umgebung* — Nachbarbauten (Bestand), Bäume
und Strassenmöbel (Umfeld) oder eine Aufnahme der Umgebung (Splat). Sie entsteht aus demselben Bild wie die
Bauwerksmaske. Seit dem 21.10.2026 fällt der Bestand aus der Bauwerksmaske heraus und steht nur hier (er machte in einer
Messung 36 % der Bauwerksmaske aus, und die Prüfung lobte das Bild für den Nachbarn). *Im Projekt:* am Heim-PC je Kamera
als Datei neben dem Bild, bei «Grundlage rendern» wie bei einer Variante; sie soll später dem Bildmodell sagen, wo der
Kontext steht (Video-Befund L4-5).

**Originalauflösung** — Ein Bild so gross, wie es gerechnet wurde, Bildpunkt für Bildpunkt — nicht das, was der
Bildschirm gerade davon zeigt. Ein Ausschnitt vom Bildschirm hat oft nur einen Bruchteil der Bildpunkte; hochgezogen auf
ein grosses Blatt wird er unscharf. *Im Projekt:* «Exportieren» in der grossen Ansicht eines Laufs gibt immer das
Original heraus; im Demolauf vom 16.10.2026 kam ein Bildschirmausschnitt von 369 × 228 Bildpunkten auf ein A0-Blatt.

**Bild im Projekt gesichert** — Ein fertiges Bild, das nicht nur am Heim-PC liegt, sondern in der Projektdatei selbst,
in Originalauflösung und mit der Angabe, aus welchem Lauf es stammt. So bleibt es, auch wenn der Heim-PC aus ist, und es
kommt nur einmal hinein, auch wenn man es mehrmals verwendet. Das Sichern ist kein Handgriff des Architekten: «Rückgängig»
nimmt es nicht zurück. *Im Projekt:* die Knotenansicht tut es beim Fertigwerden jedes Laufs, auch für ältere Läufe im
Verlauf, wo es ein Blatt gibt, auf das das Bild kommt; Bilder über 5 MB bleiben am Heim-PC, weil der Abgleich so grosse
Teile nicht trägt. Visbox hat kein Blatt — dort liegen fertige Bilder in der Mappe (`bilder/`), und es zählt «Exportieren».

**Druckprüfung am Platz** — Die Rechnung, ob ein Bild für den Druck fein genug ist, **dort, wo es auf dem Blatt steht**:
Bildpunkte geteilt durch die Breite des Felds in Zoll ergibt die → dpi. Unter 150 dpi warnt eine Meldung und nennt die
grösste Breite, bei der es noch reicht; gesperrt wird nichts. Hat das Feld ein festes Seitenverhältnis, zählt die knappere
Richtung. *Im Projekt:* ein Bild von 1600 Bildpunkten Breite reicht auf 160 mm (254 dpi), auf 800 mm nicht (51 dpi).

**Sichern-Dialog** — Das Fenster des Betriebssystems, in dem man Ort und Namen einer Datei wählt, bevor sie gespeichert
wird. Eine eingebettete Webseite kann es nicht selbst öffnen; das Programm drumherum muss es tun. *Im Projekt:*
«Exportieren» in der grossen Ansicht eines Laufs; die Mac-App fängt das Herunterladen der Knotenansicht ab und zeigt den
Dialog mit einem bereinigten Namen (`Sichername.swift`).

**Gebäudewort (im Prompt)** — Die zwei Wörter «architectural building», die der Heim-PC vor die Bildbeschreibung setzt,
wenn sonst nur der Satz der Stimmung übrig wäre. *Wozu:* Das Bildmodell weiss sonst nicht, dass ein Gebäude gemeint ist —
bei «Abendstimmung, warmes Licht» malte es eine Höhle. *Im Projekt:* seit dem 21.10.2026, nur bei leerer Beschreibung;
was der Architekt selbst schreibt, bleibt Wort für Wort.

**Kartenkennung** — Die Nummer eines Vorschlags der KI, etwa «A-1» (Assistent) oder «K-12» (Claude). *Wozu:* Der
Architekt wendet die Karte an oder lehnt sie ab; erst danach gibt es den Knoten, den sie vorschlägt. *Im Projekt:* Eine
Kartenkennung ist **keine** Kennung eines Knotens — seit dem 21.10.2026 weist der Heim-PC einen Aufruf ab, der damit
etwas verbinden will, und sagt warum.

**Anstoss (an den Assistenten)** — Ein Satz, den der Heim-PC dem Sprachmodell einmal nachschickt, wenn um ein Bild
gebeten wurde und es kein Werkzeug gerufen hat. *Wozu:* Das Modell verwechselte «Rechne das Bild» mit «Gib die
Grafikkarte frei» und tat nichts. Der Anstoss erinnert: einen Render-Auftrag als Karte vorschlagen ist erlaubt,
freigeben nicht. Erfinden darf es dabei weiterhin nichts.

**«Himmel» am Render-Knoten (Himmelsmodell, `render.himmel`)** — Eine Auswahlzeile am Render-Knoten mit vier Arten, wie
Blender einen Himmel *ausrechnen* kann (zum Beispiel PREETHAM), statt ein Foto zu nehmen; leer heisst sie «keiner». Das Feld
wird seit dem 29.09.2026 nicht mehr an den Heim-PC geschickt, weil er es nicht annimmt — die Zeile wirkt also nicht. Nicht
zu verwechseln mit dem *Himmelsbild* der Stimmung und mit *Himmel sichtbar*: Steht dort «keiner», kann der Himmel im Bild
trotzdem zu sehen sein (Generalprobe 327, S3). *Im Projekt:* `NodeCanvas.tsx` (Zeile `bedienung-himmel`), `NICHT_GESENDET`
in `vis-jobs.ts`; Umbenennen oder Ausblenden nach der Demo.

**Mappenwechsel (in der Knotenansicht)** — Was geschieht, wenn nach «Datei laden …» eine *andere* Mappe die offene wird:
Die Knotenansicht nimmt die Knoten der vorigen Mappe heraus und legt die gesicherten der neuen — oder, wenn die neue noch
keine hat, den *fertigen Anfang*. Eine neue Fassung in derselben Mappe ist kein Wechsel; die Knoten bleiben. Bis zum
22.10.2026 kam der neue Stand erst nach dem Neuladen der Seite. *Im Projekt:* `graphDerNeuenMappe` in
`kosmovis/apps/visbox-knoten/src/graph-sichern.ts`, ausgelöst von `verfolge` in `mappe.ts`.

**Variante auf der Grundlage (am Varianten-Knoten)** — Der Varianten-Knoten bestellt mehrere Bilder auf einmal (Stimmungen,
Standpunkte, Entwürfe). Liegt am Render-Knoten schon eine *Grundlage* — das Bild aus Blender mit Tiefe und Materialkarte —
für genau dieselbe Lage (gleiches Modell, gleiche Kameras, gleiche Stimmung, gleiches Material, gleiches Format), nimmt er
sie mit, statt sie am Heim-PC neu rechnen zu lassen, und rechnet mit ihrem **einen** Startwert (dem Zufallswert, mit dem das
KI-Bild beginnt). Ändert sich etwas davon — etwa das Material für eine Variante B —, entsteht eine eigene Grundlage wie
bisher. Bis zum 22.10.2026 rechnete jede Bestellung ihre eigene Grundlage und wählte aus drei Startwerten (Gegenprobe 328,
S6/S7). *Im Projekt:* `sendeGraphRenderAuftrag` in `kosmovis/apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`.

**Nicht entscheidbar je Kamera (`not_applicable`)** — Das Wort, mit dem Visbox je Kamera sagt: gemessen wurde, aber die
Messung trägt hier kein Urteil — etwa weil das Haus weniger als 20 % des Bildes füllt. Der Wert «bestanden: nein» bleibt
dabei stehen, weil die Gegenseite dort nur Ja oder Nein kennt; erst das Wort sagt, dass «nein» hier nicht «durchgefallen»
heisst. Fehlte es, zeigten Bildvergleich und Kuratieren «durchgefallen» (Gegenprobe 328, S8). *Im Projekt:* `_qa_je_kamera`
in `src/aiimaging/kosmo_szene.py`.

**Dateistamm (beim Exportieren)** — Der Anfang des Dateinamens, den «Exportieren» vorschlägt. In Visbox ist es die Mappe
(«gegenprobe-Lauf-2-sSE.png»), bei einer Variante dazu Bestellung und Stimmung («gegenprobe-Varianten-2-Abendstimmung-sSE.png»);
der Schluss («sSE») ist die Kamera. Vorher stand «Unbenannt» davor, der Name des Dokuments, den Visbox nie setzt.
*Im Projekt:* `exportName` und `registriereExportStamm` in `bild-ablage.ts`, gemeldet von `main.tsx` der Knotenansicht.

**Taktgeber (des Abholers)** — Die Uhr am Heim-PC, die den Abholer — das Programm, das freigegebene Bilder abholt und
rechnet — immer wieder startet. Er läuft nicht dauernd, sondern einmal je Takt: Nach jedem Durchgang wartet er, dann
schaut er wieder nach. Seit dem 22.10.2026 sind es 10 statt 30 Sekunden, weil nach «Freigeben» bis zu 30 Sekunden
nichts geschah (Ergebnis 329). *Im Projekt:* `betrieb/kosmo-abholer.timer`; am Heim-PC eingerichtet nach `betrieb/README.md`.

**Wahl aus drei Startwerten (Startwertauswahl)** — Rechnet der Heim-PC ein fertiges Bild ohne vorgegebenen Startwert,
malt das Bildmodell es dreimal, jedes Mal von einem anderen Zufallsrauschen aus, und behält das Bild, dessen Umriss am besten
zum Modell passt. Das kostet Zeit (in 330 rund 100 statt rund 45 Sekunden je Bild, zusammen mit der neuen Grundlage), fängt
aber Ausreisser ab: In der Messung 309 lag ein einzelner Wurf bis hinunter bei 0,38 Umrisstreue, die Wahl aus drei im Mittel
rund 0,1 über einem einzelnen. Rechnet eine Variante auf einer vorhandenen Grundlage, nimmt sie deren einen Startwert — dann
gibt es keine Wahl. *Im Projekt:* `abholer.seeds_der_kamera` (Vorgabe `VORGABE_SEEDS`), Protokoll 74 §233.

**Nachgeeichte Schätzung** — Eine Zahl, die nicht aus einem Modell der Rechnung folgt, sondern aus Messungen so eingestellt
ist, dass die Schätzung die gemessene Dauer trifft. Am Varianten-Knoten sind es 9 Sekunden je Bild für die Wahl aus drei
Startwerten: Cycles-Schätzung und KI-Schritt ergaben 91 Sekunden je Bild, gemessen waren im Mittel rund 100 (328 und 330).
Eine nachgeeichte Zahl gilt nur für die Lage, an der sie gemessen ist; sie steht darum mit ihren Messungen im Code. *Im
Projekt:* `STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME` in `kosmovis/apps/kosmo-orbit/src/modules/vis/varianten.ts`.

**Eingang (eines Knotens, z. B. «Bild 1/2/3» am Bildvergleich)** — Die Anschlussstelle links an einem Knoten, an die eine
Verbindung von einem anderen Knoten gezogen wird; ihr Name steht daneben. Der Bildvergleich hat drei solche Eingänge, weil er
bis zu drei Bilder nebeneinander zeigt. Hängt dort der Varianten-Knoten, zeigt er stattdessen dessen Raster, und die übrigen
Eingänge bleiben leer — die Namen «Bild 2» und «Bild 3» sind dann keine Spalten, sondern freie Anschlüsse (Gegenprobe 330).
*Im Projekt:* Knotentyp `vergleich` in `kosmovis/packages/kosmo-kernel/src/derive/visgraph.ts`.

**Brücke (Bestellweg am Heim-PC, `/bruecke`)** — Die Adresse am Heim-PC, über die ein Bild bestellt, freigegeben und
abgeholt wird. Die Knotenansicht bestellt über sie, aber auch jedes andere Programm kann es (die HomeStation tut das für
Messungen). Was ein anderes Programm bestellt, sieht die Knotenansicht nicht: Bildvergleich und Kuratieren zeigen nur, was
in *dieser* Seite bestellt wurde (Generalprobe 327, S8). *Im Projekt:* `oberflaeche/server.py` (Wege unter `/bruecke`),
`vis-jobs.ts` (`postRenderJob`).

**Himmel sichtbar (Messschalter `vis.himmel_sichtbar`)** — Die Kamera sieht im Bild aus Blender das Himmelsbild der
Stimmung statt eines ruhigen Farbverlaufs. *Wozu:* Hält die KI den Hintergrund fest («Umriss halten im Lauf»), sieht das
Bild sonst wie ein Modellfoto vor flachem Grund aus. *Im Projekt:* seit dem 21.10.2026 gebaut; gemessen in 309, seit Entscheid
126 Vorgabe für Varianten (am Heim-PC bestätigt mit 319); der Himmel wird wie der Verlauf eine Blendenstufe vom Haus weg
gestellt.

**M2 (Einstellung für Varianten)** — Der Kurzname einer Messreihe, die gewann: «Material vorne» (der Hauptstoff steht
vorne in der Bildbeschreibung) zusammen mit «Umriss halten im Lauf» (die KI darf ausserhalb des modellierten Hauses nichts
dazubauen). Der Name stammt aus der Messung `auf-20261021-303`, in der die Varianten U1/U2, M1/M2 und E1–E3 hiessen; M2
lieferte das beste Bild (Sichtbeton erkennbar, im Umriss, keine Naht). *Im Projekt:* zusammen mit *Himmel sichtbar* seit
Entscheid 126 die Vorgabe für Varianten — «M2 mit Himmel».

**Generalprobe (der Demo-Kette)** — Ein vollständiger Durchgang der Vorführung vorab, am echten Gerät, in der Reihenfolge
der Vorführung und ohne Eingriff: vom Laden des Modells über die Bilder bis zu den Fragen an den Assistenten. Anders als
eine Gegenprobe prüft sie nicht eine einzelne Änderung, sondern ob die Schritte *zusammen* tragen — Wartezeiten, Übergänge,
was ein Schritt für den nächsten liegen lässt. Jeder Schritt bekommt eine Ampel (grün vorführbar, gelb mit Vorbehalt, rot
nicht vorführbar). *Im Projekt:* `auf-20261022-327`, eine Woche vor der Demo am 29.10.2026.

**Sicherheitsrand (beim Grafikspeicher)** — Ein Zuschlag auf eine gemessene Zahl, weil nicht jeder Fall gemessen ist.
*Im Projekt:* Der Lauf mit Bildeingang brauchte gemessen 27'116 MiB mit einer Kamera; eingetragen sind 28'116 MiB, weil
mehrere Kameras bis 843 MiB mehr brauchten. Darüber kommt noch die feste Reserve von 512 MiB.

**Kanten-IoU** — Wie gut zwei Bilder dieselben Kanten haben: Zahl der Bildpunkte, die in beiden Bildern Kante sind,
geteilt durch die Zahl, die in mindestens einem Kante sind (1 = gleich, 0 = nichts gemeinsam). *Im Projekt:* das Mass
dafür, ob die KI auf einer Grundlage dieselbe Form gemalt hat (Feld `deckung` je Kamera; Schwelle zuerst 0,10 aus
Auftrag 317, seit 22.10.2026 0,25, siehe *Deckungsschwelle*; seit 24.10.2026 nur im Haus gezählt, siehe *Deckung im Haus*). Neue Fenster und Fugen sind auch Kanten, die die Grundlage nicht hat — darum liegt ein Bild
mit gehaltener Form schon bei 0,2, nicht bei 0,5.

**Abgeschriebener Beispielsatz** — Ein kleines Sprachmodell übernimmt einen Satz, der ihm in seiner Anweisung als
*Beispiel* gezeigt wurde, wörtlich in seine Antwort — auch dort, wo er nicht passt. *Im Projekt:* Der Assistent der
Knotenansicht bekam als Beispiel «Das Löschen ist als Karte A-1 vorgeschlagen» und schrieb diesen Satz in Auftrag 319
an drei Antworten, in denen nichts gelöscht wurde. Seither steht die Regel ohne Beispielsatz, und das Programm streicht
selbst jeden Satz, der eine Karte nennt, die in diesem Gespräch nicht entstand, oder ein Löschen, das keiner vorschlug.

**Randgrund (beim Schätzen des Hausanteils)** — Der Grund, warum die Schätzung «wieviel Haus ist im KI-Bild» an einem
Bildpunkt aufhörte, das Haus weiter wachsen zu lassen: zu nah, zu fern, Himmel, Boden, ein Sprung in der Tiefe. *Wozu:*
Im nahen Bild von Auftrag 317 schätzte das Programm 31 % Haus, von Hand gezählt waren es 46 %; woran es lag, war ohne die
Tiefenkarte nicht zu sehen. Seither zählt das Ergebnis je Grund mit (`rand_gruende`), und der nächste Lauf zeigt es.
*Seit Auftrag 320 nach Fläche:* Gezählt wurden zuerst die Punkte am Rand — eine lange, gezackte Kante wog dann mehr als
eine gerade Linie, die viel mehr Haus abschnitt. Jetzt steht je Grund, wie viel Bildfläche hinter dieser Grenze noch
stetig weiterginge (grösster Grund zuerst); die Punkte stehen daneben (`rand_punkte`). *Seit Auftrag 321:* Ein
Grund, hinter dem keine Fläche liegt («himmel 0,0»), steht nicht mehr in der Liste; seine Punkte schon.

**Trennhilfe (des Messbodens)** — Die Linie, unter der das Programm beim Prüfen eines KI-Bilds «Boden, nicht Haus»
annimmt. Sie kommt aus der Grundlage, dem Bild, das Blender aus dem 3D-Modell rechnet. *Wozu:* Viele Modelle haben
keinen Boden, das KI-Bild malt aber einen; die Linie hilft, Haus und Boden auseinanderzuhalten. *Der Haken (Auftrag
320):* Rahmt das KI-Bild das Haus näher als die Grundlage, liegt die Linie mitten in der Fassade und schneidet Sockel,
Vordach und Eingang ab. Seither fällt sie beim Schätzen des Hausanteils weg, wenn das KI-Bild anders rahmt und hinter
ihr das Haus deutlich weiterginge; der Boden wird dann am KI-Bild selbst erkannt (an der Steigung der Tiefe).
*Im Projekt:* `abholer._mit_messboden`, `baumasse.haus_im_bild` (Vermerk `trennhilfe`).

**Erfundene Angabe (beim Assistenten)** — Ein Wert, den das Sprachmodell in einen Auftrag schreibt, obwohl niemand ihn
nannte: eine Stimmung, eine Bildgrösse, eine Güte, ein Bildmodell. *Wozu der Begriff:* Ein kleines Modell füllt jedes
Feld aus, das ihm die Werkzeugbeschreibung zeigt. Bis Auftrag 320 wies das Programm solche Aufrufe ab, eins nach dem
anderen, und bei «Rechne jetzt das Bild» kam am Ende gar kein Auftrag zustande. Seither lässt das Programm erfundene oder
unerlaubte Werte einfach weg (dann gilt, was am Knoten eingestellt ist) und sagt, was es wegliess.
*Im Projekt:* `assistent._ohne_erfundenes`, `assistent._passt_zum_schema`.

**Tor für Ergebnis-Commits** — Die kleine Auswahl an Prüfungen, die der Heim-PC besteht, bevor er ein Messergebnis
hochlädt: nur die Tests, die die Auftrags- und Ergebnisordner lesen (rund 25 Sekunden, ohne Grafikkarte). Prüfungen, die
von der Ausstattung des Rechners abhängen (Swift, Node mit TypeScript), gehören nicht dazu. *Im Projekt:* in
`auftraege/README.md`, mit einer Probe, die prüft, dass jede genannte Testdatei existiert.

**KI-Bild ohne Grundlagenbild** — Ein Bild, bei dem das Bildmodell das gerenderte Bild der Grundlage (das Cycles-Bild)
gar nicht zu sehen bekam, obwohl es mitgeschickt war. Gebunden hat dann nur die Tiefenkarte: Die Form steht grob, Material,
Licht und Ausschnitt malt das Modell frei. *Wozu der Name:* Bestellt war eine Bearbeitung des Grundlagenbilds
(«image-edit»), gerechnet wurde ein Bild aus Text und Tiefe («txt2img») — und das Ergebnis sagte bis zum 21.10.2026 nur
«geliefert». *Im Projekt:* Das Vorgabemodell Z-Image Turbo hat keinen Eingang für ein Ausgangsbild; jeder solche Lauf trägt
jetzt den Satz «KI-BILD OHNE GRUNDLAGENBILD» mit dem Grund. Gemessen in den Heim-PC-Aufträgen 312 und 313 (alle sechs
KI-Läufe).

**Marke «Anders gerechnet» / «Ohne Grundlagenbild»** — Ein kleines Schild am fertigen Bild, das sagt: Dieses Bild ist
auf einem anderen Weg entstanden als bestellt. «Ohne Grundlagenbild» ist der häufigste Sonderfall (siehe *KI-Bild ohne
Grundlagenbild*) und steht dann allein. *Wozu:* Wer zwei Varianten vergleicht, soll sehen, dass ein Unterschied vom
Rechenweg kommen kann und nicht vom Entwurf. *Wichtig:* «Nicht gemeldet» ist nicht dasselbe wie «wie bestellt» — sagt
das Ergebnis nichts, steht kein Schild, aber auch keine Zusicherung. *Im Projekt:* Die Angabe liest die Knotenansicht von
Visbox aus dem Ergebnis des Heim-PCs (am Lauf als `modus`); gelesen wird zuerst das Feld `angewandt.modus`, sonst der
Satz «KI-BILD OHNE GRUNDLAGENBILD».

**Tolerant gelesen (Feld im Ergebnis)** — Ein Feld wird so gelesen, dass ein fehlender oder unerwarteter Wert nicht das
ganze Ergebnis ungültig macht, sondern nur dieses eine Feld als «unbekannt» gilt. *Wozu:* Ein neues Feld kommt manchmal
beim Absender an, bevor der Empfänger es offiziell kennt; ohne tolerantes Lesen würde es stillschweigend weggeworfen oder
das Bild abgelehnt. *Im Projekt:* So liest die Knotenansicht `angewandt.modus`, bis das Feld fest im Vertrag steht.

**Stetig gewachsen (Hausfläche im KI-Bild)** — Ein Rechenweg, der vom sicher bekannten Teil des Hauses aus Bildpunkt um
Bildpunkt weitergeht, solange sich die geschätzte Entfernung nur wenig ändert — so wie eine Fassade sich stetig vom
Betrachter entfernt, während an der Kante zum Himmel oder zu einer Hecke die Entfernung springt. Boden wird
ausgelassen, weil er Zeile für Zeile näher kommt, eine Wand nicht. *Wozu:* Malt die KI das Haus grösser, reichen seine
Flügel weit vor und zurück; die frühere Zählung nahm nur, was gleich weit weg war wie die Mitte, und meldete 15 % statt
43 %. *Im Projekt:* `baumasse.haus_im_bild` seit dem 21.10.2026; die alte Zahl steht zum Vergleich daneben. Die Grenzen sind
gesetzt, nicht gemessen.

**Aus der Frage übernommen (beim Assistenten)** — Eine Angabe, die der Architekt in seiner Bitte ausdrücklich nennt
(«Vorschau», «Stimmung abend», «1920 x 1080»), die das Sprachmodell aber nicht in den Auftrag geschrieben hat; Visbox
trägt sie selbst nach. Das Gegenstück zur *erfundenen Angabe*: Was niemand sagte, fällt weg; was jemand eindeutig sagte,
kommt dazu. *Wozu:* Ein kleines Sprachmodell lässt Wörter fallen, und dann rechnet ein anderes Bild als bestellt. *Im
Projekt:* `assistent._genannt_in_der_frage` seit dem 21.10.2026 (Befund 321 B1). Nur bei eindeutigem Wortlaut und nur mit
erlaubten Werten; nennt die Frage zwei Stimmungen oder zwei Bildgrössen, wird nichts ergänzt. Die Zwischenantwort sagt
«Aus deiner Frage übernommen: …».

**Doppelte Stimmung (Stimmungs-Knoten neben dem Preset)** — Eine Stimmung lässt sich auf zwei Wegen bestellen: als eigener
Knoten im Graph, der mit dem Render-Knoten verbunden ist, oder als Angabe direkt am Auftrag (das *Preset*). Beides zugleich,
mit demselben Wert, ist doppelt — und der Knoten ändert den Graph, ohne dass jemand darum bat. *Im Projekt:*
`assistent._ohne_doppelte_stimmung` lässt den neuen Knoten samt Verbindung aus dem Vorschlag weg, ausser die Bitte nennt
ausdrücklich einen Knoten («leg … an», «verbinde»); seit dem 21.10.2026 (321 B1).

**Untere Bildzeilen (bei der Bodenprüfung)** — Ob ein Bildpunkt Boden ist, prüft Visbox, indem es ein paar Zeilen darüber
und darunter vergleicht: Boden kommt Zeile für Zeile näher, eine Wand nicht. Ganz unten im Bild gibt es kein «darunter»;
bis zum 21.10.2026 galten die letzten Zeilen darum nie als Boden, und die geschätzte Hausfläche lief dort über die ganze
Bildbreite. Jetzt übernehmen sie den Befund der Zeilen knapp darüber — dasselbe Fenster, nur einseitig. *Im Projekt:*
`baumasse._bodenpunkte` (Befund 321 B4).

**Abweisungstext (an das Sprachmodell)** — Wenn das Sprachmodell einen Handgriff falsch ruft (eine erfundene Kennung,
ein neuer Knoten ohne seine Verbindung), weist Visbox den Aufruf zurück und sagt dem Modell in einem Satz, wie es richtig
geht. Dieser Satz ist eine Anleitung **für das Modell** — mit Werkzeugnamen und Regeln, die ein Mensch nicht braucht.
*Wozu die Unterscheidung:* Am 21.10.2026 stand ein solcher Satz zweimal wörtlich in der Antwort an den Architekten (322 B1).
*Im Projekt:* `assistent.frage_mit_werkzeugen` schickt ihn nur noch an das Modell; der Architekt liest stattdessen einmal
«Nicht vorgeschlagen: «Knoten setzen».» (`_satz_nicht_vorgeschlagen`), seit dem 22.10.2026.

**Alltagswort (für ein Werkzeug)** — Das Wort, mit dem der Architekt einen Handgriff des Assistenten liest, statt des
internen Namens, mit dem das Sprachmodell ihn ruft: «Rendern» statt `vis_render`, «Knoten löschen» statt
`vis_nodeLoeschen`. *Wozu:* Ein interner Name ist für die Maschine eindeutig, für den Menschen Fachjargon. *Im Projekt:*
`assistent.ALLTAGSWORT` und `fuer_den_architekten` (Befund 322 B2); ein unbekannter Name heisst «Knotenansicht». Dieselbe
Stelle schreibt auch «die Architektin» als «der Architekt», wie die festen Sätze von Visbox (322 B4).

**Verneinter Satz (bei der Prüfung der Antwort)** — Ein Satz, der sagt, dass etwas **nicht** geschehen ist («Der
Render-Auftrag ist noch nicht gestellt.»). Visbox streicht Sätze, die eine Bestellung oder Handlung behaupten, die es nicht
gab; ein verneinter Satz behauptet nichts und bleibt stehen. *Wie erkannt:* Ein «nicht», «nie» oder «kein» höchstens drei
Wörter vor dem Wort für die Handlung (bei «läuft» und «liegt» auch direkt dahinter). *Im Projekt:*
`assistent._meldet_bestellt` und `_verneint`, seit dem 22.10.2026 (322 B2).

**Gelesene Mappe (beim Sichern des Graphen)** — Die Mappe, aus der die Knotenansicht ihren Graph beim Öffnen geholt hat.
Der Heim-PC kennt eine *zuletzt geöffnete Mappe* für alle Geräte gemeinsam; öffnet ein anderes Gerät eine andere, ändert
sich diese Angabe, während die Ansicht am Mac noch die alte zeigt. *Wozu:* Gesichert wird darum in die gelesene Mappe, nicht
in die, die gerade zuletzt offen ist — sonst landete ein Graph in einer fremden Mappe. *Im Projekt:* `GET /knoten/graph`
nennt sie (`mappe`), die Seite sichert mit `?mappe=` (`graphMappe`, `sicherWeg` in `graph-sichern.ts`); seit dem
22.10.2026 (Protokoll 74 §231). Eine offene Karte trägt dieselbe Angabe und gilt nur in ihrer Mappe.

**Werkzeugliste je Sitzung (bei Claude)** — Welche Handgriffe ein angeschlossenes Programm anbietet, fragt Claude einmal zu
Beginn einer Sitzung ab und merkt es sich. Kommt danach eine neue Fassung mit mehr Handgriffen, kennt die laufende Sitzung
sie nicht, bis sie neu verbunden wird. *Im Projekt:* nach einem Visbox-Update Claude Desktop ganz beenden und neu öffnen
(der dort gestartete Brückenprozess läuft sonst mit der alten App weiter), in Claude Code `/mcp` neu verbinden (§231).

**Stand des Graphen (beim Sichern)** — Ein kurzer Fingerabdruck der gesicherten Graph-Datei einer Mappe. Die Knotenansicht
bekommt ihn beim Öffnen und schickt ihn beim Sichern mit. Hat inzwischen ein anderes Gerät in dieselbe Mappe gesichert,
passt er nicht mehr, und der Heim-PC überschreibt nicht, sondern sagt «ein anderes Gerät hat geändert — neu laden».
*Wozu:* Eine offene Ansicht sieht fremde Änderungen nicht; ohne den Stand gewänne still, wer zuletzt sichert. *Im Projekt:*
`knotenweg.graph_stand`, `schreibe_graph(stand=)`, `graphStand` in `graph-sichern.ts`; seit dem 22.10.2026 (§231 Nachtrag).

**Eigene Mappe des Mac (Entscheid 129)** — Die Mappe am Heim-PC, die die Knotenansicht am Mac zuletzt gelesen hat. Der Mac
merkt sich ihren Namen und öffnet nach «Schon anfangen» immer sie, statt der *zuletzt geöffneten Mappe* aller Geräte.
Von der Visbox-Seite her gilt die dort geöffnete. *Im Projekt:* `Knotenmappenwahl` (Kern), `Knotenmappengedaechtnis`
(Mac), Adresse der Knoten mit `?mappe=`; seit dem 22.10.2026.

**Glas-Kopf (am Mac-Fenster)** — Ein Fensterkopf ohne eigenen Balken: Der Inhalt des Programms reicht bis an den oberen
Fensterrand, und oben liegt nur ein durchsichtiger Streifen, der nach oben dichter wird und das Darunterliegende leicht
unscharf zeigt (wie Milchglas). Die Knöpfe stehen auf diesem Streifen. *Wozu:* mehr Platz für die Arbeit, ein ruhigeres
Fenster; die Unschärfe hält die Knöpfe lesbar, auch wenn Knoten darunter durchlaufen. *Im Projekt:* Owner-Auftrag
22.10.2026 für die Mac-App, Blatt 47, Bau mit Visbox 0.4.0 (Protokoll 74 §232).

**Ampel-Knöpfe (macOS)** — Die drei farbigen Punkte oben links in jedem Mac-Fenster: rot schliesst, gelb legt ins Dock,
grün macht das Fenster gross. Sie gehören dem Betriebssystem, nicht dem Programm. *Wozu:* Jeder Mac-Nutzer erwartet sie
dort; ein Programm, das bis oben reicht, muss ihnen Platz lassen. *Im Projekt:* bleiben beim Glas-Kopf (Blatt 47); das
Visbox-Logo steht rechts daneben.

**Lot (Senklot)** — Ein Gewicht an einer Schnur; es hängt immer genau senkrecht und zeigt am Bau, was lotrecht ist.
*Im Projekt:* Name und Symbol des Assistenten von Visbox (Blatt 48, Entscheid 133): ein Senklot an der Schnur in einer
Glaskachel, Visbox-Blau, statt der roten Kugel von KosmoOrbit. Das Symbol steht seit dem 22.10.2026 unten rechts (vor der
Demo vorgezogen, `visbox.css`); rechnet der Assistent, pendelt es sanft, bei reduzierter Bewegung hängt es still. Der Name
bleibt bis 0.4.0 «Assistent» (Protokoll 74 §232, §244).

**Detailstufe (eines Knotens)** — Wie viel ein Knoten zeigt, je nachdem, wie weit man in der Knotenansicht hinein- oder
herausgezoomt hat. Wie in einem Plan: im Massstab 1:50 sieht man die Wandschichten, in 1:200 nur noch den Raumnamen, dafür
grösser geschrieben. *Wozu:* Herausgezoomt würde die normale Schrift so klein, dass man sie nicht mehr lesen kann; statt
Überlauf oder Gekritzel zeigt der Knoten dann weniger, aber lesbar. *Im Projekt:* Regel R1.3 des Owner-Auftrags vom
22.10.2026 (Blatt 50, geplant, nach der Demo): ab Zoom 0,75 alles; zwischen 0,4 und 0,75 Kopfwort und eine Kernzeile in
grösserer Schrift; unter 0,4 nur das Kopfwort auf einer Fläche in der Farbe der Kategorie. Der Umriss bleibt gleich gross,
damit die Verbindungen nicht springen (Protokoll 74 §234).

**Kategorie (eines Knotens)** — Die Familie, zu der eine Knotenart gehört, mit einer eigenen Farbe im Band unter dem Kopf:
Quelle (grün: Modell, Kamera, Kamera aus 3D, Skizze, Referenz, Aufnahme), Stimmung und Stil (ocker: Stimmung, Prompt,
Kombinierer), Material (violett: Oberfläche, Material, Farbpalette), Rechnen (blau: Render, Varianten, Zahl), Ergebnis
(grau: Vergleich, Aufs Blatt). *Wozu:* Man erkennt auch weit herausgezoomt, was wofür steht, ohne zu lesen. Die Farbe der
Daten, die an einem Anschluss fliessen (Prompt, Szene, Bild …), bleibt davon getrennt und erscheint nur am Anschlusspunkt.
*Im Projekt:* Regel R7, Farben vom Owner am 22.10.2026 entschieden; gebaut wird nach der Demo (Blatt 50e, Protokoll 74 §234).

**Zeichnung im Massstab (Leitsatz der Knotenansicht)** — Der Grundsatz des Owner-Auftrags vom 22.10.2026: Ein Knoten
verhält sich wie eine Planzeichnung. Beim Zoomen wird alles gemeinsam grösser oder kleiner — Rahmen, Schrift, Bilder —,
nichts läuft über und nichts bleibt gross, während der Rest schrumpft. *Wozu:* Bis 0.3.33 schrumpfte der Knoten beim
Herauszoomen, die Schrift aber nicht (der Browser hält eine Mindestschrift ein), und der Text lief über den Rand. *Im
Projekt:* Regel R1; vor der Demo wird nur das Herauszoomen umgestellt (R1.2), der Rest nach dem Owner-Entscheid zu Blatt 50.

**Zoom-gebundene Schrift** — Schrift, die beim Zoomen genau so viel grösser oder kleiner wird wie der Knoten, in dem
sie steht — so wie die Beschriftung auf einem Plan, den man vergrössert oder verkleinert kopiert. Das Gegenteil wäre eine
Schrift, die ihre eigene Grösse behält, während der Rahmen schrumpft. *Wozu:* Nur so bleibt ein Knoten beim Herauszoomen
eine verkleinerte Zeichnung, statt dass der Text über den Rand läuft; wer Einzelheiten lesen will, zoomt hinein. *Im
Projekt:* seit dem 22.10.2026 beim Herauszoomen (Regel R1.2 des Owner-Auftrags, Protokoll 74 §235); beim Hineinzoomen
galt es schon vorher.

**Mindestschrift (des Browsers)** — Eine untere Grenze, die ein Darstellungsprogramm für Webseiten (Browser, auch das
Anzeigefenster in der Mac-App) für Schrift durchsetzt: Wird Text durch Verkleinern kleiner als etwa 9 Pixel, zeichnet es
ihn trotzdem 9 Pixel hoch. *Wozu:* gedacht als Lesehilfe auf Webseiten. *Im Projekt:* Sie war die Ursache dafür, dass die
Schrift in den Knoten beim Herauszoomen gross blieb und überlief (Mac-Befund 0.3.33). Seither wird die Knotenansicht beim
Herauszoomen als ganzes Bild verkleinert, nicht neu beschriftet — dann greift die Grenze nicht (Protokoll 74 §235).

**Neu auslegen gegenüber als Ganzes verkleinern (beim Zoomen)** — Zwei Arten, wie die Knotenansicht eine Zoomstufe
umsetzen kann. *Neu auslegen* heisst: alles wird in der neuen Grösse frisch gesetzt, Buchstabe für Buchstabe — scharf,
aber das Programm darf dabei eigene Regeln anwenden (etwa die Mindestschrift). *Als Ganzes verkleinern* heisst: der
Knoten wird einmal in Normalgrösse gesetzt und dann wie ein Bild verkleinert — alles schrumpft mit demselben Faktor.
*Im Projekt:* seit dem 22.10.2026 unter Zoom 1 «als Ganzes verkleinern», ab Zoom 1 «neu auslegen», damit die Knoten beim
Hineinzoomen scharf bleiben (Protokoll 74 §235). **Nachtrag (gleicher Tag, Protokoll 74 §245):** Das Neu-Auslegen ab 1 liess
die Schrift bei jedem Zoomschritt um Bruchteile springen; seither gilt für alle Stufen «als Ganzes verkleinern oder
vergrössern», und die Schärfe kommt aus dem *Schärfen in der Ruhe* (siehe dort).

**Schärfen in der Ruhe (Raster der Knotenansicht)** — Die Knotenansicht zeichnet ihre Knoten in einer von vier festen
Feinheiten: einfach, doppelt, dreifach oder vierfach so fein wie die Normalgrösse (das *Raster*). Während man zoomt, bleibt
die Feinheit stehen und das ganze Bild wird nur grösser oder kleiner gezogen; ruht der Zoom gut eine Zehntelsekunde (150 ms), wählt die
Ansicht die passende Feinheit und zeichnet einmal neu — scharf, und weil die Feinheiten ganzzahlige Vielfache sind, an genau
denselben Stellen. *Wozu:* Beim Zoomen soll nichts springen (die Schrift klebt am Knoten), danach soll alles scharf sein.
*Im Projekt:* seit dem 22.10.2026 nach dem Mac-Befund 0.3.35 (Protokoll 74 §245); beim Herauszoomen sinkt die Feinheit
sofort, damit nie ein vielfach feines Bild im Speicher liegt.

**SVG-Schrift in Bildschirmgrösse** — Eine Eigenheit der Browser: Text in einer Vektorgrafik (SVG) setzen sie in der Grösse,
die er gerade *am Bildschirm* hat, mit gerundeten Buchstabenbreiten — und rechnen das Ergebnis dann zurück. Weil die
Rundung bei jeder Zoomstufe anders ausfällt, ist derselbe Text je nach Zoom ein paar Prozent breiter oder höher.
*Im Projekt:* So waren die Knotenkopfzeile und die Namen der Anschlüsse gebaut; gemessen war «Prompt» bei halber Grösse
relativ zum Knoten 8 % höher und 4 % breiter als bei voller — ein Grund für das Zittern der Schrift (Protokoll 74 §245).

**Lineare Schriftauslegung** — Buchstaben werden mit ihren genauen, ungerundeten Breiten aus der Schriftdatei gesetzt,
statt mit Breiten, die das Programm für kleine Schriftgrössen auf ganze Bildpunkte rundet. Dann ist ein Wort in doppelter
Grösse genau doppelt so breit. *Wozu:* Nur so ist eine Zeichnung im Massstab in jeder Grösse dieselbe — kein Umbruch und
keine Abkürzung ändert sich. *Im Projekt:* seit dem 22.10.2026 für die ganze Knotenansicht eingeschaltet, Knöpfe, Felder
und Vektorgrafik eingeschlossen (Protokoll 74 §245).

**Grundbild statt «Grundlage» (geplante Umbenennung)** — Owner-Entscheid vom 22.10.2026 (Regel R9): Das Bild, das Blender
ohne KI rechnet, heisst überall gleich «Grundbild» — in den Knoten, auf der Karte, in den Beschreibungen für Claude und
hier. Der Knopf «Grundlage rendern» wird «Grundbild rechnen», «Variante erzeugen» wird «Bild erzeugen»; «Bildwerkzeug»
und «Backbone» werden «Bildmodell», «Samples» wird «Qualität» (mit «20 Schritte» im Hinweis). *Wozu:* Dieselbe Sache
hatte zwei oder drei Namen, je nachdem, wo man hinsah. *Im Projekt:* geplant, nach der Demo; eine Wortliste im Code mit
einer Probe, die alte Wörter rot macht (Baustein von UI). Bis dahin steht in der Software noch «Grundlage»; siehe auch
**Grundbild (Grundbild mit Licht)** (Protokoll 74 §234).


**Einzelwahl und Mehrfachwahl (am Stimmungs-Knoten)** — Am Stimmungs-Knoten lassen sich eine oder mehrere der acht
Stimmungen anhaken (Mehrfachwahl, Entscheid 113). Das Bild des Render-Knotens bestellt die erste; ein Bild je Stimmung
liefert der Varianten-Knoten. Gespeichert ist die Wahl zweimal: als Liste aller angehakten Stimmungen (`presets`) und als
einzelner Wert, die erste davon (`preset`), damit ältere Programmteile sie weiter lesen können. Wählt Claude oder der
Assistent eine einzelne Stimmung, ist das eine **Einzelwahl**: Sie ersetzt die ganze Liste, wie ein Klick, der alles andere
abwählt. *Im Projekt:* `stimmungAufruf` in `kosmovis/packages/kosmo-kernel/src/derive/visgraph.ts`, Protokoll 74 §236.

**«Die Liste gewinnt» (Lese-Regel am Stimmungs-Knoten)** — Die Regel, welche der zwei gespeicherten Angaben gilt, wenn sie
sich widersprechen: Steht eine gültige Liste da, gilt die Liste; der einzelne Wert ist nur ihr Abbild. Ohne Liste (ein
Graph aus der Zeit vor der Mehrfachwahl) gilt der einzelne Wert, ohne beides «Morgenlicht». So zeigen Knoten, Prompt,
Bestellung und die Antwort an Claude dieselbe Stimmung, auch in einem alten, widersprüchlich gespeicherten Graphen.
*Wozu:* Ein Widerspruch darf nie zwei Antworten haben — sonst meldet Claude «Morgen», und gerendert wird «Abend» (Mac-Befund
0.3.33). *Im Projekt:* `stimmungAusParams` (Lesen) und `stimmungAufruf` (Schreiben), Protokoll 74 §236.

**Kartenzeile (eines Vorschlags)** — Der Satz auf der Karte «Vorschlag von Claude», der sagt, was ein Vorschlag ändert,
in Alltagswörtern und mit Werten: «Stimmung: Morgenlicht → Abendstimmung» statt eines internen Feldnamens. Je Knoten der
Name, den er in der Knotenansicht trägt; je Einstellung ein Wort, das der Architekt kennt; Werte so, wie er sie am Knoten
sieht («Südost», «Vorschau», «1600 × 1000»); freier Text gekürzt in «». Was das Programm nicht kennt, heisst «eine weitere
Einstellung». *Wozu:* Wer «Anwenden» drückt, soll wissen, was passiert. *Im Projekt:* Entscheid 131, `derive/vis-kartenzeile.ts`
(Kopie unter `kosmovis/`); derselbe Satz steht nach «Anwenden» im Verlauf (Protokoll 74 §238).

**Vorher → Nachher (auf der Karte)** — Die Schreibweise der Kartenzeile, wenn sich ein Wert ändert: links der Wert, der jetzt
gilt, rechts der vorgeschlagene. Steht am Knoten noch nichts, ist «vorher» die Vorgabe, die bis dahin galt (etwa die drei
Himmelsrichtungen der Auto-Kamera). Ist der Wert gleich oder neu, steht nur einer da. *Im Projekt:* der alte Wert kommt aus
dem Graphen, wie er vor der Probe-Ausführung war — das Programm fasst erst nach der Probe zusammen und merkt sich darum den
Stand vorher (Protokoll 74 §238).
**Geduld (der Wartemeldung)** — Wie lange die Knotenansicht nach «Freigeben» abwartet, bevor sie sagt, das Bild sei
«nicht abgeholt». Der Heim-PC schaut nur alle 10 Sekunden nach neuen Aufträgen (siehe **Taktgeber**); eine Meldung
«niemand holt ab» ist darum erst nach mehreren solchen Takten eine Beobachtung und vorher nur eine Vermutung. Die Geduld
ist drei Takte, also 30 Sekunden; bis dahin steht «wartet auf den Heim-PC …». *Im Projekt:* `ABHOLER_GEDULD_MS` in
`kosmovis/apps/kosmo-orbit/src/modules/vis/vis-runtime.ts`; Protokoll 74 §240.

**Schattenfänger (Boden)** — Eine unsichtbare Fläche unter einem Modell, die nur eines zeigt: den Schatten, der auf sie
fällt. So steht ein Haus im Bild auf etwas, ohne dass ein erfundener Boden mit eigener Farbe dazukommt. Visbox legt heute
**keinen** solchen Boden an: Ein Modell ohne Gelände schwebt im Grundbild. Ob ein Ersatzboden kommt, ist nach der Demo zu
entscheiden. *Im Projekt:* Befund in Protokoll 74 §240; Messauftrag `auf-20261022-331`.

**Durchlass (eines Materials)** — Wie viel Licht ein Material durch sich hindurchlässt, wie eine Glasscheibe: Man sieht
durch sie hindurch, und zugleich spiegelt sie. Das ist etwas anderes als «halb durchsichtig gemacht» — dabei wird die
Fläche nur blasser, ohne Spiegelung. In der Modelldatei steht der Durchlass als eigene Angabe am Material (0 = gar nicht,
1 = ganz). Visbox erkennt eine Scheibe daran oder am Namen «Glas»; bei einer gewählten Fenster-Textur bleibt sie seit dem
22.10.2026 Glas, nur der Rahmen bekommt die Textur. *Im Projekt:* `_ist_glas` in
`src/aiimaging/runners/blender_depth_stage.py`; Protokoll 74 §240. Nennt eine IFC-Datei an einem Stil eine
Durchsicht, schreibt die Umwandlung sie seit dem 22.10.2026 als Durchlass in die glb (vorher kam die Scheibe als hellgraue
Platte an); Protokoll 74 §242.

**Stummer Ausgang (einer Bedienung)** — Ein Weg im Programm, auf dem ein Klick endet, ohne dass etwas geschieht und
ohne dass ein Satz sagt, warum. Für die Person am Bildschirm sieht das aus wie ein kaputter Knopf: Sie kann nicht
unterscheiden, ob sie etwas falsch gemacht hat, ob es noch kommt oder ob es nie kommt. *Wozu der Begriff:* Er benennt eine
Fehlerart, die man im Code suchen kann — jede Stelle, die «nichts tun» darf, muss es sagen. *Im Projekt:* Der Knopf
«Freigeben» am Render-Knoten hatte drei solche Ausgänge; seit dem 22.10.2026 steht in jedem Fall ein Satz am Knoten
(Protokoll 74 §239).

**Wartender Auftrag (auf Freigabe)** — Ein Bild-Auftrag, der beim Heim-PC angekommen ist, aber noch nicht rechnet: Er
wartet, bis jemand am Knoten «Freigeben» drückt, weil erst dann die Grafikkarte belegt wird. Er kostet nichts, solange er
wartet, und rechnet ohne Freigabe nie. *Wozu:* Die Grafikkarte startet nie ohne einen Klick des Architekten. *Im Projekt:*
Ein wartender Auftrag sperrt «Grundlage rendern» seit dem 22.10.2026 nicht mehr; der Knopf bricht ihn ab und bestellt die
Grundlage (Protokoll 74 §239).

**Teil eines Bauteils (Zusammenfassung in der IFC)** — In einer IFC-Datei kann ein Bauteil aus Teilen bestehen: Ein
Dach ist oft nur ein Name ohne eigene Form, und die eigentliche Fläche ist eine Platte, die als *Teil* dieses Dachs
eingetragen ist. Ebenso ein Fenster aus Rahmen und Scheibe. Wer nur die Platte ansieht, hält sie für einen Boden. *Wozu:*
Die Umwandlung schaut seit dem 22.10.2026 nach, zu welchem Ganzen ein Teil gehört, und gibt ihm dessen Art mit (Dach,
Fenster, Tür). *Im Projekt:* `_ganzes_von` und `knoten_merkmale` in `src/aiimaging/runners/ifc_to_glb_runner.py`;
Protokoll 74 §242.

**Füllung (eines Ausschnitts)** — Der Eintrag in einer IFC-Datei, der sagt: Dieses Fenster (oder diese Tür) sitzt in
jenem Loch in der Wand. Fehlt er, ist das Loch leer — im Bild ein schwarzes oder helles Viereck ohne Glas. *Wozu:* An der
Zahl der Füllungen lässt sich schon beim Laden sagen, ob eine Datei Fenster mitbringt oder nur Löcher. *Im Projekt:* Die
Umwandlung meldet seit dem 22.10.2026 «FENSTER NUR ALS LÖCHER», wenn eine Datei Ausschnitte, aber keine Füllung hat
(`warnungen_aus_bestand`); Protokoll 74 §242.

**Vordefinierter Typ (eines IFC-Bauteils)** — Eine Unterart, die eine IFC-Datei an ein Bauteil schreibt: Eine Platte kann
«Boden», «Decke» oder «Dach» sein, je nachdem, was dort steht. Steht nichts Brauchbares da («nicht festgelegt»), hilft nur
das Ganze, zu dem die Platte gehört. *Im Projekt:* geht seit dem 22.10.2026 als `PredefinedType` an den Knoten der glb;
eine Platte mit «Dach» wird in Blender als Dach behandelt (`materialwahl.art_von`); Protokoll 74 §242.

**Art-Merkmal am Knoten (`extras.kind`)** — Ein Zusatzfeld an einem Teil der Modelldatei, das sagt, *welche Art Bauteil*
es ist — Wand, Dach, Öffnung (Fenster oder Tür) —, unabhängig von seinem Namen. Es ist der Bruder der *Rolle am Knoten*,
die sagt, *wozu* ein Teil da ist (Bestand, Boden). *Wozu:* Blender wählt danach, welches Material ein Teil bekommt. *Im
Projekt:* KosmoOrbit schreibt es seit jeher; die IFC-Umwandlung von Visbox seit dem 22.10.2026 für Dächer und Öffnungen
(`knoten_merkmale`); gelesen von `materialwahl.art_von`. Protokoll 74 §242.

**Werkzeugrad (am iPad)** — Ein runder Knopf oben links auf dem Zeichenblatt, der sich zu einem Ring mit vier Feldern aufklappt:
Stifte, Strich (Stärke, Deckkraft, Glättung), Farbe (Paletten, Pipette) und Werkzeuge (Radierer, Lasso, Ebenen). Vorbild ist die
Zeichen-App «Concepts». *Wozu:* Das ganze Blatt bleibt frei zum Zeichnen; die Werkzeuge sind einen Tipp entfernt. *Im Projekt:*
vorgeschlagen auf Blatt 51 (Owner-Liste 22.10.2026, I2), noch nicht gebaut; Protokoll 74 §243.

**Glättung (eines Strichs)** — Die Zeichen-App beruhigt einen zittrigen Strich, indem sie die Linie leicht nachzieht, bevor sie
gespeichert wird. Nicht zu verwechseln mit dem *Mittelwertfilter (Glättung)* für Bilder. *Im Projekt:* Die Zeichenbibliothek von Apple
(PencilKit) kann das nicht; am iPad wäre es ein eigener Bau (Blatt 51).

**Lasso (Zeichenwerkzeug)** — Man umfährt mit dem Stift einen Teil der Zeichnung und kann ihn danach verschieben, vergrössern oder
löschen. *Im Projekt:* Teil des Werkzeugrads (Blatt 51).

**Pipette** — Ein Werkzeug, das eine Farbe von einer Stelle des Bildes aufnimmt, damit man genau mit ihr weiterzeichnet. *Im
Projekt:* im Feld «Farbe» des Werkzeugrads; nimmt die Farbe auch von der Unterlage (Blatt 51).

**Insel-Oberfläche (am iPad)** — Statt fester Leisten links und rechts schweben alle Bedienteile als kleine Inseln über dem Blatt,
wie in der Knotenansicht am Mac. Die ganze Fläche ist Arbeitsfläche. *Im Projekt:* Owner-Liste 22.10.2026, I1; Blatt 51.

**Art der Unterlage (leeres Blatt, Live-3D, Dokument)** — Worauf am iPad gezeichnet wird: auf ein leeres Blatt, in eine drehbare
3D-Ansicht des Modells oder auf ein Dokument (PDF, Plan, Bild). Die *Unterlage (einer Skizze)* war bis dahin immer ein Bild aus der
Mappe. *Im Projekt:* Owner-Liste 22.10.2026, I4; Blatt 51; Protokoll 74 §243.

**3D-Skizze** — Striche, die nicht nur als Bild, sondern mit ihrer Lage im Raum gespeichert werden: Ein Strich auf der Hauswand
«weiss», dass er auf dieser Wand liegt. *Wozu:* Er kann später ins 3D-Modell übernommen werden. *Im Projekt:* zweite Stufe der
Live-3D-Unterlage, Ziel Visbox 0.5.0 (Blatt 51).

**Zeichnungsart** — Was eine Zeichnung *ist*: Grundriss, Schnitt, Ansicht, Perspektive, Detail, Notiz, Material, Variante, Licht,
Vegetation oder Personen. *Wozu:* Ein Grundriss darf nicht wie eine Perspektive ins KI-Bild gehen. *Im Projekt:* Anlass war die
Demo-Skizze vom 22.10.2026 (ein EG-Grundriss wurde als Perspektive gerechnet); Blatt 52 schlägt vor, dass die KI die Art vorschlägt
und der Architekt bestätigt.

**Texterkennung (auf dem Gerät)** — Das iPad liest geschriebene Wörter aus einem Bild, etwa «Wohnen» oder «Bad» in einer Skizze, ohne
Internet. Sie gehört zum Betriebssystem von Apple. *Im Projekt:* vorgeschlagen für die Beschriftungen der Zeichnungsart (Blatt 52).

**Sehmodell** — Ein Sprachmodell, das zusätzlich Bilder ansehen und beschreiben kann. Das heutige Sprachmodell des Assistenten liest
nur Text. *Im Projekt:* nötig, damit die lokale KI eine Skizze als Grundriss erkennt oder Wände daraus liest; noch keins freigegeben —
es muss Apache-2.0 oder MIT tragen und am Heim-PC gemessen werden (Protokoll 74 §243).

**Weg A und Weg B (wohin eine Skizze fliesst)** — Weg A: Die Skizze ändert das 3D-Modell; die lokale KI liest Wände, Volumen,
Öffnungen und legt die Änderung als Karte vor. Weg B: Die Skizze geht nur «ins Licht», also als Bildvorgabe ins KI-Bild, und ergibt
eine Variante. *Im Projekt:* Owner-Liste 22.10.2026, I6; Blatt 52. Heute gibt es nur Weg B; Weg A ist Forschung (Ziel 0.5.0).

**Planfarben (Gelb-Rot-Plan)** — In der Schweiz übliche Farben auf Umbauplänen: Bestand grau oder schwarz, Neues rot, Abbruch gelb.
*Im Projekt:* Empfehlung auf Blatt 52, um 3D-Änderungen aus Weg A im 3D-Fenster und im Grundbild vom Original zu unterscheiden.

**Herkunft (einer Variante)** — Woraus eine Variante entstand: aus einer Skizze, aus einer 3D-Änderung (Weg A), aus dem Licht-Weg
(Weg B) oder aus dem Bildmodell (Stimmung, Material). Sie steht als kleine Marke an der Variante. *Im Projekt:* Owner-Liste
22.10.2026, I7; Blätter 52 und 53.

**Tafel (je Projekt)** — Eine zweite Ansicht neben der Knotenansicht, in der alles eines Projekts ausgelegt ist: Dokumente,
Skizzen, Bilder, Varianten und Blätter, mit Herkunft. Sie ist die Mappe, sichtbar gemacht, keine zweite Ablage; gerendert wird weiter
in der Knotenansicht. Nicht zu verwechseln mit der *Kosmo-Tafel*, der Bildwand des Owners. *Im Projekt:* Owner-Liste 22.10.2026, I5,
nach dem Vorbild von KosmoPrepare; Blatt 53.

**Materialpass** — Eine Karte, die nach dem Laden eines Modells die Farben und Materialien aus der Datei auflistet und für jede
Bauteil-Art ein Material aus der Bibliothek vorschlägt. Trägt die Datei keine Farben, schlägt sie nur nach Bauteil-Art vor. *Im
Projekt:* Owner-Liste 22.10.2026, A1; Blatt 54. Der Anlass war ein Modell ohne Farben: Die Datei hatte keine (Protokoll 74 §242).

**Zone (der Knotenansicht)** — Ein breiter Streifen der Knotenfläche für eine Art Arbeit: links alles zum 3D-Modell, in der Mitte die
Maschine, rechts alles zum KI-Bild. Neue Knoten landen in ihrer Zone. Zonen sind Hintergrund, keine Mauer. *Im Projekt:*
Owner-Liste 22.10.2026, A3; Blatt 55.

**Maschine (Mitte der Knotenansicht)** — Die mittlere Zone, in der Kombinierer und Render-Knoten stehen: dort, wo aus Modell und
Stimmung ein Bild gerechnet wird. Sie ist breiter, dunkler und blau gerahmt. *Im Projekt:* Blatt 55.

**Anschluss-Seite (eines Knotens)** — Die Seite eines Knotens, an der seine Ein- und Ausgänge sitzen, also wo die Verbindungslinien
andocken. Üblich ist «links hinein, rechts hinaus». In der Knotenansicht mit drei Zonen richtet sich die Seite stattdessen nach der
Art des Knotens: 3D-Knoten geben nach rechts ab, KI-Knoten nach links, beide also zur Maschine in der Mitte hin; die Maschine nimmt
3D von links und KI von rechts. So läuft keine Linie rückwärts quer über die Fläche. Die Seite gehört zur Knotenart, nicht zum Ort:
Ein Knoten, der in eine andere Zone gezogen wird, behält sie. *Im Projekt:* Owner-Nachtrag 22.10.2026 zu A3; Blatt 55a.

**Stil-Eingang (am Kombinierer)** — Ein Anschluss am Kombinierer, an den ein Satz für das KI-Bild kommt (Stimmung, Prompt, Stil,
Material). Heute gibt es drei feste; vorgeschlagen ist, dass immer einer frei bleibt und die Nummer die Reihenfolge im Prompt angibt.
*Im Projekt:* Owner-Liste 22.10.2026, A4; Blatt 55.

**Auto-Standpunkte (über Eck)** — Blickrichtungen, die Visbox nach dem Laden selbst setzt, aus der Hülle des Gebäudes ausgerichtet.
«Über Eck» heisst: von Südwest, Südost, Nordost und Nordwest, sodass zwei Fassaden zu sehen sind. *Im Projekt:* heute drei feste
Richtungen am Heim-PC (Entscheid 92a); vier vorgeschlagen auf Blatt 56 (A5).

**Weg nur der App (App-Weg)** — Eine Adresse, die die Knotenansicht im Mac-Programm aufruft und die **nur das Mac-Programm**
beantwortet, nicht der Heim-PC. Die Knotenansicht merkt den Unterschied nicht; das Mac-Programm führt dafür eine eigene,
kurze Liste neben der Liste der Wege, die es an den Heim-PC weiterreicht. *Im Projekt:* heute einer, «hol das Modell in die
offene Mappe» nach «Datei laden …» (`Knotenwege.appwege`). Fehlte er in der Liste, galt er als unbekannte Datei, und die
Mappe am Mac blieb ohne Modell (Befund N1, Protokoll 74 §246).

**Stumme Absage (404 als «nichts zu tun»)** — Eine Antwort «gibt es nicht», die der Empfänger absichtlich als «hier ist
nichts zu tun» liest statt als Fehler. Das ist bequem, solange die Antwort nur aus diesem Grund kommt; kommt sie aus einem
anderen, verschwindet der Fehler spurlos. *Im Projekt:* Die Knotenansicht liest 404 auf «Modell in die Mappe am Mac holen»
als «keine Mappe am Mac offen» — und schwieg, als der Weg im Mac-Programm fehlte (Protokoll 74 §246).

**Bildnachlese (Mappe am Mac)** — Beim Öffnen einer Mappe am Mac fragt das Mac-Programm den Heim-PC nach den
jüngsten Aufträgen dieser Mappe, denen noch etwas fehlt (Laufzettel, Bilder), und legt das Fehlende in die Mappe. Vorher
kamen Bilder nur, wenn die Knotenansicht im richtigen Augenblick nachfragte. *Im Projekt:* `Mappenkern.nachzuholen`, bis zu
20 Aufträge, jedes Bild bis zu dreimal (Befund N8, Protokoll 74 §246). Nicht zu verwechseln mit dem **Nachholen (nach einer
Schreibkollision)**.

**Ausgelagertes Raster (im Befund)** — Ein *Raster* ist hier eine Liste mit einem Wert je Bildpunkt, etwa «hier steht das
Haus: ja/nein» für jeden Punkt eines Bildes. Ein Bild mit 1600 × 1000 Punkten hat 1,6 Millionen solcher Werte. *Ausgelagert*
heisst: In der Messdatei eines Auftrags (`befund.json`) steht statt der langen Liste nur ein Verweis mit den Kennzahlen (wie
viele Punkte, wie viele davon «ja»); die Liste selbst liegt gepackt in einer Datei daneben (`befund_raster.json`), ein Bit je
Bildpunkt, und lässt sich ohne Verlust zurückholen. *Wozu:* Die Messdatei bleibt lesbar und klein. *Im Projekt:* seit dem
22.10.2026, nachdem eine Messdatei mit vier Standpunkten 93 MB gross war (Protokoll 74 §248).

**Voller Auftrag (Grundbild und KI in einem)** — Ein Auftrag, der das Grundbild in Blender **und** das KI-Bild darauf in einem
Lauf rechnet, statt in zwei Schritten («Grundlage rendern», dann «Variante erzeugen»). Er rechnet dabei ein neues Grundbild,
und der Heim-PC legt es als Grundlage ab. *Im Projekt:* Entscheid 98c; seit dem 22.10.2026 merkt sich der Render-Knoten auch
die Grundlage eines vollen Auftrags — vorher stand danach weiter «Grundlage veraltet» (Protokoll 74 §248).

**Himmelsgrenze (Untergrenze des sichtbaren Himmels)** — Eine Regel stellt den Hintergrund hinter dem Haus etwas dunkler,
damit sich das Haus abhebt («Abstand zum Haus», eine Blendenstufe). Sie war für einen erfundenen, ruhigen Farbverlauf
gebaut. Seit die Kamera das echte Himmelsfoto der Stimmung sieht, dunkelte dieselbe Regel den Himmel bis fast schwarz ab —
auch am Mittag. Die *Himmelsgrenze* begrenzt das: Bei dämmrigen Stimmungen darf der Himmel höchstens eine Blendenstufe (halb
so hell) dunkler werden, bei hellen Stimmungen gar nicht unter die Helligkeit, mit der die Stimmung ihn liefert. *Im
Projekt:* seit dem 22.10.2026 nach Ergebnis 333; im Bericht `himmel_grenze` (Protokoll 74 §249).

**Helle und dämmrige Stimmung** — Die Einteilung der Lichtstimmungen für die Himmelsgrenze. *Hell* sind Mittag, Bedeckt,
Nebel und Winter — Licht, bei dem der Himmel im Foto hell ist. *Dämmrig* sind Morgen, Abend, Blaue Stunde (und das
Gipsmodell «weiss») — dort darf der Himmel dunkler stehen als das Haus. Eine Setzung, keine Messung; der Heim-PC misst sie in
Auftrag 334 (Protokoll 74 §249).

**Reiner Himmel («puresky»-Himmelsbild)** — Ein Himmelsfoto rundum, bei dem der Boden weggelassen ist: Die obere Hälfte
ist Himmel, die untere ist leer, grau oder ein Spiegelbild des Himmels. *Wozu:* Ein solches Bild gibt sauberes Licht ohne
Bäume und Häuser, die sich im Glas spiegeln. *Im Projekt:* Die Himmelsbilder der Stimmungen sind solche Aufnahmen; weil die
Kamera sie in jede Richtung sah, stand unter dem Horizont «Himmel» statt Boden (Ergebnis 334, Protokoll 74 §250).

**Albedo (Rückstrahlvermögen)** — Wie viel Licht eine matte Fläche zurückwirft, als Anteil von 0 (schwarz, schluckt alles)
bis 1 (weiss, wirft alles zurück). Eine matte Fläche unter einem gleichmässig hellen Himmel erscheint ungefähr so hell wie
Albedo mal Himmel. *Im Projekt:* Das Grau der Geländeplatte (0,30) ist ihre Albedo; daraus wird die Farbe des fernen
Bodens gerechnet (Protokoll 74 §250).

**Boden bis zum Horizont (Welt-Boden)** — Was die Kamera unter dem Horizont sieht, wo kein Modell und keine Geländeplatte
mehr steht. Seit dem 22.10.2026 eine ruhige Bodenfarbe — das Grau der Platte, beleuchtet vom mittleren Himmel — statt der
unteren Hälfte des Himmelsfotos. Nur die Kamera sieht sie; Licht, Schatten und Spiegelungen kommen weiter aus dem
Himmelsfoto, und Tiefe, Masken und Platte bleiben unverändert. *Im Projekt:* `stimmung.boden_bis_horizont`, im Runner
`_boden_unter_horizont`, nur mit sichtbarem Himmel; im Bericht `umgebung.hintergrund.boden` (Protokoll 74 §250).
**Seit Ergebnis 335** ist er die Platte in der Ferne: dasselbe Grau, beleuchtet von Sonne **und** Himmel, also so hell und
so gefärbt wie die Platte — die erste Fassung (nur Himmelslicht) war ein dunkles Blaugrau, das wie Wasser aussah. Abends
dunkelt er mit dem Hintergrund ab und bleibt dämmrig (`stimmung.boden_zum_faktor`, Fassung `platte-336`, Protokoll 74 §251).

**Beleuchtungsstärke (Licht auf einer Fläche)** — Wie viel Licht auf eine Fläche fällt, zusammengezählt aus allen
Richtungen: von der Sonne (umso mehr, je höher sie steht) und vom ganzen Himmel. Eine matte Fläche erscheint so hell wie
Albedo mal Beleuchtungsstärke (geteilt durch die Kreiszahl π). *Im Projekt:* Daraus rechnet `stimmung.boden_bis_horizont`
die Helligkeit des fernen Bodens — mit derselben Sonne und demselben Himmel wie die Geländeplatte, damit beide gleich hell
sind (Protokoll 74 §251).

**Selbstleuchtend (emissiv)** — Eine Fläche oder ein Hintergrund, der seine Helligkeit nicht vom Licht der Szene bekommt,
sondern sie selbst «abgibt», wie ein Bildschirm. *Im Projekt:* Der Welt-Boden ist selbstleuchtend: Er wird nicht von der
Sonne beschienen, sondern bekommt eine fest gerechnete Farbe — darum muss seine Helligkeit aus dem Licht der Stimmung
geschätzt werden, sonst passt er nicht zur beschienenen Platte (Protokoll 74 §251).

**Naht (an der Plattenkante)** — Die sichtbare Kante, wo die Geländeplatte aufhört und der Welt-Boden beginnt, wenn beide
verschieden hell sind. Gemessen als Unterschied der Grauwerte direkt beidseits der Kante. *Im Projekt:* Ergebnis 335: mittags
31,5, abends 74,4 Grauwerte; seither ist der Boden mittags so hell wie die Platte und abends eine Blende dunkler — die Naht
soll mittags fast verschwinden und abends etwa halb so gross sein (Auftrag 336, Protokoll 74 §251). Ergebnis 336:
mittags +0,9 (weg), abends −57,8 — noch über der Grenze 45; seither ist der ferne Boden abends so hell wie die Platte
(siehe **Naher und ferner Boden**, Auftrag 338, Protokoll 74 §252).

**Naher und ferner Boden** — Der Welt-Boden hat seit Auftrag 338 zwei Helligkeiten: nah (steil nach unten geschaut, im
Vordergrund) und fern (knapp unter dem Horizont). Dazwischen ein weicher Übergang über die obersten 12 Grad unter dem
Horizont (`stimmung.BODEN_FERN_GRAD`). *Wozu:* Abends soll der Vordergrund dämmrig bleiben, damit sich das Haus abhebt;
die Kante der Geländeplatte liegt aber weiter weg, knapp unter dem Horizont — dort ist der Boden jetzt so hell wie die
Platte, und die Kante fällt weniger auf. Mittags sind beide gleich hell. *Im Projekt:* `stimmung.boden_fern_zum_faktor`,
Knoten `Boden_Fern` im Welt-Shader (Protokoll 74 §252).

**Wirkungsgrad einer Korrektur (Gewinn je Kosten)** — Wie viel eine Änderung am gewünschten Ort bringt, verglichen mit dem,
was sie anderswo kostet. *Im Projekt:* Jeder hellere Welt-Bodenpunkt neben dem Haus kostet Abend-Kontrast. Den ganzen
Boden aufzuhellen brachte an der Plattenkante je verlorenem Kontrastpunkt etwa halb so viel wie der Übergang zum fernen
Boden — darum wurde der Übergang gewählt (Protokoll 74 §252).

**Dunst (am Horizont)** — In der Ferne wird alles heller und nimmt die Farbe des Himmels an, weil Luft zwischen Auge und
Gegenstand liegt. *Im Projekt:* Der Welt-Boden geht in den letzten 6 Grad unter dem Horizont weich in die Horizontfarbe über
(`stimmung.BODEN_DUNST_GRAD`) — statt einer harten Kante zwischen Boden und Himmel (Protokoll 74 §250).

**Laufzeit-Zustand (flüchtiger Zustand)** — Was ein Programm nur im Arbeitsspeicher hält, solange es läuft, und nirgends
ablegt. Schliesst man das Fenster oder lädt die Seite neu, ist es weg. *Wozu:* Für alles, was nur jetzt gilt (ein Lauf,
der gerade rechnet), ist das richtig — es soll nicht in die Datei und nicht in Rückgängig. *Im Projekt:* Die Läufe am
Render-Knoten (`useVisRuntime.laeufe`) sind Laufzeit. Darum stand nach dem Öffnen einer Mappe «Bild erscheint hier», obwohl
das Bild in der Mappe lag (Protokoll 74 §254).

**Letzter Lauf (am Render-Knoten)** — Die Kennung des zuletzt fertig gewordenen Auftrags eines Render-Knotens, als
Einstellung am Knoten im Graph abgelegt (`letzterLauf`). *Wozu:* Der Graph wird mit der Mappe gesichert; so weiss der
Knoten nach dem Öffnen, welches Bild seines ist, und holt es wieder (aus der Mappe, auch ohne Heim-PC). Abgelegt ohne
Rückgängig-Schritt, weil es kein Schritt des Architekten ist. *Im Projekt:* `letzter-lauf.ts` im Vis-Werkzeug (Protokoll 74
§254).

**Geländefläche als Geländeelement (`IfcGeographicElement` mit «TERRAIN»)** — In einer IFC-Datei die Klasse für alles,
was zur Landschaft gehört: Bäume, Hecken — und, wenn der vordefinierte Typ «TERRAIN» (Gelände) daran steht, die
Geländefläche selbst. *Warum das eine eigene Regel braucht:* Dieselbe Klasse trägt Bäume, die nicht zum Bauwerk und nicht
zum Boden gehören (Umfeld). Erst der Typ «TERRAIN» (oder ein Geländewort in Unterart oder Name) macht daraus Boden. *Im
Projekt:* Seit dem 23.10.2026 schreibt die Umwandlung IFC → glb dann die Rolle «ground» an den Knoten, und die
Bauwerksmaske prüft Rolle und Geländename **vor** der Umfeld-Klasse; die Klasse allein bleibt Umfeld
(`ifc_to_glb_runner.ist_gelaende_element`, `maske.ist_umfeld`; Protokoll 74 §264).

**Teilmenge der Kameras (einer Grundlage)** — Eine Variante, die nur einige der Kameras ihrer Grundlage bestellt (zum
Beispiel 2 von 3). *Wozu:* Die Grundbilder dieser Kameras liegen schon da; sie neu zu rechnen kostet die ganze
Blender-Zeit (am Heim-PC 148 s statt rund 60 s). *Die Bedingung:* Jede bestellte Kamera steht in der Grundlage mit
demselben Namen und genau derselben Lage, Blickrichtung und Brennweite; bei der Auto-Kamera sind alle Werte gleich und die
Richtungen eine Auswahl aus denen der Grundlage. Eine neue oder verschobene Kamera braucht weiter eine neue Grundlage.
*Im Projekt:* `abholer.kameras_weichen_ab`, geprüft beim Anlegen (`knotenweg.grundlage_passt_nicht`) und beim Rechnen
(`abholer.lies_grundlage`); Protokoll 74 §264.

**Zugriffsrecht im Schlüsselbund** — Jeder Eintrag im Schlüsselbund des Mac merkt sich, welche App ihn ohne
Rückfrage benutzen darf; erkannt wird die App an ihrer Unterschrift. Eine App mit Behelfs-Unterschrift (ad-hoc) ist nach
jedem Update für den Mac eine «andere» App: Er fragt nach dem Passwort, oder er lässt sie gar nicht heran. *Wozu es
dient:* Ein fremdes Programm soll nicht still an Kennwörter und Schlüssel kommen. *Im Projekt:* Darum legte die Mac-App
bis 0.3.54 nach einem Update still ein neues Zertifikat an, und jedes iPad war getrennt; seither fragt sie und sagt es, wenn
neu gekoppelt werden muss (`Macidentitaetsregel`, Protokoll 74 §278). Die feste Unterschrift (Entscheid 128) soll die App
über Updates hinweg «dieselbe» bleiben lassen.

**Probe-Unterschrift** — Ein kurzes Unterschreiben eines festen Textes, nur um zu prüfen, ob ein geheimer Schlüssel
benutzbar ist. Dass ein Schlüssel im Schlüsselbund *steht*, heisst noch nicht, dass die App ihn *benutzen* darf. *Im
Projekt:* Die Mac-App macht sie beim Start mit dem Schlüssel ihres Zertifikats; gelingt sie (auch nach einer erlaubten
Rückfrage), bleibt das Zertifikat und die iPads bleiben gekoppelt (Protokoll 74 §278).

**Partitionsliste (im Schlüsselbund)** — Eine zweite Sperre am Eintrag im Schlüsselbund des Mac, seit macOS 10.12: Sie
nennt, aus welcher «Gruppe» von Programmen zugegriffen werden darf — Apple-Programme, Programme eines Apple-Entwicklerteams
oder ein einzelnes Programm. *Im Projekt:* unbelegt ist, ob eine selbst ausgestellte feste Unterschrift (Entscheid 128) hier
als stabile Gruppe zählt; am Gerät zu prüfen (Protokoll 74 §278).

**PKCS#12-Datei (.p12)** — Eine Datei, die ein Zertifikat und seinen geheimen Schlüssel zusammen trägt, meist mit einem
Passwort verschlüsselt. *Im Projekt:* So wird die feste Unterschrift der Mac-App bei GitHub hinterlegt (Entscheid 128).
Als Ablage für das Zertifikat der iPad-Leitung ausserhalb des Schlüsselbunds bewertet, aber nicht gebaut — jedes Programm
des Benutzers könnte sie ohne Rückfrage lesen (Protokoll 74 §278).

**Einzahl bei eins (Zählwort)** — Die Regel, dass ein Satz mit einer Zahl bei genau eins das Wort in der Einzahl schreibt
(«1 Bild», «1 wartet») und sonst in der Mehrzahl («0 Bilder», «3 Bilder»). *Wozu es dient:* Ein Programm, das Sätze aus
Zahlen zusammensetzt, schreibt sonst «1 Bilder» — und gerade die Vorführung arbeitet oft mit einer Kamera und einem Bild.
*Im Projekt:* im Rechenkern `sprache.zaehlwort` (Protokoll 74 §276), in der Knotenansicht `mitZahl` (`modules/vis/einzahl.ts`);
eine Probe sucht dort nach einer Zahl direkt vor einem festen Mehrzahlwort (Protokoll 74 §279).

**Modus-Marke (Plakette am Bild)** — Ein kleines Schild an einem gerechneten Bild, das sagt, dass es nicht so entstand wie
bestellt: «Ohne Grundlagenbild» (die KI hatte das gerechnete Grundbild nicht als Vorlage) oder «Anders gerechnet». *Wozu es
dient:* Ein Bild sieht man nicht an, auf welchem Weg es entstand; die Marke steht darum neben der Güte-Marke «Vorschau» an
jedem Render-Bild. *Im Projekt:* `ModusMarke.tsx`, `modus-marke.ts` in der Knotenansicht (Protokoll 74 §279).

**Ausklapper (an der Claude-Marke)** — Ein kleines Feld, das aufgeht, wenn man auf eine Marke klickt, und wieder zugeht,
wenn man daneben klickt oder Esc drückt. *Wozu es dient:* Einstellungen, die man selten braucht, stehen nicht dauernd im Bild,
sind aber mit einem Klick da. *Im Projekt:* An der Marke «Claude verbunden» unten links in der Knotenansicht klappt
«Mitschauen und Bedienen» auf — die Schalter je Agent, die Vollautomatik und ein Satz je Modus (`ModusSchalter` in
`kosmovis/apps/visbox-knoten/src/kopf.tsx`, Protokoll 74 §282).

**Spaltenraster (in einer Bildschirmfläche)** — Eine Regel, die eine Fläche in gleich breite Spalten teilt und die Teile
darin der Reihe nach einsortiert. *Wozu es dient:* Gleichartiges steht ordentlich nebeneinander, ohne dass jedes Teil seine
Lage selbst kennt. *Die Falle:* Liegt ein Raster in der Spalte eines anderen Rasters, bekommt jedes Teil nur einen Bruchteil
der Breite — Wörter brechen dann Buchstabengruppe für Buchstabengruppe um. *Im Projekt:* So lagen die Schalter von
«Mitschauen und Bedienen» am Mac (0.3.54) über ihren Wörtern; die Hülle ist seither eine einfache Spalte (Protokoll 74 §282).

**Gleitendes Fenster (beim Zählen)** — Gezählt wird immer über die letzten 60 Minuten von jetzt an zurück, nicht über die
volle Uhrstunde. *Wozu es dient:* Bei der vollen Stunde könnte man um 10:59 fünf und um 11:00 noch einmal fünf Läufe
starten — zehn in zwei Minuten. Gleitend wird ein Platz erst frei, wenn der älteste Lauf eine Stunde alt ist; darum
nennt der Heim-PC «wieder frei ab 11:42». *Im Projekt:* Grenze der Vollautomatik, `knotenweg.voll_stand`
(Entscheid 146, Protokoll 74 §283).

**Ansage-Kopf (X-Visbox-Ohne-Klick)** — Eine Zusatzzeile, die die Mac-App beim Bestellen eines Bildes mitschickt, wenn
die Vollautomatik an ist. *Wozu es dient:* Der Heim-PC weiss so, dass er den Auftrag ohne «Freigeben» starten **darf** —
ob er es tut, entscheidet er selbst (Grenze je Stunde, Lizenz des Bildmodells). Die Knotenansicht kann diese Zeile nicht
setzen; die Mac-App reicht von ihr nur drei harmlose Zeilen weiter. *Im Projekt:* `Knotenwege.ohneKlickKopf`,
`knotenweg.KOPF_OHNE_KLICK` (Entscheid 146).

**Grundlage rendern (als Werkzeug)** — Der Knopf am Render-Knoten, der nur Blender rechnen lässt (das Modell mit Licht,
Tiefe und Materialien, ohne KI), damit danach Varianten auf genau diesem Bild aufbauen. Seit dem 24.10.2026 kann auch
Claude oder der Assistent ihn auslösen: Werkzeug `vis_grundlage`, mit derselben Regel wie ein Bild (Karte, oder in Voll
ohne Klick). *Im Projekt:* `grundlage-werkzeug.ts` in der Knotenansicht (Entscheid 146).

**Stapelreihenfolge (z-index)** — Eine Zahl an einem Element einer Webseite, die sagt, was oben liegt, wenn sich zwei
Dinge auf dem Bildschirm überdecken: die grössere Zahl liegt vorn. *Wozu es dient:* Bedienflächen wie die Legende oder
eine Insel sollen über der Zeichnung liegen, nicht darunter. *Die Falle:* Die Zahl gilt nur gegen Nachbarn im selben
Stapel (siehe **Stacking-Context**) — eine grosse Zahl hilft nichts, wenn das Element in einem tieferen Stapel steckt.
*Im Projekt:* Die zentrale Tafel der Stufen steht in `kosmovis/packages/kosmo-ui/src/tokens.ts` (`zEbene`).

**Stacking-Context (Stapel)** — Eine Gruppe von Elementen einer Webseite, die der Browser als **ein** Blatt in den
Stapel legt: Was innen liegt, wird zuerst unter sich geordnet und dann als Ganzes an seinem Platz einsortiert. Ein
solcher Stapel entsteht zum Beispiel, wenn ein Element verschoben oder vergrössert wird (`transform`) oder eine eigene
Stapelzahl bekommt. *Wozu es dient:* Er hält zusammen, was zusammengehört — die Knoten einer gezoomten Leinwand bleiben
unter sich. *Die Falle:* Zwei Flächen im **selben** Stapel entscheiden nur über ihre Zahlen; liegt eine feste Fläche
eine Stufe unter etwas, das mit der Leinwand wandert, verschwindet sie dahinter, sobald es sich darüber schiebt.
*Im Projekt:* Genau so lag die Porttyp-Legende (20) unter dem Beiblatt am Render-Knoten (25) — der Fehler aus Visbox
0.3.54 (Protokoll 74 §284).

**Ebene über der Leinwand (Overlay-Ebene)** — Eine durchsichtige Schicht, die die ganze Knotenansicht deckt und die
festen Bedienflächen trägt — Legende, Kuratier-Knopf, Kuratier-Fläche. Sie liegt **neben** der verschobenen und
gezoomten Leinwand, nicht in ihr, und bildet ihren eigenen Stapel mit einer Stufe über allem, was mit der Leinwand
wandert, und unter den Inseln. Die Schicht selbst nimmt keine Klicks an, nur ihre Flächen. *Wozu es dient:* Owner-Regel
vom 24.10.2026: feste Bedienflächen geraten bei keinem Zoom hinter Inhalte der Arbeitsfläche. *Im Projekt:*
`.vis-ueber-leinwand` in `NodeCanvas.tsx`/`vis-visual.css`, Stufe `VIS_UEBER_LEINWAND` in der Tafel (Protokoll 74 §284).

**elementFromPoint (Trefferprobe)** — Eine Frage, die man dem Browser stellen kann: «Welches Element liegt an diesem
Bildschirmpunkt zuoberst?» — dasselbe Element, das ein Klick dort treffen würde. *Wozu es dient:* Ob eine Fläche
sichtbar vorn liegt, lässt sich am Code allein nicht sicher sagen; die Trefferprobe misst es so, wie es der Zeiger
erlebt. *Im Projekt:* `tools/ueber_leinwand_probe.py` schiebt bei Zoom 0,25 bis zur höchsten Stufe einen Knoten und
das Beiblatt unter jede feste Fläche und fragt an ihrer Mitte nach; `tests/test_ueber_leinwand.py` führt sie in der
Prüfstrecke (Protokoll 74 §284).

**3D-Asset (freies 3D-Modell)** — Ein fertiges dreidimensionales Ding, das jemand modelliert und zum Gebrauch
freigegeben hat: ein Baum, ein Busch, ein Auto, samt seinen Oberflächenbildern. *Wozu:* Was nicht selbst gezeichnet
werden soll, aber ins Bild gehört — das Umfeld des Hauses —, kommt so als echte Form in die Grundlage, statt dass die KI
es erfinden muss (Entscheid 97a). *Im Projekt:* der Knoten «Umfeld» (`aiimaging.umfeld`, Katalog `ASSETS`); nur
Assets unter **CC0**, aus drei Quellen: Poly Haven, Kenney, ambientCG. Die Dateien liegen nur am Heim-PC.

**CC0 für 3D-Modelle** — Dieselbe Gemeinfreiheitserklärung wie bei Texturen und Himmelsbildern (Entscheid 107), aber
für Modelle. *Warum ein eigener Eintrag:* Die Freigabe des Owners galt bis zum 24.10.2026 ausdrücklich nur für
Bilddaten; mit **Entscheid 147** (24.10.2026) gilt sie auch für 3D-Modelle — aber nur aus drei Quellen (Poly Haven,
Kenney, Quaternius), kein CC-BY, kein Sketchfab. *Im Projekt:* `umfeld.pruefe_lizenz` weist jedes Asset und jede Quelle
ab, die nicht CC0 oder nicht zugelassen ist — vor jedem Laden; der Heim-PC lädt von sich aus
(`AIIMAGING_UMFELD_MODELLE=0` stellt ab); Abschnitt «3D-Modelle (Umfeld)» im `NOTICE`.

**Platzierung (Streuung)** — Das Verteilen vieler gleichartiger Stücke über eine Fläche nach Regeln: wie dicht, wie
weit auseinander, wo nicht. *Wozu:* Zwei Bäume von Hand zu setzen ist leicht, zwanzig nicht — und von Hand landet einer
vor dem Eingang. *Im Projekt:* der Platzierungsplan `umfeld.plane`: rein rechnend, mit einem **Startwert** wiederholbar
(«Neu würfeln» am Knoten zieht den nächsten); nie im Haus, mindestens 2 m davon entfernt, nie im **Sichtkegel**, Bäume
und Büsche auf der Höhe des Geländes, Autos auf der Strasse.

**Sichtkegel (einer Kamera auf das Haus)** — Im Grundriss die Fläche zwischen dem Standpunkt einer Kamera und dem Haus,
durch die die Kamera das Haus sieht — ein Dreieck bzw. Fächer vom Auge zu den Hausecken. *Wozu:* Was dort steht, verdeckt
das Haus; und gemessen wird in diesem Projekt am Haus (Deckung, Umriss). Der Plan des Umfelds lässt diese Fläche darum
frei, mit einem Meter Rand. *Im Projekt:* `umfeld.sichtkegel`, geprüft in `tests/test_umfeld.py`.

**Zwischenspeicher der Modelle (am Heim-PC)** — Der Ordner, in den der Heim-PC geladene Modelle und Texturen legt,
jedes mit einem Zettel über Herkunft, Lizenz und Prüfsumme (`herkunft.json`). *Wozu:* Ein Baum wird einmal geladen und
dann immer wieder benutzt — auch ohne Netz. Er liegt nie im Repo (Regel 3). *Im Projekt:* `AIIMAGING_UMFELD_ORDNER`,
`umfeld.hole_asset`; abgegrenzt vom **Zwischenspeicher (Cache) einer Rechenkette**, der Ergebnisse aufhebt, nicht
Rohstoffe.

**Umkreis (des Umfelds)** — Wie weit um das Haus herum der Knoten «Umfeld» ausstattet: die halbe grösste Hausseite,
mindestens 20 m, höchstens 60 m. *Wozu:* Ein Situationsmodell kann ein halbes Kilometer gross sein; Bäume über die ganze
Fläche stünden ausserhalb des Bildes. *Im Projekt:* `umfeld.UMKREIS_MIN_M`, `UMKREIS_MAX_M`, im Plan `umkreis_m`.

**Sichtbar ausstatten (Grundlage mit und ohne Umfeld)** — Eine Grundlage mit Bäumen und Autos ist ein anderes Bild als
dieselbe ohne. *Wozu der Begriff:* Eine KI-Variante darf nur auf einer Grundlage mit demselben Umfeld rechnen, sonst
stünde ihr Bild neben dem falschen Grundbild. *Im Projekt:* `abholer.GRUNDLAGE_MUSS_PASSEN` führt `umfeld`; drüben
zählt der Stand der Grundlage das Umfeld mit.

**Situationsmodell** — Ein 3D-Modell nicht eines Hauses, sondern eines ganzen Orts: mehrere Gebäude, Gelände,
manchmal Strassen, oft hunderte Meter gross und dabei flach. Architekturwettbewerbe liefern es als Grundlage, damit
alle Teilnehmenden ihren Entwurf in dieselbe Umgebung setzen. *Wozu der Begriff:* Für ein Haus ist der Blick in
Augenhöhe richtig; ein Ort von einem halben Kilometer zeigt sich so nur als Strich am Horizont. *Im Projekt:* Visbox
erkennt es an der Grösse der Bauteile (breiter als 80 m, tiefer als 40 m, höchstens 15 % so hoch wie breit),
`kameras.ist_situationsmodell`, und stellt dann die Vogelschau.

**Vogelschau (Vogelperspektive)** — Ein Blick schräg von oben, wie ihn ein Vogel oder eine Drohne hätte: Die Kamera
steht hoch über dem Ort und schaut in einem Winkel von etwa 30 bis 45 Grad hinunter. *Wozu:* Man sieht, was wo steht,
und die Gebäude bleiben trotzdem als Körper mit Fassaden lesbar. *Im Projekt:* `kameras.vogelschau` — Ziel ist die
Mitte der Bauteile, der Abstand ist der kleinste, bei dem alles mit Rand ins Bild passt; die automatischen Kameras
eines Situationsmodells heissen `vogelschau-<Richtung>`. Sie gilt als **Aufsicht** (gewollt von oben, kein Fehler).

**Draufsicht (Plan von oben)** — Die steilste Vogelschau: fast senkrecht von oben, sodass das Bild wie ein Lageplan
aussieht. Genau senkrecht wird nicht gerechnet, weil dann «oben im Bild» unbestimmt wäre; bei 89 Grad aus Süden liegt
Norden oben. *Im Projekt:* `kameras.DRAUFSICHT_GRAD`, Werkzeug `tools/vogelschau.py --draufsicht`.

**Rasterzellen der Draufsicht (A1 bis D4)** — Ein Gitter aus vier Spalten A–D und vier Zeilen 1–4 über dem Planbild, wie auf
einem Stadtplan. *Wozu:* Der Owner kann mit einem Klick sagen «das Hauptgebäude liegt in B3», ohne Koordinaten zu
kennen; das Programm rechnet die Zelle auf den Boden zurück und stellt eine Vogelschau genau darauf. Liegt das Gesuchte
auf einer Grenze, nimmt man ein **Gebiet** aus mehreren Zellen, geschrieben «B2:C3» (von B2 bis C3, also vier Zellen).
*Im Projekt:* `kameras.rasterzelle_bereich`, `tools/vogelschau.py raster`.

**Sichtweite einer Kamera (Clipping-Ende)** — Wie weit eine Renderkamera sieht. Was weiter weg liegt, wird nicht
gezeichnet — weder im Bild noch in der Tiefenkarte, und zwar ohne Fehlermeldung. Die Rechenprogramme haben dafür
eine Vorgabe, die für ein Haus reicht, für einen ganzen Ort aus der Höhe aber nicht. Dasselbe wie die hintere
**Schnittebene** im 3D-Fenster, nur in Blender. *Im Projekt:* seit dem 24.10.2026 rechnet Visbox sie aus Grösse der
Szene und Standpunkt (`kameras.sichtweite`, `_sichtweite_setzen` im Blender-Lauf) — nur verlängert, nie gekürzt —
und schreibt sie in den Bericht (`kamera.sichtweite`).

**Grundriss-Cluster (die Bauten eines Situationsmodells)** — Bauteile, die sich im Grundriss berühren oder bis auf
1,5 m nahekommen, werden zu einem Bau zusammengefasst — so wie man auf einem Lageplan die Umrisse der Häuser sieht und
nicht jede Decke einzeln. Ist ein solcher Haufen weniger als 1 m hoch, ist er ein Belag (Platz, Weg), kein Bau.
*Wozu:* Ein Wettbewerbsmodell liefert oft nur Platten; als «Haus» galt bis dahin die Box aller Platten, also fast die
ganze Anlage, und für Bäume blieb kein Platz. *Im Projekt:* `umfeld.grundriss_cluster`; der Plan stellt im
Situationsmodell nur bei den Bauten, die die Kamera sieht, und hält den Blick auf den grössten davon frei.

**Ganz im Bild (Bildrahmen-Prüfung)** — Ob ein gestelltes Stück vollständig innerhalb des Bildausschnitts einer Kamera
liegt, mit etwas Rand — geprüft an seinen Ecken, mit derselben Rechnung wie die Kamera in Blender (siehe **Frustum
(Sichtpyramide)**). *Wozu:* Ein Auto, das der Bildrand halb abschneidet, wirkt wie ein Fehler. *Im Projekt:*
`umfeld.kamera_rahmen`, `umfeld.lage_im_bild` (ganz, angeschnitten, verdeckt hinter dem Haus, ausserhalb); findet
sich auf der Strasse kein Platz ganz im Bild, wird das Auto **neben dem Haus parkiert** oder fällt mit einem Satz weg.

**Wurzel und Variante (einer Modelldatei)** — Eine 3D-Datei ist ein Baum aus Teilen; die obersten Teile heissen
Wurzeln. Manche Sammlungen legen mehrere Fassungen desselben Dings als getrennte Wurzeln nebeneinander (Poly Haven:
drei Büsche in einer Datei), andere bauen ein einziges Ding aus mehreren Wurzeln (Kenney: Karosserie und vier Räder).
*Wozu:* Wer das verwechselt, stellt statt eines Autos ein riesiges Rad. *Im Projekt:* der Katalogvermerk
`ein_stueck` (`umfeld.ASSETS`), im Blender-Lauf `_vorlage_laden`.

**Textur-Verweis (Datei neben dem Modell)** — Ein Modell kann seine Farben in sich tragen oder nur auf eine Bilddatei
daneben zeigen («Textures/colormap.png»). Fehlt die Datei, zeichnet das Programm das Modell ohne Farbe — ohne
Fehlermeldung. *Im Projekt:* `umfeld.fehlende_bezuege` prüft jeden Verweis; fehlt etwas im Zwischenspeicher, wird es
aus dem geprüften Paket nachgeholt, sonst steht ein Satz im Ergebnis.

**Freies Bild (ohne Grundbild)** — Ein KI-Bild, das bewusst nicht vom gerenderten Grundbild ausgeht, sondern nur vom
Text (dem Prompt) und von der Tiefenkarte, die die grobe Form vorgibt. *Wozu es dient:* So kommt eine Stimmung an, die
das Grundbild nicht trägt — warmes Licht in den Fenstern, Wiese, Waldrand. Der Preis: Das Haus kann vom Modell
abweichen, Fenster und Form halten nicht sicher. Darum ist es nie die Vorgabe und trägt überall, wo es steht, die Marke
«freies Bild», damit niemand es für ein modelltreues Bild hält. *Im Projekt:* Haken «Freies Bild (ohne Grundbild)» am
Varianten-Knoten, Wort «Frei» am Render-Knoten, Bestellfeld `vis.freies_bild`, im Ergebnis `freies_bild: true` und der
Satz «FREIES BILD (Entscheid 149)» (Protokoll 74 §290).

**Bildeingang-Stärke (Vorgabe je Bildart)** — Wie viel des gerenderten Grundbilds die KI neu malen darf, als Zahl von 0
bis 1: 0,5 heisst «die Hälfte bleibt», 0,7 «mehr wird neu gemalt». Mehr Stärke lässt den Prompt besser ankommen, weniger
hält Fenster und Form genauer. *Im Projekt:* Eine Variante rechnet ohne eigene Angabe mit 0,7 (Entscheid 149, gemessen in
Auftrag 353: bis 0,7 halten Fenster und Form), auf einem Situationsmodell (einer ganzen Anlage) aber mit 0,5, weil dort die
kleinen Baukörper bei 0,7 zerfallen; das erste Bild aus dem Render-Knoten mit 0,5 (Entscheid 138); eine eigene
Stärke gewinnt immer. Steht im Ergebnis unter `angewandt.messschalter.bildeingang` mit der Herkunft («vorgabe»,
«vorgabe_situationsmodell», «bestellt», «freies_bild»). Siehe auch **Bildeingang mit Stärke**.

## Änderungsverzeichnis

| Datum | Änderung |
|---|---|
| 2026-10-24 | Ergaenzt aus Ergebnis 358 zum Knoten «Umfeld» (Protokoll 74 §288, Nachtrag; Auftrag 359): **Grundriss-Cluster (die Bauten eines Situationsmodells)**, **Ganz im Bild (Bildrahmen-Prüfung)**, **Wurzel und Variante (einer Modelldatei)**, **Textur-Verweis (Datei neben dem Modell)** |
| 2026-10-24 | Ergaenzt aus Entscheid 149 (Protokoll 74 §290, Auftrag 357): **Freies Bild (ohne Grundbild)**, **Bildeingang-Stärke (Vorgabe je Bildart)** |
| 2026-10-24 | Ergaenzt aus dem Situationsmodell (Protokoll 74 §289, Auftrag 356): **Situationsmodell**, **Vogelschau (Vogelperspektive)**, **Draufsicht (Plan von oben)**, **Rasterzellen der Draufsicht (A1 bis D4)**, **Sichtweite einer Kamera (Clipping-Ende)** |
| 2026-10-24 | Ergaenzt aus dem Knoten «Umfeld» (Protokoll 74 §288, Auftrag 355): **3D-Asset (freies 3D-Modell)**, **CC0 für 3D-Modelle**, **Platzierung (Streuung)**, **Sichtkegel (einer Kamera auf das Haus)**, **Zwischenspeicher der Modelle (am Heim-PC)**, **Sichtbar ausstatten (Grundlage mit und ohne Umfeld)**, **Umkreis (des Umfelds)** |
| 2026-10-24 | Ergaenzt aus Befund F4 «Bild aus Skizze» (Protokoll 74 §287): **Gewünschter Name (einer Skizze)**, **Bestelltes Bildwerkzeug**; nachgeführt **Anweisung (an eine Skizze)** |
| 2026-10-24 | Ergaenzt aus dem Neutralisieren einer IFC (Protokoll 74 §286, Auftrag 354): **Neutralisieren (eines Modells)**, **Schwärzen (von Beschriftungen)**, **Anmerkung (`IfcAnnotation`)**, **Eigenschaftssatz (Property Set)**, **Restprüfung (Resttexte)**; nachgeführt **GUID** (neu vergeben beim Neutralisieren), **Georeferenzierung** (zwei Stellen in der IFC, Landeskoordinaten in der Geometrie); Nachtrag §286: **Landeskoordinaten**, **Lokaler Ursprung (Modell an den Ursprung schieben)** |
| 2026-10-24 | Ergaenzt aus der Ebene über der Leinwand (Protokoll 74 §284, Owner-Regel feste Bedienflächen): **Stapelreihenfolge (z-index)**, **Stacking-Context (Stapel)**, **Ebene über der Leinwand (Overlay-Ebene)**, **elementFromPoint (Trefferprobe)** |
| 2026-10-24 | Ergaenzt aus «Vollautomatik ohne Klick» (Protokoll 74 §283, Entscheid 146): **Gleitendes Fenster (beim Zählen)**, **Ansage-Kopf (X-Visbox-Ohne-Klick)**, **Grundlage rendern (als Werkzeug)**; nachgeführt **Selbständigkeit**, **Vollautomatik** |
| 2026-10-24 | Ergaenzt aus «Mitschauen und Bedienen» (Protokoll 74 §282): **Ausklapper (an der Claude-Marke)**, **Spaltenraster (in einer Bildschirmfläche)** |
| 2026-10-24 | Ergaenzt aus dem Tafel-Abteil zur iPad-App (Protokoll 74 §281): **Gezeichnetes Schema (Drawn schematic)**; nachgeführt **Erklärkarte (je Knoten, je iPad-Bereich)** |
| 2026-10-24 | Ergaenzt aus dem Demolauf zur Nähe-Kopplung (Protokoll 74 §280): **Einladung und Sitzung (MCSession)**, **Platzhaltertext (eines Eingabefeldes)**; nachgeführt **Nähe-Verbindung (MultipeerConnectivity)** (Verbindung vor der Frage am Mac) |
| 2026-10-24 | Ergaenzt aus «1 Bild» und dem Nachzug der Knotenansicht (Protokoll 74 §279): **Einzahl bei eins (Zählwort)**, **Modus-Marke (Plakette am Bild)** |
| 2026-10-24 | Ergaenzt aus dem Mac-Update-Befund (Protokoll 74 §278): **Zugriffsrecht im Schlüsselbund**, **Probe-Unterschrift**, **Partitionsliste (im Schlüsselbund)**, **PKCS#12-Datei (.p12)**; nachgeführt **Schlüsselbund** (Zertifikat und Schlüssel der iPad-Leitung) |
| 2026-10-24 | Ergaenzt aus Ergebnis 347 (Protokoll 74 §274): **Deckung im Haus (Messbereich)**, **Ladezeit des Bildmodells**; nachgeführt **Deckungsschwelle** und **Kanten-IoU** (nur im Haus, Schwelle 0,25) |
| 2026-10-24 | Ergaenzt aus Ergebnis 346 (Protokoll 74 §272): **Farbton (Blau minus Rot)**, **Vegetationswörter (Umfeld am Namen)**; nachgeführt **Fenster gehalten** (Fassung v2) und **Umfeld** |
| 2026-10-23 | Ergaenzt aus der Geraeteprobe R59 (Protokoll 74 §273): **Punktwolke oder Splat (am Dateikopf erkannt)** |
| 2026-10-23 | Ergaenzt aus dem Mac-Befund «haus-am-hang» (Protokoll 74 §270): **Fenster gehalten (Prüfung am KI-Bild)**, **Glassatz (Messschalter)**, **Nennungen des Stoffs vorne**, **Bildraster des KI-Schritts (Umrechnen der Bildgrösse)** |
| 2026-10-23 | Nachgeführt aus dem iPad-Demolauf (Protokoll 74 §268): **Simulator** (im Simulator-Bau zeichnet jede Berührung, am Gerät nur der Stift) |
| 2026-10-23 | Ergaenzt aus den Erklärkarten je Knoten (`docs/KNOTEN_ERKLAERT.md`, Protokoll 74): **Erklärkarte (je Knoten)**, **Typische Kette (der Knoten)**, **Ehrliche Grenze (auf einer Erklärkarte)** |
| 2026-10-23 | Ergaenzt aus Ergebnis 345, Nachtrag S7 (Protokoll 74 §267): **Auskunft (im Befund, gegen Warnung)**; nachgeführt: **Kontrast am Umriss** (Schalter `kaum_sichtbar`) |
| 2026-10-23 | Ergaenzt aus der Geraeteprobe R57 (Protokoll 74 §266): **Vollautomatik** |
| 2026-10-23 | Ergaenzt aus der Geraeteprobe R56 (Protokoll 74 §264): **Geländefläche als Geländeelement (`IfcGeographicElement` mit «TERRAIN»)**, **Teilmenge der Kameras (einer Grundlage)** |
| 2026-10-23 | Ergaenzt aus Ergebnis 343 (Protokoll 74 §262): **Gelände in der Nähe**, **Reihenfolge der Bezüge (Augenhöhe)**, **Kontrast am Umriss** |
| 2026-10-23 | Ergaenzt aus Ergebnis 341, Abstand «Eingang» (Protokoll 74 §261): **Bildkegel**, **Abstand aus Bildwinkel (mit Rand)** |
| 2026-10-23 | Ergaenzt aus den Ergebnissen 341 und 342 (Protokoll 74 §260): **Gelände am Standpunkt (gemessen)**, **Warnung des ganzen Satzes (gegen Warnung je Kamera)**, **Doppelter Prompt-Teil**; nachgeführt: **Toleranz** (Augenhöhen-Band) |
| 2026-10-22 | Ergaenzt aus den Fehlerberichten 41–45, Augenhöhe «Eingang» (Protokoll 74 §259): **Augenhöhe (einer Kamera)**, **Bodenbezug (Referenzpunkt der Augenhöhe)** (mit Weltnull und OKFF), **Geländefläche und Schürze** |
| 2026-10-22 | Ergaenzt aus Ergebnis 340, Licht der Variante (Protokoll 74 §258): **Stimmungswort (im Prompt)**; nachgeführt: **Stimmung der Variante (eigene Grundlage)** (auch bei anderem bestelltem Licht, Bericht im Ergebnis) |
| 2026-10-22 | Ergaenzt aus Entscheid 138 und Ergebnis 339 (Protokoll 74 §256): **Zurückgezogene Vorgabe (beim Bildeingang)**, **Deckungsschwelle**; nachgeführt: **Bildeingang mit Stärke** (Vorgabe 0,5 für Varianten), **Vorgabe für Varianten** (vierter Wert), **Deckungsgleiche Varianten** (Schwelle 0,25), **Rückfall auf txt2img** |
| 2026-10-22 | Ergaenzt aus der Mac-Prüfliste 0.3.41, Bild nach dem Öffnen (Protokoll 74 §255): **Laufzeit-Zustand (flüchtiger Zustand)**, **Letzter Lauf (am Render-Knoten)** |
| 2026-10-22 | Ergaenzt aus Ergebnis 337, Stoff-Variante (Protokoll 74 §254): **Stoff-Variante (Material der Variante)**, **Stofffamilie**, **Fassadenwort und Nicht-Wand-Wort (beim Stoffwunsch)**; nachgeführt: **Material vorne** (die Materialwahl gewinnt, der Wunsch einer Variante ersetzt sie zuerst) |
| 2026-10-22 | Ergaenzt aus Ergebnis 336, Abend-Naht (Protokoll 74 §252): **Naher und ferner Boden**, **Wirkungsgrad einer Korrektur (Gewinn je Kosten)**; nachgeführt: **Naht (an der Plattenkante)** (Ergebnis 336) |
| 2026-10-22 | Ergaenzt aus Ergebnis 336, Variantenweg (Protokoll 74 §253): **Rückfall auf txt2img (beim Bildmodell)**; nachgeführt **img2img** (Gegenstück txt2img, `angewandt.ki.modus`) und **Denoise-Stärke** (wirksamer Wert, `angewandt.ki.denoise`) |
| 2026-10-22 | Ergaenzt aus Ergebnis 335, Boden wie die Platte (Protokoll 74 §251): **Beleuchtungsstärke (Licht auf einer Fläche)**, **Selbstleuchtend (emissiv)**, **Naht (an der Plattenkante)**; nachgeführt: **Boden bis zum Horizont (Welt-Boden)** (Licht der Platte, abends dämmrig) |
| 2026-10-22 | Ergaenzt aus Ergebnis 334, Boden bis zum Horizont (Protokoll 74 §250): **Reiner Himmel («puresky»-Himmelsbild)**, **Albedo (Rückstrahlvermögen)**, **Boden bis zum Horizont (Welt-Boden)**, **Dunst (am Horizont)**; nachgeführt: **Kontrast Haus–Hintergrund** (am KI-Bild), Zweitmeinung (`entschieden_durch` «name» auf beiden Wegen) |
| 2026-10-22 | Ergaenzt aus Ergebnis 333, Himmel zur Stimmung (Protokoll 74 §249): **Himmelsgrenze (Untergrenze des sichtbaren Himmels)**, **Helle und dämmrige Stimmung**; nachgeführt: **Toleranz (bei einem Vergleich zweier Messwerte)** |
| 2026-10-22 | Ergaenzt aus der Mac-Prüfliste 0.3.35 (Protokoll 74 §248): **Ausgelagertes Raster (im Befund)**, **Voller Auftrag (Grundbild und KI in einem)** |
| 2026-10-22 | Ergaenzt aus dem Mac-Demolauf «Haus am Hang» (Protokoll 74 §246): **Weg nur der App (App-Weg)**, **Stumme Absage (404 als «nichts zu tun»)**, **Bildnachlese (Mappe am Mac)** |
| 2026-10-22 | Ergaenzt aus N6, N5, Glas und Bericht (Protokoll 74 §247): **Stimmung der Variante (eigene Grundlage)**, **Bauteil ohne Art**, **Benanntes Material (aus der Datei)**, **Rauheit (eines Materials)**, **Ohne Bauteil / nur behalten (im Materialbericht)**, **Lichtsaum (um das Haus)**; nachgeführt: **Bauteil-Art** (Wort im Namen) |
| 2026-10-22 | Ergaenzt aus dem Mac-Befund 0.3.35, Knotenschrift jittert (Protokoll 74 §245): **Schärfen in der Ruhe (Raster der Knotenansicht)**, **SVG-Schrift in Bildschirmgrösse**, **Lineare Schriftauslegung**; nachgeführt: **Neu auslegen gegenüber als Ganzes verkleinern (beim Zoomen)** |
| 2026-10-22 | Nachgeführt aus dem Kleinauftrag «zwei Zeichen» vor der Demo (Entscheide 132/133, Protokoll 74 §244): **Lot (Senklot)** (jetzt gebaut), **Kugel des Assistenten (Orb)** (zeigt in Visbox das Lot) |
| 2026-10-22 | Ergaenzt aus dem Owner-Nachtrag zu Blatt 55 (Blatt 55a, Protokoll 74 §243 Nachtrag): **Anschluss-Seite (eines Knotens)** |
| 2026-10-22 | Ergaenzt aus der Owner-Verbesserungsliste Visbox (Blätter 51–56, Protokoll 74 §243): **Werkzeugrad (am iPad)**, **Glättung (eines Strichs)**, **Lasso (Zeichenwerkzeug)**, **Pipette**, **Insel-Oberfläche (am iPad)**, **Art der Unterlage**, **3D-Skizze**, **Zeichnungsart**, **Texterkennung (auf dem Gerät)**, **Sehmodell**, **Weg A und Weg B**, **Planfarben (Gelb-Rot-Plan)**, **Herkunft (einer Variante)**, **Tafel (je Projekt)**, **Materialpass**, **Zone (der Knotenansicht)**, **Maschine**, **Stil-Eingang (am Kombinierer)**, **Auto-Standpunkte (über Eck)** |
| 2026-10-22 | Ergaenzt aus den Verlusten der IFC-Umwandlung im Mac-Demolauf (Protokoll 74 §242): **Teil eines Bauteils (Zusammenfassung in der IFC)**, **Füllung (eines Ausschnitts)**, **Vordefinierter Typ (eines IFC-Bauteils)**, **Art-Merkmal am Knoten (`extras.kind`)**; **Durchlass (eines Materials)** nachgeführt (kommt jetzt auch aus der IFC) |
| 2026-10-22 | Ergaenzt aus dem Mac-Demolauf 0.3.33, «Freigeben» ohne Wirkung (Protokoll 74 §239): **Stummer Ausgang (einer Bedienung)**, **Wartender Auftrag (auf Freigabe)** |
| 2026-10-22 | Ergaenzt aus dem Mac-Demolauf «Skizze vom iPad bis zum Bild» (Protokoll 74 §241): **Kartenzone (der KI-Maus)**, **Lese-Kennung (L-n)**, **Bild aus Skizze erzeugen** |
| 2026-10-22 | Ergaenzt aus Entscheid 131 (K-10, Protokoll 74 §238): **Kartenzeile (eines Vorschlags)**, **Vorher → Nachher (auf der Karte)**; **Erzählzeile** nachgeführt (ohne Knöpfe) |
| 2026-10-22 | Ergaenzt aus dem Mac-Demolauf, drei Funde (Protokoll 74 §240): **Geduld (der Wartemeldung)**, **Schattenfänger (Boden)**, **Durchlass (eines Materials)** |
| 2026-10-22 | Ergaenzt aus dem Demolauf (Mac umbenannt, Protokoll 74 §237): **Feste Kennung (eines Geräts)**, **Namenskonflikt (Computername)**, **Gekoppelt gegenüber erreichbar**, **Neu koppeln (ohne Trennen)**; nachgefuehrt: **TXT-Eintrag** (`abdruck=…`) |
| 2026-10-22 | Ergaenzt aus dem Mac-Befund 0.3.33 zur Knotenschrift (Protokoll 74 §235): **Zoom-gebundene Schrift**, **Mindestschrift (des Browsers)**, **Neu auslegen gegenüber als Ganzes verkleinern (beim Zoomen)** |
| 2026-10-22 | Ergaenzt aus dem Mac-Befund 0.3.33, Stimmung per Werkzeug (Protokoll 74 §236): **Einzelwahl und Mehrfachwahl (am Stimmungs-Knoten)**, **«Die Liste gewinnt» (Lese-Regel am Stimmungs-Knoten)** |
| 2026-10-22 | Ergaenzt aus Blatt 50 (Protokoll 74 §234): **Detailstufe (eines Knotens)**, **Kategorie (eines Knotens)**, **Zeichnung im Massstab (Leitsatz der Knotenansicht)**, **Grundbild statt «Grundlage» (geplante Umbenennung)** |
| 2026-10-22 | Ergaenzt aus Gegenprobe 330 (Protokoll 74 §233): **Wahl aus drei Startwerten (Startwertauswahl)**, **Nachgeeichte Schätzung**, **Eingang (eines Knotens, z. B. «Bild 1/2/3» am Bildvergleich)** |
| 2026-10-22 | Ergaenzt aus den Blättern 47/48 (Protokoll 74 §232): **Glas-Kopf (am Mac-Fenster)**, **Ampel-Knöpfe (macOS)**, **Lot (Senklot)** |
| 2026-10-22 | Ergaenzt aus §231 Nachtrag und Entscheid 129: **Stand des Graphen (beim Sichern)**, **Eigene Mappe des Mac (Entscheid 129)** |
| 2026-10-22 | Ergaenzt aus dem Mac-Befund 0.3.33 (Protokoll 74 §231): **Gelesene Mappe (beim Sichern des Graphen)**, **Werkzeugliste je Sitzung (bei Claude)** |
| 2026-10-22 | Ergaenzt aus Gegenprobe 328 und Ergebnis 329 (Protokoll 74 §229): **Variante auf der Grundlage (am Varianten-Knoten)**, **Nicht entscheidbar je Kamera (`not_applicable`)**, **Dateistamm (beim Exportieren)**, **Taktgeber (des Abholers)** |
| 2026-10-22 | Ergaenzt aus Entscheid 127 (Protokoll 74 §228): **keep_alive**, **Grafikkarte freigeben (vor dem Bild)**; nachgeführt **Entladen (des Sprachmodells)** |
| 2026-10-22 | Ergaenzt aus Ergebnis 327 (Generalprobe, Protokoll 74 §226, Knotenansicht): **«Himmel» am Render-Knoten (Himmelsmodell, `render.himmel`)**, **Mappenwechsel (in der Knotenansicht)**, **Brücke (Bestellweg am Heim-PC, `/bruecke`)** |
| 2026-10-22 | Ergaenzt aus Ergebnis 327 (Generalprobe, Protokoll 74 §225, Bildweg im Kern): **Halbe M2 (Vorschau bis Fassung 0.3.31)**, **Hintergrund je Kamera (`hintergrund_je_kamera`)**; nachgeführt **Umriss halten** und **Vorgabe für Varianten** (gilt jetzt auch für die Vorschau), **Vorschau (Güte)** |
| 2026-10-22 | Ergaenzt aus dem Auftrag der Generalprobe (Protokoll 74 §224): **M2 (Einstellung für Varianten)**, **Generalprobe (der Demo-Kette)**; nachgeführt **Himmel sichtbar** (seit Entscheid 126 Vorgabe, nicht mehr «Vorgabe aus») |
| 2026-10-22 | Ergaenzt aus Strang «nach322» (Ergebnis 322, Protokoll 74 §219): **Abweisungstext (an das Sprachmodell)**, **Alltagswort (für ein Werkzeug)**, **Verneinter Satz (bei der Prüfung der Antwort)** |
| 2026-10-21 | Ergaenzt aus Strang «nach321» (Ergebnis 321, Protokoll 74 §218): **Aus der Frage übernommen (beim Assistenten)**, **Doppelte Stimmung (Stimmungs-Knoten neben dem Preset)**, **Untere Bildzeilen (bei der Bodenprüfung)**; nachgeführt **Randgrund** (Gründe ohne Fläche fallen weg) |
| 2026-10-21 | Ergaenzt aus Strang «nach320» (Ergebnis 320): **Trennhilfe (des Messbodens)**, **Erfundene Angabe (beim Assistenten)**; nachgeführt **Randgrund** (nach Fläche); Glossar «Sichtbackstein» |
| 2026-10-21 | Nachgeführt aus Strang «paket» (Protokoll 74 §216): **Paket von Schritten (`vis_paket`, «$neu:N»)** — auch die Einzelwerkzeuge nennen den Weg |
| 2026-10-21 | Ergaenzt aus Strang «nach317» (Ergebnisse 317–319): **Abgeschriebener Beispielsatz**, **Randgrund (beim Schätzen des Hausanteils)**, **Tor für Ergebnis-Commits**; nachgeführt **Deckungsgleiche Varianten** und **Kanten-IoU** (Schwelle 0,10), **Rang** (Lücken erlaubt), **Rolle am Knoten** (`name+rolle`) |
| 2026-10-21 | Ergaenzt aus Strang «modusko» (Protokoll 74 §214): **Marke «Anders gerechnet» / «Ohne Grundlagenbild»**, **Tolerant gelesen (Feld im Ergebnis)** |
| 2026-10-21 | Ergaenzt aus Strang «steine» (Protokoll 74 §211): **Ausrollen (von Instanzen)**, **Geteiltes Mesh**, **Kennfarbe (im Material-ID-Pass)**, **Rolle am Knoten (`extras.role`)** |
| 2026-10-21 | Ergaenzt aus Entscheid 126 und den Befunden von auf-20261021-314 (Protokoll 74 §210, §212): **Vorgabe für Varianten**, **Kamerakürzel und deutsches Gleichwort**, **OptiX**, **Paket von Schritten (`vis_paket`, «$neu:N»)** |
| 2026-10-21 | Ergaenzt aus Strang «modus» (Protokoll 74 §208): **KI-Bild ohne Grundlagenbild**, **Stetig gewachsen (Hausfläche im KI-Bild)**; **Kontextmaske** und **Hausanteil** nachgeführt |
| 2026-10-21 | Ergaenzt aus «Erstes Bild gross» (Protokoll 74 §206): **Modellstand (einer Grundlage)** |
| 2026-10-21 | Ergaenzt aus «Bild aufs Blatt» (Video-Befunde L4-16, L3-A4, L3-A5): **Originalauflösung**, **Bild im Projekt gesichert**, **Druckprüfung am Platz**, **Sichern-Dialog** |
| 2026-10-21 | Ergaenzt aus der Deckung (Protokoll 74 §199): **Kanten-IoU**; **Deckungsgleiche Varianten** um die Form ergaenzt |
| 2026-10-21 | Ergaenzt aus den Befunden 309/310 (Protokoll 74 §198): **Gebäudewort (im Prompt)**, **Kartenkennung**, **Anstoss (an den Assistenten)**, **Himmel sichtbar (Messschalter `vis.himmel_sichtbar`)**, **Sicherheitsrand (beim Grafikspeicher)** |
| 2026-10-21 | Ergaenzt aus Grossansicht und Vergleich (Protokoll 74 §197): **Grossansicht (eines Bildes)**, **Läufe einer Grundlage**, **Kontextmaske** |
| 2026-10-21 | Ergaenzt aus dem Video-Befund L4-2 (Protokoll 74 §195): **Hausanteil (an Grundlage und KI-Bild)**, **Abgeschnittener Wert (Geometrie 0.0)** |
| 2026-10-21 | Ergaenzt aus dem Video-Befund L4-4 (Protokoll 74 §196): **Gesicherter Blick** |
| 2026-10-21 | Nachgetragen aus Vertrag C17 A1 (Protokoll 74 §193): **Modusabweichung** — steht jetzt auch im Ergebnis jedes Bildauftrags |
| 2026-10-21 | Ergaenzt aus dem Strang Optik (Protokoll 74 §194): **Überstand (am Knoten)**, **Reiterleiste**; **Stilprobe (am Bau)** um die Knoten nachgefuehrt |
| 2026-10-21 | Ergaenzt aus Befund 308 B1 (Protokoll 74 §192): **Probename (im Gerätebuch)** |
| 2026-10-21 | Ergaenzt aus den Varianten-Daumen (Blatt 36, Protokoll 74 §189): **Bildzeile mit Blättern**, **Gewählte Variante**, **Portal (in der Oberfläche)**, **Verschachtelte Stilregel** |
| 2026-10-21 | Strang Karten, Folgeauftrag (Protokoll 74 §186): **Ablauf (einer Karte)** ersetzt durch **Echtes Beenden (der Arbeit mit Claude)**; neu **Leitung unterbrochen (Vermerk)** |
| 2026-10-21 | Ergaenzt aus dem Strang Stil (Protokoll 74 §188): **Stilprobe (am Bau)** (CSS und offene Klammer stehen seit §187) |
| 2026-10-21 | Ergaenzt aus Entscheid 119 (Protokoll 74 §185): **Innenbreite (eines Knotens)**; **Grundbild** um die breitere Karte nachgefuehrt |
| 2026-10-21 | Ergaenzt aus dem Strang Karten (Protokoll 74 §184): **Kartenablage (offene Vorschläge in der App)**, **Zurückgeben (einer Karte, mit neuer Probe)**, **Ablauf (einer Karte)**, **Passt nicht mehr (Karte)** |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261021-302 und -303 (Strang Kern, Protokoll 74 §182): **Urteil nach dem Halten**, **Nennung eines Stoffs**, **Unvollständiger Gewichtsordner**, **Satz der Stimmung (massgebend)**, **Halbe Übersetzung** (aus 306); **Umriss halten**, **Material vorne** und **Ohne Gradienten rechnen** um die Messung und den Bau nachgefuehrt |
| 2026-10-21 | Ergaenzt aus Entscheid 118a (Protokoll 74 §181): **Kein Rechner eingerichtet (Mac ohne Heim-PC)**; **Veraltet (ein Bild am Render-Knoten)** um den Ladestand erweitert; **HTTP-Statuscode** um `410` und **Übergangsfassung** um das Ende des direkten Wegs nachgefuehrt |
| 2026-10-21 | Ergaenzt aus dem Folgeauftrag zu den neuen Knoten (Protokoll 74 §180): **Vorgabe beim Anlegen (eines Knotens)** |
| 2026-10-21 | Ergaenzt aus Befund 304 B1 (Protokoll 74 §179): **Zuletzt geöffnete Mappe** |
| 2026-10-21 | Ergaenzt aus «Visbox eigenständig», Schritt 4 (Protokoll 74 §178): **Zertifikat des Mac (für das iPad)**, **DER (Kodierung eines Zertifikats)**, **Zertifikat-Gegenprobe (beim Koppeln)**, **Kein Rückfall auf unverschlüsselt**, **Übergangsfassung**; **Koppelschein** um Fassung 2 nachgefuehrt |
| 2026-10-21 | Ergaenzt aus den neuen Knoten in der Knotenansicht (Protokoll 74 §176): **Knoten «Oberfläche»**, **Knoten «Material»**, **Knoten «Farbpalette» (Leitfarbe)**, **Kamera-Knoten: Auto, Manuell, Modell**, **Kegel (einer Kamera im 3D-Fenster)**, **Live-Vorschau der Standpunkte**, **Grundlage je Stand**, **Führende Stimmung (bei Mehrfachwahl)**, **Vorgeschaltet (Knoten)**, **Farbverlauf statt Vorschaubild**, **Vertragsvorschlag (Schritt V)**; **Knotenkatalog** auf siebzehn nachgeführt |
| 2026-10-21 | Ergaenzt aus den Befunden von Messauftrag 305 (Protokoll 74 §187): **CSS (Stilregeln)**, **Offene Klammer (im CSS)**, **SVG (Vektorgrafik im Browser)**, **Prüfung im Kern statt Bitte** |
| 2026-10-21 | Ergaenzt aus KI-Bedienung Stufe 5 und 6 (Protokoll 74 §175): **Blick (der KI auf die Knotenansicht)**, **Maus der KI (eigener Zeiger)**, **Sperrzone (der Maus der KI)**, **Mitschauen und Bedienen (Schalter)**, **Werkzeugschleife (des Assistenten)** |
| 2026-10-21 | Ergaenzt zu Entscheid 117a (W-4, Protokoll 74 §177): **Grundbild (Grundbild mit Licht)** |
| 2026-10-21 | Ergaenzt aus «Visbox eigenständig», Schritt 3 (Protokoll 74 §174): **Mappe am Mac**, **An den Mac holen (Mappenpaket)**, **Zwillingsmappe** |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261021-301 (Protokoll 74 §172): **Modellwurzel**, **Modell-Hub (offline laden)** |
| 2026-10-21 | Ergaenzt aus dem Strang Treue (Planblatt Material und Umriss): **Umriss halten (Messschalter)**, **Freigabemaske**, **Fahrplan (der Rauschstufen)**, **Hintergrund im Fahrplan festhalten**, **Material vorne (Messschalter)**, **Gewichtung im Prompt**, **Kantenbild (Canny, HED)**, **Mehrfach-Steuerung (MultiControlNet)**, **Steuerstärke je Schritt**, **Ohne Gradienten rechnen (`torch.no_grad`)** |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261021-299 und -300 (Protokoll 74 §171): **CUDA-Kontext**, **Eigenes Assistenzmodell**, **Auslöser (eines Satzes)**, **Augenurteil** |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261021-298 (Protokoll 74 §170): **Spitze und Grundlast (beim Grafikspeicher)**, **Reserve (beim Bildeingang)**, **Fremdes Modell auf der Grafikkarte**, **Toleranz (bei einem Vergleich zweier Messwerte)**, **Beide Bilder liefern (Wahl W-4)**; **Farbabgleich**, **Bildeingang mit Stärke** und **Eigener Start** um das Messergebnis nachgefuehrt |
| 2026-10-21 | Ergaenzt zu Entscheid 117 (Protokoll 74 §168): **Kantenübereinstimmung (`kanten_iou`)**, **Bildeingang mit Stärke (Cycles-Bild und Tiefe zugleich)**, **Eigener Start (beim Bildmodell)**; **Farbabgleich (nach dem KI-Schritt)** nachgefuehrt — jetzt gebaut, fuer das ganze Bild statt je Bereich |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261021-296 (Protokoll 74 §167): **Flächenverhältnis (Haus im Bild gegen Haus im Modell)**, **Gültigkeitsvermerk der Umrisstreue (`umriss_gilt`)**, **Zusatz «leerer Hintergrund» (Messschalter)**, **Farbabgleich (nach dem KI-Schritt)**, **Unteres Quantil (25-%-Quantil)**; **Haus im KI-Bild nicht wiederzuerkennen** um die zwei neuen Auslöser nachgeführt |
| 2026-10-21 | Ergaenzt aus den Befunden von auf-20261020-295 (Protokoll 74 §164): **Mittel in Blendenstufen (geometrisches Mittel)**, **Haus im KI-Bild nicht wiederzuerkennen**, **Umriss-IoU (aus Farbe)**, **Drehung je Kamera (des Himmelsbilds)**, **Prüfbild (für eine Schwelle)** |
| 2026-10-21 | Ergaenzt aus dem Abgleich im Bau (Plan UI-Gleichheit S5, Protokoll 74 §163): **Abgleich (der Kopie mit dem Original)**, **Veraltete Spur (eines Zweigs)**, **Befehlspalette (⌘K)** |
| 2026-10-20 | Ergaenzt aus Kugel, Gesprächsfeld und Einstellungs-Insel (Plan UI-Gleichheit S3/S4, Protokoll 74 §162): **Kugel des Assistenten (Orb)**, **Gesprächsfeld (des Assistenten)**, **Antwortblase (an der Kugel)**, **Seitenfenster (des Gesprächsfelds)**, **Einstellungs-Insel**, **Gemerkte Einstellung (der Knotenansicht)**; **Nahtstelle (für einen zweiten Wirt)** um die zwei neuen Nahtstellen nachgeführt |
| 2026-10-20 | Ergaenzt aus den Befunden von auf-20261020-294 (Protokoll 74 §161): **Frontallicht**, **Sonne seitlich der Kamera (Drehung zur Kamera)**, **Gemischter Prompt**, **Neue Baumasse ausserhalb des Umrisses**; **Schattenwinkel** um den weichen Rückfall nachgeführt |
| 2026-10-20 | Ergaenzt aus den Kopfteilen der Knotenansicht (Plan UI-Gleichheit S1/S2, Protokoll 74 §159): **Kopfteile (der Knotenansicht)**, **Stationen-Palette (am Logo)**, **Speichern-Kreis**, **Zweitgruppe (des Inselkopfs)**, **Heim-PC-Chip**, **Claude-Marke**, **Erzählzeile**, **Thema (Papier, Kosmos)**, **Nahtstelle (für einen zweiten Wirt)**, **Bote «visboxWirt» (zweite Brücke)**, **UI-Ausnahme**; **Selbständigkeit**, **Tätigkeitsstrom** und **Zwei Rückgängig-Verläufe** nachgeführt (in der Knotenansicht an der Claude-Marke) |
| 2026-10-20 | Ergaenzt aus den drei Fehlern am 3D-Fenster (Protokoll 74 §160): **Metallwert (eines Materials)**, **Umgebungslicht (aus einem Raum)**, **Normale (Richtung einer Fläche)**, **Schnittebene (vorne und hinten)**, **Entzerren (eines gesicherten Graphen)** |
| 2026-10-20 | Ergaenzt aus den Befunden von auf-20261020-293 (Protokoll 74 §158): **Kontrast Haus–Hintergrund**, **Vorprobe (der Stimmung)**, **Fülllicht**, **Sonnenlampe (aus dem Himmelsbild)**, **Streiflicht**, **Schattenwinkel (Grösse der Lichtquelle)**, **Look (einer Tonwertkurve)**, **Untergrenze im KI-Schritt (kleinste lange Seite)**; **Bestellte Bildgrösse und Raster** und **Messboden** nachgeführt |
| 2026-10-20 | Ergaenzt aus der KI-Bedienung Stufe 3/4 (Protokoll 74 §156): **KI-Werkzeugsatz (der Knotenansicht)**, **Karte (Vorschlag der KI)**, **Selbständigkeit (Karte, Coop, Voll)**, **Tätigkeitsstrom**, **Zwei Rückgängig-Verläufe**, **Verlaufs-Wache**, **Bote «visboxKi» (Script-Message-Handler)**, **Werkzeuge der Mac-App (für Claude)**, **Werkzeugliste im Bau**, **Claude Desktop**; **MCP-Anschluss in der Mac-App** und **Werkzeugträger** nachgeführt |
| 2026-10-20 | Ergaenzt aus den Befunden von auf-20261020-292 (Protokoll 74 §154): **Tonwerte (Tonwertkurve)**, **Belichtung (je Stimmung)**, **Überstrahlung (voll weisse Bildpunkte)**, **Ruhiger Hintergrund (Kamerastrahl)**, **Tönung (je Stimmung)**, **Bestellte Bildgrösse und Raster**; **View-Transform** um AgX mit Himmelsbild ergänzt |
| 2026-10-20 | Ergaenzt aus F1, dem 3D-Fenster im Modell-Knoten (Entscheid 109 A, Protokoll 74 §155): **3D-Fenster (im Modell-Knoten)**, **WebGL**, **Nachgeladener Teil (der Knotenansicht)** |
| 2026-10-20 | Ergaenzt aus den drei Fehlern vom Mac (Protokoll 74 §152): **Fokusring**, **Feste Bildbox (Einpassen)**; die Seite der **Variante ohne Hochladen** steht unter diesem Eintrag (nicht doppelt angelegt) |
| 2026-10-20 | Ergaenzt aus den neuen Knoten am Heim-PC (H1–H3, Protokoll 74 §153): **Himmelsbild (HDRI)**, **Stimmung (Knoten)**, **Gipsmodell (Stimmung «Weiss»)**, **Principled BSDF**, **Box-Projektion**, **Relief (Bump)**, **Materialwahl (je Bauteil-Art)**, **Bauteil-Art**, **Fuge (im Material)**, **Senkrechte Perspektive (Zwei-Punkt-Perspektive)**, **Fester Abstand (Auto-Kamera)**, **Angewandte Vorgaben (im Ergebnis)** |
| 2026-10-20 | Ergaenzt aus den Heim-PC-Fehlern (Protokoll 74 §150): **Variante ohne Hochladen**, **Endgültiger Mangel**, **Kantenrauschen (einer Tiefenkarte)**, **Streamender Teiler**, **Lange Wartezeit (der Mac-App)**, **Eigenes Modell (des Assistenten)**, **Rollenkarte (von KosmoOrbit)**, **Marke «eine Frage läuft»**; **Formular-Upload** und **Entladen (des Sprachmodells)** nachgeführt |
| 2026-10-20 | Ergaenzt aus dem MCP-Kern der Mac-App (KI-Bedienung Stufe 2, Protokoll 74 §151): **MCP-Anschluss in der Mac-App**, **JSON-RPC**, **Hörer (Listener)**, **Loopback (127.0.0.1)**, **DNS-Rebinding**, **Streamable HTTP**, **Wartefrist (eines Aufrufs von Claude)**, **Werkzeugträger** |
| 2026-10-20 | Ergaenzt aus dem Güte-Schalter am Render-Knoten (Protokoll 74 §149): **Zwischenbild**, **Zeilenregister (Render-Knoten)** |
| 2026-10-20 | Ergaenzt aus «Visbox eigenständig», Schritte 2 und 6 (Protokoll 74 §147): **Rechenserver**, **Ohne Rechner**, **Rechner-Wahl**, **App-Einstellungen**; **Vorführmodus** als entfallen vermerkt |
| 2026-10-20 | Ergaenzt aus der schnellen KI-Vorschau (Entscheide 104–104b, Protokoll 74 §148): **Vorschau (Güte)**, **Schritte eines Bildmodells**, **Steuerbild**; **Teilbild (abgebrochen)** um die Kamera des Bilds und **Fortschritt (eines Renderauftrags)** um die Phase «abgebrochen» ergänzt (Geräteprobe der HomeStation) |
| 2026-10-20 | Ergaenzt aus «Visbox eigenständig», Schritt 1 (Protokoll 74 §146): **Eigenes Adressschema**, **App-Bündel**, **Ursprung (einer Webseite)** |
| 2026-10-20 | Ergaenzt aus der iPad-Zeile am Mac (Protokoll 74 §144): **Gerätebuch (des Heim-PC)**, **Geräteart (Kopf einer Anfrage)**, **Netzaussetzer** |
| 2026-10-20 | Ergaenzt aus Fortschritt, Vorschau und Teilbild am Heim-PC (Protokoll 74 §142): **Fortschritt (eines Renderauftrags)**, **Restzeit (geschätzt)**, **Teilbild (abgebrochen)**, **Kooperativer Abbruch** |
| 2026-10-20 | Ergaenzt aus Entscheiden 99/99a/99b (Protokoll 74 §141): **Koppelfenster**, **Koppelschein**, **Nähe-Verbindung (MultipeerConnectivity)**, **QR-Code**; **Kopplungszahl** um die zwei Minuten am Mac ergänzt |
| 2026-10-20 | Ergaenzt aus den Tafelkarten «Visbox · Tools» und «Visbox · Architecture» (`docs/WERKZEUGE_UND_ARCHITEKTUR.md`): **CC0 (Gemeinfreiheitserklärung)**, **Simple Icons**, **Markenzeichen (auf einer Logo-Karte)**, **numpy**, **Pillow**, **Mermaid**, **Chromium ohne Fenster (headless)**, **IfcOpenShell**, **trimesh**, **shapely / GEOS**, **gsplat**, **Open3D**, **PyTorch (torch)**, **transformers**, **Z-Image Turbo**, **Depth Anything V2 (Small)**, **SigLIP 2**, **Architekturbild (Organigramm der Programme)**, **OpenSSL**, **Avahi**, **libnotify (notify-send)**, **Monogramm-Kachel** |
| 2026-10-20 | Ergaenzt aus Visbox 0.2.10 (Protokoll 74 §140): **Einzelinstanz (einer App)** |
| 2026-10-20 | Ergaenzt aus Nr. 85/83/84 (Demolauf 16.10., Protokoll 74 §139): **Fester Startwert (einer Serie)**, **Blender-Grundlage (eines Renderings)**, **Deckungsgleiche Varianten**, **Nur Grundlage («nur Cycles»)**, **Pose (einer Kamera)** |
| 2026-10-15 | Ergaenzt aus A1/96a/96b (Protokoll 74 §131): **Standpunkt eines Bildes**, **Steuerzeichen**, **Laufwerksbuchstabe**; berichtigt **Anweisung (an eine Skizze)** (96a: die Bemerkung gilt, nicht der Prompt); **Pfad-Trickserei** um den Skizzennamen ergänzt |
| 2026-10-15 | Ergaenzt aus «Varianten mit einem Klick» (Entscheide 92/92a/92b, L24 Bildweg Varianten E246, Protokoll 74 §129): **Varianten-Knoten («Varianten mit einem Klick»)**, **Raster (im Bildvergleich)**, **Ebenenkombination (als Entwurf)**, **Eine Freigabe für alle**, **Befehlsjournal**, **Luft der Werkzeugliste (B19)**, **Lauf ohne Karte** |
| 2026-10-15 | Nachgeführt aus dem RealityScan-Ausfall (auf-287): **Xvfb** (eigener Bildschirm für RealityScan) |
| 2026-10-15 | Ergaenzt aus Entscheid 96 «Die Skizze führt das Bild» (Protokoll 74 §125): **Die Skizze führt das Bild (Eingang «Skizze»)**, **Anweisung (an eine Skizze)**, **Bearbeitungs-Modell**, **Eingang nur für eine Knotenart**, **Verborgene Datei (Punktdatei)**, **Feld, das ein anderes ausschliesst (Kreuzregel)**, **Additives Vertragsfeld**, **Kurzhilfe (Tooltip)** |
| 2026-10-14 | Ergaenzt aus dem Knoten «Skizze vom iPad» (Entscheide 95/95a, Protokoll 74 §123): **Skizzen-Quelle des Wirts**, **Zulieferer-Knoten**, **Daumenbild (Vorschaubild)**, **data:-Adresse (Data-URL)**, **Berechneter Schlüssel** |
| 2026-10-14 | Ergaenzt aus dem Nachzug auf Runde 29 (Protokoll 74 §122): **Nachziehen per Merge (statt Neuaufsetzen)** mit **Force-Push**, **Hilfszweig** |
| 2026-10-14 | Ergaenzt aus Strg+Z in der Visbox-Knotenansicht: **Wirt (der Knotenansicht)** |
| 2026-10-14 | Ergaenzt aus Visbox 0.2.8 (Neustart, Nummer, iPad verbindet von selbst): **Neustart-Helfer**, **Prozessnummer (PID)**, **Ein Fenster statt Fenstergruppe (`Window` / `WindowGroup`)**, **Wiederverbinden** |
| 2026-10-14 | Ergaenzt aus Entscheid 91/92 (fertiger Anfang, Auto-Kamera mit den Standpunkten des Heim-PCs): **Fertiger Anfang (Startgraph)**, **Rückgängig-Klammer**, **Standpunkte des Heim-PCs (Vorschau an der Auto-Kamera)**, **Vorbild (Bild-Referenz)** |
| 2026-10-14 | Ergaenzt aus Fassung 3 der RealityScan-Brücke (Textur statt Eckfarben): **Textur**, **Abwicklung (UV-Abwicklung)**, **Texel**, **OBJ und MTL (Dateiformate)**; **Emissions-Shader** um die Stärke 1 der Umgebung ergänzt, **Eckpunktfarbe** und **Deckel (im Netz)** nachgeführt (Grenze 2,5 % statt 5 %) |
| 2026-10-14 | Ergaenzt aus der Erklärung der Knoten für die Kosmo-Tafel (`docs/KNOTEN_ERKLAERT.md`): **Kosmo-Tafel**, **Knotenkatalog**, **Gruppe eines Knotens**, **Anschlusssorte (Porttyp)**, **Preset**, **Geometrie-Treue**, **Bildwerkzeug**, **Strichzeichnung (Line-Art)**, **Rückgängig (Undo)**, **Viewport-Aufnahme**, **Kuratierfläche**, **Prüfurteil (QA)**, **Veraltet**, **KosmoPublish** |
| 2026-10-14 | Ergaenzt aus Entscheid 90 («Datei laden …» am Modell-Knoten): **Lade-Fähigkeit des Wirts**, **Fassung des Modells (in einer Mappe)**, **Start-Mappe**, **Geschlossenes Dateiformat**, **Nachfragen (Polling)**, **Dateiwähler (Öffnen-Dialog, `NSOpenPanel`)**, **UI-Delegat (`WKUIDelegate`)** |
| 2026-10-14 | Ergaenzt aus der Übernahme Runde 26 der Knotenansicht (KosmoOrbit 22988d6ed): **Zwei-Finger-Geste (Wischen und Pinch)** |
| 2026-10-14 | Ergaenzt aus Entscheid 87 (ein Klick fürs Aktualisieren): **Selbst-Aktualisieren (Updater)**, **AppImage** |
| 2026-10-14 | Ergaenzt beim Leser des Massstab-Blocks: **Bewegungssensor (IMU)**, **Massstab (des Splats)** (mit Gegenprobe, Ampel, Kontrollmass, Drift) |
| 2026-10-14 | Ergaenzt aus Entscheid 85 (Mac zeigt zuerst die Knoten): **Segmentschalter**; nachgefuehrt: **WKWebView**, **Knotenansicht / Knoteneditor** (Kopie aus KosmoOrbit, nicht mehr der eigene Entwurf) |
| 2026-10-14 | Ergaenzt beim Reparieren der RealityScan-Bruecke (Fassung 2, nach `auf-20261013-278`): **Prozessgruppe** (mit verwaistem Prozess), **Deckel (im Netz)**, **Farbe als Ganzzahl oder Kommazahl (uchar / float)**; nachgefuehrt: **RealityScan-Brücke** (jetzt der Weg fürs Umgebungsnetz) |
| 2026-10-13 | Ergaenzt aus dem Bau von Entscheid 84 (Aktualisieren, Visbox 0.2.1): **Tag (Markierung im Verlauf)**, **Freigabe auf GitHub (Release)**, **Prüfsummen-Datei (`SHA256SUMS.txt`)**, **Provisioning-Profil (`embedded.mobileprovision`)**, **Sparkle** (mit Appcast und EdDSA), **App Translocation (verschobener Startort)**, **Weiterleitung (Redirect)** |
| 2026-10-13 | Ergaenzt aus dem Bau von Entscheid 83 (Mac koppelt mit Zahl): **Selbst unterschriebenes Zertifikat**, **Vertrauen beim ersten Mal (TOFU)**, **Dazwischenstellen (Man-in-the-Middle)**, **PAKE**, **Zeichen des Heim-PC**, **Mitteilung (am Bildschirm)**, **Drossel**, **Tailscale-Befehlszeile**, **Auflösen (eines Fundes)**; nachgefuehrt: **TLS mit festgehaltenem Schlüssel** (jetzt «Zertifikat anheften, Pinning», gebaut für den Mac im WLAN), **Zertifikat**, **Bonjour (mDNS)** (auch die Mac-App sucht) |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §78 (Entscheid 76, Splat als Umgebung): **Splat (3D Gaussian Splatting)**, **PLY (Dateiformat)**, **Punktwolke**, **Geometry Nodes, «Mesh to Points»**, **SH-Grad 0 (Grundfarbe eines Gaussians)**, **Deckkraft eines Gaussians (Opazität, Sigmoid)**, **Transformationsmatrix (4×4, zeilenweise)**, **Umgebung im Bild (Kontext)**; nachgefuehrt: **Verdeckung** (durch die Umgebung) |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §75 (Entscheide 70 und 73 am Bild): **Sprungmarke (Anker)**; nachgefuehrt: **Nicht beurteilbar** (eigenes Zeichen), **Standpunkt-Vorgabe** (steht am Bild) |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §79: **Ausschnitt (Kamera)** |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §80: **Bestand (Körper)** |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §81: **Ausblenden (in der Prüfung)** |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §82: **Glätten der Umgebung** |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §83: **Messboden** |
| 2026-10-13 | Ergaenzt beim Bau der Splat-Bruecke (Entscheid 79): **Splat-Brücke (Splat → Netz)**, **Rastern (Rasterization)**, **Erwartete Tiefe**, **TSDF (Verschmelzen von Tiefenbildern)**, **Voxel**, **Eckpunktfarbe (Vertexfarbe)**, **Insel (im Netz)**, **CUDA**, **Ersatzrenderer (cpu-probe)** |
| 2026-10-13 | Ergaenzt beim Tiefenfilter der Splat-Bruecke (nach auf-20261013-276): **Akkumulierte Deckkraft (alpha)**, **Tiefenfilter (Splat-Brücke)**, **Sprenkel (in der Tiefe)**, **Streuung entlang des Strahls**, **Nahbereich (der Kamera)**, **Weg der Aufnahme (Filter)**, **Maske der Aufnahme (Personenmaske)**, **Maskenpolarität**, **Zufallsstichprobe mit festem Startwert**, **Feste Reihenfolge (eines Netzes)**; nachgefuehrt: **Erwartete Tiefe** (Schwaeche, ED = D/alpha), **Ersatzrenderer (cpu-probe)** (mischt wie gsplat), **Deckung (des Netzes)** (Stichprobe), **Verweis (Symlink)** (Aufnahme hinter dem Verweis) |
| 2026-10-13 | Ergaenzt bei der RealityScan-Bruecke (Entscheid 81): **RealityScan-Brücke (Fotos → Netz)**, **Wine**, **Export-Parameterdatei (RealityScan)**, **COLMAP-Textformat**, **Lageprüfung (Netz ↔ Aufnahme)**, **Umeyama-Verfahren** |
| 2026-10-13 | Ergaenzt bei den Blickwinkeln aus der Aufnahme (nach auf-20261013-275): **COLMAP**, **Kamerapose (Pose)**, **Rig (Kamera-Rig)**, **Augenblick (Frame)**, **Gleichheitsprüfung (Aufnahme ↔ Splat)**, **Deckung (des Netzes)**, **Blockwache**, **Statisch eingebunden (Bibliothek)**; nachgefuehrt: **TSDF** (7 cm), **Insel (im Netz)** (bleibt absolut), **Ersatzrenderer (cpu-probe)** (Tiefe auf der Scheibe) |
| 2026-10-13 | Ergaenzt aus Sitzung 74 §84: **Photogrammetrie**, **Relightable Gaussian Splatting (lichtaktiver Splat)**, **Fremdprogramm (vom Nutzer installiert)**; nachgefuehrt: **Messboden** (nur zum Trennen) |
| 2026-10-08 | Ergaenzt aus Sitzung 74 §63 (F6, Stile aus der IFC): **Deckend (Material)**, **sRGB und linear (Farbraum)**; aus §69 (Entscheid 70): **Gesamtwert (der Prüfung)**, **Nicht beurteilbar** |
| 2026-10-07 | Ergaenzt aus Sitzung 74 §58 (v0.1.8, Bildmodell einmal je Auftrag): **Laden (eines Bildmodells)**, **Ein Modell je Auftrag (Modellvorrat)**, **Freigeben (des Grafikspeichers)**, **Aufräumen auch im Fehlerfall (try/finally, Kontextmanager)**, **Kontextvariable**; aus Antwort 259: **Oberflächenstil (IFC)**, **Ausschnitt (Öffnungselement)**; aus Antwort 261: **Standpunkt-Vorgabe**, **Komponiert (eine Ansicht)** |
| 2026-10-01 | Ergaenzt aus Sitzung 74 (Plan v0.1.7): **Gatekeeper**, **Behelfs-Unterschrift (ad-hoc)**, **Vermittler (Relay)**, **Lieferblatt**, **Vollbau**, **Sammel-Nachprobe**, **Vorführmappe**, **Platzhalter (Beispielmappe)**, **Wachsender Abstand (Backoff)**, **Bestätigte Antwort**, **Begleitdaten**, **Formatkennung**, **Bündel (.app)**, **Info.plist**, **«Trotzdem öffnen»**, **Startzeile**, **Anschluss (Port)**, **Basic-Anmeldung**, **WKWebView**, **Gedankentext**, **Entladen (des Sprachmodells)**, **Werkzeugbeschreibung**, **Vorschlagskarte**, **Verlauf**, **nvidia-smi**, **TXT-Eintrag**, **Kopf (Header)**, **Hop-by-Hop-Kopf**, **100 Continue**, **Absage der Tür**, **Flüchtige Sitzung**, **Fensterinhalt**, **ASCII**, **Prozentschreibung**, **Gegenstelle**, **Uhr mit Ruhezustand**, **TLS mit festgehaltenem Schlüssel**, **MagicDNS**, **Zertifikat**, **Schema (einer Adresse)**, **Strecke**, **local-prepare (Prüf-Helfer)**, **Versionsnummer (Visbox 0.1.0)**, **Aufsicht**, **Pipeline-Klasse**, **Randlose Silhouette**, **Nicht anwendbar**, **Bildauftrag der Innenkamera**, **Quellstand**, **Dienst-Unit**, **Journal**, **Geschütztes Leerzeichen**, **Xvfb**, **Grafikbeschleunigung**, **Software-GL**, **WebKitGTK**, **foreignObject**, **Trefferfläche**, **Zentrale**; berichtigt: **TestFlight und Apple-Entwicklerkonto** (Freigabe auf macOS 15) |
| 2026-09-30 | Ergaenzt aus Sitzung 73: **Regel B (null-Regel, E123)**, **Hinweis gegen Vorbehalt**, **Lizenz offen**, **Umrisstreue**, **Sobel-Filter**, **Rahmung (nach dem Bauwerk)**, **Formprüfung (Augenurteil als Referenz)**, **AUC**, **Störfaktor**, **Kreuzpaar**, **Richtungstreue**, **Flächentrennung**, **Decke (einer Probe)**, **Vorab festgelegte Regel**, **Wiederholbarkeit (des Augenurteils)**, **Ausgewogene Trefferquote**, **Stichentscheid**, **Nachmessung (Replikation)**, **Grauzone (des Augenurteils)**, **Union-2.1**, **Gewichte-Ordner**, **Tunnel**, **Vorführmodus**, **TestFlight und Apple-Entwicklerkonto**, **Fassung (je Knotenart)**, **Tailscale**, **Tailscale Serve (Weiterleitung)**, **Ollama**, **Qwen3** |
| 2026-09-29 | Ergaenzt aus dem Dokumentabgleich: **Integrator (KosmoOrbit Int 1)**, **Insel-Karte (n1)**, **Laufnummer**, **Fassung schneiden (Release)**, **Meilenstein**, **Kritischer Pfad**, **MPS (Apple-Rechenweg)**, **Bildanteil**, **Ordnung an Tiefensprüngen**, **Eingangswächter** |
| 2026-09-29 | Ergaenzt aus dem Owner-Entscheid zu Qwen-Image-2.1: **Forschungslizenz**, **Forschungs-Ausnahme** |
| 2026-09-29 | Ergaenzt aus E124 und der Antwort auf-142: **Ebene (im Ergebnis)**, **An der Aussengrenze übersetzen** |
| 2026-09-29 | Ergaenzt aus den Owner-Entscheiden, Sitzung 72: **Stilllegen (eines Bildmodells)**; **Paarurteil** nachgetragen |
| 2026-09-24 | Ergaenzt aus B161: **Abholer-Puls**, **Farbtemperatur (Kelvin)**, **Speicher-Riegel**, **Konvention (einer Himmelsrichtung)**, **Transmission** |
| 2026-09-24 | Ergaenzt aus der Kamera-Berichtigung: **Wandabstand (Mindestabstand der Aussenkamera)** |
| 2026-09-24 | Ergaenzt aus den Antworten 163/164: **Render-Umgebung** |
| 2026-09-24 | Ergaenzt aus der Recherche Knotensysteme: **App-Modus**, **Teilgraph**, **Render-Pass (AOV)**, **Variantenachse (Wedge)**, **Übernehmen (Bake)**, **Überbrücken (Bypass)**, **Credit**, **Abwesenheitsbefund** |
| 2026-09-24 | Ergaenzt aus dem Knotenweg: **Vorsilbe eines Wegs**, **Formular-Upload (multipart/form-data)**, **Freigabe-Marke** |
| 2026-09-24 | Ergaenzt aus der Übernahme des Vis-Werkzeugs (E26): **Stellvertreter**, **Wörtliche Kopie mit Herkunft**, **npm und Arbeitsbereich**, **Sperrdatei**, **Bau (Build)**, **Vite**, **Vitest**, **zod**, **woff2** |
| 2026-09-24 | Ergaenzt aus Sitzung 71: **Knotenansicht / Knoteneditor** |
| 2026-09-23 | Ergaenzt aus Runde 12: **Führungsregler (`true_cfg_scale`)**, **Leer-Negativprompt**, **Guidance-destilliert (`guidance_embeds`)** |
| 2026-09-23 | Ergaenzt aus Runde 11: **Zweite Tür**, **Freigabe-Abdruck**, **Buchprüfung (`FREIGABE_MIT_BUCH`)**, **Schrift mitliefern / registrieren** (mit CoreText), **PostScript-Name** (mit Namentabelle), **Variable Schrift** (mit Schriftschnitt), **TrueType**, **SHA-256**, **Ressource im App-Paket**, **Kreuzprobe** |
| 2026-09-23 | Ergaenzt aus Runde 10: **Messschalter**, **Abstand zum Hintergrund (`ferne_abstand`)** |
| 2026-09-23 | Ergaenzt aus Runde 9: **Lieferstatus**, **Heimrelativer Pfad**; nachgefuehrt: **Obergrenze, gesetzt, nicht gemessen** (an Blender 5.2.2 nachgemessen) |
| 2026-09-23 | Ergaenzt aus Runde 7b/7c: **Ueberlauf**, **Zweite Linie**, **Obergrenze, gesetzt, nicht gemessen** |
| 2026-09-23 | Ergaenzt aus Runde 7: **Standpunkt zweimal bestellt**, **Bias (Winkel einer Ueber-Eck-Ansicht)**, **Nicht gerahmt**, **Listenlage** (mit «ganz oder gar nicht»); nachgefuehrt: **Richtungsgrenze** (gilt in beide Richtungen), **Wirkungslos (im Bericht)** (auch Augenhoehe, Bias, Kameramodus) |
| 2026-09-23 | Ergaenzt aus der Welle 2c: **Mitgesandte Kamera**, **Neuzentrierung**, **Gleichwertige Mutation**, **Abschrift-Probe**, **Zweiter Zustand (eines Entwurfsblatts)**, **Owner-Entscheid offen (Schild)** |
| 2026-09-23 | Ergaenzt aus der Welle 2b: **Blattunterlage**, **Darauf skizzieren**, **Ablageplan**, **Fachzaehlung**, **Aufraeumfehler**, **Zug (Stiftzug)**, **Beruehrungsart**, **Deckungsbild**, **Einbausperre**, **Reine Absicherung**, **Bereich der Anmeldung (realm)**, **Pruefsumme im Dateinamen**; berichtigt: **Eingangsbild** (gestreckt wird die Skizze, nicht die Unterlage) |
| 2026-09-23 | Ergaenzt aus der Welle 2 der iPad-App: **Identitaet einer Ansicht**, **Treffertest**, **Unterlage (einer Skizze)**, **Eingangsbild (des Nachrenders)**, **Nachholen (nach einer Schreibkollision)**, **Handlungsquittung**, **Ebenen-Reihe**, **Seitenfeld**, **Laufwaechter**, **Aufklappbarer Vorbehalt**, **Rumpffehler**, **Unicode-Zeilentrenner**, **Signifikante Stellen**, **Unicast**, **Bekanntes, abgewiesenes Feld**, **Innenraum-Bestellung**; nachgefuehrt: **Kastenmittel** (deckungsgewichtet), **Parkfach** (ungewisse Skizzen gehen mit Schluessel von selbst noch einmal) |
| 2026-09-22 | Ergaenzt aus dem Bau der iPad-App: **Native App gegen Webseite**, **Swift**, **SwiftUI**, **PencilKit**, **Xcode**, **Swift Playgrounds**, **App-Paket (.swiftpm)**, **Bundle-Kennung**, **Simulator**, **Pruefstrecke (auf GitHub)**, **Bonjour (mDNS)**, **Rundruf**, **App Transport Security**, **Wegtafel**, **Parkfach**, **Schluesselbund**, **Doppelsendeschutz** |
| 2026-09-22 | Ergaenzt aus dem Grundlagenblatt «Wie man eine Software von Grund auf baut» (Anhang B): **Anforderung**, **Randbedingung**, **Erfolgskriterium**, **Kleinste Fassung, die ein Erfolg waere**, **Kippstelle**, **Schnittstelle**, **Blender**, **Versionsverwaltung**, **Sitzungsprotokoll**, **Die dritte Antwort**, **Ersatzwert**, **Einbau**, **Produktweg gegen direkten Aufruf**, **Worker**, **HomeStation**, **Durchsicht**, **Open Font License (OFL)**, **Tuer (Anmeldung der Oberflaeche)** |
| 2026-09-22 | Ergaenzt aus der sechsten Runde: **Richtungsgrenze**, **Wirkungslos (im Bericht)**, **Zwillingsansicht**, **Registereintrag** |
| 2026-09-22 | Ergaenzt aus der fuenften Runde: **Kameraweg (abgeleitet, vorgegeben, Rueckfall)**, **Bildpunkt-Pruefsumme gegen Datei-Pruefsumme**, **Zufallsstreuung einer Rangkorrelation**, **Die erste Zustellung zaehlt**; nachgefuehrt: **Gelaendeangabe** (Owner-Entscheid) |
| 2026-09-22 | Ergaenzt aus der vierten Runde: **Pipeline-Familie**, **Flache Kopie gegen tiefe Kopie**, **Angabe gegen Messung**, **Rollwinkel**, **Geländeangabe**, **Adresse im Heimnetz gegen «alle Adressen» (0.0.0.0)**. Jeder Eintrag traegt den Befund gegen den eigenen Code, aus dem er kam |
| 2026-09-22 | Ergaenzt aus der Abarbeitung von sechs Befunden: **Wirkungspruefung gegen Textpruefung**, **Bestellbar, aber nicht lieferbar**, **Modusabweichung**, **Laufmessung (in der Mappe)**, **Konvergenz (stuerzender Linien)**. Drei davon tragen einen Befund gegen den eigenen Code: vier Waechter, die Text statt Wirkung prueften; eine Innenansicht, die sich bestellen und nicht liefern laesst; eine fehlende Neigung, die als gemessene Null bescheinigt wurde |
| 2026-09-22 | Ergaenzt zu Abschnitt 10 aus dem ersten Verbinden: **Kopplungszahl**, **Stetige Uhr** |
| 2026-09-22 | Ergaenzt zu Abschnitt 10 aus der Arbeit an zwei Geraeten an derselben Mappe: **Standnummer**, **Schreibkollision** |
| 2026-09-21 | Nachgetragen zu Abschnitt 10 aus der Verbindung iPad/Rechner: **Wischregler**, **Übergabe-Animation**, **Bewegungsreduktion** |
| 2026-09-21 | Neuer Abschnitt **10 · Oberfläche und Entwurf**, aus dem Entwurf der iPad-Oberfläche: **Entwurfsblatt (Artboard)**, **Entwurfsfläche**, **Berührungsfläche (Touch-Ziel)**, **Kontrastverhältnis**, **Druckempfindlichkeit**, **Wortzeichen**. Der Eintrag zum Kontrastverhältnis traegt einen Befund gegen die eigene Oberflaeche: Das Rot fuer «durchgefallen» kommt auf dem dunklen Grund nur auf 4.06 zu 1 und ist damit unter dem Mindestmass — im iPad-Entwurf eine Stufe heller, in der Browser-Oberflaeche noch nicht geaendert. **BERICHTIGT am 22.09.2026:** Hier stand zuerst 3.3; das war geschaetzt und nicht gerechnet. Der gerechnete Wert ist 4.06 auf dem Grund und 3.70 auf einem Feld — der Befund bleibt, die Zahl war falsch |
| 2026-09-19 | Zum Bild-Eingang: **Bild-Eingang**, **Hineinskizzieren**, **Bildquelle (als Arbeitsschritt)**, **Nachrender**, **Ein Bildeingang, den die Tiefenkarte gewinnt**. Der letzte Eintrag traegt den scharfen Befund dieses Tages: Die Bibliothek reicht ein Ausgangsbild sehr wohl an das Modell durch — aber auf einer Pipeline mit nur EINEM Bildeingang bekommt ihn die Tiefenkarte, und das Hineingezeichnete faellt weg. Am Geraet gemessen (`auf-20260818-09`), hier erstmals mit einer Probe hinterlegt statt nur als Kommentar in der Registry |
| 2026-09-16 | Ergaenzt beim EINBAU der vier Bausteine: **Feste Schranke (einer Tiefennormierung)**, **Nutzung des Wertebereichs**, **Klemmen (einer Tiefenkarte)**, **Boden (eines Wertebereichs)**, **Quantisierungsschritt als Pruefstein**. Alle fuenf aus Befunden gegen den eigenen Code: Die am 11.09. gemeldete flachgedrueckte Tiefenkarte stammt aus UNSERER festen Schranke und nicht aus dem Perzentil der HomeStation (98,9 % der Punkte ueber 0,99, nachgerechnet); die erste Fassung des Ersatzes klemmte Geometrie auf den Hintergrundwert und machte sie damit unsichtbar fuer die Silhouette; und der zuerst gewaehlte halbe 8-Bit-Schritt als Boden ueberlebt die Rundung nicht, obwohl der Kommentar daneben behauptete, er tue es |
| 2026-09-16 | Ergaenzt aus vier gleichzeitig gebauten Bausteinen: **Zweigipflige Verteilung**, **Luecke (einer Verteilung)**, **Verhaeltnissprung gegen Abstandssprung**, **Strukturwert einer Tiefenkarte**, **Auskunft neben dem Urteil**, **Rueckkanal**, **Falscher Freund**, **Kollision beim Endungsabstreifen**. Fuenf davon tragen einen Befund und keine Lehrmeinung: Das feste Perzentil scheiterte daran, dass die Fernsichtebene 1,13 % der Flaeche einnahm und nicht unter 1 % lag; die erste Differenz trennt Verlauf und Kante NICHT (beide 0,0333); die Strukturschwelle ist gesetzt und nicht kalibriert und entscheidet darum nichts; `elf` und `acht` bleiben aus dem Zahlwort-Glossar draussen, jedes aus einem eigenen, nachgemessenen Grund. **Berichtigt am selben Tag:** Die zweite Stufe der Luecken-Trennung lief zuerst von selbst und nahm in der nachgestellten Aussenansicht eine echte Nachbarzeile als Ferne weg — sie ist jetzt abgeschaltet, und ihre urspruengliche Begruendung war ohnehin hinfaellig, weil die erste Stufe den gemeldeten Fall schon selbst loest |
| 2026-09-16 | Ergaenzt: **Warum eine Antwort fehlt — die vier Lagen**. Der Rueckstand zaehlte bis dahin nur, DASS eine Antwort fehlt. Bei 18 offenen Auftraegen und acht stillen Tagen war das zu wenig, um zu entscheiden, ob eine Nachfrage angebracht ist — gemessen: bei 2 von 18 |
| 2026-09-12 | Ergaenzt aus dem ersten Lauf bis zum fertigen Bild: **Oertliche Ergaenzung (Drop-in)**, **Zweite Differenz (Kruemmung)**, **Ersatzschreibung der Umlaute**. Alle drei aus gemessenen Befunden — der Waechter las nur die Hauptdatei, die vorgeschlagene Kennzahl trennte Verlauf und Kante nicht, und «betonwaende» erreichte das Glossar nicht |
| 2026-09-11 | Ergaenzt aus `herkunft.py`: **Herkunftstabelle** und **Belegt, gemessen, vermutet, unbekannt**. Die vierte Stufe entstand, weil eine zweifach exakte Messung weder «Norm» noch «Gewohnheit» ist |
| 2026-09-11 | Ergaenzt aus dem Befund der HomeStation zum Renderprojekt: **Stilles Abstreifen (unbekannter Felder)**. Der Begriff wurde noetig, weil `lies_szene` erfundene Bestellfelder spurlos verschluckt hat — gemessen, nicht vermutet |
| 2026-09-19 | Zum Einlass: **Einlass (Sichtgang an der Tür)**, **Das Format am Inhalt statt an der Endung bestimmen**, **Eine Absage ohne Ausweg ist eine halbe Auskunft** |
| 2026-09-19 | Zum Einbau und zu den zwei Schichten: **Gebaut, am Gerät unbestätigt**, **Abgelegt ist nicht zugestellt**, **Handeingriff**, **Geometrielayer und AI-Imaging-Layer** |
| 2026-09-21 | Zum Importeur: **Importeur (3D-Modell-Importeur)**, **Durchreichen**, **Rundreise mit bekannter Wahrheit**, **Der Vorgabewürfel** |
| 2026-09-21 | Zur Fundation: **Projekt (die Mappe)**, **Fingerabdruck (einer Datei)** |
| 2026-09-21 | Zum Einhaengen: **Arbeitsgang**, **Hochachse** |
| 2026-09-21 | Zur Oberflaeche: **Die Oberflaeche (von Visbox)** |
| 2026-09-21 | Aus der Anfrage der Modellseite: **Ausbesserung (Inpainting)** |
| 2026-09-21 | Aus dem Befund «bestellt mit Bild, gerechnet ohne»: **Bestellter und gerechneter Modus**, **Vertraeglichkeitsfilter** |
| 2026-09-21 | Aus dem Befund «der Vorgabe-Backbone rechnet gar nicht mehr»: **Bedarfsrechnung (vor dem Ladeweg)**, **Aktivierungen**, **Spielraum (einer Ladewegentscheidung)** |
| 2026-09-21 | Aus der Pruefung der Kanten zum Nachbarsystem: **Nullbar (nullable)**, **Tote Kante und leere Kante** |
| 2026-09-21 | Aus der Bildanzeige der Oberflaeche: **Verweis (Symlink)** neu; **Positivliste / Verbotsliste** um das zweite Beispiel erweitert statt ein zweites Mal angelegt — der Waechter gegen Doppeleintraege hat es gemeldet |
| 2026-09-21 | Aus dem Owner-Entscheid zum Skizzenmodus (E23): **Darstellungsmodus und Entwurfsmodus**, **Erfundenes Volumen** |
| 2026-09-21 | Aus der Zeichenflaeche fuer das iPad (E24): **Zeigerereignisse (Pointer Events)**, **Leinwand (Canvas)** |
| 2026-09-21 | Aus dem Zusehen beim Rechnen: **Belegter Fortschritt und Lebenszeichen**, **Hintergrundfaden (Thread)** |
| 2026-09-21 | Aus Beweis 31 und dem Pfadfehler: **Relativer und absoluter Pfad** |
| 2026-09-21 | Aus dem Einschalten des Speichers auf dem Produktweg: **Zwischenspeicher (Cache) einer Rechenkette** |
| 2026-09-21 | Aus dem stillen Datenverlust bei zwei gleichzeitigen Laeufen: **Sperre (Lock) und der verlorene Schreibvorgang** |
| 2026-09-21 | Aus der Pruefung fuers Netzlaufwerk: **Uhrenabweichung (Clock Skew)** |
| 2026-09-21 | Aus der Anmeldung fuers Heimnetz (E25): **Vergleich in gleichbleibender Zeit** und **Unverschluesselte Verbindung (HTTP)** neu; **Fail-closed** um das zweite Beispiel erweitert statt ein zweites Mal angelegt — zum zweiten Mal an diesem Tag hat der Waechter gegen Doppeleintraege es gemeldet |
| 2026-09-19 | Zum Rueckstand und seiner Zaehlung: **Ansage gegen Messauftrag**, **Nachfrage gegen Mahnung**, **Eine Ablehnung schliesst einen Posten so gut wie eine Erledigung** |
| 2026-09-18 | Zur neuen QA und zur Umstellung auf Visbox: **Zwei Tore statt einer Kennzahl**, **Rauschband**, **Fehlalarm gegen Durchlasser**, **Ein gemeldeter Mangel, der in der Naht abgefangen wird**, **Anwendungsdatenordner**, **Zeitfaktor (für Fristen)**, **Grössenriegel**, **Absoluter Pfad, und warum er vom System abhängt** |
| 2026-09-09 | Ergaenzt aus dem Einbau-Bericht: **Rueckstand gegen Einbau-Stand**. Der Begriff wurde noetig, als eine neue Zaehlung zeigte, dass 21 der 23 offenen Posten nur noch Auftraege nennen, die laengst beantwortet sind |
| 2026-09-09 | Ergaenzt aus `messstand` und `beruehrung`: **Codestand (eines Dokuments)**, **Grundlage (eines Dokuments)**, **Beruehrung (einer Messung)**, **Nachgesehen bis**. Der Codestand war am Vortag gebaut und NICHT ins Lexikon eingetragen worden — nachgeholt, gemeinsam mit der zweiten Haelfte derselben Frage |
| 2026-09-09 | Ergaenzt aus dem Tokenbuch (`auf-vis-20260821-03`): **Form und Befugnis**, **Tokenbuch**, **Abdruck (eines Tokens)**. Der Befund der HomeStation vom 21.08. lautete: Das Freigabe-Gate prueft, ob eine Zeichenfolge wie ein Schluessel *aussieht*, nicht ob wir sie *ausgegeben* haben. Der Abdruck kam beim Bauen dazu — ein Buch mit Klartext-Token haette die Freigabe eine Datei weiter wieder offen hingelegt |
| 2026-09-09 | Ergaenzt aus der Familienpruefung: **Korngroesse (einer Regel)** und **Familienpruefung (in der Gelaendeform)**. Beide aus einem Befund der HomeStation: Ein Gelaende aus zwanzig Streifen faellt Knoten fuer Knoten durch (groesster Grundrissanteil 0,2215) und wird als Huellbox ueber alle zwanzig zweifelsfrei erkannt (0,918). Kein Schwellenproblem, ein Korngroessenproblem |
| 2026-09-09 | Ergaenzt aus dem Befund der HomeStation zu `auf-20260909-92`: **Vertauschprobe**, **Staerkeprobe**, **Konditionierungsweg**. Alle drei tragen denselben Befund: Zwoelf erzeugte Bilder bestanden die Geometrie-Schwelle — und dieselben zwoelf bestanden sie auch gegen die falsche Soll-Karte. Der Konditionierungsweg erklaert nachtraeglich den Fehlschlag vom 18.08. (0,359): Das damalige Modell hatte gar keinen ControlNet-Eingang |
| 2026-09-09 | Ergaenzt aus den Beweisen 23-28: **Anlauffrist (Anlauf gegen Stillstand)**, **Seitencache**, **Differenzbild**. Alle drei aus gemessenen Befunden: Der kalte Blender-Start kostet 12,63 s gegen 0,15 s warm und hat vier gesunde Beweislaeufe getoetet; das Differenzbild traegt zwei gegensaetzliche Beweise (Sonne: darf nicht schwarz sein / IFC-Spielarten: muss es sein). Ausgebaut: **Beugung (Flexion)** um den gemessenen Fall «Fenstern» aus Beweis 27 |
| 2026-09-09 | Ergaenzt aus dem Beweisgang: Bauwerksbox gegen Szenenbox. Der Begriff wurde zweimal benutzt und nie erklaert — und er ist der Unterschied zwischen «Deckungsgrad eingehalten» und «Deckungsgrad vom Gelaende eingehalten» |
| 2026-09-09 | Ergaenzt aus dem Beweisgang (Sitzung 14): Nullanker, Startwertstreuung, Beweisgang, Kontrollbild. **Nullanker stand seit dem 24.08.2026 im Text und war nie erklaert** — eine Definition, die einen unerklaerten Begriff voraussetzt, ist genau der Fall, den die Arbeitsregel verbietet |
| 2026-09-09 | Ergaenzt: **Vorschrift ohne Vergabestelle**. Anlass sind zwei Kollisionen an einem Abend: Eine fremde Lane nahm erst einen belegten Rang, dann Rang UND Laufnummer, und beide Male wurde main rot. Der Waechter verlangte eine lueckenlose Reihe und sagte niemandem, welche Zahl frei ist — die Abhilfe ist keine strengere Vorschrift, sondern eine Vergabestelle |
| 2026-09-09 | Ergaenzt: **Flaechenbeherrschte Aufnahme** und **Vorpruefung (gegen tragende Messung)**. Anlass ist der Verdacht gegen die frontale Innenansicht, der seit dem 22.08. ungemessen im Plan stand: Frontal liegen 57-79 % des Bildes auf EINER Tiefenebene, ueber Eck 0,5 % — und ohne uebergebene Brennweite traegt die Karte des groesseren Raums einen einzigen Wert. Das zweite Wort trennt, was diese Messung leisten kann (ausschliessen) von dem, was sie nicht kann (zusagen) |
| 2026-09-09 | Ergaenzt: **Zielzahl, die nur durch Verstecken erreichbar ist** und **Deckelzeile**. Anlass ist Woche 2: Das Ziel «PLAN.md unter 800 Zeilen» ist nachgemessen unerreichbar — 110 offene Punkte liegen verstreut ueber fast jeden langen Abschnitt, und nach dem Umzug der 22 fertigen bleiben rund 4300 Zeilen. Korrigiert statt still fallengelassen; an ihre Stelle tritt die Deckelzeile in 23 Protokollen und 21 Planabschnitten |
| 2026-09-09 | Ergaenzt: **Baulich zwingende Deckung**. Anlass ist die Schliessung der Formbruecke: Ob beide Seiten dieselben Namen sehen, musste ueberall gemessen werden — ausser an der einen Stelle, an der beide `obj.name` desselben Blender-Objekts lesen |
| 2026-09-08 | Ergaenzt: **Bruecke zwischen zwei Regeln** und **Ein Mangel, der benannt ist, ist kein Loch mehr**. Anlass ist die zweite Seite derselben Regel: Die Bildseite hat keine Geometrie und kann die Formregel nicht rechnen. Gemessen wurde vor dem Bau, ob beide Seiten dieselben Namen sehen — Materialnamen null Prozent, Objektnamen hundert, und bei geteiltem Gelaende brach Blenders Dublettensuffix die Deckung auf 25 % |
| 2026-09-07 | Ergaenzt: **Zweitmeinung (gegen zweite Regel)** und **Gelaende an der Form**. Anlass ist der Owner-Entscheid, zur Bildarbeit zurueckzukehren, und der offenste Strang darin: Die Namensregel findet auf echtem Bestand nichts (2,32 % Schrumpfung), und ein weiteres Wort gibt es nachweislich nicht — `decke` waere noetig und ist unmoeglich. Die Form ist das zweite «von aussen», fuer das niemand gefragt werden muss |
| 2026-09-06 | Ergaenzt: **Ein Satz, der nur auf einer Maschine wahr ist**. Anlass ist ein Befund der HomeStation: Der Kommentar «in dieser Umgebung gibt es keine GPU» ist dort falsch — gemessen wurde dann statt umgestellt, und OptiX ist 10-35 % langsamer und verschiebt Kantenpixel. Verhalten richtig, Kommentar falsch |
| 2026-09-06 | Ergaenzt: **Zugestellt an die Adresse, nicht an den Adressaten** — die genaue Fassung nach zwei ungenauen. Die Bloecke lagen auf `main` des fremden Repos, beide Worker entwickeln auf Feature-Zweigen, die `main` nie mergen: 17 Dateien dort, 0 bei ihnen. Beide Diagnosen davor massen den falschen Gegenstand |
| 2026-09-06 | Ergaenzt: **Zustellung ist gerichtet**. Anlass ist die Berichtigung derselben Sache am selben Abend: Der Weg zu `cloud` und `ui` trug sehr wohl, beide hatten am 03.09. auf alle siebzehn geantwortet — der Fehler lag auf dem Rueckweg, geprueft worden war der Hinweg |
| 2026-09-06 | Ergaenzt: **Aus Nichtwissen einen Vorwurf machen**. Anlass ist der teuerste Fehler dieses Tages: `tools/einbau.py` meldete `NIE GEANTWORTET`, gemessen war aber nur «keine Datei in unserer Ablage» — und 15 Antworten von `cloud` und `ui` lagen seit dem 03.09. in einem Verzeichnis, in das wir nie sehen. Der Vorwurf war da bereits uebergeben |
| 2026-09-06 | Ergaenzt: **Abgelehnt (Lauf gegen Frage)**. Anlass ist eine Falle, die beim Bau von `tools/antwort.py` fast eingebaut wurde: Ein begruendetes Nein auf eine Frage haette als `abgelehnt` weiter als OFFEN gezaehlt — wir haetten nachgefragt, was uns beantwortet wurde |
| 2026-09-06 | Ergaenzt: **Ein Wort, zwei Gegenstaende**. Anlass ist eine ueberschriebene Datei: Ein neuer Ordner `auftraege/prompts/` fuer den dritten Zustellweg liess `tests/test_prompts.py` entstehen — die es mit 59 Proben zur Prompt-Bibliothek des Bildgenerators schon gab. Aus der Versionsgeschichte zurueckgeholt, Ordner in `auftraege/bloecke/` umbenannt |
| 2026-09-06 | Ergaenzt: **Ein Kommentar ist kein Waechter** und **Die Probe prueft ihre eigene Zufaelligkeit**. Beide Anlaesse sind Fehler in der eigenen Absicherung: Der Stichtag des Zustellbelegs ging zum zweiten Mal veraltet hinaus, obwohl ein Kommentar daneben genau davor warnte; und eine Probe zur Sortierreihenfolge war nur gruen, solange zwei Auftraege in dieselbe Sekunde fielen — unter Last wurde sie rot, weil der Code korrekt sortierte |
| 2026-09-03 | Ergaenzt: **Tiefenpass (Z-Pass) und Material-ID-Pass**, **Transparenz-Bounce**, **Alphakanal / alphaMode: BLEND**. Anlass ist der Rueckschritt von Demolauf 17: Bildwert 0.2015 -> 0.000 bei einem Modell, das BESSER geworden war. Gemessen: Die Kette war unveraendert (beide Laeufe rechnen auf vier Stellen nach), die REFERENZ war es nicht — der Tiefenpass sah durch 750 Glas-Primitive hindurch, im Median 4.49 m tiefer als der eigene Rand, an 2106 Punkten bis in den Hintergrund. Glas im Soll dicht gemacht: Score zurueck auf 0.2001. Drei Scheinproben trennen den Befund vom Eingriff |
| 2026-09-03 | Ergaenzt: **Base64** und **Kastenmittel (Box-Filter)**. Anlass ist die Naht «Aufs Blatt», die zum zweiten Mal das Regelergebnis der eigenen Kette abwies: Der Deckel vergleicht Base64-ZEICHEN, die Meldung nennt die Grenze aber als waere sie eine Byte-Zahl — 1 048 576 Zeichen sind 786 432 Byte, nicht 1.0 MB. 60 von 66 Nutzbildern lagen darueber. Das Kastenmittel ist die Art, wie die neue Blattfassung verkleinert, und der Eintrag traegt mit, warum nicht der naechste Nachbar |
| 2026-09-03 | Ergaenzt: **Abgelegt gegen ausgeliefert** und **Stale Bytecode nach einer Mutationsprobe**. Anlass ist ein Rueckstand, der keiner beim Adressaten war: Zwei `ui`-Auftraege lagen zwei bzw. einen Tag im Repo und waren nie hinausgegangen — abgelegt und ausgeliefert sahen in jeder Zaehlung gleich aus. Der zweite Eintrag stammt aus der Pruefung dieses Baus: Eine gleich lange Mutation, in derselben Sekunde zurueckgestellt, lief aus dem Zwischenspeicher weiter und meldete eine rote Probe, die es im Quelltext nicht mehr gab |
| 2026-09-02 | Ergaenzt: **Geerbter Vorbehalt** und **Die Bedingung nicht hergestellt**. Anlass ist die Nachrechnung eines fremden Befundes: Der Nachbargebaeude-Vorbehalt reproduziert hier nicht — er gilt fuer den Schaetzer und nicht fuer die Szene. Zwei von drei Anlaeufen der Messung stellten die Bedingung gar nicht her (9,8 % und 14,1 % Hintergrunddeckung statt 51,7 %) |
| 2026-09-02 | Ergaenzt: **Fassungsabstand (zwischen zwei Maschinen)**, **Erfundener Status**, **Selbstbindung (gegen Hausregel)**. Anlass: Das Repo liess sich hier nicht mehr einlesen (Python 3.14 drueben, 3.11 hier, 25 Sammelabbrueche gegen «alles gruen» auf der anderen Seite); drei Ergebnisse mit einem Status, den der Vertrag nicht kennt, galten als beantwortet; und der Deckel bindet nur den, der ihn eingefuehrt hat |
| 2026-09-01 | Ergaenzt: **Ungedrueckter Schalter**. Anlass sind drei Fehler desselben Tages, alle an Schaltern, die nie eine Probe gedrueckt hatte. Gemessen: 9 von 33; zwei waren kaputt, drei weitere nicht einmal pruefbar, weil `abholen.main()` kein argv entgegennahm — ein Einstieg, den keine Probe aufrufen kann, hat keine ungeprueften Schalter, er ist selbst einer. Nach dem Bau: 0 |
| 2026-09-01 | Ergaenzt: **Gleichstand (in einer Auswahl)** und **Eine Zahl, die an einer falschen Messung geeicht wurde**. Anlass ist ein Folgeposten ohne Adressaten aus der Abstandsberichtigung der HomeStation: Nachgemessen kennt die Standpunktguete ueber acht taugliche Standpunkte hoechstens ZWEI Werte, auf einem Wuerfel einen — und 16 von 56 Kombinationen erreichen den Bestwert. Der Flaechenanteil entscheidet den besten Standpunkt in einer von sechs Formen |
| 2026-09-01 | Ergaenzt: **Vorzeichenfehler**, **Einbahnstrasse (zwischen Annahme und Entscheidung)**, **Umfeld (gegen Bauwerk und Gelaende)**. Anlass sind zwei Messungen der HomeStation an einem echten Modell: Das Gebaeude stand auf dem Kopf, und keine Massprobe konnte es sehen (R_x(180) laesst jede Kantenlaenge gleich); und die Gelaenderegel fand auf echtem Bestand nichts — das Gelaende hiess `IfcCovering_Toposolid_1`, die Bauwerksbox schrumpfte um 2,1 % statt um 34,5 %. Der zweite Eintrag stammt aus einem Fehler im eigenen neuen Waechter desselben Tages |
| 2026-09-01 | Ergaenzt: **Ein Feldname, zwei Bedeutungen**, **Formpruefung statt Inhaltspruefung**, **Die Attrappe baut die kaputte Gestalt nach**. Anlass ist ein Absturz, der den Takt auf seinem ersten Schlag beendet haette: `auflagen` traegt zwei Formen, `darf_starten` ruft `.get`, sechs der acht laufbaren Auftraege trugen die Liste — und der Aufruf stand ausserhalb der Absicherung. Gefunden Stunden nachdem derselbe Auftrag fuer entsperrt erklaert und auf Rang 1 gesetzt worden war |
| 2026-09-01 | Ergaenzt: **Zustellbeleg**, **Antwortverhalten (eines Adressaten)**, **Rang (eines Auftrags)**. Anlass ist eine Zaehlung: Elf der 28 offenen Auftraege lagen bei zwei Adressaten, von denen noch NIE eine Antwort kam — sichtbar wurde das erst, als nicht mehr Ergebnisdateien gezaehlt wurden, sondern abgeleitete Zustaende. Der Rang-Eintrag traegt mit, warum eine Reihenfolge erst mit einem Zeitgeber zur Entscheidung wird |
| 2026-09-01 | Ergaenzt: **Auftragsart (multipass, render, qa, frage)** und **Rueckstandsdeckel**. Anlass sind neun Auftraege an die HomeStation, die `qa` trugen und eine Frage meinten — ein Sammellauf haette fuer jede einen Fehlschlag geschrieben. Der Deckel-Eintrag traegt den Satz mit, der ihn noetig machte: Ein Rueckstand waechst nicht durch eine Entscheidung, sondern durch vierzig kleine |
| 2026-09-01 | Ergaenzt: **Ersatzmessung / Ersatzkalibrierung**, **Mitgebrachter Vorbehalt**, **Fixpunkt eines Masses**. Anlass ist die Ersatzkalibrierung der Paarschwellen: 176 Zeilen, davon 88 Dubletten — 44, weil die vierte Szene (`raeume`) in allen Zeilen exakt die Zahlen der ersten lieferte, und 44, weil vier der elf Fallarten Fixpunkte von rho sind. **Berichtigt:** Der Befund vom 27.08. war als «symmetrische Kamerapaare» gedeutet — die Punktgleichheit tritt auch beim asymmetrischen `hochbau` auf und haengt am Mass, nicht am Bauwerk |
| 2026-08-28 | Ergaenzt: **Abgeleiteter Zustand**. Anlass ist eine Messung der HomeStation: 63 Auftraege, 44 Ergebnisse, 40 Paare, und kein einziger Auftrag mit Zustandsfeld — der Ordner sicherte einen Zustand zu, den er nicht fuehrte. Der Eintrag traegt die fuenf abgeleiteten Werte und den Satz, um den es geht: Ein Ergebnis zu haben heisst nicht, beantwortet zu sein |
| 2026-08-28 | Ergaenzt: **Doppelte Vorgabe**. Anlass: Ein Owner-Entscheid vom 23.08. (Kamera waagrecht statt gekippt) wurde in der Bibliothek umgesetzt, im ausfuehrenden Skript nicht — fuenf Tage lang kippte jeder Lauf. Kein Test schlug an, weil beide Stellen fuer sich schluessig aussahen; aufgefallen ist es dem Owner am fertigen Bild. Der Eintrag traegt die Abhilfe mit: nicht angleichen, sondern die zweite Stelle streichen |
| 2026-08-27 | Ergaenzt: **Boden einer Kennzahl**. Exakt bestimmt: Ein gleichfoermiges Bild bekommt bei geom_iou genau den Vordergrundanteil der Szene — auf drei Szenen auf volle Rechengenauigkeit gleich, also Arithmetik und kein Messwert. Der Eintrag traegt mit, warum das gefaehrlicher ist als eine ungenaue Zahl: 0,53 liest sich wie «zur Haelfte richtig» und heisst «die Szene ist gross» |
| 2026-08-27 | Ergaenzt: **Zustellweg (eines Auftrags)**. Anlass: Der Cloud-Worker hat unser Repo nicht, und vier Auftraege lagen deshalb an einem Ort, den ihr Adressat nicht oeffnen kann — gezaehlt wurden sie die ganze Zeit korrekt und sahen trotzdem nach Wartezeit bei ihm aus. Der Eintrag traegt die Regel mit, die daraus folgt: Ein Auftrag, den sein Adressat nicht erreichen kann, ist ein Rueckstand beim Absender |
| 2026-08-27 | Ergaenzt: **Beleg im Repo vs. Beleg am Geraet**. Anlass ist der teuerste Buchfuehrungsfehler des Projekts: Ein Posten stand sechs Tage als erledigt, waehrend auf dem Geraet eine sechs Tage aeltere Fassung lief — der Waechter prueft, ob ein Beleg EXISTIERT, und der existierte. Der Eintrag traegt mit, was ein Waechter hier ueberhaupt erzwingen kann: nicht die Wahrheit ueber ein fremdes Geraet, sondern die Angabe, welcher Art der Beleg ist |
| 2026-08-27 | Ergaenzt: **Obergrenze (eines Befundes)**. **Rasterdublette** um die Kameraachse erweitert (23 von 33 Fallarten auf vier Stellen identisch — eine Dublette braucht kein Staerkeraster, nur zwei Wege zur selben Zahl). **Paarurteil** um seinen staerksten Beleg: Die beiden Masse versagen in ENTGEGENGESETZTE Richtungen — ordentliches rho bei 2.8 % Umriss auf der einen Seite, Kantenanteil 1.0000 bei rho -1.0000 auf der anderen |
| 2026-08-27 | Ergaenzt: **Trennkurve (ueber benannte Faelle)**, und **Falsch frei / falsch gesperrt** um ihr zweites Auftreten erweitert. Anlass: Die Kalibrierung der Paarschwellen braucht eine Tabelle mit BEIDEN Fehlerzahlen — von Hand gerechnet waere sie wieder eine abgelesene Schwelle. Der Eintrag traegt mit, warum eine leere Gruppe *nicht beurteilbar* ergibt und nicht *sauber getrennt* |
| 2026-08-27 | Ergaenzt: **Abgelesene Schwelle** und **Selbstloeschende Meldung**. Beide fallen im selben Vorgang an: Gemessen wurde, dass ein VOLLSTAENDIG verschwundenes Bauwerk das Tor mit Score 0.951 besteht, waehrend das Paarurteil durchgefallen meldet (rho_maske -0.018). Sperren darf das Paarurteil noch nicht, weil seine beiden Schwellen abgelesen und nicht kalibriert sind (0.80 aus sieben Faellen einer Szene) — also wird der Widerspruch stattdessen sichtbar gemacht, und zwar mit einer Meldung, die nur in genau dieser Lage steht |
| 2026-08-26 | Ergaenzt: **Katalogbeweis (gegen Nullbefund ueber Hausnamen)**. Anlass ist ein Owner-Entscheid vom selben Tag: Seit der Maskenweg ein zweites Tor ist, kostet eine verworfene Bauwerksmaske das ganze Urteil — und sie wurde auf zwei von drei Testszenen verworfen, obwohl dort gar kein Boden steht. Der Eintrag traegt die Unterscheidung, die den Entscheid moeglich machte: Ueber IFC-Klassennamen ist «kein IfcSite dabei» ein Beweis, ueber Materialnamen («Beton», «kalksandstein») ist es keiner |
| 2026-08-26 | **Dreiwertiges Urteil** um die Frage erweitert, die sich erst stellt, wenn ZWEI solche Urteile zusammenkommen: Wie verknuepft man sie? Anlass ist ein Owner-Entscheid vom selben Tag (der Maskenweg ist ein zweites Tor). Die Antwort ist das UND nach Kleene — «falsch UND unbekannt» ist falsch, «wahr UND unbekannt» ist unbekannt — und der Eintrag traegt mit, warum Pythons eigenes `and` das NICHT tut: Bei ihm entscheidet die Reihenfolge der Argumente ueber das Ergebnis |
| 2026-08-26 | **Polaritaet (einer Tiefenkarte)** erweitert. Der Eintrag sagte, ein unbekanntes Vorzeichen zwinge zum Betrag, und der bewerte eine vollstaendig invertierte Karte wie eine perfekte. Das war bis zum selben Tag der Zustand unserer eigenen Kette — gemessen wurde das Vorzeichen seit dem 20.08., angewandt nur im Maskenweg. Die Luecke hat jetzt eine Zahl (0,7071 bestand die Grenze 0,65) und einen Test. Dazu die Auflage, die zwei Verwendungen trennt: Fuer einen Diagnosewert darf die deklarierte Angabe einspringen, fuer ein Urteil nicht |
| 2026-08-26 | Ergaenzt: **Geometrieanteil**, **Grenzstaerke**, **Rasterdublette**. Anlass ist die zweite Schwellenstudie, die dieselbe Kalibrierung auf echte Geometrie stellt: Der Geometrieanteil faellt dabei von 0,4489 auf 0,0822 bis 0,1730 — und `geom_iou` haengt an ihm, die Schwelle ist also nicht dieselbe. Die beiden anderen Eintraege tragen mit, was an einer Kalibrierung **gesetzt** und nicht gemessen ist (Grenzstaerke) und wie ein Stärkeraster in ganzen Bildpunkten eine Auswertung verfaelschen kann, ohne dass eine Zahl falsch gerechnet waere (Rasterdublette) |
| 2026-08-26 | Ergaenzt: **KosmoVis**, **KosmoOrbit**, **KosmoDraw**. Die drei meistgenannten Namen des Repos — 399 Nennungen zusammen — hatten keinen Eintrag. Anlass ist eine Owner-Klarstellung: `ai-imaging-in-a-box` IST KosmoVis, das eigene Repo ist nur die Trennung fuer die Vertiefungsarbeit. Die Wendung «Vorlaeufer KosmoVis» in etlichen Docstrings meint den aelteren Stand DERSELBEN Sache und nicht ein fremdes Produkt — falsch gelesen sucht man Fehler an der falschen Stelle |
| 2026-08-26 | Ergaenzt: **Verdeckung** und **Triage**. Anlass ist die Durchsicht der 80 Funktionen ohne Aufrufer: `kameras.ziehe_bis_frei` behandelt Verdeckung und laeuft nirgends, und an unserer synthetischen Testgeometrie verdeckt nichts — ein Anschluss haette gruene Tests ergeben, die ueber den Ernstfall nichts sagen |
| 2026-08-26 | Ergaenzt: **Waechter** und **Toleranzband**. Anlass ist der neue `tests/test_readme.py`: Das README nannte 1509 Tests bei 3595 wirklichen und behauptete in Fettschrift einen nie stattgefundenen Bildlauf, den es acht Tage zuvor gegeben hatte. Bewacht wird nur das maschinell Entscheidbare — eine Zahl, eine Datei, eine Funktion. **Kein Waechter auf Prosa:** eine Sondierung ueber veraltete Konstantenzitate in Docstrings ergab am selben Tag einen Treffer auf fuenf Fehlalarme |
| 2026-08-26 | **Integrationstest** um den Grund erweitert, warum viele gute Einzeltests ihn nicht ersetzen — mit dem Fall vom selben Tag: Acht Pruefungen einzeln gruen, und eine Angabe ging auf ihrem letzten Meter verloren. Der Einzeltest fragt, ob ein Stueck haelt, was es verspricht; der Integrationstest fragt, ob das Versprochene ankommt |
| 2026-08-26 | Ergaenzt: **Der Nullpunkt des Azimuts (Sued- gegen Nord-Konvention)**. Anlass ist das Anschliessen des Sonnenstands: Die beiden gebraeuchlichen Festlegungen liegen 180 Grad auseinander und vertauschen Vormittag und Nachmittag. Der Eintrag traegt mit, warum der Fehler an keinem einzelnen Bild erkennbar waere — und warum die gewaehlte Annahme darum in jeden Bericht gehoert |
| 2026-08-26 | Ergaenzt: **Zweizaehlige Drehsymmetrie**. Anlass ist ein Renderlauf fuer nichts: Bei einem Quader sind die beiden vorgeschriebenen Ueber-Eck-Ansichten Byte fuer Byte identisch. Der Eintrag traegt mit, warum es sich an der Huellbox NICHT entscheiden laesst — und warum die eingesparte Ansicht hinterher nicht mitzaehlen darf |
| 2026-08-26 | Ergaenzt: **Dauerwarnung**. Nachgemessen: Drei Warnungen feuerten bei jedem Auftrag und fuellten damit alle drei Plaetze der Anzeige — jede echte Warnung, die im Ablauf spaeter entsteht, war unsichtbar. Der Eintrag traegt die billige Probe mit (erscheint sie auch, wenn gar nichts vorliegt?) und den Grund, warum Loeschen keine Abhilfe ist, sondern Verschweigen |
| 2026-08-26 | Ergaenzt: **Die blinde Wache**. Anlass ist eine Fortschrittswache, die fuenf Laeufe lang auf `out/` sah, waehrend nach `out/<kuerzel>/` geschrieben wurde — und als laengste Pause jeweils exakt die Gesamtdauer meldete. Der Eintrag traegt das Erkennungszeichen mit: Eine zu GLATTE Meldung ist keine Messung, sondern das Fehlen einer |
| 2026-08-26 | Ergaenzt: **Geteilte Parameter (Parameter Sharing)**. Der technische Kern des Fehlschlags vom 25.08.: 67 gemeinsame Stuecke, und danach blieben 454 von 521 Teilen des Bildmodells liegen. Der Eintrag traegt mit, warum die Abhilfe NUR auf dem Auslagerungsweg greifen darf — eine Reparatur, die den gesunden Fall verteuert, kann ihn in den kranken kippen |
| 2026-08-26 | Ergaenzt: **Auslagerung (Offloading) und der Geraeteweg**. Anlass sind drei verlorene Stunden am 25.08.: Der gewaehlte Weg wurde gemessen und nirgends geschrieben, und darum sah ein Fehlschlag wie ein Rueckfall im Code aus. Entschieden hatten zwei Zehntel Gigabyte freier Kartenspeicher |
| 2026-08-26 | Ergaenzt: **Vorpruefung (Abbruch vor dem teuren Schritt)** und **Abbruchschwelle**. Anlass ist ein Owner-Einwand vom 25.08.: Die Geometriepruefung lief bis dahin NACH der Bilderzeugung, obwohl die entscheidende Angabe lange vorher vorliegt. Die Abbruchschwelle traegt ihre Zahl mit (`BILDBREITE_ABBRUCH = 0.65`) und damit auch den Waechter aus `tests/test_lexikon.py` — der zweite Eintrag dieser Woche, der bei der naechsten Aenderung im Code nicht mehr still veralten kann |
| 2026-08-25 | **Zwei veraltete Zahlen im Text berichtigt, die nur im Aenderungsverzeichnis korrigiert waren.** *Stuerzende Linien* nannte weiterhin 9,46° Neigung, obwohl die Zahl zweimal nachgemessen und zuletzt auf -0,51 bis +5,98 Grad korrigiert worden ist. *Kreisschluss* fuehrte 0,2269 als unabhaengigen Boden, ohne dass er der Bildlage gehoert (Faktor 14). Eine Korrektur, die nur im Verzeichnis steht, erreicht niemanden, der den Begriff nachschlaegt — genau die Falle, gegen die dieses Verzeichnis gebaut ist |
| 2026-08-25 | **Deckungsgrad** berichtigt (0.70 statt 0.55) und um den Grund erweitert — der Wechsel war eine gemessene Entscheidung und keine Geschmacksfrage. Dazu ergaenzt: **Rahmen gegen Messen (der Rahmungsbruch)**, der groesste Einzelbefund dieser Woche. Ein Eintrag, der eine Zahl nennt, veraltet mit ihr — das ist dieselbe Falle wie eine Zahl an zwei Stellen im Code, nur im Anhang |
| 2026-08-24 | Ergaenzt: **Durchgelaufen gegen richtig**. Anlass ist eine Luecke, die beide IFC-Leser teilen: neun echte Dateien, null Fehler — und kein einziger Vergleich, ob die herausgekommene Geometrie der Vorlage entspricht. Der Eintrag traegt mit, warum sich das nur an selbst erzeugten Dateien pruefen laesst, und was so eine Pruefung ueber echte Dateien NICHT beweist |
| 2026-08-24 | Ergaenzt: **Ortsfeld (eines Tiefenschaetzers)**. Der schwerwiegendste Befund dieser Woche, und er sass unter dem Tor: Was unser Schaetzer auf einem leeren Bild ausgibt, ist zu 95,75 % eine Funktion des ORTES. Dieselbe Maske verschoben laesst den Nullwert von -0,62 auf +0,65 wandern, mit Vorzeichenwechsel — eine Konstante, die wir seit dem 21.08. als solche gefuehrt haben, ist eine Zahl fuer EINE Bildlage |
| 2026-08-23 | Ergaenzt: **Klassifikatorfreie Fuehrung (und warum ein Negativ-Prompt daran haengt)**. Anlass ist eine Zaehlung: Sieben von sieben Stilen fuehren einen negativen Prompt, keiner erreicht je ein Bild — und auf dem voreingestellten Modell koennte er ohnehin nichts bewirken. Der Begriff erklaert, warum das kein Fehler im Prompt ist, sondern eine Eigenschaft des Verfahrens |
| 2026-08-23 | Ergaenzt: **Anwesenheitsmass gegen Guetemass**, und **Zufallsniveau** um den Fall des Rangmasses erweitert. Anlass ist ein Befund beim Nachbauen eines fremden Vorschlags: Sein Zufallsniveau ist 50 % und folgt aus der Konstruktion, die vorgeschlagene Schwelle lag bei 45 % — also darunter. Sie war an einer einzigen Ziehung abgelesen, und dieselbe Ziehung streut von 23 bis 77 % |
| 2026-08-23 | Ergaenzt: **Stehengebliebenes Feld**, und **Vertragsfeld** um seine Eingangsseite erweitert. Anlass ist eine Zaehlung am eigenen Code: Fuenf Felder, die die Oberflaeche setzen darf, bewirken bei uns nichts — der Sonnenstand darunter, und der ist der gefaehrlichste, weil das Bild sauber belichtet und falsch zurueckkommt. Dieselbe Fehlerart wie die tote Kante, nur von der Eingangsseite |
| 2026-08-23 | Ergaenzt: **Betragsmass gegen Rangmass**. Am selben Abend nachgereicht, weil die HomeStation die Frage nach dem groesseren Schaetzer als falsch gestellte entlarvt hat: Der Schaetzer ORDNET richtig und staucht nur den Betrag. Damit ist es keine Frage der Modellgroesse, sondern eine der Masskonstruktion — und der Preis des Rangmasses (es beantwortet Anwesenheit, nicht Guete) steht mit im Eintrag |
| 2026-08-23 | Ergaenzt aus einer Messung, die ein Mass erledigt hat: **Himmel hinter dem Umriss** und **Zustaendigkeitsgrenze (eines Messverfahrens)**. Die HomeStation hat dieselbe Kamera dreimal gerechnet und nur den Hintergrund getauscht — mit einem Nachbargebaeude dahinter trennt die Umrisstreue ein perfektes Bild nicht mehr von weissem Rauschen. Daraus folgt keine bessere Normierung, sondern eine dritte Antwort neben bestanden und durchgefallen |
| 2026-08-23 | **Vertragsfeld** ausgebaut statt verdoppelt: Ich hatte einen zweiten Eintrag dazu geschrieben, `test_lexikon` fing ihn, und der Test hatte recht — der Begriff stand laengst da. Ergaenzt ist die andere Seite derselben Sache: Alles, was KEIN Vertragsfeld ist, muss daneben landen, und wenn „daneben" in Wahrheit „gar nicht" heisst, ist es umsonst gerechnet |
| 2026-08-23 | Ergaenzt: **Auswahleffekt beim Minimum (Extremwertstatistik)**. Anlass ist eine Nebenwirkung der Umstellung auf drei Ansichten: Das Urteil ist das der schwaechsten Kamera, und ein Minimum faellt mit der Zahl der Ziehungen — um rund 0,19, also mehr als jeder Parametereffekt der Kette. Niemand hatte das entschieden |
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
| 2026-09-19 | Ergaenzt aus dem Schichtenbau der Bildkette: **Basis (eines Bildes)**, **Basis-Urteil (geerbtes Urteil)**, **Variantenstudie**. Ausgebaut: **Geometrielayer und AI-Imaging-Layer** um den Ort im Code und die Abgrenzung zur *Ebene (Layer) in einer Bilddatei*, **Handeingriff** um das, was er seit heute NICHT mehr wegwirft. **Nicht** nachgetragen wurden Geometrielayer und AI-Imaging-Layer als eigene Eintraege: Sie standen schon in Abschnitt 8, und ein zweiter Eintrag desselben Begriffs macht die Luecke unauffindbar statt kleiner |
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
