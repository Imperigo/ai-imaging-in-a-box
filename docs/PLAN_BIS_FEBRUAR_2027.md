# Der Weg bis Februar 2027

**Grundlage:** keine
**Nachgesehen bis:** 57148bf
**Codestand:** `57148bf`

> Beruht auf der Kartierung vom 18.09.2026: **17 Agenten, 3,3 Mio. Token**, 14 Bereiche
> und drei Gegenprüfungen, die die Kartierung selbst widerlegen sollten — und es an
> fünfzehn Stellen taten, auch in meinem eigenen Entscheidblatt.

---

## Der Satz, an dem der ganze Plan hängt

> **Drei Dinge können dieses Vorhaben töten, und alle drei sind billig zu messen.**
> Sie werden deshalb im **Oktober** gemessen und nicht im Januar.

| | Risiko | Wenn es zutrifft | Messung | Braucht |
|---|---|---|---|---|
| **R1** | Auf Apple Silicon läuft gar nichts Sinnvolles | Die Zielhardware fällt weg — das Vorhaben braucht eine andere Fassung | Ein einziger Lauf: lädt `flux2-klein-4b` auf MPS und erzeugt ein Bild | **einen Mac** |
| **R2** | Die Tiefen-Naht ist für das kleine Modell nicht baubar | Entweder Lizenz oder Laptop fällt — beides nicht beides | Prototyp der Konditionierung, ein Bild gegen eine Tiefenkarte | GPU (HomeStation) |
| **R3** | `rho_maske` trennt auch nicht | **Die Forschungsfrage hat keine Antwort** | Nachrechnen an Daten, die schon da sind | **nichts — geht hier und heute** |

**R3 ist zuerst dran, weil es nichts kostet.** Die zwölf Bilder aus `auf-20260909-92`
liegen samt Zahlen im Repo. Wenn `rho_maske` gegen die falsche Soll-Karte **nicht**
trennt, ist die neu gefasste Forschungsfrage schon in der ersten Oktoberwoche tot — und
dann ist noch Zeit, eine andere zu stellen.

*Eine Arbeit, die ihr tragendes Risiko im Januar prüft, prüft es zu spät.*

---

## Was im Februar wahr sein muss

Fünf Sätze. Wenn alle fünf stimmen, ist die Arbeit fertig.

1. **Eine fremde Person lädt eine Datei, doppelklickt und kommt ohne Hilfe zu einem Bild
   ihres eigenen Modells.**
2. **Das Bild trägt die Geometrie nachweislich** — belegt mit einer Kennzahl, die **gegen
   die falsche Geometrie durchfällt**.
3. **Die Software hält Regel 1** — kein GPL, kein AGPL, keine Non-Commercial-Gewichte, und
   das ist ausführbar geprüft, nicht behauptet.
4. **Sie läuft auf einem MacBook**, und die Zahlen dazu sind **gemessen, nicht gerechnet**.
5. **Es gibt eine schriftliche Arbeit**, und sie ist nicht in der letzten Woche entstanden.

---

## Der kritische Pfad

```
R3 rho_maske trennt?  ──┐
                        ├──▶  Bildweg auf Apple Silicon  ──▶  Node-Oberfläche  ──▶  Skizze
R1 MPS läuft?  ─────────┤                                          │
R2 Naht baubar?  ───────┘                                          └──▶  Ein-Klick-Paket
```

**Was NICHT auf dem kritischen Pfad liegt** und darum jederzeit fallen darf: das iPad,
der Vergleichsknoten, Mehrsprachigkeit, Windows, Selbstaktualisierung.

---

# Die fünf Abschnitte

## Oktober · **Die drei Risiken, und ein Bild auf dem Mac**

*Ziel: Am 31. Oktober weiss ich, ob dieses Vorhaben in der geplanten Form möglich ist.*

| | |
|---|---|
| **R3 zuerst** | `rho_maske` gegen die falsche Soll-Karte nachrechnen. Geht hier, kostet einen Tag. **Ergebnis entscheidet über die Forschungsfrage.** |
| **R1** | Ein Mac-Lauf: MPS-Zweig in `render.py` (heute kennt sie nur `cuda` und `cpu`), `bfloat16` auf MPS prüfen. |
| **R2** | Tiefen-Konditionierung für `flux2-klein-4b` als Prototyp — auf der HomeStation, wo eine GPU steht. |
| nebenher | Die **Startsperre** beseitigen: `VORGABE_MODELLWURZEL = "/ai"` ist auf macOS nicht beschreibbar. *Eine Studentin läuft heute in einen Rechtefehler, bevor irgendetwas rechnet.* |

**Meilenstein:** ein Bild, erzeugt auf einem MacBook, aus einem importierten Modell.

## November · **Der Bildweg wird ein Werkzeug**

*Ziel: Der Weg Modell → Kamera → Render → Bild läuft über eine Oberfläche, nicht über
die Kommandozeile.*

* **Die Naht** (E5): lokaler Python-Dienst, Fortschritt über die ganze Laufzeit.
* **Die Knotenoberflaeche herausgelöst** — aus `NodeCanvas.tsx` (2992 Zeilen), gelöst von
  `@kosmo/ui`, vom Command-Store und vom Yjs-Sync.
* **Der Bild-Eingang**, und er ist der wichtigste Einzelposten des Monats:

> **Der `render`-Knoten hat heute keinen Bild-Eingang.** Bilder können im Graphen nur
> verglichen und aufs Blatt gelegt werden — nie wieder in eine Rechnung zurück. Damit
> haben Schritt 5 (Hineinskizzieren) und Schritt 6 (Photoshop ersetzen) **keinen Pfad,
> nicht einmal einen halben.**
>
> *Zweimal unabhängig nachgemessen.* Das ist kein Detail, sondern die Bedingung dafür,
> dass die zweite Hälfte des Entwurfsablaufs überhaupt existieren kann.

* **Der Speicherdeckel** (E16) wird gebaut. Heute gibt es keinen: `max_vram_gb` ist ein
  Auswahlfilter, kein Riegel zur Laufzeit, und der Artefakt-Zwischenspeicher hat weder
  Grössengrenze noch Verdrängung.

**Meilenstein:** Ein Ablauf im Knotenbaum, von der Datei bis zum Bild, ohne Terminal.

## Dezember · **Zeichnen, und der erste Text**

*Ziel: Der Entwurfsablauf schliesst sich — und die Arbeit beginnt zu entstehen.*

* **Zeichnen auf ein Bild.** Neubau: Der vorhandene Skizzenmodus zeichnet über den
  Grundriss, **nie über ein Rendering** (null Treffer für Bildhintergrund, Radiergummi,
  Ebene im ganzen Modul). Der Stiftdruck wird heute verworfen — nur `x`/`y` werden gelesen.
* **Maske und Inpainting**: aus dem Strich wird die Auswahl, aus der Auswahl ein neues Bild.
* **Ab hier jede Woche ein fester Anteil Schreiben.** Heute gibt es bei 700 Commits und
  123 750 Zeilen Code **null Zeilen Arbeitstext**. *Das ist die Falle dieses Vorhabens,
  und sie schnappt im Februar zu, nicht im Dezember.*

**Meilenstein:** Bild → hineinzeichnen → verändertes Bild. Der Ablauf ist geschlossen.

## Januar · **Auslieferung und Härtung**

*Ziel: Aus einem Programm, das bei mir läuft, wird eines, das bei Fremden läuft.*

* **Das macOS-Paket.** Tauri baut heute nur Linux (`bundle.targets: ["deb","rpm"]`).
* **Erststart-Erlebnis**: Blender prüfen, Gewichte holen, und vorher ehrlich sagen, wie
  viel und wie lange.
* **Was ein öffentliches Repo braucht und heute ganz fehlt**: `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `.github/`, CI — und eine README, die **einen einzigen
  Satz für jemanden hat, der die Software nur benutzen will.** Heute gibt es keinen.
* **Die Zeitgrenzen neu setzen.** 300 s und 900 s sind auf der schnellen Maschine geeicht;
  auf einem Mac auf der CPU lösen sie aus, ohne dass etwas kaputt ist.
* **Tastaturbedienung** der Knotenoberfläche: heute **0 × `tabIndex`, 0 × `role=`,
  0 × `onKeyDown`** in 2992 Zeilen.

**Meilenstein:** Jemand anderes installiert und benutzt sie, ohne mich zu fragen.

## Februar · **Schreiben, messen, abgeben**

*Ziel: Die Arbeit, nicht die Software.*

* Die Messreihen fahren, die in die Arbeit gehören — jede mit Gegenprobe.
* Text fertigstellen, Bilder wählen, Anhänge ordnen.
* **Kein neues Merkmal ab dem 1. Februar.** Was dann nicht läuft, läuft nicht.

---

# Wie ich arbeite, damit Sie wenig tun müssen

**Der Wochentakt:**

| | |
|---|---|
| Montag | Stand messen, nicht schätzen: Einbau-Stand, Rückstand, offene Entscheide |
| Mo–Do | bauen, je Baustein mit Probe und Mutationsprobe |
| Freitag | **Abgleich mit KosmoOrbit** (E18) und Sitzungsprotokoll |
| ab Dezember | dazu ein fester Anteil Arbeitstext |

**Was ich ohne Rückfrage tue:** bauen, messen, prüfen, dokumentieren, Aufträge an die
Worker stellen, nach `main` führen, meine Empfehlungen anwenden.

**Was ich Ihnen vorlege:** alles, was einen der fünf Sätze oben umwirft; jede Ausgabe von
Geld; jede Entscheidung, die eine zweite Software bindet; und **jeden Befund, der gegen
etwas spricht, das ich Ihnen vorher gesagt habe** — davon gab es an einem einzigen Tag
schon drei.

**Womit ich Sie nicht behellige:** Zwischenstände, Werkzeugfragen, alles, was ich selbst
messen kann.

---

# Die Risikoliste, nach Schwere

| | Risiko | Warum es zählt | Was es entschärft |
|---|---|---|---|
| 1 | **Kein Apple-Silicon-Pfad** — `mps` kommt im ganzen Python-Bestand null Mal vor | Ohne ihn läuft alles auf der CPU, und die Zielhardware ist eine Behauptung | **Oktober-Messung R1** |
| 2 | **Bild ist eine Sackgasse im Knotenmodell** | Schritt 5 und 6 des Ablaufs haben keinen Pfad | **November, Bild-Eingang** |
| 3 | **Kein Modell erfüllt alle drei Bedingungen** | Der Kern des Vorhabens | **Oktober-Messung R2** |
| 4 | **Null Zeilen Arbeitstext** bei 700 Commits | Eine Software ohne Arbeit ist keine Vertiefungsarbeit | **ab Dezember fester Anteil** |
| 5 | **Die Kennzahl trennt möglicherweise nicht** | Die Forschungsfrage | **Oktober-Messung R3, zuerst** |
| 6 | **Alle Hardwarezahlen sind gerechnet** | Zwei Entscheide stehen darauf | **ein Mac** |
| 7 | **`kosmo-lizenz`** — signierte Lizenz mit Widerrufsliste | Strukturell unvereinbar mit Apache-2.0; kommt in der ganzen Kartierung nicht vor | prüfen, bevor etwas übernommen wird |
| 8 | **287 Auftragsdateien liegen im öffentlichen Repo**, 268 nennen die HomeStation | Regel 3 gilt auch rückwirkend | Durchsicht im Januar |
| 9 | **Kein Hinweis, dass ein Bild KI-verändert ist** — null Treffer für C2PA oder Wasserzeichen | Ein Entwurfsbild kann in einem Baugesuch landen | Entscheid nötig, siehe unten |

---

# Was ich von Ihnen brauche, und wann

| wann | was | warum |
|---|---|---|
| **sofort** | Der Name — **Baugespann**? | Paketname, Titelblatt, jeder Dateikopf |
| **sofort** | **Abgabetermin und Form** | Der ganze Plan ist rückwärts gerechnet und steht auf einer Annahme |
| **im Oktober** | **Zugang zu einem M1 Max** | Ohne ihn bleibt Risiko 1 und 6 ungemessen bis zum Schluss |
| **im November** | Zwei Bildschirmfotos von Figma Weave | E7 ist von mir entschieden, ohne das Vorbild gesehen zu haben |
| **bis Dezember** | Soll ein KI-verändertes Bild als solches erkennbar sein? | Ein Entwurfsbild kann in einem Baugesuch landen. *Diese Frage stellt sich eine Arbeit an einer Architekturschule, oder jemand anderes stellt sie ihr.* |

---

## Zwei Berichtigungen an meinem eigenen Entscheidblatt

Die Gegenprüfung hat sie gefunden, und sie gehören hierher statt in eine Fussnote:

* **Blender-Fassung.** Ich schrieb *«verbindlich: 4.2 LTS»*. Im Code stehen **zwei**
  Fassungen nebeneinander: 4.2 für die CPU-Messungen, **5.2.0 LTS** für alles, was auf der
  HomeStation mit GPU lief. Eine Fassung festzuschreiben ist richtig — aber sie muss die
  sein, auf der die Messungen beruhen, und das ist zu klären, bevor sie im `INSTALL`
  steht.
* **Blender-Grösse.** Ich schrieb *«~300 MB»*. Gemessen sind **1,3 GB entpackt**. Das
  ändert den Entscheid nicht (nicht mitliefern), aber die Zahl war falsch.
