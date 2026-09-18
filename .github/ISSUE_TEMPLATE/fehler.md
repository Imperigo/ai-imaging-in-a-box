---
name: Fehler melden
about: Etwas verhält sich anders, als es beschrieben ist
title: ''
labels: fehler
assignees: ''
---

<!--
BITTE ZUERST LESEN — zwei Dinge, die hier anders sind als anderswo:

1. REGEL 3. In dieses Formular gehören keine echten Projektdaten: keine IFC-Dateien,
   keine Pläne, keine Renderings aus echten Aufträgen, keine Büro-, Kunden- oder
   Projektnamen — auch nicht in Pfaden oder Dateinamen. Und KEIN absoluter Pfad, in dem
   ein Benutzername steht. Ersetzen Sie ihn durch <nutzer>, bevor Sie etwas einfügen.
   Das passiert am häufigsten in Fehlertexten: Ein Traceback bringt den vollen
   Skriptpfad mit, und darin steht der Name.

2. EINE SICHERHEITSLÜCKE GEHÖRT NICHT HIERHER. Siehe SECURITY.md.

Alles auf Deutsch, Schweizer Schreibung ("ss", kein Eszett).
-->

## Was Sie erwartet haben

<!-- Ein Satz. -->

## Was stattdessen passiert ist

<!-- Ein Satz, dazu die Fehlermeldung oder der Messwert im Wortlaut. -->

## Gemessen oder vermutet?

<!--
In diesem Projekt wird beides getrennt gehalten, auch in Fehlermeldungen. Beides ist
willkommen — nur die Verwechslung ist teuer. Bitte kreuzen Sie an; die Kästchen stehen
ausserhalb dieser Kommentare, weil GitHub den Inhalt eines Kommentars niemandem anzeigt.
-->

- [ ] **Gemessen** — ich habe es laufen lassen, und die Zahl oben steht so im Ergebnis.
- [ ] **Vermutet** — mir ist es aufgefallen, ich habe es nicht nachgerechnet.

## Wie man es wiederholt

<!--
Möglichst klein. Wenn Geometrie nötig ist, nehmen Sie die synthetische — das Repo
enthält keine IFC-Datei, sie wird erzeugt:

    python3 tools/make_test_ifc.py build/testbau.ifc

1.
2.
3.
-->

## Umgebung

| | |
|---|---|
| Betriebssystem und Hardware | <!-- z. B. macOS 15, M1 Max --> |
| Python | <!-- python3 --version --> |
| Fassung von Visbox | <!-- Commit oder Datum --> |
| Blender | <!-- blender --version, falls beteiligt --> |
| IFC-Umgebung (`.venv-ifc`) angelegt? | <!-- ja / nein --> |
| GPU und Modellgewichte vorhanden? | <!-- ja / nein --> |

<!--
Die letzte Zeile ist wichtiger, als sie aussieht: Die Testsammlung und die ganze
QA-Kette laufen ohne GPU. Wenn ein Fehler NUR mit Gewichten auftritt, ist das eine
andere Ecke des Programms als einer, der auch ohne auftritt.
-->

## Wo es passiert ist

<!-- Kreuzen Sie an, was zutrifft — es sagt, wer nachsehen muss. -->

- [ ] Geometrieseite: IFC → glb, Blender, Kamera, Rahmung
- [ ] Bildmodell-Stufe (braucht Gewichte)
- [ ] Messung und Tore: Geometrie-QA, Stil-Gate, Schwellen
- [ ] Auftragsweg: Aufträge, Ergebnisse, Abholung
- [ ] Bibliothek und Import (Regel 4)
- [ ] Weiss ich nicht

## Falls eine Messung beteiligt ist

<!--
Drei Antworten sind hier möglich, und sie bedeuten Verschiedenes:

  bestanden        das Tor hat geprüft und durchgelassen
  durchgefallen    das Tor hat geprüft und gesperrt
  None             NICHT GEMESSEN — das Tor hat gar nicht geprüft

Wenn Sie ein `None` bekommen haben, wo Sie eine Zahl erwarteten, ist das oft kein
Fehler, sondern die richtige Antwort. Schreiben Sie trotzdem hin, was Sie erwartet
haben — wenn die Messung hätte stattfinden müssen, ist es einer.
-->

## Sonstiges

<!-- Alles, was nirgends passt. Lieber zu viel als zu wenig, aber ohne echte Daten. -->
