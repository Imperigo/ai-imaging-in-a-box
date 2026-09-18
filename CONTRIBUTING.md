# Mitwirken an Visbox

Visbox erzeugt Architektur-Visualisierungen aus einem Gebäudemodell — und misst
hinterher nach, ob das erzeugte Bild wirklich zu diesem Modell gehört. Der Kern der
Arbeit ist nicht das Erzeugen, sondern das Messen.

Dieses Dokument sagt Ihnen, **woran ein Beitrag hier scheitert**. Es ist absichtlich
unfreundlicher als die übliche Vorlage: Eine halbe Stunde Lesen ist billiger als ein
Pull Request, der aus Gründen abgelehnt wird, die niemand vorher aufgeschrieben hat.

---

## Drei Dinge vorweg, und keines davon ist verhandelbar

### 1 · Alles ist auf Deutsch. Auch der Quelltext.

Kommentare, Docstrings, Fehlermeldungen, Testnamen, Commit-Nachrichten — alles.
Bezeichner (Variablen, Funktionen, Schlüsselnamen) sind deutsch, aber **ASCII ohne
Umlaute**: `bauwerksmaske`, `geometrie_qa`, `schwelle_folgt`. Fliesstext bekommt
richtige Umlaute, Bezeichner nicht.

Und durchgehend **Schweizer Schreibung: „ss", nie das Eszett.** Auch in einer Datei,
die sonst niemand liest.

> **Das ist eine echte Hürde, und wir verschweigen sie nicht.** Wer gern beiträgt, aber
> kein Deutsch schreibt, kann hier praktisch nicht beitragen. Wir halten das trotzdem
> so: Visbox ist die Vertiefungsarbeit an einer deutschsprachigen Hochschule, der Code
> ist Teil der Abgabe, und ein zweisprachiges Repo wäre in beiden Sprachen schlechter
> als dieses in einer. Der Preis ist bekannt und bezahlt.

Ein Pull Request mit englischen Docstrings wird nicht übersetzt, sondern
zurückgegeben. Das ist keine Geringschätzung — es ist die einzige Antwort, die die
Regel am Leben hält.

**Eine Warnung aus eigener Erfahrung:** Lassen Sie **nie** eine Wortersetzung über eine
ganze Datei laufen, um Schreibungen anzugleichen. Sie trifft Bezeichner, und der
Schaden ist danach über die ganze Datei verteilt.

### 2 · Dies ist eine Vertiefungsarbeit mit Abgabetermin

Ende Februar 2027. Bis dahin entscheidet der Plan (`docs/PLAN_BIS_FEBRUAR_2027.md`),
was gebaut wird — nicht die Reihenfolge der eingehenden Pull Requests. Ein guter
Beitrag, der nicht auf dem Plan steht, kann **liegen bleiben**, ohne dass etwas mit ihm
falsch ist.

Darum: **Erst ein Issue, dann Code.** Bei allem, was grösser ist als eine Zeile.

Ab dem 1. Februar 2027 wird kein neues Merkmal mehr aufgenommen. Fehlerbehebungen
weiterhin.

### 3 · Es gibt heute keine CI. Sie sind die CI.

Kein Lauf prüft Ihren Pull Request automatisch nach. Was Sie nicht selbst laufen
lassen, hat niemand laufen lassen:

```
python3 -m pytest
```

Die gesamte Testsammlung läuft **ohne GPU und ohne Modellgewichte** — das ist Absicht
und soll so bleiben. Wer einen Test schreibt, der eine GPU braucht, hat einen Test
geschrieben, der bei fast allen nicht läuft.

Zielhardware ist ausdrücklich ein Laptop (MacBook M1 Max), nicht eine Arbeitsstation
mit grosser Grafikkarte. Was nur auf schneller Hardware erträglich ist, ist hier kein
fertiges Merkmal.

---

## Die vier Regeln, und was sie für Ihren Beitrag heissen

Sie stehen vollständig in [`CLAUDE.md`](CLAUDE.md). Jede hat einen Wächter in der
Testsammlung — sie sind also nicht Absichtserklärung, sondern ausführbar.

### Regel 1 · Nur permissive Lizenzen. Kein GPL, kein AGPL.

Erlaubt ist, was unter **MIT, BSD, Apache-2.0 oder MPL-2.0** steht. Ein Beitrag, der
eine GPL- oder AGPL-Abhängigkeit mitbringt, **kann nicht angenommen werden** — auch
nicht als optionaler Zusatz, auch nicht „nur für die Entwicklung".

* **Prüfen Sie an der Primärquelle**, nicht am Wikipedia-Eintrag und nicht an der
  Kachel auf einer Paketseite. In diesem Projekt hat eine Sekundärquelle schon einmal
  *in die gefährliche Richtung* falsch gelegen: Sie meldete permissiv, wo Copyleft
  stand (Krita AI Diffusion).
* **Binärpakete zählen mit.** Ein Wheel kann statisch gelinkten GPL-Code mitbringen,
  den seine eigene Lizenzangabe nicht erwähnt — genau das tut `ifcopenshell` mit CGAL.
* **Modellgewichte zählen mit.** Non-Commercial-Lizenzen (FLUX.1-dev, FLUX.2-dev) sind
  ausgeschlossen, und ein LoRA erbt die Lizenz seines Grundmodells.
* **Einen GPL-Fund melden Sie ausdrücklich**, statt ihn stillschweigend zu umgehen. Im
  Repo stehen zwei solche Funde namentlich; das ist die gewünschte Form.

LGPL ist zugelassen, aber nur hinter einer Prozessgrenze, unverändert, austauschbar
und im [`NOTICE`](NOTICE) deklariert. Jeder Copyleft-Eintrag dort trägt eine Zeile
`AUFLOESUNG:` mit genau einem von drei Werten, und ein Test liest sie.

**Wenn Ihr Beitrag eine neue Abhängigkeit mitbringt, gehört in den Pull Request: Name,
Version, Lizenz, und wo Sie die Lizenz nachgelesen haben.** Ohne das kann niemand
zustimmen.

### Regel 2 · Blender nur als eigener Prozess

* Erlaubt: `blender --background --python <skript>` als Subprozess.
* Verboten: `import bpy` im Produkt-Environment, das `bpy`-Wheel, jede
  Add-on-Verpackung (`bl_info`, `register()`), jede Abhängigkeit von einer laufenden
  Blender-Oberfläche.

Blender steht unter GPL. Die saubere Grenze ist der Prozessaufruf, nicht der Import —
und sie fällt, sobald jemand ein `import bpy` schreibt, um „kurz etwas zu prüfen".
Dasselbe gilt für `ifcopenshell`, das in einem eigenen Environment (`.venv-ifc`) lebt
und ausschliesslich als Subprozess angesprochen wird.

### Regel 3 · Keine echten Daten, keine echten Namen

* Keine IFC-Dateien, Pläne, Renderings oder Gewichte aus echten Projekten.
* Keine Büro-, Kunden- oder Projektnamen — auch nicht in Pfaden, Kommentaren oder
  Testfixtures.
* **Keine absoluten Pfade mit einem Benutzernamen darin.**

Der letzte Punkt ist der, an dem es hier wirklich passiert ist: Ein Klarname kam nicht
durch Nachlässigkeit beim Schreiben ins Repo, sondern über **Fehlertexte** — ein
Traceback bringt den vollen Skriptpfad mit, und darin steht der Benutzername. Ein
Wächter liest deshalb heute jede versionierte Textdatei darauf durch.

Testgeometrie wird **erzeugt**, nicht abgelegt:

```
python3 tools/make_test_ifc.py build/testbau.ifc
```

### Regel 4 · Der Kern ist eine Bibliothek

Jede Fähigkeit muss aus Python heraus nutzbar sein, ohne dass eine Oberfläche läuft.
Die Oberfläche ist eine dünne Schicht darüber, nie deren Voraussetzung. Kein Import
eines Oberflächen-Frameworks im Kern.

Faustregel: **Was nur über einen Klick erreichbar ist, existiert nicht.**

---

## Wie hier geschrieben wird

### Kommentare tragen das WARUM und den Messwert

Was der Code tut, steht im Code. Ein Kommentar, der ihn nacherzählt, veraltet und
lügt danach. Was nicht im Code steht und verlorengeht, ist der Grund — und die Zahl,
die zu diesem Grund geführt hat.

**Und wo eine Zahl steht, steht daneben, ob sie GEMESSEN oder GESETZT ist.** Das ist
keine Formalie: Eine gesetzte Schwelle ist eine Annahme, eine gemessene ist ein Befund,
und wer sie später anfasst, muss wissen, welches von beidem er gerade anfasst.

### Die dritte Antwort: `None` heisst NICHT GEMESSEN

Nicht „in Ordnung", nicht `0`, nicht `False`. Eine Messung, die nicht stattgefunden
hat, wird als solche zurückgegeben und weitergereicht.

Wer hier `0.0` für eine ausgefallene Messung einsetzt, erzeugt eine Zahl, die aussieht
wie ein Befund und keiner ist. Das ist der teuerste Fehler, den dieses Projekt kennt.

### Fail-closed, aber unterscheidbar

Was ungeprüft ist, wird **nicht** durchgelassen. „Nicht gemessen" und „durchgefallen"
führen beide dazu, dass nichts passiert — aber sie bleiben im Ergebnis **zwei
verschiedene Auskünfte**. Ein Tor, das beide zu einem `False` verrechnet, hat die
Information vernichtet, die man zur Fehlersuche braucht.

Ein gebautes Beispiel: `geometrie_qa.zwei_tore(...)` gibt `bestanden = None` zurück,
wenn die Gegenprobe zeigt, dass die Messung gar nicht trennt — *ein Prüfverfahren, das
auch die falsche Antwort durchlässt, hat nicht die richtige bestätigt.*

### Messen statt behaupten

Das Repo unterscheidet durchgehend zwischen dem, was gemessen wurde, und dem, was
angenommen wird — im Code, in den Dokumenten und in den Commit-Nachrichten. Wo etwas
nicht gemessen werden konnte, steht das dabei.

**Eine benannte Lücke ist besser als eine, die nach Vollständigkeit aussieht.**

---

## Die Mutationsprobe: zu jedem Wächter gehört eine

**Ein bestandener Test ist kein Beleg dafür, dass er etwas geprüft hat.**

Wer hier eine Prüfung einbaut — ein Tor, eine Schwelle, einen Wächter —, baut eine
Probe dazu, die **rot wird, wenn man den Wächter entschärft.** Und führt sie aus:

1. Den Wächter entschärfen (Schwelle verstellen, Bedingung umdrehen, Zeile
   auskommentieren).
2. Die Testsammlung laufen lassen.
3. Nachsehen, dass der erwartete Test **wirklich** rot ist.
4. Zurücksetzen.
5. **Das Ergebnis in den Pull Request schreiben** — welcher Test fiel, und mit welcher
   Meldung.

Behaupten Sie die Probe nicht. Ein Wächter, der nicht fällt, bewacht nichts, und das
merkt man erst, wenn man ihn umstösst.

Die verwandte Falle heisst hier **Vakuumprobe**: eine Zusicherung über alle Elemente
einer Sammlung hält auch dann, wenn die Sammlung leer ist. `all(...)` über nichts ist
`True`. `tools/vakuumprobe.py` sucht solche Stellen; wenn Sie eine schreiben, gehört
eine Gegenprobe daneben, die zeigt, dass sich die Sammlung im umgekehrten Fall füllt.

---

## Das Lexikon wird mitgeführt

`docs/LEXIKON.md` erklärt jeden nicht-architektonischen Fachbegriff für Leser:innen
ohne Informatikhintergrund. Es ist Anhang der Vertiefungsarbeit, kein Nebenprodukt.

**Taucht in Ihrem Beitrag ein Fachbegriff auf, der dort noch nicht steht, tragen Sie
ihn nach — in demselben Pull Request.** Für Laien geschrieben: was es ist, wozu es
dient, wo es im Projekt vorkommt. Keine Definition, die einen anderen unerklärten
Fachbegriff voraussetzt.

---

## Loslegen

Voraussetzung: Python 3.11 oder neuer. Das Paket deklariert **keine**
Laufzeitabhängigkeiten, und das ist Absicht.

```
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Für die Geometrieseite zusätzlich das Environment hinter der Prozessgrenze — es bleibt
vom Produkt-Environment getrennt, weil `ifcopenshell` unter LGPL steht und GPL-Code
mitbringt:

```
python3 -m venv .venv-ifc && .venv-ifc/bin/pip install ifcopenshell trimesh numpy
```

Blender wird über `AIIMAGING_BLENDER` adressiert, die Modellablage über
`AIIMAGING_MODELLE`. Die vollständige Tabelle steht im [`README`](README.md).

Zum Verständnis des Projekts in dieser Reihenfolge: [`README.md`](README.md) →
[`CLAUDE.md`](CLAUDE.md) → `docs/LEXIKON.md` → das Modul, das Sie anfassen wollen. Die
Docstrings tragen hier die Begründungen; sie zu überspringen kostet mehr Zeit, als sie
zu lesen.

---

## Der Pull Request

* **Ein Thema pro Pull Request.** Zwei Themen brauchen zwei.
* **Commit-Nachrichten tragen das WARUM**, nicht das WAS. Die Änderung selbst steht im
  Diff.
* **Die Vorlage ausfüllen**, und zwar die Mutationsprobe wirklich. Siehe
  [`.github/pull_request_template.md`](.github/pull_request_template.md).
* **Testzahl im README**: Ein Wächter (`tests/test_readme.py`) vergleicht die im README
  genannte Anzahl Tests mit der wirklichen. Wenn Sie Tests hinzufügen, zieht er nach —
  lassen Sie die Sammlung laufen und tragen Sie die neue Zahl ein, sonst ist der Lauf
  rot und es sieht nach Ihrem Fehler aus.
* **Keine Formatierungswelle.** Ein Pull Request, der nebenbei die halbe Datei umbricht,
  ist nicht mehr prüfbar.

---

## Die Lizenz Ihres Beitrags

Visbox steht unter der **Apache License 2.0** (siehe [`LICENSE`](LICENSE)).

Es gibt **keinen CLA und keine Unterschrift**. Es gilt Abschnitt 5 der Apache-2.0: Wer
einen Beitrag absichtlich zur Aufnahme einreicht, stellt ihn unter dieselbe Lizenz —
sofern nichts anderes ausdrücklich dabeisteht. Wenn für Ihren Beitrag etwas anderes
gelten soll, schreiben Sie es hin, bevor wir ihn ansehen.

Reichen Sie nur ein, woran Sie die Rechte haben. Code aus einem GPL-Projekt lässt sich
hier nicht aufnehmen, auch nicht umgeschrieben.

---

## Umgangston

Es gilt der [Verhaltenskodex](CODE_OF_CONDUCT.md).

Kurzfassung für den technischen Teil: Hier werden **Befunde** hart geprüft und Menschen
nicht. Ein Pull Request, der eine Annahme dieses Projekts umwirft, ist willkommen — der
Ordner `docs/` ist voll von Stellen, an denen genau das passiert ist. Wer belegt, dass
eine Zahl hier nichts misst, hat dem Projekt mehr geholfen als jemand, der ein Merkmal
hinzufügt.

## Sicherheitslücken

Nicht als Issue. Siehe [`SECURITY.md`](SECURITY.md).
