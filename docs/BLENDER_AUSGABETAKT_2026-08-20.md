# Blenders Standardausgabe taugt nicht als Fortschrittszeichen

**Zwei Messungen vom 20.08.2026 · Anlass: Fortschrittswache**

> **Kurzfassung für Eilige.** Auf der **CPU** schreibt Blender alle 32 Sekunden — ein
> grober, aber brauchbarer Takt. Auf der **GPU**, also auf der Maschine, die wirklich
> rendert, schreibt es **dreimal: am Anfang, eine Sekunde später, und am Ende.**
> Dazwischen 175 Sekunden Stille. Es gibt dort keine Frist, die einen Hänger fängt, ohne
> gesunde Läufe abzubrechen.
>
> Dieses Dokument hiess bis zum Nachtrag *„Blenders Standardausgabe hat einen Takt von
> 32 Sekunden"*. Der Titel stimmte für die Maschine, auf der gemessen wurde, und für
> keine andere. Die erste Hälfte ist absichtlich stehengeblieben — sie zeigt, wie
> überzeugend eine Zahl aussehen kann, die nicht überträgt.

---

## Teil 1 · Die CPU-Messung, und was sie zu beweisen schien

---

## Warum überhaupt gemessen wurde

`fortschritt.py` unterscheidet **belegte** von **behaupteten** Fortschrittszeichen: Ein
Statuswort behauptet nur, dass etwas laufe; ein Zeichen, das sich unabhängig vom Erzähler
bewegt, belegt es. Für einen Blender-Lauf war die naheliegende Quelle die
**Standardausgabe** — sie wächst, während Blender rechnet.

Die Frage dahinter war nicht, *ob* sie wächst, sondern **wie gleichmässig**. Eine Wache,
deren Frist unter dem Abstand zweier Ausgaben liegt, bricht jeden gesunden Lauf ab. Das
ist derselbe Fehler wie im Altbestand, nur in der Gegenrichtung: Dort stellt der Wächter
bei `status == "running"` die Uhr zurück und meldet darum **nie** etwas; hier hätte er
gemeldet, wo nichts war.

Beides sind Fehler, die man nur durch Messen vermeidet. Also gemessen.

---

## Aufbau

Blender 4.2 (`/opt/blender/blender`), `--background --factory-startup`, Cycles auf der
**CPU**, in diesem Entwicklungscontainer. Szene aus Bordmitteln erzeugt (Affenkopf,
Grundfläche, Sonne, Kamera), 512 × 512, **3000 Samples mit abgeschaltetem adaptivem
Sampling** — ohne diese Abschaltung war der Lauf nach 12 Sekunden fertig und damit zu
kurz für eine Aussage.

`stdout` und `stderr` in eine **Datei** umgeleitet, nicht in eine Pipe. Alle zwei Sekunden
die Dateigrösse abgefragt.

Der Umweg über die Datei ist kein Detail: Wer bei `PIPE` pollt statt zu lesen, blockiert
den Kindprozess, sobald der Puffer voll ist. Der Lauf bliebe dann stehen — durch genau die
Wache, die den Stillstand verhindern soll.

---

## Ergebnis

| Lauf | Dauer | Änderungen | Wachstum | Längste Lücke |
|---|---|---|---|---|
| 1 | 194 s | 6 | — | 32 s |
| 2 | 190 s | 6 | 937 Bytes | 32 s |

**Die Änderungszeitpunkte des zweiten Laufs: 34, 66, 98, 130, 162, 190 Sekunden.**

Das sind Abstände von 32, 32, 32, 32, 28 Sekunden. Kein Zufall, kein Puffereffekt, kein
Ausreisser — ein **Takt**.

Zum Vergleich der Umfang: 937 Bytes über 190 Sekunden, also rund **156 Bytes je
Ausgabe**. Blender schreibt in diesem Aufbau keine Fortschrittszeile je Sample, sondern
in festem Abstand eine kurze Zusammenfassung.

---

## Was daraus folgt

**Erstens: Es gibt ein Signal.** Die erste Vermutung beim Blick auf die frühen Zahlen war
„Blender schreibt während des Renderns gar nichts". Das war falsch, und der Unterschied
ist wichtig: nicht *kein* Signal, sondern eines mit **grober Körnung**.

**Zweitens: Die Körnung ist die Untergrenze jeder Frist.** Eine Fortschrittsfrist von
10 oder 30 Sekunden wäre kein Wächter, sondern ein Zufallsgenerator, der gesunde Läufe
abbricht. Zugelassen ist bei uns darum erst **96 Sekunden — drei Takte**. Zwei wären die
nackte Grenze; der dritte ist der Abstand, den eine an einer einzigen Maschine erhobene
Zahl braucht.

**Drittens: Die Prüfung steht im Code, nicht im Docstring.** `glb_zu_multipass` **weist**
eine zu kurze Frist **ab**, mit den Messpunkten in der Fehlermeldung. Das ist die Lehre
aus Sitzung 07, wo ein Docstring „fail-closed" zusagte und die Schranke vier
fail-open-Löcher hatte:

> Ein Docstring ist keine Prüfung.

**Viertens: Auch mit 96 Sekunden ist die Wache ihr Geld wert.** Der Gesamt-Timeout eines
Multipass-Laufs steht bei 900 Sekunden. Ein Hänger fällt damit **neunmal früher** auf.

---

---

# NACHTRAG: Auf der GPU gibt es gar keinen Takt

**HomeStation, `auf-20260820-18` · Blender 5.2.0 LTS · OptiX auf einer RTX 5090 · zwei
Läufe, auf die Zehntelsekunde identisch**

Der Vorbehalt unten war berechtigt, und die Antwort fällt schärfer aus als befürchtet.

| | CPU (hier) | GPU (HomeStation) |
|---|---|---|
| Dauer | 190 s | 177 s |
| Änderungen der Ausgabe | 6 | **3** |
| Zeitpunkte | 34, 66, 98, 130, 162, 190 s | **1,0 · 2,0 · 177,0 s** |
| Längste Lücke | 32 s | **175 s** |
| Gesamtwachstum | 937 Bytes | 739 Bytes |

**Das ist kein langsamer Takt, sondern keiner: Anfang und Ende, nichts dazwischen.**

Der Inhalt bestätigt es. In den 739 Bytes stehen dreizehn Zeilen — glTF-Importmeldungen,
eine Treiberwarnung, die Messzeilen des Prüfskripts, die Versionszeile — und ganz am Ende
`02:56.274 render | Saved: …`. **Keine einzige Fortschrittszeile** während der
175 Sekunden. Blender 5.2 im Hintergrundbetrieb mit OptiX gibt während des Renderns
nichts aus.

Beide Läufe sind auf die Zehntelsekunde gleich — 1,0 / 2,0 / 177,0, je 739 Bytes. Ein
Zufall ist das nicht.

## Was daraus folgt, und es ist eine Rücknahme

**Die Zahl 32 war ein Artefakt der CPU-Messung.** Sie war keine Eigenschaft von Blender,
sondern eine von Cycles-auf-CPU in diesem Container — und sie hätte auf der Maschine, die
wirklich rechnet, aktiv Schaden angerichtet: Eine Wache mit der daraus abgeleiteten Frist
von 96 Sekunden hätte **jeden gesunden GPU-Lauf über 98 Sekunden abgebrochen**, also
praktisch jeden echten.

> Eine Messung gilt so weit, wie gemessen wurde. Der Vorbehalt in diesem Dokument war
> nicht Höflichkeit, sondern die halbe Erkenntnis.

**Die Standardausgabe taugt für Blender nicht als Fortschrittszeichen — auf keiner Frist.**
Solange sie zwischen Start und Ende schweigt, bricht jede Frist, die kürzer ist als der
ganze Lauf, einen gesunden Lauf ab; und wie lange ein Lauf dauert, weiss man vorher nicht
— genau darum gibt es ja eine Wache. `glb_zu_multipass` **weist darum jeden Wert von
`stillstand_frist_s` ab**, mit den Messpunkten in der Meldung. Nicht mehr „zu kurz",
sondern „es gibt keinen".

Was stattdessen tragen könnte — drei Kandidaten, **alle ungemessen**, als Vorschlag und
nicht als Empfehlung:

1. **Die Leistungsaufnahme der Karte** (`nvidia-smi`). Sie lag während des Laufs
   durchgehend hoch und fällt bei einem Hänger sofort.
2. **Die Änderungszeit der Zieldatei**, sofern Blender sie fortschreibt — nach dieser
   Messung tut es das nicht.
3. **Ein Fortschritts-Schreiber im Runner selbst**, der aktiv schreibt, statt auf
   Cycles-Ausgabe zu warten.

Nur der dritte hängt nicht von fremdem Verhalten ab.

## Der zweite Befund, und er ist der gefährlichere

Der Auftrag verlangte `stdout` in eine **Datei**. Das ist mit dem dort verfügbaren Blender
**nicht möglich** — und das ist selbst ein Befund:

> Das Snap-Paket **Blender 5.2.0 LTS** — das einzige mit OptiX und CUDA — beendet sich bei
> einer Umleitung nach `>` in eine Datei **nach 1,3 Sekunden mit Rückgabewert 0, ohne
> Ausgabe und ohne Bild.**

Gegengeprüft mit reiner Shell-Umleitung, unter der Datenplatte, unter dem
Benutzerverzeichnis und im Bereich des Pakets selbst: jedes Mal null Byte, jedes Mal kein
Bild. Über eine **Pipe** rendert dasselbe Blender einwandfrei. Der nicht eingesperrte Fork
(5.1.2) schreibt zwar in eine Datei, hat aber keine GPU-Kernel — GPU und Dateiumleitung
sind mit dem Installierten nicht kombinierbar.

**Eine Erfolgsmeldung ohne Ergebnis ist die teuerste Sorte Fehler, die dieses Projekt
kennt.** Rückgabewert 0, kein Bild, keine Zeile Begründung.

Und es trifft Code, der am Vormittag desselben Tages entstanden ist: `starter_mit_wache`
leitete `stdout` in eine temporäre **Datei** um — genau der Fall. Auf der HomeStation
hätte er nie ein Bild erzeugt.

**Behoben mit der Bauart, die die HomeStation selbst benutzt hat:** Die Ausgabe läuft über
eine **Pipe**, und ein eigener Faden giesst sie **laufend** in die Datei. Damit fällt
beides weg — der Puffer läuft nie voll (die Blockiergefahr, wegen der die Datei überhaupt
gewählt wurde), und die Datei wächst genau dann, wenn der Prozess schreibt. Ein Test mit
zwei Megabyte durch die Pipe hält das fest.

## Der Nebenbefund, bestätigt und verschärft

Oben steht, die Samplezahl sei eine Obergrenze und keine Angabe der Rechenzeit. Auf der
GPU ist der Abstand grösser: **3000 Samples ohne adaptives Sampling brauchen dort 2,2
Sekunden**, wo der CPU-Lauf hier 190 Sekunden brauchte. Um überhaupt drei Minuten zu
messen, waren **220 000** Samples nötig — das 73-fache der Vorgabe.

> Wer eine Laufzeit aus einer Samplezahl schätzt, liegt zwischen diesen beiden Maschinen
> um **zwei Grössenordnungen** daneben.

---

## Der Vorbehalt, und er ist nicht klein

Gemessen wurde auf einer **CPU**, in einem **Container**, an einer **Spielzeugszene**, mit
**einer** Blender-Fassung. Ob GPU-Cycles auf der HomeStation denselben Takt hält, ist
**offen**. Denkbar ist beides: ein anderer Takt, oder gar keiner, weil die GPU-Anbindung
anders berichtet.

Wer die Zahl 32 übernimmt, übernimmt diesen Vorbehalt mit. Sie steht darum als benannte
Konstante `BLENDER_TAKT_S` mit der Messung im Kommentar — und **nicht** als Vorgabewert
irgendeiner Funktion. Die Wache ist in `glb_zu_multipass` ausgeschaltet, bis jemand auf
der richtigen Maschine nachgemessen hat.

Das war der Auftrag `auf-20260820-18`. **Er ist beantwortet — siehe den Nachtrag oben.**

---

## Nebenbefund

Ohne abgeschaltetes adaptives Sampling war derselbe Lauf mit **6000** Samples nach
**12 Sekunden** fertig — bei 512 × 512. Adaptives Sampling bricht früh ab, wenn das Rauschen
unter eine Schwelle fällt.

Das ist für die Messung nur lästig, für den Renderauftrag aber eine Notiz wert: **Die
Samplezahl in unserem Auftrag ist eine Obergrenze und keine Angabe der Rechenzeit.** Wer
aus „3000 Samples" auf eine Dauer schliesst, schliesst falsch, und zwar um mehr als eine
Grössenordnung.


---

# Teil 3 · Die Quelle, die trägt — gemessen, nicht geraten

Nach dem GPU-Befund blieben drei Kandidaten für ein Fortschrittszeichen, alle ungemessen.
Zwei davon liessen sich hier sofort prüfen, weil sie **in** Blender liegen. Also geprüft,
alle drei im selben Lauf, Blender 4.2, 512 × 512, 3000 Samples ohne adaptives Sampling:

| Kandidat | Aufrufe während des Renders |
|---|---|
| `bpy.app.handlers.render_stats` | **0** — registriert, nie gefeuert |
| `bpy.app.timers` | **0** — feuern bei blockierendem Render nicht |
| **ein gewöhnlicher `threading.Thread`** | **61**, alle 2 s, durchgehend |

**Cycles gibt während des Renderns die GIL frei.** Ein einfacher Python-Faden läuft also
weiter, während `bpy.ops.render.render()` den Hauptfaden blockiert — die beiden
dokumentierten Haken tun es nicht.

Das ist Kandidat (c) aus dem Vorschlag der HomeStation, und es war der einzige, von dem
sie schrieb, er hänge **nicht von fremdem Verhalten ab**. Genau das bestätigt sich: Wir
schreiben selbst, statt auf Cycles zu warten.

## Gebaut und am echten Lauf nachgewiesen

`blender_depth_stage.py` kennt jetzt `--herzschlag-s`. Der Runner startet damit einen
Faden, der alle *n* Sekunden eine Zeile nach `<out>/herzschlag.txt` **anhängt** —
angehängt, damit die Datei *wächst*: Gleiche Grösse mit neuem Zeitstempel ist auf manchen
Dateisystemen nicht von unverändert zu unterscheiden.

Nachgewiesen an einem echten Multipass-Lauf über 42 Sekunden:

```
22 Schläge · längste Lücke 2,1 s · keine Lücke über 3 s
stdout im selben Lauf: 14 629 Byte, in Schüben
```

Auf unserer Seite der Prozessgrenze schaltet `glb_zu_multipass(herzschlag_takt_s=…)` die
Wache darauf. Sie schlägt an, wenn **fünf** Schläge nacheinander ausbleiben — fünf statt
einem, weil ein Faden ins Hintertreffen geraten kann, ohne dass etwas kaputt ist. Bei
2 Sekunden Takt sind das 10 Sekunden Frist: **neunzigmal früher als der Gesamt-Timeout.**

## Und die Einschränkung, ohne die das Ganze schädlich wäre

> Was hier entsteht, ist ein **Lebenszeichen** und kein **Fortschrittszeichen**.

Es belegt: Der Prozess lebt, und sein Python-Interpreter kommt zum Zug. Es belegt
**nicht**, dass der Renderer vorankommt — ein Cycles-Kern, der sich festfährt, ohne den
Prozess mitzunehmen, schlägt weiter.

Der Umkehrschluss trägt dagegen, und nur auf ihn schlägt die Wache an: Ein
**ausbleibender** Herzschlag heisst zuverlässig, dass der Prozess tot, eingefroren oder
vom Betriebssystem angehalten ist.

Wer aus einem laufenden Herzschlag auf Fortschritt schliesst, macht genau den Fehler,
gegen den `fortschritt.py` gebaut wurde — und den der Altbestand gemacht hat, als er
`status == "running"` für einen Beleg hielt.

## Nachgemessen auf der GPU — und der Kontrast ist der Beleg

Der Absatz hier lautete zuerst: *„Dass Cycles auch bei OptiX die GIL freigibt, ist sehr
wahrscheinlich und nicht gemessen. Solange das offen ist, bleibt `herzschlag_takt_s`
ausgeschaltet."*

**Gemessen (`auf-20260820-19`, Blender 5.2.0 LTS, OptiX auf einer RTX 5090, 220 000
Samples, zwei Läufe):**

| | |
|---|---|
| Schläge | **88** |
| Renderdauer | 175,3 s |
| Längste Lücke | **2,10 s** bei 2,0 s Takt |
| Nummern | **lückenlos 1 … 88**, kein Sprung |
| Beide Läufe | identisch |

**Der Kontrast, der es belegt:** Dieselbe Szene, dieselbe Dauer, derselbe Rechner wie in
Teil 2 — dort schwieg Blenders Standardausgabe **175 Sekunden am Stück**. Im selben
Zeitraum feuert der Faden 88 Mal.

> Der Unterschied liegt nicht am Renderer und nicht am Gerät, sondern daran, **wer**
> schreibt: Cycles schweigt, ein eigener Faden nicht.

Ausdrücklich mitgeprüft, weil danach gefragt war: Es gibt **keine verhungerten Schläge**.
Die Nummern zählen in beiden Läufen lückenlos hoch — der Faden wurde nicht zwischendurch
verdrängt.

**Damit ist der Herzschlag voreingestellt.** Vorher war er ausgeschaltet, weil nur die CPU
gemessen war, und Vermutungen bleiben in diesem Projekt ausgeschaltet. Die Frist von fünf
ausgefallenen Schlägen (10 s) liegt fast beim **Fünffachen** der grössten je beobachteten
Lücke — und lässt einen hängenden Lauf nach 10 statt nach 900 Sekunden auffallen.
