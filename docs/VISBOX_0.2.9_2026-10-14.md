# Visbox 0.2.9 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.9 auf `main` (Entscheid 94: die Knoten sind die Arbeitsfläche, die Seite ein Nebenweg; Warnung
bei fehlendem Bestand; Laden ohne Start-Mappe hängt nicht mehr); Vorgänger 0.2.8 = Tag `v0.2.8` (14.10.2026)

**Grundlage:** Owner-Klarstellung und Entscheide 94/94b (14.10.2026 per Auswahl); Ergebnisse `auf-20261014-283` und
`auf-20261014-284`; Entscheid 93 (Protokoll 74 §115–117)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.9

Der Owner hat klargestellt: In beiden Programmen ist die Knotenansicht die Arbeitsfläche zum Rendern. Die Mac-App zeigte
die alte Seite noch gleichrangig daneben — das ändert nur eine neue Fassung. Zugleich die erste Fassung, die der neue
Neustart aus 0.2.8 von selbst erreicht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: nur noch Knoten in der Leiste; die Visbox-Seite über das Menü «Darstellung», zurück mit einem Knopf | 94 | gebaut, Prüfstrecke; am Mac unbestätigt |
| Heim-PC: «Datei laden» ohne Start-Mappe hängt nicht mehr fest | 90d (Nachbesserung) | gebaut, mit Probe |
| Heim-PC: Warnung im Ergebnis, wenn eine Umgebung bestellt, aber kein Körper als Bestand markiert ist | — | gebaut, mit Probe |
| Mac: von 0.2.8 aus startet die App nach dem Aktualisieren von selbst neu und meldet die Nummer | 87 (Nachbesserung) | erster echter Gang; am Mac unbestätigt |

## Stand am Gerät

* **Mac:** In 0.2.8 einmal «● 0.2.9 verfügbar» klicken — die App beendet sich, startet neu und meldet «Visbox 0.2.9 ist
  installiert». Das ist zugleich die Probe für den neuen Neustart.
* **Heim-PC:** Die beiden Nachbesserungen kommen mit `git pull` und einem Neustart des Dienstes (angesagt).

## Passende KosmoOrbit-Fassung

* Wie 0.2.8: KosmoOrbit Runde 29, der Zweig `claude/kosmovis-startgraph` kommt dort in Runde 30.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Bestellen aus der Knotenansicht geht im Dienstbetrieb erst nach der Umstellung der Ablage (Entscheid 93, Auftrag 285).
* Strg+Z wirkt in der Visbox-Knotenansicht nicht.
* Skizzen vom iPad und die Liste der Läufe gibt es nur auf der Seite — noch nicht als Knoten.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
