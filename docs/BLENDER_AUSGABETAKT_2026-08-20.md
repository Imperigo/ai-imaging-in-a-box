# Blenders Standardausgabe hat einen Takt von 32 Sekunden

**Messung vom 20.08.2026 · Anlass: Fortschrittswache · zwei Läufe, übereinstimmend**

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

## Der Vorbehalt, und er ist nicht klein

Gemessen wurde auf einer **CPU**, in einem **Container**, an einer **Spielzeugszene**, mit
**einer** Blender-Fassung. Ob GPU-Cycles auf der HomeStation denselben Takt hält, ist
**offen**. Denkbar ist beides: ein anderer Takt, oder gar keiner, weil die GPU-Anbindung
anders berichtet.

Wer die Zahl 32 übernimmt, übernimmt diesen Vorbehalt mit. Sie steht darum als benannte
Konstante `BLENDER_TAKT_S` mit der Messung im Kommentar — und **nicht** als Vorgabewert
irgendeiner Funktion. Die Wache ist in `glb_zu_multipass` ausgeschaltet, bis jemand auf
der richtigen Maschine nachgemessen hat.

Das ist der Auftrag `auf-20260820-18`.

---

## Nebenbefund

Ohne abgeschaltetes adaptives Sampling war derselbe Lauf mit **6000** Samples nach
**12 Sekunden** fertig — bei 512 × 512. Adaptives Sampling bricht früh ab, wenn das Rauschen
unter eine Schwelle fällt.

Das ist für die Messung nur lästig, für den Renderauftrag aber eine Notiz wert: **Die
Samplezahl in unserem Auftrag ist eine Obergrenze und keine Angabe der Rechenzeit.** Wer
aus „3000 Samples" auf eine Dauer schliesst, schliesst falsch, und zwar um mehr als eine
Grössenordnung.
