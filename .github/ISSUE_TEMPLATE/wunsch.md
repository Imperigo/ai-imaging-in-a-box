---
name: Wunsch oder Vorschlag
about: Etwas soll dazukommen oder anders werden
title: ''
labels: wunsch
assignees: ''
---

<!--
BITTE ZUERST LESEN — sonst kostet der Vorschlag Sie mehr Zeit, als er bringt:

* Visbox ist eine Vertiefungsarbeit mit Abgabetermin Ende Februar 2027. Was auf dem
  Plan steht, hat Vorrang (docs/PLAN_BIS_FEBRUAR_2027.md). Ein guter Vorschlag kann
  liegen bleiben, ohne dass etwas mit ihm falsch ist. Ab dem 1. Februar 2027 kommt
  kein neues Merkmal mehr dazu.
* Zielhardware ist ein Laptop (MacBook M1 Max), nicht eine Arbeitsstation mit grosser
  Grafikkarte. Was nur auf schneller Hardware erträglich ist, ist hier kein fertiges
  Merkmal.
* Regel 3: keine echten Projektdaten, keine Büro-, Kunden- oder Projektnamen, keine
  absoluten Pfade mit einem Benutzernamen darin.

Alles auf Deutsch, Schweizer Schreibung ("ss", kein Eszett).
-->

## Welches Problem lösen Sie damit?

<!--
Das Problem, nicht die Lösung. Ein Vorschlag, der nur die Lösung nennt, lässt sich
nicht gegen einen anderen abwägen — und genau das muss hier passieren.
-->

## Wie sieht es aus, wenn es da ist?

<!-- Ein Ablauf in zwei, drei Schritten. Was tut die Anwenderin, was passiert? -->

## Woran würde man MESSEN, dass es wirklich funktioniert?

<!--
Die wichtigste Frage in diesem Formular, und der häufigste Grund, warum ein Vorschlag
hier stecken bleibt.

Dieses Projekt lebt davon, dass eine Aussage einen Messwert hinter sich hat. "Sieht
besser aus" ist keine Messung. "In 12 von 12 Fällen fällt der Wert unter die Schwelle,
wo er vorher darüber lag" ist eine.

Wenn Sie es nicht messen können, schreiben Sie das hin. Eine benannte Lücke ist besser
als eine, die nach Vollständigkeit aussieht — und manchmal ist genau das der Kern der
Aufgabe.
-->

## Und die Gegenprobe?

<!--
Woran würde man merken, dass die Messung gar nichts zeigt?

Am 18.09.2026 hat dieses Projekt genau daran seine Geometrieprüfung verloren: Die
Bilder bestanden die Schwelle — sie bestanden sie aber auch gegen die Tiefenkarte
eines völlig anderen Gebäudes. Ein Prüfverfahren, das auch die falsche Antwort
durchlässt, hat nicht die richtige bestätigt.
-->

## Berührt es eine der vier Regeln?

<!--
Die Regeln stehen in CLAUDE.md und in CONTRIBUTING.md. Bitte prüfen Sie selbst und
kreuzen Sie an — die Kästchen stehen ausserhalb dieses Kommentars, weil GitHub den
Inhalt eines Kommentars niemandem anzeigt.
-->

- [ ] **Regel 1** — Neue Abhängigkeit? Dann bitte Name, Fassung und LIZENZ hierher, und
      wo Sie sie nachgelesen haben (Primärquelle, nicht Sekundärquelle). Nur MIT, BSD,
      Apache-2.0 oder MPL-2.0. Kein GPL, kein AGPL — auch nicht optional. Modellgewichte
      zählen mit: Non-Commercial ist ausgeschlossen, und ein LoRA erbt die Lizenz seines
      Grundmodells.
- [ ] **Regel 2** — Braucht es Blender im selben Prozess (`import bpy`)? Dann geht es so
      nicht. Als Subprozess schon.
- [ ] **Regel 3** — Braucht es echte Projektdaten im Repo? Dann geht es so nicht.
- [ ] **Regel 4** — Ist es nur über die Oberfläche erreichbar? Dann fehlt der Weg aus
      Python heraus. Was nur über einen Klick erreichbar ist, existiert nicht.
- [ ] Keine davon.

## Was es ausdrücklich NICHT sein soll

<!--
Die Abgrenzung. Sie verhindert, dass aus einem Vorschlag im Bauen etwas anderes wird
als das, worüber man sich einig war.
-->

## Gibt es das schon halb?

<!--
Falls Sie nachgesehen haben: wo, und warum es nicht reicht. Falls nicht: auch gut,
dann steht es hier.
-->
