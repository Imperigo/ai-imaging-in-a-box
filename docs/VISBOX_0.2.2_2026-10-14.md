# Visbox 0.2.2 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.2 auf `main` (Bau von Entscheid 85 und RealityScan-Brücke Fassung 2); Vorgänger 0.2.1 = Tag `v0.2.1` (13.10.2026)

**Grundlage:** Owner-Entscheid 85/85a–c (14.10.2026 per Auswahl, Blatt 19 der Entwurfsfläche); Messung
`auf-20261013-278` und Owner-Entscheid «RealityScan ist der Weg fürs Umgebungsnetz» (14.10.2026, Protokoll 74 §100–101)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.2

Der Owner will die Knoten am Mac sehen; dafür braucht es eine neue Fassung (Freigabe nur bei neuer Nummer, Entscheid
84b). Es ist zugleich die erste Fassung, die eine Mac-App 0.2.1 über den Knopf «Aktualisieren» erreicht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: nach «Schon anfangen» zuerst die Knoten (das KosmoVis-Werkzeug), oben der Schalter «Knoten / Visbox-Seite» | 85, 85a, 85c | gebaut, Prüfstrecke; am Gerät unbestätigt |
| Die Knoten zeigen die zuletzt auf der Visbox-Seite geöffnete Mappe (Heim-PC merkt sie sich, auch im Browser) | 85b | gebaut; am Gerät unbestätigt |
| Umgebung aus den Fotos (RealityScan): Brücke nach der Messung am Heim-PC repariert — richtiges Startprogramm, kein Hänger an Bildpfaden, vereinfachtes Netz, Farben nicht mehr schwarz, Deckel weg, kein Programm bleibt nach einer Frist stehen | 79, 81 | gebaut; Lauf über die Brücke am Heim-PC in Prüfung |

## Stand am Gerät

* **Aktualisieren:** Diese Fassung ist die erste echte Probe des Knopfs — eine Mac-App 0.2.1 sollte oben
  «● 0.2.2 verfügbar — Aktualisieren» zeigen.
* **RealityScan:** Die HomeStation schaltet die Brücke ein und rechnet einen Hallenauftrag; erst danach ist bekannt, ob
  das Bild mit der neuen Umgebung besteht. Die Messung von Hand ergab 93 % Deckung in 324 s.

## Passende KosmoOrbit-Fassung

* Wie bei 0.2.1: **KosmoOrbit 0.1.8** (Runde 23). Die Knotenansicht in Visbox ist die Kopie aus KosmoOrbit (E26); was
  der UI-Worker drüben daran ändert, kommt erst mit einer späteren Übernahme.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Die Knoten sind eine Webseite des Heim-PC im Fenster der Mac-App**, kein Nachbau am Mac. Ohne Verbindung zum
  Heim-PC gibt es keine Knoten (der Vorführmodus bleibt, wie er war).
* **Die zuletzt geöffnete Mappe** merkt sich der Heim-PC nur, solange sein Dienst läuft; nach einem Neustart gilt wieder
  die Mappe vom Start.
* **RealityScan** läuft nur am Heim-PC des Lizenznehmers, wird nie mitgeliefert und ist nie Voraussetzung (Entscheid 79).
* Nach dem Ersetzen kann macOS einmal «Trotzdem öffnen» und den Schlüsselbund verlangen (wie in 0.2.1 beschrieben).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml` auf dem Zweig des
Baus; der Job `freigabe` legt die Freigabe erst auf `main` an.
