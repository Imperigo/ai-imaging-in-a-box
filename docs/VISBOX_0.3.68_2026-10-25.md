# Visbox 0.3.68 — Fassungsblatt (25.10.2026)

**Codestand:** Fassung 0.3.68 auf `main` (Skizze aus der Mac-Mappe, Modell ersetzen am Mac, Umfeld-Nachträge, Werkzeugkatalog);
Vorgänger 0.3.67 = Tag `v0.3.67`

**Grundlage:** Mac-Prüfungen 0.3.66/0.3.67 (Demotester), Demolauf «Haus am Hang · Variante A»; Ergebnis 366; Owner-Entscheid
153; Protokoll 74 §293a–§296; Einbau-Stand C201, C204, C207, C208, C211, C212; Aufträge 367, 368. Abgeglichen gegen alle
Änderungen seit `v0.3.67` (`git log v0.3.67..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.68

«Bild aus Skizze» ging in einer Mappe am Mac gar nicht — die Skizze reiste nicht mit. «Andere Datei …» ersetzte das
Modell einer bestehenden Mac-Mappe nicht. Am Demohaus deckten Autos mehr als den Sockel, die Kegelbäume blieben stehen,
und bei knappem Gelände stellte das Umfeld nichts.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Bild aus Skizze» in einer Mappe am Mac: Skizze und Unterlagebild reisen mit; der Standpunkt kommt vom Bild unter der Skizze | 96b | gebaut, mit Probe; Messung 368 und Mac offen |
| Ohne Wahl rechnet z-image-turbo die Skizze als Startbild (freie Lizenz, ohne Karte) | — | gebaut, mit Probe; Messung 368 offen |
| In «Voll» rechnet ein Bild aus einer Skizze mit ausdrücklich gewähltem Qwen-Image ohne Klick (zählt zu 5/h, bleibt markiert) | 153 | gebaut, mit Probe |
| «Andere Datei …» ersetzt das Modell einer bestehenden Mac-Mappe; das alte bleibt als `modell.vorher.glb`; Fehler stehen als Satz am Knoten | — | gebaut, mit Probe; am Mac offen |
| Warnung, wenn Claudes Verbindung mit einer älteren Fassung läuft als die App | — | gebaut, mit Probe |
| Werkzeugtexte je Modus richtig; «Freies Bild» im Knotenkatalog; «Grundbild rendern» meldet «vorhanden, nicht neu gerechnet» | 146, 149 | gebaut, mit Probe; am Mac offen |
| Autos vor dem Haus nur, wenn sie im Bild höchstens den Sockel decken (≤ 6 % je Bauteil) | — | gebaut, mit Probe; Messung 367 offen |
| Kegelbäume des Modells werden auch am Material erkannt und ausgeblendet | — | gebaut, mit Probe; Messung 367 offen |
| Bei knappem Gelände legt das Umfeld einen flachen Wiesenring bis 20 m um das Haus | — | gebaut, mit Probe; Messung 367 offen |

## Stand am Gerät

* **Mac:** Update-Knopf; danach Visbox ganz beenden und neu starten, Claude Desktop neu starten. Prüfen: `visbox_status`
  nennt 0.3.68; «Andere Datei …» → Knoten zeigt die neue Zahl der Bauteile, auch nach erneutem Öffnen; iPad-Skizze auf
  Grundbild sSW → «Bild aus Skizze» → Bild von sSW.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 367 und 368.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ob aus den Strichen der Skizze mit z-image-turbo wirklich Bauteile werden, ist ungemessen (368).
* Vom Bild unter der Skizze reist nur die Richtung mit, nicht Augenhöhe und Brennweite.
* Die Warnung zur Claude-Verbindung hilft erst ab dem nächsten Update (alte Verbindungen kennen sie nicht).
* Der Wiesenring verändert Bilder von Häusern mit knappem Gelände; ob am Rand eine Kante sichtbar ist, zeigt erst 367.
* Bei jedem Update fragt der Mac weiter dreimal nach dem Passwort (feste Unterschrift nach der Demo, E144).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
